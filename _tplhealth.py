# -*- coding: utf-8 -*-
"""模板体检：每个日常/通用模板在所有 1280x720 debug 截图上的最高分。低于 0.80 视为可疑。"""
import cv2, numpy as np, os, glob

def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = imread_u(f)
        if im is not None and im.shape[:2] == (720, 1280):
            shots.append((f, im))
print("shots:", len(shots))

lines = []
for sub in ["日常", "通用", "启动"]:
    d = os.path.join(IMG, sub)
    if not os.path.isdir(d):
        continue
    for fn in sorted(os.listdir(d)):
        if not fn.lower().endswith(".png"):
            continue
        t = imread_u(os.path.join(d, fn))
        if t is None:
            continue
        best = (0.0, "-")
        for f, im in shots:
            if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
                continue
            try:
                res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
                _, mx, _, _ = cv2.minMaxLoc(res)
                if mx > best[0]:
                    best = (float(mx), os.path.basename(f))
            except Exception:
                pass
        flag = "OK " if best[0] >= 0.80 else ("?? " if best[0] >= 0.60 else "XX ")
        lines.append(f"{flag} {best[0]:.4f}  {sub}/{fn:28s} best@{best[1]}")

lines.sort()
open(os.path.join(ROOT, "_tplhealth.txt"), "w", encoding="utf-8").write("\n".join(lines))
print("done")
