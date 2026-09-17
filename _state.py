# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

out = []
out.append("=== 日常模块 option ===")
o = iface["option"]["日常模块"]
out.append("type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in (o.get("cases") or o.get("case") or []):
    ov = c.get("pipeline_override", {})
    out.append("case %s:" % repr(c.get("name")))
    for k, v in ov.items():
        out.append("   %s = %s" % (k, json.dumps(v, ensure_ascii=False)))

out.append("")
out.append("=== 战斗模式 option ===")
o = iface["option"]["战斗模式"]
for c in (o.get("cases") or o.get("case") or []):
    ov = c.get("pipeline_override", {})
    out.append("case %s: %s" % (repr(c.get("name")), list(ov.keys())))

out.append("")
out.append("=== 节点 enabled ===")
for k in sorted(pipe):
    if k.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "日常_步骤")):
        out.append("%-36s enabled=%s" % (k, pipe[k].get("enabled", True)))

out.append("")
out.append("=== 前3步 日常_步骤 ===")
for k in ["日常_步骤1", "日常_步骤2", "日常_步骤3", "日常_步骤4", "日常_步骤5", "日常_步骤6", "日常_步骤7"]:
    n = pipe.get(k) or {}
    out.append("%s: next=%s" % (k, n.get("next")))

open(os.path.join(ROOT, "_state.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
