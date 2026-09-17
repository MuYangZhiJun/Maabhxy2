# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))

iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))
out = []

out.append("###### 选项开关（谁开谁关） ######")
for name, o in iface["option"].items():
    out.append("### %s type=%s default=%s" % (name, o.get("type"), o.get("default_case") or o.get("default")))
    for c in (o.get("cases") or o.get("case") or []):
        ov = c.get("pipeline_override", {})
        on = [k for k, v in ov.items() if isinstance(v, dict) and v.get("enabled") is True]
        off = [k for k, v in ov.items() if isinstance(v, dict) and v.get("enabled") is False]
        out.append("   %-18s ON(%d)=%s" % (repr(c.get("name")), len(on), on[:12]))
        if off:
            out.append("        OFF=%s" % off[:12])
    out.append("")

out.append("###### BONUS 全部节点 ######")
for k in sorted(d):
    if "活动BONUS" in k:
        n = d[k]
        out.append("%-34s en=%-5s act=%s/%s tmpl=%s roi=%s target=%s next=%s" % (
            k, n.get("enabled"), n.get("action", ""), n.get("custom_action", ""),
            n.get("template"), n.get("roi"), n.get("target"), n.get("next")))
out.append("")

out.append("###### 虚轴/使魔 快捷战斗链 ######")
for k in sorted(d):
    if ("虚轴之庭" in k or "使魔的爱" in k) and ("快捷战斗" in k or "确定" in k or "结算" in k):
        n = d[k]
        out.append("%-34s en=%-5s tmpl=%s roi=%s next=%s" % (
            k, n.get("enabled"), n.get("template"), n.get("roi"), n.get("next")))
out.append("")

out.append("###### 模板实测关键分 ######")
out.append(open(os.path.join(ROOT, "_cand.txt"), encoding="utf-8").read())

open(os.path.join(ROOT, "_plan.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok", len(out))
