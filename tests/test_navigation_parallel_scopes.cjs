'use strict';
// Behavioral and identity regression only. JSDOM is not desktop visual acceptance.
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
const TASK_COMPARISON_FIELDS = {
  "task:pointnav": {
    "inputSummary": "目标坐标",
    "completionSummary": "到达指定位置并按协议终止",
    "boundary": "已知目标位置；不借物体搜索CI补空。",
    "sourceURLs": [
      "https://arxiv.org/pdf/1807.06757v1",
      "https://aihabitat.org/challenge/2020/"
    ]
  },
  "task:imagenav": {
    "inputSummary": "地点图像",
    "completionSummary": "到达图像代表的位置",
    "boundary": "朝向对齐依版本；不是找到图中物体。",
    "sourceURLs": [
      "https://arxiv.org/html/2211.15876v1",
      "https://prior.allenai.org/projects/target-driven-visual-navigation",
      "https://openaccess.thecvf.com/content_CVPR_2020/html/Chaplot_Neural_Topological_SLAM_for_Visual_Navigation_CVPR_2020_paper.html",
      "https://github.com/facebookresearch/eai-vc/blob/main/cortexbench/DATASETS.md"
    ]
  },
  "task:instanceimagenav": {
    "inputSummary": "物体实例照片",
    "completionSummary": "找到同一物理实例并进入成功区域",
    "boundary": "同类替代物不算；不要求回到拍摄点。MOD-IIN直接和条件位置保留。",
    "sourceURLs": [
      "https://aihabitat.org/challenge/2023/",
      "https://arxiv.org/html/2211.15876v1"
    ]
  },
  "task:category-objectnav": {
    "inputSummary": "物体类别",
    "completionSummary": "找到并到达任一合格实例",
    "boundary": "按协议核停止及可见性；oracle可见性不等于末帧直接可见。",
    "sourceURLs": [
      "https://aihabitat.org/challenge/2020/",
      "https://aihabitat.org/challenge/2023/",
      "https://arxiv.org/html/2006.13171v2",
      "https://proceedings.neurips.cc/paper/2020/file/2c75cf2681788adaca63aa95ae028b22-Paper.pdf",
      "https://openaccess.thecvf.com/content/CVPR2022/papers/Ramakrishnan_PONI_Potential_Functions_for_ObjectGoal_Navigation_With_Interaction-Free_Learning_CVPR_2022_paper.pdf",
      "https://arxiv.org/pdf/2006.13171v2"
    ]
  },
  "task:language-objectnav": {
    "inputSummary": "目标物体或实例描述",
    "completionSummary": "自主搜索符合描述的目标",
    "boundary": "不是路线指令；现有方法/CI仅条件关联，预建图、楼层/房间条件不得隐藏。",
    "sourceURLs": [
      "https://arxiv.org/html/2203.10421v2",
      "https://arxiv.org/html/2512.22342v5"
    ]
  },
  "task:roomnav": {
    "inputSummary": "房间或区域目标",
    "completionSummary": "进入协议规定的目标区域成功状态",
    "boundary": "终点是房间；不是房间内物体。",
    "sourceURLs": [
      "https://arxiv.org/pdf/1807.06757v1",
      "https://arxiv.org/pdf/1801.02209",
      "https://github.com/facebookresearch/House3D"
    ]
  },
  "task:hieranav": {
    "inputSummary": "类别、房型、具体房间或唯一实例约束",
    "completionSummary": "找到符合约束的物体",
    "boundary": "四层均以物体为终点；PlanA-VID多目标和SAP-Nav单目标条件分开。",
    "sourceURLs": [
      "https://arxiv.org/html/2602.02220v3"
    ]
  },
  "task:lamon": {
    "inputSummary": "逐个到来的语言目标",
    "completionSummary": "复用同episode经验寻找各描述对象",
    "boundary": "LaMoN任务、LangNav数据、MLFM方法分开；成功阈值按版本。",
    "sourceURLs": [
      "https://arxiv.org/html/2507.07299v2",
      "https://3dlg-hcvc.github.io/langmonmap/"
    ]
  },
  "task:ddn": {
    "inputSummary": "功能需求",
    "completionSummary": "找到满足需求的物体并完成协议定位要求",
    "boundary": "多个物体可满足需求；NSR与含bbox的SSR不合并。",
    "sourceURLs": [
      "https://arxiv.org/html/2309.08138"
    ]
  },
  "task:aerial-visual-object-search": {
    "inputSummary": "目标图片与文本同时给出",
    "completionSummary": "在未见城市飞行搜索；精确成功阈值待核",
    "boundary": "L/C为空；飞行与停止不能冒充已核成功标准。",
    "sourceURLs": [
      "https://ojs.aaai.org/index.php/AAAI/article/view/38898"
    ]
  },
  "task:vln": {
    "inputSummary": "路线语言与当前观测",
    "completionSummary": "执行路线；到达与路线忠实度分别评估",
    "boundary": "SR不代替路径忠实度；VLN-CE是执行设置，不升格为第23任务。",
    "sourceURLs": [
      "https://arxiv.org/abs/1809.00786",
      "https://arxiv.org/abs/2010.07954",
      "https://github.com/jacobkrantz/VLN-CE#rxr-habitat-challenge",
      "https://openaccess.thecvf.com/content_CVPR_2019/papers/Chen_TOUCHDOWN_Natural_Language_Navigation_and_Spatial_Reasoning_in_Visual_Street_CVPR_2019_paper.pdf",
      "https://arxiv.org/abs/2001.03671",
      "https://arxiv.org/abs/1903.00401",
      "https://data.vision.ee.ethz.ch/arunv/personal/talk2nav.html",
      "https://arxiv.org/abs/2004.02857",
      "https://github.com/jacobkrantz/VLN-CE",
      "https://openaccess.thecvf.com/content_cvpr_2018/html/Anderson_Vision-and-Language_Navigation_Interpreting_CVPR_2018_paper.html",
      "https://arxiv.org/abs/1905.12255"
    ]
  },
  "task:ivln": {
    "inputSummary": "同环境tour中的多条路线指令",
    "completionSummary": "跨段复用经验并逐段评估导航",
    "boundary": "保留迭代任务范式角色；oracle接驳/reset/tour条件不可省略。",
    "sourceURLs": [
      "https://jacobkrantz.github.io/ivln",
      "https://arxiv.org/html/2210.03087v3",
      "https://arxiv.org/abs/2210.03087"
    ]
  },
  "task:remote-referent-navigation": {
    "inputSummary": "简短物体描述",
    "completionSummary": "到达可识别位置并指出正确物体",
    "boundary": "保留式字；到达与指代定位是两个结果，task不等于benchmark。",
    "sourceURLs": [
      "https://arxiv.org/abs/1904.10151",
      "https://github.com/YuankaiQi/REVERIE"
    ]
  },
  "task:soon": {
    "inputSummary": "物体、关系及周边区域描述",
    "completionSummary": "搜索并定位目标",
    "boundary": "导航距离成功与全景定位分开；共享DUET不构成任务继承。",
    "sourceURLs": [
      "https://openaccess.thecvf.com/content/CVPR2021/papers/Zhu_SOON_Scenario_Oriented_Object_Navigation_With_Graph-Based_Exploration_CVPR_2021_paper.pdf",
      "https://scenario-oriented-object-navigation.github.io/"
    ]
  },
  "task:ndh": {
    "inputSummary": "目标与已有对话历史",
    "completionSummary": "接续导航并取得目标进展",
    "boundary": "不是自主提问导航。",
    "sourceURLs": [
      "https://proceedings.mlr.press/v100/thomason20a.html",
      "https://umrobotslang.github.io/",
      "https://github.com/mmurray/cvdn"
    ]
  },
  "task:multion": {
    "inputSummary": "有序物体目标序列",
    "completionSummary": "依次寻找并报告FOUND，评估序列完成",
    "boundary": "原版彩色圆柱；错误FOUND终止，不泛化为失败后继续。",
    "sourceURLs": [
      "https://papers.nips.cc/paper/2020/file/6e01383fd96a17ae51cc3e15447e7533-Paper.pdf"
    ]
  },
  "task:goat": {
    "inputSummary": "依次到来的类别、实例图片或语言目标",
    "completionSummary": "复用记忆完成多个子任务",
    "boundary": "任务、系统、GOAT-Bench分开；记忆不是权重更新，NavHarness新episode清空条件保留。",
    "sourceURLs": [
      "https://robots-that-learn.github.io/resources/59_goat_go_to_any_thing.pdf",
      "https://arxiv.org/html/2404.06609v1",
      "https://arxiv.org/abs/2311.06430",
      "https://mukulkhanna.github.io/goat-bench/"
    ]
  },
  "task:audiogoal": {
    "inputSummary": "声音与视觉观测",
    "completionSummary": "接近声源，按配置判断成功",
    "boundary": "不默认给目标坐标；SoundSpaces为平台。",
    "sourceURLs": [
      "https://arxiv.org/abs/1912.11474",
      "https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123510018.pdf"
    ]
  },
  "task:audiopointgoal": {
    "inputSummary": "声音观测与位置目标",
    "completionSummary": "结合两种信息完成导航",
    "boundary": "比AudioGoal多位置输入；不新造两者的canonical任务边。",
    "sourceURLs": [
      "https://arxiv.org/abs/1912.11474",
      "https://www.ecva.net/papers/eccv_2020/papers_ECCV/papers/123510018.pdf"
    ]
  },
  "task:person-finding-following": {
    "inputSummary": "目标人物",
    "completionSummary": "找到后维持协议规定的跟随行为",
    "boundary": "不是避让行人或一次到达，也不是Social Rearrangement。",
    "sourceURLs": [
      "https://github.com/facebookresearch/habitat-lab/blob/main/habitat-baselines/README.md",
      "https://arxiv.org/abs/2310.13724"
    ]
  },
  "task:namo": {
    "inputSummary": "到达目标及可移动障碍条件",
    "completionSummary": "通过移动物体改变通路并到达",
    "boundary": "保留任务问题角色；搬运不是主目标；平面几何与iGibson部分观测3D条件分开。",
    "sourceURLs": [
      "https://www.ri.cmu.edu/pub_files/pub4/stilman_michael_2005_3/stilman_michael_2005_3.pdf"
    ]
  },
  "task:comon": {
    "inputSummary": "多目标任务及导航者与特权oracle通信",
    "completionSummary": "协作完成多目标导航",
    "boundary": "不是无特权多机器人探索；双方信息不同。",
    "sourceURLs": [
      "https://arxiv.org/abs/2110.05769",
      "https://shivanshpatel35.github.io/comon/resources/comon.pdf"
    ]
  }
};
const TASK_RELATIONS = [
  {
    "id": "tasks:relation:88",
    "from": "task:vln",
    "to": "task:ivln",
    "relationType": "sequential_composition",
    "renderAsTree": false,
    "proposedLabel": "同环境 tour 内多条指令，段间接驳依协议"
  },
  {
    "id": "tasks:relation:89",
    "from": "task:category-objectnav",
    "to": "task:multion",
    "relationType": "sequential_composition",
    "renderAsTree": false,
    "proposedLabel": "类别目标按序组合"
  },
  {
    "id": "tasks:relation:90",
    "from": "task:category-objectnav",
    "to": "task:goat",
    "relationType": "composed_goal_type_in",
    "renderAsTree": false,
    "proposedLabel": "提供类别目标"
  },
  {
    "id": "tasks:relation:91",
    "from": "task:instanceimagenav",
    "to": "task:goat",
    "relationType": "composed_goal_type_in",
    "renderAsTree": false,
    "proposedLabel": "提供实例图片目标"
  },
  {
    "id": "tasks:relation:92",
    "from": "task:language-objectnav",
    "to": "task:goat",
    "relationType": "composed_goal_type_in",
    "renderAsTree": false,
    "proposedLabel": "提供语言描述目标"
  },
  {
    "id": "tasks:relation:93",
    "from": "task:language-objectnav",
    "to": "task:lamon",
    "relationType": "sequential_composition",
    "renderAsTree": false,
    "proposedLabel": "语言目标按序接续"
  },
  {
    "id": "tasks:relation:94",
    "from": "task:imagenav",
    "to": "task:instanceimagenav",
    "relationType": "different_success_semantics",
    "renderAsTree": false,
    "proposedLabel": "成功对象不同：地点与物体实例"
  }
];
const LOCAL_CI_WITHOUT_GLOBAL_PROJECTION = [
  ['task:instanceimagenav', 'pos:c:6b47ea4f99620cf6f21d47'],
  ['task:roomnav', 'pos:c:28a17ca2f83c8be2f0adbd'],
  ['task:ivln', 'pos:c:32cc0654d0bcee46e52e77'],
  ['task:goat', 'pos:c:6c467a403479ac834b4f4b'],
  ['task:goat', 'pos:c:3ca63b00ad82d0661153fc'],
  ['task:audiogoal', 'pos:c:726ec5b1b3b78e1ec9e797'],
  ['task:audiopointgoal', 'pos:c:9b4cf09346206184728998'],
  ['task:person-finding-following', 'pos:c:7c201e0ac4eb4184d46981'],
  ['task:namo', 'pos:c:af8e70264c1e46c57945fa'],
  ['task:namo', 'pos:c:290e0f2dd412c7e52b5d5d'],
  ['task:comon', 'pos:c:2e0e443c1499f0b82aad01'],
];
const trackedSourceFiles = [
  'assets/navigation-product.js', 'assets/navigation-product-model.js',
  'assets/navigation-product.css', 'assets/navigation-content.js', 'assets/navigation-bootstrap.js',
  'scripts/navigation_product.py', 'scripts/navigation_transport.py',
  'scripts/navigation_research_map.py', 'scripts/navigation_native_trees.py',
  'data/navigation-product/model.json.gz', 'data/navigation-product/manifest.json',
  'tests/test_navigation_parallel_scopes.cjs',
];
const sourceSnapshot = () => Object.fromEntries(trackedSourceFiles.map(file => [file, crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')]));
const frozenSources = sourceSnapshot();
const generated = fs.mkdtempSync(path.join(os.tmpdir(), 'navigation-parallel-scopes-'));
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
      w.HTMLElement.prototype.scrollIntoView = function () {};
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

function node(x, id) {
  return x.d.getElementById('np-node-' + id);
}
function forest(x, tree) {
  assert.equal(x.a.getState().route.tree, tree, 'only the active local view may be inspected');
  const sections = [...x.d.querySelectorAll('#np-tree section[data-parallel-tree]')];
  assert.deepEqual(sections.map(section => section.dataset.parallelTree), [tree], 'the inactive forest is absent, not hidden');
  const section = x.d.querySelector('#np-tree section[data-parallel-tree="' + tree + '"]');
  assert.ok(section, 'active ' + tree + ' forest is present');
  for (let current = section; current; current = current.parentElement) {
    assert.equal(current.hidden, false, 'active forest has no hidden ancestor');
    assert.notEqual(x.w.getComputedStyle(current).display, 'none', 'active forest is not CSS-hidden');
    assert.notEqual(x.w.getComputedStyle(current).visibility, 'hidden', 'active forest is visible');
  }
  const items = [...x.d.querySelectorAll('#np-tree [role="treeitem"]')];
  assert.ok(items.every(item => item.dataset.tree === tree), 'one active scientific tree in the canvas');
  assert.equal(items.filter(item => item.tabIndex === 0).length, items.length ? 1 : 0, 'one roving keyboard domain');
  return section;
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
  x.w.history.back(); await wait(30); await frames(x.w);
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
async function overview(x) {
  x.d.querySelector('[data-tree-tab="g"]').click();
  await frames(x.w);
  assert.equal(x.a.getState().route.tree, 'g');
  assert.equal(x.d.querySelector('#np-reading-landing').hidden, false);
}
async function enterScope(x, sid, fromTaskIndex = false) {
  await overview(x);
  const selector = fromTaskIndex ? 'button[data-task-open="' + sid + '"]' : '#np-all-scopes button[data-scope-open="' + sid + '"]';
  const button = x.d.querySelector(selector);
  assert.ok(button, 'named scope control: ' + sid);
  revealDetails(button);
  button.focus();
  button.click();
  await frames(x.w);
  assert.equal(x.a.getState().route.scope, sid, 'clicked exact original scope: ' + sid);
  assert.equal(x.d.querySelector('#np-tree').dataset.parallelScope, sid);
  forest(x, x.a.getState().route.tree);
  return button;
}
function forestItems(x, tree) {
  return [...forest(x, tree).querySelectorAll('[role="treeitem"]')];
}
async function expandAll(x, sid, tree) {
  await switchLocalTree(x, tree);
  const expected = descendants(science.forests[sid][tree]);
  for (const id of expected) {
    let item = node(x, id);
    assert.ok(item, 'reachable after real parent expansions: ' + id);
    revealDetails(item);
    if (item.getAttribute('aria-expanded') === 'false') {
      item.querySelector(':scope > .np-node-row .np-node-toggle').click();
    }
  }
  await frames(x.w);
  return expected;
}
async function clickPosition(x, id) {
  const p = science.positions[id];
  assert.ok(p, 'click target belongs to the frozen scientific inventory');
  await switchLocalTree(x, p.tree);
  const pathIds = ancestorIds(id);
  for (const parentId of pathIds.slice(0, -1)) {
    const parent = node(x, parentId);
    assert.ok(parent, 'actual local ancestor is reachable: ' + parentId);
    revealDetails(parent);
    if (parent.getAttribute('aria-expanded') === 'false') {
      parent.querySelector(':scope > .np-node-row .np-node-toggle').click();
      await frames(x.w);
    }
  }
  const item = node(x, id);
  assert.ok(item, 'click target is present: ' + id);
  revealDetails(item);
  const button = item.querySelector(':scope > .np-node-row .np-node-label');
  button.focus();
  button.click();
  await frames(x.w);
  const route = x.a.getState().route;
  assert.equal(route.node, id);
  assert.equal(route.scope, p.scopeId);
  assert.equal(route.tree, p.tree);
  assert.equal(route.paper, p.paperId || null);
  assert.equal(route.version, p.versionId || null);
}
function assertTrueForest(x, sid, tree, complete = false) {
  const expected = descendants(science.forests[sid][tree]);
  const items = forestItems(x, tree), ids = items.map(item => item.dataset.position);
  assert.equal(new Set(ids).size, ids.length, sid + ': no duplicate position IDs');
  if (complete) assert.deepEqual(ids.slice().sort(), expected.slice().sort(), sid + ': complete ' + tree + ' forest');
  const roots = items.filter(item => !science.positions[item.dataset.position]?.parentId).map(item => item.dataset.position);
  assert.deepEqual(roots, science.forests[sid][tree], sid + ': exact original ' + tree + ' roots');
  for (const item of items) {
    const p = science.positions[item.dataset.position];
    assert.ok(p, 'no invented local scientific position: ' + item.dataset.position);
    assert.equal(p.scopeId, sid);
    assert.equal(p.tree, tree);
    assert.equal(item.dataset.parent, p.parentId || '', p.id + ': source parent');
    assert.equal(item.dataset.association, p.association || '', p.id + ': source association');
    assert.equal(item.dataset.entity, p.entityId, p.id + ': source entity');
    const actualParent = item.parentElement.closest('[role="treeitem"]');
    assert.equal(actualParent?.dataset.position || null, p.parentId, p.id + ': actual DOM ancestry');
    const row = item.querySelector(':scope > .np-node-row');
    assert.ok(row.querySelector('.np-node-label').textContent.trim(), p.id + ': named control');
    if (p.association === 'condition') assert.match(row.textContent, /条件/, p.id + ': nearby condition warning');
    if (p.association === 'context') assert.match(row.textContent, /跨范围|跨任务|背景/, p.id + ': context is not a task solution');
  }
  for (const edge of forest(x, tree).querySelectorAll('[data-child][data-parent]')) {
    const p = science.positions[edge.dataset.child];
    assert.ok(p, 'edge target comes from the frozen model');
    assert.equal(edge.dataset.parent, p.parentId);
    assert.equal(p.scopeId, sid);
    assert.equal(p.tree, tree);
  }
}
function assertLocalPath(x, id) {
  const p = science.positions[id];
  const host = x.d.querySelector('#np-global-context');
  assert.equal(host.dataset.pathKind, 'local-context');
  const local = host.querySelector('[data-path-kind="local-ancestry"]');
  assert.equal(local.dataset.tree, p.tree);
  assert.deepEqual([...local.querySelectorAll('[data-context-position]')].map(n => n.dataset.contextPosition), ancestorIds(id));
  assert.ok(!local.textContent.includes('Literature tree') || p.tree === 'l');
  const global = host.querySelector('[data-path-kind="global-entry"]');
  assert.ok(global, 'global reading links are separate from scientific ancestry');
  assert.equal(global.querySelector('.np-path-separator'), null);
  assert.equal(host.querySelector(':scope > .np-path-separator'), null);
}
async function contentReady(x, entityId) {
  for (let i = 0; i < 150 && !x.a.getContent().ready(entityId); i++) await wait(10);
  assert.ok(x.a.getContent().ready(entityId), 'exact entity packet finished: ' + entityId);
  await frames(x.w);
}

test('parallel presentation leaves the frozen scientific model and all original identities unchanged', async t => {
  assert.equal(crypto.createHash('sha256').update(scienceBytes).digest('hex'), SCIENCE_SHA);
  assert.equal(science.scopes.length, 64);
  assert.equal(Object.keys(science.positions).length, 1683);
  const x = await page(); t.after(() => x.w.close());
  const b = x.a.getBundle();
  assert.equal(b.delivery.sourceModelSha256, SCIENCE_SHA);
  assert.deepEqual(clean(b.scopes.map(s => s.id)), science.scopes.map(s => s.id));
  for (const [id, p] of Object.entries(science.positions)) assert.deepEqual(clean(b.positions[id]), p, id);
  assert.deepEqual(Object.values(b.positions).filter(p => p.tree !== 'g').map(p => p.id).sort(), Object.keys(science.positions).sort());
  for (const s of science.scopes) {
    for (const tree of ['l', 'c']) assert.deepEqual(clean(b.forests[s.id][tree]), science.forests[s.id][tree]);
    const candidate = b.scopes.find(row => row.id === s.id);
    for (const field of ['kind', 'parentScopeId', 'childScopeIds', 'crossReferenceTargetId']) assert.deepEqual(clean(candidate[field]), s[field]);
  }
  healthy(x);
});

test('fresh landing has no selected task and exposes the exact 22 named short contracts in retrieval order', async t => {
  const x = await page(); t.after(() => x.w.close());
  const landing = x.d.querySelector('#np-reading-landing');
  assert.ok(landing);
  assert.equal(landing.hidden, false);
  assert.equal(x.a.getState().route.tree, 'g');
  assert.equal(x.a.getState().route.scope, 'scope:all');
  assert.equal(x.a.getState().route.node, x.a.getBundle().researchMap.roots[0]);
  const controls = [...landing.querySelectorAll('button[data-task-open]')];
  assert.deepEqual(controls.map(n => n.dataset.taskOpen), TASK_INDEX.map(row => row[0]));
  for (const [sid, name, contract] of TASK_INDEX) {
    const control = controls.find(n => n.dataset.taskOpen === sid);
    assert.ok(control.textContent.includes(name), sid + ': visible short name');
    assert.ok(control.textContent.includes(contract), sid + ': visible distinguishing contract');
    assert.ok(control.getAttribute('aria-label')?.includes(scopeById.get(sid).label), sid + ': accessible full name');
    assert.notEqual(control.getAttribute('aria-current'), 'true');
    assert.notEqual(control.getAttribute('aria-selected'), 'true');
    assert.notEqual(control.getAttribute('aria-pressed'), 'true');
  }
  for (const text of ['给了什么信息', '怎样才算完成', '过程改变了什么', 'Literature', 'Challenge', '22', '全部阅读范围与术语']) assert.ok(landing.textContent.includes(text), text);
  assert.match(landing.textContent, /不是领域全集/);
  assert.equal(landing.querySelectorAll('[data-parent][data-child]').length, 0, 'navigation comparisons do not invent scientific parent edges');
  assert.equal(x.calls.length, 0, 'the complete overview needs no content fetch');
  assert.equal(x.d.querySelector('.np-panels').hidden, true, 'the legacy map is not presented as the fresh reading overview');
  const before = clean(x.a.getState().route);
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  assert.equal(x.d.querySelector('#np-reading-landing').hidden, true);
  assert.equal(x.d.querySelector('.np-panels').hidden, false);
  assert.deepEqual(clean(x.a.getState().route), before, 'changing a reading view does not create a scientific route');
  assert.equal(x.M.getBucket(x.a.getState()).originalMapOpen, true);
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  assert.equal(x.d.querySelector('#np-reading-landing').hidden, false);
  assert.equal(x.d.querySelector('.np-panels').hidden, true);
  assert.deepEqual(clean(x.a.getState().route), before);
  healthy(x);
});

test('cold explicit and historical g-root links keep the original map, while fresh entry and new overview snapshots stay distinct', async t => {
  const fresh = await page(); t.after(() => fresh.w.close());
  assert.equal(fresh.d.querySelector('#np-reading-landing').hidden, false);
  const route = clean(fresh.a.getState().route), hash = fresh.M.encodeRoute(route);
  const untouchedFreshHistory = clean(fresh.w.history.state);
  for (const reloadHash of ['', hash]) {
    const reload = await page({hash:reloadHash, saved:untouchedFreshHistory}); t.after(() => reload.w.close());
    assert.equal(reload.d.querySelector('#np-reading-landing').hidden, false, 'an untouched fresh overview must not be mistaken for historical original-map state');
    assert.equal(reload.d.querySelector('.np-panels').hidden, true);
    assert.deepEqual(clean(reload.a.getState().route), route);
    healthy(reload);
  }
  const legacySaved = clean(fresh.w.history.state);
  for (const bucket of Object.values(legacySaved[fresh.M.KEY].contexts)) {
    delete bucket.originalMapOpen;
    delete bucket.overviewView;
  }
  legacySaved.unrelatedOwnerField = 'legacy-global-owner';
  for (const oldHash of ['', hash]) {
    const legacy = await page({hash:oldHash, saved:legacySaved}); t.after(() => legacy.w.close());
    assert.deepEqual(clean(legacy.a.getState().route), route);
    assert.equal(legacy.d.querySelector('#np-reading-landing').hidden, true);
    assert.equal(legacy.d.querySelector('.np-panels').hidden, false);
    assert.equal(legacy.M.getBucket(legacy.a.getState()).originalMapOpen, true);
    assert.equal(legacy.w.history.state.unrelatedOwnerField, 'legacy-global-owner');
    healthy(legacy);
  }
  const cold = await page({hash}); t.after(() => cold.w.close());
  assert.equal(cold.d.querySelector('#np-reading-landing').hidden, true);
  assert.equal(cold.d.querySelector('.np-panels').hidden, false);
  const task = Object.values(cold.a.getBundle().researchMap.positions).find(p => p.sourceScopeId === 'task:pointnav' && p.sourceRootPositionIds);
  node(cold, task.id).querySelector('.np-node-label').click(); await frames(cold.w);
  assert.equal(cold.a.getState().route.node, task.id);
  cold.w.history.back(); await wait(30); await frames(cold.w);
  assert.deepEqual(clean(cold.a.getState().route), route);
  assert.equal(cold.d.querySelector('#np-reading-landing').hidden, true);
  assert.equal(cold.M.getBucket(cold.a.getState()).originalMapOpen, true);
  cold.d.querySelector('#np-catalog > summary').click();
  const scope = [...cold.d.querySelectorAll('#np-directory-list button')].find(button => button.textContent === scopeById.get('task:hieranav').label);
  assert.ok(scope); scope.focus(); scope.click(); await frames(cold.w);
  assert.equal(cold.a.getState().route.scope, 'task:hieranav');
  await assertBothLocalForests(cold, 'task:hieranav');
  cold.w.history.back(); await wait(30); await frames(cold.w);
  assert.deepEqual(clean(cold.a.getState().route), route);
  assert.equal(cold.d.querySelector('#np-reading-landing').hidden, true);
  assert.equal(cold.d.querySelector('.np-panels').hidden, false);
  healthy(fresh); healthy(cold);
});

test('each of the 22 main-task buttons enters one real local forest and switches to its exact companion view', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [sid] of TASK_INDEX) {
    await enterScope(x, sid, true);
    await assertBothLocalForests(x, sid);
    assert.ok(x.d.querySelector('#np-active-scope').textContent.includes(scopeById.get(sid).label));
  }
  healthy(x);
});

test('all 64 named scopes retain every actual local position, parent, role and association through real expansions', async t => {
  const x = await page(); t.after(() => x.w.close());
  const all = [...x.d.querySelectorAll('#np-all-scopes button[data-scope-open]')];
  assert.equal(all.length, 64);
  assert.deepEqual(all.map(n => n.dataset.scopeOpen).sort(), science.scopes.map(s => s.id).sort());
  assert.equal(new Set(all.map(n => n.dataset.scopeOpen)).size, 64);
  for (const control of all) {
    const source = scopeById.get(control.dataset.scopeOpen);
    assert.ok(control.textContent.includes(source.label), source.id + ': original scope name');
    assert.ok(control.textContent.includes(source.displayRole || source.kind), source.id + ': original role');
    const row = control.closest('[data-directory-scope]');
    assert.equal(row.dataset.parentScope, source.parentScopeId || '');
    assert.equal(row.parentElement.closest('[data-directory-scope]')?.dataset.directoryScope || null, source.parentScopeId);
  }
  const groups = [...x.d.querySelectorAll('#np-all-scopes [data-original-directory-group]')];
  assert.deepEqual(groups.map(n => n.dataset.originalDirectoryGroup), science.directoryGroups.map(g => g.id));
  for (const group of groups) {
    const source = science.directoryGroups.find(g => g.id === group.dataset.originalDirectoryGroup);
    assert.ok(group.querySelector('h4').textContent.includes(source.label));
    assert.equal(source.isScientificTaxonomy, false);
  }
  let checked = 0;
  for (const s of science.scopes) {
    await enterScope(x, s.id);
    for (const tree of ['l', 'c']) {
      checked += (await expandAll(x, s.id, tree)).length;
      assertTrueForest(x, s.id, tree, true);
    }
  }
  assert.equal(checked, Object.values(science.positions).filter(p => p.tree === 'l' || p.tree === 'c').length);
  t.diagnostic('Verified 64 scope entry clicks, 128 exact forests and ' + checked + ' original local positions.');
  healthy(x);
});

test('subordinate scopes, cross-reference identity and the virtual all-sources scope are not promoted or lost', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const [sid, parent] of [
    ['task:coin', 'task:interactive-instance-nav'],
    ['task:iign', 'task:interactive-instance-nav'],
    ['task:dialnav', 'task:remote-guide-dialog-navigation'],
    ['protocol:sequential-eqa', 'task:sequential-eqa'],
  ]) {
    assert.ok(!TASK_INDEX.some(row => row[0] === sid));
    assert.equal(scopeById.get(sid).parentScopeId, parent);
    await enterScope(x, parent);
    assert.equal(x.a.getBundle().scopes.find(s => s.id === parent).childScopeIds.includes(sid), true);
    await enterScope(x, sid);
    assert.equal(x.a.getBundle().scopes.find(s => s.id === sid).parentScopeId, parent);
  }
  await enterScope(x, 'task:av-question-answering');
  assert.equal(x.a.getState().route.scope, 'task:av-question-answering', 'alias does not replace original route identity');
  assert.equal(x.a.getBundle().scopes.find(s => s.id === 'task:av-question-answering').crossReferenceTargetId, 'task:active-eqa');
  await enterScope(x, 'scope:all');
  assert.equal(x.a.getBundle().scopes.find(s => s.id === 'scope:all').kind, 'reading_index');
  healthy(x);
});

