#!/usr/bin/env python3
"""组装一个能双击运行的 MFAAvalonia GUI 包（崩坏学园2 小助手）。

做的事情就是把官方模板 CI（.github/workflows/install.yml）在本地复现一遍：

  1. 下 MaaFramework 原生库  -> deps/
  2. 下 MFAAvalonia          -> MFA/
  3. 按 tools/install.py 的布局拼出 gui/：
       gui/                          <- MFAAvalonia（去掉它自带的 runtimes）
       gui/runtimes/win-x64/native/  <- MaaFramework 的 bin/
       gui/plugins/win-x64/          <- MaaFramework 的 bin/plugins/
       gui/libs/MaaAgentBinary/      <- MaaFramework 的 share/MaaAgentBinary/
       gui/resource/                 <- assets/resource/
       gui/interface.json            <- assets/interface.json
       gui/agent/                    <- agent/

之后双击 gui/MFAAvalonia.exe 就是你想要的界面。装完就不用再跑这个脚本了，
改 pipeline / 模板图之后重跑一次同步过去即可（会跳过已下载的压缩包）。

用法：
    python tools/get_gui.py                 # 首次：下载 + 组装
    python tools/get_gui.py --sync-only     # 只把 assets/ 和 agent/ 同步进 gui/
    python tools/get_gui.py --force         # 重新下载并重建 gui/
"""

import argparse
import json
import os
import shutil
import sys
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEPS_DIR = os.path.join(ROOT, "deps")
DOWNLOADS_DIR = os.path.join(ROOT, ".downloads")
MFA_DIR = os.path.join(ROOT, "MFA")
GUI_DIR = os.path.join(ROOT, "gui")

# 按官方模板 CI 的变量；MaaFramework 版本要和 deps/tools 里的 schema 对得上
MAAFW_VERSION = "v5.13.0"
MFA_VERSION = "v2.16.1"

MAAFW_URL = (
    f"https://github.com/MaaXYZ/MaaFramework/releases/download/"
    f"{MAAFW_VERSION}/MAA-win-x86_64-{MAAFW_VERSION}.zip"
)
MFA_URL = (
    f"https://github.com/MaaXYZ/MFAAvalonia/releases/download/"
    f"{MFA_VERSION}/MFAAvalonia-{MFA_VERSION}-win-x64.zip"
)

# .NET RID，和 tools/install.py 的 get_dotnet_platform_tag() 一致
RID = "win-x64"

# install.py 里从 bin/ 拷进 runtimes 时要排除的东西（调试/RPC 用的控制单元）
IGNORE_IN_RUNTIMES = shutil.ignore_patterns(
    "*MaaDbgControlUnit*",
    "*MaaThriftControlUnit*",
    "*MaaRpc*",
    "*MaaHttp*",
    "plugins",
    "*.node",
    "*MaaPiCli*",
)


def log(msg):
    print(msg, flush=True)


def download(url, dest):
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        log(f"[跳过] 已经下过了: {os.path.basename(dest)}")
        return dest

    os.makedirs(os.path.dirname(dest), exist_ok=True)
    log(f"[下载] {url}")
    request = urllib.request.Request(url, headers={"User-Agent": "bh2-maa-setup"})
    with urllib.request.urlopen(request, timeout=180) as response:
        total = int(response.headers.get("Content-Length") or 0)
        done = 0
        step = 8 * 1024 * 1024
        marked = 0
        with open(dest, "wb") as handle:
            while True:
                chunk = response.read(256 * 1024)
                if not chunk:
                    break
                handle.write(chunk)
                done += len(chunk)
                if done - marked >= step:
                    marked = done
                    if total:
                        log(f"       {done / 1048576:7.1f} / {total / 1048576:.1f} MB")
                    else:
                        log(f"       {done / 1048576:7.1f} MB")
    log(f"[完成] {os.path.basename(dest)}  {os.path.getsize(dest) / 1048576:.1f} MB")
    return dest


def extract_zip(zip_path, dest):
    log(f"[解压] {os.path.basename(zip_path)} -> {os.path.relpath(dest, ROOT)}")
    os.makedirs(dest, exist_ok=True)
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(dest)


