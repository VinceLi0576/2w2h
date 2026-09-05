(function(){
  var steps = Array.prototype.slice.call(document.querySelectorAll('details.sec'));
  var idx = -1, readMode = false;
  var curEl = document.getElementById('cur'), totEl = document.getElementById('tot');
  totEl.textContent = steps.length;

  function mark(){
    steps.forEach(function(d){ d.classList.remove('cur'); });
    if(idx >= 0 && steps[idx] && steps[idx].open) steps[idx].classList.add('cur');
    curEl.textContent = idx >= 0 ? (idx + 1) : '–';
    document.dispatchEvent(new CustomEvent('secchange', {detail: idx}));   // 侧边目录靠它高亮
  }
  function goto(i, scroll){
    if(i < 0 || i >= steps.length) return;
    idx = i;
    var target = steps[i];
    if(readMode){ target.open = true; }
    else{ steps.forEach(function(d){ d.open = (d === target); }); }
    mark();
    if(history.replaceState) history.replaceState(null, '', '#' + target.id);
    if(scroll !== false) target.scrollIntoView({behavior:'smooth', block:'start'});
  }
  document.getElementById('next').addEventListener('click', function(){ goto(idx + 1); });
  document.getElementById('prev').addEventListener('click', function(){ goto(idx - 1); });
  document.getElementById('collapse').addEventListener('click', function(){
    readMode = false;
    steps.forEach(function(d){ d.open = false; });
    idx = -1; mark();
    if(steps[0]) steps[0].scrollIntoView({behavior:'smooth', block:'start'});
  });
  document.getElementById('expand').addEventListener('click', function(){
    readMode = true;
    steps.forEach(function(d){ d.open = true; }); mark();
  });
  document.querySelectorAll('.ring button').forEach(function(b){
    b.addEventListener('click', function(){
      var i = steps.indexOf(document.getElementById(b.dataset.go));
      if(i !== -1) goto(i);
    });
  });
  steps.forEach(function(d, i){
    d.addEventListener('toggle', function(){
      if(d.open){ idx = i; }
      mark();
    });
  });
  document.addEventListener('keydown', function(e){
    if(/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) return;
    if(e.key === 'ArrowRight'){ e.preventDefault(); goto(idx + 1); }
    if(e.key === 'ArrowLeft'){ e.preventDefault(); goto(idx - 1); }
  });
  window.__goto = goto; window.__idx = function(){ return idx; };   // 侧边目录用
  var h = location.hash.replace('#','');
  var hi = h ? steps.indexOf(document.getElementById(h)) : -1;
  if(hi !== -1) goto(hi, true); else goto(0, false);
})();
/* 缩放（`260905` 老徐要的）：只缩 #page，右上角胶囊不跟着变；记在浏览器里，下次打开还在 */
(function(){
  var page=document.getElementById('page'), zi=document.getElementById('zoomin'), zo=document.getElementById('zoomout');
  if(!page||!zi||!zo) return;
  var KEY='2w2h-zoom', z=100;
  try{ z=parseInt(localStorage.getItem(KEY),10)||100; }catch(e){}
  function apply(){
    page.style.zoom=(z/100);
    zi.title='放大（现在 '+z+'%）'; zo.title='缩小（现在 '+z+'%）';
    try{ localStorage.setItem(KEY, String(z)); }catch(e){}
  }
  zi.addEventListener('click', function(){ if(z<160){ z+=10; apply(); } });
  zo.addEventListener('click', function(){ if(z>80){ z-=10; apply(); } });
  apply();
  window.__zoom=function(){ return z; };
})();
/* 侧边目录（`260905` 老徐：参考飞书／语雀，多段内容要能从侧边看到全部框架）
   宽屏（≥1180）默认常驻左侧，☰ 可收起并记住；窄屏是抽屉，☰ 拉出、点项或点外面收回。
   目录从 DOM 现算（段：num·tag·标题；小节：details.sub 的名字），🚫 不在生成器里另拼一份 */