test('all 11 CI positions absent from the entire global projection remain reachable through their real local C ancestry', async t => {
  const x = await page(); t.after(() => x.w.close());
  const missing = LOCAL_CI_WITHOUT_GLOBAL_PROJECTION;
  assert.equal(missing.length, 11);
  assert.equal(new Set(missing.map(row => row[0])).size, 9);
  assert.equal(new Set(missing.map(row => science.positions[row[1]].entityId)).size, 10);
  for (const [sid, id] of missing) {
    await enterScope(x, sid);
    await clickPosition(x, id);
    assertLocalPath(x, id);
    const p = science.positions[id];
    assert.equal(node(x, id).dataset.association, p.association);
    assert.deepEqual(clean(x.a.getBundle().positions[id].claimIds), p.claimIds);
    assert.ok(!Object.values(x.a.getBundle().researchMap.positions).some(g => g.entityId === p.entityId), 'no new g parent introduced for ' + id);
  }
  healthy(x);
});

test('condition-only and empty scopes show their own boundaries and never borrow another task to fill a gap', async t => {
  const x = await page(); t.after(() => x.w.close());
  for (const sid of ['task:pointnav', 'task:imagenav', 'task:language-objectnav', 'task:aerial-visual-object-search']) {
    await enterScope(x, sid);
    for (const tree of ['l', 'c']) {
      await expandAll(x, sid, tree);
      assertTrueForest(x, sid, tree, true);
      const children = descendants(science.forests[sid][tree]).filter(id => science.positions[id].parentId);
      if (!children.length) assert.match(forest(x, tree).textContent, /尚无|暂无|未整理|空覆盖/, sid + ': explicit ' + tree + ' gap');
      if (sid !== 'task:aerial-visual-object-search') for (const id of children) assert.equal(science.positions[id].association, 'condition');
    }
    if (sid === 'task:language-objectnav') assert.match(x.d.querySelector('#np-tree').textContent + x.d.querySelector('#np-reader-summary').textContent, /预建图|楼层|房间/);
  }
  await enterScope(x, 'task:pointnav');
  const cmp = Object.values(science.positions).find(p => p.scopeId === 'task:pointnav' && p.tree === 'l' && p.kind === 'pipeline_recipe');
  await clickPosition(x, cmp.id);
  await contentReady(x, cmp.entityId);
  assert.match(x.d.querySelector('.np-method-mechanism .np-reading-association').textContent, /条件关联/);
  assert.equal(x.a.getState().route.version, cmp.versionId);
  healthy(x);
});

