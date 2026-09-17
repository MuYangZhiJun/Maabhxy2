# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

out = []
out.append("############ OPTIONS ############")
for name, o in iface["option"].items():
    out.append("### %s type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        ov = c.get("pipeline_override", {})
        out.append("  -- case %r" % c.get("name"))
        for k, v in ov.items():
            out.append("       %s = %s" % (k, json.dumps(v, ensure_ascii=False)))
    out.append("")

out.append("############ STEPS ############")
for k in ["日常_步骤1", "日常_步骤2", "日常_步骤3", "日常_步骤4", "日常_步骤5",
          "日常_步骤6", "日常_步骤7", "日常_收尾", "关卡战斗_入口"]:
    n = pipe.get(k)
    out.append("%s = %s" % (k, json.dumps(n, ensure_ascii=False) if n else "MISSING"))

out.append("")
out.append("############ 关键节点 enabled ############")
for k in sorted(pipe):
    if ("虚轴之庭" in k or "使魔的爱" in k or "活动BONUS" in k):
        out.append("%-36s enabled=%s" % (k, pipe[k].get("enabled", True)))

open(os.path.join(ROOT, "_final.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
