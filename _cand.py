# -*- coding: utf-8 -*-
"""测候补模板在全部相关截图上的最高分。"""
import cv2, numpy as np, os, glob

def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

KEY = ["comb", "fz", "bonus", "bn1", "bn2", "act", "seq", "cyc", "live", "sm", "dp",
       "now", "battle", "real", "b1", "b2", "c1", "e1", "g1", "w1", "u1", "n1"]
shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        b = os.path.basename(f)
        if any(k in b for k in KEY):
            im = imread_u(f)
            if im is not None and im.shape[:2] == (720, 1280):
                shots.append((b, im))
print("shots:", len(shots), sorted(n for n, _ in shots))

TESTS = ["日常/选择助战好友.png", "日常/开战.png", "日常/战斗结算.png", "日常/结算确定.png",
         "通用/确定.png", "日常/奖励领取_确定.png", "日常/再次挑战.png", "日常/已领取奖励.png",
         "日常/使用双倍券.png", "日常/助战_备用装备.png", "日常/备用装备加成.png",
         "日常/活动_BONUS.png", "日常/BONUS详情标题.png", "日常/快捷战斗.png",
         "日常/快捷战斗确定.png", "日常/虚轴之庭.png", "日常/使魔的爱_卡片.png",
         "日常/使魔的爱.png", "通用/返回箭头.png", "日常/出击.png"]

lines = []
for tp in TESTS:
    fp = os.path.join(IMG, *tp.split("/"))
    if not os.path.exists(fp):
        lines.append("-- %s 不存在" % tp); continue
    t = imread_u(fp)
    best = (0.0, "-", None)
    for n, im in shots:
        if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
            continue
        res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), n, loc)
    lines.append("%.4f  %-26s best@%-24s box=%s  tmpl=%dx%d" % (
        best[0], tp, best[1], best[2], t.shape[1], t.shape[0]))

open(os.path.join(ROOT, "_cand.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("done")
