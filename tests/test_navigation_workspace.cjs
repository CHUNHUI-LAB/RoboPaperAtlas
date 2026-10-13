'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),crypto=require('node:crypto');
const {JSDOM,VirtualConsole,ResourceLoader}=require('jsdom'),root=path.resolve(__dirname,'..');
const html=cp.execFileSync('python3',['-c',"import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;r=Path('.').resolve();print(p.render(r,p.payloads(r)[1]))"],{cwd:root,encoding:'utf8',maxBuffer:20e6});
const frames=w=>new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)));
async function page(width,stallChrome=false,height){const errors=[],external=[],vc=new VirtualConsole();class StalledChrome extends ResourceLoader{fetch(url){external.push(url);const request=new Promise(()=>{});request.abort=()=>{};return request;}}vc.on('jsdomError',e=>errors.push(e.message));const d=new JSDOM(html,{url:'https://example.org/RoboPaperAtlas/research/navigation/',runScripts:'dangerously',resources:stallChrome?new StalledChrome():undefined,pretendToBeVisual:true,virtualConsole:vc,beforeParse(w){w.innerWidth=width;if(height)w.innerHeight=height;w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;Object.defineProperty(w.crypto,'subtle',{value:crypto.webcrypto.subtle});w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.fetch=()=>new Promise(()=>{});}});for(let i=0;i<100&&!d.window.NavigationProductApp;i++)await new Promise(r=>setTimeout(r,15));assert.ok(d.window.NavigationProductApp);await frames(d.window);return {w:d.window,d:d.window.document,errors,external};}
for(const width of [390,768,1024])test('compact '+width+' switches real tree and reader panes while preserving exact route, nodes and offsets',async t=>{
 const x=await page(width);t.after(()=>x.w.close());const {w,d}=x,a=w.NavigationProductApp,M=w.NavigationProductModel,b=a.getBundle(),p=Object.values(b.positions).find(p=>p.tree==='l'&&p.scopeId==='task:category-objectnav'&&p.paperId==='poni'&&p.kind==='pipeline_recipe');
 a.navigate(M.routeForPosition(b,{scope:p.scopeId},p.id),{cross:true});await frames(w);
 const tree=d.getElementById('np-tree-scroll'),reader=d.getElementById('np-detail-scroll'),node=d.getElementById('np-node-'+p.id),forest=d.getElementById('np-tree'),route=JSON.stringify(a.getState().route),hash=w.location.hash,length=w.history.length,expanded=JSON.stringify(M.getBucket(a.getState()).expandedByTree);
 tree.scrollTop=83;tree.scrollLeft=27;d.getElementById('np-panel-reader').click();
 assert.equal(d.getElementById('np-tree-pane').hidden,true);assert.equal(reader.hidden,false);assert.equal(d.getElementById('np-panel-reader').getAttribute('aria-selected'),'true');assert.equal(d.activeElement.id,'np-panel-reader');reader.scrollTop=247;
 // Display:none can report zero offsets; that must not erase the inactive pane anchor.
 tree.scrollTop=0;tree.scrollLeft=0;d.getElementById('np-panel-tree').click();assert.equal(tree.scrollTop,83);assert.equal(tree.scrollLeft,27);assert.equal(reader.hidden,true);reader.scrollTop=0;w.dispatchEvent(new w.Event('pagehide'));
 d.getElementById('np-panel-reader').dispatchEvent(new w.KeyboardEvent('keydown',{key:'End',bubbles:true,cancelable:true}));assert.equal(reader.scrollTop,247);assert.equal(d.getElementById('np-tree'),forest);assert.equal(d.getElementById('np-node-'+p.id),node);assert.equal(JSON.stringify(a.getState().route),route);assert.equal(w.location.hash,hash);assert.equal(w.history.length,length);assert.equal(JSON.stringify(M.getBucket(a.getState()).expandedByTree),expanded);
 assert.match(d.getElementById('np-selection-context').textContent,/当前任务.*ObjectNav.*当前路线.*当前论文.*PONI.*来源版本/s);assert.ok(d.title.includes('PONI'));assert.deepEqual(x.errors,[]);
});
test('mobile task entry overview keeps every scientific entry reachable without desktop coordinates',async t=>{
 const x=await page(390);t.after(()=>x.w.close());const {d,w}=x,map=d.getElementById('np-overview-map'),a=w.NavigationProductApp,b=a.getBundle();assert.ok(map.classList.contains('np-compact-overview'));assert.equal(map.querySelectorAll('[data-task-open]').length,22);assert.equal(map.querySelectorAll('[data-challenge-open]').length,13);assert.equal(d.getElementById('np-map-relations-toggle').hidden,true);for(const node of map.querySelectorAll('.np-map-node')){assert.equal(node.style.left,'');assert.equal(node.style.width,'');}const task=map.querySelector('[data-task-open="task:category-objectnav"]');assert.ok(task);task.click();await frames(w);assert.equal(a.getState().route.scope,'task:category-objectnav');assert.equal(d.getElementById('np-panel-tree').getAttribute('aria-selected'),'true');assert.ok(d.querySelectorAll('#np-tree [role=treeitem]').length>1);assert.deepEqual(x.errors,[]);
});
test('desktop restoration shows both panes and preserves a selected compact reader',async t=>{
 const x=await page(768);t.after(()=>x.w.close());const {w,d}=x,a=w.NavigationProductApp,b=a.getBundle(),M=w.NavigationProductModel,p=Object.values(b.positions).find(p=>p.tree==='c'&&p.scopeId==='task:category-objectnav'&&p.paperId==='poni'&&p.kind==='insight');a.navigate(M.routeForPosition(b,{scope:p.scopeId},p.id));await frames(w);d.getElementById('np-panel-reader').click();d.getElementById('np-detail-scroll').scrollTop=174;w.innerWidth=1440;w.dispatchEvent(new w.Event('resize'));await frames(w);assert.equal(d.getElementById('np-tree-pane').hidden,false);assert.equal(d.getElementById('np-reading-pane').hidden,false);assert.equal(d.querySelector('.np-mobile-panels').hidden,true);assert.equal(d.getElementById('np-detail-scroll').scrollTop,174);w.innerWidth=768;w.dispatchEvent(new w.Event('resize'));await frames(w);assert.equal(d.getElementById('np-tree-pane').hidden,true);assert.equal(d.getElementById('np-panel-reader').getAttribute('aria-selected'),'true');assert.equal(a.getState().route.node,p.id);assert.deepEqual(x.errors,[]);
});

