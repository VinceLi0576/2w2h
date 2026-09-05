/* 批注（`260905` 老徐定的四条，全对）：
   ① 选中一段字 → 光标旁冒「💬 批注」气泡，右键菜单里也有 → 点开就写
   ② 写完：被批注的字底下画黄线，卡片贴在右侧空白、跟那段对齐（像 Word）
   ③ 解决后：卡片变灰折叠、黄线消失；历史在 GitHub 里翻得到（每张卡「发到 GitHub」按钮，🔴 点了才出去）
   ④ 手机没有右边空白：点黄线弹出卡片
   锚定＝段 key ＋ 引用原文 exact ＋ 前后各 32 字 prefix/suffix（W3C Web Annotation 的选择器思路），改了字靠前后文重定位。
   存储先在浏览器（localStorage，按页分桶）；存哪最后定，换存储只改 store 这一小块。

   🔴 **编号＝版本＋序号（`260905` 老徐定，本页的核心规矩）**：
   **版本 ＝ 一轮审阅，不是一次改动。** 一轮里页面改多少次，版本号都锁死不动。
   这一轮的批注顺着编 `2.9.01` `2.9.02` …… **递增不复用**（解决了也不让位）。
   他说一句「这轮排查完毕」⇒ AI 收尾 → 把整轮批注归档进版本迭代那一栏 → 清空页面标记 → 才升下一版。
   ⭐ 这样 changelog 一条 ＝ 一轮，不是流水账；也结构性消掉了「老批注锚不回新版」。 */
