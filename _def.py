# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

KEEP = ("enabled", "recognition", "template", "roi", "threshold", "action",
        "custom_action", "target", "max_hit", "post_delay", "next")

out = []
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"]:
    out.append("#" * 14 + " " + pre)
    for k in sorted(d):
        if k.startswith(pre):
            n = d[k]
            c = {kk: n[kk] for kk in KEEP if kk in n}
            out.append("%s = %s" % (k, json.dumps(c, ensure_ascii=False)))
    out.append("")

out.append("#" * 14 + " 谁引用 虚轴/使魔/BONUS")
for k, n in d.items():
    nxt = n.get("next") or []
    hit = [x for x in nxt if x.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"))]
    if hit:
        out.append("%s -> %s" % (k, hit))

open(os.path.join(ROOT, "_def.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
