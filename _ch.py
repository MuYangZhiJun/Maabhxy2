# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

KEYS = [
    "关卡战斗_入口", "日常_开始", "日常_步骤1", "日常_步骤2", "日常_步骤3",
    "日常_步骤4", "日常_步骤5", "日常_步骤6", "日常_步骤7", "日常_收尾",
    "日常_虚轴之庭", "日常_虚轴之庭_点卡", "日常_虚轴之庭_点关卡",
    "日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_确定1", "日常_虚轴之庭_结算1",
    "日常_虚轴之庭_回列表", "日常_虚轴之庭_收尾", "日常_虚轴之庭_逃逸",
    "日常_使魔的爱", "日常_使魔的爱_点卡",
    "日常_使魔的爱_快捷战斗1", "日常_使魔的爱_确定1", "日常_使魔的爱_结算1",
    "日常_使魔的爱_收尾", "日常_使魔的爱_逃逸",
    "日常_活动BONUS", "日常_活动BONUS_进活动", "日常_活动BONUS_点左上",
    "日常_活动BONUS_选好友", "日常_活动BONUS_点好友", "日常_活动BONUS_点好友_按坐标",
    "日常_活动BONUS_开战", "日常_活动BONUS_开战_重试", "日常_活动BONUS_助战就绪",
    "日常_活动BONUS_打完_自动", "日常_活动BONUS_收尾", "日常_活动BONUS_回列表",
]
L = []
for k in KEYS:
    n = d.get(k)
    if n is None:
        L.append("%-34s 【不存在】" % k)
        continue
    t = n.get("template")
    t = ("|".join(t) if isinstance(t, list) else str(t)) if t else "-"
    L.append("%-34s en=%-5s tmpl=%-46s roi=%-18s thr=%-5s act=%-8s ca=%-16s tgt=%-16s next=%s" % (
        k, n.get("enabled", True), t[:46], str(n.get("roi"))[:18], n.get("threshold"),
        n.get("action", ""), n.get("custom_action", ""), str(n.get("target"))[:16], n.get("next")))
open(os.path.join(ROOT, "CH.txt"), "w", encoding="utf-8").write("\n".join(L))
for x in L:
    print(x)
