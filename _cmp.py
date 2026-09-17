# -*- coding: utf-8 -*-
import subprocess, os, json, io

ROOT = r"D:\bh2-maa"
REL = "assets/resource/pipeline/30_清日常.json"

def show(rev):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, REL)], cwd=ROOT, capture_output=True)
    return json.loads(r.stdout.decode("utf-8-sig", "replace"))

base = show("cfb90bb")
cur = json.load(open(os.path.join(ROOT, REL), encoding="utf-8"))

KEYS = []
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"]:
    KEYS += sorted(k for k in set(base) | set(cur) if k.startswith(pre))

out = []
out.append("BASE(cfb90bb) %d nodes | CUR %d nodes" % (len(base), len(cur)))
out.append("")
for k in KEYS:
    b, c = base.get(k), cur.get(k)
    same = " =同" if b == c else " ≠异"
    out.append("###%s %s" % (same, k))
    if b is None:
        out.append("   BASE: (无)")
    else:
        out.append("   BASE: %s" % json.dumps(b, ensure_ascii=False))
    if c is None:
        out.append("   CUR : (无)")
    else:
        out.append("   CUR : %s" % json.dumps(c, ensure_ascii=False))
    out.append("")

io.open(os.path.join(ROOT, "CMP.txt"), "w", encoding="utf-8").write("\n".join(out))
print("keys", len(KEYS))
