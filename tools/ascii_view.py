#!/usr/bin/env python3
"""把截图变成字符画 —— 给"看不见图"的时候用。

背景：这个 agent 跑的是纯文本模型，`read_image` 直接报「不支持图片输入」，
所以排查界面只能靠模板匹配 + OCR 猜。但"这一屏长什么样、卡片在哪、按钮在哪"
其实用**亮度字符画**就能看个大概：

    python tools/ascii_view.py debug/live_d.png            # 整屏
    python tools/ascii_view.py debug/live_d.png --crop 100,200,400,200 --cols 100
    python tools/ascii_view.py debug/live_d.png --color    # 用色相区分（比亮度更能看出色块）

字符含义：空格=黑/暗，`.`=暗，`:`=偏暗，`+`=中间，`*`=亮，`#`=很亮/白。
每行左边的数字是**原图 y 坐标**，每 10 列标一次 x 坐标。
"""
import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAMP = " .:-=+*#%@"


def rd(path):
    data = np.fromfile(path, dtype=np.uint8)
    return cv2.imdecode(data, cv2.IMREAD_COLOR) if data.size else None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="截图转字符画")
    ap.add_argument("shot")
    ap.add_argument("--crop", help="只看这一块 x,y,w,h")
    ap.add_argument("--cols", type=int, default=110, help="字符画宽度（列数）")
    ap.add_argument("--color", action="store_true", help="按色相上字符（H/S/V 分档）")
    args = ap.parse_args()

    path = args.shot if os.path.isabs(args.shot) else os.path.join(ROOT, args.shot)
    img = rd(path)
    if img is None:
        print(f"[!!] 读不到 {path}")
        return 1
    ox, oy = 0, 0
    if args.crop:
        x, y, w, h = [int(v) for v in args.crop.split(",")]
        img = img[y:y + h, x:x + w]
        ox, oy = x, y
    H, W = img.shape[:2]

    cols = max(20, args.cols)
    rows = max(6, int(cols * (H / float(W)) * 0.5))  # 字符高宽比约 2:1
    small = cv2.resize(img, (cols, rows), interpolation=cv2.INTER_AREA)

    if args.color:
        hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
        hue, sat, val = hsv[:, :, 0], hsv[:, :, 1], hsv[:, :, 2]
        # 低饱和 = 灰/黑/白，用亮度档；高饱和按色相给字母
        out = []
        for r in range(rows):
            line = []
            for c in range(cols):
                if sat[r, c] < 60 or val[r, c] < 60:
                    line.append(RAMP[min(len(RAMP) - 1, int(val[r, c] / 25.6))])
                else:
                    hh = hue[r, c]
                    if hh < 10 or hh >= 170:
                        line.append("R")     # 红
                    elif hh < 25:
                        line.append("O")     # 橙
                    elif hh < 40:
                        line.append("Y")     # 黄
                    elif hh < 85:
                        line.append("G")     # 绿
                    elif hh < 130:
                        line.append("C")     # 青
                    elif hh < 170:
                        line.append("B")     # 蓝
                    else:
                        line.append("P")
            out.append("".join(line))
    else:
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        out = ["".join(RAMP[min(len(RAMP) - 1, int(v / 25.6))] for v in row)
               for row in gray]

    sx = W / float(cols)
    sy = H / float(rows)
    print(f"{os.path.basename(path)}  原图 {W}x{H}（crop 起点 {ox},{oy}）"
          f"  每字符 ≈ {sx:.0f}x{sy:.0f} 像素")
    header = " " * 6 + "".join(
        ("|" if (i % 10 == 0) else " ") for i in range(cols))
    print(header)
    for i, line in enumerate(out):
        y = oy + int(i * sy + sy / 2)
        print("%5d " % y + line)
    # 底部再标一次 x，方便对坐标
    ticks = [" "] * cols
    for i in range(0, cols, 10):
        label = str(ox + int(i * sx))
        for j, ch in enumerate(label):
            if i + j < cols:
                ticks[i + j] = ch
    print(" " * 6 + "".join(ticks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
