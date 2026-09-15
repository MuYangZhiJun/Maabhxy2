#!/usr/bin/env python3
"""崩坏学园2 小助手 —— 环境与资源自检。

干三件事：
  1. 把 assets/resource/pipeline/*.json 全读一遍，检查语法、next 里引用的节点是否真的存在；
  2. 汇总所有 template，对一下 assets/resource/image/ 下缺哪几张（也就是「还要截哪些图」）；
  3. 看一眼 python 依赖、agent 进程能不能起来、adb 在不在、连没连上设备。

用法：
    python tools/check_env.py            # 全部检查
    python tools/check_env.py --templates  # 只看模板图缺哪些
"""

import argparse
import json
import os
import re
import shutil
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PIPELINE_DIR = os.path.join(ROOT, "assets", "resource", "pipeline")
IMAGE_DIR = os.path.join(ROOT, "assets", "resource", "image")
INTERFACE = os.path.join(ROOT, "assets", "interface.json")
AGENT_CONFIG = os.path.join(ROOT, "agent", "battle_config.json")

# v5 起 next 里可以给节点加前缀，比如 "[JumpBack]某节点"；校验引用时必须剥掉
PREFIX_RE = re.compile(r"^\[[A-Za-z]+\]")

OK = "[OK]  "
BAD = "[!!]  "
WARN = "[??]  "
WAIT = "[..]  "

# MuMu 12 的 adb 端口：第一个实例 16384，往后每个 +32
MUMU_PORTS = [16384, 16416, 16448, 16480]


def connected_devices(adb):
    out = subprocess.run([adb, "devices"], capture_output=True, text=True, timeout=20).stdout
    found = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            found.append(parts[0])
    return found


def ensure_device(adb):
    """没设备就照着 MuMu 的端口连一遍，连上就返回设备号。"""
    for port in MUMU_PORTS:
        address = f"127.0.0.1:{port}"
        try:
            out = subprocess.run(
                [adb, "connect", address], capture_output=True, text=True, timeout=20
            ).stdout.strip()
        except Exception:  # noqa: BLE001
            continue
        if "connected" in out:
            print(f"{OK}已连接 {address}")
            devices = connected_devices(adb)
            if devices:
                return devices
    return []


def load_json_with_comments(path):
    """interface.json 带注释，优先用 json-with-comments，没有就把 // 注释剥掉。"""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()
    try:
        import json_with_comments  # type: ignore

        return json_with_comments.loads(text)
    except ImportError:
        stripped = re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE)
        return json.loads(stripped)


def iter_pipeline_files():
    if not os.path.isdir(PIPELINE_DIR):
        return []
    return sorted(
        os.path.join(PIPELINE_DIR, n)
        for n in os.listdir(PIPELINE_DIR)
        if n.endswith(".json")
    )


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def check_pipelines():
    print("== pipeline 文件 ==")
    nodes = {}
    templates = {}
    problems = 0

    for path in iter_pipeline_files():
        name = os.path.basename(path)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as exc:  # noqa: BLE001
            print(f"{BAD}{name}: JSON 解析失败 -> {exc}")
            problems += 1
            continue

        if not isinstance(data, dict):
            print(f"{BAD}{name}: 顶层不是对象")
            problems += 1
            continue

        print(f"{OK}{name}: {len(data)} 个节点")
        for node, body in data.items():
            if node in nodes:
                print(f"{BAD}{name}: 节点「{node}」在 {nodes[node]} 里已经定义过了")
                problems += 1
            nodes[node] = name
            if not isinstance(body, dict):
                print(f"{BAD}{name}: 节点「{node}」的值不是对象")
                problems += 1
                continue
            for tpl in as_list(body.get("template")):
                if isinstance(tpl, str):
                    templates.setdefault(tpl, set()).add(node)

    print()
    print("== next 引用 ==")
    dangling = 0
    for path in iter_pipeline_files():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:  # noqa: BLE001
            continue
        for node, body in data.items():
            if not isinstance(body, dict):
                continue
            for ref in as_list(body.get("next")):
                if not isinstance(ref, str):
                    continue
                target = PREFIX_RE.sub("", ref)
                if target not in nodes:
                    print(f"{BAD}{os.path.basename(path)}: 「{node}」的 next 指向了不存在的节点「{ref}」")
                    dangling += 1
    if dangling == 0:
        print(f"{OK}所有 next 引用都能对上（共 {len(nodes)} 个节点）")
    problems += dangling

    print()
    print("== 模板图 ==")
    manifest = {}
    mpath = os.path.join(ROOT, "tools", "templates.json")
    try:
        with open(mpath, "r", encoding="utf-8") as f:
            for item in json.load(f).get("templates", []):
                manifest[item["file"]] = item
    except Exception as exc:  # noqa: BLE001
        print(f"{WARN}tools/templates.json 读不了: {exc}")

    missing = []
    for tpl in sorted(templates):
        full = os.path.join(IMAGE_DIR, tpl.replace("/", os.sep))
        exists = os.path.isfile(full)
        mark = OK if exists else BAD
        if not exists:
            missing.append(tpl)
        used = "、".join(sorted(templates[tpl])[:3])
        note = "" if tpl in manifest else "  (清单里没登记)"
        print(f"{mark}{tpl}{note}   被 {used} 用到")
    if missing:
        print(f"\n还缺 {len(missing)} 张模板图 —— 用 tools/capture.py 截，清单和说明在 tools/templates.json")

    for tpl in manifest:
        if tpl not in templates:
            print(f"{WARN}{tpl} 登记了但没有任何节点在用")
    return problems


