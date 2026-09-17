# -*- coding: utf-8 -*-
import json, os, io, re

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []
L.append("############ A. 选项 ############")
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
for name, o in iface["option"].items():
    L.append("### %s type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        L.append("  -- case %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("       %-40s %s" % (k, json.dumps(v, ensure_ascii=False)))
L.append("")
L.append("### tasks")
for t in iface["task"]:
    L.append("%s | entry=%s | option=%s" % (t.get("name"), t.get("entry"), t.get("option")))

L.append("")
L.append("############ B. 步骤链 ############")
for k in sorted(d):
    if k.startswith(("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗")):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))

L.append("")
L.append("############ C. 三大模块节点 ############")
KEEP = ("enabled", "recognition", "template", "roi", "threshold", "action",
        "custom_action", "target", "max_hit", "post_delay", "next")
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"]:
    L.append("")
    L.append("========== %s ==========" % pre)
    for k in sorted(d):
        if k.startswith(pre):
            n = {kk: d[k][kk] for kk in KEEP if kk in d[k]}
            L.append("%s" % k)
            L.append("   %s" % json.dumps(n, ensure_ascii=False))

open(os.path.join(ROOT, "EVERY.txt"), "w", encoding="utf-8").write("\n".join(L))
print("lines", len(L))

# 单独把运行 trace 也写出来
T = []
tp = os.path.join(ROOT, "gui", "debug", "maafw.log")
if os.path.exists(tp):
    pat = re.compile(r'"name"\s*:\s*"([^"]+)"')
    seq = []
    for line in io.open(tp, encoding="utf-8", errors="replace"):
        if "Node." in line or "Tasker" in line:
            m = pat.search(line)
            if m:
                seq.append(m.group(1))
    prev = None
    uniq = []
    for s in seq:
        if s != prev:
            uniq.append(s)
            prev = s
    T.append("events %d uniq %d" % (len(seq), len(uniq)))
    T.extend(uniq[-160:])
open(os.path.join(ROOT, "TRACE.txt"), "w", encoding="utf-8").write("\n".join(T))
print("trace lines", len(T))
