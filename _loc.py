# -*- coding: utf-8 -*-
import cv2, numpy as np, os, glob

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def rd(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = rd(f)
        if im is not None and im.shape[:2] == (720, 1280):
            shots.append((os.path.relpath(f, ROOT), im))

L = []
L.append("截图 %d 张:" % len(shots))
for n, im in sorted(shots):
    L.append("   " + n)
L.append("")

for tp in ["日常/开战.png", "日常/选择助战好友.png", "日常/助战_备用装备.png",
           "日常/快捷战斗.png", "日常/快捷战斗确定.png", "日常/结算确定.png",
           "日常/备用装备加成.png", "日常/虚轴之庭.png", "日常/虚轴之庭_关卡入口.png",
           "日常/使魔的爱_卡片.png", "日常/活动_难度B.png", "日常/活动_剩余时间.png",
           "日常/活动_BONUS.png", "日常/BONUS详情标题.png", "通用/主界面.png"]:
    fp = os.path.join(IMG, *tp.split("/"))
    if not os.path.exists(fp):
        L.append("-- %s 缺失" % tp); continue
    t = rd(fp)
    rows = []
    for n, im in shots:
        if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
            continue
        res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx >= 0.55:
            rows.append("%.3f@%s" % (mx, loc))
    rows.sort(reverse=True)
    L.append("%-28s %dx%d  %s" % (tp, t.shape[1], t.shape[0], "  ".join(rows[:4]) or "(无>=0.55)"))

open(os.path.join(ROOT, "LOC.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
