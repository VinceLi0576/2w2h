#!/usr/bin/env bash
# 读老徐在页面上留的批注。🔴 存的是**私有**仓库 yunexcel2026 的议题（标签「留言」）⇒ 匿名读不到，
# 只能从他浏览器里读（站有登录门，浏览器有登录态）。走 Mac CDP，判据见 rules/cdp-用哪台浏览器.md。
# 用法：bash scripts/读留言.sh [页名] [open|closed|all]     例：bash scripts/读留言.sh 2w2h open
# 🔴 笔记本合盖／ssh 不通 ⇒ 换飞牛（ssh nas，端口 16002，不用 export CDP_PORT）
page="${1:-}"; state="${2:-open}"
ssh mac "export CDP_PORT=9333; python3 ~/.local/bin/cdp_tool.py list 2>/dev/null" | grep -q "yunexcel2026.pages.dev" || {
  echo "🔴 笔记本浏览器里没有站的标签，先开一个：ssh mac 'export CDP_PORT=9333; python3 ~/.local/bin/cdp_tool.py new https://yunexcel2026.pages.dev/'"; exit 1; }
T=$(ssh mac "export CDP_PORT=9333; python3 ~/.local/bin/cdp_tool.py list 2>/dev/null" | grep "yunexcel2026.pages.dev" | head -1 | awk '{print $3}')
ssh mac "export CDP_PORT=9333; python3 ~/.local/bin/cdp_tool.py eval $T \"(async function(){ var r=await fetch('/api/note?page=${page}&state=${state}'); return await r.text(); })()\"" 2>/dev/null \
| python3 -c '
# 🔴 cdp_tool eval 回来的是【被 JSON 字符串化过一层】的文本（\" 转义），先剥壳再解析 —— 260905 实撞
import sys, json, re
raw = sys.stdin.read()
m = re.search(r"\"\{.*\}\"|\{.*\}", raw, re.S)
if not m: print("读不到：", raw[-300:]); sys.exit(1)
t = m.group(0)
d = json.loads(json.loads(t) if t.startswith("\"") else t)
if not d.get("ok"): print("🔴", d.get("error")); sys.exit(1)
if not d["items"]: print("（没有批注）"); sys.exit(0)
for it in d["items"]:
    print("#%d  [%s]  %s" % (it["number"], it["state"], it["title"]))
    print("   " + it["url"])
    for ln in (it["body"] or "").strip().split("\n"): print("   | " + ln)
    print()
'
