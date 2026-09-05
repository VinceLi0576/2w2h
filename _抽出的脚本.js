(function(){
  var steps = Array.prototype.slice.call(document.querySelectorAll('details.sec'));
  var idx = -1, readMode = false;
  var curEl = document.getElementById('cur'), totEl = document.getElementById('tot');
  totEl.textContent = steps.length;

  function mark(){
    steps.forEach(function(d){ d.classList.remove('cur'); });
    if(idx >= 0 && steps[idx] && steps[idx].open) steps[idx].classList.add('cur');
    curEl.textContent = idx >= 0 ? (idx + 1) : '–';
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
  var h = location.hash.replace('#','');
  var hi = h ? steps.indexOf(document.getElementById(h)) : -1;
  if(hi !== -1) goto(hi, true); else goto(0, false);
})();
