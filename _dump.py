# -*- coding: utf-8 -*-
import json, os, cv2, numpy as np, glob

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

NODES = [
    "日常_虚轴之庭", "日常_虚轴之庭_点卡", "日常_虚轴之庭_点关卡",
    "日常_虚轴之庭_快捷战斗1", "日常_虚轴之庭_确定1", "日常_虚轴之庭_结算1", "日常_虚轴之庭_收尾",
    "日常_使魔的爱", "日常_使魔的爱_点卡", "日常_使魔的爱_快捷战斗1", "日常_使魔的爱_收尾",
    "日常_活动BONUS", "日常_活动BONUS_选好友", "日常_活动BONUS_点好友",
    "日常_活动BONUS_点好友_按坐标", "日常_活动BONUS_开战", "日常_活动BONUS_开战_重试",
    "日常_活动BONUS_助战就绪", "日常_活动BONUS_收尾",
    "日常_活动BONUS_打完_自动", "日常_活动BONUS_打完_挂机",
]
out = []
for k in NODES:
    n = d.get(k)
    out.append("== %s ==" % k)
    out.append(json.dumps(n, ensure_ascii=False))
    out.append("")

# 模板实测
def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = imread_u(f)
        if im is not None and im.shape[:2] == (720, 1280):
            shots.append((os.path.basename(f), im))

out.append("=== 截图清单 (%d) ===" % len(shots))
out.append(", ".join(sorted(n for n, _ in shots)))
out.append("")
out.append("=== 模板实测 ===")
IMG = os.path.join(ROOT, "assets", "resource", "image")
for tp in ["日常/快捷战斗.png", "日常/开战.png", "日常/选择助战好友.png",
           "日常/助战_备用装备.png", "日常/备用装备加成.png", "日常/结算确定.png",
           "日常/快捷战斗确定.png", "日常/虚轴之庭_关卡入口.png"]:
    t = imread_u(os.path.join(IMG, *tp.split("/")))
    if t is None:
        out.append("?? %s 模板不存在" % tp)
        continue
    best = (0.0, "-", None)
    for n, im in shots:
        if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
            continue
        res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), n, loc)
    out.append("%.4f  %-28s best@%-26s box@%s tmpl=%dx%d" % (
        best[0], tp, best[1], best[2], t.shape[1], t.shape[0]))

open(os.path.join(ROOT, "_dump.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
