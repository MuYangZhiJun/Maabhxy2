#!/usr/bin/env python3
"""核对发布 tag 和 interface.json 里的 version 是否一致。

为什么要有这一步：MFAAvalonia 的「更新资源」是**读 interface.json 的 `version`**
来判断有没有新版本的 —— 如果打了 `v0.1.2` 的 tag 却忘了改 version（还写着 0.1.1），
别人点更新会以为"已经是最新"，收不到更新。

用法：
    python tools/check_version.py v0.1.0
    python tools/check_version.py            # 不传就只打印 version
"""

import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
    lines = [l for l in raw.splitlines() if not l.lstrip().startswith("//")]
    version = json.loads("\n".join(lines)).get("version", "")
    print("interface.json version = %r" % version)

    if len(sys.argv) < 2 or not sys.argv[1].strip():
        return 0
    tag = sys.argv[1].strip()
    print("tag = %r" % tag)
    if not version:
        print("[!!] interface.json 里没有 version 字段")
        return 1
    if tag == "v" + version or tag == version:
        print("一致 ✅")
        return 0
    print("[!!] 不一致 ✗ —— 打 tag 之前先把 interface.json 的 version 改成 %s"
          % (tag.lstrip("v")))
    print("     （不改的话，用「更新资源」的人会以为已经是最新，收不到这次更新）")
    return 1


if __name__ == "__main__":
    sys.exit(main())
