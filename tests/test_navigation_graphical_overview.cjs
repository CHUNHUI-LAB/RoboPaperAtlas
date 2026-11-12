'use strict';
// Display migration: seven original relations remain, with dropdown selectors outside
// the graph and one selected evidence article in the C panel; all-lines is opt-in.
// Keep the default invocation memory-bounded without raising Node's heap limit.
// The parent only loads node:test and child_process. Each child owns its own
// immutable fixture and source snapshot, and runs one complete named group.
const graphicalGroup = process.env.NAV_GRAPHICAL_TEST_GROUP;
if (!graphicalGroup) {
  const test = require('node:test');
  const assert = require('node:assert/strict');
  const cp = require('node:child_process');
  const originalNames = [
    "graphical S0 leaves frozen science and the original global projection intact",
    "fresh S0 is an unselected General goal with two real parallel branches and 39 original graph positions",
    "all 22 default task graph nodes show short contracts above their original task names",
    "13 default CI controls are actual original root positions and preserve complete accessible questions",
    "all 38 parent paths connect existing S0 positions using their exact preexisting g parents",
    "each of the 22 graphical task controls enters its own active S1 forest and switches between its original views",
    "each of the 13 CI controls opens its exact original g position and Back restores S0 focus",
    "seven selectable typed paths keep exact original endpoints/types and cannot acquire tree-parent semantics",
    "click and Enter on every typed graph edge expose its exact source while preserving route and scientific structure",
    "every source relation endpoint still enters its original S1 scope and Back retains endpoint focus",
    "auxiliary comparison, all 64 source scopes and reading notes remain available outside the default graph",
    "S0 task and subordinate-scope history restore visible entry focus and independent overview scrolling",
    "local AudioGoal S1 preserves scientific selection, zoom, both scrolling regions and focus across Back/Forward",
    "the explicit old graph and cold original g links remain available without overwriting fresh S0 history",
    "graphical S0 retains the exact published literature deep-link and historical reading position",
    "graphical S0 retains the exact published analysis deep-link and historical reading position",
    "graphical S0 retains the exact published index deep-link and historical reading position",
    "relation visibility and notes disclosure survive a task round-trip and saved-history reload",
    "new notes and relation visibility history fields accept only booleans while older snapshots stay valid",
    "SVG parent and typed paths terminate on their advertised original node boxes in the intended coordinate model",
    "typed relation source links are real original URLs without adjoining Chinese prose",
    "resizing the overview preserves the focused typed-relation identity and current scientific route"
];
  const originalPattern = '^(?:' + originalNames.map(name => Array.from(name, ch => '\\^$.*+?()[]{}|'.includes(ch) ? '\\' + ch : ch).join('')).join('|') + ')$';
  for (const [group, pattern, expectedPasses] of [
    ['original22', originalPattern, 22],
    ['review10', '^review: ', 10],
    ['nohash4', '^nohash: ', 4],
  ]) {
    test('graphical overview isolated group: ' + group, t => {
      const env = {...process.env, NAV_GRAPHICAL_TEST_GROUP:group, PYTHONDONTWRITEBYTECODE:'1'};
      // A child test runner needs its own transport, not its parent's IPC mode.
      delete env.NODE_TEST_CONTEXT;
      const result = cp.spawnSync(process.execPath, ['--test', '--test-reporter=tap', '--test-name-pattern=' + pattern, __filename], {
        env, encoding:'utf8', maxBuffer:20 * 1024 * 1024, timeout:180000,
      });
      if (result.stdout) t.diagnostic(result.stdout.trimEnd());
      if (result.stderr) t.diagnostic(result.stderr.trimEnd());
      assert.equal(result.error, undefined, group + ': child must start and finish without timeout or output-buffer failure');
      assert.equal(result.signal, null, group + ': child must not terminate from a signal');
      assert.equal(result.status, 0, group + ': every selected assertion must pass');
      const summary = [...(result.stdout || '').matchAll(/^# pass (\d+)$/gm)].at(-1);
      assert.ok(summary, group + ': child must emit its terminal TAP result');
      assert.equal(Number(summary[1]), expectedPasses, group + ': no expected tests may be silently skipped or omitted');
    });
  }
} else {
  require('node:assert/strict').ok(['original22', 'review8', 'review10', 'nohash4'].includes(graphicalGroup), 'unknown graphical test group');
// S0 graphical-overview behavioral and identity regression only.
// JSDOM does not establish real-browser 1440-pixel readability or visual acceptance.
// The fixture renders production code unchanged and serves exact generated packets
// from a test-owned temporary directory. It never contacts the network.
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const cp = require('node:child_process');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const {JSDOM, ResourceLoader, VirtualConsole} = require('jsdom');
const root = path.resolve(__dirname, '..');
const scienceBytes = zlib.gunzipSync(fs.readFileSync(path.join(root, 'data/navigation-product/model.json.gz')));
const science = JSON.parse(scienceBytes);
const SCIENCE_SHA = '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c';
const scopeById = new Map(science.scopes.map(s => [s.id, s]));
// Audited reading specification, 2026-10-10. These expectations do not come from
// the candidate presentation payload, so a lost or altered entry cannot self-pass.
const TASK_INDEX = [
  ['task:audiogoal', 'AudioGoal', '声音→声源'],
  ['task:audiopointgoal', 'AudioPointGoal', '声音＋位置→到达'],
  ['task:aerial-visual-object-search', 'AVOS', '图文→飞行搜索'],
  ['task:comon', 'CoMON', '特权协作→多目标'],
  ['task:ddn', 'DDN', '需求→可用物体'],
  ['task:goat', 'GOAT', '类别/实例图/语言序列'],
  ['task:hieranav', 'HieraNav', '多级约束→物体'],
  ['task:imagenav', 'ImageNav', '地点图→地点'],
  ['task:instanceimagenav', 'InstanceImageNav', '实例图→同一物'],
  ['task:ivln', 'IVLN', '同环境多段指令'],
  ['task:lamon', 'LaMoN', '逐个描述→对象'],
  ['task:multion', 'MultiON', '有序目标→逐个找'],
  ['task:namo', 'NAMO', '移障→创造通路'],
  ['task:ndh', 'NDH', '对话历史→进展'],
  ['task:category-objectnav', 'ObjectNav', '类别→任一实例'],
  ['task:pointnav', 'PointNav', '坐标→位置'],
  ['task:remote-referent-navigation', 'REVERIE式', '描述→到达并指认'],
  ['task:roomnav', 'RoomNav', '区域→进入区域'],
  ['task:soon', 'SOON', '物体及周边描述→定位'],
  ['task:vln', 'VLN', '路线语句→执行'],
  ['task:person-finding-following', '找人并跟随', '人物→持续跟随'],
  ['task:language-objectnav', '语言物体目标', '描述→合格对象'],
];
const CI_ENTITIES = [
  'legacy:ci_search_unknown_target', 'legacy:ci_generalize_environments',
  'legacy:ci_instruction_progress', 'legacy:ci_recover_route_error',
  'legacy:ci_candidate_verification', 'legacy:ci_semantic_commitment',
  'legacy:ci_dynamic_revisit', 'legacy:ci_negative_evidence',
  'legacy:ci_long_horizon_evidence', 'methods:ci_ground_dynamic_plan',
  'methods:ci_hierarchical_spatial_query', 'methods:ci_spatial_language_grounding',
  'methods:ci_compact_relational_memory',
];
const TASK_RELATIONS = [
  ['tasks:relation:88', 'task:vln', 'task:ivln', 'sequential_composition'],
  ['tasks:relation:89', 'task:category-objectnav', 'task:multion', 'sequential_composition'],
  ['tasks:relation:90', 'task:category-objectnav', 'task:goat', 'composed_goal_type_in'],
  ['tasks:relation:91', 'task:instanceimagenav', 'task:goat', 'composed_goal_type_in'],
  ['tasks:relation:92', 'task:language-objectnav', 'task:goat', 'composed_goal_type_in'],
  ['tasks:relation:93', 'task:language-objectnav', 'task:lamon', 'sequential_composition'],
  ['tasks:relation:94', 'task:imagenav', 'task:instanceimagenav', 'different_success_semantics'],
];
// The science payload and reviewed projection implementation are independently
// pinned: checking DOM against a candidate-defined hierarchy alone could self-pass.
// c26f035's exact source bytes except NATIVE_CSS and _page, whose only role
// is native-page presentation. This retains every projection function, including
// _extend_canonical_scopes below the presentation section; the independent full
// descriptor comparison below is unchanged. The reviewed excluded diff is CSS
// plus shared chrome/title rendering, not scientific inputs or graph identity.
const REVIEWED_PROJECTION_SHA = '08c7fcba5aa4d13d4b8bdb0166133469473699a56526e1f5cfceb68479d1df03';
function projectionImplementationBytes() {
  const source = fs.readFileSync(path.join(root, 'scripts/navigation_research_map.py'), 'utf8');
  const start = source.indexOf('\nNATIVE_CSS = '), end = source.indexOf('\ndef _enhanced(', start);
  assert.ok(start > 0 && end > start, 'the reviewed native-presentation section has exact boundaries');
  return Buffer.from(source.slice(0, start) + source.slice(end));
}
// Frozen descriptor produced by the independently pinned c2301e8 projection
// (implementation SHA-256 c1dcba7bb06d0ad8961ce33b28b596d94b32d4e1fe41d0811de40502321005be).
// It is test evidence, not generated from the implementation under test.
const BASELINE_PROJECTION_SHA = 'f510b12be1bb00747245da9f1ce823ef4279e279f6a0f37565ece43fe8ec9c59';
const BASELINE_PROJECTION_GZIP = [
  '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',
  'QArYvQYA'
].join('');
const REVIEWED_TITLE_CORRECTIONS = [
  {
    "positionId": "pos:g:751e83079cd6d4ffeaf58a",
    "paperId": "cow",
    "versionId": "publication:cow:a7abf1e326e6",
    "old": "CLIP on Wheels: Zero-Shot Object Navigation as Object Localization and Exploration",
    "new": "CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation"
  },
  {
    "positionId": "pos:g:e45df86dddd9cb1b67463c",
    "paperId": "cow",
    "versionId": "publication:cow:a7abf1e326e6",
    "old": "CLIP on Wheels: Zero-Shot Object Navigation as Object Localization and Exploration",
    "new": "CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation"
  },
  {
    "positionId": "pos:g:18a33fba17e8e92ee1ed5d",
    "paperId": "langmap26",
    "versionId": "arxiv:2602.02220v3",
    "old": "LangMap: A Hierarchical Benchmark for Open-Vocabulary Goal Navigation",
    "new": "LangMap: A Human-Verified Benchmark for Hierarchical Open-Vocabulary Goal Navigation"
  },
  {
    "positionId": "pos:g:31c6cd8857132fbe346c39",
    "paperId": "cow",
    "versionId": "publication:cow:a7abf1e326e6",
    "old": "CLIP on Wheels: Zero-Shot Object Navigation as Object Localization and Exploration",
    "new": "CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation"
  }
];
function reviewedProjection() {
  const bytes = zlib.gunzipSync(Buffer.from(BASELINE_PROJECTION_GZIP, 'base64'));
  assert.equal(crypto.createHash('sha256').update(bytes).digest('hex'), BASELINE_PROJECTION_SHA);
  const expected = JSON.parse(bytes);
  for (const correction of REVIEWED_TITLE_CORRECTIONS) {
    const position = expected.positions[correction.positionId];
    assert.equal(position.paperId, correction.paperId);
    assert.equal(position.versionId, correction.versionId);
    assert.equal(position.label, correction.old);
    position.label = correction.new;
  }
  return expected;
}

const trackedSourceFiles = [
  'assets/navigation-product.js', 'assets/navigation-product-model.js',
  'assets/navigation-product.css', 'assets/navigation-content.js', 'assets/navigation-bootstrap.js',
  'scripts/navigation_product.py', 'scripts/navigation_transport.py',
  'scripts/navigation_research_map.py', 'scripts/navigation_native_trees.py',
  'data/navigation-product/model.json.gz', 'data/navigation-product/manifest.json',
  'tests/test_navigation_parallel_scopes.cjs', 'tests/test_navigation_graphical_overview.cjs',
];
const sourceSnapshot = () => Object.fromEntries(trackedSourceFiles.map(file => [file, crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')]));
const frozenSources = sourceSnapshot();
const generated = fs.mkdtempSync(path.join(os.tmpdir(), 'navigation-graphical-overview-'));
try {
  cp.execFileSync('python3', ['-c', [
    'import sys',
    'from pathlib import Path',
    "sys.path.insert(0, 'scripts')",
    'import navigation_product as p',
    "root=Path('.').resolve(); target=Path(sys.argv[1])",
    'raw,model=p.payloads(root); delivery=p.project(model,p.MODEL_SHA256)',
    "(target/'index.html').write_text(p.render(root,model,delivery),encoding='utf8')",
    "content=target/'content'; content.mkdir()",
    "for name,raw in delivery['files'].items(): (content/name).write_bytes(raw)",
  ].join('\n'), generated], {cwd:root, env:{...process.env, PYTHONDONTWRITEBYTECODE:'1'}, timeout:30000});
} catch (error) {
  fs.rmSync(generated, {recursive:true, force:true});
  throw error;
}
assert.deepEqual(sourceSnapshot(), frozenSources, 'source changed while generating the test fixture');
test.after(() => {
  try { assert.deepEqual(sourceSnapshot(), frozenSources, 'source changed during execution; this is not a frozen-version result'); }
  finally { fs.rmSync(generated, {recursive:true, force:true}); }
});
const html = fs.readFileSync(path.join(generated, 'index.html'), 'utf8');
const clean = value => value === undefined ? undefined : JSON.parse(JSON.stringify(value));
const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
async function frames(w) {
  await new Promise(resolve => w.requestAnimationFrame(() => w.requestAnimationFrame(resolve)));
}
async function page(options = {}) {
  const errors = [], calls = [], external = [], chromeRequests = [];
  // The scientific runtime is inline and must work while optional shared chrome
  // is unavailable. Only these exact same-origin, content-versioned assets are
  // permitted; neither network access nor an arbitrary basename is allowlisted.
  const chromeAssets = ['site.css', 'catalog-navigation.js', 'presentation.js', 'interface.js', 'chrome.js'];
  const allowedChrome = new Set(chromeAssets.map(name => {
    const digest = crypto.createHash('sha256').update(fs.readFileSync(path.join(root, 'assets', name))).digest('hex').slice(0, 16);
    return 'https://example.org/assets/' + name + '?v=' + digest;
  }));
  class NoNetwork extends ResourceLoader {
    fetch(url) {
      if (allowedChrome.has(url)) chromeRequests.push(url);
      else external.push(url);
      return null;
    }
  }
  const vc = new VirtualConsole();
  vc.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(html, {
    url:'https://example.org/research/navigation/' + (options.hash || ''),
    runScripts:'dangerously', resources:new NoNetwork(), pretendToBeVisual:true, virtualConsole:vc,
    beforeParse(w) {
      // This suite exercises the desktop graph; compact workspace behavior is
      // covered by its dedicated viewport tests, not JSDOM's implicit 1024px.
      w.innerWidth = options.width || 1440; w.innerHeight = 900;
      w.TextEncoder = TextEncoder;
      w.TextDecoder = TextDecoder;
      w.scrollTo = (x, y) => Object.defineProperty(w, 'scrollY', {value:y, configurable:true});
      w.__scrollTargets = [];
      w.HTMLElement.prototype.scrollIntoView = function () { w.__scrollTargets.push(this); };
      Object.defineProperty(w.crypto, 'subtle', {value:crypto.webcrypto.subtle});
      if (options.saved) w.history.replaceState(options.saved, '', w.location.href);
      w.fetch = async url => {
        calls.push(String(url));
        const resolved = new URL(String(url), w.location.href);
        assert.equal(resolved.origin, w.location.origin, 'only same-origin fixture packets are permitted');
        const match = resolved.pathname.match(/^\/research\/navigation\/(content\/[a-f0-9]{64}\.json)$/);
        assert.ok(match, 'unexpected resource request: ' + url);
        const bytes = fs.readFileSync(path.join(generated, match[1]));
        if (options.fetch) return options.fetch(String(url), bytes, w);
        return {ok:true, status:200, arrayBuffer:async () => bytes};
      };
    },
  });
  const w = dom.window;
  for (let i = 0; i < 150 && !w.NavigationProductApp; i++) await wait(10);
  assert.ok(w.NavigationProductApp, w.document.querySelector('#np-load-message')?.textContent);
  await frames(w);
  return {w, d:w.document, a:w.NavigationProductApp, M:w.NavigationProductModel, errors, calls, external, chromeRequests, allowedChrome};
}
function descendants(ids) {
  return ids.flatMap(id => [id, ...descendants(science.positions[id].childIds || [])]);
}
function ancestorIds(id) {
  const result = [];
  for (let p = science.positions[id]; p; p = p.parentId && science.positions[p.parentId]) result.unshift(p.id);
  return result;
}
function healthy(x) {
  assert.deepEqual(x.errors, []);
  assert.deepEqual(x.external, []);
  assert.deepEqual(x.chromeRequests.slice().sort(), [...x.allowedChrome].sort(), 'every requested chrome asset is expected and versioned; scientific startup needs none of them');
  assert.equal(x.d.querySelector('#np-navigation-error').hidden, true);
}

function home(x) { return x.d.querySelector('#np-reading-landing'); }
function map(x) {
  const value = x.d.querySelector('#np-overview-map');
  assert.ok(value, 'the default S0 has a real graphical overview');
  return value;
}
function visible(x, target) {
  assert.ok(target, 'required visible control exists');
  for (let p = target; p; p = p.parentElement) {
    assert.notEqual(p.hidden, true, 'no hidden ancestor: ' + p.id);
    const style = x.w.getComputedStyle(p);
    assert.notEqual(style.display, 'none', 'no CSS-hidden ancestor: ' + p.id);
    assert.notEqual(style.visibility, 'hidden', 'no invisible ancestor: ' + p.id);
    if (p.tagName === 'DETAILS' && !p.open) assert.ok(p.querySelector(':scope > summary')?.contains(target), 'only a summary is visible inside a closed disclosure');
  }
}
function positionNode(x, id) {
  return map(x).querySelector('[data-map-position="' + id + '"]');
}
function positionForEntity(x, entityId) {
  const rows = Object.values(x.a.getBundle().researchMap.positions).filter(p => p.entityId === entityId);
  assert.equal(rows.length, 1, 'unambiguous original global position for ' + entityId);
  return rows[0];
}
function graphTask(x, sid) {
  const control = map(x).querySelector('button[data-task-open="' + sid + '"]');
  assert.ok(control, sid + ': graphical task button exists');
  return control;
}
function node(x, id) { return x.d.getElementById('np-node-' + id); }
function forest(x, tree) {
  assert.equal(x.a.getState().route.tree, tree, 'only the active local view may be inspected');
  const sections = [...x.d.querySelectorAll('#np-tree section[data-parallel-tree]')];
  assert.deepEqual(sections.map(section => section.dataset.parallelTree), [tree], 'the inactive forest is absent, not hidden');
  const result = x.d.querySelector('#np-tree section[data-parallel-tree="' + tree + '"]');
  assert.ok(result, 'original active local ' + tree + ' forest is present');
  visible(x, result);
  const items = [...x.d.querySelectorAll('#np-tree [role="treeitem"]')];
  assert.ok(items.every(item => item.dataset.tree === tree), 'one active scientific tree in the canvas');
  assert.equal(items.filter(item => item.tabIndex === 0).length, items.length ? 1 : 0, 'one roving keyboard domain');
  return result;
}
async function switchLocalTree(x, tree) {
  const route = clean(x.a.getState().route);
  assert.ok(['l', 'c'].includes(route.tree), 'local switching cannot silently leave a global view');
  assert.ok(['l', 'c'].includes(tree));
  if (route.tree !== tree) {
    const key = x.M.contextKey(route), bucket = clean(x.M.getBucket(x.a.getState()));
    x.d.querySelector('[data-tree-tab="' + tree + '"]').click();
    await frames(x.w);
    assert.equal(x.a.getState().route.tree, tree);
    assert.equal(x.a.getState().route.scope, route.scope);
    const retained = x.a.getState().contexts[key];
    assert.equal(retained.selectedByTree[route.tree], bucket.selectedByTree[route.tree], 'inactive selection remains in its original context');
    assert.deepEqual(clean(retained.expandedByTree[route.tree]), bucket.expandedByTree[route.tree], 'inactive expansion remains in its original context');
  }
  forest(x, tree);
}
async function assertBothLocalForests(x, sid) {
  const route = clean(x.a.getState().route), other = route.tree === 'l' ? 'c' : 'l';
  assertTrueForest(x, sid, route.tree);
  await switchLocalTree(x, other);
  assertTrueForest(x, sid, other);
  await back(x);
  assert.deepEqual(clean(x.a.getState().route), route, 'view inspection restores the original history entry');
  assertTrueForest(x, sid, route.tree);
}
function revealDetails(target) {
  const chain = [];
  for (let parent = target.parentElement; parent; parent = parent.parentElement) {
    if (parent.tagName === 'DETAILS') chain.unshift(parent);
  }
  for (const details of chain) if (!details.open) details.querySelector(':scope > summary').click();
}
async function back(x) {
  x.w.history.back();
  await wait(30);
  await frames(x.w);
}
async function overview(x) {
  x.d.querySelector('[data-tree-tab="g"]').click();
  await frames(x.w);
  assert.equal(x.a.getState().route.tree, 'g');
  assert.equal(home(x).hidden, false);
}
function assertTrueForest(x, sid, tree) {
  const items = [...forest(x, tree).querySelectorAll('[role="treeitem"]')];
  const ids = items.map(item => item.dataset.position);
  assert.equal(new Set(ids).size, ids.length, 'no repeated original position IDs');
  assert.deepEqual(items.filter(item => !science.positions[item.dataset.position]?.parentId).map(item => item.dataset.position), science.forests[sid][tree]);
  for (const item of items) {
    const p = science.positions[item.dataset.position];
    assert.ok(p, 'only existing local positions may be rendered');
    assert.equal(p.scopeId, sid);
    assert.equal(p.tree, tree);
    assert.equal(item.dataset.parent, p.parentId || '');
    assert.equal(item.dataset.entity, p.entityId);
    assert.equal(item.dataset.association, p.association || '');
    assert.equal(item.parentElement.closest('[role="treeitem"]')?.dataset.position || null, p.parentId);
    assert.ok(item.querySelector(':scope > .np-node-row .np-node-label').textContent.trim());
  }
}
async function clickPosition(x, id) {
  const p = science.positions[id];
  assert.ok(p, 'click target belongs to the frozen scientific inventory');
  await switchLocalTree(x, p.tree);
  for (const parentId of ancestorIds(id).slice(0, -1)) {
    const parent = node(x, parentId);
    assert.ok(parent, 'original ancestor is reachable: ' + parentId);
    revealDetails(parent);
    if (parent.getAttribute('aria-expanded') === 'false') {
      parent.querySelector(':scope > .np-node-row .np-node-toggle').click();
      await frames(x.w);
    }
  }
  const item = node(x, id);
  assert.ok(item, 'original position is reachable: ' + id);
  const button = item.querySelector(':scope > .np-node-row .np-node-label');
  button.focus(); button.click();
  await frames(x.w);
  const route = x.a.getState().route;
  assert.equal(route.node, id);
  assert.equal(route.scope, p.scopeId);
  assert.equal(route.tree, p.tree);
  assert.equal(route.paper, p.paperId || null);
  assert.equal(route.version, p.versionId || null);
}
function originalRelation(id) {
  const row = science.relations[id] || science.relatedRelations.find(row => row.id === id);
  assert.ok(row, 'relation belongs to frozen science: ' + id);
  return row;
}
function assertOriginalLocatorDisplay(x, row, source) {
  const originals = source.detail.locators;
  const paragraphs = [...row.querySelectorAll('p[data-task-relation-locator-index]')];
  assert.equal(paragraphs.length, originals.length, 'one visible paragraph per original locator');
  const fixture88 = require('./fixtures/navigation_relation_locator.json').find(item => item.name === 'relation88');
  originals.forEach((loc, index) => {
    const paragraph = paragraphs[index];
    assert.equal(paragraph.dataset.taskRelationLocatorIndex, String(index), 'original locator order');
    assert.equal(paragraph.dataset.taskRelationLocator, loc.locator, 'exact original locator provenance');
    const expected = loc.locator === fixture88.raw ? fixture88.expected : {text:loc.locator, links:[]};
    assert.equal(paragraph.textContent, expected.text, 'complete visible locator display');
    visible(x, paragraph);
    // Only visible text and flat anchors may carry the copy. Hidden raw-text
    // suffixes cannot substitute for the provenance or visible display checks.
    for (const child of paragraph.childNodes) {
      assert.ok(child.nodeType === 3 || child.nodeType === 1 && child.tagName === 'A', 'only text or source anchors');
      if (child.nodeType === 1) {
        visible(x, child);
        assert.equal(child.children.length, 0, 'no hidden nested link copy');
        assert.notEqual(child.getAttribute('aria-hidden'), 'true');
      }
    }
    assert.deepEqual([...paragraph.querySelectorAll('a')].map(anchor => ({
      text:anchor.textContent, url:anchor.getAttribute('href'),
      target:anchor.getAttribute('target'), rel:anchor.getAttribute('rel')
    })), expected.links, 'original URL, visible label and safe external-link attributes');
    if (loc.version) assert.ok(row.textContent.includes(loc.version), source.id + ': original source version');
  });
}
function relationPath(x, id) {
  const paths = map(x).querySelectorAll('path[data-map-relation="' + id + '"]');
  assert.equal(paths.length, 1, 'one actual graph path per original relation');
  return paths[0];
}
function snapshotGraph(x) {
  const b = x.a.getBundle();
  return clean({positions:b.positions, scopes:b.scopes, forests:b.forests, researchMap:b.researchMap});
}

test('graphical S0 leaves frozen science and the original global projection intact', async t => {
  assert.equal(crypto.createHash('sha256').update(scienceBytes).digest('hex'), SCIENCE_SHA);
  assert.equal(crypto.createHash('sha256').update(projectionImplementationBytes()).digest('hex'), REVIEWED_PROJECTION_SHA, 'the graph uses every independently reviewed projection implementation byte outside native CSS and page chrome');
  assert.equal(science.scopes.length, 64);
  assert.equal(Object.keys(science.positions).length, 1683);
  const x = await page(); t.after(() => x.w.close());
  const b = x.a.getBundle();
  assert.equal(b.delivery.sourceModelSha256, SCIENCE_SHA);
  assert.deepEqual(clean(b.researchMap), reviewedProjection(), 'only the four reviewed title substitutions may differ from the pinned baseline descriptor');
  for (const [id, original] of Object.entries(science.positions)) assert.deepEqual(clean(b.positions[id]), original, id);
  for (const original of science.scopes) {
    for (const tree of ['l', 'c']) assert.deepEqual(clean(b.forests[original.id][tree]), science.forests[original.id][tree]);
    const current = b.scopes.find(s => s.id === original.id);
    for (const key of ['kind', 'parentScopeId', 'childScopeIds', 'crossReferenceTargetId']) assert.deepEqual(clean(current[key]), original[key]);
  }
  assert.equal(Object.keys(b.positions).filter(id => !b.researchMap.positions[id]).length, 1683);
  assert.deepEqual(Object.keys(b.entities).sort(), [...new Set([...Object.keys(science.entities), ...Object.keys(b.researchMap.presentationEntities || {})])].sort(), 'spatial layout cannot invent scientific entities');
  healthy(x);
});

test('fresh S0 is an unselected General goal with two real parallel branches and 39 original graph positions', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), b = x.a.getBundle(), route = x.a.getState().route;
  assert.equal(home(x).hidden, false);
  assert.equal(route.scope, 'scope:all');
  assert.equal(route.tree, 'g');
  assert.equal(route.node, b.researchMap.roots[0]);
  assert.equal(x.d.querySelector('.np-panels').hidden, true);
  visible(x, graph);
  const goal = graph.querySelector('[data-overview-entity="legacy:nav:goal"]');
  assert.ok(goal.textContent.includes('General goal'));
  assert.equal(goal.dataset.mapPosition, b.researchMap.roots[0]);
  visible(x, goal);
  const heads = [...graph.querySelectorAll('[data-reading-branch]')];
  assert.deepEqual(heads.map(n => n.dataset.readingBranch).sort(), ['c', 'l']);
  for (const branch of heads) {
    const p = b.researchMap.positions[branch.dataset.mapPosition];
    assert.ok(p);
    assert.equal(p.entityId, 'legacy:nav:' + branch.dataset.readingBranch);
    assert.equal(p.parentId, goal.dataset.mapPosition);
    visible(x, branch);
  }
  const positions = [...graph.querySelectorAll('[data-map-position]')];
  assert.equal(positions.length, 39, 'root + two branches + original task directory + 22 tasks + 13 CI');
  assert.equal(new Set(positions.map(n => n.dataset.mapPosition)).size, 39);
  for (const n of positions) assert.ok(b.researchMap.positions[n.dataset.mapPosition], 'no new scientific position');
  assert.equal(x.calls.length, 0, 'the complete S0 needs no lazy content fetch');
  healthy(x);
});

test('all 22 default task graph nodes show short contracts above their original task names', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), b = x.a.getBundle();
  const buttons = [...graph.querySelectorAll('button[data-task-open]')];
  assert.equal(buttons.length, 22);
  assert.deepEqual(buttons.map(n => n.dataset.taskOpen).sort(), TASK_INDEX.map(row => row[0]).sort());
  for (const [sid, name, contract] of TASK_INDEX) {
    const control = graphTask(x, sid), title = control.querySelector('.np-task-reading-name'), short = control.querySelector('.np-task-reading-contract');
    assert.equal(control.id, 'np-task-entry-' + sid, 'stable entry focus identity');
    assert.equal(title.textContent.trim(), name);
    assert.equal(short.textContent.trim(), contract);
    assert.ok(short.compareDocumentPosition(title) & x.w.Node.DOCUMENT_POSITION_FOLLOWING, 'short contract is first in accessible DOM reading order');
    assert.ok(control.getAttribute('aria-label').includes(scopeById.get(sid).label));
    assert.equal(control.dataset.mapPosition, b.researchMap.canonicalScopePositionIds[sid]);
    const p = b.researchMap.positions[control.dataset.mapPosition];
    assert.equal(p.sourceScopeId, sid);
    assert.deepEqual(clean(p.sourceRootPositionIds), science.forests[sid].l);
    for (const attr of ['aria-current', 'aria-selected', 'aria-pressed']) assert.notEqual(control.getAttribute(attr), 'true');
    visible(x, control); visible(x, short); visible(x, title);
  }
  healthy(x);
});

test('13 default CI controls are actual original root positions and preserve complete accessible questions', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), ci = positionForEntity(x, 'legacy:nav:c');
  const buttons = [...graph.querySelectorAll('button[data-challenge-open]')];
  assert.equal(buttons.length, 13);
  assert.deepEqual(buttons.map(n => n.dataset.challengeOpen).sort(), clean(ci.childIds).sort());
  assert.deepEqual(buttons.map(n => x.a.getBundle().positions[n.dataset.challengeOpen].entityId).sort(), CI_ENTITIES.slice().sort());
  for (const control of buttons) {
    const p = x.a.getBundle().researchMap.positions[control.dataset.challengeOpen];
    assert.equal(p.parentId, ci.id);
    assert.equal(control.dataset.mapPosition, p.id);
    assert.equal(control.id, 'np-challenge-entry-' + p.id);
    assert.ok(control.title.includes(p.label), p.id + ': unabridged original question remains available');
    assert.ok(control.getAttribute('aria-label')?.includes(p.label));
    assert.ok(control.textContent.trim(), p.id + ': displayed question is not empty');
    visible(x, control);
  }
  healthy(x);
});

