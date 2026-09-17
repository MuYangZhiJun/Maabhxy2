# -*- coding: utf-8 -*-
import json, os, io

ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
d = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []
L.append("version=%s" % d.get("version"))
L.append("option 类型=%s  keys=%s" % (type(d.get("option")).__name__, list(d["option"])))
L.append("")
L.append("### TASKS")
for t in d["task"]:
    L.append("  %s | entry=%s | option=%s" % (t.get("name"), t.get("entry"), t.get("option")))
L.append("")
L.append("### OPTION 结构")
for name, o in d["option"].items():
    cs = o.get("cases")
    L.append("%s | type=%s | default=%s | cases=%s" % (
        name, o.get("type"), o.get("default_case") or o.get("default"),
        (len(cs) if isinstance(cs, list) else type(cs).__name__)))
    if isinstance(cs, list):
        for c in cs:
            if isinstance(c, dict):
                ov = c.get("pipeline_override", {})
                L.append("    case %-14s | override %d 项: %s" % (
                    c.get("name"), len(ov), ",".join(list(ov)[:8])))
            else:
                L.append("    case(raw) %r" % (c,))
io.open(os.path.join(ROOT, "IFACE.txt"), "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L[:80]))
