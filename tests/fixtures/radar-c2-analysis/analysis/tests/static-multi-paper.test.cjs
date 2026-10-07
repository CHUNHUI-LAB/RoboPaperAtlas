'use strict';
// Read-only static contract tests. These complement, not replace, old HarnessVLN tests.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawnSync} = require('node:child_process');
const analysis = path.resolve(__dirname, '..');
const publicRoot = fs.existsSync(path.join(analysis, 'reading.html')) ? path.dirname(analysis) : path.resolve(analysis, '../../../../previews/radar-c2-analysis');
const load = name => JSON.parse(fs.readFileSync(path.join(analysis, 'data', name), 'utf8'));
const schema = load('method.json');
const mappings = {harnessvln:load('mapping.json'), navharness:load('navharness.mapping.json')};
const ledgers = {harnessvln:load('ledger.json'), navharness:load('navharness.ledger.json')};
const unknowns = {harnessvln:mappings.harnessvln.unresolvedQuestions, navharness:load('navharness.unknowns.json')};
const catalog = JSON.parse(fs.readFileSync(path.join(analysis, '../data/catalog.json'), 'utf8'));
const html = fs.readFileSync(path.join(publicRoot, 'analysis/reading.html'), 'utf8');
const esc = x => String(x).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"','&quot;').replaceAll("'",'&#x27;');
const unesc = x => x.replaceAll('&quot;','"').replaceAll('&#x27;',"'").replaceAll('&gt;','>').replaceAll('&lt;','<').replaceAll('&amp;','&');
const nodeAnchor = (pid,nid) => 'node-' + (pid === 'harnessvln' ? '' : pid+'-') + nid;
const article = id => {
  const start = html.indexOf('<article id="'+esc(id)+'"');
  assert(start >= 0, 'Missing article ' + id);
  const end = html.indexOf('</article>', start);
  assert(end > start, 'Unclosed article ' + id);
  return html.slice(start, end + 10);
};
const links = text => [...text.matchAll(/href="([^"]*)"/g)].map(m => unesc(m[1]));
const leaves = value => value && typeof value === 'object' ? Object.values(value).flatMap(leaves) : [value];
function retainedValues(record, rendered, description) {
  for (const value of leaves(record)) assert(rendered.includes(esc(value === null ? 'null' : value)), description + ': missing exact value '+value);
}
let checks = 0;
function test(name, fn) { fn(); checks++; console.log('PASS '+name); }

test('script-free reading exposes exactly39 canonical paper anchors and no duplicate DOM IDs', () => {
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(m=>unesc(m[1]));
  assert.equal(ids.length,new Set(ids).size);
  assert.equal(ids.filter(id=>id.startsWith('paper-')).length,39);
  for (const paper of catalog.papers) assert(ids.includes('paper-'+paper.canonical_id));
  assert(!/<(?:script|img|iframe|object|embed)\b/i.test(html));
  assert(html.includes('id="source-coverage"'));
  assert(html.includes('相关源码尚未阅读'));
  for(const target of links(html).filter(u=>u.startsWith('#'))) assert(ids.includes(target.slice(1)), 'Unresolved local link '+target);
});

