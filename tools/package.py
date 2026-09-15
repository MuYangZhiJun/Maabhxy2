#!/usr/bin/env python3
"""打发布包：把「资源 + agent」打成 MAA 生态通用的 zip。

为什么要单独打个包：别人拿到的不该是开发目录（里面有 debug 截图、deps、gui 构建产物、
还有 `config/` 里的账号痕迹）。发布包只要三样东西：

    bh2-maa-<版本>/
        interface.json      <- 任务与选项定义
        resource/           <- pipeline + 模板图 + model
        agent/              <- Python agent（自动战斗、刷关）

这个布局和仓库里的 `assets/` 是对应的：MFAAvalonia 的「更新资源」直接吃仓库 zip，
所以仓库本身也能当更新源（见 PUBLISH.md）。

用法：
    python tools/package.py                 # 出 dist/bh2-maa-<版本>.zip
    python tools/package.py --with-tools    # 额外出「能自己构建 GUI」的完整源码包
"""

import argparse
import json
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_NAMES = {".git", "__pycache__", "debug", "deps", "gui", "MFA", ".downloads", "config",
              # `_raw` 是裁模板用的原始整屏截图：又大、又带着玩家头像/昵称/ID，
              # 绝对不能进发布包（.gitignore 里也是排除的）。
              "_raw"}


def read_interface():
    path = os.path.join(ROOT, "assets", "interface.json")
    raw = open(path, encoding="utf-8").read()
    lines = [l for l in raw.splitlines() if not l.lstrip().startswith("//")]
    return json.loads("\n".join(lines))


def add_tree(zf, src_dir, arc_prefix):
    """把一个目录塞进 zip（跳过临时/构建产物）。"""
    added = 0
    for root, dirs, files in os.walk(src_dir):
        dirs[:] = [d for d in dirs if d not in SKIP_NAMES and d != "__pycache__"]
        for f in sorted(files):
            if f.endswith((".pyc", ".pyo", ".bak")) or f.endswith(".bak_personal"):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, src_dir).replace("\\", "/")
            zf.write(path, "%s/%s" % (arc_prefix, rel))
            added += 1
    return added


def add_file(zf, path, arc):
    if os.path.isfile(path):
        zf.write(path, arc)
        return 1
    return 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="打发布包")
    parser.add_argument("--with-tools", action="store_true",
                        help="额外打一个完整源码包（含 tools/ 和 README，能自己构建 GUI）")
    args = parser.parse_args()

    iface = read_interface()
    version = iface.get("version", "0.0.0")
    name = "bh2-maa-%s" % version
    dist = os.path.join(ROOT, "dist")
    os.makedirs(dist, exist_ok=True)

    # 1) 资源包（MAA 生态通用：interface.json + resource/ + agent/）
    res_zip = os.path.join(dist, name + ".zip")
    with zipfile.ZipFile(res_zip, "w", zipfile.ZIP_DEFLATED) as zf:
        n1 = add_file(zf, os.path.join(ROOT, "assets", "interface.json"), name + "/interface.json")
        n2 = add_tree(zf, os.path.join(ROOT, "assets", "resource"), name + "/resource")
        n3 = add_tree(zf, os.path.join(ROOT, "agent"), name + "/agent")
    size = os.path.getsize(res_zip) / 1024.0 / 1024.0
    print("资源包: %s  (%.1f MB)  interface=%d resource=%d agent=%d"
          % (os.path.relpath(res_zip, ROOT), size, n1, n2, n3))

    # 2) 完整源码包（给想自己构建的人）
    if args.with_tools:
        src_zip = os.path.join(dist, name + "-source.zip")
        with zipfile.ZipFile(src_zip, "w", zipfile.ZIP_DEFLATED) as zf:
            for item in ("assets", "agent", "tools", "docs"):
                p = os.path.join(ROOT, item)
                if os.path.isdir(p):
                    add_tree(zf, p, name + "/" + item)
            for item in ("README.md", "HANDOFF.md", "LICENSE", "package.json",
                         "maatools.config.mts"):
                add_file(zf, os.path.join(ROOT, item), name + "/" + item)
        size = os.path.getsize(src_zip) / 1024.0 / 1024.0
        print("源码包: %s  (%.1f MB)" % (os.path.relpath(src_zip, ROOT), size))

    print()
    print("发布检查清单（每次发版前过一遍）：")
    print("  1. interface.json 的 github 字段指向你自己的仓库（不是 MaaXYZ 模板）")
    print("  2. version 已经往上加（MFAAvalonia 靠它判断有没有新版本）")
    print("  3. 模板图里没有个人隐私（头像/昵称/ID/等级）—— 尤其是信息板那一块")
    print("  4. debug/ 和 config/ 没进 git（.gitignore 里有）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
