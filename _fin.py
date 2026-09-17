# -*- coding: utf-8 -*-
"""最终取证：素材清单 + 候选模板在各真实截图上的分数。"""
import cv2, numpy as np, os, glob, json

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def rd(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

L = []
# 1) 素材清单
L.append("########## 素材清单 ##########")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if os.path.isdir(p):
        L.append("[%s] %d 张" % (sub, len(os.listdir(p))))
        for f in sorted(os.listdir(p)):
            im = rd(os.path.join(p, f))
            dim = "%dx%d" % (im.shape[1], im.shape[0]) if im is not None else "?"
            L.append("    %-30s %s" % (f, dim))
L.append("")

# 2) 所有截图
SHOTS = {}
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = rd(f)
        if im is not None and im.shape[:2] == (720, 1280):
            SHOTS[os.path.basename(f)] = im
L.append("########## 截图 %d 张 ##########" % len(SHOTS))
L.append(", ".join(sorted(SHOTS)))
L.append("")

# 3) 模板实测（全部模板 x 全部截图，取最高）
L.append("########## 模板实测最高分 ##########")
rows = []
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if not os.path.isdir(p):
        continue
    for fn in sorted(os.listdir(p)):
        if not fn.lower().endswith(".png"):
            continue
        t = rd(os.path.join(p, fn))
        if t is None:
            continue
        best = (0.0, "-")
        for n, im in SHOTS.items():
            if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
                continue
            res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, _ = cv2.minMaxLoc(res)
            if mx > best[0]:
                best = (float(mx), n)
        tag = "OK" if best[0] >= 0.85 else ("??" if best[0] >= 0.70 else "XX")
        rows.append((best[0], "%s %.4f %-32s best@%s" % (tag, best[0], sub + "/" + fn, best[1])))
rows.sort()
L.extend(r[1] for r in rows)

open(os.path.join(ROOT, "FINAL.txt"), "w", encoding="utf-8").write("\n".join(L))
print("lines", len(L))
