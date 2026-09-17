# -*- coding: utf-8 -*-
import json, os

ROOT = r"D:\bh2-maa"
PIPE = os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json")
d = json.load(open(PIPE, encoding="utf-8"))

out = []
out.append("=== 步骤链 & 收尾 & 开始 ===")
for k in ["关卡战斗_入口", "关卡战斗_就绪", "关卡战斗_回首页", "关卡战斗_退一步",
          "日常_开始", "日常_步骤1", "日常_步骤2", "日常_步骤3", "日常_步骤4",
          "日常_步骤5", "日常_步骤6", "日常_步骤7", "日常_收尾"]:
    n = d.get(k)
    out.append(f"{k}: next={n.get('next') if n else 'MISSING'} | enabled={n.get('enabled') if n else '-'} | act={n.get('action') if n else '-'} | ca={n.get('custom_action') if n else '-'}")

out.append("")
out.append("=== 谁引用了 活动BONUS / 快捷战斗 ===")
for k, n in d.items():
    nxt = n.get("next") or []
    hit = [x for x in nxt if "活动BONUS" in x or "快捷战斗" in x or "结算" in x or "确定" in x]
    if hit:
        out.append(f"{k:34s} -> {hit}")

out.append("")
out.append("=== 活动BONUS 全部节点 ===")
for k in sorted(d):
    if "活动BONUS" in k:
        n = d[k]
        out.append(f"{k:36s} en={str(n.get('enabled')):5s} act={n.get('action','')}/{n.get('custom_action','')} next={n.get('next')}")

out.append("")
out.append("=== 快捷战斗/确定/结算 节点 ===")
for k in sorted(d):
    if "快捷战斗" in k or k.endswith("_确定1") or k.endswith("_确定2") or k.endswith("_确定3") or k.endswith("_结算1") or k.endswith("_结算2") or k.endswith("_结算3"):
        n = d[k]
        out.append(f"{k:34s} en={str(n.get('enabled')):5s} act={n.get('action','')} next={n.get('next')}")

open(os.path.join(ROOT, "_chain.txt"), "w", encoding="utf-8").write("\n".join(out))
print("ok")
