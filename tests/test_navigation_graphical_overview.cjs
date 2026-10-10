'use strict';
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
    "each of the 22 graphical task controls enters only its own original pair of S1 forests",
    "each of the 13 CI controls opens its exact original g position and Back restores S0 focus",
    "seven visible typed paths keep exact original endpoints/types and cannot acquire tree-parent semantics",
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
    ['review8', '^review: ', 8],
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
  require('node:assert/strict').ok(['original22', 'review8'].includes(graphicalGroup), 'unknown graphical test group');
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
// The science payload and pre-S0 projection implementation are independently
// pinned: checking DOM against a candidate-defined hierarchy alone could self-pass.
const ORIGINAL_PROJECTION_SHA = 'c1dcba7bb06d0ad8961ce33b28b596d94b32d4e1fe41d0811de40502321005be';
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
  const errors = [], calls = [], external = [];
  class NoNetwork extends ResourceLoader {
    fetch(url) { external.push(url); return null; }
  }
  const vc = new VirtualConsole();
  vc.on('jsdomError', error => errors.push(error.message));
  const dom = new JSDOM(html, {
    url:'https://example.org/research/navigation/' + (options.hash || ''),
    runScripts:'dangerously', resources:new NoNetwork(), pretendToBeVisual:true, virtualConsole:vc,
    beforeParse(w) {
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
  return {w, d:w.document, a:w.NavigationProductApp, M:w.NavigationProductModel, errors, calls, external};
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
  const result = x.d.querySelector('#np-tree section[data-parallel-tree="' + tree + '"]');
  assert.ok(result, 'original local ' + tree + ' forest is present');
  return result;
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
  const p = science.positions[id], route = x.a.getState().route;
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
  assert.equal(frozenSources['scripts/navigation_research_map.py'], ORIGINAL_PROJECTION_SHA, 'the graph cannot redefine its expected scientific parents');
  assert.equal(science.scopes.length, 64);
  assert.equal(Object.keys(science.positions).length, 1683);
  const x = await page(); t.after(() => x.w.close());
  const b = x.a.getBundle();
  assert.equal(b.delivery.sourceModelSha256, SCIENCE_SHA);
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

test('each of the 22 graphical task controls enters only its own original pair of S1 forests', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [sid] of TASK_INDEX) {
    const control = graphTask(x, sid);
    control.focus(); control.click(); await frames(x.w);
    assert.equal(x.a.getState().route.scope, sid);
    assert.equal(home(x).hidden, true);
    assert.equal(x.d.querySelector('#np-tree').dataset.parallelScope, sid);
    for (const tree of ['l', 'c']) assertTrueForest(x, sid, tree);
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

test('seven visible typed paths keep exact original endpoints/types and cannot acquire tree-parent semantics', async t => {
  const x = await page(); t.after(() => x.w.close());
  const graph = map(x), paths = [...graph.querySelectorAll('path[data-map-relation]')];
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
      const path = relationPath(x, id), source = originalRelation(id);
      x.w.__scrollTargets.length = 0;
      if (action === 'click') path.dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
      else {
        path.focus();
        path.dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'Enter', bubbles:true, cancelable:true}));
      }
      await frames(x.w);
      assert.equal(panel.open, true, id + ': ' + action + ' opens source details');
      const row = panel.querySelector('[data-task-relation="' + id + '"]');
      assert.ok(row);
      assert.ok(row === x.d.activeElement || row.contains(x.d.activeElement) || x.w.__scrollTargets.some(target => target === row || row.contains(target)), id + ': source action locates the exact relation, not only the shared disclosure');
      for (const loc of source.detail.locators) {
        assert.ok(row.textContent.includes(loc.locator), id + ': original source locator');
        if (loc.version) assert.ok(row.textContent.includes(loc.version), id + ': original source version');
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
      relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
      const row = x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
      const control = row.querySelectorAll('button')[index];
      assert.ok(control.textContent.includes(scopeById.get(sid).label));
      control.focus(); control.click(); await frames(x.w);
      assert.equal(x.a.getState().route.scope, sid);
      for (const tree of ['l', 'c']) assertTrueForest(x, sid, tree);
      await back(x);
      assert.equal(x.d.querySelector('#np-task-relations').open, true);
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
    for (const tree of ['l', 'c']) assertTrueForest(x, source.id, tree);
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
    const x = await page({hash:fixture.urlHash, saved:fixture.history}); t.after(() => x.w.close());
    assert.deepEqual(clean(x.a.getState().route), fixture.history[x.M.KEY].route);
    assert.equal(x.d.querySelector('#np-tree-scroll').scrollTop, 123);
    assert.equal(x.d.querySelector('#np-detail-scroll').scrollTop, 570);
    assert.equal(x.w.scrollY, 1750);
    assert.equal(x.w.history.state.unrelatedOwnerField, 'preserve-me');
    if (['l', 'c'].includes(x.a.getState().route.tree)) for (const tree of ['l', 'c']) assertTrueForest(x, x.a.getState().route.scope, tree);
    healthy(x);
  });
}

test('relation visibility and notes disclosure survive a task round-trip and saved-history reload', async t => {
  const x = await page(); t.after(() => x.w.close());
  const initial = clean(x.a.getState().route);
  assert.equal(map(x).dataset.relationsVisible, 'true');
  assert.equal(x.d.querySelector('#np-map-relations-toggle').getAttribute('aria-pressed'), 'true');
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
  assert.equal(map(backwards).dataset.relationsVisible, 'true', 'old S0 snapshots get default visible relationships');
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
    const row = x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
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
  path.focus();
  assert.equal(x.d.activeElement, path);
  x.w.innerWidth = 1440;
  x.w.dispatchEvent(new x.w.Event('resize'));
  await frames(x.w);
  assert.equal(x.d.activeElement, relationPath(x, id));
  assert.deepEqual(clean(x.a.getState().route), route);
  x.d.activeElement.dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'Enter', bubbles:true, cancelable:true}));
  await frames(x.w);
  assert.equal(x.d.querySelector('#np-task-relations').open, true);
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
  relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true}));
  await frames(x.w);
  const row = x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
  assert.equal(x.d.activeElement, row);
  assert.equal(row.getAttribute('tabindex'), '-1');
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.w.history.state), hash = x.M.encodeRoute(x.a.getState().route);
  const reload = await page({saved, hash}); t.after(() => reload.w.close());
  const restored = reload.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
  assert.equal(reload.d.querySelector('#np-task-relations').open, true);
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
    relationPath(x, id).dispatchEvent(new x.w.MouseEvent('click', {bubbles:true})); await frames(x.w);
    const row = x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
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
  x.d.querySelector('#np-map-relations-toggle').click();
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
    assert.equal(control.getAttribute('aria-controls'), x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]').id, id + ': accessible control target is the exact article');
    assert.ok(control.textContent.includes(RELATION_DISPLAY_LABELS[id]), id + ': exact relation wording');
    assert.ok(control.textContent.includes(RELATION_TYPE_LABELS[type]), id + ': literal relation type');
    assert.equal(control.closest('[data-task-relation]'), null, 'selection controls do not replace or masquerade as the two scope endpoints');
    visible(x, control);
    control.focus();
    assert.equal(x.d.activeElement, control, 'the native control is independently focusable');
    // JSDOM does not implement native Enter/Space-to-click activation. This
    // exercises the real click callback without inventing a production keydown
    // handler or claiming real-browser keyboard, pointer hit or pixel acceptance.
    control.click(); await frames(x.w);
    const article = x.d.querySelector('#np-task-relations [data-task-relation="' + id + '"]');
    assert.equal(x.d.activeElement, article, id + ': exact source article receives focus');
    assert.equal(x.d.querySelector('#np-task-relations').open, true);
    assert.deepEqual(clean(x.a.getState().route), route);
  }
  assert.deepEqual(snapshotGraph(x), scientific);
  const focusedId = 'np-relation-select-tasks:relation:90';
  x.d.getElementById(focusedId).focus();
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const reload = await page({saved:clean(x.w.history.state), hash:x.M.encodeRoute(x.a.getState().route)}); t.after(() => reload.w.close());
  assert.equal(map(reload).dataset.relationsVisible, 'false');
  assert.equal(reload.d.querySelector('#np-task-relations').open, true);
  assert.equal(reload.d.activeElement, reload.d.getElementById(focusedId));
  visible(reload, reload.d.activeElement);
  healthy(x); healthy(reload);
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
  const texts = [...map(x).querySelectorAll('.np-task-reading-contract,.np-task-reading-name,.np-map-challenge-label,.np-map-layout-note,.np-map-editorial-note,.np-map-legend span,.np-overview-goal h2,.np-overview-goal p,[data-reading-branch] h3,.np-map-task-root'), ...x.d.querySelectorAll('nav.np-relation-selectors button')];
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

}
