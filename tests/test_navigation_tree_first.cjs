'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),cp=require('node:child_process'),{JSDOM}=require('jsdom');
const root=path.resolve(__dirname,'..');
const html=cp.execFileSync('python3',['-c',"import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;r=Path('.').resolve();print(p.render(r,p.payloads(r)[1]))"],{cwd:root,encoding:'utf8',maxBuffer:12e6});
test('tree-first document keeps current scope and all research entries before actual workspace',()=>{
 const d=new JSDOM(html),doc=d.window.document;tCleanup(d,()=>{
 const before=(a,b)=>!!(a.compareDocumentPosition(b)&4),workspace=doc.querySelector('#np-workspace'),conditions=doc.querySelector('#np-task-conditions');
 assert.ok(before(doc.querySelector('#np-active-scope'),workspace));
 assert.ok(before(workspace,conditions));assert.equal(conditions.open,false);
 for(const id of ['np-scope-summary','np-coverage-summary','np-benchmark','np-protocol','np-benchmark-summary'])assert.ok(conditions.contains(doc.getElementById(id)),id+' remains present in disclosure');
 assert.equal(doc.querySelector('#np-common'),null,'preferred-six picker is retired');
 assert.match(doc.querySelector('#np-catalog summary').textContent,/查找具体任务/);
 assert.ok(before(doc.querySelector('#np-catalog'),workspace));
 assert.match(doc.querySelector('#np-global-index').textContent,/来源与论文/);
 assert.ok(doc.querySelector('.np-identity-controls').contains(doc.querySelector('#np-paper')));
 assert.ok(doc.querySelector('.np-identity-controls').contains(doc.querySelector('#np-version')));
 assert.ok(doc.querySelector('.np-tree-options').contains(doc.querySelector('#np-node-search')));
 assert.equal(doc.querySelectorAll('.np-tabs [data-tree-tab]').length,3);assert.ok(doc.querySelector('.np-identity-controls [data-tree-tab="a"]'),'analysis is evidence drilldown');
 assert.equal(doc.querySelectorAll('[id]').length,new Set([...doc.querySelectorAll('[id]')].map(x=>x.id)).size,'all controller IDs remain unique');
 });
});
function tCleanup(d,fn){try{fn();}finally{d.window.close();}}
test('tree-first layout preserves complete content and static failure reading',()=>{
 const d=new JSDOM(html);tCleanup(d,()=>{const doc=d.window.document;
 for(const id of ['np-static-reading','np-retry','np-loading','np-origin-trail','np-version-note','np-share-link','np-copy-link','np-detail-content','np-method-comparison','np-coverage-table'])assert.ok(doc.getElementById(id),id);
 assert.equal(doc.querySelector('#np-workspace').hidden,true);
 assert.ok(doc.querySelector('a[href*="tree%3Dg"],a[href*="tree=g"]')); assert.ok(doc.querySelector('a[href="../../review/radar-c2-analysis/index.html"]'));
 assert.match(doc.querySelector('#np-task-conditions').textContent,/定义、边界、协议与原文/);
 });
});
test('full directory scope selection collapses picker, preserves scope route and returns visible keyboard focus',async t=>{
 const zlib=require('node:zlib'),b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/navigation-product/model.json.gz'))));
 const d=new JSDOM(html,{url:'https://example.org/RoboPaperAtlas/research/navigation/',runScripts:'outside-only',pretendToBeVisual:true});t.after(()=>d.window.close());const w=d.window,doc=w.document;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.NAVIGATION_PRODUCT=b;
 for(const name of ['navigation-product-model.js','navigation-product.js'])w.eval(fs.readFileSync(path.join(root,'assets',name),'utf8'));
 await new Promise(r=>setTimeout(r,35));
 const picker=doc.querySelector('#np-catalog');picker.open=true;
 const goat=[...doc.querySelectorAll('#np-directory-list button')].find(x=>x.textContent.startsWith('GOAT'));assert.ok(goat);goat.focus();goat.click();
 const state=w.NavigationProductApp.getState();assert.equal(state.route.scope,'task:goat');assert.equal(state.route.paper,null);assert.equal(state.route.version,null);assert.equal(picker.open,false);assert.equal(doc.activeElement,picker.querySelector('summary'));
 await new Promise(r=>setTimeout(r,45));assert.equal(doc.activeElement,picker.querySelector('summary'),'visible summary focus remains after render RAF');
 assert.match(doc.querySelector('#np-active-scope').textContent,/GOAT/);assert.ok(doc.querySelectorAll('#np-tree [role=treeitem]').length>1);
 doc.querySelector('#np-task-conditions').open=true;assert.match(doc.querySelector('#np-scope-summary').textContent,/680k|725k/);assert.ok(doc.querySelector('#np-scope-summary a[href]'));
});
test('first scope expands bounded routes; revisiting deliberate collapse and Back/Forward retain it',async t=>{
 const zlib=require('node:zlib'),b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/navigation-product/model.json.gz'))));
 const d=new JSDOM(html,{url:'https://example.org/RoboPaperAtlas/research/navigation/',runScripts:'outside-only',pretendToBeVisual:true});t.after(()=>d.window.close());const w=d.window,doc=w.document;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.NAVIGATION_PRODUCT=b;
 for(const name of ['navigation-product-model.js','navigation-product.js'])w.eval(fs.readFileSync(path.join(root,'assets',name),'utf8'));
 const settle=async()=>{await new Promise(r=>setTimeout(r,20));await new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)));};await settle();
 const choose=name=>{doc.querySelector('#np-catalog').open=true;[...doc.querySelectorAll('#np-directory-list button')].find(x=>x.textContent.startsWith(name)).click();};
 choose('GOAT');await settle();const M=w.NavigationProductModel,goatState=w.NavigationProductApp.getState(),rootId=M.roots(b,goatState.route)[0];
 assert.ok(M.visible(b,goatState).length>1);assert.ok(M.getBucket(goatState).expandedByTree.l.length<=3,'only bounded initial expansion');
 doc.getElementById('np-node-'+rootId).querySelector('.np-node-toggle').click();await settle();
 assert.equal(doc.querySelectorAll('#np-tree [role=treeitem]').length,1);
 doc.querySelector('#np-tree-scroll').scrollTop=123;
 choose('ObjectNav');await settle();w.history.back();await settle();
 assert.equal(w.NavigationProductApp.getState().route.scope,'task:goat');assert.equal(doc.querySelectorAll('#np-tree [role=treeitem]').length,1);assert.equal(doc.querySelector('#np-tree-scroll').scrollTop,123);
 w.history.forward();await settle();assert.equal(w.NavigationProductApp.getState().route.scope,'task:category-objectnav');
 choose('GOAT');await settle();assert.equal(doc.querySelectorAll('#np-tree [role=treeitem]').length,1,'returning picker must not override deliberate collapse');
 assert.equal(w.NavigationProductApp.getState().route.paper,null);assert.equal(w.NavigationProductApp.getState().route.version,null);
});
test('conditions button opens retained evidence without replacing canonical route or corrupting Back',async t=>{
 const zlib=require('node:zlib'),b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(root,'data/navigation-product/model.json.gz'))));
 const d=new JSDOM(html,{url:'https://example.org/RoboPaperAtlas/research/navigation/',runScripts:'outside-only',pretendToBeVisual:true});t.after(()=>d.window.close());const w=d.window,doc=w.document;w.scrollTo=()=>{};w.HTMLElement.prototype.scrollIntoView=function(){};w.NAVIGATION_PRODUCT=b;
 for(const name of ['navigation-product-model.js','navigation-product.js'])w.eval(fs.readFileSync(path.join(root,'assets',name),'utf8'));
 const settle=async()=>{await new Promise(r=>setTimeout(r,20));await new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)));};await settle();
 const choose=name=>[...doc.querySelectorAll('#np-directory-list button')].find(x=>x.textContent.startsWith(name)).click();
 choose('GOAT');await settle();const hash=w.location.hash,length=w.history.length;
 doc.querySelector('#np-open-conditions').click();await settle();assert.equal(doc.querySelector('#np-task-conditions').open,true);assert.equal(w.location.hash,hash);assert.equal(w.history.length,length);assert.equal(doc.activeElement,doc.querySelector('#np-task-conditions>summary'));
 choose('ObjectNav');await settle();w.history.back();await settle();assert.equal(w.location.hash,hash);assert.equal(w.NavigationProductApp.getState().route.scope,'task:goat');assert.match(doc.querySelector('#np-active-scope').textContent,/GOAT/);
});
