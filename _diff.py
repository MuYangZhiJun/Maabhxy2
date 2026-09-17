# -*- coding: utf-8 -*-
import json, subprocess, os, sys

ROOT = r"D:\bh2-maa"
sys.stdout.reconfigure(encoding="utf-8")

def git_show(rev, path):
    p = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=ROOT, capture_output=True)
    raw = p.stdout
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:
            continue
    raise RuntimeError("decode fail")

REL = "assets/resource/pipeline/30_清日常.json"
good = git_show("48c7402", REL)
cur = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))

L = []
L.append("GOOD(48c7402) nodes=%d   CUR nodes=%d" % (len(good), len(cur)))
L.append("")
L.append("=== 只在当前存在（我新增的） ===")
for k in sorted(set(cur) - set(good)):
    L.append("%-34s %s" % (k, json.dumps(cur[k], ensure_ascii=False)[:200]))
L.append("")
L.append("=== 只在 48c7402 存在（被删的） ===")
for k in sorted(set(good) - set(cur)):
    L.append("%-34s %s" % (k, json.dumps(good[k], ensure_ascii=False)[:200]))
L.append("")
L.append("=== 两边都有但内容不同 ===")
for k in sorted(set(good) & set(cur)):
    if good[k] != cur[k]:
        L.append("---- %s" % k)
        L.append("   GOOD: %s" % json.dumps(good[k], ensure_ascii=False)[:420])
        L.append("   CUR : %s" % json.dumps(cur[k], ensure_ascii=False)[:420])

open(os.path.join(ROOT, "DIFF.txt"), "w", encoding="utf-8").write("\n".join(L))
print("written", len(L))
