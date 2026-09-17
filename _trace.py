# -*- coding: utf-8 -*-
"""从 maafw.log 还原节点执行轨迹。"""
import re, io, os, sys

ROOT = r"D:\bh2-maa"
LOG = os.path.join(ROOT, "gui", "debug", "maafw.log")

reco_hit = re.compile(r"reco hit \[result\.name=([^\]]+)\]")
reco_fail = re.compile(r"\[data\.name=([^\]]+)\] \| enter")
matcher = re.compile(r"TemplateMatcher::analyze\] (\S+) \[all_results_=\[([^\]]*)\]")
act = re.compile(r"Actuator::run\] \[pipeline_data\.name=([^\]]+)\]")
action_start = re.compile(r"Node\.Action\.Starting.*?pipeline_data\.name=([^\]]+)")
next_fail = re.compile(r"Node\.Recognition\.Failed.*?\"name\":\"([^\"]+)\"")

seq = []
shots = {}
for line in io.open(LOG, encoding="utf-8", errors="replace"):
    m = reco_hit.search(line)
    if m:
        seq.append(("HIT", m.group(1)))
        continue
    m = matcher.search(line)
    if m:
        shots.setdefault(m.group(1), []).append(m.group(2)[:120])
        continue
    m = act.search(line)
    if m:
        seq.append(("ACT", m.group(1)))

# 只保留 BONUS / 虚轴 / 使魔 / 快捷 相关
KEYS = ["活动BONUS", "快捷战斗", "虚轴之庭", "使魔的爱", "助战", "开战", "选好友", "打完", "结算"]
out = []
for kind, name in seq:
    if any(k in name for k in KEYS):
        out.append(f"{kind:3s} {name}")

open(os.path.join(ROOT, "_trace.txt"), "w", encoding="utf-8").write(
    "\n".join(out) + "\n\n==== 模板分数 ====\n" +
    "\n".join(f"{k}: {v}" for k, v in shots.items()))
print("seq", len(seq), "-> _trace.txt")