test('all 38 parent paths connect existing S0 positions using their exact preexisting g parents', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), positions = x.a.getBundle().researchMap.positions;
  const nodes = [...graph.querySelectorAll('[data-map-position]')].map(n => n.dataset.mapPosition);
  const edges = [...graph.querySelectorAll('path[data-map-parent][data-map-child]')];
  assert.equal(edges.length, 38);
  assert.equal(new Set(edges.map(n => n.dataset.mapChild)).size, 38);
  for (const edge of edges) {
    const child = positions[edge.dataset.mapChild];
    assert.ok(child);
    assert.equal(edge.dataset.mapParent, child.parentId, child.id + ': source g parent cannot be replaced by a spatial group');
    assert.ok(nodes.includes(edge.dataset.mapParent));
    assert.ok(nodes.includes(edge.dataset.mapChild));
    assert.ok(edge.getAttribute('d')?.trim(), 'a parent relation is an SVG path, not only metadata');
    assert.equal(edge.hasAttribute('data-map-relation'), false, 'typed relation and tree parent paths remain separate');
  }
  const expected = nodes.filter(id => positions[id].parentId).sort();
  assert.deepEqual(edges.map(n => n.dataset.mapChild).sort(), expected, 'no shown node is disconnected from its real visible parent');
  for (const note of graph.querySelectorAll('[data-layout-note]')) {
    assert.equal(note.tagName, 'SPAN');
    for (const attr of ['data-map-position', 'data-position', 'data-entity', 'data-overview-entity', 'data-parent', 'data-map-parent', 'data-map-child']) assert.equal(note.hasAttribute(attr), false, 'layout note is not a scientific entity or parent');
    assert.notEqual(note.getAttribute('role'), 'treeitem');
  }
  assert.equal(graph.querySelectorAll('[data-layout-note] [data-map-position]').length, 0);
  healthy(x);
});