test('selecting a method or insight does not auto-select a same-paper node or invent a cross-tree parent', async t => {
  const x = await page(); t.after(() => x.w.close());
  await enterScope(x, 'task:category-objectnav', true);
  const recipe = Object.values(science.positions).find(p => p.scopeId === 'task:category-objectnav' && p.tree === 'l' && p.paperId === 'poni' && p.kind === 'pipeline_recipe');
  const insight = Object.values(science.positions).find(p => p.scopeId === 'task:category-objectnav' && p.tree === 'c' && p.paperId === 'poni' && p.kind === 'insight' && p.association === 'direct');
  await clickPosition(x, recipe.id);
  const recipeRoute = clean(x.a.getState().route);
  assert.equal(forest(x, 'l').querySelectorAll('[aria-selected="true"]').length, 1);
  assert.equal(node(x, insight.id), null, 'same-paper CI is not mounted beside the selected method');
  await switchLocalTree(x, 'c');
  assert.notEqual(x.a.getState().route.node, insight.id, 'switching views does not auto-select a same-paper insight');
  await clickPosition(x, insight.id);
  const insightRoute = clean(x.a.getState().route);
  assert.equal(forest(x, 'c').querySelectorAll('[aria-selected="true"]').length, 1);
  assert.equal(node(x, recipe.id), null, 'inactive method tree is absent from the canvas');
  assertLocalPath(x, insight.id);
  assertTrueForest(x, 'task:category-objectnav', 'c');
  await switchLocalTree(x, 'l');
  assert.deepEqual(clean(x.a.getState().route), recipeRoute, 'L restores its own method, paper and version');
  assertTrueForest(x, 'task:category-objectnav', 'l');
  assertLocalPath(x, recipe.id);
  await switchLocalTree(x, 'c');
  assert.deepEqual(clean(x.a.getState().route), insightRoute, 'C restores its own insight, paper and version');
  assertTrueForest(x, 'task:category-objectnav', 'c');
  healthy(x);
});


