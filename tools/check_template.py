#!/usr/bin/env python3
"""给模板图实测打分（用 OpenCV，和 MaaFramework 的 TemplateMatch 同一套原理）。

用途：裁完模板别靠眼睛判断"应该能认出来"，先量一下分数。
    >= 0.95  很稳，threshold 可以放 0.85
    0.85~0.95 能用，threshold 放 0.8 左右
    < 0.85   不可靠，多半是模板里混进了会动的东西（动画、光效、数字）
             或者裁歪了，重裁

连拍多张同一界面再逐个打分，就能判断模板里有没有混进动画 ——
分数抖动大 = 那张图在动，得换一张静态的当锚点。

用法：
    python tools/check_template.py 首页/出击.png
    python tools/check_template.py 启动/标题页.png --shots assets/resource/image/_raw/anim
    python tools/check_template.py 启动/标题页.png 启动/抚摸屏幕继续.png --live 6
"""

import argparse
import glob
import os
import struct
import subprocess
import sys
import time

import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")
RAW_DIR = os.path.join(IMAGE_DIR, "_raw")

sys.path.insert(0, os.path.join(ROOT, "tools"))

ADB_CANDIDATES = [
    r"E:\MuMu Player 12\shell\adb.exe",
    r"D:\MuMu Player 12\shell\adb.exe",
    r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
]
MUMU_PORTS = [16384, 16416, 16448, 16480]


def imread_unicode(path):
    """cv2.imread 在 Windows 上读不了中文路径，绕一下。"""
    try:
        data = np.fromfile(path, dtype=np.uint8)
    except OSError:
        return None
    if data.size == 0:
        return None
    return cv2.imdecode(data, cv2.IMREAD_COLOR)


def find_adb():
    for candidate in ADB_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    import shutil

    return shutil.which("adb")


def capture_live(count, interval=1.0):
    """连拍 count 张，返回文件路径列表。"""
    adb = find_adb()
    if adb is None:
        print("找不到 adb，没法连拍")
        return []
    out_dir = os.path.join(RAW_DIR, "anim")
    os.makedirs(out_dir, exist_ok=True)
    for old in glob.glob(os.path.join(out_dir, "*.png")):
        os.remove(old)

    device = None
    for port in MUMU_PORTS:
        out = subprocess.run([adb, "connect", f"127.0.0.1:{port}"],
                             capture_output=True, text=True, timeout=20).stdout
        if "connected" in out:
            device = f"127.0.0.1:{port}"
            break
    if device is None:
        print("没有设备在线")
        return []

    shots = []
    for index in range(count):
        target = os.path.join(out_dir, f"shot_{index + 1}.png")
        data = subprocess.run([adb, "-s", device, "exec-out", "screencap", "-p"],
                              capture_output=True, timeout=30).stdout
        with open(target, "wb") as handle:
            handle.write(data)
        shots.append(target)
        if index + 1 < count:
            time.sleep(interval)
    return shots


def score_one(shot_path, template_path, roi=None):
    shot = imread_unicode(shot_path)
    template = imread_unicode(template_path)
    if shot is None:
        return None
    if template is None:
        return None

    if roi:
        x, y, w, h = roi
        shot = shot[y:y + h, x:x + w]

    if template.shape[0] > shot.shape[0] or template.shape[1] > shot.shape[1]:
        return None

    result = cv2.matchTemplate(shot, template, cv2.TM_CCOEFF_NORMED)
    _, best, _, location = cv2.minMaxLoc(result)
    offset_x = roi[0] if roi else 0
    offset_y = roi[1] if roi else 0
    return float(best), (location[0] + offset_x, location[1] + offset_y)


def verdict(score):
    if score >= 0.95:
        return "很稳"
    if score >= 0.85:
        return "能用"
    return "不可靠"


