'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),zlib=require('node:zlib'),M=require('../assets/navigation-product-model.js');
const b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname,'../data/navigation-product/model.json.gz'))));
const scope='task:category-objectnav',poni='pos:l:98bc421b8bfd17d6699922',esc='pos:c:6a8a9d2f7b1f3ab3a8ada5',vlfmL='pos:l:ff0298ffa17b4cfcf009bd',vlfmC='pos:c:0c9cde8f173cb56ce4becf';
function at(id){return M.routeForPosition(b,{scope},id);}
function captured(s,id,scroll){s=M.navigate(b,s,at(id),{crossTree:true});return M.capture(s,{treeScroll:scroll,treeScrollLeft:scroll/2,detailScroll:scroll+10,windowScroll:12,focusTarget:id});}
test('task-neutral pointers preserve independent exact paper/version buckets across L/C views',()=>{
 let s=M.initialState(b,{scope,tree:'l'});s=captured(s,poni,111);const old=M.clone(M.getBucket(s));s=captured(s,esc,222);
 const v=M.taskView(s);assert.deepEqual(v.lastRouteByTree.l,at(poni));assert.deepEqual(v.lastRouteByTree.c,at(esc));assert.equal(v.focusTargetByTree.l,poni);assert.equal(v.focusTargetByTree.c,esc);assert.deepEqual(s.contexts[M.contextKey(at(poni))],old);
 s=M.navigate(b,s,v.lastRouteByTree.l,{crossTree:true,restoreScroll:true});assert.equal(M.getBucket(s).treeScrollByTree.l,111);assert.equal(M.getBucket(s).detailScrollByTree.l,121);assert.equal(M.getBucket(s).treeScrollLeftByTree.l,55.5);assert.equal(s.route.paper,'poni');assert.equal(s.route.version,'publication:poni:e83f98bb7132');M.validateState(b,s);
});
test('same paper in different trees retains original different versions including unpinned null identities',()=>{
 let s=M.initialState(b,{scope,tree:'l'});s=captured(s,vlfmL,72);s=captured(s,vlfmC,39);const v=M.taskView(s);assert.equal(v.lastRouteByTree.l.version,'source:method-lineage:vlfm');assert.equal(v.lastRouteByTree.c.version,'source:challenge-insights:vlfm2024');
 const insight=Object.values(b.positions).find(p=>p.scopeId===scope&&p.tree==='c'&&p.paperId==='vlfm'&&p.versionId===null);assert.ok(insight);s=captured(s,insight.id,29);assert.equal(M.taskView(s).lastRouteByTree.c.version,null);M.validateState(b,s);
});
test('explicit origin restores relation presentation and the historical task pointers, not newer paper pointers',()=>{
 let s=M.initialState(b,{scope,tree:'l'});s=M.capture(s,{treeScroll:100,detailScroll:300,focusTarget:'np-task-change-target-'+scope+'-methods:relation:90-'+poni});const root=M.clone(s.route),bucket=M.getBucket(s);bucket.relationViewByTree={l:{id:'methods:relation:90',route:M.clone(root)}};
 s=M.navigate(b,s,at(poni),{crossTree:true});s=captured(s,esc,200);assert.equal(M.taskView(s).lastRouteByTree.c.node,esc);
 const restored=M.restoreOrigin(b,s,0);assert.deepEqual(restored.route,root);assert.equal(M.getBucket(restored).relationViewByTree.l.id,'methods:relation:90');assert.equal(M.getBucket(restored).detailScrollByTree.l,300);assert.equal(M.taskView(restored).lastRouteByTree.c,null);assert.equal(M.taskView(restored).lastRouteByTree.l.node,root.node);M.validateState(b,restored);
 assert.equal(s.contexts[M.contextKey(root)].relationViewByTree.l.id,'methods:relation:90','snapshot operations are deep copies');
});
test('new selection clears only target-view relation after origin snapshot, never scientific route identity',()=>{
 let s=M.initialState(b,{scope,tree:'l'});const original=M.clone(s.route);M.getBucket(s).relationViewByTree={l:{id:'methods:relation:90',route:M.clone(s.route)}};s=M.capture(s,{focusTarget:'np-task-relation-title'});s=M.navigate(b,s,at(poni),{crossTree:true});assert.deepEqual(s.originTrail[0].route,original);assert.equal(s.originTrail[0].bucket.relationViewByTree.l.id,'methods:relation:90');assert.ok(!M.getBucket(s).relationViewByTree?.l);assert.deepEqual(s.route,at(poni));M.validateState(b,s);
});
test('legacy history without optional fields stays valid and malformed presentation never relaxes route checks',()=>{
 const legacy=M.initialState(b,{scope,tree:'l'});M.validateState(b,legacy);const s=M.capture(legacy,{focusTarget:legacy.route.node});M.getBucket(s).relationViewByTree={l:{id:'methods:relation:90',route:M.clone(s.route)}};M.validateState(b,s);
 const corrupt=[x=>M.taskView(x).schema=2,x=>M.taskView(x).lastRouteByTree.l=at(esc),x=>M.taskView(x).lastRouteByTree.l.scope='task:goat',x=>M.taskView(x).focusTargetByTree.c=4,x=>{M.taskView(x).lastRouteByTree.l.paper='poni';M.taskView(x).lastRouteByTree.l.version='publication:semexp:38f1c5a000ce';},x=>M.getBucket(x).relationViewByTree.l.id='90',x=>M.getBucket(x).relationViewByTree.l.route=at(poni),x=>M.getBucket(x).relationViewByTree.a={id:'methods:relation:90',route:x.route}];
 for(const mutate of corrupt){const x=M.clone(s);mutate(x);assert.throws(()=>M.validateState(b,x));}
 const tasks=M.clone(s);M.getBucket(tasks).relationViewByTree.l.id='tasks:relation:90';M.validateState(b,tasks);assert.notEqual(M.getBucket(tasks).relationViewByTree.l.id,M.getBucket(s).relationViewByTree.l.id,'namespace is never reduced to numeric suffix; loaded allowed set validates existence later');
 const next=M.navigate(b,s,at(poni),{crossTree:true}),bad=M.clone(next);bad.originTrail[0].taskView.lastRouteByTree.l.scope='task:goat';assert.throws(()=>M.validateState(b,bad));
});

test('relationship disclosure is exact-route presentation and origin restores its open state',()=>{let s=M.initialState(b,{scope,tree:'l'});const r=M.clone(s.route);M.getBucket(s).relationOverviewByTree={l:{route:M.clone(r),open:true}};M.validateState(b,s);s=M.navigate(b,s,at(poni),{crossTree:true});assert.equal(M.getBucket(s).relationOverviewByTree,undefined);s=M.restoreOrigin(b,s,0);assert.equal(M.getBucket(s).relationOverviewByTree.l.open,true);assert.deepEqual(s.route,r);M.validateState(b,s);for(const mutate of [x=>M.getBucket(x).relationOverviewByTree.l.open='yes',x=>M.getBucket(x).relationOverviewByTree.l.route=at(esc),x=>M.getBucket(x).relationOverviewByTree.l.route=at(poni),x=>M.getBucket(x).relationOverviewByTree.l.extra=1]){const bad=M.clone(s);mutate(bad);assert.throws(()=>M.validateState(b,bad));}});