test('both complete node inventories preserve schema labels, parentage and instance slots', () => {
  for (const [pid,mapping] of Object.entries(mappings)) {
    const nodes = [...schema.nodes, ...mapping.expandedNodes.map(n=>({...n,id:n.nodeId}))];
    assert.equal(nodes.length,pid === 'harnessvln' ? 72 :77);
    const actual = [...html.matchAll(/<article id="[^"]+" data-node-key="([^"]+)" data-paper-id="([^"]+)"/g)].filter(m=>m[2]===pid).map(m=>unesc(m[1]));
    assert.deepEqual(actual,nodes.map(n=>n.id));
    for (const n of nodes) {
      const rendered = article(nodeAnchor(pid,n.id));
      assert(rendered.includes(esc(n.labelOriginal)));
      if(n.parentId) assert(links(rendered).includes('#'+nodeAnchor(pid,n.parentId)));
      for(const key of ['repeatOfSchemaNode','expansionSlot']) if(n[key]) {
        assert(rendered.includes(key));assert(links(rendered).includes('#'+nodeAnchor(pid,n[key])));
      }
      const deep = links(rendered).find(l=>l.startsWith('../index.html#analysis='));
      const state = JSON.parse(decodeURIComponent(deep.split('#analysis=')[1]));
      assert.equal(state.paperId,pid);assert.equal(state.selected,n.id);
      assert.equal(state.focus,n.parentId||'paper-analysis-tree');
    }
  }
});

test('every complete answer, raw status and exact locator occurrence survives independently per paper', () => {
  for(const [pid,mapping] of Object.entries(mappings)) {
    let locatorCount =0;
    assert.equal(mapping.answers.length,pid === 'harnessvln' ? 47:51);
    const actualAnswers = [...html.matchAll(/data-answer-node="([^"]+)"/g)].map(m=>unesc(m[1]));
    for(const answer of mapping.answers) {
      const rendered = article(nodeAnchor(pid,answer.nodeId));
      assert(actualAnswers.includes(answer.nodeId));retainedValues(answer,rendered,pid+'/'+answer.nodeId);
      const locatorBlocks = [...rendered.matchAll(/<li data-source-locator="answer">(.*?)<\/li>/gs)];
      // Locators are flat except the optional pdfPages list. Read the exact source URL once per locator.
      const actualUrls = locatorBlocks.map(m=>links(m[1])[0]);
      assert.deepEqual(actualUrls,answer.sourceLocators.map(l=>l.sourceUrl),pid+'/'+answer.nodeId);
      locatorCount += actualUrls.length;
      for(const eid of answer.evidenceRecordIds||[]) assert(links(rendered).includes('#evidence-'+pid+'-'+eid));
      for(const uid of answer.sourceGapIds||[]) assert(links(rendered).includes('#unknown-'+pid+'-'+uid));
    }
    if(pid === 'navharness') assert.equal(locatorCount,724);
  }
  assert(html.includes('部分已报告，仍有缺口'));
});

test('all20 implementation-unknown answers keep raw codeEvidence and U02 links', () => {
  const records = mappings.navharness.answers.filter(a=>a.codeEvidence.status==='not_reviewed_implementation_unknown');
  assert.equal(records.length,20);
  for(const answer of records) {
    const rendered = article(nodeAnchor('navharness',answer.nodeId));
    assert(rendered.includes('data-field="sourceKind"'));
    assert(rendered.includes('data-field="codeEvidence"'));
    retainedValues(answer.codeEvidence,rendered,answer.nodeId+' codeEvidence');
    assert(links(rendered).includes('#unknown-navharness-U02'));
  }
  assert(html.includes('0 条实现已核验'));
});

test('all12 unknown records preserve raw fields and only original answer relationships', () => {
  assert.equal(unknowns.navharness.length,12);
  for(const q of unknowns.navharness) {
    const rendered = article('unknown-navharness-'+q.id);
    retainedValues(q,rendered,q.id);
    for(const url of q.sourceUrls||[]) assert(links(rendered).includes(url));
    for(const eid of q.evidenceRecordIds||[]) assert(links(rendered).includes('#evidence-navharness-'+eid));
    const expected = mappings.navharness.answers.filter(a=>(a.sourceGapIds||[]).includes(q.id)).map(a=>'#'+nodeAnchor('navharness',a.nodeId));
    assert.deepEqual(links(rendered).filter(u=>u.startsWith('#node-')),expected,q.id+' answer backlinks');
    assert(!rendered.includes('data-node-key='));
  }
  const u12=article('unknown-navharness-U12');
  assert(links(u12).includes('https://arxiv.org/pdf/2609.34276v1#page=39'));
  assert(u12.includes('Figure18(p39)'));assert(u12.includes('task34'));assert(u12.includes('多11步'));
  assert(u12.includes('全篇层级未知项'));
});

test('all source ledger values survive with local paper evidence namespaces', () => {
  assert.equal(ledgers.navharness.records.length,31);
  for(const [pid,ledger] of Object.entries(ledgers)) for(const record of ledger.records) {
    const eid=record.id||record.evidenceRecordId, rendered=article('evidence-'+pid+'-'+eid);
    retainedValues(record,rendered,pid+'/'+eid);
    for(const locator of record.sourceLocators) {
      assert(links(rendered).includes(locator.sourceUrl));
      if(locator.htmlAnchor) assert(links(rendered).includes(locator.htmlAnchor));
    }
    if(pid==='navharness') {assert.equal(record.independentlyReproduced,false);assert(rendered.includes('false'));}
  }
});

test('all static entry counters derive two supported and37 pending without Adaptive Goals identity leakage', () => {
  const supported=Object.keys(mappings).filter(id=>catalog.papers.some(p=>p.canonical_id===id));
  assert.equal(supported.length,2);assert.equal(catalog.papers.length-supported.length,37);
  for(const name of ['index.html','all-papers.html','harnessvln.html','analysis/reading.html']) {
    const page=fs.readFileSync(path.join(publicRoot,name),'utf8');
    assert(page.includes('2 篇有内容视图、37 篇待填'),name);
    assert(page.includes('data-c2-range="baseline-weekly"'));
    assert(page.includes('4 篇 weekly 独有候选未进入本次重构双树或论文解析'));
  }
  const pending=article('paper-arxiv:2609.39915');
  assert(pending.includes('解析树尚未建立'));
  assert.equal(mappings.navharness.sourceVersion,'2609.34276v1');
  const all=fs.readFileSync(path.join(publicRoot,'all-papers.html'),'utf8');
  assert.equal((all.match(/<article id="paper-/g)||[]).length,39);
  assert(!/<script\b/.test(all));
  for(const pid of supported) assert(links(all).includes('analysis/reading.html#paper-'+pid));
});

test('static generation reproduces all four reviewed pages without writing source', () => {
  const files=['index.html','harnessvln.html','all-papers.html','analysis/reading.html'];
  const before=files.map(f=>fs.readFileSync(path.join(publicRoot,f)));
  const run=spawnSync('python',[path.join(analysis,'build_reading.py'),'--source-dir',analysis,'--output-dir',publicRoot,'--check'],{encoding:'utf8'});
  assert.equal(run.status,0,run.stdout+run.stderr);
  assert.match(run.stdout,/PASS deterministic/);
  files.forEach((f,i)=>assert.deepEqual(fs.readFileSync(path.join(publicRoot,f)),before[i]));
});
console.log('PASS '+checks+' script-free multi-paper checks; real-browser behavior remains NOT_RUN');
