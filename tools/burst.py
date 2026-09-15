#!/usr/bin/env python3
"""连拍模拟器画面，落成一串带时间戳的文件。

跑任务的时候它最有用的地方：pipeline 的节点日志只告诉你「哪个节点没命中」，
不告诉你「当时屏幕上到底是什么」。后台开着这个，跑完再翻帧，
就能看到流程是在哪一屏跑偏的（踩过：开战节点没命中，一直以为是坐标错，
其实是好友面板还没滑出来）。

用法：
    python tools/burst.py                        # 每 1.5 秒一张，拍 120 秒
    python tools/burst.py --interval 1.0 --seconds 90
    python tools/burst.py --out debug/burst/run1
"""

import argparse
import os
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ADB_CANDIDATES = [
    r"E:\MuMu Player 12\nx_main\adb.exe",
    r"E:\MuMu Player 12\shell\adb.exe",
    r"D:\MuMu Player 12\shell\adb.exe",
]
ADDRESS = "127.0.0.1:16384"


def find_adb():
    for candidate in ADB_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    import shutil

    return shutil.which("adb")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="连拍模拟器画面")
    parser.add_argument("--interval", type=float, default=1.5, help="间隔秒数")
    parser.add_argument("--seconds", type=float, default=120.0, help="总时长秒数")
    parser.add_argument("--out", default=os.path.join("debug", "burst"), help="输出目录")
    parser.add_argument("--address", default=ADDRESS)
    args = parser.parse_args()

    adb = find_adb()
    if not adb:
        print("[!!] 找不到 adb")
        return 1

    out_dir = args.out if os.path.isabs(args.out) else os.path.join(ROOT, args.out)
    os.makedirs(out_dir, exist_ok=True)

    start = time.monotonic()
    index = 0
    while time.monotonic() - start < args.seconds:
        elapsed = time.monotonic() - start
        index += 1
        target = os.path.join(out_dir, "f%03d_%05.1fs.png" % (index, elapsed))
        data = subprocess.run(
            [adb, "-s", args.address, "exec-out", "screencap", "-p"],
            capture_output=True, timeout=30,
        ).stdout
        if data:
            with open(target, "wb") as handle:
                handle.write(data)
        else:
            print("[!!] 第 %d 张没抓到" % index)
        time.sleep(max(0.0, args.interval - (time.monotonic() - start - elapsed)))

    print("拍了 %d 张 -> %s" % (index, out_dir))
    return 0


if __name__ == "__main__":
    sys.exit(main())