(function(){
  var page=document.getElementById('page'); if(!page) return;
  var secs=Array.prototype.slice.call(document.querySelectorAll('details.sec')); if(!secs.length) return;
  var nav=document.createElement('nav'); nav.className='toc'; nav.id='toc';
  var head=document.createElement('div'); head.className='toc-h'; head.appendChild(document.createTextNode('目录'));
  var xb=document.createElement('button'); xb.type='button'; xb.className='toc-x'; xb.title='收起目录（右上角 ☰ 再打开）'; xb.textContent='«'; head.appendChild(xb); nav.appendChild(head);
  var ol=document.createElement('ol');
  function closeDrawer(){ document.body.classList.remove('toc-drawer'); }
  secs.forEach(function(d,i){
    var li=document.createElement('li'); li.dataset.i=i;
    var a=document.createElement('a'); a.href='#'+d.id;
    var tag=d.querySelector('summary .tag'), ti=d.querySelector('summary .ti');
    if(tag){ var t=document.createElement('span'); t.className=tag.className; t.textContent=tag.textContent; a.appendChild(t); }
    a.appendChild(document.createTextNode((tag?' ':'')+(ti?ti.textContent:d.id)));
    a.addEventListener('click', function(e){ e.preventDefault(); window.__goto ? window.__goto(i) : (d.open=true, d.scrollIntoView()); closeDrawer(); });
    li.appendChild(a);
    var subs=d.querySelectorAll('details.sub');
    if(subs.length){
      var ol2=document.createElement('ol');
      subs.forEach(function(sd,j){
        if(!sd.id) sd.id=d.id+'-'+(j+1);
        var li2=document.createElement('li'), a2=document.createElement('a'); a2.href='#'+sd.id;
        var nm=sd.querySelector('summary .nm'); a2.textContent=nm?nm.textContent:sd.id;
        a2.addEventListener('click', function(e){
          e.preventDefault();
          if(window.__goto) window.__goto(i,false); d.open=true; sd.open=true;
          sd.scrollIntoView({behavior:'smooth', block:'start'});
          if(history.replaceState) history.replaceState(null,'','#'+sd.id);
          closeDrawer();
        });
        li2.appendChild(a2); ol2.appendChild(li2);
      });
      li.appendChild(ol2);
    }
    ol.appendChild(li);
  });
  nav.appendChild(ol);
  document.body.insertBefore(nav, page);
  function hl(i){ Array.prototype.forEach.call(ol.children, function(li){ li.classList.toggle('cur', +li.dataset.i===i); }); }
  document.addEventListener('secchange', function(e){ hl(e.detail); });
  if(window.__idx) hl(window.__idx());
  var KEY='2w2h-toc', wide=window.matchMedia('(min-width:1180px)'), on=true;
  try{ var v=localStorage.getItem(KEY); if(v!==null) on=(v==='1'); }catch(e){}
  function render(){ document.body.classList.toggle('toc-on', wide.matches && on); if(wide.matches) closeDrawer(); }
  var tb=document.getElementById('toctoggle');
  function toggle(){
    if(wide.matches){ on=!on; try{ localStorage.setItem(KEY, on?'1':'0'); }catch(e){} render(); }
    else{ document.body.classList.toggle('toc-drawer'); }
  }
  if(tb) tb.addEventListener('click', toggle);
  xb.addEventListener('click', function(e){ e.stopPropagation(); toggle(); });
  document.addEventListener('click', function(e){
    if(document.body.classList.contains('toc-drawer') && !nav.contains(e.target) && !(tb && tb.contains(e.target))) closeDrawer();
  });
  (wide.addEventListener ? wide.addEventListener('change', render) : wide.addListener(render));
  render();
  window.__toc=function(){ return {items:ol.children.length, on:document.body.classList.contains('toc-on'), drawer:document.body.classList.contains('toc-drawer')}; };
})();
/* 💬 留言（`260905` 老徐：基于点的位置写留言备注，保存了 AI 再读再改）
   页面 → POST /api/note（Pages Function）→ GitHub Issue（仓库 2w2h，标签「留言」）；AI 用公开 API 读，改完关 issue。
   位置＝当前段／小节（选中文字则带引用）。本地 file:// 打开时发不了，会提示去站上发。 */
