# -*- coding: utf-8 -*-
"""只查「关卡战斗」这条链的关键模板，限量截图，快速出分。"""
import cv2, numpy as np, os, glob

def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

# 只挑可能相关的截图名
KEY = ["live_", "sm", "dp", "fz", "bonus", "bn1", "act", "now", "seq", "comb", "cyc",
       "s1", "s2", "s3", "after_", "stuck", "user_now", "home_now", "nav_battle", "x1", "y1", "z1"]
shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        b = os.path.basename(f)
        if any(k in b for k in KEY):
            im = imread_u(f)
            if im is not None and im.shape[:2] == (720, 1280):
                shots.append((b, im))
print("shots:", len(shots))

TARGETS = [
    "日常/虚轴之庭.png", "日常/虚轴之庭_关卡入口.png", "日常/快捷战斗.png",
    "日常/快捷战斗确定.png", "日常/结算确定.png", "日常/使魔的爱_卡片.png",
    "日常/选择助战好友.png", "日常/助战_备用装备.png", "日常/开战.png",
    "日常/备用装备加成.png", "日常/活动_BONUS.png", "日常/BONUS详情标题.png",
    "日常/活动_难度B.png", "日常/活动_剩余时间.png", "通用/主界面.png",
]
lines = []
for tp in TARGETS:
    t = imread_u(os.path.join(IMG, *tp.split("/")))
    if t is None:
        lines.append(f"?? {tp} 模板读不到"); continue
    best = (0.0, "-")
    for b, im in shots:
        if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
            continue
        res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, _ = cv2.minMaxLoc(res)
        if mx > best[0]:
            best = (float(mx), b)
    flag = "OK " if best[0] >= 0.85 else ("?? " if best[0] >= 0.70 else "XX ")
    lines.append(f"{flag} {best[0]:.4f}  {tp:32s} best@{best[1]}  tmpl={t.shape[1]}x{t.shape[0]}")

open(os.path.join(ROOT, "_key.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("done")
