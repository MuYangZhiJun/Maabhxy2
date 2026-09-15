#!/usr/bin/env python3
"""让 MaaFramework 本体跑一次指定的 pipeline 节点，用来验证资源是不是真的能用。

这是最接近真实运行的验证：真的加载 assets/resource、真的连 adb、真的执行识别。
模板裁完、roi 改完，用这个确认一下再交给 GUI。

用法：
    python tools/run_once.py                      # 默认跑「主界面_就绪」
    python tools/run_once.py 启动_标题页
    python tools/run_once.py 主界面_就绪 --adb "E:\\MuMu Player 12\\shell\\adb.exe" --address 127.0.0.1:16384
"""

import argparse
import os
import sys

from maa.controller import AdbController
from maa.resource import Resource
from maa.tasker import Tasker
from maa.toolkit import Toolkit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DEFAULT_ADB = r"E:\MuMu Player 12\shell\adb.exe"
DEFAULT_ADDRESS = "127.0.0.1:16384"


def describe(obj, label):
    keys = [k for k in dir(obj) if not k.startswith("_")]
    print(f"  [{label}] 可用字段: {keys}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="跑一次 pipeline 节点做验证")
    parser.add_argument("entry", nargs="?", default="主界面_就绪", help="节点名")
    parser.add_argument("--adb", default=DEFAULT_ADB)
    parser.add_argument("--address", default=DEFAULT_ADDRESS)
    parser.add_argument("--agent", default=None, help="自定义 agent 路径（可选）")
    parser.add_argument(
        "--enable",
        default="",
        help="逗号分隔的节点名，临时把这些节点 enabled 设为 true。"
             "pipeline 里默认关着的日常模块用它测，不用先去 GUI 里勾。",
    )
    args = parser.parse_args()

    if not os.path.isfile(args.adb):
        print(f"[!!] 找不到 adb: {args.adb}")
        sys.exit(1)

    override = {}
    for name in args.enable.split(","):
        name = name.strip()
        if name:
            override[name] = {"enabled": True}
    if override:
        print(f"临时启用 {len(override)} 个节点: {', '.join(override)}")

    Toolkit.init_option(ROOT)

    print(f"== 跑一次「{args.entry}」 ==")
    resource = Resource()
    print(f"[1/3] 加载资源 {os.path.join('assets', 'resource')}")
    load_job = resource.post_bundle(os.path.join(ROOT, "assets", "resource"))
    load_job.wait()
    if not load_job.succeeded:
        print("[!!] 资源加载失败")
        describe(load_job, "Job")
        sys.exit(1)
    print("      资源加载 OK")

    print(f"[2/3] 连接模拟器 {args.address}")
    controller = AdbController(args.adb, args.address)
    controller.post_connection().wait()
    if not controller.connected:
        print("[!!] 连接失败")
        sys.exit(1)
    print("      已连接")

    print(f"[3/3] 执行节点")
    tasker = Tasker()
    if not tasker.bind(resource, controller):
        print("[!!] bind 失败")
        sys.exit(1)
    detail = tasker.post_task(args.entry, override).wait().get()

    status = getattr(detail, "status", None)
    ok = getattr(status, "succeeded", None)
    if ok is None:
        ok = "succeeded" in str(status).lower()
    print(f"      执行结果: {status}（succeeded={ok}）")
    nodes = getattr(detail, "nodes", None) or []
    for node in nodes:
        name = getattr(node, "name", "?")
        reco = getattr(node, "recognition", None)
        box = getattr(reco, "box", None) if reco is not None else None
        hit = "命中" if box is not None else "未命中"
        print(f"      - {name}: {hit}" + (f"  {box}" if box is not None else ""))

    if not nodes:
        print("      （没拿到节点明细）")
        describe(detail, "TaskDetail")

    print()
    if nodes:
        hit = any(getattr(getattr(n, "recognition", None), "box", None) is not None
                  for n in nodes)
        print("[OK] 节点命中，资源可用" if hit else "[!!] 没命中，调模板或 roi")
    else:
        print("[??] 没拿到节点明细，看上面的输出")


if __name__ == "__main__":
    main()