test('each of the 22 graphical task controls enters its own active S1 forest and switches between its original views', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [sid] of TASK_INDEX) {
    const control = graphTask(x, sid);
    control.focus(); control.click(); await frames(x.w);
    assert.equal(x.a.getState().route.scope, sid);
    assert.equal(home(x).hidden, true);
    assert.equal(x.d.querySelector('#np-tree').dataset.parallelScope, sid);
    await assertBothLocalForests(x, sid);
    await overview(x);
    assert.equal(x.d.activeElement, graphTask(x, sid), sid + ': return restores visible graph entry focus');
    visible(x, x.d.activeElement);
  }
  healthy(x);
});

test('each of the 13 CI controls opens its exact original g position and Back restores S0 focus', async t => {
  const x = await page(); t.after(() => x.w.close());
  const ids = [...map(x).querySelectorAll('[data-challenge-open]')].map(n => n.dataset.challengeOpen);
  for (const id of ids) {
    const control = map(x).querySelector('[data-challenge-open="' + id + '"]');
    control.focus(); control.click(); await frames(x.w);
    assert.equal(x.a.getState().route.tree, 'g');
    assert.equal(x.a.getState().route.node, id);
    assert.equal(home(x).hidden, true);
    assert.ok(node(x, id), 'the original graph remains the destination for CI');
    await back(x);
    assert.equal(home(x).hidden, false);
    assert.equal(x.d.activeElement, map(x).querySelector('[data-challenge-open="' + id + '"]'));
    visible(x, x.d.activeElement);
  }
  healthy(x);
});

test('seven selectable typed paths keep exact original endpoints/types and cannot acquire tree-parent semantics', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), paths = [...graph.querySelectorAll('path[data-map-relation]')];
  assert.equal(graph.dataset.relationsVisible,'false','old default-all overlay becomes opt-in');
  assert.equal(x.d.getElementById('np-overview-relation-panel').hidden,true);
  for(const path of paths)assert.equal(x.w.getComputedStyle(path).visibility,'hidden');
  x.d.querySelector('#np-map-relations-toggle').click();assert.equal(graph.dataset.relationsVisible,'true');
  assert.deepEqual(paths.map(n => n.dataset.mapRelation).sort(), TASK_RELATIONS.map(row => row[0]).sort());
  for (const [id, from, to, type] of TASK_RELATIONS) {
    const path = relationPath(x, id), source = originalRelation(id);
    assert.equal(source.renderAsTree, false);
    assert.equal(source.from, from); assert.equal(source.to, to); assert.equal(source.relationType, type);
    assert.equal(path.dataset.fromEntity, from);
    assert.equal(path.dataset.toEntity, to);
    assert.equal(path.dataset.relationType, type);
    assert.ok(graphTask(x, from)); assert.ok(graphTask(x, to));
    assert.equal(path.hasAttribute('data-map-parent'), false);
    assert.equal(path.hasAttribute('data-map-child'), false);
    assert.equal(path.hasAttribute('data-parent'), false);
    assert.equal(path.hasAttribute('data-child'), false);
    assert.equal(path.getAttribute('role'), 'button');
    assert.equal(path.getAttribute('tabindex'), '0');
    assert.ok(path.getAttribute('aria-label')?.trim(), 'each edge has an accessible name');
    assert.ok(path.getAttribute('d')?.trim());
    const dash = path.getAttribute('stroke-dasharray') || path.style.strokeDasharray || x.w.getComputedStyle(path).strokeDasharray;
    assert.ok(dash && !/^(none|0(?:px)?(?:[ ,]+0(?:px)?)*)$/.test(dash), 'typed relationships are visually distinguished from parent edges');
    visible(x, path);
  }
  assert.equal(graph.querySelector('[data-map-relation="tasks:relation:87"]'), null);
  healthy(x);
});

