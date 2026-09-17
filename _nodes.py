# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

out = []
for prefix in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "关卡战斗"]:
    out.append("########## %s ##########" % prefix)
    for k in sorted(d):
        if k.startswith(prefix):
            out.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
    out.append("")

# 谁引用这些
out.append("########## 引用索引 ##########")
for k, n in d.items():
    nxt = n.get("next") or []
    hit = [x for x in nxt if x.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "关卡战斗"))]
    if hit:
        out.append("%s -> %s" % (k, hit))

open(os.path.join(ROOT, "_nodes.txt"), "w", encoding="utf-8").write("\n".join(out))
print("lines", len(out))
