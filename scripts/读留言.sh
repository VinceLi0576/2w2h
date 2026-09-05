#!/usr/bin/env bash
# 读老徐在页面上留的言（GitHub Issues，标签「留言」，公开仓库 ⇒ 不要钥匙）
# 用法：bash scripts/读留言.sh [open|closed|all]（默认 open）
state="${1:-open}"
curl -s -m 20 "https://api.github.com/repos/VinceLi0576/2w2h/issues?labels=%E7%95%99%E8%A8%80&state=$state&per_page=50" \
| python3 -c '
import sys, json
d = json.load(sys.stdin)
if not isinstance(d, list): print(d.get("message", d)); sys.exit(1)
if not d: print("（没有留言）"); sys.exit(0)
for it in d:
    print("#%d  %s  [%s]" % (it["number"], it["title"], it["state"]))
    print("   " + it["html_url"])
    body = (it.get("body") or "").strip()
    for ln in body.split("\n"): print("   │ " + ln)
    print()
'
