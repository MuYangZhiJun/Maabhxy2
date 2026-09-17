# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
d = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []
o = d["option"]["日常模块"]
L.append("### 日常模块 type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in (o.get("cases") or o.get("case") or []):
    L.append("-- case %s" % c.get("name"))
    for k, v in c.get("pipeline_override", {}).items():
        L.append("     %-44s %s" % (k, json.dumps(v, ensure_ascii=False)))
o = d["option"]["战斗模式"]
L.append("")
L.append("### 战斗模式 type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in (o.get("cases") or o.get("case") or []):
    L.append("-- case %s -> %s" % (c.get("name"), list(c.get("pipeline_override", {}).keys())))
L.append("")
L.append("### 任务")
for t in d["task"]:
    L.append("%s entry=%s option=%s" % (t.get("name"), t.get("entry"), t.get("option")))
open(os.path.join(ROOT, "OPT.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
