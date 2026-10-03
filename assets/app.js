'use strict';
(() => {
  const grid = document.querySelector('#paper-grid');
  if (!grid) return;
  const cards = Array.from(grid.querySelectorAll('.paper-card'));
  const search = document.querySelector('#search');
  const year = document.querySelector('#year-filter');
  const status = document.querySelector('#status-filter');
  const sort = document.querySelector('#sort');
  const method = document.querySelector('#method-filter');
  const resource = document.querySelector('#resource-filter');
  const direction = document.querySelector('#direction-filter');
  const reading = document.querySelector('#reading-filter');
  const topicSelect = document.querySelector('#topic-select');
  const clearSearch = document.querySelector('#clear-catalog-search');
  const filterSelects = [direction, method, resource, year, status, reading].filter(Boolean);
  const methodButtons = Array.from(document.querySelectorAll('[data-method-chip]'));
  const topicButtons = Array.from(document.querySelectorAll('[data-topic]'));
  const viewButtons = Array.from(document.querySelectorAll('[data-view]'));
  const count = document.querySelector('#result-count');
  const empty = document.querySelector('#empty-state');
  const more = document.querySelector('#load-more');
  const chips = document.querySelector('#active-filters');
  const filterDisclosure = document.querySelector('.filter-disclosure');
  const filterSummary = filterDisclosure?.querySelector('summary');
  const defaultView = grid.dataset.defaultView === 'list' ? 'list' : 'cards';
  const stateKey = 'robopaperatlas:catalog:v1';
  let topic = 'all', limit = 24, committedLimit = 24, timer, composing = false;
  let view = defaultView, appliedSearch = '';
  const validSelect = (select, value) => Array.from(select.options).some(o => o.value === value) ? value : 'all';
  const cleanQuery = value => globalThis.RoboCatalogNavigation?.cleanQuery(value) ?? new URLSearchParams(value).toString();
  const boundedLimit = value => Number.isInteger(value) && value >= 24 && value <= Math.max(24, cards.length + 23) ? value : 24;
  const boundedScroll = value => Number.isFinite(value) && value >= 0 && value < 1000000 ? value : 0;
  function syncView() {
    grid.classList.toggle('list-view', view === 'list');
    viewButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.view === view)));
  }
  function readQuery() {
    const q = new URLSearchParams(window.location.search);
    search.value = (q.get('q') || '').slice(0, 512);
    view = ['cards', 'list'].includes(q.get('view')) ? q.get('view') : defaultView;
    syncView();
    topic = topicButtons.some(b => b.dataset.topic === q.get('topic')) ? q.get('topic') : 'all';
    direction.value = validSelect(direction, q.get('direction') || q.get('topic'));
    method.value = validSelect(method, q.get('method'));
    resource.value = validSelect(resource, q.get('resource'));
    year.value = validSelect(year, q.get('year'));
    status.value = validSelect(status, q.get('status'));
    if (reading) reading.value = validSelect(reading, q.get('reading'));
    sort.value = ['curated', 'newest', 'title'].includes(q.get('sort')) ? q.get('sort') : 'curated';
  }
  function snapshot(query = cleanQuery(window.location.search), savedLimit = limit) {
    return {query, limit: boundedLimit(savedLimit), scrollY: boundedScroll(window.scrollY || 0)};
  }
  function saveSnapshot(savedLimit = limit) {
    const value = snapshot(undefined, savedLimit);
    window.history.replaceState({...window.history.state, atlasCatalog: value}, '', window.location.href);
    // Bounded per-tab memory supports an explicit detail/reader return link as well as Back.
    try {
      const parsed = JSON.parse(window.sessionStorage.getItem(stateKey) || '[]');
      const items = (Array.isArray(parsed) ? parsed : []).filter(x => x && x.query !== value.query).slice(-19);
      items.push(value);
      window.sessionStorage.setItem(stateKey, JSON.stringify(items));
    } catch (_) { /* History remains usable when session storage is unavailable. */ }
  }
  function restoredSnapshot(state) {
    const query = cleanQuery(window.location.search);
    let value = state?.atlasCatalog;
    if (!value || value.query !== query) {
      if (window.location.hash !== '#catalog') return null;
      try {
        const items = JSON.parse(window.sessionStorage.getItem(stateKey) || '[]');
        value = Array.isArray(items) ? items.find(x => x?.query === query) : null;
      } catch (_) { value = null; }
    }
    return value?.query === query ? {limit: boundedLimit(value.limit), scrollY: boundedScroll(value.scrollY)} : null;
  }
  function updateQuery() {
    const q = new URLSearchParams();
    if (search.value.trim()) q.set('q', search.value.trim().slice(0, 512));
    if (topic !== 'all') q.set('topic', topic);
    if (direction.value !== 'all') q.set('direction', direction.value);
    if (method.value !== 'all') q.set('method', method.value);
    if (resource.value !== 'all') q.set('resource', resource.value);
    if (year.value !== 'all') q.set('year', year.value);
    if (status.value !== 'all') q.set('status', status.value);
    if (reading && reading.value !== 'all') q.set('reading', reading.value);
    if (sort.value !== 'curated') q.set('sort', sort.value);
    if (view !== defaultView) q.set('view', view);
    const next = window.location.pathname + (q.size ? '?' + q.toString() : '') + window.location.hash;
    const current = window.location.pathname + window.location.search + window.location.hash;
    if (next !== current) {
      saveSnapshot(committedLimit);
      window.history.pushState({atlasCatalog: snapshot(cleanQuery(q.toString()))}, '', next);
    }
    committedLimit = limit;
    saveSnapshot();
    document.dispatchEvent(new CustomEvent('catalog:updated'));
  }
  function focusSearch() { search.focus({preventScroll: true}); }
  function clearFilters() {
    search.value = '';
    topic = 'all';
    filterSelects.forEach(select => select.value = 'all');
  }
  function renderFilterFeedback() {
    const advanced = filterSelects.filter(select => select.value !== 'all').length;
    if (filterSummary) filterSummary.textContent = `更多筛选${advanced ? ' · ' + advanced + ' 项' : ''} ＋`;
    if (!chips) return;
    const active = [];
    if (search.value.trim()) active.push(['关键词：' + search.value.trim(), () => search.value = '']);
    if (topic !== 'all') active.push([topicButtons.find(b => b.dataset.topic === topic).querySelector('span').textContent, () => topic = 'all']);
    for (const [select, prefix] of [[direction, '细分方向：'], [method, '方法：'], [resource, '资源：'], [year, '出版年：'], [status, ''], [reading, '阅读：']]) {
      if (select && select.value !== 'all') active.push([prefix + select.selectedOptions[0].textContent, () => select.value = 'all']);
    }
    const signature = JSON.stringify(active.map(([label]) => label));
    if (chips.dataset.feedbackSignature === signature) return;
    chips.dataset.feedbackSignature = signature;
    chips.replaceChildren();
    active.forEach(([label, clear], index) => {
      const b = document.createElement('button');
      b.type = 'button'; b.textContent = label + ' ×'; b.setAttribute('aria-label', '移除筛选 ' + label);
      b.addEventListener('click', () => {
        cancelPendingSearch(); clear(); apply();
        const remaining = Array.from(chips.querySelectorAll('button')).filter(button => !button.classList.contains('clear-all'));
        (remaining[Math.min(index, remaining.length - 1)] || search).focus({preventScroll: true});
      });
      chips.append(b);
    });
    if (active.length) {
      const b = document.createElement('button'); b.type = 'button'; b.className = 'clear-all'; b.textContent = '清除全部';
      b.addEventListener('click', () => { cancelPendingSearch(); clearFilters(); apply(); focusSearch(); }); chips.append(b);
    }
    chips.hidden = !active.length;
  }
  filterDisclosure?.addEventListener('keydown', event => {
    if (event.key === 'Escape' && filterDisclosure.open) {
      event.preventDefault(); filterDisclosure.open = false; filterSummary?.focus({preventScroll: true});
    }
  });
  function apply(reset = true, save = true) {
    if (reset) limit = 24;
    search.value = search.value.slice(0, 512).replace(/[\uD800-\uDBFF]$/, '');
    const terms = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
    const match = cards.filter(c => (topic === 'all' || c.dataset.topics.split(' ').includes(topic))
      && (direction.value === 'all' || c.dataset.category === direction.value)
      && (method.value === 'all' || c.dataset.methods.split('|').includes(method.value))
      && (resource.value === 'all' || c.dataset.resources.split('|').includes(resource.value))
      && (year.value === 'all' || c.dataset.year === year.value)
      && (status.value === 'all' || c.dataset.status === status.value)
      && (!reading || reading.value === 'all' || c.dataset.reading === reading.value)
      && terms.every(t => c.dataset.search.includes(t)));
    match.sort((a, b) => {
      if (sort.value === 'curated' && a.dataset.status !== b.dataset.status) return a.dataset.status === 'verified' ? -1 : 1;
      if (sort.value !== 'title' && a.dataset.sortYear !== b.dataset.sortYear) return Number(b.dataset.sortYear) - Number(a.dataset.sortYear);
      return a.dataset.title.localeCompare(b.dataset.title, 'en');
    });
    cards.forEach(c => c.hidden = true);
    match.forEach((c, i) => { c.hidden = i >= limit; grid.appendChild(c); });
    count.textContent = `找到 ${match.length} 篇论文${match.length > limit ? ` · 已显示 ${limit} 篇` : ''}`;
    empty.hidden = match.length !== 0;
    const emptyQuery = document.querySelector('#empty-query');
    if (emptyQuery) emptyQuery.textContent = search.value.trim() ? `“${search.value.trim()}”在当前条件下没有匹配。试试作者或方法名，或清除筛选。` : '当前筛选条件没有匹配。试试放宽研究方向、年份或阅读状态。';
    more.hidden = match.length <= limit;
    more.textContent = `显示更多论文（还剩 ${Math.max(0, match.length - limit)} 篇） ↓`;
    const label = document.querySelector('#catalog-search-label');
    if (label) label.textContent = search.value.trim() || '搜索标题、作者或关键词';
    if (clearSearch) clearSearch.hidden = !search.value;
    const applyFilters = document.querySelector('#apply-catalog-filters');
    if (applyFilters) applyFilters.textContent = `查看 ${match.length} 篇结果`;
    if (topicSelect) topicSelect.value = topic;
    topicButtons.forEach(b => { const active = b.dataset.topic === topic; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
    methodButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.methodChip === method.value)));
    renderFilterFeedback();
    appliedSearch = search.value.trim();
    if (save) updateQuery();
    else document.dispatchEvent(new CustomEvent('catalog:updated'));
  }
  const cancelPendingSearch = () => { if (timer !== undefined) { clearTimeout(timer); timer = undefined; } };
  function queueSearch() {
    cancelPendingSearch();
    if (!composing) timer = setTimeout(() => { timer = undefined; apply(); }, 180);
  }
  search.addEventListener('compositionstart', () => { composing = true; cancelPendingSearch(); });
  search.addEventListener('compositionend', () => { composing = false; queueSearch(); });
  search.addEventListener('input', queueSearch);
  search.closest('form')?.addEventListener('submit', event => { event.preventDefault(); cancelPendingSearch(); apply(); });
  clearSearch?.addEventListener('click', () => { cancelPendingSearch(); search.value = ''; apply(); focusSearch(); });
  methodButtons.forEach(b => b.addEventListener('click', () => { cancelPendingSearch(); method.value = method.value === b.dataset.methodChip ? 'all' : b.dataset.methodChip; apply(); }));
  viewButtons.forEach(b => b.addEventListener('click', () => { cancelPendingSearch(); view = b.dataset.view; syncView(); apply(search.value.trim() !== appliedSearch); }));
  [...filterSelects, sort].forEach(select => select.addEventListener('change', () => { cancelPendingSearch(); apply(); }));
  topicButtons.forEach(b => b.addEventListener('click', () => { cancelPendingSearch(); topic = b.dataset.topic; apply(); }));
  topicSelect?.addEventListener('change', () => { cancelPendingSearch(); topic = validSelect(topicSelect, topicSelect.value); apply(); });
  more.addEventListener('click', () => {
    cancelPendingSearch();
    if (search.value.trim() !== appliedSearch) { apply(); focusSearch(); return; }
    const previous = limit; limit += 24; apply(false);
    const visible = Array.from(grid.querySelectorAll('.paper-card')).filter(c => !c.hidden);
    count.textContent += ` · 新增显示 ${Math.max(0, visible.length - previous)} 篇`;
    if (more.hidden) visible[previous]?.querySelector('h3')?.querySelector('a')?.focus({preventScroll: true});
  });
  document.querySelector('#reset-filters').addEventListener('click', () => { cancelPendingSearch(); clearFilters(); apply(); focusSearch(); });
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && !composing && !event.isComposing && document.activeElement === search && search.value) {
      event.preventDefault(); cancelPendingSearch(); search.value = ''; apply();
    }
  });
  function restore(state, scroll = true) {
    cancelPendingSearch();
    readQuery();
    const saved = restoredSnapshot(state);
    limit = saved?.limit || 24;
    committedLimit = limit;
    apply(false, false);
    if (saved && scroll) window.scrollTo?.({top: saved.scrollY, behavior: 'instant'});
  }
  window.addEventListener('popstate', event => restore(event.state));
  window.addEventListener('pageshow', event => { if (event.persisted) restore(window.history.state); });
  window.addEventListener('pagehide', () => { cancelPendingSearch(); saveSnapshot(); });
  document.addEventListener('click', event => { if (event.target.closest('a')) saveSnapshot(); });
  restore(window.history.state);
})();
