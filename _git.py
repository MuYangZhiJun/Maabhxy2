# -*- coding: utf-8 -*-
import json, subprocess, os, sys

ROOT = r"D:\bh2-maa"

def git_show(rev, path):
    p = subprocess.run(["git", "show", "%s:%s" % (rev, path)], cwd=ROOT,
                       capture_output=True)
    raw = p.stdout
    for enc in ("utf-8-sig", "utf-8", "gbk"):
        try:
            return json.loads(raw.decode(enc))
        except Exception:
            continue
    raise RuntimeError("decode fail")

# 列出改过这个文件的提交
p = subprocess.run(["git", "log", "--oneline", "--", "assets/resource/pipeline/30_清日常.json"],
                   cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
print("=== 改动历史 ===")
print(p.stdout)

sys.stdout.reconfigure(encoding="utf-8")
cur = json.load(open(os.path.join(ROOT, "assets", "resource", "pipeline", "30_清日常.json"), encoding="utf-8"))
print("CUR nodes", len(cur))
