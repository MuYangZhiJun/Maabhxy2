#!/usr/bin/env python3
"""模板体检：把每个模板对着手里所有原生截图扫一遍，按分数排出来。

为什么需要它：模板失效是**静默**的 —— 节点不报错，只是永远不命中，
整条链安静地掉到收尾，表现出来就是"这个模块没干活"。
踩过：`日常/多元裂缝.png` 被误判成"废图"，其实是列表滚动位置的问题；
反过来也可能有真废的模板一直没人发现。

判据：
    最高分 >= 0.95   健康（至少在某张截图上是干净的）
    0.90 ~ 0.95      将就（阈值 0.85 能过，但没余量）
    < 0.90           可疑 —— 要么模板裁歪了/混了会动的东西，要么只是**没截到对应界面**
    （注意：从没出现过 ≠ 坏。输出里会把"最高分在哪张图上"打出来，好人工判断。）

用法：
    python tools/template_health.py
    python tools/template_health.py --shots debug/shots --shots debug/al
    python tools/template_health.py --below 0.95      # 只看低于这个分的
"""

import argparse
import glob
import hashlib
import os
import sys

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")
DEFAULT_SHOT_DIRS = ["debug/shots", "debug/al", "debug/mail", "debug/cz", "debug/scan"]


def rd(path):
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def collect_shots(dirs):
    """收集原生截图，按内容去重（我一次会话里很多张是重复的）。"""
    out = {}
    for d in dirs:
        path = d if os.path.isabs(d) else os.path.join(ROOT, d)
        for f in sorted(glob.glob(os.path.join(path, "*.png"))):
            try:
                data = open(f, "rb").read()
            except OSError:
                continue
            key = hashlib.sha256(data).hexdigest()
            if key in out:
                continue
            img = rd(f)
            # 只收 1280x720 的原生截图；别把用户给的窗口截图混进来污染分数
            if img is None or img.shape[1] != 1280 or img.shape[0] != 720:
                continue
            out[key] = (f, img)
    return list(out.values())


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="模板体检")
    parser.add_argument("--shots", action="append", default=None,
                        help="截图目录，可给多个（默认扫 debug/ 下几个目录）")
    parser.add_argument("--below", type=float, default=1.01,
                        help="只列出低于这个分数的模板，默认全列")
    parser.add_argument("--max-shots", type=int, default=60,
                        help="最多用多少张截图（全量扫太慢，默认 60 张，够用了）")
    args = parser.parse_args()

    shots = collect_shots(args.shots or DEFAULT_SHOT_DIRS)
    if len(shots) > args.max_shots:
        # 均匀抽样，别只取前 N 张（前面往往是同一个流程的连拍）
        step = len(shots) / float(args.max_shots)
        shots = [shots[int(i * step)] for i in range(args.max_shots)]
    print("原生截图 %d 张（已按内容去重 + 抽样）" % len(shots))
    if not shots:
        print("[!!] 一张原生截图都没有，先 adb 抓几张")
        return 1

    rows = []
    for root, _dirs, files in os.walk(IMAGE_DIR):
        for f in sorted(files):
            if not f.lower().endswith(".png"):
                continue
            path = os.path.join(root, f)
            rel_check = os.path.relpath(path, IMAGE_DIR).replace("\\", "/")
            if rel_check.startswith("_raw/") or "/_raw/" in rel_check:
                continue  # _raw 是原始素材（整屏截图），不是模板，别参与体检
            rel = rel_check
            t = rd(path)
            if t is None:
                continue
            best = None
            for shot_path, img in shots:
                if t.shape[0] > img.shape[0] or t.shape[1] > img.shape[1]:
                    continue
                res = cv2.matchTemplate(img, t, cv2.TM_CCOEFF_NORMED)
                _, value, _, loc = cv2.minMaxLoc(res)
                if best is None or value > best[0]:
                    best = (float(value), os.path.basename(shot_path),
                            (int(loc[0]), int(loc[1])))
            rows.append((rel, t.shape[1], t.shape[0], best))

    rows.sort(key=lambda r: (r[3][0] if r[3] else -1))
    print()
    print("%-34s %-9s %-8s %s" % ("模板", "尺寸", "最高分", "在哪张 / 位置"))
    print("-" * 88)
    for rel, w, h, best in rows:
        if best is None:
            print("%-34s %-9s %-8s %s" % (rel, "%dx%d" % (w, h), "--", "尺寸太大，没试"))
            continue
        if best[0] > args.below:
            continue
        mark = "很稳" if best[0] >= 0.95 else ("将就" if best[0] >= 0.90 else "可疑")
        print("%-34s %-9s %.4f %-4s %s @%s"
              % (rel, "%dx%d" % (w, h), best[0], mark, best[1], best[2]))

    weak = [r for r in rows if r[3] and r[3][0] < 0.90]
    ok = [r for r in rows if r[3] and r[3][0] >= 0.95]
    print()
    print("合计 %d 张：很稳 %d，可疑 %d（可疑的要么裁坏了，要么只是没截到对应界面，"
          "看「在哪张」那一列人工判断）。" % (len(rows), len(ok), len(weak)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
