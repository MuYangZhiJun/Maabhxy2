# -*- coding: utf-8 -*-
"""修「关卡战斗」：
1) 虚轴之庭 / 使魔的爱：走「快捷战斗 → 确定」扫荡链，节点在 pipeline 里直接 enabled=True
   （不再依赖选项，之前默认关着 → 收尾立刻抢走 → 没打就跳）
2) 活动 BONUS：必须「选择助战好友 → 点好友 → 开战 → bonus_battle 真打」
   - 开战.png 是死模板(0.497)，改为点底部大按钮（与“选择助战好友”同一位置）
   - 打完_自动(custom bonus_battle) 打开
3) 所有 next 里把无识别的 收尾/逃逸 放到最后，杜绝抢跑
4) 结算确定.png 死模板(0.475)，扫荡链不再依赖它
"""
import json, os

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

def N(k):
    if k not in d:
        raise KeyError(k)
    return d[k]

# ======================= 1. 虚轴之庭：扫荡 =======================
N("日常_虚轴之庭")["next"] = ["日常_虚轴之庭_点卡", "日常_虚轴之庭_翻页", "日常_虚轴之庭_收尾"]
N("日常_虚轴之庭_点卡")["next"] = ["日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_点卡", "日常_虚轴之庭_收尾"]

sc = N("日常_虚轴之庭_快捷战斗1")
sc["enabled"] = True
sc["next"] = ["日常_虚轴之庭_确定1", "日常_虚轴之庭_收尾"]

cf = N("日常_虚轴之庭_确定1")
cf["enabled"] = True
cf["next"] = ["日常_虚轴之庭_收尾"]        # 扫荡确认后即完成（结算确定.png 是死模板，不依赖）

N("日常_虚轴之庭_结算1")["enabled"] = False
N("日常_虚轴之庭_逃逸")["next"] = ["日常_虚轴之庭_收尾"]
N("日常_虚轴之庭_收尾")["next"] = ["日常_步骤5"]

# 开列表/点关卡/回列表/进多元：不再从主链引用，禁用避免干扰
for k in ["日常_虚轴之庭_开列表", "日常_虚轴之庭_点关卡", "日常_虚轴之庭_回列表", "日常_虚轴之庭_进多元"]:
    d[k]["enabled"] = False

# ======================= 2. 使魔的爱：扫荡 =======================
N("日常_使魔的爱")["next"] = ["日常_使魔的爱_点卡", "日常_使魔的爱_翻页", "日常_使魔的爱_收尾"]
N("日常_使魔的爱_点卡")["next"] = ["日常_使魔的爱_快捷战斗1", "日常_使魔的爱_点卡", "日常_使魔的爱_收尾"]

sc = N("日常_使魔的爱_快捷战斗1")
sc["enabled"] = True
sc["next"] = ["日常_使魔的爱_确定1", "日常_使魔的爱_收尾"]

cf = N("日常_使魔的爱_确定1")
cf["enabled"] = True
cf["next"] = ["日常_使魔的爱_收尾"]

N("日常_使魔的爱_结算1")["enabled"] = False
N("日常_使魔的爱_逃逸")["next"] = ["日常_使魔的爱_收尾"]
N("日常_使魔的爱_收尾")["next"] = ["日常_步骤6"]

for k in ["日常_使魔的爱_开列表", "日常_使魔的爱_回列表", "日常_使魔的爱_进多元"]:
    d[k]["enabled"] = False

# ======================= 3. 活动 BONUS：选助战 → 真打 =======================
b = N("日常_活动BONUS")
b["enabled"] = True                       # 不再依赖选项
b["next"] = ["日常_活动BONUS_选好友", "日常_活动BONUS_收尾"]

xg = N("日常_活动BONUS_选好友")
xg["enabled"] = True
xg["template"] = "日常/选择助战好友.png"
xg["roi"] = [400, 580, 700, 160]
xg["threshold"] = 0.90
xg["action"] = "Click"
xg.pop("target", None)                    # 点识别到的按钮中心
xg["post_delay"] = 3500
xg["next"] = ["日常_活动BONUS_点好友", "日常_活动BONUS_开战", "日常_活动BONUS_收尾"]

dh = N("日常_活动BONUS_点好友")
dh["enabled"] = True
dh["template"] = "日常/助战_备用装备.png"
dh["roi"] = [200, 150, 900, 400]
dh["threshold"] = 0.90
dh["action"] = "Click"
dh.pop("target", None)
dh["post_delay"] = 4500
dh["next"] = ["日常_活动BONUS_开战", "日常_活动BONUS_收尾"]

kz = N("日常_活动BONUS_开战")
kz["enabled"] = True
kz.pop("recognition", None)
kz.pop("template", None)
kz.pop("threshold", None)
kz.pop("roi", None)
kz["action"] = "Click"
kz["target"] = [620, 600, 200, 100]       # 底部大按钮（与“选择助战好友”同槽位，选完好友后变“开战”）
kz["max_hit"] = 2
kz["post_delay"] = 6000
kz["next"] = ["日常_活动BONUS_打完_自动", "日常_活动BONUS_收尾"]

pd = N("日常_活动BONUS_打完_自动")
pd["enabled"] = True
pd["action"] = "Custom"
pd["custom_action"] = "bonus_battle"
pd["next"] = ["日常_活动BONUS_收尾"]

N("日常_活动BONUS_收尾")["enabled"] = True
N("日常_活动BONUS_收尾")["next"] = ["日常_步骤7"]

# 盲点重试：降级为后备，放在“开战”之后由开战自身兜底；这里停用避免抢跑
N("日常_活动BONUS_开战_重试")["enabled"] = False
N("日常_活动BONUS_点好友_按坐标")["enabled"] = False
N("日常_活动BONUS_双倍券")["enabled"] = False
N("日常_活动BONUS_翻页")["enabled"] = False
N("日常_活动BONUS_助战就绪")["enabled"] = False
N("日常_活动BONUS_回列表")["enabled"] = False
N("日常_活动BONUS_进活动")["enabled"] = False

with open(PIPE, "w", encoding="utf-8", newline="\n") as f:
    f.write(json.dumps(d, ensure_ascii=False, indent=4) + "\n")

print("已写回。关键链：")
for k in ["日常_虚轴之庭", "日常_虚轴之庭_点卡", "日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_确定1",
          "日常_虚轴之庭_收尾", "日常_使魔的爱_快捷战斗1", "日常_使魔的爱_收尾",
          "日常_活动BONUS", "日常_活动BONUS_选好友", "日常_活动BONUS_点好友",
          "日常_活动BONUS_开战", "日常_活动BONUS_打完_自动", "日常_活动BONUS_收尾"]:
    n = d[k]
    print("  %-30s en=%-5s next=%s" % (k, n.get("enabled", True), n.get("next")))
