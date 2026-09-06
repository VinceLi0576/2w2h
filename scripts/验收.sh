#!/usr/bin/env bash
# 2w2h 出页验收 —— 用法：bash 验收.sh <html>
# 查六样：字节数没倒退 · ring 四钮齐 · 每段有 data-key · 搜索框在 · 顶部产物标记 · 没有未填占位
#        （＋ 代码块里有没有裸尖括号 —— 宪法头号大坑）
# 🔴 为什么要比字节数：出页器里变量撞名会让正文全丢而 Python 不报错
set -u
f="${1:?用法: 验收.sh <html>}"
[ -f "$f" ] || { echo "🔴 文件不存在: $f"; exit 1; }
bad=0
STD_VER="v3.0"   # 🔴 本脚本按哪版标准硬查；标准升级同一次改这里＋加检查项（见 SKILL.md「改本夹东西之前」）
ok{ echo "✅ $*"; }; ng{ echo "🔴 $*"; bad=1; }; wn{ echo "⚠️ $*"; }

# ① 字节数：跟 git HEAD 里的上一版比（有就比）
now=$(stat -c %s "$f"); dir=$(dirname "$f"); base=$(basename "$f")
if git -C "$dir" rev-parse HEAD >/dev/null 2>&1 && git -C "$dir" cat-file -e "HEAD:./$base" 2>/dev/null; then
  prev=$(git -C "$dir" cat-file -s "HEAD:./$base")
  if [ "$prev" -gt 0 ] && [ "$now" -lt "$prev" ]; then
    pct=$(( (prev-now)*100/prev ))
    if [ "$pct" -ge 15 ]; then ng "字节数倒退 $prev → $now（-$pct%）—— 先怀疑正文丢了"
    else wn "字节数比上一版少 $pct%（$prev → $now），确实删了内容就正常"; fi
  else ok "字节数 $prev → $now，没倒退"; fi
else
  wn "没有上一版可比（新页，或不在 git 里）· 本版 $now 字节"
fi

# ② ring 四钮：按档位配色 w1..w4 各至少一个
miss=""; for w in w1 w2 w3 w4; do grep -q "class=\"$w\"" "$f" || miss="$miss $w"; done
[ -z "$miss" ] && ok "ring 四钮齐" || ng "ring 缺档：$miss（w1=WHY w2=HOW w3=WHAT w4=HOW-GOOD）"

# ③ 每段有稳定锚
secs=$(grep -c '<details class="sec"' "$f"); keys=$(grep -c '<details class="sec" id="s[0-9]*" data-key=' "$f")
[ "$secs" -gt 0 ] || ng "一段 details.sec 都没有 —— 不是 build_ring 出的？"
if [ "$secs" -gt 0 ]; then
  [ "$secs" -eq "$keys" ] && ok "$secs 段全有稳定锚 data-key" || wn "$secs 段里 $((secs-keys)) 段没 key，只能靠会漂的 #sN 引用"
fi

# ④⑤⑥
grep -q 'id="q"' "$f" && ok "页内搜索框在" || ng "没有页内搜索框（折叠段里的字 Ctrl+F 搜不到）"
head -c 8000 "$f" | grep -q '<!-- 产物 · 源在' && ok "顶部有「产物 · 源在」标记" || ng "顶部没有产物标记 —— 是手写页？"
if grep -q '<!-- inject:' "$f"; then ng "有未填的注入占位：$(grep -o '<!-- inject:[^ ]* -->' "$f" | tr '\n' ' ')"; else ok "没有未填占位"; fi

# ⑥½ <pre> 开闭配对
po=$(grep -o '<pre[ >]' "$f" | wc -l); pc=$(grep -o '</pre>' "$f" | wc -l)
[ "$po" -eq "$pc" ] && ok "<pre> 开闭配对 $po/$pc" || ng "<pre> 开 $po 闭 $pc 不配对 —— 有代码块被渲染坏了"

# ⑦ 代码块里的裸尖括号（会被浏览器当标签吃掉，页面上直接少字）
if grep -q '<pre' "$f"; then
  raw=$(python3 - "$f" <<'PY'
import re, sys
s = open(sys.argv[1], encoding="utf-8").read
n = 0
for m in re.finditer(r"<pre[^>]*>(.*?)</pre>", s, re.S):
    body = re.sub(r"</?(code|span|b|i|em|strong|br|a|mark)\b[^>]*>", "", m.group(1))
    n += len(re.findall(r"<[a-zA-Z/!]", body))
print(n)
PY
)
  [ "$raw" = "0" ] && ok "代码块里没有裸尖括号" || ng "代码块里疑似 $raw 处裸尖括号（会被当标签吃掉）"
fi

# ⑧ md 表格糊掉
tbl=$(grep -c '<table' "$f" 2>/dev/null); bar=$(grep -cE '<p[^>]*>[[:space:]]*\|' "$f" 2>/dev/null)
{ [ "$tbl" -eq 0 ] && [ "$bar" -eq 0 ]; } && ok "没有表格残留" || ng "疑似 md 表格糊掉（<table>×$tbl · 裸竖线段落×$bar）—— 渲染器不支持表格，改列表或定宽代码块"

# ⑨ 段折叠
op=$(grep -oE '<details class="sec[^"]*"[^>]*open' "$f" | wc -l | tr -d ' '); s0=$(grep -oE '<details class="sec s0"[^>]*open' "$f" | wc -l | tr -d ' ')
{ [ "$op" = "1" ] && [ "$s0" = "1" ]; } && ok "段折叠对（只第 0 段展开）" || wn "段折叠异常：共 $op 个展开、第 0 段 open=$s0"

# —— 脚本查不了的语义，列出来让你自己过，🚫 不假装查过
echo ""
echo "🖐 下面这几条脚本查不了，按 $STD_VER 标准你自己过一遍："
echo "   · 每段第一段是不是「能独立成立的结论」—— 段头收起会露它，是铺垫就露出铺垫"
echo "   · 四档判没判对 —— WHY 别写成功能清单（删掉这段还知道「不做会怎样」吗）"
echo "   · 副标有没有进正文「要点」块"

ver=$(grep -oE 'v[0-9]+\.[0-9]+' "$f" | head -1)
echo ""
echo "📋 本脚本按 $STD_VER 硬查，本页 ${ver:-?}。两个号对不上 ⇒ 中间的新规矩没进这脚本，上面「你自己过」那几条就是缺口"
if [ $bad -eq 0 ]; then echo "—— 硬检查全过（🔴 但「过」≠「合格」，还有上面人工那几条）"; else echo "—— 有 🔴，别当出完了"; exit 1; fi
