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
  function hierarchyLayout(papers, directions, problems) {
    const centers = {}, systems = {}, subsystems = {}, output = [];
    const count = directions.length;
    directions.forEach((direction, index) => {
      const angle = -Math.PI / 2 + index * Math.PI * 2 / count;
      // Fixed coordinates are navigation geometry, never citation or importance data.
      const center = { x: Math.cos(angle) * 1900, y: Math.sin(angle) * 1350, rx: 565, ry: 440 };
      centers[direction.id] = center;
      const children = problems.filter(p => p.direction === direction.id).slice().sort(stableCompare);
      systems[direction.id] = { ...direction, ...center, children: children.map(p => p.id) };
      children.forEach((problem, pi) => {
        const theta = -.6 + pi * Math.PI * 2 / Math.max(1, children.length);
        const radius = children.length === 1 ? 0 : 295;
        const c = { ...problem, x: center.x + Math.cos(theta) * radius, y: center.y + Math.sin(theta) * radius * .76, rx: 150, ry: 120 };
        subsystems[problem.id] = c;
        const cluster = papers.filter(p => p.classification?.problem === problem.id).slice().sort(stableCompare);
        cluster.forEach((paper, i) => {
          const a = .5 + i * Math.PI * (3 - Math.sqrt(5));
          const r = Math.sqrt((i + 1) / (cluster.length + 1));
          output.push({ ...paper, x: c.x + Math.cos(a) * r * 135, y: c.y + Math.sin(a) * r * 100, anchor: i === 0 });
        });
      });
    });
    return { nodes: output, centers, systems, subsystems };
  }
  function search(papers, query) {
    const terms = normalize(query).trim().split(/\s+/).filter(Boolean);
    if (!terms.length) return papers.slice();
    return papers.filter(p => {
      const haystack = normalize([p.title, p.shortName, p.authors, ...(p.tags || [])].join(' '));
      return terms.every(term => haystack.includes(term));
    }).sort((a, b) => Number(normalize(b.title) === normalize(query).trim()) - Number(normalize(a.title) === normalize(query).trim()));
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
    const k = clamp(Math.min((width - 62) / Math.max(140, maxX - minX), (height - 130) / Math.max(140, maxY - minY)), .025, 1.55);
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
  const Core = { hierarchyLayout, layout, regionsFor, search, related, fitCamera, nearest, normalize, TOPICS, CENTERS };
  if (typeof module !== 'undefined' && module.exports) { module.exports = Core; return; }
  if (!scope.document) return;
  const root = document.getElementById('paper-map');
  if (!root) return;
  let data;
  try {
    data = JSON.parse(document.getElementById('paper-map-data').textContent);
    if (data.relationMode !== 'topic-only' || data.verifiedRelations.length || !Array.isArray(data.papers) || !Array.isArray(data.problems) || data.papers.some(p => !p.classification)) return;
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
  const displayLabel = item => item?.displayLabel || item?.label || '';
  const problemLabel = p => displayLabel(data.problems.find(item => item.id === p.classification.problem)) || p.classification.problemLabel;
  const resourceLabels = {benchmark: '基准测试', 'data-collection': '数据采集', 'data-generator': '数据生成器', dataset: '数据集', model: '模型', simulator: '仿真器', software: '软件'};
  const categories = new Map(data.categories.map(c => [c.id, c]));
  const hierarchy = hierarchyLayout(data.papers, data.categories, data.problems);
  const regions = hierarchy.centers;
  const nodes = hierarchy.nodes, nodeById = new Map(nodes.map(p => [p.id, p]));
  const svg = $('#map-canvas'), world = $('.map-world'), nodeLayer = $('.map-nodes'), edgeLayer = $('.map-edges');
  const canvas = $('.map-canvas-wrap'), listWrap = $('.map-list-wrap'), panel = $('.map-sidebar');
  const input = $('#map-search'), suggestions = $('#map-suggestions'), hover = $('.map-hover-card');
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  const smallScreen = window.matchMedia('(max-width: 760px)');
  const nodeEls = new Map(), rows = new Map($$('[data-map-row]').map(el => [el.dataset.mapRow, el]));
  let camera = { x: 0, y: 0, k: .5 }, width = 1, height = 1, animation = 0, cameraEpoch = 0;
  let visible = true, activeSuggestions = [], suggestionIndex = -1, pointer = null, ignoreClickUntil = 0;
  let opener = null, focusedId = nodes[0]?.id || '', lastViewExplicit = false;
  let state = { topic: 'all', problem: '', query: '', selected: '', view: smallScreen.matches ? 'list' : 'map' };
  const yearText = p => p.display?.yearLabel || (p.year ? `${p.year}${p.yearBasis === 'user_provided' ? ' · 原始记录年' : p.yearBasis === 'preprint' ? ' · 预印本年' : ' · 出版年'}` : '年份待核验');
  const shortLabel = p => {
    const title = p.shortName || p.title;
    const colon = title.indexOf(':');
    const preferred = colon > 1 && colon < 24 ? title.slice(0, colon) : title;
    return preferred.length > 31 ? preferred.slice(0, 29).trim() + '…' : preferred;
  };
  const currentNodes = () => search(nodes.filter(p => (state.topic === 'all' || p.mapTopic === state.topic) && (!state.problem || p.classification.problem === state.problem)), state.query);
  const systemEls = new Map(), problemEls = new Map();

  function navigationObject(item, kind, layer) {
    const g = createSvg('g', { transform: `translate(${item.x} ${item.y})`, class: `atlas-${kind}`, role: 'button', tabindex: '-1',
      [`data-atlas-${kind}`]: item.id, 'aria-label': `${displayLabel(item)}。${kind === 'system' ? '探索研究问题' : '查看论文'}。`, style: `--topic:${categories.get(item.direction || item.id).color}` });
    const title = createSvg('title'); title.textContent = item.english || item.label;
    const halo = createSvg('ellipse', { rx: kind === 'system' ? 340 : 150, ry: kind === 'system' ? 255 : 110, class: 'atlas-navigation-halo', 'aria-hidden': 'true' });
    const ring = createSvg('ellipse', { rx: kind === 'system' ? 340 : 150, ry: kind === 'system' ? 255 : 110, class: 'atlas-navigation-orbit', 'aria-hidden': 'true', transform: 'rotate(-16)' });
    const hit = createSvg('rect', { class: 'atlas-navigation-hit', rx: 5 });
    const core = createSvg('circle', { r: 12, class: 'atlas-navigation-core', 'aria-hidden': 'true' });
    const label = createSvg('text', { class: 'atlas-navigation-label' }); label.textContent = displayLabel(item);
    const meta = createSvg('text', { class: 'atlas-navigation-meta' });
    const number = nodes.filter(p => kind === 'system' ? p.mapTopic === item.id : p.classification.problem === item.id).length;
    meta.textContent = `${number} 篇论文${kind === 'system' ? ` / ${item.children.length} ${item.id === 'resources' || item.id === 'cross-domain' ? '个分组' : '个问题'}` : ''}`;
    g.append(title, halo, ring, hit, core, label, meta); layer.append(g); return g;
  }
  const centerTitle = createSvg('text', { x: 0, y: 0, class: 'atlas-galaxy-title', 'text-anchor': 'middle', 'aria-hidden': 'true' }); centerTitle.textContent = 'Atlas';
  const centerNote = createSvg('text', { x: 0, y: 0, class: 'atlas-galaxy-note', 'text-anchor': 'middle', 'aria-hidden': 'true' }); centerNote.textContent = `${nodes.length} 篇论文 / 研究地图`;
  $('.map-regions').append(centerTitle, centerNote);
  Object.values(hierarchy.systems).forEach(item => systemEls.set(item.id, navigationObject(item, 'system', $('.atlas-systems'))));
  Object.values(hierarchy.subsystems).forEach(item => problemEls.set(item.id, navigationObject(item, 'problem', $('.atlas-problems'))));
  nodes.forEach(p => {
    const group = createSvg('g', { transform: `translate(${p.x} ${p.y})`, class: 'map-node', role: 'button',
      tabindex: '-1', 'aria-pressed': 'false', 'aria-label': `${p.title}；${categories.get(p.mapTopic || p.category).english} · ${categories.get(p.mapTopic || p.category).chinese}；${yearText(p)}。查看论文资源。`,
      'data-paper-id': p.id, style: `--topic:${categories.get(p.mapTopic || p.category).color}` });
    const title = createSvg('title'); title.textContent = p.title;
    const label = createSvg('text', { x: 14, y: 4, class: 'map-node-label' }); label.textContent = shortLabel(p);
    group.append(title, createSvg('circle', { r: 28, class: 'map-node-hit' }), createSvg('circle', { r: 15, class: 'map-node-aura', 'aria-hidden': 'true' }), createSvg('circle', { r: 17, class: 'map-node-ring' }), createSvg('circle', { r: 7, class: 'map-node-dot' }), label);
    nodeLayer.append(group); nodeEls.set(p.id, group);
  });

  function cancelCamera() { if (pointer) { const id = pointer.id; pointer = null; svg.classList.remove('is-dragging'); if (svg.hasPointerCapture(id)) svg.releasePointerCapture(id); } cameraEpoch++; if (animation) cancelAnimationFrame(animation); animation = 0; }
  function drawCamera() {
    world.setAttribute('transform', `translate(${camera.x.toFixed(3)} ${camera.y.toFixed(3)}) scale(${camera.k.toFixed(5)})`);
    $('#map-zoom').textContent = `${Math.round(camera.k * 100)}%`;
    const scale = 1 / camera.k;
    centerTitle.style.fontSize = `${(smallScreen.matches ? 19 : 32) * scale}px`; centerTitle.setAttribute('y', -8 * scale);
    centerNote.style.fontSize = `${(smallScreen.matches ? 11 : 13) * scale}px`; centerNote.setAttribute('y', 13 * scale);
    centerTitle.style.display = centerNote.style.display = state.topic === 'all' && !state.query ? '' : 'none';
    for (const [collection, kind] of [[systemEls, 'system'], [problemEls, 'problem']]) collection.forEach(group => {
      const hit = group.querySelector('.atlas-navigation-hit');
      const text = group.querySelector('.atlas-navigation-label').textContent;
      const compact = smallScreen.matches && kind === 'system';
      const labelSize = smallScreen.matches ? 16 : kind === 'system' ? 19 : 17;
      // Account for full-width Chinese glyphs in the screen-space hit target.
      const labelWidth = Array.from(text).reduce((sum, char) => sum + (/[^\x00-\x7f]/.test(char) ? 1 : .6), 0) * labelSize;
      const half = compact ? 27 : Math.max(32, labelWidth / 2 + 8);
      const item = kind === 'system' ? hierarchy.systems[group.dataset.atlasSystem] : hierarchy.subsystems[group.dataset.atlasProblem];
      const screenX = item.x * camera.k + camera.x;
      // Keep a visible node's enlarged label inside a narrow desktop canvas.
      const offset = !compact && screenX >= 0 && screenX <= width ? clamp(screenX, half + 8, width - half - 8) - screenX : 0;
      hit.setAttribute('x', (offset - half) * scale); hit.setAttribute('y', -27 * scale); hit.setAttribute('width', half * 2 * scale); hit.setAttribute('height', (compact ? 54 : kind === 'system' ? 112 : 83) * scale);
      group.querySelector('.atlas-navigation-core').setAttribute('r', (kind === 'system' ? 7 : 4) * scale);
      const label = group.querySelector('.atlas-navigation-label'), meta = group.querySelector('.atlas-navigation-meta');
      label.setAttribute('x', offset * scale); meta.setAttribute('x', offset * scale);
      label.style.fontSize = `${labelSize * scale}px`;
      label.setAttribute('y', (kind === 'system' ? 62 : 30) * scale); meta.style.fontSize = `${13 * scale}px`; meta.setAttribute('y', (kind === 'system' ? 84 : 52) * scale);
    });
    nodeEls.forEach((group, id) => {
      group.querySelector('.map-node-hit').setAttribute('r', 22 * scale);
      group.querySelector('.map-node-dot').setAttribute('r', (id === state.selected ? 3 : state.topic === 'all' && !state.query ? 1.3 : 2) * scale);
      group.querySelector('.map-node-aura').setAttribute('r', (id === state.selected ? 13 : 8) * scale);
      group.querySelector('.map-node-ring').setAttribute('r', 8.5 * scale);
      const label = group.querySelector('.map-node-label');
      label.setAttribute('font-size', String(14 * scale));
      label.style.fontSize = `${14 * scale}px`; label.setAttribute('x', String(12 * scale)); label.setAttribute('y', String(3.5 * scale));
      const p = nodeById.get(id);
      group.classList.remove('is-label');
    });
    // Screen-space label collision checks preserve legibility as zoom changes.
    const occupied = [];
    const candidates = currentNodes().slice().sort((a, b) => Number(b.id === state.selected) - Number(a.id === state.selected) || Number(b.anchor) - Number(a.anchor) || stableCompare(a, b));
    candidates.forEach(p => {
      if (p.id !== state.selected && !state.problem && !state.query) return;
      const rect = { x: p.x * camera.k + camera.x + 11, y: p.y * camera.k + camera.y - 12, w: Array.from(shortLabel(p)).reduce((sum, char) => sum + (/[^\x00-\x7f]/.test(char) ? 14 : 8.4), 0) + 7, h: 23 };
      if (rect.x < 6 || rect.x + rect.w > width - 6 || rect.y < 42 || rect.y + rect.h > height - 72) return;
      if (p.id !== state.selected && occupied.some(r => rect.x < r.x + r.w && rect.x + rect.w > r.x && rect.y < r.y + r.h && rect.y + rect.h > r.y)) return;
      nodeEls.get(p.id).classList.add('is-label'); occupied.push(rect);
    });
  }
  function moveCamera(target, animate = true) {
    cancelCamera(); hover.hidden = true;
    target = { ...target, k: clamp(target.k, .025, 3.5) };
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
  function scopePoints() {
    if (state.problem) return currentNodes();
    if (state.topic !== 'all') return Object.values(hierarchy.subsystems).filter(p => p.direction === state.topic).flatMap(p => [{ x: p.x - 175, y: p.y - 145 }, { x: p.x + 175, y: p.y + 145 }]);
    if (state.query) return currentNodes();
    return Object.values(hierarchy.systems).flatMap(p => [{ x: p.x - 360, y: p.y - 280 }, { x: p.x + 360, y: p.y + 280 }]);
  }
  function fit(animate = true) { moveCamera(fitCamera(scopePoints(), width, height), animate); }
  function focusScope() {
    const target = state.selected ? $('#map-selected-title') : state.view === 'list' ? rows.get(currentNodes()[0]?.id)?.querySelector('a') : state.problem ? nodeEls.get(currentNodes()[0]?.id) : state.topic !== 'all' ? [...problemEls.values()].find(g => !g.hidden) : [...systemEls.values()].find(g => !g.hidden);
    target?.focus({ preventScroll: true });
  }
  function navigate(topic = 'all', problem = '', { push = true, animate = true } = {}) {
    const active = document.activeElement;
    const movingFocus = active?.closest('[data-atlas-system]') || active?.closest('[data-atlas-problem]') || active?.closest('[data-paper-id]') || active?.closest('#atlas-breadcrumbs') || active?.closest('#map-panel-content');
    cancelCamera(); closeSuggestions(); hover.hidden = true; state.topic = categories.has(topic) ? topic : 'all';
    state.problem = hierarchy.subsystems[problem]?.direction === state.topic ? problem : '';
    state.query = ''; state.selected = ''; input.value = ''; opener = null;
    renderMap(); renderPanel(false); renderNavigation(); syncURL(push); fit(animate);
    if (movingFocus) focusScope();
  }
  function goUp() { if (state.selected) closePanel(); else if (state.problem) { const id = state.problem; navigate(state.topic); if (state.view === 'map') problemEls.get(id)?.focus({ preventScroll: true }); else focusScope(); } else if (state.topic !== 'all') { const id = state.topic; navigate(); if (state.view === 'map') systemEls.get(id)?.focus({ preventScroll: true }); else focusScope(); } }
  function renderNavigation() {
    root.dataset.level = state.query ? 'search' : state.problem ? 'problem' : state.topic !== 'all' ? 'system' : 'galaxy';
    const crumbs = $('#atlas-breadcrumbs'); crumbs.replaceChildren();
    const add = (label, topic, problem, current) => { const button = create('button', label); button.type = 'button'; button.dataset.atlasCrumb = topic; button.dataset.atlasProblem = problem || ''; if (current) button.setAttribute('aria-current', 'location'); crumbs.append(button); };
    add('全部方向', 'all', '', state.topic === 'all');
    if (state.topic !== 'all') add(displayLabel(categories.get(state.topic)), state.topic, '', !state.problem);
    if (state.problem) add(displayLabel(hierarchy.subsystems[state.problem]), state.topic, state.problem, true);
    $('#atlas-back').disabled = state.topic === 'all' && !state.selected;
    $('#atlas-level-description').textContent = state.query ? `搜索全部 ${nodes.length} 篇论文` : state.problem ? '选择论文，查看分类证据与资源' : state.topic !== 'all' ? (state.topic === 'resources' ? '跨领域资源：独立资源集合，不作为研究方向' : state.topic === 'cross-domain' ? '跨领域研究：尚无唯一主方向归属' : '选择研究问题，或直接查看论文') : '选择研究方向，展开具体问题';
  }
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
    const k = clamp(camera.k * factor, .025, 3.5);
    moveCamera({ x: x - (x - camera.x) * k / camera.k, y: y - (y - camera.y) * k / camera.k, k }, animate);
  }
  function syncURL(push = false) {
    const url = new URL(location.href);
    for (const key of ['paper', 'topic', 'problem', 'q', 'view']) url.searchParams.delete(key);
    if (state.selected) url.searchParams.set('paper', state.selected);
    if (state.topic !== 'all') url.searchParams.set('topic', state.topic);
    if (state.problem) url.searchParams.set('problem', state.problem);
    if (state.query) url.searchParams.set('q', state.query);
    if (lastViewExplicit) url.searchParams.set('view', state.view);
    if (url.href !== location.href) history[push ? 'pushState' : 'replaceState']({}, '', url);
  }
  function readURL() {
    const params = new URLSearchParams(location.search);
    const topic = params.get('topic') || 'all', paper = params.get('paper') || '', view = params.get('view');
    lastViewExplicit = view === 'map' || view === 'list';
    state = { topic: categories.has(topic) ? topic : 'all', problem: hierarchy.subsystems[params.get('problem')]?.direction === topic ? params.get('problem') : '', query: (params.get('q') || '').slice(0, 300),
      selected: nodeById.has(paper) ? paper : '', view: lastViewExplicit ? view : smallScreen.matches ? 'list' : 'map' };
    if (state.query) { state.topic = 'all'; state.problem = ''; }
    if (state.selected) { const p = nodeById.get(state.selected); state.topic = p.mapTopic; state.problem = p.classification.problem; state.query = ''; }
    input.value = state.query;
  }
  function setRoving(id, focus = false) {
    if (id && nodeEls.has(id)) focusedId = id;
    nodeEls.forEach((group, key) => group.setAttribute('tabindex', key === focusedId && !group.hidden && (state.topic !== 'all' || state.query) ? '0' : '-1'));
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
    systemEls.forEach((group, id) => { const showing = state.topic === 'all' && !state.query; group.hidden = !showing; group.style.display = showing ? '' : 'none'; group.setAttribute('tabindex', showing ? '0' : '-1'); });
    problemEls.forEach((group, id) => { const showing = state.topic !== 'all' && !state.problem && hierarchy.subsystems[id].direction === state.topic && !state.query; group.hidden = !showing; group.style.display = showing ? '' : 'none'; group.setAttribute('tabindex', showing ? '0' : '-1'); });
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
    renderNavigation();
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
    const heading = create('h2', p.title); heading.id = 'map-selected-title'; heading.tabIndex = -1;
    content.append(heading, create('p', p.authors || '作者待核验', 'map-panel-authors'));
    content.append(create('p', `${displayLabel(c)} / ${yearText(p)}`, 'map-panel-kicker'));
    content.append(create('p', c.english, 'map-panel-topic-full'));
    const classification = p.classification;
    content.append(create('p', `${displayLabel(c)} / ${problemLabel(p)}`, 'map-panel-path'));
    const evidence = create('div', null, 'map-classification-evidence');
    evidence.append(create('strong', classification.needsReview ? '分类待复核 · 暂定判断' : '有主来源支持的分类 · 编辑判断'), create('p', p.display?.classificationRationale || classification.rationale), create('small', `证据范围：${p.display?.classificationEvidenceScope || classification.evidenceScope}。${classification.evidenceNote}`));
    if (classification.reviewNote) evidence.append(create('p', classification.reviewNote, 'map-classification-pending'));
    content.append(evidence);
    const crossTags = create('div', null, 'map-panel-tags');
    classification.methodTags.forEach(tag => { const span = create('span', `${tag.label} · 方法`); span.title = tag.evidence_scope; crossTags.append(span); });
    classification.resourceKinds.forEach(kind => crossTags.append(create('span', `${resourceLabels[kind] || kind} · 资源`)));
    classification.secondaryDirections.forEach(id => crossTags.append(create('span', `${displayLabel(categories.get(id)) || id} · 次要方向`)));
    if (crossTags.children.length) content.append(crossTags);
 
    if (p.tags.length) { content.append(create('p', '原始编目标签', 'map-original-tags-label')); const tags = create('div', null, 'map-panel-tags'); p.tags.forEach(tag => tags.append(create('span', tag))); content.append(tags); }
    const badge = create('div', null, 'map-panel-badge');
    badge.append(create('strong', p.display?.metadataLabel || (p.originalRecord ? '原始书目 · 来源字段保留' : '增补书目 · 主来源元数据核验')));
    badge.append(create('span', p.originalRecord ? '原始书目字段的核验状态与 Atlas 分类证据分别记录；摘要支持的分类不等于全文、方法或结论已核验。' : '元数据编目不代表完成全文精读、代码审计或独立复现。'));
    content.append(badge);
    if (p.summary) content.append(create('p', p.summary, 'map-panel-summary'));
    const section = (title) => { const element = create('section', null, 'map-panel-section'); element.append(create('h3', title)); content.append(element); return element; };
    const resources = section('原文与资源'), resourceLinks = create('div', null, 'map-resource-links');
    const links = [safeLink(p.pdfUrl, p.pdfKind === 'publisher' ? '出版方 PDF' : '预印本替代 PDF'), safeLink(p.paperUrl, '出版 / 论文页面'), safeLink(p.projectUrl, '官方项目'), ...p.codeUrls.map((url, i) => safeLink(url, p.codeUrls.length > 1 ? `代码 / 数据 ${i + 1}` : '代码 / 数据')), safeLink(p.detailUrl, '完整书目详情', true), safeLink(p.catalogUrl, '在 Library 中查看')].filter(Boolean);
    links.forEach(link => resourceLinks.append(link)); resources.append(resourceLinks);
    if (!p.paperUrl && !p.pdfUrl) resources.append(create('p', '原文与 PDF 链接尚待核验，暂不提供猜测入口。', 'map-panel-note'));
    if (p.pdfNote) { resources.append(create('p', p.display?.pdfNoteHeading || '书目／链接核验记录；后续阅读范围见各阶段报告。', 'map-panel-note')); resources.append(create('p', p.pdfNote, 'map-panel-note')); }
    if (p.codeNote) resources.append(create('p', p.display?.codeNote || p.codeNote, 'map-panel-note'));
    const stages = section('分阶段阅读'), stageList = create('div', null, 'map-stage-list');
    for (const [index, name] of ['初读', '写作精读', '方法精读'].entries()) {
      const state=p.stages['stage'+(index+1)],artifact=state?.status==='imported'?state.artifacts[0]:null;
      const entry=artifact&&typeof artifact.url==='string'&&artifact.url.startsWith('../')
        ?globalThis.RoboPaperPresentation?.reportEntryPath(p.id,'stage'+(index+1),artifact.url.slice(3),artifact.version):null;
      const report=entry?safeLink('../'+entry,`S${index+1} ${name}`):null;
      if(report){report.classList.add('map-stage-report');report.append(create('small',artifact.version+' · 已导入'));stageList.append(report);}
      else{const button = create('button', `S${index + 1} ${name}`); button.type = 'button'; button.disabled = true;button.append(create('span', '尚未导入')); stageList.append(button);}
    }
    stages.append(stageList, create('p', '只有实际报告完成导入与检查，阅读入口才会开放。', 'map-panel-note'));
    const evidenceLinks = section('分类来源');
    classification.sources.map((url, i) => safeLink(url, `主来源 ${i + 1}`)).filter(Boolean).forEach(link => evidenceLinks.append(link));
    if (!classification.sources.length) evidenceLinks.append(create('p', '仅按题名暂定；尚待主来源分类核查。', 'map-panel-note'));
    const relations = related(nodes, p.id), relationSection = section(relations.mode === 'shared-tags' ? '沿原始编目标签继续探索' : '同一主展示分组');
    relationSection.append(create('p', relations.mode === 'shared-tags' ? `原始编目标签相近（推断），不是已核验方法标签或引用关系。共 ${relations.total} 条匹配，仅显示 ${relations.items.length} 条，按共享标签数及固定 ID 排序。` : `此条目没有共享标签匹配，仅显示 ${relations.items.length} 条同主展示分组的论文作为导航，不绘制关系线。`, 'map-panel-note'));
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
      li.append(create('span', p.title), create('small', `${displayLabel(categories.get(p.mapTopic || p.category))} · ${yearText(p)}`)); suggestions.append(li);
    });
    if (!activeSuggestions.length) { const li = create('li', '没有匹配论文，试试更短的关键词', 'map-suggest-empty'); li.setAttribute('role', 'presentation'); suggestions.append(li); }
    suggestions.hidden = false; input.setAttribute('aria-expanded', 'true');
  }
  function selectPaper(id, source, { history: writeHistory = true, focusPanel = false, animate = true } = {}) {
    const p = nodeById.get(id); if (!p) return;
    cancelCamera(); closeSuggestions(); hover.hidden = true;
    opener = source?.isConnected ? source : nodeEls.get(id);
    state.topic = p.mapTopic; state.problem = p.classification.problem;
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
    navigate();
  }

  input.addEventListener('input', () => {
    state.query = input.value.slice(0, 300); state.topic = 'all'; state.problem = ''; state.selected = '';
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
  $$('[data-map-topic]').forEach(button => button.addEventListener('click', () => navigate(button.dataset.mapTopic)));
  $('#atlas-back').addEventListener('click', goUp);
  $('#atlas-breadcrumbs').addEventListener('click', event => { const button = event.target.closest('[data-atlas-crumb]'); if (button) navigate(button.dataset.atlasCrumb, button.dataset.atlasProblem); });
  for (const [collection, kind] of [[systemEls, 'system'], [problemEls, 'problem']]) collection.forEach((group, id) => {
    const activate = () => kind === 'system' ? navigate(id) : navigate(hierarchy.subsystems[id].direction, id);
    group.addEventListener('click', event => { if (performance.now() < ignoreClickUntil) return; event.stopPropagation(); activate(); });
    group.addEventListener('keydown', event => {
      if (event.key === 'Enter' || event.key === ' ') { event.preventDefault(); event.stopPropagation(); activate(); }
      else if (['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) {
        event.preventDefault(); event.stopPropagation();
        const candidates = Object.values(kind === 'system' ? hierarchy.systems : hierarchy.subsystems).filter(item => !collection.get(item.id).hidden);
        const next = nearest(candidates, candidates.find(p => p.id === id), event.key); if (next) collection.get(next.id).focus({ preventScroll: true });
      }
    });
    group.addEventListener('focusin', () => group.classList.add('is-hovered'));
    group.addEventListener('focusout', () => group.classList.remove('is-hovered'));
  });
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
    if (event.key === 'Escape' && event.target !== input && (state.selected || state.topic !== 'all')) { event.preventDefault(); event.stopPropagation(); goUp(); }
  });

  function paperAtPointer(event) {
    if (state.topic === 'all' && !state.query) return undefined;
    if (!Number.isFinite(event.clientX) || !Number.isFinite(event.clientY)) return event.target.closest('[data-paper-id]')?.dataset.paperId;
    const rect = svg.getBoundingClientRect(), x = event.clientX - rect.left, y = event.clientY - rect.top;
    if (x < 0 || y < 0 || x > rect.width || y > rect.height) return undefined;
    const candidates = currentNodes().filter(p => !nodeEls.get(p.id).hidden).map(p => ({
      paper: p, distance: Math.hypot(p.x * camera.k + camera.x - x, p.y * camera.k + camera.y - y)
    })).sort((a, b) => a.distance - b.distance || stableCompare(a.paper, b.paper));
    // A direct star hit wins; otherwise visible text is the same target as its star.
    // Use rendered screen bounds, not SVG paint order or guessed text widths.
    if (candidates[0]?.distance <= 8) return candidates[0].paper.id;
    const label = candidates.find(({ paper }) => {
      const group = nodeEls.get(paper.id);
      if (!group.classList.contains('is-label') && !group.classList.contains('is-selected') && document.activeElement !== group) return false;
      const box = group.querySelector('.map-node-label').getBoundingClientRect();
      return box.width > 0 && box.height > 0 && event.clientX >= box.left && event.clientX <= box.right && event.clientY >= box.top && event.clientY <= box.bottom;
    });
    return label?.paper.id || (candidates[0]?.distance <= 22 ? candidates[0].paper.id : undefined);
  }
  svg.addEventListener('pointerdown', event => {
    if (event.button !== 0 || event.pointerType === 'touch' || event.target.closest('[data-atlas-system]') || event.target.closest('[data-atlas-problem]')) return;
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
    if (state.topic === 'all' && !state.query) {
      if (['Enter', ' ', 'ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)) { event.preventDefault(); [...systemEls.values()].find(g => !g.hidden)?.focus({ preventScroll: true }); return; }
    }
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
    const p = nodeById.get(id); hover.replaceChildren(create('span', p.title), create('small', `${displayLabel(categories.get(p.mapTopic || p.category))} · 点击查看原文与资源`));
    hover.hidden = false; const x = p.x * camera.k + camera.x, y = p.y * camera.k + camera.y;
    hover.style.left = `${clamp(x + 14, 12, Math.max(12, width - hover.offsetWidth - 14))}px`;
    hover.style.top = `${clamp(y + 15, 45, Math.max(45, height - hover.offsetHeight - 75))}px`;
  }
  nodeLayer.addEventListener('pointerover', updateHover);
  svg.addEventListener('pointermove', updateHover);
  nodeLayer.addEventListener('pointerout', event => { if (!event.relatedTarget?.closest?.('[data-paper-id]')) hover.hidden = true; });
  svg.addEventListener('pointerleave', () => { hover.hidden = true; });
  window.addEventListener('popstate', () => {
    const restoreFocus = !!document.activeElement?.closest('#paper-map');
    cancelCamera(); closeSuggestions(); hover.hidden = true; readURL(); renderMap(); renderPanel(false); renderView();
    if (state.selected && state.view === 'map') focusPaper(state.selected, false); opener = null;
    if (restoreFocus) focusScope();
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
  $('.map-canvas-top>span:last-child').textContent = `${nodes.length} PAPERS / ATLAS`;
  $('.atlas-navigation').hidden = false;
  syncURL(false);
})(typeof window !== 'undefined' ? window : globalThis);