test('active-tree keyboard expansion preserves scientific selection and keeps one roving tab stop while the other view is cached', async t => {
  const x = await page(); t.after(() => x.w.close());
  await enterScope(x, 'task:audiogoal', true);
  const literatureRoute = clean(x.a.getState().route);
  await switchLocalTree(x, 'c');
  const cRoot = science.forests['task:audiogoal'].c[0];
  const before = clean(x.a.getState().route);
  node(x, cRoot).focus();
  node(x, cRoot).dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'ArrowLeft', bubbles:true, cancelable:true}));
  await frames(x.w);
  assert.equal(node(x, cRoot).getAttribute('aria-expanded'), 'false');
  assert.deepEqual(clean(x.a.getState().route), before);
  node(x, cRoot).dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'ArrowRight', bubbles:true, cancelable:true}));
  await frames(x.w);
  assert.equal(node(x, cRoot).getAttribute('aria-expanded'), 'true');
  assert.deepEqual(clean(x.a.getState().route), before);
  node(x, cRoot).dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'ArrowDown', bubbles:true, cancelable:true}));
  assert.equal(x.d.activeElement.dataset.position, science.positions[cRoot].childIds[0]);
  assert.equal(x.d.activeElement.tabIndex, 0);
  assert.deepEqual(clean(x.a.getState().route), before);
  x.d.activeElement.dispatchEvent(new x.w.KeyboardEvent('keydown', {key:'Enter', bubbles:true, cancelable:true}));
  await frames(x.w);
  assert.equal(x.a.getState().route.node, science.positions[cRoot].childIds[0]);
  assert.equal(x.a.getState().route.tree, 'c');
  const challengeRoute = clean(x.a.getState().route);
  assert.equal(forest(x, 'c').querySelectorAll('[role="treeitem"][tabindex="0"]').length, 1);
  await switchLocalTree(x, 'l');
  assert.deepEqual(clean(x.a.getState().route), literatureRoute, 'C keyboard navigation leaves the cached L selection unchanged');
  await switchLocalTree(x, 'c');
  assert.deepEqual(clean(x.a.getState().route), challengeRoute);
  assert.equal(forest(x, 'c').querySelectorAll('[role="treeitem"][tabindex="0"]').length, 1);
  healthy(x);
});

