# -*- coding: utf-8 -*-
"""一次导全：素材清单 + 选项真值 + 关键模板实测分。"""
import cv2, numpy as np, os, glob, json

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def rd(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []
L.append("################## 1. 素材清单 ##################")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if not os.path.isdir(p):
        continue
    fs = sorted(os.listdir(p))
    L.append("[%s] %d 张" % (sub, len(fs)))
    for f in fs:
        im = rd(os.path.join(p, f))
        L.append("     %-30s %s" % (f, ("%dx%d" % (im.shape[1], im.shape[0])) if im is not None else "?"))

L.append("")
L.append("################## 2. 选项真值 ##################")
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
for name, o in iface["option"].items():
    L.append("### %s  type=%s  default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        L.append("   -- %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("        %s" % k)
L.append("")
L.append("### 任务")
for t in iface["task"]:
    L.append("%s | entry=%s | option=%s" % (t.get("name"), t.get("entry"), t.get("option")))

L.append("")
L.append("################## 3. 关键模板实测分 ##################")
SHOTS = {}
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = rd(f)
        if im is not None and im.shape[:2] == (720, 1280):
            SHOTS[os.path.basename(f)] = im
L.append("截图 %d 张: %s" % (len(SHOTS), ", ".join(sorted(SHOTS))))
L.append("")
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
        best = (0.0, "-", None)
        for n, im in SHOTS.items():
            if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
                continue
            res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, loc = cv2.minMaxLoc(res)
            if mx > best[0]:
                best = (float(mx), n, loc)
        tag = "OK" if best[0] >= 0.85 else ("??" if best[0] >= 0.70 else "XX")
        L.append("%s %.4f  %-30s best@%-24s box=%s" % (tag, best[0], sub + "/" + fn, best[1], best[2]))

open(os.path.join(ROOT, "Q.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok lines", len(L))
