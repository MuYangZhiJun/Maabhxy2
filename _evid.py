# -*- coding: utf-8 -*-
"""把「关卡战斗」相关的一切证据导出为可读文本。"""
import json, os

ROOT = r"D:\bh2-maa"

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))

L = []
L.append("###################### OPTIONS ######################")
for name, o in iface["option"].items():
    L.append("")
    L.append("=== OPTION %s  type=%s  default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        L.append("  -- case %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("       %-40s %s" % (k, json.dumps(v, ensure_ascii=False)))

L.append("")
L.append("###################### 节点定义 ######################")
KEEP = ("enabled", "recognition", "template", "roi", "threshold", "action",
        "custom_action", "target", "max_hit", "post_delay", "next")
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "日常_步骤", "关卡战斗_"]:
    L.append("")
    L.append("========== %s ==========" % pre)
    for k in sorted(pipe):
        if k.startswith(pre):
            n = pipe[k]
            c = {kk: n[kk] for kk in KEEP if kk in n}
            L.append("%s" % k)
            L.append("    %s" % json.dumps(c, ensure_ascii=False))

L.append("")
L.append("###################### 引用索引 ######################")
for k, n in pipe.items():
    nxt = n.get("next") or []
    hit = [x for x in nxt if x.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "日常_步骤", "关卡战斗_"))]
    if hit:
        L.append("%-34s -> %s" % (k, hit))

open(os.path.join(ROOT, "EVID.txt"), "w", encoding="utf-8").write("\n".join(L))
print("lines", len(L))
