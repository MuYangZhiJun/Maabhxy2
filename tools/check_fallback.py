#!/usr/bin/env python3
"""找出「next 列表里没有一个必然命中的兜底节点」的节点。

为什么需要这个：MAA 的 next 逻辑是 `while(!timeout) { foreach(next); }`，
默认 20 秒。如果列表里每个候选都带识别（TemplateMatch / OCR / …），
而当时屏幕上恰好一个都认不到，就会**死等 20 秒然后把这个任务判失败**。

踩过的例子：`日常_邮件_领取` 的 next 是
`["日常_邮件_领取_关窗", "日常_邮件_体力"]` —— 邮件里没有可领附件时，
点「一键领取」不弹「已领取奖励」窗，`领取_关窗` 认不到；而「领取体力」那个选项
用户没勾（节点 enabled=false），于是两个候选全废，任务失败，
日志上只有一句「任务失败：领取邮件」，看不出来是死等。

判据：候选节点里只要有**一个**是"必然命中"的就算安全 ——
即没有 `recognition`（默认 DirectHit）或者显式写成 DirectHit 的节点
（通常是纯 Click 的收尾节点）。

用法：
    python tools/check_fallback.py
    python tools/check_fallback.py assets/resource/pipeline
"""

import argparse
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_jsonc(path):
    """pipeline/interface 都是 JSONC，去掉 // 行注释再解析。"""
    raw = open(path, encoding="utf-8").read()
    lines = [l for l in raw.splitlines() if not l.lstrip().startswith("//")]
    return json.loads("\n".join(lines))


def always_hits(node):
    """这个节点是不是必然命中（不带识别）。"""
    if not isinstance(node, dict):
        return False
    reco = node.get("recognition")
    return reco is None or reco == "DirectHit"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="检查 next 列表有没有兜底节点")
    parser.add_argument("dir", nargs="?",
                        default=os.path.join(ROOT, "assets", "resource", "pipeline"))
    args = parser.parse_args()

    problems = []
    total_nodes = 0

    for name in sorted(os.listdir(args.dir)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(args.dir, name)
        data = load_jsonc(path)
        if not isinstance(data, dict):
            continue

        for node_name, node in data.items():
            if not isinstance(node, dict):
                continue
            total_nodes += 1
            nxt = node.get("next") or []
            if not nxt:
                continue

            missing = [n for n in nxt if n not in data]
            hits = [n for n in nxt if n in data and always_hits(data[n])]
            if not hits:
                problems.append((name, node_name, nxt, missing))

    print("== next 列表里没有必然命中兜底节点的 ==")
    if not problems:
        print("  (无)")
    for fname, node_name, nxt, missing in problems:
        print("  %s" % node_name)
        print("      文件: %s     next: %s" % (fname, nxt))
        if missing:
            print("      [!!] 其中这些节点不存在（会让资源加载直接失败）: %s" % missing)
    print()
    print("扫了 %d 个节点，可疑 %d 个。" % (total_nodes, len(problems)))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
