#!/usr/bin/env bash
# 把本夹（ops/skill/2w2h，正本）单向推到公开库 https://github.com/VinceLi0576/2w2h（老徐 260905 建）
# 用法：bash scripts/发布到github.sh "一句话说这次改了什么"
# 🔴 单向：正本永远是 ops 这个夹，公开库是发布件。别在公开库里直接改，下一次推会被覆盖
# 🚫 不推：项目说明源/ 与 _出项目说明页.py（主目录线的内部文档）· _旧设计语言-待退役.css（只本机两页在用）· __pycache__
# README.md 由本脚本拼出来（GitHub 的门面），🚫 不是第二份正本 —— 三行从 自述.md 抬头现取
set -euo pipefail
SRC="$(cd "$(dirname "$0")/.." && pwd)"
PUB="$HOME/.cache/2w2h-github"            # 公开库的本地检出，只给本脚本用
REPO="git@github.com:VinceLi0576/2w2h.git"
MSG="${1:-同步自 ops/skill/2w2h}"

if [ ! -d "$PUB/.git" ]; then
  git clone -q "$REPO" "$PUB" 2>/dev/null || { mkdir -p "$PUB"; git -C "$PUB" init -q; git -C "$PUB" remote add origin "$REPO"; }
  git -C "$PUB" checkout -q -B main
fi
rsync -a --delete --exclude '.git' --exclude '__pycache__' --exclude '项目说明源' --exclude '_出项目说明页.py' \
      --exclude '_旧设计语言-待退役.css' --exclude 'README.md' --exclude '.gitignore' "$SRC/" "$PUB/"
printf '__pycache__/\n' > "$PUB/.gitignore"

python3 - "$SRC/自述.md" "$PUB/README.md" <<'PY'
import re, sys
md = open(sys.argv[1], encoding="utf-8").read()
three = "\n".join(re.findall(r"^\d+\. .*$", md.split("\n## ", 2)[1], re.M)[:3])
open(sys.argv[2], "w", encoding="utf-8").write(f"""# 2w2h —— 黄金圈 HTML 出页 skill（Claude Code）

2W ＝ WHY · WHAT，2H ＝ HOW · HOW GOOD。把一份 md 正本出成黄金圈结构的 HTML：
**标题 → 一句话 → 三行 → 功能栏 → 四钮 → 折叠段**，带页内搜索、稳定锚、版本徽章与 changelog。

{three}

## 装

```bash
git clone https://github.com/VinceLi0576/2w2h ~/.claude/skills/2w2h
```

## 用

对 Claude Code 说「出页」「给这份 md 出个 html」就会触发。生成器只要 20 行（`SKILL.md` ④），出完跑 `bash scripts/验收.sh <html>`。

## 读什么

- `SKILL.md` —— 给 AI 的六步：机读标记 · 四档怎么判 · 五个坑 · 验收
- `结构输出标准.md` —— 结构长什么样（必备五件 · 反例六条）
- `自述.md` —— 给人看的：它是什么、什么时候动、不对怎么改
- `说明-三层管线与归属.md` —— 它怎么长成这样的
- `模板.html` ＋ `_抽出的*` —— 样式与脚本的来源

## 边界

正本在作者的 ops 项目里，本库由 `scripts/发布到github.sh` **单向同步**；直接改本库会被下一次同步覆盖，要改请开 issue。
""")
PY

git -C "$PUB" add -A
git -C "$PUB" commit -q -m "$MSG" || { echo "没有变化，不用推"; exit 0; }
git -C "$PUB" push -q -u origin main
echo "✅ 已推 $(git -C "$PUB" rev-parse --short HEAD) → https://github.com/VinceLi0576/2w2h"
