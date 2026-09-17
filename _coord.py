# -*- coding: utf-8 -*-
"""一次算准：按钮坐标 + 选项真值 + 截图清单。"""
import cv2, numpy as np, os, glob, json

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def rd(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

def loc(tp, shot):
    t = rd(os.path.join(IMG, *tp.split("/")))
    im = rd(shot)
    if t is None or im is None:
        return None
    if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
        return "模板比截图大"
    res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
    _, mx, _, l = cv2.minMaxLoc(res)
    cx, cy = l[0] + t.shape[1] // 2, l[1] + t.shape[0] // 2
    return "%.4f box=(%d,%d) size=%dx%d center=(%d,%d)" % (mx, l[0], l[1], t.shape[1], t.shape[0], cx, cy)

L = []
L.append("### 快捷战斗.png on fz_dlg.png : %s" % loc("日常/快捷战斗.png", os.path.join(ROOT, "debug", "fz_dlg.png")))
L.append("### 快捷战斗确定.png on fz_dlg.png : %s" % loc("日常/快捷战斗确定.png", os.path.join(ROOT, "debug", "fz_dlg.png")))
L.append("### 选择助战好友.png on dp5.png : %s" % loc("日常/选择助战好友.png", os.path.join(ROOT, "debug", "dp5.png")))
L.append("### 开战.png on dp5.png : %s" % loc("日常/开战.png", os.path.join(ROOT, "debug", "dp5.png")))
L.append("")
L.append("### debug 截图清单")
for base in ["debug", os.path.join("gui", "debug")]:
    p = os.path.join(ROOT, base)
    if os.path.isdir(p):
        for f in sorted(os.listdir(p)):
            if f.lower().endswith(".png"):
                im = rd(os.path.join(p, f))
                L.append("   %-40s %s" % (base + "/" + f, ("%dx%d" % (im.shape[1], im.shape[0])) if im is not None else "?"))
open(os.path.join(ROOT, "COORD.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
