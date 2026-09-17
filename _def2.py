# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
d = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

KEYS = [
    "关卡战斗_入口",
    # 虚轴
    "日常_虚轴之庭", "日常_虚轴之庭_点卡", "日常_虚轴之庭_点关卡",
    "日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_确定1", "日常_虚轴之庭_结算1",
    "日常_虚轴之庭_快捷战斗2", "日常_虚轴之庭_确定2", "日常_虚轴之庭_结算2",
    "日常_虚轴之庭_回列表", "日常_虚轴之庭_开列表", "日常_虚轴之庭_收尾",
    # 使魔
    "日常_使魔的爱", "日常_使魔的爱_点卡",
    "日常_使魔的爱_快捷战斗1", "日常_使魔的爱_确定1", "日常_使魔的爱_结算1",
    "日常_使魔的爱_回列表", "日常_使魔的爱_收尾",
    # BONUS
    "日常_活动BONUS", "日常_活动BONUS_进活动", "日常_活动BONUS_点左上",
    "日常_活动BONUS_选好友", "日常_活动BONUS_点好友", "日常_活动BONUS_点好友_按坐标",
    "日常_活动BONUS_开战", "日常_活动BONUS_开战_重试", "日常_活动BONUS_助战就绪",
    "日常_活动BONUS_打完_自动", "日常_活动BONUS_收尾", "日常_活动BONUS_点左上2",
    "日常_活动BONUS_回列表",
]
out = []
for k in KEYS:
    n = d.get(k)
    if n is None:
        out.append("### %s  【不存在】" % k)
        continue
    out.append("### %s" % k)
    out.append(json.dumps(n, ensure_ascii=False))
open(os.path.join(ROOT, "DEF.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
