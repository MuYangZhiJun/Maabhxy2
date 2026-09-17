# -*- coding: utf-8 -*-
import subprocess, io
ROOT = r"D:\bh2-maa"

def g(*a):
    return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True).stdout.decode("utf-8-sig", "replace")

L = []
L.append("===== git log -20 (时间倒序) =====")
L.append(g("log", "--pretty=%h | %ad | %s", "--date=format:%m-%d %H:%M", "-20"))
L.append("")
L.append("===== cfb90bb 详情 =====")
L.append(g("show", "-s", "--pretty=%h | %ad | %s", "--date=format:%m-%d %H:%M", "cfb90bb"))
L.append("===== cfb90bb 的父 =====")
L.append(g("log", "--pretty=%h | %ad | %s", "--date=format:%m-%d %H:%M", "-1", "cfb90bb^"))
L.append("===== cfb90bb..HEAD 改了哪些文件 =====")
L.append(g("diff", "--stat", "cfb90bb", "HEAD"))
L.append("===== HEAD 详情 =====")
L.append(g("show", "-s", "--pretty=%h | %ad | %s", "--date=format:%m-%d %H:%M", "HEAD"))

io.open(ROOT + r"\GITLOG.txt", "w", encoding="utf-8").write("\n".join(L))
print("ok")
