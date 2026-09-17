# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
lines = [l for l in raw.splitlines() if not l.strip().startswith("//")]
d = json.loads("\n".join(lines))

out = []
out.append("TASK entry 关卡战斗: %s" % [t for t in d["task"] if t["name"] == "关卡战斗"][0])
out.append("")
for name, o in d["option"].items():
    out.append("### OPTION %s  type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    cases = o.get("cases") or o.get("case") or []
    for c in cases:
        ov = c.get("pipeline_override", {})
        on = [k for k, v in ov.items() if isinstance(v, dict) and v.get("enabled") is True]
        off = [k for k, v in ov.items() if isinstance(v, dict) and v.get("enabled") is False]
        other = [k for k, v in ov.items() if not (isinstance(v, dict) and "enabled" in v)]
        out.append("   case %-16s ON=%s OFF=%s other=%s" % (repr(c.get("name")), on, off, other))
    out.append("")

open(os.path.join(ROOT, "_optcases.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
