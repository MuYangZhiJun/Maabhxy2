# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
L = []
L.append("========== gui/config/instances/default.json ==========")
p = os.path.join(ROOT, "gui", "config", "instances", "default.json")
try:
    L.append(open(p, encoding="utf-8-sig").read())
except Exception as e:
    L.append("ERR %s" % e)
L.append("")
L.append("========== 步骤链 ==========")
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
for k in sorted(d):
    if k.startswith(("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗")):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)))
open(os.path.join(ROOT, "STEP.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
