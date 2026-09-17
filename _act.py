# -*- coding: utf-8 -*-
import re, os, json, io

ROOT = r"D:\bh2-maa"
AG = os.path.join(ROOT, "agent")

L = []
# 1) 所有注册的 custom action 名
L.append("########## 注册的动作 ##########")
for fn in os.listdir(AG):
    if not fn.endswith(".py"):
        continue
    s = open(os.path.join(AG, fn), encoding="utf-8").read()
    L.append("=== %s ===" % fn)
    for m in re.finditer(r'@(?:\w+)\.custom_action\(\s*["\']([^"\']+)["\']', s):
        L.append("   @custom_action(%s)" % m.group(1))
    for m in re.finditer(r'@(?:\w+)\.\w*[Aa]ction\w*\(\s*["\']?([^"\')]*?)["\']?\s*\)', s):
        L.append("   @action-like: %s" % m.group(1))
    for m in re.finditer(r'(AgentServer|self)\.register\w*\(\s*["\']([^"\']+)["\']', s):
        L.append("   register: %s" % m.group(2))
    for m in re.finditer(r'class\s+(\w+)', s):
        L.append("   class %s" % m.group(1))
L.append("")

# 2) 哪些节点用了 custom_action
L.append("########## pipeline 里用到 custom_action 的节点 ##########")
for fn in os.listdir(os.path.join(ROOT, "assets", "resource", "pipeline")):
    p = os.path.join(ROOT, "assets", "resource", "pipeline", fn)
    d = json.load(open(p, encoding="utf-8"))
    for k, v in d.items():
        if v.get("custom_action"):
            L.append("%s :: %s -> %s (en=%s)" % (fn, k, v["custom_action"], v.get("enabled", True)))

open(os.path.join(ROOT, "ACT.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
