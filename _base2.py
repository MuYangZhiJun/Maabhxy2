# -*- coding: utf-8 -*-
import subprocess, json, io, os, sys

ROOT = r"D:\bh2-maa"
L = []

def show(rev, rel):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, rel)], cwd=ROOT, capture_output=True)
    return json.loads(r.stdout.decode("utf-8-sig", "replace"))

for rel in ["assets/resource/pipeline/10_启动.json"]:
    b = show("cfb90bb", rel)
    c = json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))
    L.append("############ %s ############" % rel)
    L.append("--- BASELINE cfb90bb 节点: %s" % list(b))
    L.append(json.dumps(b, ensure_ascii=False, indent=1))
    L.append("--- CURRENT 节点: %s" % list(c))
    L.append("")

# 回归赠礼相关
b = show("cfb90bb", "assets/resource/pipeline/30_清日常.json")
L.append("############ 基线里 回归赠礼/关弹窗/签到 节点 ############")
for k in sorted(b):
    if any(x in k for x in ["回归赠礼", "关弹窗", "签到"]):
        L.append("%s = %s" % (k, json.dumps(b[k], ensure_ascii=False)))

# 每日奖励
L.append("")
L.append("############ 基线里 存在感/每周/奖励 领取节点 ############")
for k in sorted(b):
    if any(x in k for x in ["存在感", "每周", "一键领取", "领取"]):
        n = b[k]
        L.append("%s = thr=%s tmpl=%s next=%s" % (k, n.get("threshold"), n.get("template"), n.get("next")))

# 步骤链
L.append("")
L.append("############ 基线 步骤链 ############")
for k in sorted(b):
    if k.startswith(("日常_步骤", "日常_开始", "日常_收尾", "关卡战斗")):
        L.append("%s = %s" % (k, json.dumps(b[k], ensure_ascii=False)))

# 使魔探险
L.append("")
L.append("############ 基线 使魔探险 节点 ############")
for k in sorted(b):
    if "使魔探险" in k or "派遣" in k:
        L.append("%s = %s" % (k, json.dumps(b[k], ensure_ascii=False)))

io.open(os.path.join(ROOT, "BASE2.txt"), "w", encoding="utf-8").write("\n".join(L))
print("ok", len(L))
