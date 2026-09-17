# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

L = []
L.append("############ OPTION: 日常模块 ############")
o = iface["option"]["日常模块"]
L.append("type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in (o.get("cases") or o.get("case") or []):
    L.append("")
    L.append("-- case %s" % c.get("name"))
    for k, v in c.get("pipeline_override", {}).items():
        L.append("     %-42s %s" % (k, json.dumps(v, ensure_ascii=False)))

L.append("")
L.append("############ OPTION: 战斗模式 ############")
o = iface["option"]["战斗模式"]
L.append("type=%s default=%s" % (o.get("type"), o.get("default_case") or o.get("default")))
for c in (o.get("cases") or o.get("case") or []):
    L.append("-- case %s -> %s" % (c.get("name"), list(c.get("pipeline_override", {}).keys())))

L.append("")
L.append("############ 快捷战斗链 定义 ############")
for pre in ["日常_虚轴之庭", "日常_使魔的爱"]:
    for k in sorted(pipe):
        if k.startswith(pre) and any(x in k for x in ["快捷战斗", "确定", "结算", "点卡", "点关卡", "收尾", "逃逸"]):
            n = pipe[k]
            L.append("%-28s en=%-5s tmpl=%-24s roi=%s thr=%s tgt=%s next=%s" % (
                k, n.get("enabled", True), str(n.get("template")), n.get("roi"),
                n.get("threshold"), n.get("target"), n.get("next")))

L.append("")
L.append("############ BONUS 链 定义 ############")
for k in sorted(pipe):
    if k.startswith("日常_活动BONUS"):
        n = pipe[k]
        L.append("%-30s en=%-5s ca=%-18s tmpl=%-22s roi=%s thr=%s next=%s" % (
            k.replace("日常_活动BONUS", "BONUS"), n.get("enabled", True), str(n.get("custom_action")),
            str(n.get("template")), n.get("roi"), n.get("threshold"), n.get("next")))

open(os.path.join(ROOT, "SW.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok")
