# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

def short(n, k):
    v = n.get(k)
    if k == "next" and isinstance(v, list):
        return "[" + ",".join(x.replace("日常_", "") for x in v) + "]"
    if isinstance(v, list):
        return str(v)
    return str(v)

KEYS = []
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"]:
    KEYS += [k for k in d if k.startswith(pre)]

L = []
for k in sorted(KEYS):
    n = d[k]
    L.append("%s | en=%s tmpl=%s tgt=%s thr=%s | next=%s" % (
        k.replace("日常_", ""),
        n.get("enabled", True),
        short(n, "template"),
        short(n, "target"),
        n.get("threshold"),
        short(n, "next")))
open(os.path.join(ROOT, "DUMP.txt"), "w", encoding="utf-8").write("\n".join(L))
print("nodes", len(L))