test('click and Enter on every typed graph edge expose its exact source while preserving route and scientific structure', async t => {
  const x = await page(); t.after(() => x.w.close());
  const route = clean(x.a.getState().route), original = snapshotGraph(x), hash = x.w.location.hash;
  for (const [id] of TASK_RELATIONS) {
    for (const action of ['click', 'Enter']) {
      const panel = x.d.querySelector('#np-task-relations');
      panel.open = false;
      if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
      const path = relationPath(x, id), source = originalRelation(id);visible(x,path);
      x.w.__scrollTargets.length = 0;
      if (action === 'click') path.dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
      else {
        path.focus();
        path.dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'Enter', bubbles:true, cancelable:true}));
      }
      await frames(x.w);
      assert.equal(panel.open, false, id + ': ' + action + ' dismisses the picker while opening its evidence');
      const row = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
      assert.ok(row);
      assert.ok(row === x.d.activeElement || row.contains(x.d.activeElement) || x.w.__scrollTargets.some(target => target === row || row.contains(target)), id + ': source action locates the exact relation, not only the shared disclosure');
      assertOriginalLocatorDisplay(x, row, source);
      if (id === 'tasks:relation:88' && action === 'click') {
        // Mutations use detached clones: never alter production state or science.
        const corruptions = [
          p => p.dataset.taskRelationLocator = 'wrong original locator',
          p => p.dataset.taskRelationLocatorIndex = '99',
          p => p.querySelector('a').setAttribute('href', 'javascript:alert(1)'),
          p => p.querySelector('a').setAttribute('target', '_self'),
          p => p.querySelector('a').setAttribute('rel', 'opener'),
          p => p.firstChild.textContent = 'missing scientific qualifier',
          p => p.hidden = true,
          p => p.querySelector('a').hidden = true,
          p => p.querySelector('a').remove(),
        ];
        for (const corrupt of corruptions) {
          const clone = row.cloneNode(true);
          assertOriginalLocatorDisplay(x, clone, source);
          corrupt(clone.querySelector('p[data-task-relation-locator-index]'));
          assert.throws(() => assertOriginalLocatorDisplay(x, clone, source), {name:'AssertionError'});
        }
      }
      assert.equal(row.dataset.fromEntity, source.from);
      assert.equal(row.dataset.toEntity, source.to);
      assert.equal(row.dataset.relationType, source.relationType);
      assert.equal(row.querySelectorAll('button').length, 2, 'both exact scope endpoints remain actionable');
      assert.deepEqual(clean(x.a.getState().route), route, 'reading relation evidence is not scientific navigation');
      assert.equal(x.w.location.hash, hash);
    }
  }
  assert.deepEqual(snapshotGraph(x), original, 'examining non-tree relations does not mutate any scientific or projection identity');
  healthy(x);
});

test('every source relation endpoint still enters its original S1 scope and Back retains endpoint focus', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [id, from, to] of TASK_RELATIONS) {
    for (const [index, sid] of [from, to].entries()) {
      if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
      relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
      const row = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
      const control = row.querySelectorAll('button')[index];
      assert.ok(control.textContent.includes(scopeById.get(sid).label));
      control.focus(); control.click(); await frames(x.w);
      assert.equal(x.a.getState().route.scope, sid);
      await assertBothLocalForests(x, sid);
      await back(x);
      assert.equal(x.d.querySelector('#np-task-relations').open, false);
      assert.equal(x.d.activeElement.id, 'np-relation-entry-' + id + '-' + sid);
    }
  }
  healthy(x);
});

test('auxiliary comparison, all 64 source scopes and reading notes remain available outside the default graph', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const id of ['np-overview-comparison', 'np-all-scopes', 'np-task-relations', 'np-overview-notes']) {
    const disclosure = x.d.getElementById(id);
    assert.ok(disclosure);
    assert.equal(disclosure.tagName, 'DETAILS');
    assert.equal(disclosure.open, false, id + ': supporting prose does not dominate the initial graph');
    assert.equal(map(x).contains(disclosure), false);
  }
  const scopes = [...x.d.querySelectorAll('#np-all-scopes [data-scope-open]')];
  assert.equal(scopes.length, 64);
  assert.deepEqual(scopes.map(n => n.dataset.scopeOpen).sort(), science.scopes.map(s => s.id).sort());
  for (const control of scopes) {
    const s = scopeById.get(control.dataset.scopeOpen), row = control.closest('[data-directory-scope]');
    assert.ok(control.textContent.includes(s.label));
    assert.ok(control.textContent.includes(s.displayRole || s.kind));
    assert.equal(row.dataset.parentScope, s.parentScopeId || '');
    assert.equal(row.parentElement.closest('[data-directory-scope]')?.dataset.directoryScope || null, s.parentScopeId);
  }
  const comparison = x.d.querySelector('#np-overview-comparison');
  assert.deepEqual([...comparison.querySelectorAll('[data-task-comparison]')].map(row => row.dataset.taskComparison).sort(), TASK_INDEX.map(row => row[0]).sort());
  for (const source of science.scopes) {
    const control = x.d.querySelector('#np-all-scopes [data-scope-open="' + source.id + '"]');
    revealDetails(control); control.focus(); control.click(); await frames(x.w);
    assert.equal(x.a.getState().route.scope, source.id);
    await assertBothLocalForests(x, source.id);
    await back(x);
    assert.equal(x.d.activeElement.id, 'np-scope-entry-' + source.id);
    assert.equal(x.d.querySelector('#np-all-scopes').open, true);
  }
  healthy(x);
});

test('S0 task and subordinate-scope history restore visible entry focus and independent overview scrolling', async t => {
  const x = await page(); t.after(() => x.w.close());
  home(x).scrollTop = 193;
  const task = graphTask(x, 'task:roomnav');
  task.focus(); task.click(); await frames(x.w);
  await back(x);
  assert.equal(home(x).scrollTop, 193);
  assert.equal(x.d.activeElement, graphTask(x, 'task:roomnav'));
  const scope = x.d.querySelector('#np-all-scopes [data-scope-open="task:coin"]');
  revealDetails(scope); home(x).scrollTop = 247; scope.focus(); scope.click(); await frames(x.w);
  await back(x);
  assert.equal(home(x).scrollTop, 247);
  assert.equal(x.d.activeElement.id, 'np-scope-entry-task:coin');
  visible(x, x.d.activeElement);
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const restored = await page({saved:clean(x.w.history.state), hash:x.M.encodeRoute(x.a.getState().route)}); t.after(() => restored.w.close());
  assert.equal(home(restored).hidden, false);
  assert.equal(home(restored).scrollTop, 247);
  assert.equal(restored.d.querySelector('#np-all-scopes').open, true);
  assert.equal(restored.d.activeElement.id, 'np-scope-entry-task:coin');
  visible(restored, restored.d.activeElement);
  healthy(x); healthy(restored);
});

test('local AudioGoal S1 preserves scientific selection, zoom, both scrolling regions and focus across Back/Forward', async t => {
  const x = await page(); t.after(() => x.w.close());
  graphTask(x, 'task:audiogoal').click(); await frames(x.w);
  const challenge = 'pos:c:726ec5b1b3b78e1ec9e797', insight = 'pos:c:6dcc2ce43c02d908266f20';
  await clickPosition(x, challenge); await clickPosition(x, insight);
  const reader = x.d.querySelector('#np-detail-scroll'), canvas = x.d.querySelector('#np-tree-scroll');
  assert.notEqual(reader, canvas);
  x.d.querySelector('#np-zoom-in').click();
  reader.scrollTop = 173; canvas.scrollTop = 61; canvas.scrollLeft = 27; node(x, insight).focus();
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.M.getBucket(x.a.getState()));
  x.d.querySelector('[data-path-kind="local-ancestry"] [data-context-position="' + challenge + '"]').click(); await frames(x.w);
  await back(x);
  const route = x.a.getState().route;
  assert.equal(route.node, insight); assert.equal(route.paper, 'sound20'); assert.equal(route.version, 'arxiv:1912.11474v3');
  assert.equal(reader.scrollTop, 173); assert.equal(canvas.scrollTop, 61); assert.equal(canvas.scrollLeft, 27);
  assert.equal(x.M.getBucket(x.a.getState()).graphScale, 1.1);
  for (const tree of ['l', 'c']) assert.deepEqual(clean(x.M.getBucket(x.a.getState()).expandedByTree[tree]), saved.expandedByTree[tree]);
  assert.equal(x.d.activeElement, node(x, insight));
  x.w.history.forward(); await wait(30); await frames(x.w);
  assert.equal(x.a.getState().route.node, challenge);
  await back(x); await overview(x); await back(x);
  assert.equal(x.a.getState().route.node, insight);
  assert.equal(x.d.activeElement, node(x, insight));
  assert.equal(reader.scrollTop, 173); assert.equal(canvas.scrollTop, 61); assert.equal(canvas.scrollLeft, 27);
  healthy(x);
});

test('the explicit old graph and cold original g links remain available without overwriting fresh S0 history', async t => {
  const x = await page(); t.after(() => x.w.close());
  const route = clean(x.a.getState().route), hash = x.M.encodeRoute(route), freshSaved = clean(x.w.history.state);
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  assert.equal(home(x).hidden, true);
  assert.equal(x.d.querySelector('.np-panels').hidden, false);
  assert.deepEqual(clean(x.a.getState().route), route);
  assert.ok(x.d.querySelectorAll('#np-tree [role="treeitem"]').length >= 39);
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  assert.equal(home(x).hidden, false);
  const cold = await page({hash}); t.after(() => cold.w.close());
  assert.equal(home(cold).hidden, true);
  assert.equal(cold.d.querySelector('.np-panels').hidden, false);
  assert.deepEqual(clean(cold.a.getState().route), route);
  const reload = await page({hash, saved:freshSaved}); t.after(() => reload.w.close());
  assert.equal(home(reload).hidden, false);
  assert.deepEqual(clean(reload.a.getState().route), route);
  const legacySaved = clean(freshSaved);
  for (const bucket of Object.values(legacySaved[x.M.KEY].contexts)) { delete bucket.originalMapOpen; delete bucket.overviewView; }
  legacySaved.unrelatedOwnerField = 'original-owner';
  const legacy = await page({hash, saved:legacySaved}); t.after(() => legacy.w.close());
  assert.equal(home(legacy).hidden, true);
  assert.equal(legacy.w.history.state.unrelatedOwnerField, 'original-owner');
  healthy(x); healthy(cold); healthy(reload); healthy(legacy);
});

const publishedHistory = require('./fixtures/navigation-pr53-history.json');
for (const [name, fixture] of Object.entries(publishedHistory.states)) {
  test('graphical S0 retains the exact published ' + name + ' deep-link and historical reading position', async t => {
    // Published document-scroll histories were captured below the 1200px
    // fixed desktop workspace breakpoint; preserve that original viewport.
    const x = await page({hash:fixture.urlHash, saved:fixture.history, width:1024}); t.after(() => x.w.close());
    assert.deepEqual(clean(x.a.getState().route), fixture.history[x.M.KEY].route);
    assert.equal(x.d.querySelector('#np-tree-scroll').scrollTop, 123);
    assert.equal(x.d.querySelector('#np-detail-scroll').scrollTop, 570);
    assert.equal(x.w.scrollY, 1750);
    assert.equal(x.w.history.state.unrelatedOwnerField, 'preserve-me');
    if (['l', 'c'].includes(x.a.getState().route.tree)) await assertBothLocalForests(x, x.a.getState().route.scope);
    healthy(x);
  });
}

