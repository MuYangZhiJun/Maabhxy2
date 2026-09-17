# -*- coding: utf-8 -*-
import io, re, sys
s = io.open(r"D:\bh2-maa\HANDOFF.md", encoding="utf-8").read().splitlines()
# 抓「关卡战斗 / 快捷战斗 / 助战 / BONUS / 虚轴」相关段，每段带上下文
pat = re.compile(r"快捷战斗|选择助战|助战|BONUS|虚轴之庭|使魔的爱|开战|关卡战斗|扫荡|多元裂缝")
idx = [i for i, l in enumerate(s) if pat.search(l)]
blocks = []
seen = set()
for i in idx:
    a, b = max(0, i - 2), min(len(s), i + 3)
    if any(x in seen for x in range(a, b)):
        continue
    for x in range(a, b):
        seen.add(x)
    blocks.append((i + 1, "\n".join("%5d| %s" % (x + 1, s[x]) for x in range(a, b))))
out = ["##### HANDOFF 共 %d 行，命中 %d 段 #####" % (len(s), len(blocks)), ""]
for n, b in blocks:
    out.append(b)
    out.append("")
io.open(r"D:\bh2-maa\H1.txt", "w", encoding="utf-8").write("\n".join(out))
print("blocks", len(blocks), "->  H1.txt")
