'use strict';
(() => {
  const grid = document.querySelector('#paper-grid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll('.paper-card'));
  const search = document.querySelector('#search');
  const year = document.querySelector('#year-filter');
  const status = document.querySelector('#status-filter');
  const sort = document.querySelector('#sort');
  const method=document.querySelector('#method-filter'),resource=document.querySelector('#resource-filter'),direction=document.querySelector('#direction-filter');
  const methodButtons=Array.from(document.querySelectorAll('[data-method-chip]'));
  const topicButtons = Array.from(document.querySelectorAll('[data-topic]'));
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty-state');
  const more = document.querySelector('#load-more');
  let topic = 'all', limit = 24, timer;
  let view='cards';
  const chips=document.querySelector('#active-filters'),viewButtons=Array.from(document.querySelectorAll('[data-view]'));
  function syncView(){grid.classList.toggle('list-view',view==='list');viewButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.view===view)))}
  const validSelect = (select, value) => Array.from(select.options).some(o => o.value === value) ? value : 'all';
  function readQuery() {
    const q = new URLSearchParams(window.location.search);
    search.value = q.get('q') || '';
    view=q.get('view')==='list'?'list':'cards';syncView();
    topic = topicButtons.some(b => b.dataset.topic === q.get('topic')) ? q.get('topic') : 'all';
    direction.value=validSelect(direction,q.get('direction')||q.get('topic'));
    method.value=validSelect(method,q.get('method'));resource.value=validSelect(resource,q.get('resource'));
    year.value = validSelect(year, q.get('year'));
    status.value = validSelect(status, q.get('status'));
    sort.value = ['curated','newest','title'].includes(q.get('sort')) ? q.get('sort') : 'curated';
  }
  function updateQuery() {
    const q = new URLSearchParams();
    if (search.value.trim()) q.set('q', search.value.trim());
    if (topic !== 'all') q.set('topic', topic);
    if(direction.value!=='all')q.set('direction',direction.value);
    if(method.value!=='all')q.set('method',method.value);if(resource.value!=='all')q.set('resource',resource.value);
    if (year.value !== 'all') q.set('year', year.value);
    if (status.value !== 'all') q.set('status', status.value);
    if (sort.value !== 'curated') q.set('sort', sort.value);
    if(view==='list')q.set('view','list');
    const next = window.location.pathname + (q.size ? '?' + q.toString() : '') + window.location.hash;
    window.history.replaceState(null, '', next);
    document.dispatchEvent(new CustomEvent('catalog:updated'));
  }
  function apply(reset = true, save = true) {
    if (reset) limit = 24;
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const match = cards.filter(c => (topic === 'all' || c.dataset.topics.split(' ').includes(topic))
      && (direction.value==='all'||c.dataset.category===direction.value)
      && (method.value==='all'||c.dataset.methods.split('|').includes(method.value))
      && (resource.value==='all'||c.dataset.resources.split('|').includes(resource.value))
      && (year.value === 'all' || c.dataset.year === year.value)
      && (status.value === 'all' || c.dataset.status === status.value)
      && terms.every(t => c.dataset.search.includes(t)));
    match.sort((a,b) => {
      if (sort.value === 'curated' && a.dataset.status !== b.dataset.status) return a.dataset.status === 'verified' ? -1 : 1;
      if (sort.value !== 'title' && a.dataset.sortYear !== b.dataset.sortYear) return Number(b.dataset.sortYear) - Number(a.dataset.sortYear);
      return a.dataset.title.localeCompare(b.dataset.title, 'en');
    });
    cards.forEach(c => { c.hidden = true; });
    match.forEach((c,i) => { c.hidden = i >= limit; grid.appendChild(c); });
    count.textContent = `找到 ${match.length} 篇论文${match.length > limit ? ` · 已显示 ${limit} 篇` : ''}`;
    empty.hidden = match.length !== 0;
    more.hidden = match.length <= limit;
    more.textContent = `显示更多论文（还剩 ${Math.max(0, match.length-limit)} 篇） ↓`;
    const label=document.querySelector('#catalog-search-label');if(label)label.textContent=search.value.trim()||'搜索标题、作者或关键词';
    topicButtons.forEach(b => { const active = b.dataset.topic === topic; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
    methodButtons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.methodChip===method.value)));
    if(chips){chips.replaceChildren();const active=[];if(search.value.trim())active.push(['关键词：'+search.value.trim(),()=>search.value='']);if(topic!=='all')active.push([topicButtons.find(b=>b.dataset.topic===topic).querySelector('span').textContent,()=>topic='all']);if(direction.value!=='all')active.push(['细分方向：'+direction.selectedOptions[0].textContent,()=>direction.value='all']);if(method.value!=='all')active.push(['方法：'+method.selectedOptions[0].textContent,()=>method.value='all']);if(resource.value!=='all')active.push(['资源：'+resource.selectedOptions[0].textContent,()=>resource.value='all']);if(year.value!=='all')active.push(['出版年：'+year.selectedOptions[0].textContent,()=>year.value='all']);if(status.value!=='all')active.push([status.selectedOptions[0].textContent,()=>status.value='all']);for(const [label,clear] of active){const b=document.createElement('button');b.type='button';b.textContent=label+' ×';b.setAttribute('aria-label','移除筛选 '+label);b.addEventListener('click',()=>{clear();apply()});chips.append(b)}if(active.length){const b=document.createElement('button');b.type='button';b.className='clear-all';b.textContent='清除全部';b.addEventListener('click',()=>{search.value='';topic='all';year.value='all';status.value='all';method.value='all';resource.value='all';direction.value='all';apply()});chips.append(b)}chips.hidden=!active.length}
    if (save) updateQuery();
    else document.dispatchEvent(new CustomEvent('catalog:updated'));
  }
  methodButtons.forEach(b=>b.addEventListener('click',()=>{method.value=method.value===b.dataset.methodChip?'all':b.dataset.methodChip;apply()}));
  viewButtons.forEach(b=>b.addEventListener('click',()=>{view=b.dataset.view;syncView();updateQuery()}));
  search.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(() => apply(), 120); });
  [year,status,sort,method,resource,direction].forEach(s => s.addEventListener('change', () => apply()));
  topicButtons.forEach(b => b.addEventListener('click', () => { topic = b.dataset.topic; apply(); }));
  more.addEventListener('click', () => { limit += 24; apply(false); });
  document.querySelector('#reset-filters').addEventListener('click', () => { search.value=''; topic='all'; year.value='all'; status.value='all'; method.value='all'; resource.value='all';direction.value='all'; sort.value='curated'; apply(); document.querySelector('.catalog-search-trigger')?.focus(); });
  document.addEventListener('keydown', e => {
    
    if (e.key === 'Escape' && document.activeElement === search && search.value) { search.value=''; apply(); }
  });
  window.addEventListener('popstate', () => { readQuery(); apply(true,false); });
  window.addEventListener('pageshow', e => { if (e.persisted) { readQuery(); apply(true,false); } });
  readQuery(); apply(true,false);
})();