test('relation visibility and notes disclosure survive a task round-trip and saved-history reload', async t => {
  const x = await page(); t.after(() => x.w.close());
  const initial = clean(x.a.getState().route);
  assert.equal(map(x).dataset.relationsVisible, 'false');
  assert.equal(x.d.querySelector('#np-map-relations-toggle').getAttribute('aria-pressed'), 'false');
  x.d.querySelector('#np-map-relations-toggle').click();
  assert.equal(map(x).dataset.relationsVisible, 'true','explicit all-lines control still works');
  x.d.querySelector('#np-map-relations-toggle').click();
  assert.equal(map(x).dataset.relationsVisible, 'false');
  assert.equal(x.d.querySelector('#np-map-relations-toggle').getAttribute('aria-pressed'), 'false');
  assert.deepEqual(clean(x.a.getState().route), initial, 'toggling an overlay does not navigate');
  assert.equal(map(x).querySelectorAll('[data-map-relation]').length, 7, 'all relation identities remain available when the overlay is hidden');
  for (const path of map(x).querySelectorAll('[data-map-relation]')) assert.equal(x.w.getComputedStyle(path).visibility, 'hidden');
  visible(x, x.d.querySelector('#np-task-relations > summary'));
  x.d.querySelector('#np-overview-notes > summary').click();
  assert.equal(x.d.querySelector('#np-overview-notes').open, true);
  const entry = graphTask(x, 'task:pointnav');
  entry.focus(); entry.click(); await frames(x.w);
  await back(x);
  assert.equal(map(x).dataset.relationsVisible, 'false');
  assert.equal(x.d.querySelector('#np-map-relations-toggle').getAttribute('aria-pressed'), 'false');
  assert.equal(x.d.querySelector('#np-overview-notes').open, true);
  assert.equal(x.d.activeElement, graphTask(x, 'task:pointnav'));
  const state = x.M.getBucket(x.a.getState()).overviewView;
  assert.equal(state.linesVisible, false); assert.equal(state.notesOpen, true);
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.w.history.state), hash = x.M.encodeRoute(x.a.getState().route);
  const reload = await page({saved, hash}); t.after(() => reload.w.close());
  assert.equal(map(reload).dataset.relationsVisible, 'false');
  assert.equal(reload.d.querySelector('#np-map-relations-toggle').getAttribute('aria-pressed'), 'false');
  assert.equal(reload.d.querySelector('#np-overview-notes').open, true);
  assert.equal(reload.d.activeElement, graphTask(reload, 'task:pointnav'));
  reload.d.querySelector('#np-map-relations-toggle').click();
  reload.d.querySelector('#np-overview-notes > summary').click();
  reload.w.dispatchEvent(new reload.w.Event('pagehide'));
  assert.equal(reload.M.getBucket(reload.a.getState()).overviewView.linesVisible, true);
  assert.equal(reload.M.getBucket(reload.a.getState()).overviewView.notesOpen, false);
  const old = clean(saved);
  for (const bucket of Object.values(old[x.M.KEY].contexts)) {
    if (bucket.overviewView) { delete bucket.overviewView.notesOpen; delete bucket.overviewView.linesVisible; }
  }
  const backwards = await page({saved:old, hash}); t.after(() => backwards.w.close());
  assert.equal(map(backwards).dataset.relationsVisible, 'false', 'old S0 snapshots without a preference get the new single-selection default');
  assert.equal(backwards.d.querySelector('#np-overview-notes').open, false, 'old S0 snapshots get default closed notes');
  healthy(x); healthy(reload); healthy(backwards);
});

test('new notes and relation visibility history fields accept only booleans while older snapshots stay valid', async t => {
  const x = await page(); t.after(() => x.w.close());
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const baseline = clean(x.a.getState()), b = x.a.getBundle();
  for (const field of ['notesOpen', 'linesVisible']) {
    for (const value of [true, false]) {
      const current = clean(baseline);
      x.M.getBucket(current).overviewView[field] = value;
      assert.doesNotThrow(() => x.M.validateState(b, current), field + ' permits ' + value);
    }
    for (const value of [null, 'true', 'false', 0, 1, [], {}]) {
      const invalid = clean(baseline);
      x.M.getBucket(invalid).overviewView[field] = value;
      assert.throws(() => x.M.validateState(b, invalid), /概览显示状态无效/, field + ' rejects ' + JSON.stringify(value));
    }
    const old = clean(baseline);
    delete x.M.getBucket(old).overviewView[field];
    assert.doesNotThrow(() => x.M.validateState(b, old), 'absence remains backwards-compatible');
  }
  healthy(x);
});

// This parses intended SVG coordinates, not a browser layout or pixel screenshot.
// It proves the connector endpoints refer to the advertised boxes in the layout
// model. It cannot prove line-label separation, actual font metrics or readability.
function endpointCoordinates(pathNode) {
  const tokens = pathNode.getAttribute('d').match(/[a-zA-Z]|[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/g) || [];
  const counts = {M:2, L:2, H:1, V:1, C:6, S:4, Q:4, T:2, A:7};
  let cursor = [0, 0], first;
  while (tokens.length) {
    const command = tokens.shift(), kind = command.toUpperCase(), n = counts[kind];
    if (kind === 'Z') { cursor = first.slice(); continue; }
    assert.ok(n, 'supported SVG endpoint command: ' + command);
    const args = tokens.splice(0, n).map(Number);
    assert.equal(args.length, n);
    assert.ok(args.every(Number.isFinite));
    const relative = command !== kind;
    if (kind === 'H') cursor = [args[0] + (relative ? cursor[0] : 0), cursor[1]];
    else if (kind === 'V') cursor = [cursor[0], args[0] + (relative ? cursor[1] : 0)];
    else cursor = [args[n - 2] + (relative ? cursor[0] : 0), args[n - 1] + (relative ? cursor[1] : 0)];
    if (!first) { assert.equal(kind, 'M'); first = cursor.slice(); }
  }
  return {from:first, to:cursor};
}
function intendedBox(node) {
  const box = {x:parseFloat(node.style.left), y:parseFloat(node.style.top), w:parseFloat(node.style.width), h:Math.max(node.offsetHeight, parseFloat(node.style.minHeight))};
  assert.ok(Object.values(box).every(Number.isFinite), 'graph node has finite intended box coordinates');
  return box;
}
function onBoundary(point, box) {
  const [x, y] = point, epsilon = 0.01;
  return x >= box.x - epsilon && x <= box.x + box.w + epsilon && y >= box.y - epsilon && y <= box.y + box.h + epsilon &&
    (Math.abs(x - box.x) < epsilon || Math.abs(x - box.x - box.w) < epsilon || Math.abs(y - box.y) < epsilon || Math.abs(y - box.y - box.h) < epsilon);
}
test('SVG parent and typed paths terminate on their advertised original node boxes in the intended coordinate model', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const path of map(x).querySelectorAll('path[data-map-parent][data-map-child]')) {
    const points = endpointCoordinates(path);
    assert.ok(onBoundary(points.from, intendedBox(positionNode(x, path.dataset.mapParent))), 'parent path starts at its actual parent');
    assert.ok(onBoundary(points.to, intendedBox(positionNode(x, path.dataset.mapChild))), 'parent path ends at its actual child');
  }
  for (const [id, from, to] of TASK_RELATIONS) {
    const points = endpointCoordinates(relationPath(x, id));
    assert.ok(onBoundary(points.from, intendedBox(graphTask(x, from))), id + ': starts at the original from entity');
    assert.ok(onBoundary(points.to, intendedBox(graphTask(x, to))), id + ': ends at the original to entity');
  }
  healthy(x);
});

test('typed relation source links are real original URLs without adjoining Chinese prose', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [id] of TASK_RELATIONS) {
    const row = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
    const locators = originalRelation(id).detail.locators;
    const expected = [...new Set(locators.flatMap(loc => (String(loc.locator).match(/https:\/\/[^\s)；，、<>]+/g) || []).map(url => url.replace(/[.;。；，]+$/, ''))))];
    const allowed = new Set(expected.concat(relationSourceIds(id).map(sourceId => {
      const source = science.sources[sourceId];
      assert.ok(source, id + ': source ID must exist in the frozen inventory');
      return source.url || source.sourceURL;
    })));
    const hrefs = [...row.querySelectorAll('a[href]')].map(a => a.href);
    for (const url of expected) assert.ok(hrefs.includes(url), id + ': original embedded URL remains available: ' + url);
    for (const href of hrefs) assert.ok(allowed.has(href), id + ': each URL is either original locator text or an exact original source ID target, never adjacent prose');
  }
  healthy(x);
});

test('resizing the overview preserves the focused typed-relation identity and current scientific route', async t => {
  const x = await page(); t.after(() => x.w.close());
  const id = 'tasks:relation:90', path = relationPath(x, id), route = clean(x.a.getState().route);
  x.d.querySelector('#np-map-relations-toggle').click();visible(x,path);
  path.focus();
  assert.equal(x.d.activeElement, path);
  x.w.innerWidth = 1440;
  x.w.dispatchEvent(new x.w.Event('resize'));
  await frames(x.w);
  assert.equal(x.d.activeElement, relationPath(x, id));
  assert.deepEqual(clean(x.a.getState().route), route);
  x.d.activeElement.dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'Enter', bubbles:true, cancelable:true}));
  await frames(x.w);
  assert.equal(x.d.querySelector('#np-task-relations').open, false);
  assert.equal(x.d.activeElement.dataset.taskRelation, id);
  healthy(x);
});

// Independently reviewed display wording. These are presentation strings only;
// complete original questions, scopes and evidence must remain unchanged.
const CI_DISPLAY_LABELS = [
  ['legacy:ci_search_unknown_target', '未见目标，怎样少走冤路？'],
  ['legacy:ci_generalize_environments', '路线更多，新屋仍难适应？'],
  ['legacy:ci_instruction_progress', '指令哪段真正完成？'],
  ['legacy:ci_recover_route_error', '走错后如何少代价纠正？'],
  ['legacy:ci_candidate_verification', '看见候选，为何不能停？'],
  ['legacy:ci_semantic_commitment', '语义有分歧，单标签丢什么？'],
  ['legacy:ci_dynamic_revisit', '旧地图哪部分仍可信？'],
  ['legacy:ci_negative_evidence', '未找到，何时算可信反证？'],
  ['legacy:ci_long_horizon_evidence', '跨调用如何保留证据与待办？'],
  ['methods:ci_ground_dynamic_plan', '未知布局为何难预先完整规划？'],
  ['methods:ci_hierarchical_spatial_query', '扁平检索为何丢失楼层房间？'],
  ['methods:ci_spatial_language_grounding', '仅图文匹配，怎样找两地标之间？'],
  ['methods:ci_compact_relational_memory', '逐点语义冗余且缺少对象关系'],
];
async function entityReady(x, entityId) {
  for (let i = 0; i < 150 && !x.a.getContent().ready(entityId); i++) await wait(10);
  assert.ok(x.a.getContent().ready(entityId), entityId + ': exact source packet finished');
  await frames(x.w);
}
function relationSourceIds(id) {
  const detail = originalRelation(id).detail;
  return [...new Set([...(detail.sourceIds || []), ...(detail.locators || []).flatMap(loc => loc.sourceIds || [])])];
}

test('review: all 13 reviewed CI short questions retain their exact original full questions, entities and evidence packets', async t => {
  const x = await page(); t.after(() => x.w.close());
  assert.deepEqual(CI_DISPLAY_LABELS.map(row => row[0]).sort(), CI_ENTITIES.slice().sort());
  for (const [entityId, display] of CI_DISPLAY_LABELS) {
    const position = positionForEntity(x, entityId), original = science.entities[entityId];
    const control = map(x).querySelector('[data-challenge-open="' + position.id + '"]');
    assert.equal(control.querySelector('.np-map-challenge-label').textContent, display, entityId + ': reviewed question keeps its specific scientific constraint');
    assert.equal(control.title, original.label, entityId + ': the full source question is not rewritten');
    assert.equal(control.getAttribute('aria-label'), original.label + '；展开原问题与来源');
    assert.equal(position.label, original.label);
    assert.equal(control.dataset.mapPosition, position.id);
    control.focus(); control.click(); await frames(x.w);
    assert.equal(x.a.getState().route.node, position.id);
    assert.equal(x.a.getState().route.tree, 'g');
    await entityReady(x, entityId);
    assert.deepEqual(clean(x.a.getBundle().entities[entityId]), original, entityId + ': sourceRefs, detail, claim IDs and source label are unchanged');
    for (const claimId of original.claimIds || []) assert.deepEqual(clean(x.a.getBundle().claims[claimId]), science.claims[claimId], entityId + ': original claim ' + claimId);
    await back(x);
    assert.equal(x.d.activeElement, map(x).querySelector('[data-challenge-open="' + position.id + '"]'));
  }
  healthy(x);
});

test('review: CI layout responds to injected measured heights without overlapping following rows or detaching real parent endpoints', async t => {
  const x = await page(); t.after(() => x.w.close());
  const ci = positionForEntity(x, 'legacy:nav:c'), ids = clean(ci.childIds), target = positionNode(x, ids[5]);
  const route = clean(x.a.getState().route), scientific = snapshotGraph(x);
  let measuredHeight = 68;
  // JSDOM supplies no layout measurements. This controlled offsetHeight input
  // exercises the layout algorithm only; it is not evidence of font wrapping,
  // a real two-line rendering, mouse hit areas or 1440-pixel visual acceptance.
  Object.defineProperty(target, 'offsetHeight', {configurable:true, get:() => measuredHeight});
  for (const height of [68, 52]) {
    measuredHeight = height;
    x.w.innerWidth = 1440;
    x.w.dispatchEvent(new x.w.Event('resize'));
    await frames(x.w);
    const boxes = ids.map(id => intendedBox(positionNode(x, id)));
    assert.equal(boxes[5].h, height, 'the supplied current measurement is consumed');
    for (let index = 1; index < boxes.length; index++) {
      assert.ok(boxes[index].y >= boxes[index - 1].y + boxes[index - 1].h + 5 - 0.01, 'CI row ' + index + ' follows the measured previous bottom with at least a 5px intended gap');
    }
    for (const id of ids) {
      const path = map(x).querySelector('path[data-map-parent="' + ci.id + '"][data-map-child="' + id + '"]');
      assert.ok(path, id + ': original global parent remains unchanged');
      const points = endpointCoordinates(path);
      assert.ok(onBoundary(points.from, intendedBox(positionNode(x, ci.id))), id + ': starts at the real CI root');
      assert.ok(onBoundary(points.to, intendedBox(positionNode(x, id))), id + ': follows the current measured child boundary');
    }
    assert.deepEqual(clean(x.a.getState().route), route);
    assert.deepEqual(snapshotGraph(x), scientific);
  }
  healthy(x);
});

