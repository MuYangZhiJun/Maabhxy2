#!/usr/bin/env python3
"""提交并推送到 GitHub —— 带重试，专治国内访问 GitHub 的间歇性抽风。

为什么要这个脚本：这台机器到 GitHub 的连接**时通时断**，
实测推一次可能失败五六次（`Connection was reset` / `Failed to connect ... port 443`），
而 `git push` 本身不会重试。所以把「配置 → 提交 → 重试推送 → 校验」包成一条命令，
失败自己重来，成功就打印远端和本地是否一致。

用法：
    python tools/push.py                       # 自动提交（用默认提交信息）+ 推送
    python tools/push.py -m "fix: 修了 XX"      # 自己写提交信息
    python tools/push.py --retries 20          # 多试几次（网络特别差的时候）
    python tools/push.py --dry-run             # 只看会提交什么，不提交不推送

Windows 上直接双击根目录的「推送更新.bat」也一样。
"""

import argparse
import os
import subprocess
import sys
import time
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(args, timeout=180):
    """跑一条 git 命令，返回 (returncode, 合并后的输出)。"""
    try:
        p = subprocess.run(["git"] + args, cwd=ROOT, capture_output=True,
                           text=True, encoding="utf-8", errors="replace",
                           timeout=timeout)
        return p.returncode, ((p.stdout or "") + (p.stderr or "")).strip()
    except subprocess.TimeoutExpired:
        return 124, "超时（%ds）" % timeout


def short(out, n=3):
    lines = [l for l in out.splitlines() if l.strip()]
    return " | ".join(lines[-n:]) if lines else ""


def main():
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="提交并推送到 GitHub（带重试）")
    ap.add_argument("-m", "--message", default=None, help="提交信息")
    ap.add_argument("--retries", type=int, default=10, help="推送最多试几次（默认 10）")
    ap.add_argument("--interval", type=int, default=20, help="每次重试间隔秒数")
    ap.add_argument("--dry-run", action="store_true", help="只看状态，不提交不推送")
    args = ap.parse_args()

    # 1) 连接相关的稳妥配置（幂等，重复跑没事）
    run(["config", "http.version", "HTTP/1.1"])
    run(["config", "http.postBuffer", "524288000"])
    print("已确保 http.version=HTTP/1.1（GitHub 的 HTTP/2 在国内容易被重置）")

    # 2) 暂存 + 看有没有要提交的
    run(["add", "-A"])
    rc, staged = run(["diff", "--cached", "--name-only"])
    files = [f for f in staged.splitlines() if f.strip()]
    if files:
        print("待提交 %d 个文件：" % len(files))
        for f in files[:12]:
            print("   ", f)
        if len(files) > 12:
            print("    ... 还有 %d 个" % (len(files) - 12))
    else:
        print("没有新增改动")

    if args.dry_run:
        print("\n（--dry-run：到此为止）")
        return 0

    # 3) 提交
    if files:
        msg = args.message or ("chore: 自动提交 %s" % datetime.now().strftime("%Y-%m-%d %H:%M"))
        rc, out = run(["-c", "user.name=MuYangZhiJun",
                       "-c", "user.email=MuYangZhiJun@users.noreply.github.com",
                       "commit", "-q", "-m", msg])
        if rc != 0:
            print("[!!] 提交失败：%s" % short(out))
            return 1
        print("已提交：%s" % msg)
    else:
        print("没有要提交的，直接推送")

    # 4) 推送（重试）
    ok = False
    for i in range(1, args.retries + 1):
        print("推送第 %d/%d 次……" % (i, args.retries))
        rc, out = run(["push", "origin", "main"], timeout=300)
        if rc == 0 or "main -> main" in out or "up to date" in out:
            print("   ✅ 推送成功")
            ok = True
            break
        print("   ✗ %s" % short(out, 2))
        if i < args.retries:
            time.sleep(args.interval)

    if not ok:
        print("\n[!!] 试了 %d 次都没推上去 —— 基本是网络到 GitHub 不通。" % args.retries)
        print("     过一会儿再跑一次这个脚本就行（本地提交已经做好了，不会丢）。")
        return 1

    # 5) 校验：远端和本地是不是同一个提交
    local = run(["rev-parse", "HEAD"])[1].strip()
    remote = ""
    for i in range(5):
        rc, out = run(["ls-remote", "origin", "main"], timeout=90)
        if out and len(out.split()) and len(out.split()[0]) == 40:
            remote = out.split()[0]
            break
        time.sleep(10)
    print("\n本地 HEAD : %s" % local)
    print("远端 main : %s" % (remote or "(取不到，但推送已成功)"))
    if remote:
        print("→ %s" % ("一致 ✅" if remote == local else "不一致 ✗（再跑一次脚本试试）"))
    print("\n仓库：https://github.com/MuYangZhiJun/Maabhxy2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
