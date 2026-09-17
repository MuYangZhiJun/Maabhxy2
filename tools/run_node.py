#!/usr/bin/env python3
"""跑单个 pipeline 节点（可以带 pipeline_override），排查用的。

为什么单独写一个：`tools/run_task.py --node 节点名` **不带 override**，
而项目里很多节点在文件里是 `enabled: false`（靠任务的选项/override 才打开），
单独跑就是「没启用」，什么都不会发生。这个脚本用来做**单节点隔离测试** ——
比如「选好友这一下到底点没点动」、「这个门槛认不认得出来」。

用法：
    python tools/run_node.py 日常_活动BONUS_选好友
    python tools/run_node.py 日常_活动BONUS_选好友 '{"target":[682,651,0,0]}'
    python tools/run_node.py 主界面_就绪 '{"threshold":0.9}' --no-agent
"""

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_ADB_CANDIDATES = [
    r"E:\MuMu Player 12\nx_main\adb.exe",
    r"E:\MuMu Player 12\shell\adb.exe",
    r"D:\MuMu Player 12\shell\adb.exe",
]
DEFAULT_ADDRESS = "127.0.0.1:16384"


def find_adb():
    for c in DEFAULT_ADB_CANDIDATES:
        if os.path.isfile(c):
            return c
    import shutil
    return shutil.which("adb")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="跑单个节点（带 override）")
    ap.add_argument("node", help="节点名")
    ap.add_argument("override", nargs="?", default="{}",
                    help='额外字段，JSON，例如 \'{"threshold":0.9}\'')
    ap.add_argument("--address", default=DEFAULT_ADDRESS)
    ap.add_argument("--adb", default=None)
    args = ap.parse_args()

    try:
        extra = json.loads(args.override)
    except Exception as exc:  # noqa: BLE001
        print(f"[!!] override 不是合法 JSON: {exc}")
        return 1

    from maa.controller import AdbController
    from maa.resource import Resource
    from maa.tasker import Tasker
    from maa.toolkit import Toolkit

    Toolkit.init_option(ROOT)
    resource = Resource()
    job = resource.post_bundle(os.path.join(ROOT, "assets", "resource"))
    job.wait()
    if not job.succeeded:
        print("[!!] 资源加载失败")
        return 1

    override = {args.node: dict({"enabled": True}, **extra)}
    print("override:", json.dumps(override, ensure_ascii=False))
    resource.override_pipeline(override)

    adb = args.adb or find_adb()
    if not adb:
        print("[!!] 找不到 adb")
        return 1
    controller = AdbController(adb, args.address)
    controller.post_connection().wait()
    if not controller.connected:
        print("[!!] 连不上模拟器")
        return 1

    tasker = Tasker()
    if not tasker.bind(resource, controller):
        print("[!!] bind 失败")
        return 1

    print("跑节点:", args.node)
    detail = tasker.post_task(args.node).wait().get()
    status = getattr(detail, "status", None)
    print("结果: succeeded =", getattr(status, "succeeded", "?"))
    rows = []
    for n in (getattr(detail, "nodes", None) or []):
        reco = getattr(n, "recognition", None)
        box = getattr(reco, "box", None) if reco is not None else None
        line = "   %-32s %s" % (getattr(n, "name", "?"),
                                ("命中 " + str(box)) if box is not None else "未命中")
        print(line)
        rows.append(line)
    # 节点结果也落一份 UTF-8：控制台/重定向经常把中文吃掉
    try:
        log = os.path.join(ROOT, "debug", "run_node.log")
        os.makedirs(os.path.dirname(log), exist_ok=True)
        with open(log, "w", encoding="utf-8") as f:
            f.write("节点: %s\noverride: %s\n\n" %
                    (args.node, json.dumps(override, ensure_ascii=False)))
            f.write("\n".join(r.rstrip() for r in rows) + "\n")
        print("节点日志 ->", log)
    except Exception as exc:  # noqa: BLE001
        print("[!!] 写不了节点日志:", exc)
    time.sleep(1.0)
    return 0


if __name__ == "__main__":
    sys.exit(main())
