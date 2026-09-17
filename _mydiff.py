# -*- coding: utf-8 -*-
import subprocess, io, os
ROOT = r"D:\bh2-maa"

def g(*a):
    return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True).stdout.decode("utf-8-sig", "replace")

L = []
L.append("############ 我到底改了哪些文件 (cfb90bb..HEAD) ############")
L.append(g("diff", "--stat", "cfb90bb", "HEAD"))
L.append("")
L.append("############ 未提交改动 ############")
L.append(g("status", "--short"))
L.append("")
L.append("############ interface.json 差异 ############")
L.append(g("diff", "cfb90bb", "HEAD", "--", "assets/interface.json"))
L.append("")
L.append("############ tools/templates.json 差异(仅计数) ############")
d = g("diff", "--numstat", "cfb90bb", "HEAD", "--", "tools/templates.json")
L.append(d)
L.append("")
L.append("############ 10_启动.json 差异 ############")
L.append(g("diff", "cfb90bb", "HEAD", "--", "assets/resource/pipeline/10_启动.json"))
io.open(os.path.join(ROOT, "MYDIFF.txt"), "w", encoding="utf-8").write("\n".join(L))
print("written")
