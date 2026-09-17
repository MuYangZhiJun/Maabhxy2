# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
lines = []
for k in sorted(d):
    if k.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "日常_步骤", "关卡战斗")):
        n = d[k]
        lines.append("%s|en=%s|act=%s%s|tmpl=%s|roi=%s|thr=%s|tgt=%s|next=%s" % (
            k, n.get("enabled", True), n.get("action", ""),
            ("/"+n["custom_action"]) if n.get("custom_action") else "",
            n.get("template"), n.get("roi"), n.get("threshold"), n.get("target"), n.get("next")))
open(os.path.join(ROOT, "z.txt"), "w", encoding="utf-8").write("\n".join(lines))
print(len(lines))
