#!/usr/bin/env python3
"""把截图裁一块出来放大看（标定坐标时用）。

标坐标的老办法是眯着眼看全屏截图里的预览图，估出来的数经常差几十像素
（踩过：把 300 宽的选择助战好友按钮估成了 216 宽）。裁出来放大看就准了。

用法：
    python tools/crop.py debug/shots/x.png 240 192 444 150 out.png
    python tools/crop.py debug/shots/x.png 240 192 444 150 out.png --scale 2
    python tools/crop.py debug/shots/x.png 240 192 444 150 out.png --grid 20
"""

import argparse
import os
import sys

import cv2
import numpy as np


def imread_unicode(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def imwrite_unicode(path, image):
    ext = os.path.splitext(path)[1] or ".png"
    ok, buf = cv2.imencode(ext, image)
    if not ok:
        return False
    buf.tofile(path)
    return True


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="裁剪截图并放大")
    parser.add_argument("image")
    parser.add_argument("x", type=int)
    parser.add_argument("y", type=int)
    parser.add_argument("w", type=int)
    parser.add_argument("h", type=int)
    parser.add_argument("out")
    parser.add_argument("--scale", type=float, default=2.0)
    parser.add_argument("--grid", type=int, default=0,
                        help="每隔 N 像素画一条网格线（原图坐标）")
    args = parser.parse_args()

    image = imread_unicode(args.image)
    if image is None:
        print(f"[!!] 读不到 {args.image}")
        return 1

    height, width = image.shape[:2]
    x0 = max(0, args.x)
    y0 = max(0, args.y)
    x1 = min(width, args.x + args.w)
    y1 = min(height, args.y + args.h)
    if x1 <= x0 or y1 <= y0:
        print(f"[!!] 裁出来的区域是空的（原图 {width}x{height}）")
        return 1

    crop = image[y0:y1, x0:x1].copy()

    if args.grid > 0:
        step = args.grid
        for gx in range(x0 - x0 % step, x1, step):
            if gx >= x0:
                cv2.line(crop, (gx - x0, 0), (gx - x0, crop.shape[0]), (0, 0, 255), 1)
        for gy in range(y0 - y0 % step, y1, step):
            if gy >= y0:
                cv2.line(crop, (0, gy - y0), (crop.shape[1], gy - y0), (0, 0, 255), 1)

    if args.scale != 1.0:
        crop = cv2.resize(crop, None, fx=args.scale, fy=args.scale,
                          interpolation=cv2.INTER_NEAREST)

    if not imwrite_unicode(args.out, crop):
        print(f"[!!] 写不了 {args.out}")
        return 1

    print(f"裁出 ({x0},{y0})-({x1},{y1})  {x1 - x0}x{y1 - y0}"
          f"  ->  {args.out}  ({crop.shape[1]}x{crop.shape[0]})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
