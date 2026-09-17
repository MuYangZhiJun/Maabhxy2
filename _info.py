# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
L = []
L.append("========== 素材清单 ==========")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if os.path.isdir(p):
        L.append("[%s]" % sub)
        for f in sorted(os.listdir(p)):
            L.append("   " + f)
L.append("")
L.append("========== 选项 ==========")
for name, o in iface["option"].items():
    L.append("### %s type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        L.append("  case %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("      %-42s %s" % (k, json.dumps(v, ensure_ascii=False)))
L.append("")
L.append("========== 任务 ==========")
for t in iface["task"]:
    L.append("%s entry=%s option=%s" % (t.get("name"), t.get("entry"), t.get("option")))

open(os.path.join(ROOT, "INFO.txt"), "w", encoding="utf-8").write("\n".join(L))
print("lines", len(L))