def flatten_single_dir(dest):
    """有些包解出来会多套一层同名目录，这里把它拍平，保证 dest/bin 存在。"""
    if os.path.isdir(os.path.join(dest, "bin")):
        return
    entries = [
        name
        for name in os.listdir(dest)
        if os.path.isdir(os.path.join(dest, name)) and not name.startswith(".")
    ]
    if len(entries) != 1:
        return
    inner = os.path.join(dest, entries[0])
    if not os.path.isdir(os.path.join(inner, "bin")):
        return
    log(f"[整理] 把 {entries[0]}/ 里的内容提到上一层")
    for name in os.listdir(inner):
        shutil.move(os.path.join(inner, name), os.path.join(dest, name))
    os.rmdir(inner)


def fetch_runtime(force):
    maafw_zip = os.path.join(DOWNLOADS_DIR, os.path.basename(MAAFW_URL))
    if force and os.path.isfile(maafw_zip):
        os.remove(maafw_zip)
    download(MAAFW_URL, maafw_zip)
    if force and os.path.isdir(os.path.join(DEPS_DIR, "bin")):
        shutil.rmtree(os.path.join(DEPS_DIR, "bin"))
    if not os.path.isdir(os.path.join(DEPS_DIR, "bin")):
        extract_zip(maafw_zip, DEPS_DIR)
        flatten_single_dir(DEPS_DIR)
    wanted = os.path.join(DEPS_DIR, "bin")
    if not os.path.isdir(wanted):
        log(f"[!!] 解压后没找到 {wanted}，MaaFramework 包结构可能变了")
        sys.exit(1)
    agent_bin = os.path.join(DEPS_DIR, "share", "MaaAgentBinary")
    log(f"[OK] MaaFramework 原生库: {os.path.relpath(wanted, ROOT)}"
        f"{'' if os.path.isdir(agent_bin) else '（没找到 share/MaaAgentBinary，agent 可能起不来）'}")


def fetch_gui(force):
    mfa_zip = os.path.join(DOWNLOADS_DIR, os.path.basename(MFA_URL))
    if force and os.path.isfile(mfa_zip):
        os.remove(mfa_zip)
    download(MFA_URL, mfa_zip)
    if force and os.path.isdir(MFA_DIR):
        shutil.rmtree(MFA_DIR)
    if not os.path.isdir(MFA_DIR):
        extract_zip(mfa_zip, MFA_DIR)
        flatten_single_dir(MFA_DIR)
    exe = os.path.join(MFA_DIR, "MFAAvalonia.exe")
    if not os.path.isfile(exe):
        found = [n for n in os.listdir(MFA_DIR) if n.lower().endswith(".exe")]
        log(f"[!!] {os.path.relpath(MFA_DIR, ROOT)} 里没找到 MFAAvalonia.exe，"
            f"只有这些 exe: {found}")
        sys.exit(1)
    log(f"[OK] MFAAvalonia: {os.path.relpath(exe, ROOT)}")


def assemble(force):
    if force and os.path.isdir(GUI_DIR):
        shutil.rmtree(GUI_DIR)

    os.makedirs(GUI_DIR, exist_ok=True)
    log(f"[组装] MFAAvalonia -> {os.path.relpath(GUI_DIR, ROOT)}")
    shutil.copytree(MFA_DIR, GUI_DIR, dirs_exist_ok=True)

    # CI 里这一步是 `rm -rf MFA/runtimes`：用 MaaFramework 官方包里的原生库，
    # 而不是 MFAAvalonia 自带的，保证和 deps/tools 的 schema 版本一致
    gui_runtimes = os.path.join(GUI_DIR, "runtimes")
    if os.path.isdir(gui_runtimes):
        shutil.rmtree(gui_runtimes)
    shutil.copytree(
        os.path.join(DEPS_DIR, "bin"),
        os.path.join(gui_runtimes, RID, "native"),
        ignore=IGNORE_IN_RUNTIMES,
        dirs_exist_ok=True,
    )
    plugins_src = os.path.join(DEPS_DIR, "bin", "plugins")
    if os.path.isdir(plugins_src):
        shutil.copytree(
            plugins_src, os.path.join(GUI_DIR, "plugins", RID), dirs_exist_ok=True
        )

    agent_bin = os.path.join(DEPS_DIR, "share", "MaaAgentBinary")
    if os.path.isdir(agent_bin):
        shutil.copytree(
            agent_bin, os.path.join(GUI_DIR, "libs", "MaaAgentBinary"), dirs_exist_ok=True
        )

    sync_assets(version=read_version())


