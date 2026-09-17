# -*- coding: utf-8 -*-
"""模拟「关卡战斗」任务：套用 日常模块 + 战斗模式 选项后，看真实可达链。"""
import json, os, sys

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline")
OUT = os.path.join(ROOT, "_sim.txt")

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    lines = [l for l in raw.splitlines() if not l.strip().startswith("//")]
    return json.loads("\n".join(lines))

# 合并所有 pipeline 文件
nodes = {}
for fn in os.listdir(PIPE):
    if fn.endswith(".json"):
        d = load_jsonc(os.path.join(PIPE, fn))
        for k, v in d.items():
            nodes[k] = dict(v)

# interface 选项
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
def apply(option_name, case_names):
    o = iface["option"][option_name]
    for c in o.get("cases", []):
        if c["name"] in case_names:
            for nk, nv in c.get("pipeline_override", {}).items():
                nodes.setdefault(nk, {})
                nodes[nk].update(nv)

apply("日常模块", ["虚轴之庭", "使魔的爱", "活动 BONUS"])
apply("战斗模式", ["自动战斗"])
apply("使用双倍卷", ["No"])

# 该任务入口
task = [t for t in iface["task"] if t["name"] == "关卡战斗"][0]
entry = task["entry"]

def enabled(k):
    return nodes.get(k, {}).get("enabled", True)

out = []
out.append("入口: %s" % entry)
out.append("")
# BFS 打印
seen = set()
stack = [(entry, 0)]
while stack:
    k, d = stack.pop(0)
    if k in seen or d > 6:
        continue
    seen.add(k)
    n = nodes.get(k)
    if n is None:
        out.append("  " * d + f"[缺失] {k}")
        continue
    flag = "" if enabled(k) else "  ❌disabled"
    act = n.get("action", "")
    ca = n.get("custom_action", "")
    tmpl = n.get("template")
    tinfo = f" tmpl={tmpl}" if tmpl else ""
    out.append("  " * d + f"{k}  [{act}{'/'+ca if ca else ''}]{flag}{tinfo}")
    if not enabled(k):
        continue
    for nx in (n.get("next") or []):
        stack.append((nx, d + 1))

out.append("")
out.append("=== 关键节点 enabled 状态 ===")
for k in sorted(nodes):
    if any(x in k for x in ["快捷战斗", "确定", "结算", "选好友", "点好友", "开战", "助战", "双倍券", "打完"]):
        out.append(f"  {'ON ' if enabled(k) else 'off'} {k}")

open(OUT, "w", encoding="utf-8").write("\n".join(out))
print("written", OUT)
