const fs=require('fs'),vm=require('vm'),assert=require('assert/strict');
const base=require('path').resolve(__dirname,'..')+'/';
const els=new Map(),listeners={};
function el(id){if(!els.has(id))els.set(id,{id,innerHTML:'',value:'',hidden:false,scrollTop:0,classList:{toggle(){}},setAttribute(){},closest(){return null},focus(){},scrollIntoView(){},addEventListener(){}});return els.get(id)}
const document={getElementById:el,addEventListener:(k,fn)=>listeners[k]=fn,querySelectorAll:()=>[]};const errors=[];
const window={location:{hash:''},history:{pushState(){},replaceState(){}},matchMedia:()=>({matches:false}),addEventListener(){},scrollTo(){}};
const context={window,document,console:{error:e=>errors.push(String(e))}};
for(const f of ['data/catalog.js','data/literature.js','data/challenge.js','model.js','app.js'])vm.runInNewContext(fs.readFileSync(base+f,'utf8'),context);
el('c2-app').hidden=true;assert.deepEqual(errors,[]);const M=window.TreeModel,nav=window.NavigationPrototype,m=nav.model;
assert.equal(m.papers.size,39);assert.equal(M.validate(m).length,0);
const dataBefore=JSON.stringify([window.PAPER_CATALOG,window.LITERATURE_TREE,window.CHALLENGE_TREE]);
assert.equal(M.rootOverview(m,'l','pipeline').length,19);assert.equal(M.rootOverview(m,'c').length,12);
assert.equal((el('global-map').innerHTML.match(/class="atlas-vertex atlas-root /g)||[]).length,31);
assert(!el('tree-l').hidden&&el('tree-c').hidden&&el('paper-panel').hidden);assert(el('tree-l').innerHTML.includes('focus-empty'));
assert.equal(nav.getState().globalTree,'l');
const panelTag=key=>el('global-map').innerHTML.match(new RegExp('<section id="global-panel-'+key+'"[^>]*>'))[0];
assert(!panelTag('l').includes('hidden'));assert(panelTag('c').includes('hidden'));
assert(el('global-map').innerHTML.includes('19 个任务'));
nav.dispatch({type:'globalTree',key:'c'});assert.equal(nav.getState().globalTree,'c');assert(panelTag('l').includes('hidden'));assert(!panelTag('c').includes('hidden'));
assert.equal(M.deserialize(m,M.serialize(nav.getState())).globalTree,'c');
nav.dispatch({type:'globalTree',key:'l'});assert.equal(nav.getState().globalTree,'l');
assert.equal(M.sanitizeState(m,{globalTree:'not-a-tree'}).globalTree,'l');

for(const key of ['l','c']){
 for(const root of M.rootOverview(m,key,key==='l'?'pipeline':undefined)){
  nav.dispatch({type:'root',key,id:root.node.id});assert.equal(nav.getState()[key][0],root.node.id);assert(!el('tree-'+key).hidden);
  assert(!el('global-map').hidden);assert(el('branch-rail').hidden);
  assert.equal((el('global-map').innerHTML.match(/class="atlas-vertex atlas-root /g)||[]).length,31);
  const actual=new Set(M.matchingPaths(m.trees[key],[root.node.id],key==='l'?'pipeline':undefined).map(p=>p.paperId));assert.equal(actual.size,root.paperIds.length);
 }
}
for(const facet of ['pipeline','representation']){
 nav.dispatch({type:'facet',facet});assert.equal(M.rootOverview(m,'l',facet).length,19);
 for(const path of m.trees.l.paths.filter(p=>p.viewKind===facet)){
  nav.dispatch({type:'path',key:'l',id:path.id});assert.equal(nav.getState().paper,path.paperId);assert.equal(nav.getState().l[0],path.nodeIds[0]);assert.equal(nav.getState().lFacet,facet);
  assert(!el('paper-panel').hidden);assert(!el('global-map').hidden);
  const restored=M.deserialize(m,M.serialize(nav.getState()));assert.deepEqual(JSON.parse(JSON.stringify(restored)),JSON.parse(JSON.stringify(nav.getState())));
 }
}
for(const path of m.trees.l.paths.filter(p=>p.viewKind==='protocol')){nav.dispatch({type:'path',key:'l',id:path.id});assert.equal(nav.getState().paper,path.paperId);assert.equal(nav.getState().l[0],path.nodeIds[0]);}
for(const path of m.trees.c.paths){nav.dispatch({type:'path',key:'c',id:path.id});assert.equal(nav.getState().paper,path.paperId)}
nav.dispatch({type:'paper',id:'harnessvln'});nav.dispatch({type:'tab',tab:'paths'});assert(el('paper-panel').innerHTML.includes('HarnessVLN'));
nav.dispatch({type:'overview'});assert.equal(nav.getState().paper,null);assert(el('paper-panel').hidden);assert(!el('tree-l').hidden&&el('tree-c').hidden);assert(el('tree-l').innerHTML.includes('focus-empty'));
nav.dispatch({type:'root',key:'l',id:'fake-root'});assert.equal(nav.getState().l.length,0);
nav.dispatch({type:'root',key:'l',id:'task-vln-ce'});nav.dispatch({type:'facet',facet:'representation'});assert.equal(nav.getState().l[0],'task-vln-ce');
nav.dispatch({type:'search',query:'harnessvln'});assert(!el('catalog-panel').hidden);assert(el('global-map').hidden);assert(M.catalogResults(m,'harnessvln').some(p=>p.canonical_id==='harnessvln'));
nav.dispatch({type:'global'});assert(!el('global-map').hidden);assert(el('branch-rail').hidden);assert.equal(JSON.stringify([window.PAPER_CATALOG,window.LITERATURE_TREE,window.CHALLENGE_TREE]),dataBefore);
nav.dispatch({type:'root',key:'l',id:'task-object-open'});assert(el('tree-l').innerHTML.includes('有任务 / 协议来源记录 · 首创未核实'));assert(!el('tree-l').innerHTML.includes('作者限定的首创声明'));assert(el('tree-l').innerHTML.includes('不授予所有开放词汇导航首创'));
for(const [id,name] of [['task-vln-iterative','IVLN'],['task-goat-sequence','GOAT-Bench'],['task-open-eqa-active','OpenEQA'],['task-open-eqa-memory','OpenEQA']]){nav.dispatch({type:'root',key:'l',id});assert(el('tree-l').innerHTML.includes(name));assert(el('tree-l').innerHTML.includes('任务 / 协议来源记录'));assert(!el('tree-l').innerHTML.includes('原始定义来源待核'));}
nav.dispatch({type:'back',key:'l'});assert(!el('tree-l').hidden);assert(el('tree-l').innerHTML.includes('focus-empty'));assert(!el('global-map').hidden);
// Purpose switching preserves both paths; returning to overview clears only the active path and evidence.
nav.dispatch({type:'root',key:'l',id:'task-vln-ce'});
const challengeRoot=M.rootOverview(m,'c')[0].node.id;
nav.dispatch({type:'root',key:'c',id:challengeRoot});
nav.dispatch({type:'paper',id:'harnessvln'});
const selectedBefore=JSON.stringify([nav.getState().l,nav.getState().c,nav.getState().paper]);
for(const key of ['l','c','l']){nav.dispatch({type:'globalTree',key});assert.equal(nav.getState().globalTree,key);assert.equal(JSON.stringify([nav.getState().l,nav.getState().c,nav.getState().paper]),selectedBefore);assert(!panelTag(key).includes('hidden'));assert(panelTag(key==='l'?'c':'l').includes('hidden'));}
const preservedChallenge=JSON.stringify(nav.getState().c);nav.dispatch({type:'global'});assert.equal(nav.getState().l.length,0);assert.equal(nav.getState().paper,null);assert.equal(JSON.stringify(nav.getState().c),preservedChallenge);
// Keyboard global tabs do not change the unrelated paper tab.
let prevented=false;const oldPaperTab=nav.getState().tab;
listeners.keydown({key:'ArrowRight',preventDefault(){prevented=true},target:{closest(){return {dataset:{action:'globalTree'}}}}});
assert(prevented);assert.equal(nav.getState().globalTree,'c');assert.equal(nav.getState().tab,oldPaperTab);
assert.deepEqual(errors,[]);
console.log(JSON.stringify({passed:true,roots:31,literaturePaths:m.trees.l.paths.length,challengePaths:m.trees.c.paths.length,catalog:m.papers.size,coverage:M.coverage(m),kind:'Model + captured DOM markup, not browser layout'}));
