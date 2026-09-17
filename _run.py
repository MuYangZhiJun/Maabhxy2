# -*- coding: utf-8 -*-
"""从 maafw.log 提取最近一次运行的节点序列（只看 关卡战斗 相关）。"""
import io, os, re

ROOT = r"D:\bh2-maa"
LOG = os.path.join(ROOT, "gui", "debug", "maafw.log")

names = []
pat = re.compile(r"(日常_[\w\u4e00-\u9fff]+|关卡战斗_[\w\u4e00-\u9fff]+|启动_[\w\u4e00-\u9fff]+|通用_[\w\u4e00-\u9fff]+)")
# maafw 节点执行日志形如: [ts][INF][Px..][Th..][Node.Recognition] "name":"xxx"  或  reco hit
reco = re.compile(r'\[(?:Node\.[A-Za-z]+|Tasker)\][^\n]*?"name"\s*:\s*"([^"]+)"')
hit = re.compile(r'reco hit[^\n]*?name=([^\]]+)\]')

seq = []
try:
    with io.open(LOG, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = reco.search(line) or hit.search(line)
            if m:
                seq.append(m.group(1))
except FileNotFoundError:
    pass

out = []
out.append("总节点事件 %d" % len(seq))
# 去重连续
prev = None
uniq = []
for s in seq:
    if s != prev:
        uniq.append(s)
        prev = s
out.append("去重后 %d" % len(uniq))
out.append("")
out.append("--- 最近 120 个 ---")
out.extend(uniq[-120:])

# 统计每个节点出现次数
from collections import Counter
c = Counter(seq)
out.append("")
out.append("--- 次数 top40 ---")
for k, v in c.most_common(40):
    out.append("%4d  %s" % (v, k))

open(os.path.join(ROOT, "RUN.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok seq=%d" % len(seq))