(function(){
  var page=document.getElementById('page'), main=document.querySelector('main'); if(!page||!main) return;
  var PAGE=(location.pathname.split('/').filter(Boolean)[0]||'local');
  var VER=(document.querySelector('.foot .badge')||{}).textContent||'';
  var KEY='2w2h-anno:'+PAGE;

  /* ── store（换存储只改这里） */
  var store={
    load:function(){ try{ return JSON.parse(localStorage.getItem(KEY)||'[]'); }catch(e){ return []; } },
    save:function(list){ try{ localStorage.setItem(KEY, JSON.stringify(list)); }catch(e){} }
  };
  var notes=store.load();

  /* 这一轮（当前版本）的下一个编号。递增不复用 —— 已解决的也占着号，🚫 别让新的顶上去 */
  /* 圆圈里那个数字 ＝ 编号末段（2.9.03 → 3）。正文黄线后面和卡片左上角用同一个，一眼对得上 */
  function seq(a){
    var m=(a.no||'').match(/\.(\d+)$/);
    return m ? String(parseInt(m[1],10)) : String(notes.indexOf(a)+1);
  }
  function nextNo(){
    var base=(VER||'v?').replace(/^v/,''), max=0;
    notes.forEach(function(a){
      var m=(a.no||'').match(new RegExp('^'+base.replace(/\./g,'\\.')+'\\.(\\d+)$'));
      if(m) max=Math.max(max, parseInt(m[1],10));
    });
    return base+'.'+(max+1<10?'0':'')+(max+1);
  }
  (function migrate(){ var dirty=false; notes.forEach(function(a){ if(!a.no){ a.no=nextNo(); dirty=true; } }); if(dirty) store.save(notes); })();

  /* ── 工具 */
  function esc(s){ return String(s).replace(/[&<>"]/g,function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function zoom(){ return parseFloat(page.style.zoom)||1; }
  function secOf(node){ var el=node&&(node.nodeType===1?node:node.parentElement); return el&&el.closest?el.closest('details.sec'):null; }
  function whereOf(sec, node){
    if(!sec) return {where:'整页', anchor:''};
    var el=node&&(node.nodeType===1?node:node.parentElement), sub=el&&el.closest?el.closest('details.sub'):null;
    var ti=sec.querySelector('summary .ti'), n=sec.querySelector('summary .num');
    var w='第'+(n?n.textContent:'?')+'段 '+(ti?ti.textContent:''), a='#'+(sec.dataset.key||sec.id);
    if(sub){ var nm=sub.querySelector('summary .nm'); w+=' · '+(nm?nm.textContent:''); if(sub.id) a='#'+sub.id; }
    return {where:w, anchor:a, sec:sec};
  }
  function textNodes(root){
    var w=document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {acceptNode:function(n){
      var p=n.parentNode&&n.parentNode.nodeName; if(p==='SCRIPT'||p==='STYLE'||p==='SUMMARY') return NodeFilter.FILTER_REJECT;
      return n.nodeValue?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT; }});
    var out=[], n; while((n=w.nextNode())) out.push(n); return out;
  }
  /* 在 root 的正文文本里找 exact（用 prefix/suffix 消歧），把命中的文字包进 <mark class="anno"> */
  function shown(el){ var d=el; while(d){ if(d.tagName==='DETAILS' && !d.open) return false; d=d.parentElement; } return true; }
  function wrap(root, a){
    var nodes=textNodes(root), full='', pos=[];
    nodes.forEach(function(n){ pos.push(full.length); full+=n.nodeValue; });
    var cands=[], i=full.indexOf(a.exact); while(i>=0){ cands.push(i); i=full.indexOf(a.exact, i+1); }
    if(!cands.length) return false;
    var best=cands[0], bs=-1;
    cands.forEach(function(c){ var s=0; if(a.prefix&&full.slice(Math.max(0,c-a.prefix.length),c)===a.prefix) s+=2; if(a.suffix&&full.slice(c+a.exact.length, c+a.exact.length+a.suffix.length)===a.suffix) s+=2; if(s>bs){ bs=s; best=c; } });
    var start=best, end=best+a.exact.length, marks=[];
    for(var k=nodes.length-1;k>=0;k--){                 // 从后往前包，前面节点的偏移不受影响
      var n=nodes[k], ns=pos[k], ne=ns+n.nodeValue.length;
      if(ne<=start||ns>=end) continue;
      var s0=Math.max(start,ns)-ns, e0=Math.min(end,ne)-ns;
      var r=document.createRange(); r.setStart(n,s0); r.setEnd(n,e0);
      var m=document.createElement('mark'); m.className='anno'+(a.resolved?' done':''); m.dataset.id=a.id; m.title='点击看批注';
      r.surroundContents(m); marks.push(m);
    }
    return marks.reverse();
  }
  function unwrapAll(){
    document.querySelectorAll('span.anno-dot.inline').forEach(function(d){ d.parentNode && d.parentNode.removeChild(d); });
    document.querySelectorAll('mark.anno').forEach(function(m){ var p=m.parentNode; while(m.firstChild) p.insertBefore(m.firstChild, m); p.removeChild(m); p.normalize(); });
  }

  /* ── 选中 → 气泡 / 右键菜单 */
  var bub=document.createElement('button'); bub.type='button'; bub.className='abub'; bub.hidden=true; bub.textContent='💬 批注'; document.body.appendChild(bub);
  var menu=document.createElement('div'); menu.className='amenu'; menu.hidden=true;
  menu.innerHTML='<button type="button" data-act="anno">💬 批注</button><button type="button" data-act="copy">复制</button>'; document.body.appendChild(menu);
  var pending=null;   // 当前选区快照
  function snap(){
    var s=document.getSelection(); if(!s||s.isCollapsed||!s.rangeCount) return null;
    var r=s.getRangeAt(0), t=s.toString().trim(); if(!t) return null;
    if(!main.contains(r.commonAncestorContainer)) return null;
    var sec=secOf(r.startContainer); if(!sec) return null;
    var body=sec.querySelector('.body'); var nodes=textNodes(body), full='', off=-1, acc=0;
    for(var k=0;k<nodes.length;k++){ if(nodes[k]===r.startContainer){ off=acc+r.startOffset; } acc+=nodes[k].nodeValue.length; full+=nodes[k].nodeValue; }
    if(off<0){ off=full.indexOf(t); } else { var j=full.indexOf(t, Math.max(0,off-2)); if(j>=0) off=j; }
    if(off<0) return null;
    var w=whereOf(sec, r.startContainer);
    return {exact:t.slice(0,600), prefix:full.slice(Math.max(0,off-32),off), suffix:full.slice(off+t.length, off+t.length+32), where:w.where, anchor:w.anchor, secId:sec.id, rect:r.getBoundingClientRect()};
  }
  function showBub(){
    var p=snap(); if(!p){ bub.hidden=true; return; }
    pending=p; bub.hidden=false;
    var x=p.rect.left+p.rect.width/2, y=p.rect.top-10;
    bub.style.left=Math.max(8, Math.min(window.innerWidth-90, x-40))+'px';
    bub.style.top=(y<40? p.rect.bottom+8 : y-36)+'px';
  }
  document.addEventListener('mouseup', function(e){ if(e.target.closest&&e.target.closest('.abub,.amenu,.acomp,.acard,.ctl,.note')) return; setTimeout(showBub, 10); });
  document.addEventListener('touchend', function(){ setTimeout(showBub, 200); });
  document.addEventListener('selectionchange', function(){ var s=document.getSelection(); if(!s||s.isCollapsed){ bub.hidden=true; } });
  document.addEventListener('contextmenu', function(e){
    if(!main.contains(e.target)) return;
    var p=snap(); if(!p) return;
    e.preventDefault(); pending=p; bub.hidden=true;
    menu.hidden=false; menu.style.left=Math.min(window.innerWidth-130, e.clientX)+'px'; menu.style.top=Math.min(window.innerHeight-80, e.clientY)+'px';
  });
  document.addEventListener('mousedown', function(e){ if(!menu.hidden&&!menu.contains(e.target)) menu.hidden=true; });
  menu.addEventListener('click', function(e){
    var b=e.target.closest('button'); if(!b) return; menu.hidden=true;
    if(b.dataset.act==='copy'){ try{ navigator.clipboard.writeText(pending?pending.exact:''); }catch(err){} return; }
    openComposer(pending);
  });
  bub.addEventListener('click', function(){ bub.hidden=true; openComposer(pending); });

  /* ── 写批注的小卡 */
  var comp=document.createElement('div'); comp.className='acomp'; comp.hidden=true;
  comp.innerHTML='<div class="acomp-w"></div><div class="acomp-m"></div><blockquote class="acomp-q"></blockquote><textarea placeholder="这里怎么了、想改成什么"></textarea><div class="acomp-b"><button type="button" class="ok">保存批注</button><button type="button" class="no">取消</button></div>';
  document.body.appendChild(comp);
  var cur=null, editing=null;
  function openComposer(p, edit){
    if(!p) return; cur=p; editing=edit||null;
    comp.querySelector('.acomp-w').textContent=p.where; comp.querySelector('.acomp-q').textContent=p.exact;
    // 写的时候就告诉他这条会编成几号（260905 老徐：没有版本号）；改的时候显示原号
    comp.querySelector('.acomp-m').innerHTML='<span class="anno-dot">'+esc(edit?seq(edit):nextNo().split('.').pop().replace(/^0/,''))+'</span>'
      +'<span class="acard-no">'+esc(edit?edit.no:nextNo())+'</span><span class="acomp-tag">'+(edit?'改这条':'新批注 · '+esc(VER))+'</span>';
    comp.querySelector('textarea').value=editing?editing.text:'';
    comp.querySelector('.ok').textContent=editing?'保存修改':'保存批注';
    comp.hidden=false;
    var x=Math.max(8, Math.min(window.innerWidth-360, p.rect.left)), y=p.rect.bottom+12;
    if(y+220>window.innerHeight) y=Math.max(8, p.rect.top-230);
    comp.style.left=x+'px'; comp.style.top=y+'px';
    comp.querySelector('textarea').focus();
    try{ document.getSelection().removeAllRanges(); }catch(e){}
  }
  comp.querySelector('.no').addEventListener('click', function(){ comp.hidden=true; });
  comp.querySelector('.ok').addEventListener('click', function(){
    var text=comp.querySelector('textarea').value.trim(); if(!text) return;
    if(editing){   // 改一条已有的：内容与「改于」时间，其余（锚、发过的议题）原样不动
      editing.text=text; editing.edited=new Date().toISOString();
      store.save(notes); comp.hidden=true; editing=null; render(); pop.hidden=true; return;
    }
    var a={id:'a'+Date.now().toString(36), no:nextNo(), page:PAGE, version:VER, where:cur.where, anchor:cur.anchor, secId:cur.secId,
           exact:cur.exact, prefix:cur.prefix, suffix:cur.suffix, text:text, created:new Date().toISOString(), resolved:false, remote:''};
    notes.push(a); store.save(notes); comp.hidden=true; render();
  });

  /* ── 渲染：黄线 ＋ 右侧卡片（宽屏）／点黄线弹卡（窄屏） */
  var rail=document.createElement('div'); rail.className='arail'; page.appendChild(rail);
  /* 右侧批注栏的收起把手（跟左边目录的 « 对称）—— 260905 老徐：可以缩进去 */
  var grip=document.createElement('button'); grip.type='button'; grip.className='agrip'; grip.hidden=true;
  document.body.appendChild(grip);
  var AK='2w2h-anno-off';
  try{ if(localStorage.getItem(AK)==='1') document.body.classList.add('anno-off'); }catch(e){}
  grip.addEventListener('click', function(){ var off=document.body.classList.toggle('anno-off');
    try{ localStorage.setItem(AK, off?'1':'0'); }catch(e){} render(); });
  var pop=document.createElement('div'); pop.className='apop'; pop.hidden=true; document.body.appendChild(pop);
  /* 什么时候写的：今天只显示时分，别的显示 月-日 时:分（老徐 260905 要）*/
  function when(iso){
    var d=new Date(iso); if(isNaN(d)) return '';
    var p=function(n){ return (n<10?'0':'')+n; };
    var hm=p(d.getHours())+':'+p(d.getMinutes());
    var t=new Date(); var sameDay=d.toDateString()===t.toDateString();
    return sameDay ? hm : (p(d.getMonth()+1)+'-'+p(d.getDate())+' '+hm);
  }
  function meta(a){
    return '<span class="acard-when" title="'+esc(a.created)+(a.edited?('　改于 '+esc(a.edited)):'')+'">'
      + esc(when(a.created)) + (a.edited?' ✎':'') + '</span>';
  }
  function cardHTML(a){
    var head = '<div class="acard-w"><span class="anno-dot">'+esc(seq(a))+'</span><span class="acard-where">'+esc(a.where)+'</span></div>'
             + '<div class="acard-m"><span class="acard-no">'+esc(a.no||a.version)+'</span>'+meta(a)+'</div>';
    var body = '<blockquote>'+esc(a.exact.slice(0,120))+(a.exact.length>120?'…':'')+'</blockquote>'
             + '<div class="acard-t">'+esc(a.text)+'</div>';
    var look = a.remote ? '<a class="op" href="'+esc(a.remote)+'" target="_blank" rel="noopener" title="看 GitHub 上那条议题">看</a>' : '';
    // 操作一律一个字的绿圆圈（260905 老徐：增删改查之类的一个字就行，✎⇧✓✕ 看不懂）
    if(a.resolved){
      return '<div class="acard done" data-id="'+a.id+'">'+head
        +'<div class="acard-more">'+body+'</div>'
        +'<div class="acard-act">'+look
        +'<button type="button" class="op" data-act="res" title="重新打开这条">开</button>'
        +'<button type="button" class="op" data-act="del" title="删掉这条">删</button></div></div>';
    }
    return '<div class="acard" data-id="'+a.id+'">'+head+body
      +'<div class="acard-act">'
      +'<button type="button" class="op" data-act="edit" title="改这条批注的内容">改</button>'
      +(a.remote ? look : '<button type="button" class="op" data-act="gh" title="发到 GitHub 存起来">传</button>')
      +'<button type="button" class="op" data-act="res" title="标为已解决，页面上就不显示了">解</button>'
      +'<button type="button" class="op" data-act="del" title="删掉这条">删</button></div></div>';
  }
  var GAP=14, MIN=150;   // 正文到卡片的间距 · 卡片最窄（再窄中文一行放不下几个字，不如退回点黄线弹出）
  function railRoom(){
    if(document.body.classList.contains('anno-off')) return 0;
    var ctl=document.querySelector('.ctl');
    var right = ctl ? ctl.getBoundingClientRect().left - 8 : window.innerWidth - 12;
    var room = right - main.getBoundingClientRect().right - GAP;
    return room>=MIN ? room : 0;
  }
  /* 地方够不够摆卡，跟「目录开着没」直接相关 —— 不够时把这句话告诉他，别让卡片默默消失（260905 实撞：
     他窗口 1382＋缩放 110%，扣掉竖条只剩 149，卡片一声不响就没了） */
  function roomHint(){
    if(railRoom()) return '';
    var ctl=document.querySelector('.ctl');
    var right=(ctl?ctl.getBoundingClientRect().left-8:window.innerWidth-12)-main.getBoundingClientRect().right-GAP;
    if(document.body.classList.contains('toc-on')) return '（右边只剩 '+Math.round(right)+'px，收起左边目录就摆得下）';
    return '（右边只剩 '+Math.round(right)+'px，窗口再宽一点就摆得下）';
  }
  function render(){
    unwrapAll(); rail.innerHTML='';
    var room=railRoom(), pending=[];
    notes.forEach(function(a){ try{
      // 🔴 260905 老徐：解决了就从页面上消失 —— 批注本来就是要求改文档，改完原文多半已经没了，
      //    再拿黄线去锚它只会一直标「原文找不到了」。要回看去 💬 列表里翻。
      if(a.resolved){ a._lost=false; return; }
      var sec=document.getElementById(a.secId)||document.querySelector('details.sec[data-key="'+(a.anchor||'').replace('#','')+'"]');
      var marks=sec?wrap(sec.querySelector('.body'), a):false;
      a._lost=!marks;
      if(!marks) return;
      marks.forEach(function(m){ m.addEventListener('click', function(e){ e.stopPropagation(); showPop(a, m); }); });
      // 黄线末尾挂一个绿圆圈序号 —— 跟右边卡片上那个是同一个数（260905 老徐：标记明显一些）
      var last=marks[marks.length-1];
      var dot=document.createElement('span'); dot.className='anno-dot inline'; dot.textContent=seq(a);
      dot.title='第 '+(a.no||seq(a))+' 条批注 · 点看内容';
      dot.addEventListener('click', function(e){ e.stopPropagation(); showPop(a, last); });
      last.appendChild(dot);
      if(room && shown(marks[0])){
        var z=zoom(), pr=page.getBoundingClientRect(), mr=marks[0].getBoundingClientRect();
        pending.push({a:a, top:(mr.top-pr.top)/z});
      }
    }catch(err){ a._lost=true; if(window.console) console.warn('批注渲染失败', a.id, err); } });
    // 🔴 先按黄线在页面上的高度排序，再依次摆；碰撞只把后面的往下推（260905 实撞：按创建顺序摆，第 4 段那条排第一，s1 的两张被挤到它下面）
    pending.sort(function(x,y){ return x.top-y.top; });
    var bottom=-1e9, left=(main.getBoundingClientRect().right-page.getBoundingClientRect().left)/zoom()+GAP;
    pending.forEach(function(it){
      var top=Math.max(it.top, bottom+8);
      var el=document.createElement('div'); el.innerHTML=cardHTML(it.a); el=el.firstChild;
      el.style.top=top+'px'; el.style.left=left+'px'; el.style.width=Math.min(260, room)/zoom()+'px'; rail.appendChild(el);
      bottom=top+el.offsetHeight;
    });

    // 💬 列表：未解决在上，已解决收进折叠 —— 它现在是回看已解决批注的唯一地方
    var list=document.querySelector('.note .note-list');
    if(list){
      var open=notes.filter(function(a){ return !a.resolved; });
      var done=notes.filter(function(a){ return a.resolved; });
      var one=function(a){ return '<div class="acard'+(a.resolved?' done show':'')+' inlist" data-id="'+a.id+'">'
        + (a._lost?'<div class="acard-lost">⚠️ 原文找不到了（文档改过）—— 页面上没有黄线，只在这儿看得到</div>':'')
        + cardHTML(a).replace(/^<div class="acard[^"]*"[^>]*>/,'').replace(/<\/div>$/,'') + '</div>'; };
      var html = open.length ? open.map(one).join('') : '<div class="note-empty">没有未解决的批注。选中一段字，点冒出来的「💬 批注」。</div>';
      if(done.length) html += '<details class="donebox"><summary>✅ 已解决（'+done.length+'）</summary><div>'+done.map(one).join('')+'</div></details>';
      list.innerHTML=html;
    }

    var off=document.body.classList.contains('anno-off'), n=notes.filter(function(a){ return !a.resolved; }).length;
    var hint=roomHint();
    if(off){ grip.textContent='批注 '+n+' »'; grip.title='展开右侧批注栏'; }
    else if(hint){ grip.textContent='批注 '+n+' · 点黄线看'; grip.title='摆不下卡片 '+hint; }
    else{ grip.textContent='«'; grip.title='收起右侧批注栏'; }
    grip.hidden=!n;
    var cnt=document.getElementById('notecnt'); if(cnt){ cnt.textContent=n||''; cnt.hidden=!n; }
  }
  function showPop(a, m){
    pop.innerHTML=cardHTML(a); pop.hidden=false;
    var r=m.getBoundingClientRect(); var x=Math.max(8, Math.min(window.innerWidth-340, r.left)), y=r.bottom+8;
    if(y+200>window.innerHeight) y=Math.max(8, r.top-210);
    pop.style.left=x+'px'; pop.style.top=y+'px';
  }
  document.addEventListener('mousedown', function(e){ if(!pop.hidden&&!pop.contains(e.target)&&!(e.target.closest&&e.target.closest('mark.anno'))) pop.hidden=true; });
  function act(e){
    var b=e.target.closest('button[data-act]'); if(!b) return; var card=b.closest('.acard'); var a=notes.filter(function(x){return x.id===card.dataset.id;})[0]; if(!a) return;
    if(b.dataset.act==='res'){ a.resolved=!a.resolved; store.save(notes); render(); pop.hidden=true;
      // 同步关／开远端议题（发过 GitHub 的才有）—— 260905：解决了那边也该合上
      if(a.remote){ var num=(a.remote.match(/\/(\d+)$/)||[])[1];
        if(num) fetch('/api/note',{method:'PATCH',headers:{'Content-Type':'application/json'},
          body:JSON.stringify({number:+num, state:a.resolved?'closed':'open'})}).catch(function(){}); } }
    if(b.dataset.act==='del'){ if(confirm('删掉这条批注？')){ notes=notes.filter(function(x){return x!==a;}); store.save(notes); render(); pop.hidden=true; } }
    if(b.dataset.act==='gh'){ sendGH(a, b); }
    if(b.dataset.act==='edit'){
      var m=document.querySelector('mark.anno[data-id="'+a.id+'"]');
      openComposer({exact:a.exact, prefix:a.prefix, suffix:a.suffix, where:a.where, anchor:a.anchor, secId:a.secId,
                    rect:(m?m.getBoundingClientRect():card.getBoundingClientRect())}, a);
      pop.hidden=true;
    }
  }
  rail.addEventListener('click', act); pop.addEventListener('click', act);
  document.addEventListener('click', function(e){ var w=e.target.closest&&e.target.closest('.acard.done .acard-w, .acard.done .acard-m'); if(w&&!e.target.closest('button,a')) w.parentNode.classList.toggle('show'); });
  document.addEventListener('click', function(e){ if(e.target.closest&&e.target.closest('.note .note-list')) act(e); });

  /* ── 发到 GitHub（🔴 只在点了按钮时；走 /api/note，站上没配钥匙会回明白话） */
  function sendGH(a, b){
    b.disabled=true; b.textContent='…';
    fetch('/api/note',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({page:PAGE, anchor:a.anchor, where:a.where+' · '+a.version, quote:a.exact, text:a.text+'\n\n<!-- anno '+JSON.stringify({id:a.id,version:a.version,anchor:a.anchor,prefix:a.prefix,suffix:a.suffix})+' -->'})})
      .then(function(r){ return r.json(); }).then(function(j){
        if(j.ok){ a.remote=j.url; store.save(notes); render(); }
        else{ b.disabled=false; b.textContent='传'; alert('没发出去：'+(j.error||'未知错误')); }
      }).catch(function(e){ b.disabled=false; b.textContent='传'; alert('没发出去：'+(location.protocol==='file:'?'本地文件打开的页面发不了，去站上发':e.message)); });
  }

  /* ── 竖条里的 💬：批注列表面板 */
  var btn=document.getElementById('notebtn');
  if(btn){
    var cnt=document.createElement('span'); cnt.id='notecnt'; cnt.className='ctl-badge'; cnt.hidden=true; btn.appendChild(cnt);
    var panel=document.createElement('div'); panel.className='note'; panel.hidden=true;
    panel.innerHTML='<div class="note-h">💬 批注<button type="button" class="note-x" title="关闭">×</button></div><div class="note-list"></div><div class="note-tip">选中正文里的字就能加新批注；「发到 GitHub」点了才出去。</div>';
    document.body.appendChild(panel);
    btn.addEventListener('click', function(){ panel.hidden=!panel.hidden; if(!panel.hidden) render(); });
    panel.querySelector('.note-x').addEventListener('click', function(){ panel.hidden=true; });
  }

  /* ── 重排时机：段展开/收起、缩放、窗口变化 */
  document.querySelectorAll('details').forEach(function(d){ d.addEventListener('toggle', function(){ setTimeout(render, 30); }); });
  window.addEventListener('resize', function(){ clearTimeout(render._t); render._t=setTimeout(render, 120); });
  var zi=document.getElementById('zoomin'), zo=document.getElementById('zoomout');
  [zi,zo].forEach(function(b){ if(b) b.addEventListener('click', function(){ setTimeout(render, 30); }); });
  render();
  window.__anno={list:function(){ return notes; }, add:function(a){ notes.push(a); store.save(notes); render(); }, render:render, snap:snap};
})();