def sync_assets(version="0.1.0"):
    """把本项目的资源、interface.json、agent 同步进 gui/。改完 pipeline 重跑用。"""
    log(f"[同步] assets/ + agent/ -> {os.path.relpath(GUI_DIR, ROOT)}")

    resource_src = os.path.join(ROOT, "assets", "resource")
    resource_dst = os.path.join(GUI_DIR, "resource")
    if os.path.isdir(resource_dst):
        shutil.rmtree(resource_dst)
    shutil.copytree(resource_src, resource_dst, dirs_exist_ok=True)
    # _raw 里是采集用的原始截图，别塞进发布包
    raw = os.path.join(resource_dst, "image", "_raw")
    if os.path.isdir(raw):
        shutil.rmtree(raw)

    interface_src = os.path.join(ROOT, "assets", "interface.json")
    interface_dst = os.path.join(GUI_DIR, "interface.json")
    with open(interface_src, "r", encoding="utf-8") as handle:
        text = handle.read()
    # interface.json 带 // 注释，先用 json-with-comments 解析再写一份干净的
    try:
        import jsonc  # type: ignore

        data = jsonc.loads(text)
    except ImportError:
        import re

        data = json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.MULTILINE))
    data["version"] = version
    with open(interface_dst, "w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=4)
    log(f"[OK] interface.json（{len(data.get('task', []))} 个任务）")

    agent_src = os.path.join(ROOT, "agent")
    agent_dst = os.path.join(GUI_DIR, "agent")
    if os.path.isdir(agent_dst):
        shutil.rmtree(agent_dst)
    shutil.copytree(agent_src, agent_dst, dirs_exist_ok=True)
    shutil.rmtree(os.path.join(agent_dst, "__pycache__"), ignore_errors=True)
    log("[OK] agent/")


def read_version():
    try:
        import re

        with open(
            os.path.join(ROOT, "assets", "interface.json"), "r", encoding="utf-8"
        ) as handle:
            match = re.search(r'"version"\s*:\s*"([^"]+)"', handle.read())
        return match.group(1) if match else "0.1.0"
    except Exception:  # noqa: BLE001
        return "0.1.0"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="组装 MFAAvalonia GUI 包")
    parser.add_argument("--force", action="store_true", help="重新下载并重建")
    parser.add_argument(
        "--sync-only",
        action="store_true",
        help="只把 assets/ 和 agent/ 同步进已有 gui/，不下载",
    )
    args = parser.parse_args()

    log("== 崩坏学园2 小助手 · GUI 组装 ==")
    log(f"MaaFramework {MAAFW_VERSION} / MFAAvalonia {MFA_VERSION} / {RID}")
    log("")

    if args.sync_only:
        if not os.path.isdir(GUI_DIR):
            log("[!!] gui/ 不存在，先跑一次不带 --sync-only 的")
            sys.exit(1)
        sync_assets()
    else:
        fetch_runtime(args.force)
        fetch_gui(args.force)
        assemble(args.force)

    log("")
    log("== 好了 ==")
    log(f"双击运行: {os.path.join(GUI_DIR, 'MFAAvalonia.exe')}")
    log("")
    log("第一次进去要做的事：")
    log("  1. 左下角加实例 -> 选「安卓端」控制器")
    log("  2. adb 路径填 E:\\MuMu Player 12\\shell\\adb.exe")
    log("  3. 地址填 127.0.0.1:16384（MuMu 12 第一个实例）")
    log("  4. 勾任务 -> 开始")
    log("")
    log("改完 pipeline 或补了新模板图，跑 python tools/get_gui.py --sync-only 同步过去。")


if __name__ == "__main__":
    main()