test('scientific workspace starts while optional chrome stylesheet and scripts are permanently stalled',async t=>{const x=await page(1440,true);t.after(()=>x.w.close());assert.equal(x.d.readyState,'loading','optional deferred resources remain pending');assert.equal(x.d.getElementById('navigation-product').dataset.loadState,'ready');assert.ok(x.w.NavigationProductApp);assert.ok(x.d.querySelectorAll('#np-tree [role=treeitem]').length>1);assert.deepEqual(new Set(x.external.map(url=>new URL(url).pathname.split('/').at(-1))),new Set(['site.css','catalog-navigation.js','presentation.js','interface.js','chrome.js']));assert.deepEqual(x.errors,[]);});

test('selection identity preserves actual task, condition, protocol and index roles', async t => {
 const {w,d,errors}=await page(1440);t.after(()=>w.close());
 const a=w.NavigationProductApp,M=w.NavigationProductModel,b=a.getBundle();
 const expected=[['task:category-objectnav','当前任务'],['setting:portable-objectnav','当前条件扩展'],['setting:open-vocabulary-objectnav','当前条件扩展'],['protocol:sequential-eqa','当前评估协议'],['scope:all','当前虚拟阅读索引']];
 for(const [id,role] of expected){
  a.navigate(M.initialState(b,{scope:id,tree:'l',mode:'tree'}).route);await frames(w);
  const field=d.querySelector('#np-selection-context .np-context-field');
  assert.equal(field.querySelector('dt').textContent,role,id);
  assert.equal(field.querySelector('dd').textContent,b.scopes.find(s=>s.id===id).label,id);
 }
 assert.deepEqual(errors,[]);
});

