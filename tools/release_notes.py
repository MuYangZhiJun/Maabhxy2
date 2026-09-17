#!/usr/bin/env python3
"""生成某次发布的 Release 正文：**只取这次**的更新小节 + 固定的尾部说明。

为什么要这个脚本（用户 2026-09-18 指出）：
以前 `.github/RELEASE_NOTES.md` 是一个文件、一直往里**追加**，
而发布流水线又把整个文件当正文 → **越发布越长**，每篇 Release 都带着之前所有版本。
现在分开了：
    CHANGELOG.md               所有版本的小节（历史）
    .github/release_footer.md  「怎么用」「注意」这段固定说明
这个脚本按 tag 取**对应那一节**拼上 footer，只输出本次内容。

用法：
    python tools/release_notes.py v0.1.11              # 打到 stdout
    python tools/release_notes.py v0.1.11 -o out.md    # 写到文件
    python tools/release_notes.py --list              # 看看 CHANGELOG 里有哪些版本
"""

import argparse
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CHANGELOG = os.path.join(ROOT, "CHANGELOG.md")
FOOTER = os.path.join(ROOT, ".github", "release_footer.md")


def sections():
    """把 CHANGELOG 拆成 {版本号: 正文}，版本号不带 v。"""
    text = open(CHANGELOG, encoding="utf-8").read()
    hits = list(re.finditer(r"^## v([0-9][0-9.]*).*$", text, re.M))
    out = {}
    for i, m in enumerate(hits):
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        out[m.group(1)] = text[m.start():end].rstrip() + "\n"
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(description="生成本次 Release 的说明")
    ap.add_argument("tag", nargs="?", help="形如 v0.1.11（也接受 0.1.11）")
    ap.add_argument("-o", "--out", help="写到文件（默认打 stdout）")
    ap.add_argument("--list", action="store_true", help="列出 CHANGELOG 里的版本")
    args = ap.parse_args()

    data = sections()
    if args.list:
        for v in data:
            print("v" + v)
        return 0
    if not args.tag:
        ap.error("要么给 tag，要么加 --list")

    ver = args.tag.lstrip("v")
    if ver not in data:
        print(f"[!!] CHANGELOG.md 里没有 v{ver} 这一节（有：{', '.join('v'+k for k in data)}）",
              file=sys.stderr)
        print("[!!] 发版前记得**在 CHANGELOG.md 顶部写一节本次的改动**。", file=sys.stderr)
        return 1

    body = data[ver]
    if os.path.isfile(FOOTER):
        body = body.rstrip() + "\n\n" + open(FOOTER, encoding="utf-8").read().lstrip()
    if args.out:
        with open(args.out, "w", encoding="utf-8", newline="\n") as f:
            f.write(body)
        print(f"已写入 {args.out}（{len(body)} 字符）")
    else:
        sys.stdout.write(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
