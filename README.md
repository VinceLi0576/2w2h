# 2w2h —— 黄金圈 HTML 出页 skill（Claude Code）

2W ＝ WHY · WHAT，2H ＝ HOW · HOW GOOD。把一份 md 正本出成黄金圈结构的 HTML：
**标题 → 一句话 → 三行 → 功能栏 → 四钮 → 折叠段**，带页内搜索、稳定锚、版本徽章与 changelog。

1. **它是什么**：全机唯一黄金圈出页 skill
2. **什么时候动**：谁出页谁调它，调了就记、就推
3. **不对怎么改**：按第 4 段判据说一句

## 装

```bash
git clone https://github.com/VinceLi0576/2w2h ~/.claude/skills/2w2h
```

## 用

对 Claude Code 说「出页」「给这份 md 出个 html」就会触发。生成器只要 20 行（`SKILL.md` ④），出完跑 `bash scripts/验收.sh <html>`。

## 读什么

- `SKILL.md` —— 给 AI 的六步：机读标记 · 四档怎么判 · 五个坑 · 验收
- `结构输出标准.md` —— 结构长什么样（必备五件 · 反例六条）
- `样式.css` · `脚本.js` · `控件.html` · `批注.js` —— 前端骨架
- `模板.html` —— 参考样板；出页走「md → 生成器」这条路，不手写

## 边界

正本在作者自己的项目里，本库**单向同步**、对外已清洗个人场景；直接改本库会被下一次同步覆盖，要改请开 issue。
