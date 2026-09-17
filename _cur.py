# -*- coding: utf-8 -*-
import json, os, sys, io

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline")
L = []

def load(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

d = json.load(open(os.path.join(PIPE, "30_清日常.json"), encoding="utf-8"))
L.append("### 30_清日常 节点数 %d" % len(d))

L.append("")
L.append("### 三模块 next ###")
for k in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS",
          "日常_虚轴之庭_收尾", "日常_使魔的爱_收尾", "日常_活动BONUS_收尾"]:
    n = d.get(k)
    L.append("%-24s en=%-5s ca=%-14s tmpl=%s" % (k, (n or {}).get("enabled", True),
             (n or {}).get("custom_action"), (n or {}).get("template")))
    L.append("      next=%s" % ((n or {}).get("next"),))

L.append("")
L.append("### 步骤链 ###")
for k in sorted(d):
    if k.startswith(("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗")):
        L.append("%s = %s" % (k, json.dumps(d[k], ensure_ascii=False)[:300]))

L.append("")
L.append("### 快捷战斗/开战/选好友/打完 节点 enabled ###")
for k in sorted(d):
    if any(x in k for x in ["快捷战斗", "开战", "选好友", "打完", "助战", "结算"]):
        n = d[k]
        L.append("%-34s en=%-5s ca=%-14s next=%s" % (k, n.get("enabled", True),
                 n.get("custom_action"), n.get("next")))

L.append("")
L.append("### 回归赠礼/关弹窗/签到/存在感 相关 ###")
for k in sorted(d):
    if any(x in k for x in ["回归赠礼", "关弹窗", "签到", "存在感", "每周", "吼姆"]):
        n = d[k]
        L.append("%-34s en=%-5s tmpl=%s thr=%s tgt=%s next=%s" % (
            k, n.get("enabled", True), n.get("template"), n.get("threshold"),
            n.get("target"), n.get("next")))

L.append("")
L.append("### 使魔探险/派遣 ###")
for k in sorted(d):
    if "使魔探险" in k or "派遣" in k:
        n = d[k]
        L.append("%-34s en=%-5s tmpl=%s thr=%s tgt=%s next=%s" % (
            k, n.get("enabled", True), n.get("template"), n.get("threshold"),
            n.get("target"), n.get("next")))

# 图片清单
L.append("")
L.append("### 图片模板 ###")
for sub in ["日常", "通用", "启动"]:
    p = os.path.join(ROOT, "assets", "resource", "image", sub)
    if os.path.isdir(p):
        L.append("[%s] %s" % (sub, " | ".join(sorted(os.listdir(p)))))

io.open(os.path.join(ROOT, "CUR.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
