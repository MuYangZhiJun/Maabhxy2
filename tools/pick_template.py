#!/usr/bin/env python3
"""候选模板 vs 现有模板：拿同一张原生截图比分数，决定该不该换。

为什么需要它：用户/合作方给的图常是 MuMu 窗口尺寸（1467x825），
直接拿来当模板会静默掉到 0.5 左右；或者裁的范围和现有模板不一样（只裁文字 vs 连按钮一起裁）。
光看尺寸和肉眼判断不出来，必须**在原生 1280x720 截图上量**。

用法：
    # 单个候选：跟现有模板比
    python tools/pick_template.py --shots debug/shots/hd0_before.png \
        --candidate debug/ref/u07.png --current 日常/选择助战好友.png

    # 批量：一条 --candidate 一张图，--current 留空就只量候选自己
    python tools/pick_template.py --shots debug/shots/b6_support.png \
        --candidate debug/ref/u05.png --candidate debug/ref/u05b.png

输出里：
    原样    = 候选图直接拿去匹配
    缩回    = 按 1280/图宽 ~ 1467/1280 这几种常见窗口比例试一遍，取最好的那个
    对位    = 命中位置（跟现有模板的命中位置应该基本重合，差太多说明裁的不是同一块）
结论：
    缩回能到 0.95+ 而原样不行  → 比例问题，别当模板坏了
    原样就 0.95+               → 可以直接用
    怎么试都上不去             → 这张图根本不适合作模板（裁歪了 / 混进了会动的东西）
"""

import argparse
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")

SCALES = [
    (1280 / 1467, "1467->1280"),
    (1467 / 1280, "1280->1467"),
    (1920 / 1280, "1280->1920"),
]


def rd(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def best_match(shot, tmpl):
    if tmpl is None or shot is None:
        return None
    if tmpl.shape[0] > shot.shape[0] or tmpl.shape[1] > shot.shape[1]:
        return None
    res = cv2.matchTemplate(shot, tmpl, cv2.TM_CCOEFF_NORMED)
    _, value, _, loc = cv2.minMaxLoc(res)
    return float(value), (int(loc[0]), int(loc[1]))


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="候选模板 vs 现有模板，同一张截图比分数")
    parser.add_argument("--shots", required=True, help="原生截图（1280x720）")
    parser.add_argument("--candidate", action="append", default=[],
                        help="候选图路径，可以给多个")
    parser.add_argument("--current", action="append", default=[],
                        help="现有模板（相对 assets/resource/image/），可给多个")
    args = parser.parse_args()

    shot_path = args.shots
    if not os.path.isabs(shot_path):
        shot_path = os.path.join(ROOT, shot_path)
    shot = rd(shot_path)
    if shot is None:
        print("[!!] 读不到截图 %s" % shot_path)
        return 1
    print("截图: %s  (%dx%d)" % (os.path.basename(shot_path),
                                 shot.shape[1], shot.shape[0]))

    for name in args.current:
        path = name if os.path.isabs(name) else os.path.join(IMAGE_DIR, name)
        t = rd(path)
        if t is None:
            print("[!!] 读不到现有模板 %s" % name)
            continue
        got = best_match(shot, t)
        print("\n[现有] %-34s %dx%d  %s"
              % (name, t.shape[1], t.shape[0],
                 ("%.4f  @%s" % got) if got else "尺寸不匹配"))

    for path in args.candidate:
        if not os.path.isabs(path):
            path = os.path.join(ROOT, path)
        t = rd(path)
        if t is None:
            print("\n[!!] 读不到候选 %s" % path)
            continue
        print("\n[候选] %-34s %dx%d" % (os.path.basename(path), t.shape[1], t.shape[0]))
        got = best_match(shot, t)
        print("   原样: %s" % (("%.4f  @%s" % got) if got else "尺寸不匹配"))
        best = None
        for factor, label in SCALES:
            sc = cv2.resize(t, None, fx=factor, fy=factor, interpolation=cv2.INTER_AREA)
            g = best_match(shot, sc)
            if g and (best is None or g[0] > best[1][0]):
                best = (label, g, sc.shape[1], sc.shape[0])
        if best:
            label, g, w, h = best
            print("   缩回(%s -> %dx%d): %.4f  @%s" % (label, w, h, g[0], g[1]))
            if g[0] >= 0.95 and (got is None or got[0] < 0.95):
                print("   → 结论：**比例不对**，把图缩到 1280x720 再裁（坑 37）")
            elif got and got[0] >= 0.95:
                print("   → 结论：原样就能用（%.4f），可以直接换" % got[0])
            else:
                print("   → 结论：怎么试都上不去，这张图不适合作模板")
        else:
            print("   → 结论：尺寸都对不上，用不了")
    return 0


if __name__ == "__main__":
    sys.exit(main())