test('AudioGoal real clicks, Back/Forward and global return restore exact identity, expansion, zoom, reader and canvas scroll, and focus', async t => {
  const x = await page(); t.after(() => x.w.close());
  await enterScope(x, 'task:audiogoal', true);
  const rootId = 'pos:c:dc5852b0f642613ffc3df7';
  const challenge = 'pos:c:726ec5b1b3b78e1ec9e797';
  const insight = 'pos:c:6dcc2ce43c02d908266f20';
  for (const id of [rootId, challenge, insight]) await clickPosition(x, id);
  assertLocalPath(x, insight);
  const reader = x.d.querySelector('#np-detail-scroll'), canvas = x.d.querySelector('#np-tree-scroll');
  assert.notEqual(reader, canvas);
  x.d.querySelector('#np-zoom-in').click();
  reader.scrollTop = 173;
  canvas.scrollTop = 61;
  canvas.scrollLeft = 27;
  node(x, insight).focus();
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.M.getBucket(x.a.getState()));
  assert.equal(saved.detailScrollByTree.c, 173);
  assert.equal(saved.treeScrollByTree.c, 61);
  assert.equal(saved.treeScrollLeftByTree.c, 27);
  assert.equal(saved.graphScale, 1.1);
  const crumb = x.d.querySelector('[data-path-kind="local-ancestry"] [data-context-position="' + challenge + '"]');
  crumb.click(); await frames(x.w);
  assert.equal(x.a.getState().route.node, challenge);
  x.w.history.back(); await wait(30); await frames(x.w);
  assert.equal(x.a.getState().route.node, insight);
  assert.equal(x.a.getState().route.paper, 'sound20');
  assert.equal(x.a.getState().route.version, 'arxiv:1912.11474v3');
  assert.equal(reader.scrollTop, 173);
  assert.equal(canvas.scrollTop, 61);
  assert.equal(canvas.scrollLeft, 27);
  assert.equal(x.M.getBucket(x.a.getState()).graphScale, 1.1);
  for (const tree of ['l', 'c']) assert.deepEqual(clean(x.M.getBucket(x.a.getState()).expandedByTree[tree]), saved.expandedByTree[tree]);
  assert.equal(x.d.activeElement.dataset.position, insight);
  assert.equal(x.d.activeElement.tabIndex, 0);
  assertLocalPath(x, insight);
  x.w.history.forward(); await wait(30); await frames(x.w);
  assert.equal(x.a.getState().route.node, challenge);
  x.w.history.back(); await wait(30); await frames(x.w);
  await overview(x);
  x.w.history.back(); await wait(30); await frames(x.w);
  assert.equal(x.a.getState().route.node, insight);
  assert.equal(reader.scrollTop, 173);
  assert.equal(canvas.scrollTop, 61);
  assert.equal(canvas.scrollLeft, 27);
  assert.equal(x.d.activeElement.dataset.position, insight);
  assertLocalPath(x, insight);
  healthy(x);
});

