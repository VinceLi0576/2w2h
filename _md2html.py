#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ops 通用 md → HTML 引擎（260823 立）。

**为什么是共享的**：`多AI调用/` 与 `lwr/` 各有一页要出，两份 216 行的生成器
各自改 CSS 必然漂移 ⇒ 引擎一份、各夹只留三行调用文件。
🔴 一页可以由**多份 md** 拼出来（各 md 仍是自己那段的唯一正本，🚫 不复制内容）。

用法（各夹的 _生成HTML.py 里）：
    import sys; sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from _md2html import build
    build(dst="x.html", title="标题", srcs=["a.md","b.md"], version="v3",
          changelog=[("v3","260823","干了啥")])
"""
import io, re, html, datetime, subprocess, os
from pathlib import Path

def esc(t):
    return html.escape(t, quote=False)

def inline(t):
    """行内：先转义，再还原 md 的行内标记。🔴 顺序不能反，否则代码里的尖括号会被吃掉。

    🔴 `260824` 修一个真 bug：原来 `code` 段直接就地替换成 <code>…</code>，
       于是**代码里的 `*` 还留在文本里，会跟别处的 `*` 配成一对斜体**。
       ⭐ 实撞：一行里写 `Browser.*`（窗口）· `Extensions.*`（装扩展），
       渲染成 `Browser.<i></code>（窗口）· <code>Extensions.</i>` —— 中间内容被吞进 <i>。
       ⇒ 改成**先把 code 段抽走换占位符**，斜体/加粗处理完再放回。
       ⚠️ 这个 bug 影响所有用本渲染器的页，只要一行里出现两个 `xxx.*`。
    """
    t = esc(t)
    stash = []

    def _keep(m):
        stash.append(m.group(1))
        return "\x00%d\x00" % (len(stash) - 1)

    t = re.sub(r'`([^`]+)`', _keep, t)          # 🔑 先抽走，别让 code 里的 * 参与配对
    t = re.sub(r'\*\*([^*]+)\*\*', r'<b>\1</b>', t)
    t = re.sub(r'(?<!\w)\*([^*\n]+)\*(?!\w)', r'<i>\1</i>', t)
    t = re.sub(r'&lt;(https?://[^\s&]+)&gt;', r'<a href="\1">\1</a>', t)
    t = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)', r'<a href="\2">\1</a>', t)
    t = re.sub(r'\x00(\d+)\x00', lambda m: '<code>%s</code>' % stash[int(m.group(1))], t)
    return t

TONE = [('🔴','crit'),('⭐','star'),('⚠️','warn'),('🚫','no'),('✅','ok'),('🔑','key'),
        ('📌','note'),('🔄','upd'),('⬜','todo'),('🥇','star'),('⏱','key'),('🎯','key')]
def tone_of(t):
    for e, c in TONE:
        if t.lstrip().startswith(e): return c
    return ''

def render(md):
    out, i, lines = [], 0, md.split('\n')
    while i < len(lines):
        L = lines[i]
        if L.startswith('```'):
            lang = L[3:].strip(); i += 1; buf = []
            while i < len(lines) and not lines[i].startswith('```'):
                buf.append(lines[i]); i += 1
            i += 1
            out.append('<pre data-lang="%s"><code>%s</code></pre>' % (esc(lang), esc('\n'.join(buf))))
            continue
        if L.startswith('#### '):
            out.append('§§H3§§' + inline(L[5:])); i += 1; continue
        if L.startswith('### '):
            out.append('§§H3§§' + inline(L[4:])); i += 1; continue
        if L.startswith('## '):
            out.append('§§H2§§' + inline(L[3:])); i += 1; continue
        if L.startswith('# '):
            i += 1; continue                          # 一级标题走页头/分册头
        if L.startswith('> '):
            buf = []
            while i < len(lines) and lines[i].startswith('> '):
                buf.append(lines[i][2:]); i += 1
            out.append('<blockquote>%s</blockquote>' % inline(' '.join(buf))); continue
        if re.match(r'^\s*[-*] ', L):
            items = []
            while i < len(lines) and (re.match(r'^\s*[-*] ', lines[i]) or (lines[i].startswith('  ') and lines[i].strip() and items)):
                if re.match(r'^\s*[-*] ', lines[i]):
                    items.append(re.sub(r'^\s*[-*] ', '', lines[i]))
                else:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            out.append('<ul>%s</ul>' % ''.join(
                '<li class="%s">%s</li>' % (tone_of(x), inline(x)) for x in items))
            continue
        if re.match(r'^\d+\. ', L):
            items = []
            while i < len(lines) and (re.match(r'^\d+\. ', lines[i]) or (lines[i].startswith('   ') and lines[i].strip() and items)):
                if re.match(r'^\d+\. ', lines[i]):
                    items.append(re.sub(r'^\d+\. ', '', lines[i]))
                else:
                    items[-1] += ' ' + lines[i].strip()
                i += 1
            out.append('<ol>%s</ol>' % ''.join(
                '<li class="%s">%s</li>' % (tone_of(x), inline(x)) for x in items))
            continue
        if L.strip() in ('---', ''):
            i += 1; continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r'^(#{1,4} |```|> |\s*[-*] |\d+\. |---)', lines[i]):
            buf.append(lines[i]); i += 1
        if buf:
            t = ' '.join(buf)
            out.append('<p class="%s">%s</p>' % (tone_of(t), inline(t)))
    return out

def sha(paths):
    try:
        paths = [p for p in paths if not isinstance(p, (tuple, list))]
        r = subprocess.run(['git', 'log', '-1', '--format=%h', '--'] + list(paths),
                           capture_output=True, text=True)
        return r.stdout.strip() or 'n/a'
    except Exception:
        return 'n/a'

CSS = """
:root{--paper:#F5F7F6;--surface:#fff;--surface2:#ECF1EF;--ink:#101A1C;--ink2:#4A5A5C;
--line:#D6E0DD;--crit:#B3261E;--star:#0B6E4F;--warn:#8A5A00;--no:#7A2E2E;--ok:#0B6E4F;
--key:#0B4F6C;--note:#4A5A5C;--upd:#5B3E8A;--todo:#6B6B6B;--codebg:#0E1B1D;--codefg:#E6EFEC}
@media(prefers-color-scheme:dark){:root:not([data-theme=light]){--paper:#0D1416;--surface:#131E21;
--surface2:#182529;--ink:#E8F0EE;--ink2:#9FB2B4;--line:#26383C;--codebg:#0A1113;--crit:#FF8A80;
--star:#6EE7B7;--warn:#F7C86B;--no:#FF9E9E;--ok:#6EE7B7;--key:#7FD4F5;--note:#9FB2B4;--upd:#C4B5FD;--todo:#9A9A9A}}
:root[data-theme=dark]{--paper:#0D1416;--surface:#131E21;--surface2:#182529;--ink:#E8F0EE;
--ink2:#9FB2B4;--line:#26383C;--codebg:#0A1113;--crit:#FF8A80;--star:#6EE7B7;--warn:#F7C86B;
--no:#FF9E9E;--ok:#6EE7B7;--key:#7FD4F5;--note:#9FB2B4;--upd:#C4B5FD;--todo:#9A9A9A}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font:16px/1.75 "Source Sans 3",-apple-system,"PingFang SC","Microsoft YaHei",sans-serif}
.wrap{max-width:920px;margin:0 auto;padding:28px 18px 96px}
header{border-bottom:2px solid var(--ink);padding-bottom:14px;margin-bottom:8px}
h1{font:700 clamp(22px,3.4vw,32px)/1.25 Archivo,sans-serif;margin:0 0 8px}
.meta{color:var(--ink2);font-size:13px;display:flex;gap:14px;flex-wrap:wrap;align-items:center}
.badge{background:var(--ink);color:var(--paper);padding:2px 9px;font-weight:700;font-size:12px;letter-spacing:.04em}
nav{position:sticky;top:0;background:var(--paper);border-bottom:1px solid var(--line);
padding:9px 0;margin:14px 0 22px;display:flex;gap:6px;overflow-x:auto;z-index:9}
nav a{color:var(--ink2);text-decoration:none;font-size:12.5px;white-space:nowrap;
padding:3px 9px;border:1px solid var(--line)}
nav a:hover{color:var(--ink);border-color:var(--ink)}
section{margin:0 0 34px}
h2{font:600 clamp(17px,2.2vw,21px)/1.35 Archivo,sans-serif;margin:26px 0 12px;
padding-left:11px;border-left:4px solid var(--ink)}
.part{margin:34px 0 6px;padding:7px 12px;background:var(--ink);color:var(--paper);
font:700 13px/1.4 Archivo,sans-serif;letter-spacing:.06em}
details{background:var(--surface);border:1px solid var(--line);margin:9px 0}
summary{cursor:pointer;padding:11px 14px;font-weight:600;font-size:15px;list-style:none}
summary::-webkit-details-marker{display:none}
summary::before{content:"▸ ";color:var(--ink2)}
details[open] summary::before{content:"▾ "}
details[open] summary{border-bottom:1px solid var(--line)}
.d{padding:4px 14px 14px}
p,li{margin:.5em 0}
ul,ol{padding-left:1.35em;margin:.5em 0}
li.crit,p.crit{color:var(--crit);font-weight:600}
li.star,p.star{color:var(--star)}
li.warn,p.warn{color:var(--warn)}
li.no,p.no{color:var(--no)}
li.ok,p.ok{color:var(--ok)}
li.key,p.key{color:var(--key);font-weight:600}
li.upd,p.upd{color:var(--upd)}
li.todo,p.todo{color:var(--todo)}
code{background:var(--surface2);padding:1px 5px;font:13.5px/1.5 "JetBrains Mono",ui-monospace,monospace;
border-radius:2px;word-break:break-word}
pre{background:var(--codebg);color:var(--codefg);padding:13px 15px;overflow-x:auto;
margin:11px 0;border-left:3px solid var(--star);position:relative}
pre code{background:none;color:inherit;padding:0;font-size:13px;line-height:1.6}
pre[data-lang]:not([data-lang=""])::after{content:attr(data-lang);position:absolute;top:0;right:0;
background:var(--star);color:var(--codebg);font:600 10.5px/1 "JetBrains Mono",monospace;padding:4px 7px}
blockquote{border-left:3px solid var(--line);margin:11px 0;padding:2px 0 2px 14px;color:var(--ink2)}
a{color:var(--key)}
footer{margin-top:44px;padding-top:16px;border-top:1px solid var(--line);color:var(--ink2);font-size:13px}
#zoom{position:fixed;right:14px;bottom:14px;display:flex;gap:6px;z-index:20}
#zoom button{background:var(--surface);color:var(--ink);border:1px solid var(--line);
width:34px;height:34px;font:600 14px/1 sans-serif;cursor:pointer}
@media print{nav,#zoom{display:none}details{break-inside:avoid}details>div{display:block!important}}
"""

JS = """
(function(){
 var z=1, r=document.documentElement;
 function ap(){r.style.fontSize=(16*z)+'px'}
 document.getElementById('zin').onclick=function(){z=Math.min(1.5,z+0.1);ap()};
 document.getElementById('zout').onclick=function(){z=Math.max(0.8,z-0.1);ap()};
 document.getElementById('zall').onclick=function(){
   var d=document.querySelectorAll('details'), open=[].every.call(d,function(x){return x.open});
   [].forEach.call(d,function(x){x.open=!open});
 };
})();
"""

def build(dst, title, srcs, version, changelog, gen_rel, subtitle=None):
    """srcs: [md 路径, ...]（相对调用者的 cwd）。多份时每份的 H1 会变成一个分册条。"""
    secs, parts = [], []
    for path in srcs:
        # 🔑 srcs 里可以放 (标签, md文本) 元组 —— 给「现算出来的段落」用（名单/数字别写死）
        if isinstance(path, (tuple, list)):
            label, md = path
            path = label
        else:
            md = io.open(path, encoding='utf-8').read()
        h1 = md.split('\n')[0].lstrip('# ').strip()
        parts.append((h1, os.path.basename(path)))
        cur = None
        first_of_file = True
        for b in render(md):
            if b.startswith('§§H2§§'):
                cur = {'h': b[6:], 'lead': [], 'subs': [],
                       'part': (h1 if first_of_file else None), 'src': os.path.basename(path)}
                secs.append(cur); first_of_file = False
            elif b.startswith('§§H3§§'):
                if cur is None:
                    cur = {'h': h1, 'lead': [], 'subs': [], 'part': h1, 'src': os.path.basename(path)}
                    secs.append(cur); first_of_file = False
                cur['subs'].append({'h': b[6:], 'body': []})
            else:
                if cur is None:
                    cur = {'h': h1, 'lead': [], 'subs': [], 'part': h1, 'src': os.path.basename(path)}
                    secs.append(cur); first_of_file = False
                (cur['subs'][-1]['body'] if cur['subs'] else cur['lead']).append(b)

    body = []
    for n, s in enumerate(secs):
        if s['part']:
            body.append('<div class="part">%s ｜ 源 %s</div>' % (esc(s['part']), esc(s['src'])))
        body.append('<section id="s%d"><h2>%s</h2>%s' % (n, s['h'], ''.join(s['lead'])))
        for sub in s['subs']:
            body.append('<details><summary>%s</summary><div class="d">%s</div></details>'
                        % (sub['h'], ''.join(sub['body'])))
        body.append('</section>')

    nav = ''.join('<a href="#s%d">%s</a>' % (n, re.sub(r'<[^>]+>', '', s['h'])[:22])
                  for n, s in enumerate(secs))
    nfold = sum(len(s['subs']) for s in secs)
    srclist = ' ＋ '.join('<code>%s</code>' % os.path.basename(p[0] if isinstance(p,(tuple,list)) else p) for p in srcs)
    cl = '<br>'.join('<code>%s</code> %s：%s' % (v, d, t) for v, d, t in changelog)
    today = datetime.date.today().isoformat()

    out = """<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>%s</title>
<!-- 产物 · 源在 %s · 生成器 %s · 🚫 别手改本文件 -->
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@600;700&family=Source+Sans+3:wght@400;600;700&family=JetBrains+Mono:wght@400;600&display=swap">
<style>%s</style></head><body><div class="wrap">
<header><h1>%s</h1>
<div class="meta"><span class="badge">%s</span><span>源 %s · 提交 <code>%s</code></span><span>生成 %s</span><span>%d 节 · %d 个折叠块</span></div>
%s</header>
<nav>%s</nav>
%s
<footer><b>这页是产物，不是正本。</b> 内容改动改那几份 md，然后 <code>python3 %s</code> 重出。🚫 别手改本文件。<br>
<b>changelog</b> —— %s</footer>
</div>
<div id="zoom"><button id="zout" title="缩小">A-</button><button id="zin" title="放大">A+</button><button id="zall" title="全部展开/收起">⇕</button></div>
<script>%s</script></body></html>""" % (
        esc(title), ' ＋ '.join(p[0] if isinstance(p,(tuple,list)) else p for p in srcs), gen_rel, CSS, inline(title), version, srclist,
        sha(srcs), today, len(secs), nfold,
        ('<p class="note">%s</p>' % inline(subtitle)) if subtitle else '',
        nav, ''.join(body), gen_rel, cl, JS)

    io.open(dst, 'w', encoding='utf-8').write(out)
    print("✅ %s  %.1f KB · %d 节 · %d 折叠块 · 源 %d 份" % (dst, len(out)/1024, len(secs), nfold, len(srcs)))
    return out