(function(){
  var btn=document.getElementById('notebtn'), page=document.getElementById('page'); if(!btn||!page) return;
  var sel={quote:'',where:'',anchor:''};
  function locate(node){
    var el=node&&(node.nodeType===1?node:node.parentElement);
    var sub=el&&el.closest?el.closest('details.sub'):null, sec=el&&el.closest?el.closest('details.sec'):null, w='', a='';
    if(sec){ var ti=sec.querySelector('summary .ti'), n=sec.querySelector('summary .num');
      w='第'+(n?n.textContent:'?')+'段 '+(ti?ti.textContent:''); a='#'+(sec.dataset.key||sec.id); }
    if(sub){ var nm=sub.querySelector('summary .nm'); w+=(w?' · ':'')+(nm?nm.textContent:''); if(sub.id) a='#'+sub.id; }
    return {where:w, anchor:a};
  }
  document.addEventListener('selectionchange', function(){
    var s=document.getSelection(); if(!s||s.isCollapsed) return;
    var t=s.toString().trim(); if(!t||!page.contains(s.anchorNode)) return;
    var l=locate(s.anchorNode); sel={quote:t.slice(0,600), where:l.where, anchor:l.anchor};
  });
  var box=document.createElement('div'); box.className='note'; box.hidden=true;
  box.innerHTML='<div class="note-h">💬 留言给 AI<button type="button" class="note-x" title="关闭">×</button></div>'
    +'<div class="note-w"></div><blockquote class="note-q" hidden></blockquote>'
    +'<textarea placeholder="哪里不对、想改成什么。发出去会变成 GitHub 上的一条 issue，AI 读了改，改完关掉。"></textarea>'
    +'<div class="note-b"><button type="button" class="note-send">发送</button><span class="note-s"></span></div>';
  document.body.appendChild(box);
  var W=box.querySelector('.note-w'), Q=box.querySelector('.note-q'), TA=box.querySelector('textarea'), S=box.querySelector('.note-s');
  function open(){
    var cur=document.querySelector('details.sec.cur')||document.querySelector('details.sec[open]');
    var l=sel.quote?{where:sel.where,anchor:sel.anchor}:locate(cur);
    box.dataset.where=l.where||''; box.dataset.anchor=l.anchor||'';
    W.textContent='位置：'+(l.where||'整页'); Q.hidden=!sel.quote; Q.textContent=sel.quote;
    S.textContent=''; box.hidden=false; TA.focus();
  }
  btn.addEventListener('click', function(){ if(box.hidden) open(); else box.hidden=true; });
  box.querySelector('.note-x').addEventListener('click', function(){ box.hidden=true; });
  box.querySelector('.note-send').addEventListener('click', function(){
    var text=TA.value.trim(); if(!text){ S.textContent='先写点什么'; return; }
    S.textContent='发送中…';
    var pg=location.pathname.split('/').filter(Boolean)[0]||'';
    fetch('/api/note',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({page:pg, anchor:box.dataset.anchor, where:box.dataset.where, quote:Q.hidden?'':Q.textContent, text:text})})
      .then(function(r){ return r.json(); })
      .then(function(j){
        if(j.ok){ S.innerHTML='已存为 <a href="'+j.url+'" target="_blank" rel="noopener">issue #'+j.number+'</a>'; TA.value=''; sel={quote:'',where:'',anchor:''}; }
        else{ S.textContent='没存上：'+(j.error||'未知错误'); }
      })
      .catch(function(e){ S.textContent='没存上：'+(location.protocol==='file:'?'本地文件打开的页面发不了，去站上发':e.message); });
  });
  window.__note=function(){ return {open:!box.hidden, where:box.dataset.where, anchor:box.dataset.anchor, quote:Q.hidden?'':Q.textContent}; };
})();