test('returning to the overview restores the actual main-task entry focus instead of focusing a hidden legacy node', async t => {
  const x = await page(); t.after(() => x.w.close());
  await enterScope(x, 'task:roomnav', true);
  await overview(x);
  const entry = x.d.querySelector('button[data-task-open="task:roomnav"]');
  assert.equal(x.d.activeElement, entry);
  assert.equal(x.d.querySelector('#np-reading-landing').contains(x.d.activeElement), true);
  healthy(x);
});

test('returning from a subordinate scope restores the named directory control inside an open disclosure', async t => {
  const x = await page(); t.after(() => x.w.close());
  await overview(x);
  const source = x.d.querySelector('#np-all-scopes button[data-scope-open="task:coin"]');
  revealDetails(source);
  x.d.querySelector('#np-reading-landing').scrollTop = 247;
  source.focus(); source.click(); await frames(x.w);
  assert.equal(x.a.getState().route.scope, 'task:coin');
  x.w.history.back(); await wait(30); await frames(x.w);
  assert.equal(x.a.getState().route.tree, 'g');
  assert.equal(x.d.querySelector('#np-reading-landing').hidden, false);
  const entry = x.d.querySelector('#np-all-scopes button[data-scope-open="task:coin"]');
  assert.equal(x.d.activeElement, entry);
  assert.equal(x.d.querySelector('#np-all-scopes').open, true, 'restored directory focus must not be hidden inside a closed disclosure');
  for (let p = entry.parentElement; p; p = p.parentElement) {
    assert.equal(p.hidden, false, 'restored focus has no hidden ancestor');
    if (p.tagName === 'DETAILS') assert.equal(p.open, true);
  }
  assert.equal(x.d.querySelector('#np-reading-landing').scrollTop, 247);
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const saved = clean(x.w.history.state), hash = x.M.encodeRoute(x.a.getState().route);
  const restored = await page({saved, hash}); t.after(() => restored.w.close());
  assert.equal(restored.d.querySelector('#np-reading-landing').scrollTop, 247, 'overview scroll must survive saved-history reload, not just a reused DOM element');
  assert.equal(restored.d.querySelector('#np-all-scopes').open, true);
  assert.equal(restored.d.activeElement, restored.d.querySelector('#np-all-scopes button[data-scope-open="task:coin"]'));
  healthy(x); healthy(restored);
});

