#!/usr/bin/env python3
"""扫 interface.json 里的「选项互相覆盖」冲突。

背景（踩过两次，都是"界面勾了但根本不生效"）：
  1. 「碎水晶」那个 bug —— 任务级 pipeline_override 强行把某个节点 enabled 打开了，
     而它在合并顺序里排在选项后面，于是把选项的选择整个盖掉。
  2. 「存在感」那个 bug —— 同一个 checkbox 的两个 case 都写了
     `日常_存在感.next`，用户两个都勾，后合并的那个赢，
     结果只切「每周任务」，存在感的奖励永远不领。

判据是「同一节点的同一字段被两处写」：
  - 同一个 checkbox 的两个 case 之间写了同一个 (节点, 字段)
    → 用户同时勾选时，只有 case 顺序里靠后的那个生效（静默失效）
  - 任务的 pipeline_override 和它某个选项的 case 写了同一个 (节点, 字段)
    → 任务级那份一定赢（合并顺序最后），选项形同虚设
  - 两个不同选项的 case 之间写了同一个 (节点, 字段)
    → 谁赢取决于任务里 option 数组的顺序，很脆

字段级别的"覆盖"只在**非 dict 字段**上成立（enabled 是 bool，
next/target/roi 这类是整体替换的数组）。custom_action_param 官方文档写明
"直接替换，内部不会合并"，所以也按整体替换算。

用法：
    python tools/check_option_conflict.py
"""

import argparse
import json
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_jsonc(path):
    raw = open(path, encoding="utf-8").read()
    lines = [l for l in raw.splitlines() if not l.lstrip().startswith("//")]
    return json.loads("\n".join(lines))


def fields_of(override):
    """把 pipeline_override 摊平成 {(节点, 字段): 值}。

    带上值是为了过滤掉「两边写的是同一个值」这种无害重叠 ——
    踩过：任务级和选项 case 都写 `enabled: true`，字段确实撞了，
    但值一样，谁赢都无所谓，不该当问题报出来。
    """
    out = {}
    for node, fields in (override or {}).items():
        if not isinstance(fields, dict):
            out[(node, "<整个节点>")] = fields
            continue
        for field, value in fields.items():
            out[(node, field)] = value
    return out


def _same_value(a, b):
    try:
        return a == b
    except Exception:  # noqa: BLE001
        return False


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="扫 interface.json 的选项覆盖冲突")
    parser.add_argument("interface", nargs="?",
                        default=os.path.join(ROOT, "assets", "interface.json"))
    args = parser.parse_args()

    data = load_jsonc(args.interface)
    options = data.get("option", {})
    tasks = data.get("task", [])

    problems = 0

    print("== 同一个 checkbox 的两个 case 抢同一个字段 ==")
    for opt_name, opt in options.items():
        # 只有 checkbox 的多个 case 会同时生效；switch / select 只能选一个，不算冲突。
        if opt.get("type") != "checkbox":
            continue
        cases = opt.get("cases", [])
        seen = defaultdict(list)
        for case in cases:
            for key, value in fields_of(case.get("pipeline_override")).items():
                seen[key].append((case.get("name"), value))
        for (node, field), entries in sorted(seen.items()):
            if len(entries) < 2:
                continue
            if all(_same_value(entries[0][1], v) for _, v in entries[1:]):
                continue  # 写的是同一个值，谁赢都一样
            problems += 1
            print("  [选项] %s" % opt_name)
            print("     %s.%s  被这些 case 都写了: %s" % (node, field, [n for n, _ in entries]))
            print("     → 用户同时勾选时只有最后一个生效")
    if problems == 0:
        print("  (无)")

    print()
    print("== 任务级 override 和选项 case 抢同一个字段 ==")
    before = problems
    for task in tasks:
        task_fields = fields_of(task.get("pipeline_override"))
        if not task_fields:
            continue
        for opt_name in task.get("option", []):
            opt = options.get(opt_name)
            if not opt:
                continue
            for case in opt.get("cases", []):
                case_fields = fields_of(case.get("pipeline_override"))
                for key in sorted(set(case_fields) & set(task_fields)):
                    if _same_value(case_fields[key], task_fields[key]):
                        continue  # 值一样，无害
                    node, field = key
                    problems += 1
                    print("  [任务] %s  的选项 %s / case %s"
                          % (task["name"], opt_name, case.get("name")))
                    print("     %s.%s  → 任务级那份合并时赢，选项形同虚设" % (node, field))
    if problems == before:
        print("  (无)")

    print()
    print("== 不同选项的 case 之间抢同一个字段 ==")
    before = problems
    owner = {}
    for opt_name, opt in options.items():
        for case in opt.get("cases", []):
            for key, value in fields_of(case.get("pipeline_override")).items():
                owner.setdefault(key, []).append(
                    ("%s/%s" % (opt_name, case.get("name")), value))
    for (node, field), entries in sorted(owner.items()):
        who = [n for n, _ in entries]
        distinct_opts = {n.split("/")[0] for n in who}
        if len(distinct_opts) > 1 and not all(
                _same_value(entries[0][1], v) for _, v in entries[1:]):
            problems += 1
            print("  %s.%s  被这些地方写: %s" % (node, field, who))
            print("     → 谁赢取决于任务里 option 数组的顺序")
    if problems == before:
        print("  (无)")

    print()
    print("共 %d 处可疑冲突。" % problems)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
