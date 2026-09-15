#!/usr/bin/env python3
"""把「应用了任务默认选项之后」的节点真实内容打出来。

用来回答这类问题：某个节点到底 enabled 没有？custom_action_param 展开成什么了？
（override 是「顶层字段同名就覆盖」，光看 pipeline 原文看不出来最终值。）

用法：
    python tools/dump_nodes.py 重复刷关 日常_活动BONUS
    python tools/dump_nodes.py 重复刷关 日常_活动BONUS_双倍券 日常_活动BONUS_开战
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from run_task import ROOT, build_overrides, load_interface  # noqa: E402


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    task_name = sys.argv[1]
    wanted = sys.argv[2:]

    interface = load_interface()
    overrides = build_overrides(interface, task_name, [])

    from maa.resource import Resource
    from maa.toolkit import Toolkit

    Toolkit.init_option(ROOT)
    resource = Resource()
    job = resource.post_bundle(os.path.join(ROOT, "assets", "resource"))
    job.wait()
    if not job.succeeded:
        print("[!!] 资源加载失败")
        return 1

    if overrides:
        resource.override_pipeline(overrides)

    print("== override 里出现的节点 ==")
    for name in sorted(overrides):
        print("  %-34s %s" % (name, json.dumps(overrides[name], ensure_ascii=False)))
    print()

    if not wanted:
        print("（只列 override。想看成品的节点内容，把节点名也传进来。）")
        return 0

    # v5 的 Resource 有 get_node_data，能把 override 合并之后的最终内容读出来。
    # v4.3.2 没有这个方法，所以老版本上只能看 override 原文。
    if not hasattr(resource, "get_node_data"):
        print("[!!] 这个 maafw 版本没有 Resource.get_node_data（v5 起才有），只能看上面的 override")
        return 0

    for name in wanted:
        data = resource.get_node_data(name)
        print("== %s ==" % name)
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
