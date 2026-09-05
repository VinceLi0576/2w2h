#!/usr/bin/env python3
"""自述.html 的生成器 —— 2w2h 用自己出自己的说明页（老徐 260904：「自己说明自己，其他的都参考这个模板」）。
产物两处同出：本夹 自述.html（ops 正本）＋ 站夹 html-个人ai手册/2w2h/index.html（→ https://yunexcel2026.pages.dev/2w2h/，老徐 260905 定发到站上）。
🔴 站夹那份是副本，🚫 别手改；首页 NAV 登记归 ops-claude（index.html 常有别条线压着未提交的行）。
骨架在同夹 _出页.py，🚫 别在这写第二份。
🔴 文件名刻意不叫 _出页.py（同名会 import 到自己，静默导错）；🔴 局部变量不叫 parts。
三处现算注入（🚫 别写死进 md）：usage＝使用记录快照 · downstream＝全机现状。
用法：cd ~/projects/ops/skill/2w2h && python3 _生成自述HTML.py
"""
import glob, os, pathlib, shutil, subprocess, sys, time
D = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(D))
from _出页 import build_ring  # noqa: E402

HOME = pathlib.Path.home()
NOW = time.strftime("%Y-%m-%d %H:%M")


def usage_md():
    p = HOME / ".claude/.rs-notify/skill-usage.tsv"
    if not p.exists():
        return "📌 出页时（%s）还没有任何使用记录。" % NOW
    rows = [l.split("\t") for l in p.read_text(encoding="utf-8").splitlines()[1:] if l.strip()]
    mine = [r for r in rows if len(r) > 1 and r[1] == "2w2h"]
    tail = mine[-8:]
    out = ["📌 **出页时（%s）的快照**：全机 skill 调用共 %d 条，其中 2w2h %d 条。最近 %d 条 2w2h：" % (NOW, len(rows), len(mine), len(tail)), ""]
    for r in reversed(tail):
        out.append("- `%s` · 在 `%s`%s" % (r[0], r[2] or "?", (" · 参数「%s」" % r[3]) if len(r) > 3 and r[3] else ""))
    out.append("")
    out.append("⚠️ 这是快照，会过时；活的数据用上面那条 `column -t` 现采。")
    return "\n".join(out)


def downstream_md():
    gens = subprocess.run(["bash", "-c",
        "grep -rl 'from _出页 import\\|from _md2html import' ~/projects --include=*.py 2>/dev/null | grep -v '/skill/2w2h/' | wc -l"],
        capture_output=True, text=True).stdout.strip()
    ring = subprocess.run(["bash", "-c",
        "grep -rl 'class=\"ring\"' ~/projects --include=*.html 2>/dev/null | grep -v '/收料/\\|node_modules' | wc -l"],
        capture_output=True, text=True).stdout.strip()
    allh = subprocess.run(["bash", "-c",
        "find ~/projects -name '*.html' -not -path '*/node_modules/*' -not -path '*/收料/*' 2>/dev/null | wc -l"],
        capture_output=True, text=True).stdout.strip()
    selfpages = sorted(os.path.basename(os.path.dirname(x)) for x in glob.glob(str(HOME / "projects/ops/skill/*/自述.html")))
    return ("📌 **出页时（%s）现算**：\n\n"
            "- import 本夹公共库的生成器：**%s 个**（不含本夹自己）\n"
            "- 全机 HTML **%s** 页里带黄金圈骨架的 **%s** 页 —— 存量不回填，老页迭代时才改\n"
            "- 已有自述页的 skill：%s\n\n"
            "⚠️ 快照会过时；现采命令在 `SKILL.md` 头部。" % (NOW, gens, allh, ring, "、".join("`%s`" % s for s in selfpages) or "（还没有）"))


build_ring(
    src=D / "自述.md", dst=D / "自述.html",
    eyebrow="ops · skill · 2w2h",
    lead="收到 2w2h 的推送后打开：判这次用得对不对，不对怎么改。",
    version="v2.0",
    changelog=[
        ("v2.0", "260905", "批注改成 Word 式：选中冒气泡／右键 → 黄线 ＋ 右侧对齐卡片 → 解决变灰折叠 → 手机点黄线弹卡；先存浏览器，发 GitHub 点了才出去（老徐四条全对）"),
        ("v1.9", "260905", "控件条改竖排、分四组（导航·展收·阅读·留言），为后面加按钮留位（老徐：要竖着）"),
        ("v1.8", "260905", "加 💬 留言：选中文字点它 → 变成 GitHub issue（老徐：基于位置写留言备注，保存了 AI 再读再改）"),
        ("v1.7", "260905", "右侧对称留白（≥1300 宽）；目录栏自带 « 收起（老徐：右边也要空一点、侧边可缩进去）"),
        ("v1.6", "260905", "加侧边目录（老徐：参考飞书／语雀，从侧边看全部框架）：宽屏常驻左侧可收起，窄屏抽屉，点哪跳哪、当前段高亮"),
        ("v1.5", "260905", "四钮改两行两列、跟正文同宽（老徐：一行太宽）"),
        ("v1.4", "260905", "功能栏改右上角胶囊（搜 · 缩放 · 上下段 · 全收全展 · 段号），撤吸顶大条；样式脚本改名为正本，不再重抽样板"),
        ("v1.3", "260905", "公开到 github.com/VinceLi0576/2w2h（正本仍在 ops，脚本单向推）；新生成器路径改 ~/.claude/skills/2w2h"),
        ("v1.2", "260905", "抬头改三段式：标题 ≤16 · 一句话 ≤30 · 三行各 ≤20，三行进抬头、功能栏后移；正文默认全收起（老徐一段段聊定的）"),
        ("v1.1", "260905", "上站 yunexcel2026.pages.dev/2w2h/（老徐：发到站上，一段段聊）；生成器两处同出"),
        ("v1", "260904", "开张：老徐要「推送底部指一页，页面自己说明自己，其他 skill 都参考这个模板」"),
    ],
    gen_rel="ops/skill/2w2h/_生成自述HTML.py",
    inject={"usage": usage_md(), "downstream": downstream_md()},
)

SITE = HOME / "Code/html集合/html-个人ai手册/2w2h/index.html"
if SITE.parent.parent.is_dir():   # 只在老徐这台有站夹；别人 clone 了跑不会在家目录乱建夹
    shutil.copy(D / "自述.html", SITE)
    print("✅ 同步到站夹 %s" % SITE)
