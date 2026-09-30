/* RoboPaperAtlas topic map: deterministic SVG, zero runtime dependencies.
 * There is no citation graph, force simulation, importance score, or model call.
 */
(function (scope) {
  'use strict';
  const TOPICS = ['navigation', 'wbc', 'vla', 'methods', 'sim-tools', 'data-benchmarks'];
  const CENTERS = Object.fromEntries(TOPICS.map((id, index) => [id, { x: 370 + (index % 3) * 680, y: 310 + Math.floor(index / 3) * 555, rx: 295, ry: 215 }]));
  const normalize = value => String(value || '').normalize('NFKC').toLocaleLowerCase();
  const stableCompare = (a, b) => a.id < b.id ? -1 : a.id > b.id ? 1 : 0;
  const clamp = (value, low, high) => Math.min(high, Math.max(low, value));
  function regionsFor(topicIds = TOPICS) {
    if (topicIds.length === TOPICS.length && topicIds.every(id => CENTERS[id])) return Object.fromEntries(topicIds.map(id => [id, { ...CENTERS[id] }]));
    // Geometry configuration only; adding a region never reclassifies a paper.
    return Object.fromEntries(topicIds.map((id, index) => [id, { x: 370 + (index % 3) * 680, y: 310 + Math.floor(index / 3) * 555, rx: 295, ry: 215 }]));
  }
  function layout(papers, regions) {
    regions = regions || regionsFor([...new Set(papers.map(p => p.mapTopic || p.category))].sort((a, b) => {
      const ai = TOPICS.indexOf(a), bi = TOPICS.indexOf(b);
      return (ai < 0 ? 99 : ai) - (bi < 0 ? 99 : bi) || (a < b ? -1 : a > b ? 1 : 0);
    }));
    const nodes = [];
    for (const category of Object.keys(regions)) {
      const cluster = papers.filter(p => (p.mapTopic || p.category) === category).slice().sort(stableCompare);
      const c = regions[category];
      cluster.forEach((paper, index) => {
        // Golden-angle packing, fixed order and fixed category centers. No physics.
        const angle = index * Math.PI * (3 - Math.sqrt(5)) + .35;
        const radius = Math.sqrt((index + .65) / (cluster.length + 1));
        nodes.push({ ...paper, x: c.x + Math.cos(angle) * radius * (c.rx - 31),
          y: c.y + Math.sin(angle) * radius * (c.ry - 29),
          anchor: index === 0 || index === Math.floor(cluster.length / 2) });
      });
    }
    return nodes;
  }
  function search(papers, query) {
    const terms = normalize(query).trim().split(/\s+/).filter(Boolean);
    if (!terms.length) return papers.slice();
    return papers.filter(p => {
      const haystack = normalize([p.title, p.shortName, p.authors, ...(p.tags || [])].join(' '));
      return terms.every(term => haystack.includes(term));
    });
  }
  function related(papers, id, limit = 6) {
    const selected = papers.find(p => p.id === id);
    if (!selected) return { mode: 'none', items: [], total: 0 };
    const tags = new Map((selected.tags || []).map(tag => [normalize(tag), tag]));
    const matches = papers.filter(p => p.id !== id).map(p => {
      const other = new Set((p.tags || []).map(normalize));
      return { paper: p, sharedTags: [...tags].filter(([key]) => other.has(key)).map(([, tag]) => tag) };
    }).filter(match => match.sharedTags.length)
      .sort((a, b) => b.sharedTags.length - a.sharedTags.length || stableCompare(a.paper, b.paper));
    if (matches.length) return { mode: 'shared-tags', items: matches.slice(0, limit), total: matches.length };
    const fallback = papers.filter(p => p.id !== id && (p.mapTopic || p.category) === (selected.mapTopic || selected.category)).sort(stableCompare);
    return { mode: 'category-only', items: fallback.slice(0, limit).map(paper => ({ paper, sharedTags: [] })), total: fallback.length };
  }
  function fitCamera(nodes, width, height) {
    if (!nodes.length || !width || !height) return { x: width / 2, y: height / 2, k: .5 };
    const minX = Math.min(...nodes.map(p => p.x)) - 74, maxX = Math.max(...nodes.map(p => p.x)) + 74;
    const minY = Math.min(...nodes.map(p => p.y)) - 105, maxY = Math.max(...nodes.map(p => p.y)) + 76;
    const k = clamp(Math.min((width - 62) / Math.max(140, maxX - minX), (height - 130) / Math.max(140, maxY - minY)), .08, 1.55);
    return { x: width / 2 - (maxX + minX) / 2 * k, y: (height - 12) / 2 - (maxY + minY) / 2 * k, k };
  }
  function nearest(nodes, current, direction) {
    const vector = { ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1] }[direction];
    if (!vector || !current) return nodes[0] || null;
    let best = null, bestScore = Infinity;
    nodes.forEach(p => {
      const dx = p.x - current.x, dy = p.y - current.y, ahead = dx * vector[0] + dy * vector[1];
      if (ahead <= 1) return;
      const side = Math.abs(dx * vector[1] - dy * vector[0]);
      const score = Math.hypot(dx, dy) + side * 2.2;
      if (score < bestScore) { best = p; bestScore = score; }
    });
    return best;
  }
  const Core = { layout, regionsFor, search, related, fitCamera, nearest, normalize, TOPICS, CENTERS };
  if (typeof module !== 'undefined' && module.exports) { module.exports = Core; return; }
  if (!scope.document) return;
  const root = document.getElementById('paper-map');
  if (!root) return;
  let data;
  try {
    data = JSON.parse(document.getElementById('paper-map-data').textContent);
    if (data.relationMode !== 'topic-only' || data.verifiedRelations.length || !Array.isArray(data.papers)) return;
  } catch (_) { return; }

  const $ = selector => root.querySelector(selector);
  const $$ = selector => Array.from(root.querySelectorAll(selector));
  const svgNS = 'http://www.w3.org/2000/svg';
  const createSvg = (name, attrs = {}) => {
    const element = document.createElementNS(svgNS, name);
    Object.entries(attrs).forEach(([key, value]) => element.setAttribute(key, String(value)));
    return element;
  };
  const create = (name, text, className) => {
    const element = document.createElement(name);
    if (text != null) element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  const categories = new Map(data.categories.map(c => [c.id, c]));
  const regions = regionsFor(data.categories.map(c => c.id));
  const nodes = layout(data.papers, regions), nodeById = new Map(nodes.map(p => [p.id, p]));
  const svg = $('#map-canvas'), world = $('.map-world'), nodeLayer = $('.map-nodes'), edgeLayer = $('.map-edges');
  const canvas = $('.map-canvas-wrap'), listWrap = $('.map-list-wrap'), panel = $('.map-sidebar');
  const input = $('#map-search'), suggestions = $('#map-suggestions'), hover = $('.map-hover-card');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const smallScreen = window.matchMedia('(max-width: 760px)');
  const nodeEls = new Map(), rows = new Map($$('[data-map-row]').map(el => [el.dataset.mapRow, el]));
  let camera = { x: 0, y: 0, k: .5 }, width = 1, height = 1, animation = 0, cameraEpoch = 0;
  let visible = true, activeSuggestions = [], suggestionIndex = -1, pointer = null, ignoreClickUntil = 0;
  let opener = null, focusedId = nodes[0]?.id || '', lastViewExplicit = false;
  let state = { topic: 'all', query: '', selected: '', view: smallScreen.matches ? 'list' : 'map' };
  const yearText = p => p.year ? `${p.year}${p.yearBasis === 'user_provided' ? ' · 原始记录年' : p.yearBasis === 'preprint' ? ' · 预印本年' : ' · 出版年'}` : '年份待核验';
  const shortLabel = p => {
    const title = p.shortName || p.title;
    const colon = title.indexOf(':');
    const preferred = colon > 1 && colon < 24 ? title.slice(0, colon) : title;
    return preferred.length > 31 ? preferred.slice(0, 29).trim() + '…' : preferred;
  };
  const currentNodes = () => search(nodes.filter(p => state.topic === 'all' || (p.topics || [p.category]).includes(state.topic)), state.query);

  data.categories.forEach(category => {
    const c = regions[category.id], group = createSvg('g', { 'data-region': category.id, style: `--topic:${category.color}` });
    group.append(createSvg('ellipse', { cx: c.x, cy: c.y, rx: c.rx, ry: c.ry, class: 'map-region-shape', transform: `rotate(-18 ${c.x} ${c.y})` }));
    const title = createSvg('text', { x: c.x - c.rx + 14, y: c.y - c.ry - 26, class: 'map-region-title' });
    title.textContent = category.label;
    const subtitle = createSvg('text', { x: c.x - c.rx + 14, y: c.y - c.ry - 7, class: 'map-region-subtitle' });
    subtitle.textContent = `${nodes.filter(p => (p.mapTopic || p.category) === category.id).length} PAPERS`; 
    group.append(title, subtitle); $('.map-regions').append(group);
  });
  nodes.forEach(p => {
    const group = createSvg('g', { transform: `translate(${p.x} ${p.y})`, class: 'map-node', role: 'button',
      tabindex: '-1', 'aria-pressed': 'false', 'aria-label': `${p.title}；${categories.get(p.mapTopic || p.category).english} · ${categories.get(p.mapTopic || p.category).chinese}；${yearText(p)}。查看论文资源。`,
      'data-paper-id': p.id, style: `--topic:${categories.get(p.mapTopic || p.category).color}` });
    const title = createSvg('title'); title.textContent = p.title;
    const label = createSvg('text', { x: 14, y: 4, class: 'map-node-label' }); label.textContent = shortLabel(p);
    group.append(title, createSvg('circle', { r: 28, class: 'map-node-hit' }), createSvg('circle', { r: 15, class: 'map-node-aura', 'aria-hidden': 'true' }), createSvg('circle', { r: 17, class: 'map-node-ring' }), createSvg('circle', { r: 7, class: 'map-node-dot' }), label);
    nodeLayer.append(group); nodeEls.set(p.id, group);
  });

  function cancelCamera() { cameraEpoch++; if (animation) cancelAnimationFrame(animation); animation = 0; }
  function drawCamera() {
    world.setAttribute('transform', `translate(${camera.x.toFixed(3)} ${camera.y.toFixed(3)}) scale(${camera.k.toFixed(5)})`);
    $('#map-zoom').textContent = `${Math.round(camera.k * 100)}%`;
    const scale = 1 / camera.k;
    $$('.map-regions>g').forEach(group => {
      const c = regions[group.dataset.region];
      const title = group.querySelector('.map-region-title'), subtitle = group.querySelector('.map-region-subtitle');
      title.style.fontSize = `${(smallScreen.matches ? 9 : 12) * scale}px`; title.setAttribute('y', String(c.y - c.ry - 22 * scale));
      subtitle.style.fontSize = `${7 * scale}px`; subtitle.setAttribute('y', String(c.y - c.ry - 8 * scale));
    });
    nodeEls.forEach((group, id) => {
      group.querySelector('.map-node-hit').setAttribute('r', 22 * scale);
      group.querySelector('.map-node-dot').setAttribute('r', (id === state.selected ? 2.8 : 1.9) * scale);
      group.querySelector('.map-node-aura').setAttribute('r', (id === state.selected ? 13 : 8) * scale);
      group.querySelector('.map-node-ring').setAttribute('r', 8.5 * scale);
      const label = group.querySelector('.map-node-label');
      label.setAttribute('font-size', String(11 * scale));
      label.style.fontSize = `${11 * scale}px`; label.setAttribute('x', String(12 * scale)); label.setAttribute('y', String(3.5 * scale));
      const p = nodeById.get(id);
      group.classList.remove('is-label');
    });
    // Screen-space label collision checks preserve legibility as zoom changes.
    const occupied = [];
    const candidates = currentNodes().slice().sort((a, b) => Number(b.id === state.selected) - Number(a.id === state.selected) || Number(b.anchor) - Number(a.anchor) || stableCompare(a, b));
    candidates.forEach(p => {
      if (p.id !== state.selected && camera.k < .9) return;
      const rect = { x: p.x * camera.k + camera.x + 11, y: p.y * camera.k + camera.y - 9, w: shortLabel(p).length * 6.3 + 7, h: 18 };
      if (rect.x < 6 || rect.x + rect.w > width - 6 || rect.y < 42 || rect.y + rect.h > height - 72) return;
      if (p.id !== state.selected && occupied.some(r => rect.x < r.x + r.w && rect.x + rect.w > r.x && rect.y < r.y + r.h && rect.y + rect.h > r.y)) return;
      nodeEls.get(p.id).classList.add('is-label'); occupied.push(rect);
    });
  }
  function moveCamera(target, animate = true) {
    cancelCamera(); hover.hidden = true;
    target = { ...target, k: clamp(target.k, .08, 3.5) };
    if (!animate || reducedMotion.matches || !visible || document.hidden || state.view !== 'map') { camera = target; drawCamera(); return; }
    const start = { ...camera }, started = performance.now(), epoch = cameraEpoch;
    const tick = now => {
      if (epoch !== cameraEpoch || document.hidden || !visible) { animation = 0; return; }
      const elapsed = clamp((now - started) / 360, 0, 1), ease = 1 - Math.pow(1 - elapsed, 3);
      camera = { x: start.x + (target.x - start.x) * ease, y: start.y + (target.y - start.y) * ease, k: start.k + (target.k - start.k) * ease };
      drawCamera(); animation = elapsed < 1 ? requestAnimationFrame(tick) : 0;
    };
    animation = requestAnimationFrame(tick);
  }
  function fit(animate = true) { moveCamera(fitCamera(currentNodes(), width, height), animate); }
  function focusPaper(id, animate = true) {
    const p = nodeById.get(id); if (!p) return;
    const k = smallScreen.matches ? .98 : 1.13;
    moveCamera({ x: width / 2 - p.x * k, y: height * .47 - p.y * k, k }, animate);
  }
  function resize() {
    if (state.view !== 'map') { cancelCamera(); return; }
    const rect = canvas.getBoundingClientRect(); if (!rect.width || !rect.height) return;
    width = rect.width; height = rect.height; svg.setAttribute('viewBox', `0 0 ${width} ${height}`);
    if (state.selected) focusPaper(state.selected, false); else fit(false);
  }
  function zoom(factor, x = width / 2, y = height / 2, animate = true) {
    const k = clamp(camera.k * factor, .08, 3.5);
    moveCamera({ x: x - (x - camera.x) * k / camera.k, y: y - (y - camera.y) * k / camera.k, k }, animate);
  }
  function syncURL(push = false) {
    const url = new URL(location.href);
    for (const key of ['paper', 'topic', 'q', 'view']) url.searchParams.delete(key);
    if (state.selected) url.searchParams.set('paper', state.selected);
    if (state.topic !== 'all') url.searchParams.set('topic', state.topic);
    if (state.query) url.searchParams.set('q', state.query);
    if (lastViewExplicit) url.searchParams.set('view', state.view);
    if (url.href !== location.href) history[push ? 'pushState' : 'replaceState']({}, '', url);
  }
  function readURL() {
    const params = new URLSearchParams(location.search);
    const topic = params.get('topic') || 'all', paper = params.get('paper') || '', view = params.get('view');
    lastViewExplicit = view === 'map' || view === 'list';
    state = { topic: categories.has(topic) ? topic : 'all', query: (params.get('q') || '').slice(0, 300),
      selected: nodeById.has(paper) ? paper : '', view: lastViewExplicit ? view : smallScreen.matches ? 'list' : 'map' };
    if (state.selected && !currentNodes().some(p => p.id === state.selected)) { state.topic = 'all'; state.query = ''; }
    input.value = state.query;
  }
  function setRoving(id, focus = false) {
    if (id && nodeEls.has(id)) focusedId = id;
    nodeEls.forEach((group, key) => group.setAttribute('tabindex', key === focusedId && !group.hidden ? '0' : '-1'));
    if (focus) nodeEls.get(focusedId)?.focus({ preventScroll: true });
  }
  function renderMap() {
    const filtered = currentNodes(), ids = new Set(filtered.map(p => p.id));
    const relations = related(nodes, state.selected), relatedIds = new Set(relations.items.map(item => item.paper.id));
    nodeEls.forEach((group, id) => {
      const showing = ids.has(id);
      group.style.display = showing ? '' : 'none'; group.hidden = !showing;
      group.setAttribute('aria-hidden', String(!showing));
      group.classList.toggle('is-selected', id === state.selected);
      group.classList.toggle('is-related', !!state.selected && relatedIds.has(id));
      group.classList.toggle('is-muted', !!state.selected && id !== state.selected && !relatedIds.has(id));
      group.setAttribute('aria-pressed', String(id === state.selected));
    });
    rows.forEach((row, id) => {
      row.hidden = !ids.has(id);
      const link = row.querySelector('a');
      if (id === state.selected) link.setAttribute('aria-current', 'true'); else link.removeAttribute('aria-current');
    });
    if (!ids.has(focusedId)) focusedId = filtered[0]?.id || '';
    setRoving(focusedId);
    $$('.map-regions>g').forEach(group => {
      const count = filtered.filter(p => (p.mapTopic || p.category) === group.dataset.region).length;
      group.style.display = count ? '' : 'none';
      group.querySelector('.map-region-subtitle').textContent = `${count} PAPER STARS`;
    });
    edgeLayer.replaceChildren();
    if (state.selected && ids.has(state.selected) && relations.mode === 'shared-tags') {
      const from = nodeById.get(state.selected);
      relations.items.filter(item => ids.has(item.paper.id)).forEach(({ paper, sharedTags }) => {
        const path = createSvg('path', { d: `M ${from.x} ${from.y} Q ${(from.x + paper.x) / 2 - (paper.y - from.y) * .08} ${(from.y + paper.y) / 2 + (paper.x - from.x) * .08} ${paper.x} ${paper.y}`,
          'data-relation-type': 'shared-tags-inferred' });
        const title = createSvg('title'); title.textContent = `主题相近（共享标签推断）：${sharedTags.join('、')}。不是引用关系。`; path.append(title); edgeLayer.append(path);
      });
    }
    $('#map-result-count').textContent = filtered.length === nodes.length ? `${nodes.length} 篇论文` : `${filtered.length} / ${nodes.length} 篇论文`;
    $('.map-empty').hidden = !!filtered.length; $('.map-list-empty').hidden = !!filtered.length;
    $('#map-search-clear').hidden = !state.query;
    $$('[data-map-topic]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapTopic === state.topic)));
    drawCamera(); // Restore equal default star sizes immediately when a selection closes.
  }
  function safeLink(url, label, full = false) {
    if (!url) return null;
    let parsed; try { parsed = new URL(url, location.href); } catch (_) { return null; }
    if (!['https:', 'http:'].includes(parsed.protocol)) return null;
    const link = create('a', label, full ? 'map-full-detail' : ''); link.href = url;
    if (parsed.origin !== location.origin) { link.target = '_blank'; link.rel = 'noopener noreferrer'; }
    link.append(create('span', '↗')); return link;
  }
  function renderPanel(animate = true) {
    const selected = $('.map-panel-selected'), welcome = $('.map-panel-welcome');
    selected.getAnimations?.().forEach(animation => animation.cancel()); selected.classList.remove('is-entering');
    const p = nodeById.get(state.selected); selected.hidden = !p; welcome.hidden = !!p;
    const content = $('#map-panel-content'); content.replaceChildren(); if (!p) return;
    const c = categories.get(p.mapTopic || p.category); selected.style.setProperty('--topic', c.color);
    content.append(create('p', `${c.label} / ${yearText(p)}`, 'map-panel-kicker'));
    content.append(create('p', `${c.english} · ${c.chinese}`, 'map-panel-topic-full'));
    content.append(create('p', `展示标签（可交叉）：${(p.topics || [p.category]).map(t => categories.get(t)?.label || t).join(' · ')}`, 'map-panel-note')); 
    const heading = create('h2', p.title); heading.id = 'map-selected-title'; heading.tabIndex = -1;
    content.append(heading, create('p', p.authors || '作者待核验', 'map-panel-authors'));
    if (p.tags.length) { const tags = create('div', null, 'map-panel-tags'); p.tags.forEach(tag => tags.append(create('span', tag))); content.append(tags); }
    const badge = create('div', null, 'map-panel-badge');
    badge.append(create('strong', p.originalRecord ? (p.hasVerifiedOverlay ? '原始书目 · 部分字段另有核验' : '原始书目 · 分类暂定') : '增补书目 · 主来源元数据核验'));
    badge.append(create('span', p.originalRecord ? '目录主题与标签仅为初步编目，不代表方法或结论已核验。' : '元数据编目不代表完成全文精读、代码审计或独立复现。'));
    content.append(badge);
    if (p.summary) content.append(create('p', p.summary, 'map-panel-summary'));
    const section = (title) => { const element = create('section', null, 'map-panel-section'); element.append(create('h3', title)); content.append(element); return element; };
    const resources = section('原文与资源'), resourceLinks = create('div', null, 'map-resource-links');
    const links = [safeLink(p.pdfUrl, p.pdfKind === 'publisher' ? '出版方 PDF' : '预印本替代 PDF'), safeLink(p.paperUrl, '出版 / 论文页面'), safeLink(p.projectUrl, '官方项目'), ...p.codeUrls.map((url, i) => safeLink(url, p.codeUrls.length > 1 ? `代码 / 数据 ${i + 1}` : '代码 / 数据')), safeLink(p.detailUrl, '完整书目详情', true), safeLink(p.catalogUrl, '查看同主题目录')].filter(Boolean);
    links.forEach(link => resourceLinks.append(link)); resources.append(resourceLinks);
    if (!p.paperUrl && !p.pdfUrl) resources.append(create('p', '原文与 PDF 链接尚待核验，暂不提供猜测入口。', 'map-panel-note'));
    if (p.pdfNote) resources.append(create('p', p.pdfNote, 'map-panel-note'));
    if (p.codeNote) resources.append(create('p', p.codeNote, 'map-panel-note'));
    const stages = section('分阶段阅读'), stageList = create('div', null, 'map-stage-list');
    for (const [index, name] of ['初读', '写作精读', '方法精读'].entries()) {
      const state=p.stages['stage'+(index+1)],artifact=state?.status==='imported'?state.artifacts[0]:null;
      const report=artifact&&/^\.\.\/artifacts\/rpa-0062\/v1\/(first-pass|writing-close-reading|method-code-reading)\.html$/.test(artifact.url)?safeLink(artifact.url,`S${index+1} ${name}`):null;
      if(report){report.classList.add('map-stage-report');report.append(create('small',artifact.version+' · 已导入'));stageList.append(report);}
      else{const button = create('button', `S${index + 1} ${name}`); button.type = 'button'; button.disabled = true;button.append(create('span', '尚未导入')); stageList.append(button);}
    }
    stages.append(stageList, create('p', '只有实际报告完成导入与检查，阅读入口才会开放。', 'map-panel-note'));
    const relations = related(nodes, p.id), relationSection = section(relations.mode === 'shared-tags' ? '沿共享标签继续探索' : '同一主展示分组');
    relationSection.append(create('p', relations.mode === 'shared-tags' ? `主题相近（推断），非引用关系。共 ${relations.total} 条匹配，仅显示 ${relations.items.length} 条，按共享标签数及固定 ID 排序。` : `此条目没有共享标签匹配，仅显示 ${relations.items.length} 条同主展示分组的论文作为导航，不绘制关系线。`, 'map-panel-note'));
    const list = create('ul', null, 'map-related-list');
    relations.items.forEach(item => {
      const li = create('li'), button = create('button'); button.type = 'button'; button.dataset.relatedPaper = item.paper.id;
      button.append(create('strong', shortLabel(item.paper)), create('small', item.sharedTags.length ? `共享：${item.sharedTags.join(' · ')}` : '仅同主展示分组 · 非方法关系'));
      button.setAttribute('aria-label', `查看 ${item.paper.title}；${item.sharedTags.length ? '共享标签：' + item.sharedTags.join('、') : '同主展示分组'}`);
      li.append(button); list.append(li);
    });
    relationSection.append(list);
    if (p.verificationScope) { const provenance = section('编目核验范围'); provenance.append(create('p', p.verificationScope, 'map-panel-note')); }
    panel.scrollTop = 0;
    if (animate && !reducedMotion.matches && visible && !document.hidden) { void selected.offsetWidth; selected.classList.add('is-entering'); }
  }
  function renderView() {
    $('#map-help').textContent = smallScreen.matches ? '点击节点查看 · 使用按钮缩放 · 页面可正常滚动' : '拖动平移 · Ctrl / ⌘ + 滚轮缩放 · 方向键选择';
    root.dataset.view = state.view; canvas.hidden = state.view !== 'map'; listWrap.hidden = state.view !== 'list';
    $$('[data-map-view]').forEach(button => button.setAttribute('aria-pressed', String(button.dataset.mapView === state.view)));
    if (state.view !== 'map') cancelCamera(); else resize();
  }
  function closeSuggestions() {
    activeSuggestions = [];
    suggestions.hidden = true; input.setAttribute('aria-expanded', 'false'); input.removeAttribute('aria-activedescendant'); suggestionIndex = -1;
  }
  function renderSuggestions() {
    suggestions.replaceChildren(); suggestionIndex = -1; input.removeAttribute('aria-activedescendant');
    const query = input.value.trim(); if (!query) { closeSuggestions(); return; }
    activeSuggestions = search(nodes, query).slice(0, 8);
    activeSuggestions.forEach((p, index) => {
      const li = create('li'); li.id = `map-option-${index}`; li.setAttribute('role', 'option'); li.setAttribute('aria-selected', 'false'); li.dataset.suggestPaper = p.id;
      li.append(create('span', p.title), create('small', `${categories.get(p.mapTopic || p.category).label} · ${yearText(p)}`)); suggestions.append(li);
    });
    if (!activeSuggestions.length) { const li = create('li', '没有匹配论文，试试更短的关键词', 'map-suggest-empty'); li.setAttribute('role', 'presentation'); suggestions.append(li); }
    suggestions.hidden = false; input.setAttribute('aria-expanded', 'true');
  }
  function selectPaper(id, source, { history: writeHistory = true, focusPanel = false, animate = true } = {}) {
    const p = nodeById.get(id); if (!p) return;
    cancelCamera(); closeSuggestions(); hover.hidden = true;
    opener = source?.isConnected ? source : nodeEls.get(id);
    if (state.topic !== 'all' && !(p.topics || [p.category]).includes(state.topic)) state.topic = 'all';
    state.query = ''; input.value = ''; state.selected = id;
    renderMap(); renderPanel(animate); setRoving(id);
    if (state.view === 'map') focusPaper(id, animate);
    if (writeHistory) syncURL(true);
    // This panel is intentionally non-modal. Focus never gets trapped.
    if (focusPanel) $('#map-selected-title').focus({ preventScroll: true });
    if (smallScreen.matches) panel.scrollIntoView({ behavior: 'instant', block: 'start' });
  }
  function closePanel({ restore = true, writeHistory = true } = {}) {
    const previous = state.selected; state.selected = ''; cancelCamera(); renderMap(); renderPanel(false); hover.hidden = true;
    if (writeHistory) syncURL(true);
    if (restore) {
      const target = state.view === 'list' ? rows.get(previous)?.querySelector('a') : nodeEls.get(previous);
      if (opener?.isConnected && !opener.closest('[hidden]') && !opener.closest('#map-panel-content') && opener !== input) opener.focus({ preventScroll: true });
      else target?.focus({ preventScroll: true });
    }
    opener = null;
  }
  function clearFilters() {
    state.topic = 'all'; state.query = ''; input.value = ''; closeSuggestions(); renderMap(); syncURL(true); fit();
  }

  input.addEventListener('input', () => {
    state.query = input.value.slice(0, 300); state.topic = 'all'; state.selected = '';
    renderMap(); renderPanel(false); renderSuggestions(); syncURL(false); if (state.view === 'map') fit();
  });
  input.addEventListener('focus', () => { if (input.value.trim()) renderSuggestions(); });
  input.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); event.stopPropagation(); closeSuggestions(); return; }
    if (['ArrowDown', 'ArrowUp'].includes(event.key)) {
      if (suggestions.hidden) renderSuggestions(); if (!activeSuggestions.length) return;
      event.preventDefault(); suggestionIndex = suggestionIndex < 0 ? (event.key === 'ArrowDown' ? 0 : activeSuggestions.length - 1) : (suggestionIndex + (event.key === 'ArrowDown' ? 1 : -1) + activeSuggestions.length) % activeSuggestions.length;
      Array.from(suggestions.children).forEach((li, index) => li.setAttribute('aria-selected', String(index === suggestionIndex)));
      const option = suggestions.children[suggestionIndex]; input.setAttribute('aria-activedescendant', option.id); option.scrollIntoView({ block: 'nearest' });
    } else if (event.key === 'Enter' && activeSuggestions.length && !suggestions.hidden) {
      event.preventDefault(); selectPaper(activeSuggestions[Math.max(0, suggestionIndex)].id, input, { focusPanel: true });
    }
  });
  suggestions.addEventListener('pointerdown', event => event.preventDefault());
  suggestions.addEventListener('click', event => { const option = event.target.closest('[data-suggest-paper]'); if (option) selectPaper(option.dataset.suggestPaper, input, { focusPanel: true }); });
  $('#map-search-clear').addEventListener('click', () => { state.query = ''; input.value = ''; closeSuggestions(); renderMap(); syncURL(false); fit(); input.focus(); });
  document.addEventListener('pointerdown', event => { if (!event.target.closest('.map-search-wrap')) closeSuggestions(); });
  root.addEventListener('focusout', () => queueMicrotask(() => { if (!document.activeElement?.closest('.map-search-wrap')) closeSuggestions(); }));
  $$('[data-map-topic]').forEach(button => button.addEventListener('click', () => {
    cancelCamera(); closeSuggestions(); state.topic = button.dataset.mapTopic; state.query = ''; state.selected = ''; input.value = '';
    renderMap(); renderPanel(false); syncURL(true); fit();
  }));
  $$('[data-map-view]').forEach(button => button.addEventListener('click', () => {
    state.view = button.dataset.mapView; lastViewExplicit = true; hover.hidden = true; closeSuggestions(); renderView(); syncURL(true);
  }));
  $$('[data-map-reset]').forEach(button => button.addEventListener('click', clearFilters));
  $$('[data-camera]').forEach(button => button.addEventListener('click', () => {
    if (button.dataset.camera === 'fit') fit(); else zoom(button.dataset.camera === 'in' ? 1.3 : 1 / 1.3);
  }));
  $('.map-paper-list').addEventListener('click', event => {
    const link = event.target.closest('[data-map-paper]'); if (!link || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button) return;
    event.preventDefault(); selectPaper(link.dataset.mapPaper, link, { focusPanel: true });
  });
  panel.addEventListener('click', event => {
    const button = event.target.closest('[data-related-paper]'); if (button) selectPaper(button.dataset.relatedPaper, button, { focusPanel: true });
  });
  $('#map-panel-close').addEventListener('click', () => closePanel());
  root.addEventListener('keydown', event => {
    if (event.key === 'Escape' && state.selected && event.target !== input) { event.preventDefault(); event.stopPropagation(); closePanel(); }
  });

  function paperAtPointer(event) {
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) return event.target.closest('[data-paper-id]')?.dataset.paperId;
    const rect = svg.getBoundingClientRect(), x = event.clientX - rect.left, y = event.clientY - rect.top;
    let nearestId, distance = 22;
    currentNodes().forEach(p => {
      const d = Math.hypot(p.x * camera.k + camera.x - x, p.y * camera.k + camera.y - y);
      if (d <= distance) { nearestId = p.id; distance = d; }
    });
    return nearestId;
  }
  svg.addEventListener('pointerdown', event => {
    if (event.button !== 0 || event.pointerType === 'touch') return;
    cancelCamera(); hover.hidden = true;
    pointer = { id: event.pointerId, startX: event.clientX, startY: event.clientY, x: event.clientX, y: event.clientY, moved: false, nodeId: paperAtPointer(event) };
    svg.setPointerCapture(event.pointerId);
  });
  svg.addEventListener('pointermove', event => {
    if (!pointer || pointer.id !== event.pointerId) return;
    const dx = event.clientX - pointer.x, dy = event.clientY - pointer.y;
    if (Math.hypot(event.clientX - pointer.startX, event.clientY - pointer.startY) > 4) pointer.moved = true;
    if (pointer.moved) { camera.x += dx; camera.y += dy; drawCamera(); svg.classList.add('is-dragging'); }
    pointer.x = event.clientX; pointer.y = event.clientY;
  });
  function endPointer(event) {
    if (!pointer || pointer.id !== event.pointerId) return;
    const done = pointer; pointer = null; svg.classList.remove('is-dragging');
    if (svg.hasPointerCapture(event.pointerId)) svg.releasePointerCapture(event.pointerId);
    ignoreClickUntil = performance.now() + 180;
    if (event.type === 'pointerup' && !done.moved && done.nodeId) selectPaper(done.nodeId, nodeEls.get(done.nodeId), { focusPanel: true });
  }
  svg.addEventListener('pointerup', endPointer); svg.addEventListener('pointercancel', endPointer);
  svg.addEventListener('lostpointercapture', () => { pointer = null; svg.classList.remove('is-dragging'); });
  nodeLayer.addEventListener('click', event => {
    if (performance.now() < ignoreClickUntil) return;
    const id = paperAtPointer(event); if (id) selectPaper(id, nodeEls.get(id), { focusPanel: true });
  });
  svg.addEventListener('wheel', event => {
    if (!event.ctrlKey && !event.metaKey) return; // Normal wheel keeps page scrolling.
    event.preventDefault(); const rect = svg.getBoundingClientRect();
    zoom(Math.exp(-clamp(event.deltaY, -100, 100) * .006), event.clientX - rect.left, event.clientY - rect.top, false);
  }, { passive: false });
  svg.addEventListener('keydown', event => {
    const id = event.target.closest('[data-paper-id]')?.dataset.paperId || focusedId;
    if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
      event.preventDefault(); const next = nearest(currentNodes(), nodeById.get(id), event.key);
      if (next) { setRoving(next.id, true); focusPaper(next.id); } return;
    }
    if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); if (id) selectPaper(id, nodeEls.get(id), { focusPanel: true }); }
    if (event.key === '+' || event.key === '=') { event.preventDefault(); zoom(1.3); }
    if (event.key === '-') { event.preventDefault(); zoom(1 / 1.3); }
    if (event.key === 'Home' || event.key === '0') { event.preventDefault(); fit(); }
  });
  nodeLayer.addEventListener('focusin', event => {
    const node = event.target.closest('[data-paper-id]'); if (node) setRoving(node.dataset.paperId);
  });
  function updateHover(event) {
    if (pointer || event.pointerType === 'touch' || smallScreen.matches) return;
    const id = paperAtPointer(event); if (!id) { hover.hidden = true; return; }
    const p = nodeById.get(id); hover.replaceChildren(create('span', p.title), create('small', `${categories.get(p.mapTopic || p.category).label} · 点击查看原文与资源`));
    hover.hidden = false; const x = p.x * camera.k + camera.x, y = p.y * camera.k + camera.y;
    hover.style.left = `${clamp(x + 14, 12, Math.max(12, width - hover.offsetWidth - 14))}px`;
    hover.style.top = `${clamp(y + 15, 45, Math.max(45, height - hover.offsetHeight - 75))}px`;
  }
  nodeLayer.addEventListener('pointerover', updateHover);
  svg.addEventListener('pointermove', updateHover);
  nodeLayer.addEventListener('pointerout', event => { if (!event.relatedTarget?.closest?.('[data-paper-id]')) hover.hidden = true; });
  svg.addEventListener('pointerleave', () => { hover.hidden = true; });
  window.addEventListener('popstate', () => {
    cancelCamera(); closeSuggestions(); hover.hidden = true; readURL(); renderMap(); renderPanel(false); renderView();
    if (state.selected && state.view === 'map') focusPaper(state.selected, false); opener = null;
  });
  document.addEventListener('visibilitychange', () => { if (document.hidden) { cancelCamera(); hover.hidden = true; } });
  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver(entries => {
      visible = entries[0].isIntersecting;
      if (!visible) { cancelCamera(); hover.hidden = true; $('.map-panel-selected').getAnimations?.().forEach(a => a.cancel()); }
    }, { threshold: 0 }); observer.observe(canvas);
  }
  if ('ResizeObserver' in window) { const observer = new ResizeObserver(resize); observer.observe(canvas); } else window.addEventListener('resize', resize);
  reducedMotion.addEventListener('change', () => { cancelCamera(); if (state.selected) focusPaper(state.selected, false); else fit(false); });
  smallScreen.addEventListener('change', () => { if (!lastViewExplicit) state.view = smallScreen.matches ? 'list' : 'map'; renderView(); });

  readURL(); renderMap(); renderPanel(false); root.classList.add('map-ready'); $('.map-toolbar').hidden = false; $('.map-topics').hidden = false;
  renderView(); $('#map-help').textContent = smallScreen.matches ? '点击节点查看 · 使用按钮缩放 · 页面可正常滚动' : '拖动平移 · Ctrl / ⌘ + 滚轮缩放 · 方向键选择';
  $('.map-canvas-top>span:last-child').textContent = `${nodes.length} PAPERS / ${data.categories.length} TOPICS`;
  syncURL(false);
})(typeof window !== 'undefined' ? window : globalThis);
