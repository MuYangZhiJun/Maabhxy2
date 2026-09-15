#!/usr/bin/env python3
"""检查打出来的发布包干不干净。

发布包是要给人下载的，所以两件事必须在打包后立刻验：
  1. **不能混进隐私/调试文件** —— `image/_raw/`（原始整屏截图，含玩家头像、昵称、ID）、
     `debug/`（调试截图）、`config/`（本机配置）、`*.bak_*`（备份图）
  2. **该有的东西得在** —— interface.json、resource/pipeline、agent、模板图

踩过：`主界面.png.bak_personal`（含玩家头像的旧模板）被误提交进仓库；
所以发布前的自动检查必须有，别指望人眼。

用法：
    python tools/check_package.py              # 检查 dist/ 下所有 zip
    python tools/check_package.py dist/xxx.zip  # 检查指定包
"""

import glob
import os
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BAD_PATTERNS = [
    "_raw/",           # 原始整屏截图
    "/debug/",         # 调试产物
    "/config/",        # 本机配置
    ".bak_personal",   # 含玩家头像的模板备份
    ".bak_",
    "__pycache__",
    ".pyc",
]

NEED_SUFFIXES = [
    "interface.json",
    "/resource/pipeline/",
    "/agent/main.py",
]

MIN_PNG = 20  # 模板图至少得有这么多张，少于此数说明打漏了


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    args = sys.argv[1:]
    if args:
        zips = args
    else:
        zips = sorted(glob.glob(os.path.join(ROOT, "dist", "*.zip")))
    if not zips:
        print("[!!] 没有找到 zip。先跑 python tools/package.py")
        return 1

    failed = False
    for path in zips:
        name = os.path.basename(path)
        try:
            with zipfile.ZipFile(path) as z:
                names = z.namelist()
        except Exception as exc:  # noqa: BLE001
            print("[!!] %s 打不开: %s" % (name, exc))
            failed = True
            continue

        bad = sorted({p for n in names for p in BAD_PATTERNS if p in n})
        pngs = [n for n in names if n.lower().endswith(".png")]
        missing = [s for s in NEED_SUFFIXES if not any(s in n for n in names)]

        size_mb = os.path.getsize(path) / 1024.0 / 1024.0
        verdict = "OK" if not bad and not missing and len(pngs) >= MIN_PNG else "有问题"
        print("%-34s %6.1f MB  %4d 条  模板图 %3d 张  -> %s"
              % (name, size_mb, len(names), len(pngs), verdict))
        if bad:
            print("      [!!] 混进了不该有的东西: %s" % bad)
            failed = True
        if missing:
            print("      [!!] 缺少必需内容: %s" % missing)
            failed = True
        if len(pngs) < MIN_PNG:
            print("      [!!] 模板图只有 %d 张（少于 %d），多半打漏了" % (len(pngs), MIN_PNG))
            failed = True

    print()
    print("结论:", "全部干净 ✅" if not failed else "有问题，别发布 ✗")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
