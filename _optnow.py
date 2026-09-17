# -*- coding: utf-8 -*-
import json, os, io

ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
d = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []
L.append("version=%s" % d.get("version"))
L.append("")
L.append("############ TASKS ############")
for t in d["task"]:
    L.append("%s | entry=%s | option=%s" % (t.get("name"), t.get("entry"), t.get("option")))
L.append("")
L.append("############ OPTIONS ############")
for name, o in d["option"].items():
    L.append("### %s  type=%s  default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        ov = c.get("pipeline_override", {})
        L.append("   -- %s" % c.get("name"))
        for k, v in ov.items():
            L.append("        %-44s %s" % (k, json.dumps(v, ensure_ascii=False)))
    L.append("")

io.open(os.path.join(ROOT, "OPTNOW.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
