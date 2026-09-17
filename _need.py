# -*- coding: utf-8 -*-
import json, os, io
ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
iface = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

L = []
L.append("=========== 选项: 日常模块 ===========")
o = iface["option"]["日常模块"]
L.append("type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in o["cases"]:
    L.append("-- case %s" % c["name"])
    for k, v in c["pipeline_override"].items():
        L.append("     %-40s %s" % (k, json.dumps(v, ensure_ascii=False)))
L.append("")
L.append("=========== 选项: 战斗模式 ===========")
o = iface["option"]["战斗模式"]
for c in o["cases"]:
    L.append("-- case %s" % c["name"])
    for k, v in c["pipeline_override"].items():
        L.append("     %-40s %s" % (k, json.dumps(v, ensure_ascii=False)))
L.append("")
L.append("=========== 虚轴之庭 全节点 ===========")
for k in sorted(d):
    if k.startswith("日常_虚轴之庭"):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
L.append("")
L.append("=========== 使魔的爱 全节点 ===========")
for k in sorted(d):
    if k.startswith("日常_使魔的爱"):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
L.append("")
L.append("=========== 活动BONUS 全节点 ===========")
for k in sorted(d):
    if k.startswith("日常_活动BONUS"):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
io.open(os.path.join(ROOT, "NEED.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
