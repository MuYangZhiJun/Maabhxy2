# -*- coding: utf-8 -*-
import json, os, subprocess, io

ROOT = r"D:\bh2-maa"

def g(*a):
    return subprocess.run(["git"] + list(a), cwd=ROOT, capture_output=True).stdout.decode("utf-8-sig", "replace")

L = []
L.append("############ GIT ############")
L.append(g("log", "--pretty=%h | %ad | %s", "--date=format:%m-%d %H:%M", "-12"))
L.append("---- HEAD 相对 cfb90bb 的改动文件 ----")
L.append(g("diff", "--stat", "cfb90bb", "HEAD"))
L.append("---- 工作区状态 ----")
L.append(g("status", "--short"))
L.append("---- 远端 ----")
L.append(g("log", "--oneline", "-1", "origin/main") if "origin" in g("remote") else "(无 origin)")
L.append("---- 蓝叉图是否还在 ----")
L.append(str(os.path.exists(os.path.join(ROOT, "assets", "resource", "image", "通用", "回归赠礼_关闭.png"))))

L.append("")
L.append("############ 选项: 日常模块 ############")
raw = open(os.path.join(ROOT, "assets", "interface.json"), encoding="utf-8").read()
iface = json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))
o = iface["option"]["日常模块"]
L.append("type=%s default=%s" % (o.get("type"), o.get("default_case")))
for c in o.get("cases", []):
    L.append("-- case %s" % c.get("name"))
    for k, v in c.get("pipeline_override", {}).items():
        L.append("     %-42s %s" % (k, json.dumps(v, ensure_ascii=False)))

L.append("")
L.append("############ 选项: 自动模式 / 碎水晶 ############")
for nm in ["自动模式", "碎水晶"]:
    o = iface["option"][nm]
    L.append("### %s type=%s default=%s" % (nm, o.get("type"), o.get("default_case")))
    for c in o.get("cases", []):
        L.append("-- case %s" % c.get("name"))
        for k, v in c.get("pipeline_override", {}).items():
            L.append("     %-42s %s" % (k, json.dumps(v, ensure_ascii=False)))

L.append("")
L.append("############ 关卡战斗 task ############")
for t in iface["task"]:
    L.append("%s | entry=%s | option=%s" % (t.get("name"), t.get("entry"), t.get("option")))

io.open(os.path.join(ROOT, "STATE.txt"), "w", encoding="utf-8").write("\n".join(L))
print("written", len(L))
