# -*- coding: utf-8 -*-
"""一次导出：模板实测分 + 步骤链 + 选项真值 + 素材清单。"""
import json, os, glob, cv2, numpy as np

ROOT = r"D:\bh2-maa"
IMG = os.path.join(ROOT, "assets", "resource", "image")

def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

L = []

# 1) 素材清单
L.append("################## 素材清单 ##################")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if os.path.isdir(p):
        L.append("[%s] %d" % (sub, len(os.listdir(p))))
        for f in sorted(os.listdir(p)):
            sz = os.path.getsize(os.path.join(p, f))
            im = imread_u(os.path.join(p, f))
            dim = "%dx%d" % (im.shape[1], im.shape[0]) if im is not None else "?"
            L.append("    %-30s %-10s %d B" % (f, dim, sz))
L.append("")

# 2) 模板实测分（全部截图）
shots = []
for base in [os.path.join(ROOT, "debug"), os.path.join(ROOT, "gui", "debug")]:
    for f in glob.glob(os.path.join(base, "*.png")):
        im = imread_u(f)
        if im is not None and im.shape[:2] == (720, 1280):
            shots.append((os.path.basename(f), im))
L.append("################## 模板实测分 (截图%d张) ##################" % len(shots))
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if not os.path.isdir(p):
        continue
    for fn in sorted(os.listdir(p)):
        if not fn.lower().endswith(".png"):
            continue
        t = imread_u(os.path.join(p, fn))
        if t is None:
            continue
        best = (0.0, "-")
        for n, im in shots:
            if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
                continue
            res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
            _, mx, _, _ = cv2.minMaxLoc(res)
            if mx > best[0]:
                best = (float(mx), n)
        L.append("%s %.4f  %-32s best@%s" % (
            "OK" if best[0] >= 0.85 else ("??" if best[0] >= 0.70 else "XX"),
            best[0], sub + "/" + fn, best[1]))
L.append("")

# 3) 步骤链 + 入口
pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
L.append("################## 步骤链 ##################")
for k in sorted(pipe):
    if k.startswith(("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗", "启动_等主界面", "日常_每日签到", "日常_回归赠礼")):
        n = pipe[k]
        L.append("%-28s en=%-5s ca=%-16s tmpl=%-22s next=%s" % (
            k, n.get("enabled", True), str(n.get("custom_action")), str(n.get("template")), n.get("next")))
L.append("")

# 4) 选项真值
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
L.append("################## 选项真值 ##################")
for name, o in iface["option"].items():
    L.append("### %s type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        L.append("  -- %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("      %-42s %s" % (k, json.dumps(v, ensure_ascii=False)))
L.append("")

# 5) task
L.append("################## TASKS ##################")
for t in iface["task"]:
    L.append("%s entry=%s opts=%s" % (t.get("name"), t.get("entry"), t.get("option")))

open(os.path.join(ROOT, "ALL.txt"), "w", encoding="utf-8").write("\n".join(L))
print("lines", len(L))