test('review: a clicked relation source article restores exact focus and open evidence after saved-history reload', async t => {
  const x = await page(); t.after(() => x.w.close());
  const id = 'tasks:relation:90';
  if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
  relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
  await frames(x.w);
  const row = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
  assert.equal(x.d.activeElement, row);
  assert.equal(row.getAttribute('tabindex'), '-1');
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.w.history.state), hash = x.M.encodeRoute(x.a.getState().route);
  const reload = await page({saved, hash}); t.after(() => reload.w.close());
  const restored = reload.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
  assert.equal(reload.d.querySelector('#np-task-relations').open, false);
  assert.equal(restored.getAttribute('tabindex'), '-1', 'the article is focusable on its initial reconstruction, before any new relation click');
  assert.equal(reload.d.activeElement, restored, 'focus cannot fall back to BODY or a hidden original-map node');
  assert.equal(restored.id, row.id);
  visible(reload, restored);
  healthy(x); healthy(reload);
});

function axisAlignedSegments(pathNode) {
  const tokens = pathNode.getAttribute('d').match(/[a-zA-Z]|[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/g) || [];
  const result = [];
  let current = [0, 0];
  while (tokens.length) {
    const command = tokens.shift(), from = current.slice();
    if (command === 'M' || command === 'L') current = [Number(tokens.shift()), Number(tokens.shift())];
    else if (command === 'H') current = [Number(tokens.shift()), current[1]];
    else if (command === 'V') current = [current[0], Number(tokens.shift())];
    else assert.fail('typed path geometry requires an explicit segment checker for command ' + command);
    assert.ok(current.every(Number.isFinite));
    if (command === 'M') continue;
    const [x1, y1] = from, [x2, y2] = current;
    if (Math.abs(x1 - x2) < 0.01 && Math.abs(y1 - y2) > 0.01) result.push({axis:'v', fixed:x1, start:Math.min(y1, y2), end:Math.max(y1, y2)});
    else if (Math.abs(y1 - y2) < 0.01 && Math.abs(x1 - x2) > 0.01) result.push({axis:'h', fixed:y1, start:Math.min(x1, x2), end:Math.max(x1, x2)});
    else assert.ok(Math.abs(x1 - x2) < 0.01 && Math.abs(y1 - y2) < 0.01, 'typed graph paths use auditable axis-aligned segments');
  }
  return result;
}
test('review: different typed relations do not share a positive-length axis-aligned SVG segment', async t => {
  const x = await page(); t.after(() => x.w.close());
  // Segment identity is an intended-geometry check. Stroke widths, painted
  // intersections, occlusion and actual pointer hit testing still need a browser.
  const paths = TASK_RELATIONS.map(([id]) => ({id, segments:axisAlignedSegments(relationPath(x, id))}));
  for (let i = 0; i < paths.length; i++) {
    assert.ok(paths[i].segments.length, paths[i].id + ': actual connector segments are present');
    for (let j = i + 1; j < paths.length; j++) {
      for (const a of paths[i].segments) for (const b of paths[j].segments) {
        const sameAxis = a.axis === b.axis && Math.abs(a.fixed - b.fixed) < 0.01;
        const overlap = Math.min(a.end, b.end) - Math.max(a.start, b.start);
        assert.ok(!sameAxis || overlap <= 0.01, paths[i].id + ' and ' + paths[j].id + ' must not share a positive-length ' + a.axis + ' segment');
      }
    }
  }
  for (const [id, from, to] of TASK_RELATIONS) {
    const points = endpointCoordinates(relationPath(x, id));
    assert.ok(onBoundary(points.from, intendedBox(graphTask(x, from))), id + ': separate port still starts at its original entity');
    assert.ok(onBoundary(points.to, intendedBox(graphTask(x, to))), id + ': separate port still ends at its original entity');
  }
  healthy(x);
});

test('review: all nine legacy root challenges expose original conditions, tasks and failure limits directly after the reader heading', async t => {
  const x = await page(); t.after(() => x.w.close());
  const legacy = CI_ENTITIES.filter(id => id.startsWith('legacy:'));
  assert.equal(legacy.length, 9);
  for (const entityId of legacy) {
    const position = positionForEntity(x, entityId), original = science.entities[entityId].detail;
    map(x).querySelector('[data-challenge-open="' + position.id + '"]').click(); await frames(x.w);
    await entityReady(x, entityId);
    const section = x.d.querySelector('#np-reader-summary [data-reading-node="' + position.id + '"]');
    assert.ok(section, entityId + ': challenge has a real reader section');
    const heading = section.querySelector('h3'), scope = section.querySelector('[data-challenge-scope]');
    assert.ok(scope, entityId + ': source scope is shown in the actual reader');
    assert.equal(scope.closest('details'), null, 'applicability cannot be hidden behind evidence disclosures');
    assert.ok(heading.compareDocumentPosition(scope) & x.w.Node.DOCUMENT_POSITION_FOLLOWING, 'scope follows the original question heading');
    const expected = [original.condition_scope.condition, ...original.condition_scope.tasks, original.condition_scope.remaining_limit, original.scope_and_failure_boundary];
    for (const text of expected) { assert.ok(text); assert.ok(scope.textContent.includes(text), entityId + ': original scope/limit ' + text); }
    visible(x, scope);
    assert.equal(x.a.getState().route.node, position.id);
    assert.equal(x.a.getBundle().positions[position.id].entityId, entityId);
    await back(x);
  }
  healthy(x);
});

test('review: every typed relation exposes all original source IDs with exact inventory URLs, versions and status', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [id] of TASK_RELATIONS) {
    if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
    relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true})); await frames(x.w);
    const row = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
    const expected = relationSourceIds(id), anchors = [...row.querySelectorAll('[data-task-relation-source]')];
    assert.ok(expected.length > 0, id + ': an original source inventory exists');
    assert.ok(anchors.length > 0, id + ': source links cannot all be omitted');
    assert.deepEqual(anchors.map(a => a.dataset.taskRelationSource).sort(), expected.slice().sort(), id + ': every unique original source ID is covered exactly once');
    for (const anchor of anchors) {
      const sourceId = anchor.dataset.taskRelationSource, original = science.sources[sourceId];
      assert.ok(original, sourceId + ': source comes from the frozen inventory');
      assert.equal(anchor.tagName, 'A');
      assert.equal(anchor.href, original.url || original.sourceURL);
      assert.equal(anchor.dataset.sourceVersion, original.versionId);
      assert.equal(anchor.dataset.sourceStatus, original.versionStatus);
      assert.ok(anchor.textContent.trim(), sourceId + ': usable source link name');
      visible(x, anchor);
    }
  }
  healthy(x);
});


const RELATION_DISPLAY_LABELS = {
  'tasks:relation:88': '同环境 tour 内多条指令，段间接驳依协议',
  'tasks:relation:89': '类别目标按序组合',
  'tasks:relation:90': '提供类别目标',
  'tasks:relation:91': '提供实例图片目标',
  'tasks:relation:92': '提供语言描述目标',
  'tasks:relation:93': '语言目标按序接续',
  'tasks:relation:94': '成功对象不同：地点与物体实例',
};
const RELATION_TYPE_LABELS = {
  sequential_composition: '按序组合',
  composed_goal_type_in: '组合中的目标类型',
  different_success_semantics: '成功判据不同',
};
test('review: all seven relations have independent native text buttons with exact selection and saved focus while lines are hidden', async t => {
  const x = await page(); t.after(() => x.w.close());
  const route = clean(x.a.getState().route), scientific = snapshotGraph(x);
  assert.equal(map(x).dataset.relationsVisible, 'false');
  x.d.querySelector('#np-task-relations > summary').click();
  const selectors = x.d.querySelector('#np-task-relations nav.np-relation-selectors');
  assert.ok(selectors, 'precise relationship selection has its own native text controls');
  const controls = [...selectors.querySelectorAll('[data-relation-select]')];
  assert.deepEqual(controls.map(n => n.dataset.relationSelect).sort(), TASK_RELATIONS.map(row => row[0]).sort());
  for (const [id, , , type] of TASK_RELATIONS) {
    const control = selectors.querySelector('[data-relation-select="' + id + '"]');
    assert.equal(control.id, 'np-relation-select-' + id);
    assert.equal(control.tagName, 'BUTTON');
    assert.equal(control.getAttribute('type'), 'button');
    assert.equal(control.disabled, false);
    assert.equal(control.tabIndex, 0);
    assert.equal(control.dataset.relationType, type);
    assert.equal(control.getAttribute('aria-controls'), x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]').id, id + ': accessible control target is the exact article');
    assert.ok(control.textContent.includes(RELATION_DISPLAY_LABELS[id]), id + ': exact relation wording');
    assert.ok(control.textContent.includes(RELATION_TYPE_LABELS[type]), id + ': literal relation type');
    assert.equal(control.closest('[data-task-relation]'), null, 'selection controls do not replace or masquerade as the two scope endpoints');
    if(!x.d.querySelector('#np-task-relations').open)x.d.querySelector('#np-task-relations > summary').click();
    visible(x, control);
    control.focus();
    assert.equal(x.d.activeElement, control, 'the native control is independently focusable');
    // JSDOM does not implement native Enter/Space-to-click activation. This
    // exercises the real click callback without inventing a production keydown
    // handler or claiming real-browser keyboard, pointer hit or pixel acceptance.
    control.click(); await frames(x.w);
    const article = x.d.querySelector('#np-overview-relation-panel [data-task-relation="' + id + '"]');
    assert.equal(x.d.activeElement, article, id + ': exact source article receives focus');
    assert.equal(map(x).dataset.selectedRelation,id);assert.equal(map(x).dataset.relationsVisible,'false','choosing one relationship never enables all-lines');
    const evidencePanel=x.d.getElementById('np-overview-relation-panel');assert.equal(evidencePanel.parentElement,map(x));assert.equal(evidencePanel.hidden,false);
    assert.deepEqual([...evidencePanel.querySelectorAll('[data-task-relation]:not([hidden])')].map(row=>row.dataset.taskRelation),[id]);
    for(const [other] of TASK_RELATIONS){const path=relationPath(x,other);assert.equal(x.w.getComputedStyle(path).visibility,other===id?'visible':'hidden',other+': only selected scientific relation is visible');assert.equal(path.getAttribute('tabindex'),other===id?'0':'-1');}
    assert.equal(x.d.querySelector('#np-task-relations').open, false);
    assert.deepEqual(clean(x.a.getState().route), route);
  }
  assert.deepEqual(snapshotGraph(x), scientific);
  const focusedId = 'np-relation-select-tasks:relation:90';
  x.d.querySelector('#np-task-relations > summary').click();
  x.d.getElementById(focusedId).focus();
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const reload = await page({saved:clean(x.w.history.state), hash:x.M.encodeRoute(x.a.getState().route)}); t.after(() => reload.w.close());
  assert.equal(map(reload).dataset.relationsVisible, 'false');
  assert.equal(reload.d.querySelector('#np-task-relations').open, true);
  assert.equal(reload.d.activeElement, reload.d.getElementById(focusedId));
  visible(reload, reload.d.activeElement);
  healthy(x); healthy(reload);
});

