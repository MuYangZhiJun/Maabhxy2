# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
d = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

out = []
for name, o in d["option"].items():
    out.append("### %s  type=%s  default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    cases = o.get("cases") or o.get("case") or []
    if not cases:
        out.append("   (无 cases, keys=%s)" % list(o.keys()))
    for c in cases:
        ov = c.get("pipeline_override", {})
        out.append("   -- case %s" % repr(c.get("name")))
        for k, v in ov.items():
            out.append("        %s = %s" % (k, json.dumps(v, ensure_ascii=False)))
    out.append("")

open(os.path.join(ROOT, "_ov.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
