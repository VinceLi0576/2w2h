#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""结构输出标准的**共用出页器** —— 🔑 `260824` 从 ops/飞牛/_生成路径清单HTML.py 抽出来的。
🔴 别在各项目的生成器里再写一份骨架代码，import 这个。
📍 `260904` 真身搬到 ~/projects/ops/skill/2w2h/；下面用法里的 OPC/格式标准 路径是软链接，跑顺前别改各生成器。

用法（各项目的生成器只剩几行）：
    import sys, pathlib
    sys.path.insert(0, os.path.expanduser("~/.claude/skills/2w2h"))   # 260905 起新生成器走这条；老的写 OPC/格式标准 的靠软链接照旧
    from _出页 import build_ring
    build_ring(src="xxx.md", dst="xxx.html", eyebrow="ops · 飞牛",
               lead="一句话说这页解决什么", version="v1",
               changelog=[("v1","260824","开张")], gen_rel="ops/飞牛/_生成xxx.py")

md 里的机读标记（放在 `## 标题` 的下一行）——细则见同夹 结构输出标准.md：
    <!-- sec tldr sub=副标 -->
    <!-- sec tag=WHY sub=副标 ring=按钮标题|一句钩子 -->
    <!-- sec sub=副标 -->
🔴 四档（WHY/HOW/WHAT/HOW-GOOD）缺哪档就往 stderr 报警 —— 缺档说明那部分没想清楚。
⭐ 样式与脚本从同夹 `样式.css` `脚本.js` `控件.html` 读 —— `260905` 起**本夹就是正本**（老徐「最后你改的才是标准」），不再从 Feynman 样板重抽。
"""
import io, os, pathlib, re, subprocess, sys

STD = pathlib.Path(__file__).resolve().parent


def _load_md2html():
    """复用 ops 项目里的共用 md 渲染器 —— 🚫 别写第二份 md 解析。"""
    sys.path.insert(0, str(STD))          # 🔴 260824 起 _md2html.py 就在同夹（原来在 ops 根目录，靠跨项目硬编码路径抓）
    from _md2html import render, inline, esc
    return render, inline, esc


render, inline, esc = _load_md2html()

TAGCLS = {"WHY": "why", "HOW": "how", "WHAT": "what", "HOW-GOOD": "good"}
TAGTXT = {"WHY": "WHY", "HOW": "HOW", "WHAT": "WHAT", "HOW-GOOD": "HOW GOOD"}


def parse(md):
    """切成段：每段 = {标题, 标记, 正文块列表}。标记来自 H2 下一行的 <!-- sec ... -->。"""
    lines, secs, i = md.split("\n"), [], 0
    while i < len(lines):
        if lines[i].startswith("## "):
            title = lines[i][3:].strip()
            meta, body = {}, []
            i += 1
            m = re.match(r"\s*<!--\s*sec\s+(.*?)\s*-->\s*$", lines[i]) if i < len(lines) else None
            if m:
                raw = m.group(1)
                if re.search(r"(^|\s)tldr(\s|$)", raw):
                    meta["tldr"] = True
                for k in ("tag", "sub", "ring", "key"):
                    mm = re.search(r"\b%s=([^=]*?)(?=\s+\w+=|$)" % k, raw)
                    if mm:
                        meta[k] = mm.group(1).strip()
                i += 1
            while i < len(lines) and not lines[i].startswith("## "):
                body.append(lines[i]); i += 1
            secs.append({"title": title, "meta": meta, "md": "\n".join(body)})
        else:
            i += 1
    return secs


def three(md_body):
    """TL;DR 的有序列表 → ol.three（‖ 左边是主句，右边进 <em>）。"""
    items = []
    for ln in md_body.split("\n"):
        m = re.match(r"^\d+\.\s+(.*)$", ln.strip())
        if m:
            head, _, tail = m.group(1).partition("‖")
            items.append("<li>%s%s</li>" % (
                inline(head.strip()),
                "<em>%s</em>" % inline(tail.strip()) if tail.strip() else ""))
    return '<ol class="three">%s</ol>' % "".join(items) if items else ""


def body_html(md_body, first_is_lead=True, warn=True):
    """普通段正文：复用 render()，把 H3 变成 details.sub，首个 <p> 提成 p.lead2。"""
    out, sub, done_lead = [], None, not first_is_lead
    for b in render("\n" + md_body):
        if b.startswith("§§H2§§"):
            continue
        if b.startswith("§§H3§§"):
            if sub:
                out.append(sub + "</div></details>")
            sub = ('<details class="sub" open><summary><span class="nm">%s</span></summary>'
                   '<div class="body">' % b[6:])
            continue
        if not done_lead:
            done_lead = True
            # 🔴 `260904` ops-cdp 实撞：原正则 `^<p[^>]*>` 连 `<pre data-lang>` 也吃 ⇒ 开 <p> 闭 </pre>，
            #    浏览器容错成普通段落，代码块等宽与换行全丢；源码里 grep 不出来，只有渲染了才露馅。
            #    ⇒ `<p` 后必须紧跟空白或 `>`。首块不是段落（pre/ul/ol）就不包 lead2，并往 stderr 报 ——
            #    标准要求 `.body` 第一句是结论（p.lead2），段首放代码块本身就违反它。
            if re.match(r'<p(?=[\s>])', b):
                out.append(re.sub(r'^<p(?=[\s>])[^>]*>', '<p class="lead2">', b, count=1))
                continue
            if warn:   # 只对挂了档的段报；📎 对照读物那种不挂档的段首是列表很正常
                _tag = re.match(r'<(\w+)', b)
                print("⚠️ 段首不是段落而是 <%s>，标准要求展开第一句就是结论（p.lead2）" % (_tag.group(1) if _tag else "?"),
                      file=sys.stderr)
        if sub is None:
            out.append(b)
        else:
            sub += b
    if sub:
        out.append(sub + "</div></details>")
    return "".join(out)




# ── 页内搜索（`260824` 老徐要：输入一个词就高亮，多个就逐个跳）
# `260905` 起样式与脚本以本夹 样式.css／脚本.js／控件.html 为正本；搜索的高亮样式与核心 JS 仍留在下面两个常量里。
# 🔑 为什么不靠浏览器的 Ctrl+F：本页大部分内容在折叠的 <details> 里，
#    **原生查找搜不到没展开的内容** ⇒ 自建搜索的核心价值就是**跳过去时自动把祖先 details 展开**。
SEARCH_CSS = """
mark.hit{ background:#fde68a; color:inherit; padding:0 1px; border-radius:2px; }
mark.hit.cur{ background:var(--warn); color:#fff; box-shadow:0 0 0 2px var(--warn); }

/* 🥇 稳定锚：不占位、不可见 */
a.kanchor{ display:block; height:0; overflow:hidden; scroll-margin-top:calc(var(--bar) + 14px); }

/* 🏷 顶部三维度标签 */
.dims{ display:flex; justify-content:center; flex-wrap:wrap; gap:8px; margin:14px auto 0; }
.dims .dim{ display:inline-flex; align-items:baseline; gap:6px; background:var(--card);
  border:1px solid var(--line); border-radius:20px; padding:5px 13px; font-size:12px; }
.dims .dim b{ color:var(--muted); font-weight:700; letter-spacing:.04em; }
.dims .dim .v{ font-weight:800; color:var(--ink); letter-spacing:1px; }
.dims .dim .lab{ color:var(--acc-d); font-weight:700; }
.dims .dim.mt .v{ color:var(--what); } .dims .dim.im .v{ color:var(--good); }

/* 📚 底部版本迭代折叠 */
.foot details.cl{ margin-top:8px; }
.foot details.cl > summary{ cursor:pointer; list-style:none; font-weight:700; color:var(--acc-d);
  padding:6px 0; min-height:36px; display:flex; align-items:center; gap:6px; }
.foot details.cl > summary::-webkit-details-marker{ display:none; }
.foot details.cl > summary::after{ content:"＋"; color:var(--muted); font-weight:700; }
.foot details.cl[open] > summary::after{ content:"－"; }
.foot details.cl .body{ padding-top:4px; }
"""

# ── 抬头三行（`260905` 老徐定：标题 → 一句话 → 三行 → 才到功能栏；三行就是 TL;DR，🚫 不再另开折叠段，否则重复）
#    字数是作者规矩，超了往 stderr 报，🚫 不截断（截断＝静默改内容）
HEAD_MAX = {"标题": 16, "一句话": 30, "三行每行": 20}
HERO_CSS = """
.hero .three{ text-align:left; max-width:40em; margin:18px auto 0; }
.hero .three li{ font-size:15px; padding-bottom:10px; }
"""

# 搜索框已在 控件.html 的 .q 里（`260905` 胶囊化），不再往工具条里插

SEARCH_JS = """
(function(){
  var q=document.getElementById('q'), qn=document.getElementById('qn');
  var hits=[], cur=-1, timer=null;

  function clearHits(){
    document.querySelectorAll('mark.hit').forEach(function(m){
      m.parentNode.replaceChild(document.createTextNode(m.textContent), m);
    });
    // 🔑 normalize 把被切碎的相邻文本节点合回去，否则搜第二次会漏跨节点的词
    document.querySelectorAll('main, .hero').forEach(function(n){ n.normalize(); });
    hits=[]; cur=-1;
  }

  function markAll(s){
    clearHits();
    if(!s) { qn.textContent='–'; qn.classList.remove('none'); return; }
    var root=document.querySelector('main');
    var w=document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
      acceptNode:function(n){
        if(!n.nodeValue || !n.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
        var p=n.parentNode && n.parentNode.nodeName;
        if(p==='SCRIPT'||p==='STYLE') return NodeFilter.FILTER_REJECT;
        return NodeFilter.FILTER_ACCEPT;
      }
    });
    // 🔴 先收集再改 —— 边走边替换会让 TreeWalker 走乱
    var nodes=[], n;
    while((n=w.nextNode())) nodes.push(n);
    var low=s.toLowerCase();
    nodes.forEach(function(node){
      var txt=node.nodeValue, t=txt.toLowerCase(), i=t.indexOf(low);
      if(i<0) return;
      var frag=document.createDocumentFragment(), last=0;
      while(i>=0){
        if(i>last) frag.appendChild(document.createTextNode(txt.slice(last,i)));
        var m=document.createElement('mark'); m.className='hit';
        m.textContent=txt.slice(i, i+s.length);
        frag.appendChild(m); hits.push(m);
        last=i+s.length; i=t.indexOf(low, last);
      }
      if(last<txt.length) frag.appendChild(document.createTextNode(txt.slice(last)));
      node.parentNode.replaceChild(frag, node);
    });
    qn.textContent = hits.length ? ('0/'+hits.length) : '无';
    qn.classList.toggle('none', hits.length===0);
    if(hits.length) jump(0);
  }

  function jump(i){
    if(!hits.length) return;
    cur=(i+hits.length)%hits.length;
    hits.forEach(function(h){ h.classList.remove('cur'); });
    var h=hits[cur]; h.classList.add('cur');
    // 🥇 这条是自建搜索存在的理由：把祖先 details 全打开，否则跳过去也看不见
    var p=h.parentElement;
    while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
    h.scrollIntoView({behavior:'smooth', block:'center'});
    qn.textContent=(cur+1)+'/'+hits.length;
  }

  q.addEventListener('input', function(){
    clearTimeout(timer);
    timer=setTimeout(function(){ markAll(q.value.trim()); }, 180);
  });
  q.addEventListener('keydown', function(e){
    if(e.key==='Enter'){ e.preventDefault(); e.shiftKey?jump(cur-1):jump(cur+1); }
    if(e.key==='Escape'){ q.value=''; clearHits(); qn.textContent='–'; qn.classList.remove('none'); q.blur(); hideQ(); }
  });
  // 🔍 `260905` 胶囊化：搜索框点开才出来
  var qbox=document.getElementById('qbox'), qt=document.getElementById('qtoggle');
  function showQ(){ qbox.hidden=false; q.focus(); q.select(); }
  function hideQ(){ qbox.hidden=true; }
  qt.addEventListener('click', function(){ qbox.hidden ? showQ() : hideQ(); });
  document.getElementById('qnext').addEventListener('click', function(){ jump(cur+1); });
  document.getElementById('qprev').addEventListener('click', function(){ jump(cur-1); });
  document.addEventListener('keydown', function(e){
    if(/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
    if(e.key==='/'){ e.preventDefault(); showQ(); }
  });
  // （`260905` 撤了吸顶大条，原来实测 --bar 高度那段随之去掉；--bar 现在是 6px 常量）

  // 🔴 `260824`：原脚本只认 `#sN`（getElementById 后 steps.indexOf）——
  //    语义锚会让它 `hi=-1` 然后**静默跳到第一段**。⇒ 必须一起加这段，否则锚是个会骗人的东西。
  function gotoKey(k){
    if(!k) return false;
    var d=document.querySelector('details.sec[data-key="'+CSS.escape(k)+'"]');
    if(!d) return false;
    return openAndScroll(d, document.getElementById(k));
  }
  // 🔴 `260824` 实测抓到的行为不一致：原脚本的 hash 处理**只在加载时跑一次、没监听 hashchange**
  //    ⇒ 页面打开后再点站内 `#sN` 链接**没反应**，而语义锚（我这套监听了）有反应。
  //    ⇒ 两种锚行为不一致，而"有的锚能用有的不能"比"都不能用"更坑。
  //    ⇒ 这里对 sN 也走同一套（展开祖先 ＋ 滚过去），🚫 不动原脚本。
  function openAndScroll(el, target){
    if(!el) return false;
    el.open = true;
    var p = el.parentElement;
    while(p){ if(p.tagName==='DETAILS') p.open=true; p=p.parentElement; }
    (target || el).scrollIntoView({behavior:'smooth', block:'start'});
    return true;
  }
  function handleHash(){
    var h=decodeURIComponent(location.hash.replace('#',''));
    if(!h) return;
    if(/^s[0-9]+$/.test(h)){ return openAndScroll(document.getElementById(h)); }
    return gotoKey(h);
  }
  handleHash();
  window.addEventListener('hashchange', handleHash);
  window.__gotoKey=gotoKey;
  window.__keys=function(){ return Array.prototype.map.call(
    document.querySelectorAll('details.sec[data-key]'), function(d){ return d.dataset.key; }); };

  // 供自动化验证用（🔑 出页后能在真浏览器里跑 __pageSearch('词') 自证）
  window.__pageSearch=function(s){ markAll(s); return {q:s, hits:hits.length, cur:cur}; };
  window.__pageSearchJump=function(i){ jump(i); return {cur:cur, total:hits.length,
    text:(hits[cur]?hits[cur].textContent:null),
    visible:(hits[cur]? !!hits[cur].getClientRects().length : false)}; };
})();
"""



def _src_commit(src_p):
    """徽章里的「提交」＝ **这份 md 自己**最后一次提交，🚫 不是仓库 HEAD。
    🔴 `260904` ops-tailscale 实撞：md 从没提交过（untracked），徽章却印了仓库 HEAD `c271adc` ——
       那是别条线一笔毫不相关的提交。原实现只在 git 命令报错时才回落「未提交」，文件 untracked 照样拿到 HEAD
       ⇒ 一个看着很准、实际无关的数字，正是「会变的数字骗人不报错」那一型。
    三种结果：`未提交`（untracked）· `abc1234`（tracked 且工作区干净）· `abc1234+未提交改动`（tracked 但改了没提交）。"""
    d, name = str(src_p.resolve().parent), src_p.name
    def git(*args):
        return subprocess.run(["git", "-C", d, *args], capture_output=True, text=True, timeout=15)
    try:
        if git("ls-files", "--error-unmatch", "--", name).returncode != 0:
            return "未提交"
        h = git("log", "-1", "--format=%h", "--", name).stdout.strip() or "未提交"
        dirty = git("diff", "--quiet", "HEAD", "--", name).returncode != 0
        return h + ("+未提交改动" if dirty else "")
    except Exception:
        return "未提交"

def build_ring(src, dst, eyebrow, lead, version, changelog, gen_rel, title=None,
               inject=None, dims=None):
    """inject: {"名字": "一段 **markdown**"} —— md 里写 `<!-- inject:名字 -->` 占位。
    🔑 用途：**会变的东西（文件清单／数量／体积）别写死在 md 里，出页时现算注入。**
    ⭐ 判据来自全局 CLAUDE.md：手写的清单抄下来第二天就开始烂，而且烂得没有声音。

    🔴 `260902` 修正：原来这行写的是「已渲染好的 HTML 片段」，**是错的，照它写会踩坑** ——
       注入在下面第一步就做，发生在 `parse(md)` / `render()` **之前** ⇒ 注入内容会当正文再渲染一遍，
       给 HTML 就被 esc 成字面量，页面上出现 `-&amp;gt;` 和裸的 `&lt;/code&gt;&lt;/pre&gt;`。
       ⇒ **一律给 markdown**（要代码块就给 ``` 围起来的）。`ops/自动化/_生成定时任务HTML.py` 是对的用法。"""
    src_p, dst_p = pathlib.Path(src), pathlib.Path(dst)
    md = src_p.read_text(encoding="utf-8")
    for k, v in (inject or {}).items():
        tag = "<!-- inject:%s -->" % k
        if tag not in md:
            print("⚠️ md 里没有占位 %s，注入被忽略" % tag, file=sys.stderr)
        md = md.replace(tag, v)
    import re as _re
    left = _re.findall(r"<!-- inject:(\w+) -->", md)
    if left:
        print("🔴 未填的注入占位：%s —— 生成器少传了" % "、".join(left), file=sys.stderr)
    h1 = title or md.split("\n")[0].lstrip("# ").strip()
    secs = parse(md)

    def _plain(x):
        return re.sub(r"<[^>]+>", "", inline(x)).strip()
    # 🎯 第一段是 tldr ⇒ 三行进抬头（标题 → 一句话 → 三行 → 功能栏），🚫 不再当折叠段
    tldr_html = ""
    if secs and secs[0]["meta"].get("tldr"):
        tl = secs.pop(0)
        tldr_html = three(tl["md"])
        mains = [ln.strip() for ln in tl["md"].split("\n") if re.match(r"^\d+\.\s+", ln.strip())]
        mains = [re.sub(r"^\d+\.\s+", "", m).partition("‖")[0].strip() for m in mains]
        if len(mains) != 3:
            print("⚠️ 抬头三行应是 3 条，现在 %d 条" % len(mains), file=sys.stderr)
        for i, m in enumerate(mains, 1):
            if len(_plain(m)) > HEAD_MAX["三行每行"]:
                print("⚠️ 抬头第 %d 行 %d 字，上限 %d：%s" % (i, len(_plain(m)), HEAD_MAX["三行每行"], _plain(m)[:30]), file=sys.stderr)
    else:
        print("⚠️ md 第一段不是 tldr ⇒ 抬头没有三行（标准要求 标题→一句话→三行→功能栏）", file=sys.stderr)
    if len(_plain(h1)) > HEAD_MAX["标题"]:
        print("⚠️ 标题 %d 字，上限 %d" % (len(_plain(h1)), HEAD_MAX["标题"]), file=sys.stderr)
    if len(_plain(lead)) > HEAD_MAX["一句话"]:
        print("⚠️ 一句话 %d 字，上限 %d" % (len(_plain(lead)), HEAD_MAX["一句话"]), file=sys.stderr)

    ring, parts, nokey = [], [], []
    for n, s in enumerate(secs, 1):
        sid = "s%d" % n
        meta = s["meta"]
        tag = (meta.get("tag") or "").upper()
        tagspan = ('<span class="tag %s">%s</span>' % (TAGCLS[tag], TAGTXT[tag])) if tag in TAGCLS else ""
        subspan = ('<span class="sub">%s</span>' % inline(meta["sub"])) if meta.get("sub") else ""
        if meta.get("ring"):
            t, _, d = meta["ring"].partition("|")
            # 🔴 `260824` 修：ring 按钮的 w1..w4 是**按档位配色**的，不是按顺序
            #    （样式里 .w1=--why · .w2=--how · .w3=--what · .w4=--good）。
            #    原来按 len(ring)+1 发，碰巧对——直到一档横跨两段（第 5 个按钮会没样式）。
            #    ⭐ 一档两段是标准允许的，所以这里按 tag 映射。
            wcls = {"WHY": "w1", "HOW": "w2", "WHAT": "w3", "HOW-GOOD": "w4"}.get(tag, "w2")
            ring.append('<button type="button" class="%s" data-go="%s">'
                        '<div class="k">%s · 第 %d 段</div><div class="t">%s</div>'
                        '<div class="d">%s</div></button>'
                        % (wcls, sid, TAGTXT.get(tag, tag), n,
                           inline(t.strip()), inline(d.strip())))
        inner = three(s["md"]) if meta.get("tldr") else body_html(s["md"], warn=(tag in TAGCLS))
        # 🥇 `260824` 修一个真缺陷（`ops-问题对齐` 报，老徐的用法暴露的）：
        #    `id="sN"` 是**位置编号**，插一段后面全漂 ⇒ 他收藏的 #s3 回来是另一段，**而且完全静默**。
        # 🔑 病因不是"编号会漂"，是**同一个 id 担了两个职责**：
        #    导航（翻页／进度／ring 的"第 N 段"）必须是**位置** · 寻址（收藏回来看同一段）必须是**身份**。
        #    ⇒ 拆开：`id="sN"` 只管导航；`key=` 给一个**稳定锚**只管寻址。
        # 🚫 **故意不做"标题自动 slug 兜底"** —— 标题也会改，那只是把"会漂"换成"会断"，
        #    等于造出第二个静默失效的东西。没写 key 就没有锚，并往 stderr 报，让人补。
        key = (meta.get("key") or "").strip()
        anchor = ('<a id="%s" class="kanchor" aria-hidden="true"></a>\n' % esc(key)) if key else ""
        if not key:
            nokey.append("s%d %s" % (n, s["title"][:20]))
        parts.append(
            '%s<details class="sec" id="%s"%s%s>\n  <summary><span class="num">%d</span>%s'
            '<span class="ti">%s</span>%s</summary>\n  <div class="body">%s</div>\n</details>'
            % (anchor, sid, (' data-key="%s"' % esc(key)) if key else '',
               '', n, tagspan, inline(s["title"]), subspan, inner))   # 260905 起默认全收起：抬头三行已把结论给了

    if nokey:
        print("⚠️ 这些段没有稳定锚（md 里加 `key=xxx`，否则只能靠会漂的 #sN 引用）：\n   "
              + " · ".join(nokey), file=sys.stderr)

    missing = [k for k in ("WHY", "HOW", "WHAT", "HOW-GOOD")
               if k not in [(x["meta"].get("tag") or "").upper() for x in secs]]
    if missing:
        print("🔴 黄金圈缺档：%s —— 标准要求四档必须齐" % "、".join(missing), file=sys.stderr)

    style = (STD / "样式.css").read_text(encoding="utf-8")
    script = (STD / "脚本.js").read_text(encoding="utf-8")
    ctl = (STD / "控件.html").read_text(encoding="utf-8").strip()
    commit = _src_commit(src_p)
    cl = "<br>".join("<code>%s</code> %s：%s" % (v, d, esc(t)) for v, d, t in changelog)

    # 🏷 三维度标签（`260824` 老徐定）：成熟度 1-5（播种→常青）· 重要程度 1-5 星 · 类型
    MT = {1: "播种", 2: "萌芽", 3: "成长", 4: "稳定", 5: "常青"}
    dims_html = ""
    if dims:
        # 🔴 `260824` 实撞：这里原来把局部变量叫 `parts`，**撞掉了外面装 section HTML 的 `parts`**
        #    ⇒ <main> 渲染出 4 个标签、7 段正文全丢，产物从 98KB 掉到 30KB。
        #    ⚠️ Python 不会为此报错 —— 它只是安静地覆盖。⭐ 所以出页后必须看**字节数有没有倒退**。
        dim_parts = []
        m = dims.get("maturity")
        if m:
            dim_parts.append('<span class="dim mt"><b>成熟度</b>'
                         '<span class="v">%s</span><span class="lab">%d/5 %s</span></span>'
                         % ("●" * m + "○" * (5 - m), m, MT.get(m, "")))
        i = dims.get("importance")
        if i:
            dim_parts.append('<span class="dim im"><b>重要程度</b>'
                         '<span class="v">%s</span><span class="lab">%d/5</span></span>'
                         % ("★" * i + "☆" * (5 - i), i))
        k = dims.get("kind")
        if k:
            dim_parts.append('<span class="dim"><b>类型</b><span class="lab">%s</span></span>' % esc(k))
        if dims.get("note"):
            dim_parts.append('<span class="dim"><b>评级依据</b><span class="lab">%s</span></span>'
                         % esc(dims["note"]))
        if dim_parts:
            dims_html = '<div class="dims">%s</div>' % "".join(dim_parts)


    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>%s</title>
<!-- 产物 · 源在 %s · 生成器 %s · 🚫 别手改本文件
     结构照 ~/projects/OPC/格式标准/结构输出标准.md（TL;DR ＋ 黄金圈四档） -->
<style>
%s
%s
.foot{max-width:780px;margin:26px auto 0;padding:16px 22px 40px;border-top:1px solid var(--line);
 font-size:12.5px;color:var(--muted);line-height:1.9;}
.foot .badge{display:inline-block;background:var(--ink);color:#fff;padding:2px 9px;
 font-weight:700;font-size:12px;letter-spacing:.04em;border-radius:5px;margin-right:8px;}
</style>
</head>
<body>
%s
<div id="page">
<div class="hero">
  <span class="eyebrow">%s</span>
  <h1>%s</h1>
  <p class="lead">%s</p>
  %s
  %s
</div>

%s
<main>
%s
</main>

<div class="foot">
  <span class="badge">%s</span>源 <code>%s</code> · 生成器 <code>%s</code> · 提交 <code>%s</code>
  <details class="cl"><summary>版本迭代（%d 版）</summary><div class="body">%s</div></details>
</div>
</div>

<script>
%s
</script>
</body>
</html>
""" % (esc(h1), src_p.name, gen_rel, style, SEARCH_CSS + HERO_CSS, ctl, esc(eyebrow), inline(h1), inline(lead),
       tldr_html, dims_html,
       '\n<div class="ring">\n%s\n</div>\n' % "\n".join(ring) if ring else "",
       "\n".join(parts), version, src_p.name, gen_rel, commit, len(changelog), cl,
       script + SEARCH_JS)

    dst_p.write_text(html, encoding="utf-8")
    print("✅ %s  %.1f KB · %d 段 · 黄金圈 %d 档%s"
          % (dst_p.name, len(html.encode()) / 1024, len(secs), len(ring),
             "" if not missing else " · 🔴 缺 " + "、".join(missing)))
    return dst_p
