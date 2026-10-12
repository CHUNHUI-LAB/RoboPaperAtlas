'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),zlib=require('node:zlib'),path=require('node:path'),M=require('../assets/navigation-product-model.js');
const b=JSON.parse(zlib.gunzipSync(fs.readFileSync(path.join(__dirname,'../data/navigation-product/model.json.gz'))));
test('companion expansion requires an explicit same-scope local-forest option and never changes selected route or identity',()=>{
 const state=M.initialState(b,{scope:'task:audiogoal',tree:'l'}),id=b.forests['task:audiogoal'].c[0],before=structuredClone(state);
 assert.throws(()=>M.toggle(b,state,id));const opened=M.toggle(b,state,id,true,{parallelScope:true});assert.deepEqual(opened.route,before.route);assert.deepEqual(M.getBucket(opened).selectedByTree,M.getBucket(before).selectedByTree);assert.deepEqual(M.getBucket(opened).expandedByTree.l,M.getBucket(before).expandedByTree.l);assert.ok(M.getBucket(opened).expandedByTree.c.includes(id));assert.deepEqual(state,before);M.validateState(b,opened);
 for(const bad of [b.forests['task:goat'].c[0],b.forests['task:goat'].l[0],b.template.roots[0]])assert.throws(()=>M.toggle(b,state,bad,true,{parallelScope:true}));
});
test('presentation fields round-trip with old snapshots while malformed values fail closed',()=>{
 const state=M.initialState(b,{scope:'task:audiogoal',tree:'l'});M.validateState(b,state);const bucket=M.getBucket(state);bucket.originalMapOpen=false;bucket.parallelScopeReady=true;bucket.overviewView={allScopesOpen:true,comparisonOpen:true,relationsOpen:true,scrollTop:247};M.validateState(b,state);assert.deepEqual(M.clone(state),state);
 for(const [field,value] of [['originalMapOpen','false'],['parallelScopeReady',1],['overviewView',{allScopesOpen:true,comparisonOpen:true,scrollTop:-1}],['overviewView',{allScopesOpen:true,comparisonOpen:true,scrollTop:0,relationsOpen:'yes'}]]){const bad=M.clone(state);M.getBucket(bad)[field]=value;assert.throws(()=>M.validateState(b,bad),field);}
});