// Receipt-backed height inputs, independent of the candidate's minHeight values.
// Chrome 154.0.8037.97 S0 receipt for b28546e: map 1358x718 at (41,149), actual goal
// 42.390625, L/C 37.390625, directory 26.5, task rows 52 and CI rows 37.
// These are controlled JSDOM layout inputs, not a replacement for browser QA.
const PARENT_CORRIDOR_HEIGHTS = {goal:42.390625, branch:37.390625, directory:26.5, task:52, challenge:37};
async function measuredParentCorridorPage(viewportWidth, noteHeight = 20.25) {
  const x = await page(), graph = map(x), viewportHeight = viewportWidth === 1440 ? 900 : 1080;
  const width = viewportWidth - 82, height = viewportHeight - 182;
  Object.defineProperty(graph, 'clientWidth', {configurable:true, get:() => width});
  Object.defineProperty(graph, 'clientHeight', {configurable:true, get:() => height});
  function measured(node, h) {
    Object.defineProperty(node, 'offsetHeight', {configurable:true, get:() => Math.round(h)});
    node.getBoundingClientRect = () => {
      const left = 41 + parseFloat(node.style.left || 0), top = 149 + parseFloat(node.style.top || 0), w = parseFloat(node.style.width || 0);
      return {x:left, y:top, left, top, width:w, height:h, right:left+w, bottom:top+h};
    };
  }
  for (const node of graph.querySelectorAll('[data-map-position]')) {
    const kind = node.matches('[data-overview-entity]') ? 'goal' : node.matches('[data-reading-branch]') ? 'branch' : node.matches('.np-map-task-root') ? 'directory' : node.matches('[data-task-open]') ? 'task' : 'challenge';
    measured(node, PARENT_CORRIDOR_HEIGHTS[kind]);
  }
  // 15px x 1.35 is the current one-line note box. A measured two-line
  // counterexample must move the bus rather than allowing it through prose.
  for (const note of graph.querySelectorAll('[data-layout-note]')) measured(note, note.dataset.layoutNote === 'editorial' ? 20.25 : noteHeight);
  x.w.innerWidth = viewportWidth; x.w.innerHeight = viewportHeight;
  x.w.dispatchEvent(new x.w.Event('resize')); await frames(x.w);
  return {x, graph, width, height};
}
function parentCorridorBox(node) {
  const box = {x:parseFloat(node.style.left), y:parseFloat(node.style.top), w:parseFloat(node.style.width), h:node.getBoundingClientRect().height};
  assert.ok(Object.values(box).every(Number.isFinite)); assert.ok(box.w > 0 && box.h > 0);
  return box;
}
function parentPolyline(path) {
  const tokens = path.getAttribute('d').match(/[a-zA-Z]|[-+]?(?:\d*\.)?\d+(?:e[-+]?\d+)?/g) || [], points = [];
  let current = [0, 0];
  while (tokens.length) {
    const command = tokens.shift(); assert.ok(['M','L','H','V'].includes(command), 'parent path uses an explicitly checked straight-segment command');
    assert.equal(command === 'M', points.length === 0, 'one complete parent polyline begins with M');
    if (command === 'M' || command === 'L') current = [Number(tokens.shift()), Number(tokens.shift())];
    else if (command === 'H') current = [Number(tokens.shift()), current[1]];
    else current = [current[0], Number(tokens.shift())];
    assert.ok(current.every(Number.isFinite)); points.push(current);
  }
  assert.ok(points.length >= 2);
  return {points, segments:points.slice(1).map((to,index) => {
    const from = points[index]; assert.ok(Math.abs(from[0]-to[0]) < 0.001 || Math.abs(from[1]-to[1]) < 0.001, 'parent route segments are axis-aligned');
    return {from, to};
  })};
}
function segmentCrossesInterior({from, to}, box) {
  const epsilon = 0.001, [x1,y1] = from, [x2,y2] = to;
  if (Math.abs(y1-y2) < epsilon) return y1 > box.y+epsilon && y1 < box.y+box.h-epsilon && Math.min(Math.max(x1,x2),box.x+box.w)-Math.max(Math.min(x1,x2),box.x) > epsilon;
  return x1 > box.x+epsilon && x1 < box.x+box.w-epsilon && Math.min(Math.max(y1,y2),box.y+box.h)-Math.max(Math.min(y1,y2),box.y) > epsilon;
}
function assertParentCorridors({x, graph, width, height}) {
  const nodes = [...graph.querySelectorAll('[data-map-position]')], boxes = new Map(nodes.map(node => [node.dataset.mapPosition,parentCorridorBox(node)]));
  const paths = [...graph.querySelectorAll('path[data-map-parent][data-map-child]')], bundle = x.a.getBundle();
  assert.equal(nodes.length,39); assert.equal(boxes.size,39); assert.equal(paths.length,38);
  const expected = nodes.filter(node => boxes.has(bundle.positions[node.dataset.mapPosition].parentId)).map(node => [bundle.positions[node.dataset.mapPosition].parentId,node.dataset.mapPosition].join('|')).sort();
  assert.deepEqual(paths.map(path => [path.dataset.mapParent,path.dataset.mapChild].join('|')).sort(),expected,'every exact original parent edge appears once');
  const obstacles = nodes.map(node => ({name:'node '+node.dataset.mapPosition,box:boxes.get(node.dataset.mapPosition)})).concat([...graph.querySelectorAll('[data-layout-note]:not([hidden])')].map(note => ({name:'note '+note.dataset.layoutNote,box:parentCorridorBox(note)})));
  const directory = graph.querySelector('.np-map-task-root'), directoryId = directory.dataset.mapPosition, litId = graph.querySelector('[data-reading-branch="l"]').dataset.mapPosition;
  const directoryBox = boxes.get(directoryId), litBox = boxes.get(litId), noteBoxes = obstacles.filter(row => row.name.startsWith('note ')).map(row => row.box);
  for (const path of paths) {
    const {mapParent:parent,mapChild:child} = path.dataset, label = parent+' → '+child, {points,segments} = parentPolyline(path);
    assert.equal(bundle.positions[child].parentId,parent,label+': immutable source parent');
    assert.ok(onBoundary(points[0],boxes.get(parent)),label+': starts on actual measured parent boundary');
    assert.ok(onBoundary(points.at(-1),boxes.get(child)),label+': ends on actual measured child boundary');
    const halfStroke = parseFloat(x.w.getComputedStyle(path).getPropertyValue('stroke-width'))/2;
    assert.ok(Number.isFinite(halfStroke) && halfStroke > 0);
    for (const [px,py] of points) assert.ok(px >= halfStroke && px <= width-halfStroke && py >= halfStroke && py <= height-halfStroke,label+': complete stroke stays inside map, including its gutter');
    for (const segment of segments) for (const obstacle of obstacles) assert.equal(segmentCrossesInterior(segment,obstacle.box),false,label+': parent corridor crosses '+obstacle.name);
    if (parent === litId && child === directoryId) {
      const bends = segments.filter(segment => Math.abs(segment.from[1]-segment.to[1]) < 0.001 && Math.abs(segment.from[0]-segment.to[0]) > 0.001);
      assert.equal(bends.length,1);assert.ok(bends[0].from[1] > litBox.y+litBox.h && bends[0].from[1] < directoryBox.y,'L-to-directory elbow lies in the measured gap, never inside the L card');
    }
    if (parent === directoryId) {
      const target = boxes.get(child), incoming = segments.at(-1);
      assert.equal(points[0][0],directoryBox.x,'task parents leave the directory toward its in-map left gutter');
      assert.equal(incoming.to[0],target.x,'task parent enters the exact task left boundary');
      assert.ok(incoming.from[0] < target.x && incoming.from[0] >= halfStroke,'the task inlet has an in-canvas lane');
      const bus = segments.filter(segment => Math.abs(segment.from[1]-segment.to[1]) < 0.001 && Math.abs(segment.from[0]-segment.to[0]) > 0.001 && segment.from[1] > directoryBox.y+directoryBox.h && segment.from[1] < target.y);
      // First-column paths share the vertical gutter and need no horizontal bus.
      if (target.x > directoryBox.x+0.001) {assert.ok(bus.length);for (const segment of bus) assert.ok(noteBoxes.every(box => segment.from[1] >= box.y+box.h+4.99),'task bus is below every explanatory label, with a five-pixel gap');}
    }
  }
  return paths;
}
test('review: all 38 measured parent corridors stay inside both desktop canvases and avoid node and note interiors',async()=>{
  for (const width of [1440,1920]) for (const noteHeight of [20.25,40.5]) {
    const fixture = await measuredParentCorridorPage(width,noteHeight), {x} = fixture;
    try {const route = clean(x.a.getState().route), scientific = snapshotGraph(x);assertParentCorridors(fixture);assert.deepEqual(clean(x.a.getState().route),route);assert.deepEqual(snapshotGraph(x),scientific);healthy(x);} finally {x.w.close();}
  }
});
test('review: parent corridor guard rejects the former negative-six gutter and 92px elbow plus a bus through note text',async()=>{
  for (const width of [1440,1920]) {
    const fixture = await measuredParentCorridorPage(width), {x,graph} = fixture;
    try {
      assertParentCorridors(fixture);
      const directory = graph.querySelector('.np-map-task-root'), dir = parentCorridorBox(directory), lit = graph.querySelector('[data-reading-branch="l"]'), l = parentCorridorBox(lit), first = graphTask(x,'task:pointnav'), firstBox = parentCorridorBox(first), later = graphTask(x,'task:vln'), laterBox = parentCorridorBox(later);
      const cases = [
        {child:first.dataset.mapPosition,d:'M '+dir.x+' '+(dir.y+dir.h/2)+' H -6 V 150 H -6 V '+(firstBox.y+firstBox.h/2)+' H '+firstBox.x,reason:/complete stroke stays inside map/},
        {child:directory.dataset.mapPosition,d:'M '+(l.x+l.w/2)+' '+(l.y+l.h)+' V 92 H '+(dir.x+dir.w/2)+' V '+dir.y,reason:/parent corridor crosses node|L-to-directory elbow/},
        {child:later.dataset.mapPosition,d:'M '+dir.x+' '+(dir.y+dir.h/2)+' H 2 V 134 H '+(laterBox.x-6)+' V '+(laterBox.y+laterBox.h/2)+' H '+laterBox.x,reason:/parent corridor crosses node|parent corridor crosses note|task bus is below/},
      ];
      for (const invalid of cases) {
        const path = graph.querySelector('path[data-map-child="'+invalid.child+'"]'), original = path.getAttribute('d');
        try {path.setAttribute('d',invalid.d);assert.throws(()=>assertParentCorridors(fixture),invalid.reason,'independent validator must reject the exact former geometry');} finally {path.setAttribute('d',original);}
        assertParentCorridors(fixture);
      }
      healthy(x);
    } finally {x.w.close();}
  }
});


