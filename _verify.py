# -*- coding: utf-8 -*-
import json, os, re, io

ROOT = r"D:\bh2-maa"
L = []

# 1) agent 注册的动作名
L.append("########## agent 动作注册 ##########")
for fn in ["my_action.py", "my_bonus.py", "main.py", "my_reco.py"]:
    p = os.path.join(ROOT, "agent", fn)
    if not os.path.exists(p):
        continue
    s = open(p, encoding="utf-8").read()
    L.append("=== %s ===" % fn)
    for m in re.finditer(r'@\w+\.\w*(?:action|Action)\w*\(\s*["\']([^"\']+)["\']', s):
        L.append("   decorator action: %s" % m.group(1))
    for m in re.finditer(r'def\s+(\w+)\s*\(', s):
        L.append("   def %s" % m.group(1))
L.append("")

# 2) 关键节点原文
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
L.append("########## 关键节点原文 ##########")
for k in ["日常_虚轴之庭", "日常_虚轴之庭_点卡", "日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_确定1",
          "日常_虚轴之庭_结算1", "日常_虚轴之庭_收尾", "日常_虚轴之庭_逃逸", "日常_虚轴之庭_翻页",
          "日常_使魔的爱", "日常_使魔的爱_点卡", "日常_使魔的爱_快捷战斗1", "日常_使魔的爱_确定1",
          "日常_使魔的爱_收尾", "日常_使魔的爱_逃逸",
          "日常_活动BONUS", "日常_活动BONUS_选好友", "日常_活动BONUS_点好友",
          "日常_活动BONUS_开战", "日常_活动BONUS_打完_自动", "日常_活动BONUS_收尾",
          "日常_步骤5", "日常_步骤6", "日常_步骤7"]:
    n = d.get(k)
    L.append("%s = %s" % (k, json.dumps(n, ensure_ascii=False) if n else "【不存在】"))
L.append("")

# 3) 所有含 BONUS/虚轴/使魔 的节点名
L.append("########## 节点名全表 ##########")
for k in sorted(d):
    if k.startswith(("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS")):
        L.append("   %s  en=%s" % (k, d[k].get("enabled", True)))

open(os.path.join(ROOT, "VERIFY.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