test('the full 22-task comparison retains audited input, completion, boundaries and source links and restores its reading position', async t => {
  const x = await page(); t.after(() => x.w.close());
  const comparison = x.d.querySelector('#np-overview-comparison');
  assert.ok(comparison);
  comparison.querySelector(':scope > summary').click();
  assert.equal(comparison.open, true);
  const rows = [...comparison.querySelectorAll('[data-task-comparison]')];
  assert.deepEqual(rows.map(row => row.dataset.taskComparison), TASK_INDEX.map(row => row[0]));
  for (const row of rows) {
    const sid = row.dataset.taskComparison, expected = TASK_COMPARISON_FIELDS[sid];
    for (const key of ['inputSummary', 'completionSummary', 'boundary']) assert.ok(row.textContent.includes(expected[key]), sid + ': audited ' + key);
    assert.ok(row.textContent.includes(scopeById.get(sid).label));
    assert.ok(row.textContent.includes(scopeById.get(sid).displayRole));
    const hrefs = [...row.querySelectorAll('a[href]')].map(a => a.href);
    for (const url of expected.sourceURLs) assert.ok(hrefs.includes(url), sid + ': original source link ' + url);
  }
  x.d.querySelector('#np-reading-landing').scrollTop = 311;
  const source = comparison.querySelector('[data-task-comparison="task:namo"] button');
  source.focus(); source.click(); await frames(x.w);
  assert.equal(x.a.getState().route.scope, 'task:namo');
  x.w.history.back(); await wait(30); await frames(x.w);
  assert.equal(x.d.querySelector('#np-overview-comparison').open, true);
  assert.equal(x.d.querySelector('#np-reading-landing').scrollTop, 311);
  assert.equal(x.d.activeElement, x.d.querySelector('#np-overview-comparison [data-task-comparison="task:namo"] button'));
  x.w.dispatchEvent(new x.w.Event('pagehide'));
  const restored = await page({saved:clean(x.w.history.state), hash:x.M.encodeRoute(x.a.getState().route)}); t.after(() => restored.w.close());
  assert.equal(restored.d.querySelector('#np-overview-comparison').open, true);
  assert.equal(restored.d.querySelector('#np-reading-landing').scrollTop, 311);
  assert.equal(restored.d.activeElement, restored.d.querySelector('#np-overview-comparison [data-task-comparison="task:namo"] button'));
  healthy(x); healthy(restored);
});

