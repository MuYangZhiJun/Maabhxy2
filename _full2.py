# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

prefs = ("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗", "日常_活动BONUS",
         "日常_虚轴之庭", "日常_使魔的爱")
L = []
for k in sorted(d):
    if k.startswith(prefs):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
open(os.path.join(ROOT, "FULL.txt"), "w", encoding="utf-8").write("\n".join(L))
print("nodes", len(L))
