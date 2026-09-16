#!/usr/bin/env python3
"""给一张截图，说出它最像哪个界面（按模板匹配分数排序）。

用途：排查"游戏现在停在哪一屏"。没有 OCR 模型、或者看不了图的时候，
用已有模板反查是最快的办法 —— 分数最高的那几张模板就说明了当前界面。

用法：
    python tools/what_is_this.py debug/boot/f100.png
    python tools/what_is_this.py 截图.png --top 8
"""

import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")


def rd(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="这张截图是什么界面")
    ap.add_argument("shot")
    ap.add_argument("--top", type=int, default=6)
    args = ap.parse_args()

    path = args.shot if os.path.isabs(args.shot) else os.path.join(ROOT, args.shot)
    shot = rd(path)
    if shot is None:
        print("[!!] 读不到 %s" % path)
        return 1
    print("截图: %s  (%dx%d)" % (os.path.basename(path), shot.shape[1], shot.shape[0]))

    rows = []
    for root, _dirs, files in os.walk(IMAGE_DIR):
        rel_dir = os.path.relpath(root, IMAGE_DIR).replace("\\", "/")
        if rel_dir.startswith("_raw") or "/_raw" in rel_dir:
            continue
        for f in sorted(files):
            if not f.lower().endswith(".png"):
                continue
            t = rd(os.path.join(root, f))
            if t is None or t.shape[0] > shot.shape[0] or t.shape[1] > shot.shape[1]:
                continue
            res = cv2.matchTemplate(shot, t, cv2.TM_CCOEFF_NORMED)
            _, value, _, loc = cv2.minMaxLoc(res)
            name = ("%s/%s" % (rel_dir, f)) if rel_dir != "." else f
            rows.append((float(value), name, (int(loc[0]), int(loc[1]))))

    rows.sort(reverse=True)
    print("最像的几个界面:")
    for value, name, loc in rows[: args.top]:
        mark = "← 很稳" if value >= 0.95 else ("← 可能" if value >= 0.85 else "")
        print("   %.4f  %-34s @%s %s" % (value, name, loc, mark))
    if not rows:
        print("   （没有能比的模板）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