# 用户给的截图常常是 MuMu 窗口尺寸（1467x825），从它裁出来的模板在原生
# 1280x720 上会静默掉到 0.5 左右 —— 看着像"模板坏了"，其实是比例不对（坑 37）。
# 这里在分数低的时候自动试几个常见比例，能救回来就明确喊出来。
_WINDOW_SCALES = [
    (1280 / 1467, "1467x825 窗口 -> 1280x720"),
    (1467 / 1280, "1280x720 -> 1467x825"),
    (1920 / 1280, "1280 -> 1920"),
]


def diagnose_scale(shot_path, template_path):
    """返回 (救回来的比例说明, 缩放后的分数) 或 None。"""
    shot = imread_unicode(shot_path)
    template = imread_unicode(template_path)
    if shot is None or template is None:
        return None
    if template.shape[0] > shot.shape[0] or template.shape[1] > shot.shape[1]:
        # 先按比例缩小再看
        pass
    best = None
    for factor, label in _WINDOW_SCALES:
        scaled = cv2.resize(template, None, fx=factor, fy=factor,
                            interpolation=cv2.INTER_AREA)
        if scaled.shape[0] > shot.shape[0] or scaled.shape[1] > shot.shape[1]:
            continue
        result = cv2.matchTemplate(shot, scaled, cv2.TM_CCOEFF_NORMED)
        _, value, _, _ = cv2.minMaxLoc(result)
        if best is None or value > best[1]:
            best = (label, float(value))
    if best and best[1] >= 0.95:
        return best
    return None


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="模板匹配打分")
    parser.add_argument("templates", nargs="+", help="模板路径（相对 assets/resource/image/）")
    parser.add_argument("--shots", default=None, help="截图文件或目录，默认用 _raw 里最新那张")
    parser.add_argument("--live", type=int, default=0, help="先连拍 N 张再打分")
    args = parser.parse_args()

    if args.live:
        shots = capture_live(args.live)
        if not shots:
            return
    elif args.shots:
        shots = ([args.shots] if os.path.isfile(args.shots)
                 else sorted(glob.glob(os.path.join(args.shots, "*.png"))))
    else:
        candidates = [p for p in glob.glob(os.path.join(RAW_DIR, "*.png"))]
        if not candidates:
            print("_raw 里没有截图，先跑 tools/capture.py shoot")
            return
        shots = [max(candidates, key=os.path.getmtime)]

    for name in args.templates:
        path = name if os.path.isabs(name) else os.path.join(IMAGE_DIR, name)
        template = imread_unicode(path)
        if template is None:
            print(f"[!!] 读不到模板 {name}")
            continue
        th, tw = template.shape[:2]
        print(f"\n=== {name}  ({tw}x{th}) ===")
        scores = []
        for shot in shots:
            result = score_one(shot, path)
            if result is None:
                print(f"  {os.path.basename(shot):<22} 匹配不了（尺寸问题？）")
                continue
            best, location = result
            scores.append(best)
            print(f"  {os.path.basename(shot):<22} {best:.4f}  {verdict(best):<6} 命中于 {location}")
        if scores:
            low, high = min(scores), max(scores)
            spread = high - low
            print(f"  ---- 最低 {low:.4f} / 平均 {sum(scores)/len(scores):.4f} / 最高 {high:.4f}"
                  f" / 抖动 {spread:.4f}")
            if len(scores) > 1 and spread > 0.05:
                print("  [!!] 抖动大 —— 模板里多半混进了会动的东西，换一张静态的当锚点")
            if low >= 0.95:
                print("  [OK] 建议 threshold 0.85")
            elif low >= 0.85:
                print("  [OK] 建议 threshold 0.80")
            else:
                print("  [!!] 分数太低，重裁")
                fixed = diagnose_scale(shots[0], path)
                if fixed:
                    label, value = fixed
                    print("  [!!] 但是 —— 按比例「%s」缩放后能打到 %.4f！"
                          % (label, value))
                    print("       这不是模板坏了，是**比例不对**（坑 37）。"
                          "把它缩到 1280x720 再裁一遍，或者干脆用 adb 抓原生截图重裁。")


if __name__ == "__main__":
    main()
