# -*- coding: utf-8 -*-
import io, sys, re
sys.stdout.reconfigure(encoding="utf-8")
s = io.open(r"D:\bh2-maa\HANDOFF.md", encoding="utf-8").read().splitlines()
pat = re.compile(r"快捷战斗|助战|BONUS|虚轴|使魔的爱|开战|关卡战斗|扫荡|选好友|日常模块|选项")
out = []
for i, l in enumerate(s, 1):
    if pat.search(l):
        out.append("%4d| %s" % (i, l))
io.open(r"D:\bh2-maa\HIT.txt", "w", encoding="utf-8").write("\n".join(out))
print("hits", len(out), "total lines", len(s))
