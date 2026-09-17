# -*- coding: utf-8 -*-
import json, os, cv2, numpy as np

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
IMG = os.path.join(ROOT, "assets", "resource", "image")
d = json.load(open(PIPE, encoding="utf-8"))

def imread_u(p):
    return cv2.imdecode(np.fromfile(p, dtype=np.uint8), cv2.IMREAD_COLOR)

out = []
out.append("########## 节点原文 ##########")
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS", "日常_步骤"]:
    for k in sorted(d):
        if k.startswith(pre):
            n = d[k]
            keep = {kk: n[kk] for kk in ("enabled", "recognition", "template", "roi", "threshold",
                                          "action", "custom_action", "target", "max_hit", "next")
                    if kk in n}
            out.append("%s = %s" % (k, json.dumps(keep, ensure_ascii=False)))
    out.append("")

out.append("########## 模板文件 ##########")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(IMG, sub)
    if os.path.isdir(p):
        out.append("[%s] %s" % (sub, " | ".join(sorted(os.listdir(p)))))

out.append("")
out.append("########## 关键模板 4张实拍实测 ##########")
shots = {}
for nm in ["comb1", "comb2", "comb3", "fz_dlg"]:
    p = os.path.join(ROOT, "debug", nm + ".png")
    if os.path.exists(p):
        shots[nm] = imread_u(p)
out.append("shots: %s" % list(shots))
TESTS = ["日常/虚轴之庭.png", "日常/多元裂缝.png", "日常/出击.png", "日常/快捷战斗.png",
         "日常/快捷战斗确定.png", "日常/结算确定.png", "日常/使魔的爱_卡片.png",
         "日常/选择助战好友.png", "日常/开战.png", "日常/活动_BONUS.png",
         "通用/主界面.png", "日常/返回箭头.png", "通用/返回箭头.png"]
for tp in TESTS:
    fp = os.path.join(IMG, *tp.split("/"))
    if not os.path.exists(fp):
        out.append("-- %s 不存在" % tp)
        continue
    t = imread_u(fp)
    row = []
    for nm, im in shots.items():
        if t.shape[0] > im.shape[0] or t.shape[1] > im.shape[1]:
            row.append("%s:--" % nm); continue
        res = cv2.matchTemplate(im, t, cv2.TM_CCOEFF_NORMED)
        _, mx, _, loc = cv2.minMaxLoc(res)
        row.append("%s:%.3f@%s" % (nm, mx, loc))
    out.append("%-26s %s  tmpl=%dx%d" % (tp, "  ".join(row), t.shape[1], t.shape[0]))

open(os.path.join(ROOT, "_full.txt"), "w", encoding="utf-8").write("\n".join(out))
print("lines", len(out))
