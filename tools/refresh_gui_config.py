# -*- coding: utf-8 -*-
"""修 GUI 实例配置里的**选项勾选**（selected_cases）。

为什么需要：MFAAvalonia 的 `config/instances/*.json` 里存着用户勾了什么
（`selected_cases`）。**interface.json 里新加的 case 不会自动出现在这份勾选里** ——
于是界面上看不到、跑起来也不执行，症状是"我加了选项但它没生效"。

⚠️ **`pipeline_override` 那一项不用管**：实测 GUI 重启时会自己按 interface.json
重新算一遍并存回配置（用户勾选保留、派生部分重建）。所以这个脚本只负责勾选；
真要连 override 一起重算，加 `--also-override`。

用法：
    python tools/refresh_gui_config.py                                  # 预览
    python tools/refresh_gui_config.py --add 领取奖励=领取奖励项目:吼姆的礼物 --write
"""

import argparse
import json
import os
import shutil
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_task import load_interface  # noqa: E402

CONFIG = os.path.join(ROOT, "gui", "config", "instances", "default.json")


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="重算 GUI 实例配置里的 pipeline_override")
    parser.add_argument("--add", action="append", default=[],
                        help="补勾选项，形如 --add 领取奖励=领取奖励项目:吼姆的礼物")
    parser.add_argument("--write", action="store_true", help="真的写回（不加就只预览）")
    parser.add_argument("--also-override", action="store_true",
                        help="顺便把 pipeline_override 也重算（一般不需要，GUI 自己会算）")
    args = parser.parse_args()

    adds = {}
    for item in args.add:
        task, rest = item.split("=", 1)
        opt, case = rest.split(":", 1)
        adds.setdefault(task, {}).setdefault(opt, []).append(case)

    interface = load_interface()
    tasks_by_name = {t["name"]: t for t in interface.get("task", [])}
    options = interface.get("option", {})

    data = json.load(open(CONFIG, encoding="utf-8"))
    changed = 0

    for item in data.get("TaskItems", []):
        name = item.get("name")
        task = tasks_by_name.get(name)
        if not task:
            print("[跳过] %s（interface.json 里没有这个任务，多半是旧条目）" % name)
            continue

        # 1) 修 selected_cases
        for opt_item in item.get("option", []) or []:
            opt = options.get(opt_item.get("name"))
            if not opt:
                continue
            valid = {c["name"] for c in opt.get("cases", [])}
            sel = list(opt_item.get("selected_cases") or [])
            kept = [s for s in sel if s in valid]
            stale = [s for s in sel if s not in valid]
            for case in adds.get(name, {}).get(opt_item["name"], []):
                if case in valid and case not in kept:
                    kept.append(case)
            if stale:
                print("[清理] %s / %s 去掉失效 case: %s" % (name, opt_item["name"], stale))
            if kept != sel:
                opt_item["selected_cases"] = kept
                changed += 1
                print("[选择] %s / %s -> %s" % (name, opt_item["name"], kept))

        # 2) 可选：连 override 一起重算（一般不需要，GUI 自己会算）
        if not args.also_override:
            continue
        from run_task import build_overrides
        case_over = {}
        for opt_item in item.get("option", []) or []:
            sel = opt_item.get("selected_cases")
            if sel is not None:
                case_over[opt_item["name"]] = sel
        new_override = build_overrides(interface, name, [], case_over)
        if item.get("pipeline_override") != new_override:
            item["pipeline_override"] = new_override
            changed += 1
            print("[重算 override] %s: %d 个节点" % (name, len(new_override)))

    print("\n共 %d 处改动" % changed)
    if args.write:
        shutil.copy2(CONFIG, CONFIG + ".bak")
        with open(CONFIG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("已写回 %s（备份 %s.bak）" % (CONFIG, CONFIG))
    else:
        print("（预览模式，没写。加 --write 才写回）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