function inheritedComputedValue(x, node, property) {
  for (let current = node; current; current = current.parentElement) {
    const value = x.w.getComputedStyle(current).getPropertyValue(property).trim();
    if (value && !['inherit', 'unset'].includes(value)) return value;
  }
  return '';
}
function cssRGBA(x, node, raw) {
  let value = String(raw || 'transparent').trim().toLowerCase();
  for (let depth = 0; /^var\(/.test(value) && depth < 8; depth++) {
    const variable = value.match(/^var\((--[^,\s)]+)(?:,\s*(.*))?\)$/);
    assert.ok(variable, 'supported computed CSS variable: ' + value);
    value = inheritedComputedValue(x, node, variable[1]) || variable[2] || '';
    assert.ok(value, 'computed CSS variable must resolve: ' + variable[1]);
    value = value.trim().toLowerCase();
  }
  if (value === 'currentcolor') value = inheritedComputedValue(x, node, 'color');
  if (value === 'transparent') return [0, 0, 0, 0];
  if (value === 'white') return [255, 255, 255, 1];
  if (value === 'black') return [0, 0, 0, 1];
  if (/^#[a-f0-9]{3,8}$/i.test(value)) {
    let hex = value.slice(1);
    if (hex.length === 3 || hex.length === 4) hex = Array.from(hex, c => c + c).join('');
    assert.ok(hex.length === 6 || hex.length === 8, 'supported hex color length');
    return [parseInt(hex.slice(0, 2), 16), parseInt(hex.slice(2, 4), 16), parseInt(hex.slice(4, 6), 16), hex.length === 8 ? parseInt(hex.slice(6, 8), 16) / 255 : 1];
  }
  const functional = value.match(/^rgba?\((.*)\)$/i);
  assert.ok(functional, 'unsupported computed color must not silently pass: ' + value);
  const parts = functional[1].trim().split(/[\s,/]+/);
  assert.ok(parts.length === 3 || parts.length === 4);
  const rgb = parts.slice(0, 3).map(part => part.endsWith('%') ? parseFloat(part) * 2.55 : Number(part));
  const alpha = parts.length === 4 ? (parts[3].endsWith('%') ? parseFloat(parts[3]) / 100 : Number(parts[3])) : 1;
  assert.ok(rgb.every(n => Number.isFinite(n) && n >= 0 && n <= 255));
  assert.ok(Number.isFinite(alpha) && alpha >= 0 && alpha <= 1);
  return rgb.concat(alpha);
}
function alphaOver(foreground, background) {
  const alpha = foreground[3] + background[3] * (1 - foreground[3]);
  if (!alpha) return [0, 0, 0, 0];
  return foreground.slice(0, 3).map((channel, index) => (channel * foreground[3] + background[index] * background[3] * (1 - foreground[3])) / alpha).concat(alpha);
}
function numericOpacity(value) {
  if (!value || value === 'normal') return 1;
  const result = value.endsWith('%') ? parseFloat(value) / 100 : Number(value);
  assert.ok(Number.isFinite(result) && result >= 0 && result <= 1, 'valid computed opacity');
  return result;
}
function luminance(rgb) {
  const channels = rgb.slice(0, 3).map(value => {
    const channel = value / 255;
    return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function computedContrast(x, node, property) {
  const style = x.w.getComputedStyle(node), raw = property === 'color' ? inheritedComputedValue(x, node, property) : style.getPropertyValue(property);
  assert.ok(raw, 'the tested paint comes from actual computed style');
  const ink = cssRGBA(x, node, raw);
  if (property === 'stroke') ink[3] *= numericOpacity(style.getPropertyValue('stroke-opacity'));
  let painted = ink.slice(), adjacent = [0, 0, 0, 0];
  const backgrounds = [];
  for (let current = node; current; current = current.parentElement) {
    const computed = x.w.getComputedStyle(current), background = cssRGBA(x, current, computed.backgroundColor);
    if (background[3] > 0) backgrounds.push({element:current.id || current.tagName, rgba:background});
    const backgroundImage = computed.getPropertyValue('background-image');
    assert.ok(!backgroundImage || backgroundImage === 'none', 'a painted background image needs real-browser contrast analysis');
    painted = alphaOver(painted, background);
    adjacent = alphaOver(adjacent, background);
    const opacity = numericOpacity(computed.opacity);
    painted[3] *= opacity; adjacent[3] *= opacity;
  }
  assert.ok(backgrounds.length, 'contrast must use an actual painted ancestor background');
  // Composite any remaining transparency over the browser canvas. In the current
  // view, the measured opaque white overview background is reached beforehand.
  painted = alphaOver(painted, [255, 255, 255, 1]);
  adjacent = alphaOver(adjacent, [255, 255, 255, 1]);
  const a = luminance(painted), b = luminance(adjacent);
  return {ratio:(Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05), ink, painted, adjacent, backgrounds};
}
test('review: computed normal and selected connector contrast stays at least 3 to 1 without shrinking visible labels', async t => {
  const x = await page(); t.after(() => x.w.close());
  const parents = [...map(x).querySelectorAll('path[data-map-parent][data-map-child]')];
  const typed = [...map(x).querySelectorAll('path[data-map-relation]')];
  assert.equal(parents.length, 38); assert.equal(typed.length, 7);
  const minimum = {parent:Infinity, typed:Infinity, active:Infinity};
  for (const [kind, nodes, expected] of [['parent', parents, [87, 118, 124]], ['typed', typed, [60, 131, 125]]]) {
    for (const node of nodes) {
      const result = computedContrast(x, node, 'stroke'), style = x.w.getComputedStyle(node);
      assert.deepEqual(result.ink.slice(0, 3), expected, kind + ': actual computed stroke uses the reviewed palette');
      assert.equal(numericOpacity(style.opacity), 1, kind + ': normal stroke is fully opaque');
      assert.ok(result.ratio >= 3, kind + ': composited line contrast must be at least 3:1, got ' + result.ratio);
      if (kind === 'parent') assert.equal(parseFloat(style.getPropertyValue('stroke-width')), 1.5);
      minimum[kind] = Math.min(minimum[kind], result.ratio);
    }
  }
  x.d.querySelector('#np-task-relations > summary').click();
  const selectedId = 'tasks:relation:90';
  x.d.getElementById('np-relation-select-' + selectedId).click(); await frames(x.w);
  const selected = relationPath(x, selectedId), result = computedContrast(x, selected, 'stroke');
  assert.equal(selected.classList.contains('np-map-relation-active'), true, 'active color follows a real relation selection');
  assert.deepEqual(result.ink.slice(0, 3), [171, 90, 37]);
  assert.equal(numericOpacity(x.w.getComputedStyle(selected).opacity), 1);
  assert.ok(result.ratio >= 3, 'selected relation composited contrast is at least 3:1');
  minimum.active = result.ratio;
  const texts = [...map(x).querySelectorAll('.np-task-reading-contract,.np-task-reading-name,.np-map-challenge-label,.np-map-layout-note,.np-map-editorial-note,.np-overview-goal h2,.np-overview-goal p,[data-reading-branch] h3,.np-map-task-root'), ...x.d.querySelectorAll('#np-reading-landing .np-map-legend span'), ...x.d.querySelectorAll('nav.np-relation-selectors button')];
  assert.equal(x.d.querySelectorAll('#np-reading-landing .np-map-legend span').length, 3, 'moving the footer cannot silently omit legend typography coverage');
  assert.ok(texts.length >= 70, 'task, CI, branch, legend and independent selection labels are checked');
  for (const node of texts) {
    const size = inheritedComputedValue(x, node, 'font-size');
    assert.ok(/^\d+(?:\.\d+)?px$/.test(size) && parseFloat(size) >= 15, 'label computed font size remains at least 15px: ' + node.textContent);
    assert.ok(computedContrast(x, node, 'color').ratio >= 3, 'computed label color remains legible against its actual ancestor background');
    for (let current = node; current; current = current.parentElement) {
      const style = x.w.getComputedStyle(current), transform = style.getPropertyValue('transform'), zoom = style.getPropertyValue('zoom');
      assert.ok(!transform || transform === 'none', 'labels are not made smaller through a transform');
      if (zoom && zoom !== 'normal') assert.ok((zoom.endsWith('%') ? parseFloat(zoom) / 100 : Number(zoom)) >= 1, 'labels are not made smaller through CSS zoom');
    }
  }
  t.diagnostic('Computed composited contrast: parent ' + minimum.parent.toFixed(3) + ':1; typed ' + minimum.typed.toFixed(3) + ':1; selected ' + minimum.active.toFixed(3) + ':1.');
  // No pseudo-element style or synthetic :hover result is claimed here. The
  // legend's ::before marks, actual hover/focus appearance and rendered pixels
  // remain part of real-browser screenshot/interaction acceptance.
  healthy(x);
});


test('nohash: saved relation focus and disclosure restore on the actual bare URL', async t => {
  const x = await page(); t.after(() => x.w.close());
  assert.equal(x.w.location.hash, '');
  if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
  relationPath(x, 'tasks:relation:90').dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
  await frames(x.w);
  // A document scroll exists in the compact layout; desktop intentionally
  // pins the outer page at zero. Select the real edge before changing layout.
  x.w.innerWidth = 1024; x.w.dispatchEvent(new x.w.Event('resize')); await frames(x.w);
  home(x).scrollTop = 143;
  x.w.scrollTo(0, 211);
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.w.history.state), focus = x.d.activeElement.id;
  assert.equal(x.w.location.hash, '');
  const reload = await page({saved, width:1024}); t.after(() => reload.w.close());
  assert.equal(reload.w.location.hash, '', 'test the original bare URL, not a synthetic canonical hash');
  assert.equal(reload.d.activeElement.id, focus);
  assert.equal(reload.d.activeElement.tagName, 'ARTICLE');
  assert.equal(reload.d.querySelector('#np-task-relations').open, false);
  assert.equal(home(reload).scrollTop, 143);
  assert.equal(reload.w.scrollY, 211);
  assert.deepEqual(clean(reload.a.getState().route), clean(x.a.getState().route));
  visible(reload, reload.d.activeElement);
  healthy(x); healthy(reload);
});

test('nohash: fresh and invalid-history bare entry do not force focus', async t => {
  const fresh = await page(); t.after(() => fresh.w.close());
  assert.equal(fresh.d.activeElement, fresh.d.body);
  assert.equal(home(fresh).hidden, false);
  const root = fresh.a.getBundle().researchMap.roots[0];
  for (const invalid of [{invalid:true}, {route:{tree:'g',node:root}}]) {
    const x = await page({saved:{[fresh.M.KEY]:invalid}}); t.after(() => x.w.close());
    assert.equal(x.w.location.hash, '');
    assert.equal(x.d.activeElement, x.d.body);
    assert.equal(home(x).hidden, false, 'rejected history cannot switch presentation mode');
    assert.equal(x.M.getBucket(x.a.getState()).originalMapOpen, false);
    healthy(x);
  }
  healthy(fresh);
});

test('nohash: rapid task switches after restored relation keep the newest route and focus', async t => {
  const x = await page(); t.after(() => x.w.close());
  if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
  relationPath(x, 'tasks:relation:90').dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
  await frames(x.w);
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const reload = await page({saved:clean(x.w.history.state)}); t.after(() => reload.w.close());
  assert.equal(reload.d.activeElement.id, 'np-map-relation-evidence-tasks:relation:90');
  reload.a.render({restore:true, focus:true}); // Leave an old restoration RAF queued.
  const audio = graphTask(reload, 'task:audiogoal'), goat = graphTask(reload, 'task:goat');
  audio.click();
  goat.click();
  await frames(reload.w);
  const route = clean(reload.a.getState().route);
  assert.equal(route.scope, 'task:goat');
  assert.equal(reload.d.activeElement.id, 'np-node-' + route.node);
  assert.notEqual(reload.d.activeElement.tagName, 'ARTICLE');
  await frames(reload.w);
  assert.deepEqual(clean(reload.a.getState().route), route);
  assert.equal(reload.d.activeElement.id, 'np-node-' + route.node);
  healthy(x); healthy(reload);
});


test('nohash: unload saves the final scroll before the debounce without cancelling navigation', async t => {
  const x = await page(); t.after(() => x.w.close());
  if(map(x).dataset.relationsVisible!=='true')x.d.querySelector('#np-map-relations-toggle').click();
  relationPath(x, 'tasks:relation:90').dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
  await frames(x.w);
  // A document scroll exists in the compact layout; desktop intentionally
  // pins the outer page at zero. Select the real edge before changing layout.
  x.w.innerWidth = 1024; x.w.dispatchEvent(new x.w.Event('resize')); await frames(x.w);
  home(x).scrollTop = 527;
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  x.w.history.replaceState({...clean(x.w.history.state),unrelatedOwnerField:'preserved'}, '', x.w.location.href);
  let added=0, removed=0;
  const add=x.w.addEventListener.bind(x.w),remove=x.w.removeEventListener.bind(x.w);
  x.w.addEventListener=function(type,...args){if(type==='beforeunload')added++;return add(type,...args);};
  x.w.removeEventListener=function(type,...args){if(type==='beforeunload')removed++;return remove(type,...args);};
  home(x).scrollTop = 872;
  x.w.scrollTo(0, 33);
  home(x).dispatchEvent(new x.w.Event('scroll'));
  home(x).dispatchEvent(new x.w.Event('scroll'));
  assert.equal(added,1,'pending scroll registers one temporary listener');
  assert.equal(x.M.getBucket(x.w.history.state[x.M.KEY]).overviewView.scrollTop, 527, 'precondition: delayed persistence has not fired');
  const event = new x.w.Event('beforeunload', {cancelable:true});
  assert.equal(x.w.dispatchEvent(event), true);
  assert.equal(event.defaultPrevented, false, 'saving must not cancel navigation or request a prompt');
  const saved = clean(x.w.history.state);
  assert.equal(x.M.getBucket(saved[x.M.KEY]).overviewView.scrollTop, 872);
  assert.equal(x.M.getBucket(saved[x.M.KEY]).windowScroll, 33);
  assert.equal(saved.unrelatedOwnerField, 'preserved');
  assert.equal(removed,1,'successful persistence removes the lifecycle listener');
  home(x).dispatchEvent(new x.w.Event('scroll'));
  assert.equal(added,2,'a later dirty scroll creates a new bounded pending window');
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  assert.equal(removed,2,'existing pagehide also flushes and removes the listener');
  x.a.render({restore:true,focus:true});
  home(x).dispatchEvent(new x.w.Event('scroll'));
  assert.equal(added,2,'restoration scroll does not arm an unload listener');
  await frames(x.w);
  home(x).scrollTop=900;
  home(x).dispatchEvent(new x.w.Event('scroll'));
  assert.equal(added,3);
  await wait(160);
  assert.equal(removed,3,'normal debounce persistence also disarms');
  assert.equal(x.M.getBucket(x.w.history.state[x.M.KEY]).overviewView.scrollTop,900);

  assert.equal(fs.readFileSync(path.join(root,'assets/navigation-product.js'),'utf8').split("addEventListener('beforeunload',saveCurrent)").length-1, 1, 'one lifecycle listener registration');
  const reload = await page({saved, width:1024}); t.after(() => reload.w.close());
  assert.equal(reload.w.location.hash, '');
  assert.equal(home(reload).scrollTop, 872);
  assert.equal(reload.w.scrollY, 33);
  assert.equal(reload.d.activeElement.id, 'np-map-relation-evidence-tasks:relation:90');
  healthy(x); healthy(reload);
});

}
