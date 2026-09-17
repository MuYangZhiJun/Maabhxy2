# -*- coding: utf-8 -*-
import subprocess, json, io
ROOT = r"D:\bh2-maa"
REL = "assets/resource/pipeline/30_清日常.json"

def show(rev):
    r = subprocess.run(["git", "show", "%s:%s" % (rev, REL)], cwd=ROOT, capture_output=True)
    return json.loads(r.stdout.decode("utf-8-sig", "replace"))

b = show("cfb90bb")
out = []
for pre in ["日常_虚轴之庭", "日常_使魔的爱", "日常_活动BONUS"]:
    out.append("#" * 20 + " " + pre)
    for k in sorted(b):
        if k.startswith(pre):
            out.append("%s = %s" % (k, json.dumps(b[k], ensure_ascii=False)))
    out.append("")
io.open(ROOT + r"\BASE_MOD.txt", "w", encoding="utf-8").write("\n".join(out))
print("ok nodes", len(b))
