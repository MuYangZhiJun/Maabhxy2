# -*- coding: utf-8 -*-
import subprocess, os, sys, json

ROOT = r"D:\bh2-maa"
sys.stdout.reconfigure(encoding="utf-8")

def show(rev, rel):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, rel)], cwd=ROOT, capture_output=True)
    return json.loads(r.stdout.decode("utf-8-sig", "replace"))

REL = "assets/resource/pipeline/30_清日常.json"
base = show("cfb90bb", REL)          # 会话开始
cur = json.load(open(os.path.join(ROOT, REL), encoding="utf-8"))

L = []
L.append("base(cfb90bb) nodes=%d  cur nodes=%d" % (len(base), len(cur)))
L.append("")
L.append("======== 内容不同的节点 ========")
for k in sorted(set(base) | set(cur)):
    b, c = base.get(k), cur.get(k)
    if b == c:
        continue
    L.append("---- %s" % k)
    L.append("  base: %s" % json.dumps(b, ensure_ascii=False)[:500])
    L.append("  cur : %s" % json.dumps(c, ensure_ascii=False)[:500])
open(os.path.join(ROOT, "D2.txt"), "w", encoding="utf-8").write("\n".join(L))
print("diff nodes:", sum(1 for k in set(base) | set(cur) if base.get(k) != cur.get(k)))