def check_adb():
    print()
    print("== adb ==")
    adb = shutil.which("adb")
    if adb is None:
        candidates = [
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
        for c in candidates:
            if os.path.isfile(c):
                adb = c
                break
    if adb is None:
        print(f"{BAD}没找到 adb：装个 platform-tools 丢进 PATH，或者装模拟器自带的那个")
        return
    print(f"{OK}adb: {adb}")
    try:
        devices = connected_devices(adb)
        if not devices:
            print(f"{WAIT}adb devices 是空的，试着连一下模拟器（MuMu 12 默认 16384 起）…")
            devices = ensure_device(adb)
        if not devices:
            print(f"{BAD}没有设备在线：先把模拟器打开，再跑一次")
            return
        for name in devices:
            print(f"{OK}设备 {name}")

        # 注意：`wm size` 报的是面板物理尺寸，模拟器把显示覆盖成横屏时它会骗人
        # （MuMu 12 就报 Physical size: 720x1280，但实际截图是 1280x720）。
        # 所以直接量一张截图的像素 —— 那才是 MaaFramework 会看到的东西。
        wm = subprocess.run(
            [adb, "-s", devices[0], "shell", "wm", "size"],
            capture_output=True, text=True, timeout=15,
        ).stdout.strip()
        print(f"{WAIT}{wm}（面板尺寸，仅供参考）")

        size = screencap_size(adb, devices[0])
        if size is None:
            print(f"{BAD}截图失败，量不到真实分辨率")
            return
        w, h = size
        short = min(w, h)
        print(f"{OK}实际截图: {w}x{h}")
        if short != 720:
            print(
                f"{BAD}短边是 {short}，不是 720 —— interface.json 里 display_short_side 是 720，"
                "坐标按短边 720 缩放，先把模拟器分辨率调对"
            )
        elif w > h:
            print(f"{OK}横屏 {w}x{h}，和 pipeline 里的 roi 坐标系一致")
        else:
            print(f"{BAD}是竖屏 {w}x{h}，但本项目 roi 按横屏 1280x720 写的，把游戏切到横屏再用")
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD}adb 查询失败: {exc}")


def screencap_size(adb, device):
    """真的截一张图，读 PNG 头拿宽高。"""
    data = subprocess.run(
        [adb, "-s", device, "exec-out", "screencap", "-p"],
        capture_output=True,
        timeout=30,
    ).stdout
    if len(data) < 24 or data[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    w, h = struct.unpack(">II", data[16:24])
    return w, h


def check_python():
    print()
    print("== python 依赖 ==")
    print(f"{OK}python {sys.version.split()[0]}")
    try:
        import maa  # type: ignore

        version = getattr(maa, "__version__", "未知版本")
        print(f"{OK}maa-framework-python: {version}")
    except ImportError:
        print(f"{BAD}没装 maa：pip install maa-framework")
        return
    try:
        from maa.controller import AdbController  # type: ignore

        for method in ("post_click", "post_swipe", "post_screencap"):
            mark = OK if hasattr(AdbController, method) else BAD
            print(f"{mark}AdbController.{method}")
    except Exception as exc:  # noqa: BLE001
        print(f"{WARN}检查 AdbController 时出岔子: {exc}")


def check_configs():
    print()
    print("== 项目配置 ==")
    try:
        data = load_json_with_comments(INTERFACE)
        tasks = data.get("task", [])
        print(f"{OK}interface.json: {data.get('name')} v{data.get('version')}，{len(tasks)} 个任务")
        agent = data.get("agent") or {}
        if agent:
            print(f"{OK}agent 进程: {agent.get('child_exec')} {' '.join(agent.get('child_args', []))}（需要 pip install maa-framework）")
        else:
            print(f"{WARN}interface.json 里没有 agent 字段，自定义识别/动作起不来（自动战斗会失效）")
    except Exception as exc:  # noqa: BLE001
        print(f"{BAD}interface.json 读不了: {exc}")

    try:
        with open(AGENT_CONFIG, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        print(f"{OK}battle_config.json: 攻击键 {cfg.get('attack_button')}，摇杆 {cfg.get('joystick_center')}")
    except Exception as exc:  # noqa: BLE001
        print(f"{WARN}battle_config.json 读不了（会自动用内置默认值）: {exc}")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        # Windows 终端默认 GBK，中文和符号会变乱码
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="崩坏学园2 小助手自检")
    parser.add_argument("--templates", action="store_true", help="只检查模板图")
    args = parser.parse_args()

    if args.templates:
        check_pipelines()
        return

    check_configs()
    problems = check_pipelines()
    check_python()
    check_adb()

    print()
    print(f"== 结论 ==\n流水线自身的问题: {problems} 个（0 才算干净）")


if __name__ == "__main__":
    main()
