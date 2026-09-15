#!/usr/bin/env python3
"""崩坏学园2 小助手 —— 截图 / 采模板小工具。

整个项目的模板图都靠这个工具产出：先 shoot 一张全屏截图，再按 tools/templates.json
里登记的坐标裁出模板，存到 assets/resource/image/ 下对应的路径。

用法：
    python tools/capture.py devices              # 看看连上模拟器没
    python tools/capture.py pkg                  # 查当前前台应用的包名（拿去填 interface.json）
    python tools/capture.py shoot                # 存一张全屏截图到 image/_raw/
    python tools/capture.py list                 # 打印模板清单，标出还缺哪几张
    python tools/capture.py crop 首页/出击.png 60 380 220 90
                                                 # 从最新截图裁一块出来存成该模板

crop 的 x y w h 都按 1280x720 的坐标系写（模拟器分辨率必须是 1280x720 横屏）。
想要更直观的框选，用 MaaFramework 自带的 ImageCropper 或 MaaDebugger，见 README。
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")
RAW_DIR = os.path.join(IMAGE_DIR, "_raw")
MANIFEST = os.path.join(ROOT, "tools", "templates.json")

ADB_CANDIDATES = [
    r"E:\MuMu Player 12\shell\adb.exe",
    r"D:\MuMu Player 12\shell\adb.exe",
    r"C:\Program Files\Netease\MuMuPlayer-12.0\shell\adb.exe",
    r"C:\Program Files\Netease\MuMuPlayer-12.0\vmonitor\bin\adb_server.exe",
    r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe",
    r"D:\Program Files\BlueStacks_nxt\HD-Adb.exe",
    r"C:\LDPlayer\LDPlayer9\adb.exe",
    r"D:\LDPlayer\LDPlayer9\adb.exe",
    r"C:\Program Files\Nox\bin\adb.exe",
]

# MuMu 12 的 adb 端口：第一个实例 16384，往后每个 +32
MUMU_PORTS = [16384, 16416, 16448, 16480]


def find_adb():
    found = shutil.which("adb")
    if found:
        return found
    for candidate in ADB_CANDIDATES:
        if os.path.isfile(candidate):
            return candidate
    return None


def run_adb(adb, args, binary=False):
    proc = subprocess.run([adb] + args, capture_output=True, timeout=60)
    if proc.returncode != 0:
        message = proc.stderr.decode("utf-8", "replace").strip()
        raise RuntimeError(f"adb {' '.join(args)} 失败: {message or proc.returncode}")
    return proc.stdout if binary else proc.stdout.decode("utf-8", "replace")


def require_adb():
    adb = find_adb()
    if adb is None:
        print("没找到 adb。装 platform-tools 丢进 PATH，或用模拟器自带的那份（MuMu 12 在 shell\\adb.exe）。")
        sys.exit(1)
    return adb


def connected_devices(adb):
    out = run_adb(adb, ["devices"])
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            found.append(parts[0])
    return found


def ensure_device(adb):
    """没设备就照着 MuMu 的端口连一遍。"""
    devices = connected_devices(adb)
    if devices:
        return devices
    for port in MUMU_PORTS:
        address = f"127.0.0.1:{port}"
        try:
            out = run_adb(adb, ["connect", address])
        except RuntimeError:
            continue
        if "connected" in out:
            print(f"已连接模拟器 {address}")
            devices = connected_devices(adb)
            if devices:
                return devices
    return []


def require_device(adb):
    devices = ensure_device(adb)
    if not devices:
        print("没有设备在线：先把模拟器打开，再跑一次。")
        print(f"手动排查: {adb} devices")
        sys.exit(1)
    return devices[0]


def cmd_devices(_args):
    adb = require_adb()
    print(f"adb: {adb}")
    devices = ensure_device(adb)
    if not devices:
        print("没有设备在线。先把模拟器打开；MuMu 12 默认端口 16384。")
        return
    for name in devices:
        print(f"  {name}")


def cmd_pkg(_args):
    """打印当前前台包名 —— interface.json 里的「游戏包名」就用这个。"""
    adb = require_adb()
    device = require_device(adb)
    out = run_adb(adb, ["-s", device, "shell", "dumpsys", "window", "displays"])
    packages = set()
    for line in out.splitlines():
        line = line.strip()
        if "mCurrentFocus" in line or "mFocusedApp" in line:
            for chunk in line.replace("}", " ").replace("{", " ").split():
                if "/" in chunk and "." in chunk:
                    packages.add(chunk.split("/")[0])
    if not packages:
        print("没读到前台包名。确认游戏已经在前台，再试一次。")
        return
    print("当前前台包名：")
    for pkg in sorted(packages):
        print(f"  {pkg}")
    print("\n把 interface.json 里「游戏包名」选项的 package 换成上面这个。")


def draw_grid(source, target, step=100, minor=50):
    """在截图上画坐标网格并标数字，用来肉眼（或让模型）读坐标。"""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        print("需要 Pillow 才能画网格: pip install pillow")
        return None

    with Image.open(source) as img:
        canvas = img.convert("RGB")
        width, height = canvas.size
        draw = ImageDraw.Draw(canvas)

        for x in range(0, width, minor):
            draw.line([(x, 0), (x, height)], fill=(255, 170, 170) if x % step else (255, 0, 0))
        for y in range(0, height, minor):
            draw.line([(0, y), (width, y)], fill=(255, 170, 170) if y % step else (255, 0, 0))
        for x in range(0, width, step):
            for y in range(0, height, step):
                draw.text((x + 4, y + 4), f"{x},{y}", fill=(255, 0, 0))

        canvas.save(target)
    return target


def cmd_grid(args):
    target = os.path.splitext(args.file)[0] + "_grid.png"
    saved = draw_grid(args.file, target)
    if saved:
        print(f"网格图已保存: {saved}")


def cmd_shoot(args):
    adb = require_adb()
    device = require_device(adb)
    os.makedirs(RAW_DIR, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    target = os.path.join(RAW_DIR, f"shot_{stamp}.png")
    # exec-out 不会做换行转换，二进制截图要靠它
    data = run_adb(adb, ["-s", device, "exec-out", "screencap", "-p"], binary=True)
    with open(target, "wb") as f:
        f.write(data)
    print(f"已保存: {target}（{len(data)} 字节）")

    if getattr(args, "grid", False):
        grid_path = os.path.splitext(target)[0] + "_grid.png"
        if draw_grid(target, grid_path):
            print(f"网格图: {grid_path}")

    print("接下来用 crop 裁模板，或者用 MaaDebugger 看坐标。")


def latest_raw():
    if not os.path.isdir(RAW_DIR):
        return None
    shots = [
        os.path.join(RAW_DIR, n)
        for n in os.listdir(RAW_DIR)
        if n.lower().endswith(".png")
    ]
    if not shots:
        return None
    return max(shots, key=os.path.getmtime)


def load_manifest():
    try:
        with open(MANIFEST, "r", encoding="utf-8") as f:
            return json.load(f).get("templates", [])
    except Exception as exc:  # noqa: BLE001
        print(f"templates.json 读不了: {exc}")
        return []


def cmd_list(_args):
    entries = load_manifest()
    if not entries:
        return
    missing = 0
    for item in entries:
        path = os.path.join(IMAGE_DIR, item["file"].replace("/", os.sep))
        exists = os.path.isfile(path)
        if not exists:
            missing += 1
        print(f"{'[有]' if exists else '[缺]'} {item['file']}")
        print(f"       {item['desc']}")
        print(f"       建议 roi: {item.get('roi_hint')}")
    print(f"\n共 {len(entries)} 张，缺 {missing} 张。")
    print("裁图示例: python tools/capture.py crop 首页/出击.png 60 380 220 90")


def cmd_crop(args):
    try:
        from PIL import Image
    except ImportError:
        print("需要 Pillow 来裁图: pip install pillow")
        sys.exit(1)

    source = args.from_file or latest_raw()
    if not source:
        print("没找到源截图，先跑一次 shoot。")
        sys.exit(1)
    if not os.path.isfile(source):
        print(f"源截图不存在: {source}")
        sys.exit(1)

    with Image.open(source) as img:
        width, height = img.size
        x, y, w, h = args.x, args.y, args.w, args.h
        if x < 0 or y < 0 or w <= 0 or h <= 0:
            print("x y 必须 >= 0，w h 必须 > 0")
            sys.exit(1)
        if x + w > width or y + h > height:
            print(f"裁剪区域超出截图范围（截图是 {width}x{height}）")
            sys.exit(1)
        if width < height:
            print(f"注意：截图是竖屏 {width}x{height}，但本项目的 roi 是按横屏 1280x720 写的。")
            print("      把游戏切到横屏再截。")
        if min(width, height) != 720:
            print(f"注意：截图短边是 {min(width, height)}，不是 720。")
            print("      interface.json 里 display_short_side 是 720，坐标按短边 720 缩放，先去调模拟器分辨率。")
        cropped = img.crop((x, y, x + w, y + h))
        target = os.path.join(IMAGE_DIR, args.key.replace("/", os.sep))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        cropped.save(target)

    print(f"已保存模板: {target}  ({w}x{h} @ {x},{y}，源 {os.path.basename(source)})")
    print("小提示：模板别裁太大也别太糊，尽量只含那一处独特图案，别带会变动的数字和光效。")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 终端默认 GBK，中文路径会变乱码
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="崩坏学园2 小助手截图/采模板工具")
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("devices", help="列 adb 设备").set_defaults(func=cmd_devices)
    sub.add_parser("pkg", help="查前台包名").set_defaults(func=cmd_pkg)
    sub.add_parser("list", help="打印模板清单").set_defaults(func=cmd_list)

    shoot = sub.add_parser("shoot", help="存一张全屏截图")
    shoot.add_argument("--grid", action="store_true", help="额外存一张带坐标网格的图")
    shoot.set_defaults(func=cmd_shoot)

    grid = sub.add_parser("grid", help="给已有截图画坐标网格")
    grid.add_argument("file", help="截图路径")
    grid.set_defaults(func=cmd_grid)

    crop = sub.add_parser("crop", help="裁剪模板图")
    crop.add_argument("key", help="模板路径，如 首页/出击.png")
    crop.add_argument("x", type=int)
    crop.add_argument("y", type=int)
    crop.add_argument("w", type=int)
    crop.add_argument("h", type=int)
    crop.add_argument("--from", dest="from_file", default=None, help="指定源截图，默认用最新那张")
    crop.set_defaults(func=cmd_crop)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
