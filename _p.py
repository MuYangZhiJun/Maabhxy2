# -*- coding: utf-8 -*-
import json, os
ROOT = r"D:\bh2-maa"
pipe = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

def load_jsonc(p):
    raw = open(p, encoding="utf-8").read()
    return json.loads("\n".join(l for l in raw.splitlines() if not l.strip().startswith("//")))
iface = load_jsonc(os.path.join(ROOT, "assets", "interface.json"))

print("=== TASKS ===")
for t in iface["task"]:
    print(t.get("name"), "| entry =", t.get("entry"), "| option =", t.get("option"))

print()
print("=== 步骤链 ===")
for k in ["关卡战斗_入口", "日常_开始", "日常_步骤1", "日常_步骤2", "日常_步骤3",
          "日常_步骤4", "日常_步骤5", "日常_步骤6", "日常_步骤7", "日常_收尾"]:
    n = pipe.get(k)
    print("%-16s %s" % (k, (n.get("next") if n else "【不存在】")))

print()
print("=== 谁引用三大模块 ===")
targets = ("日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS")
for k, n in pipe.items():
    nx = n.get("next") or []
    hits = [x for x in nx if x in targets]
    if hits:
        print("%-20s -> %s" % (k, hits))

print()
print("=== 三大模块当前定义 ===")
for k in ["日常_虚轴之庭", "日常_虚轴之庭_收尾", "日常_虚轴之庭_逃逸",
          "日常_使魔的爱", "日常_使魔的爱_收尾", "日常_使魔的爱_逃逸",
          "日常_活动BONUS", "日常_活动BONUS_收尾"]:
    n = pipe.get(k)
    print(k, "=", json.dumps(n, ensure_ascii=False) if n else "【不存在】")