test('all seven audited task relations expose their exact endpoints without becoming scientific tree edges', async t => {
  const x = await page(); t.after(() => x.w.close());
  const panel = x.d.querySelector('#np-task-relations');
  assert.ok(panel);
  panel.querySelector(':scope > summary').click();
  assert.equal(panel.open, true);
  assert.deepEqual([...panel.querySelectorAll('[data-task-relation]')].map(row => row.dataset.taskRelation).sort(), TASK_RELATIONS.map(row => row.id).sort());
  assert.equal(panel.querySelectorAll('[role="treeitem"], [data-child][data-parent]').length, 0);
  assert.equal(panel.querySelector('[data-task-relation="tasks:relation:87"]'), null, 'the VLN execution setting is not promoted to a 23rd task relation');
  for (const expected of TASK_RELATIONS) {
    assert.equal(expected.renderAsTree, false);
    for (const index of [0, 1]) {
      const row = x.d.querySelector('#np-task-relations [data-task-relation="' + expected.id + '"]');
      assert.equal(row.dataset.fromEntity, expected.from);
      assert.equal(row.dataset.toEntity, expected.to);
      assert.equal(row.dataset.relationType, expected.relationType);
      assert.ok(row.textContent.includes(expected.proposedLabel));
      const controls = [...row.querySelectorAll('button')], sid = index ? expected.to : expected.from;
      assert.equal(controls.length, 2);
      assert.ok(controls[index].textContent.includes(scopeById.get(sid).label));
      controls[index].focus(); controls[index].click(); await frames(x.w);
      assert.equal(x.a.getState().route.scope, sid);
      await assertBothLocalForests(x, sid);
      x.w.history.back(); await wait(20); await frames(x.w);
      assert.equal(x.d.querySelector('#np-task-relations').open, true);
      const restoredControl = x.d.querySelectorAll('#np-task-relations [data-task-relation="' + expected.id + '"] button')[index];
      assert.equal(x.d.activeElement, restoredControl, expected.id + ': exact endpoint focus after Back');
      assert.equal(restoredControl.id, 'np-relation-entry-' + expected.id + '-' + sid);
    }
  }
  healthy(x);
});

test('default skip targets the visible overview, and fullscreen exit stays reachable after returning from the original map', async t => {
  const x = await page(); t.after(() => x.w.close());
  x.d.querySelector('.np-skip').click(); await frames(x.w);
  assert.equal(x.d.activeElement.id, 'np-overview-heading');
  assert.equal(x.d.querySelector('#np-reading-landing').contains(x.d.activeElement), true);
  const route = clean(x.a.getState().route), workspace = x.d.querySelector('#np-workspace');
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  let entered = false, exited = false;
  Object.defineProperty(x.d, 'fullscreenElement', {configurable:true, value:null});
  workspace.requestFullscreen = function () {
    entered = true;
    Object.defineProperty(x.d, 'fullscreenElement', {configurable:true, value:workspace});
    x.d.dispatchEvent(new x.w.Event('fullscreenchange'));
    return Promise.resolve();
  };
  x.d.exitFullscreen = function () {
    exited = true;
    Object.defineProperty(x.d, 'fullscreenElement', {configurable:true, value:null});
    x.d.dispatchEvent(new x.w.Event('fullscreenchange'));
    return Promise.resolve();
  };
  x.d.querySelector('#np-graph-fullscreen').click();
  assert.equal(entered, true);
  x.d.querySelector('#np-overview-toggle').click(); await frames(x.w);
  const exit = x.d.querySelector('#np-graph-fullscreen');
  assert.equal(exit.textContent, '退出全屏');
  assert.equal(x.d.querySelector('#np-reading-landing').hidden, false);
  for (let p = exit; p; p = p.parentElement) {
    assert.equal(p.hidden, false, 'fullscreen exit has no hidden ancestor');
    assert.notEqual(x.w.getComputedStyle(p).display, 'none', 'fullscreen exit is not CSS-hidden');
  }
  assert.ok(workspace.contains(exit));
  assert.ok(workspace.contains(x.d.querySelector('#np-reading-landing')));
  exit.click();
  assert.equal(exited, true);
  assert.deepEqual(clean(x.a.getState().route), route);
  healthy(x);
});

test('delayed method content updates only its reading section while preserving exact source identity and focused tree DOM', async t => {
  const p = Object.values(science.positions).find(p => p.scopeId === 'task:category-objectnav' && p.tree === 'l' && p.paperId === 'poni' && p.kind === 'pipeline_recipe');
  let release;
  const x = await page({fetch: (url, bytes) => {
    if (JSON.parse(bytes).ownerId === p.entityId) return {ok:true, status:200, arrayBuffer:() => new Promise(resolve => { release = () => resolve(bytes); })};
    return {ok:true, status:200, arrayBuffer:async () => bytes};
  }});
  t.after(() => x.w.close());
  await enterScope(x, p.scopeId, true);
  await clickPosition(x, p.id);
  assert.equal(typeof release, 'function');
  const item = node(x, p.id), control = item.querySelector('.np-node-label');
  control.focus();
  x.d.querySelector('#np-detail-scroll').scrollTop = 144;
  const exactRoute = clean(x.a.getState().route);
  release();
  await contentReady(x, p.entityId);
  assert.equal(node(x, p.id), item);
  assert.equal(node(x, p.id).querySelector('.np-node-label'), control);
  assert.equal(x.d.activeElement, control);
  assert.equal(x.d.querySelector('#np-detail-scroll').scrollTop, 144);
  assert.deepEqual(clean(x.a.getState().route), exactRoute);
  assert.ok(x.d.querySelector('.np-method-mechanism .np-method-flow'));
  healthy(x);
});

const publishedHistory = require('./fixtures/navigation-pr53-history.json');
for (const [name, fixture] of Object.entries(publishedHistory.states)) {
  test('parallel reading preserves the exact published ' + name + ' deep-link and scrolling history', async t => {
    const x = await page({hash:fixture.urlHash, saved:fixture.history}); t.after(() => x.w.close());
    assert.deepEqual(clean(x.a.getState().route), fixture.history[x.M.KEY].route);
    assert.equal(x.d.querySelector('#np-tree-scroll').scrollTop, 123);
    assert.equal(x.d.querySelector('#np-detail-scroll').scrollTop, 570);
    assert.equal(x.w.scrollY, 1750);
    assert.equal(x.w.history.state.unrelatedOwnerField, 'preserve-me');
    if (['l', 'c'].includes(x.a.getState().route.tree)) {
      await assertBothLocalForests(x, x.a.getState().route.scope);
    }
    healthy(x);
  });
}