for(const width of [1165,1180,1440,1920])test('desktop '+width+' returns from HAMT to the exact VLN pane, focus and reading position', async t => {
 const {w,d,errors}=await page(width,false,width===1180?757:width===1440?900:1080);t.after(()=>w.close());
 const a=w.NavigationProductApp,M=w.NavigationProductModel,b=a.getBundle(),plain=value=>JSON.parse(JSON.stringify(value));
 let pageY=0;Object.defineProperty(w,'scrollY',{configurable:true,get:()=>pageY});
 w.scrollTo=(x,y)=>{pageY=typeof x==='object'?x.top:y;};
 const taskRoute=M.initialState(b,{scope:'task:vln',tree:'l',mode:'tree'}).route;
 a.navigate(taskRoute,{cross:true});await frames(w);
 const tree=d.getElementById('np-tree-scroll'),reader=d.getElementById('np-detail-scroll');
 tree.scrollTop=219;tree.scrollLeft=11;pageY=width<1200?180:0;
 const taskNode=d.getElementById('np-node-'+taskRoute.node);taskNode.focus({preventScroll:true});
 w.dispatchEvent(new w.Event('pagehide'));
 const taskSnapshot=plain(w.history.state),taskHash=w.location.hash;
 const method=Object.values(b.positions).find(p=>p.tree==='l'&&p.scopeId==='task:vln'&&p.paperId==='hamt'&&p.kind==='pipeline_recipe');
 assert.ok(method);
 a.navigate(M.routeForPosition(b,{scope:'task:vln'},method.id),{cross:true});await frames(w);
 if(width<1200)d.getElementById('np-panel-reader').click();
 reader.scrollTop=271;pageY=width<1200?500:0;w.dispatchEvent(new w.Event('pagehide'));
 const methodSnapshot=plain(w.history.state),methodHash=w.location.hash;
 d.querySelector('.np-return-previous').click();await frames(w);
 const assertTask=()=>{
  assert.equal(M.encodeRoute(a.getState().route),M.encodeRoute(taskRoute));
  assert.equal(d.getElementById('np-tree-pane').hidden,false);
  assert.equal(d.getElementById('np-reading-pane').hidden,width<1200);
  if(width<1200)assert.equal(d.getElementById('np-panel-tree').getAttribute('aria-selected'),'true');
  assert.equal(tree.scrollTop,219);assert.equal(tree.scrollLeft,11);assert.equal(pageY,width<1200?180:0);
  assert.equal(d.activeElement.id,'np-node-'+taskRoute.node);
 };
 assertTask();
 // Replay exact browser-history entries in both directions, independently of the return button.
 w.history.replaceState(methodSnapshot,'',methodHash);w.dispatchEvent(new w.PopStateEvent('popstate'));await frames(w);
 assert.equal(a.getState().route.node,method.id);assert.equal(reader.scrollTop,271);assert.equal(pageY,width<1200?500:0);
 assert.equal(d.getElementById('np-reading-pane').hidden,false);
 assert.equal(d.getElementById('np-tree-pane').hidden,width<1200);
 w.history.replaceState(taskSnapshot,'',taskHash);w.dispatchEvent(new w.PopStateEvent('popstate'));await frames(w);assertTask();
 assert.deepEqual(Object.keys(a.getState().route).sort(),Object.keys(taskRoute).sort(),'presentation adds no route fields');
 assert.deepEqual(errors,[]);
});

test('compact pane snapshots are optional, bounded UI state and cannot alter scientific routes', async t => {
 const {w,d}=await page(1180,false,757);t.after(()=>w.close());
 const a=w.NavigationProductApp,M=w.NavigationProductModel,b=a.getBundle(),clone=value=>JSON.parse(JSON.stringify(value));
 a.navigate(M.initialState(b,{scope:'task:vln',tree:'l',mode:'tree'}).route);await frames(w);
 d.getElementById('np-panel-reader').click();w.dispatchEvent(new w.Event('pagehide'));
 const saved=clone(a.getState()),route=clone(saved.route);
 assert.equal(M.getBucket(saved).compactPanelByTree.l,'reader');assert.doesNotThrow(()=>M.validateState(b,saved));
 for(const invalid of [null,[],{l:'both'},{x:'tree'},{l:1}]){
  const bad=clone(saved);M.getBucket(bad).compactPanelByTree=invalid;
  assert.throws(()=>M.validateState(b,bad),/阅读面板/);
 }
 const legacy=clone(saved);for(const bucket of Object.values(legacy.contexts))delete bucket.compactPanelByTree;
 for(const entry of legacy.originTrail)delete entry.bucket.compactPanelByTree;
 assert.doesNotThrow(()=>M.validateState(b,legacy));
 w.history.replaceState(M.mergeHistory(w.history.state,legacy),'',M.encodeRoute(route));w.dispatchEvent(new w.PopStateEvent('popstate'));await frames(w);
 assert.equal(d.getElementById('np-tree-pane').hidden,false,'old snapshots fall back to the visible research tree');
 assert.deepEqual(clone(a.getState().route),route);
});
