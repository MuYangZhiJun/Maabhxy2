#!/usr/bin/env python3
"""把一张截图上的**文字**读出来（带坐标）。

为什么需要它：这台机器上的 agent 是**瞎**的 —— 只会模板匹配，认不到就只会
"没命中、等 20 秒、判失败"。以前排查"卡在哪一屏"唯一的办法是把模板挨个扫一遍，
但模板只能告诉你"这里有我认识的东西"，说不出**这一屏到底写着什么**。
有了 OCR，`python tools/read_screen.py debug/now.png` 就能直接看到屏幕上的字。

⚠️ 这只是**开发/排查工具**，pipeline 不依赖它：
   依赖 `rapidocr-onnxruntime`（自带模型，pip 装完就能离线跑），
   没装的话这个脚本会提示怎么装，不影响正常跑任务。

用法：
    python tools/read_screen.py debug/now.png          # 读一张截图
    python tools/read_screen.py --live                 # 直接抓模拟器现在这一屏
    python tools/read_screen.py 图.png --min-score 0.6 # 分数低的也打出来
"""

import argparse
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_CANDIDATES = [
    r"E:\MuMu Player 12\nx_main\adb.exe",
    r"E:\MuMu Player 12\shell\adb.exe",
]
DEFAULT_ADDRESS = "127.0.0.1:16384"


def grab_live(address=DEFAULT_ADDRESS):
    """抓一屏到临时文件，返回路径。"""
    adb = next((c for c in ADB_CANDIDATES if os.path.isfile(c)), "adb")
    remote = "/sdcard/_read_screen.png"
    out = os.path.join(tempfile.gettempdir(), "_read_screen.png")
    subprocess.run([adb, "-s", address, "shell", "screencap", "-p", remote],
                   check=True, capture_output=True)
    subprocess.run([adb, "-s", address, "pull", remote, out],
                   check=True, capture_output=True)
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="读屏幕上的字")
    ap.add_argument("shot", nargs="?", help="截图路径")
    ap.add_argument("--live", action="store_true", help="直接抓模拟器当前画面")
    ap.add_argument("--address", default=DEFAULT_ADDRESS)
    ap.add_argument("--min-score", type=float, default=0.5, help="低于这个置信度不打印")
    ap.add_argument("--tap", nargs=2, type=int, metavar=("X", "Y"),
                    help="先点一下这个坐标再抓图（省得 adb 一条条敲）")
    ap.add_argument("--wait", type=float, default=2.5, help="--tap 之后等几秒再抓")
    ap.add_argument("--save", help="把抓到的图另存一份到这个路径（留证据）")
    ap.add_argument("--crop", help="只读这一块 x,y,w,h（按钮上的小字这样读得准）")
    args = ap.parse_args()

    if not args.shot and not args.live and not args.tap:
        ap.error("要么给截图路径，要么加 --live")

    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError:
        print("[!!] 没装 rapidocr-onnxruntime。装一下就能用：")
        print("     python -m pip install rapidocr-onnxruntime")
        return 1

    if args.tap:
        adb = next((c for c in ADB_CANDIDATES if os.path.isfile(c)), "adb")
        print(f"点 ({args.tap[0]},{args.tap[1]})")
        subprocess.run([adb, "-s", args.address, "shell", "input", "tap",
                        str(args.tap[0]), str(args.tap[1])], check=False)
        time.sleep(args.wait)
        args.live = True

    path = grab_live(args.address) if args.live else (
        args.shot if os.path.isabs(args.shot) else os.path.join(ROOT, args.shot))
    if not os.path.isfile(path):
        print(f"[!!] 找不到 {path}")
        return 1
    if args.save:
        import shutil
        dst = args.save if os.path.isabs(args.save) else os.path.join(ROOT, args.save)
        shutil.copyfile(path, dst)
        print(f"图已存: {dst}")
    print(f"读图: {path}")

    engine = RapidOCR()
    target = path
    offset = (0, 0)
    scale = 1.0
    if args.crop:
        import cv2
        import numpy as np
        x, y, w, h = [int(v) for v in args.crop.split(",")]
        data = np.fromfile(path, dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            print("[!!] 读不到图，裁不了")
            return 1
        patch = img[y:y + h, x:x + w]
        # 放大 2 倍再 OCR：小字号（按钮上的字）不放大识别率很差
        patch = cv2.resize(patch, None, fx=2.0, fy=2.0, interpolation=cv2.INTER_CUBIC)
        scale = 2.0
        target = os.path.join(tempfile.gettempdir(), "_read_screen_crop.png")
        # ⚠️ cv2.imwrite 写不了非 ASCII 路径（这台机器用户名是中文，临时目录直接踩雷），
        #    必须自己编码再 tofile —— 项目里其他工具也是这么绕的。
        ok, buf = cv2.imencode(".png", patch)
        if not ok:
            print("[!!] 裁出来的图编码失败")
            return 1
        buf.tofile(target)
        offset = (x, y)
        print(f"只看这一块: ({x},{y}) {w}x{h}（坐标已换算回原图）")

    result, _elapse = engine(target)
    if not result:
        print("（一个字都没读出来）")
        return 0

    rows = []
    for item in result:
        box, text, score = item[0], item[1], float(item[2])
        if score < args.min_score:
            continue
        xs = [p[0] / scale + offset[0] for p in box]
        ys = [p[1] / scale + offset[1] for p in box]
        rows.append((min(ys), min(xs), max(xs) - min(xs), max(ys) - min(ys),
                     text, score))

    rows.sort()
    width = max((len(r[4]) for r in rows), default=1)
    print("%-21s %-8s %s" % ("位置(左上)", "尺寸", "文字"))
    print("-" * 70)
    for y, x, w, h, text, score in rows:
        print("(%4d,%4d)%13s %-8s %s  %.2f"
              % (x, y, "", "%dx%d" % (w, h), text.ljust(width), score))
    return 0


if __name__ == "__main__":
    sys.exit(main())
