'use strict';
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),zlib=require('node:zlib'),path=require('node:path');
const M=require('../assets/navigation-product-model.js'),root=path.resolve(__dirname,'..'),raw=fs.readFileSync(path.join(root,'data/navigation-product/model.json.gz')),source=JSON.parse(zlib.gunzipSync(raw)),sha='9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c';
function fixture(){const b=M.clone(source),names=['legacy:nav:goal','legacy:nav:l','legacy:nav:c'],positions={};names.forEach((entityId,i)=>{const id='pos:g:fixture'+i,e=b.entities[entityId];positions[id]={id,entityId,label:e.label,kind:e.kind,tree:'g',scopeId:'scope:all',paperId:null,versionId:null,claimIds:[],parentId:i?'pos:g:fixture0':null,childIds:i?[]:['pos:g:fixture1','pos:g:fixture2'],sourceRelationIds:i?['legacy:host-'+(i===1?'literature':'challenge')]:[]};});b.delivery={sourceModelSha256:sha,researchMap:{schemaVersion:'research-map/1',sourceModelSha256:sha,positions,roots:['pos:g:fixture0'],scopeEntries:[]}};return b;}
test('global presentation installs atomically while every original identity and placement remains unchanged',()=>{const b=fixture(),old=JSON.stringify(b.positions),before=M.clone(b);M.installResearchMap(b);assert.equal(Object.keys(b.positions).length,Object.keys(source.positions).length+3);for(const [id,p] of Object.entries(source.positions))assert.deepEqual(b.positions[id],p);assert.deepEqual(b.entities,before.entities);assert.deepEqual(b.analyses,before.analyses);assert.deepEqual(b.template,before.template);assert.equal(M.initialState(b).route.tree,'g');assert.equal(M.initialState(b).route.node,'pos:g:fixture0');assert.deepEqual(M.parseRoute(b,M.encodeRoute(M.initialState(b).route)),M.initialState(b).route);assert.ok(old.length>0);});
for(const [label,mutate] of [
 ['wrong source',m=>m.sourceModelSha256='0'.repeat(64)],
 ['unknown entity',m=>m.positions['pos:g:fixture1'].entityId='missing'],
 ['existing position shadow',m=>m.positions[Object.keys(source.positions)[0]]=M.clone(Object.values(source.positions)[0])],
 ['unreachable extra node',m=>m.positions['pos:g:extra']={...m.positions['pos:g:fixture1'],id:'pos:g:extra',parentId:null}],
 ['incorrect paper identity',m=>m.positions['pos:g:fixture1'].paperId='missing-paper'],
 ['wrong scope',m=>m.positions['pos:g:fixture1'].scopeId='task:category-objectnav'],
 ['dangling claim',m=>m.positions['pos:g:fixture1'].claimIds=['missing-claim']],
 ['parent mismatch',m=>m.positions['pos:g:fixture1'].parentId=null]
])test('invalid global descriptor fails without partially changing science/runtime: '+label,()=>{const b=fixture();mutate(b.delivery.researchMap);const before=JSON.stringify({positions:b.positions,forests:b.forests,entities:b.entities});assert.throws(()=>M.installResearchMap(b));assert.equal(JSON.stringify({positions:b.positions,forests:b.forests,entities:b.entities}),before);assert.equal(b.researchMap,undefined);});
test('old l/c/a share links and pre-overview history remain exact after global installation',()=>{const b=fixture(),p=Object.values(b.positions).find(p=>p.tree==='l'&&p.paperId==='poni'&&p.scopeId==='task:category-objectnav');const route=M.routeForPosition(b,{scope:p.scopeId},p.id),s=M.initialState(b,route);for(const bucket of Object.values(s.contexts)){delete bucket.selectedByTree.g;delete bucket.expandedByTree.g;delete bucket.treeScrollByTree.g;delete bucket.detailScrollByTree.g;delete bucket.treeScrollLeftByTree;}M.installResearchMap(b);assert.deepEqual(M.parseRoute(b,M.encodeRoute(route)),route);assert.equal(M.validateState(b,s),s);});
test('global to fixed paper evidence and return preserves full overview snapshot',()=>{const b=fixture();M.installResearchMap(b);let s=M.initialState(b);s=M.toggle(b,s,'pos:g:fixture1',true);s=M.capture(s,{treeScroll:120,treeScrollLeft:31,detailScroll:44,windowScroll:80,focusTarget:'pos:g:fixture1'});const before=M.snapshot(s),answer=Object.values(b.positions).find(p=>p.tree==='a'&&p.paperId==='poni'&&p.kind==='analysis_answer'),route=M.routeForPosition(b,{scope:'task:category-objectnav'},answer.id);s=M.navigate(b,s,route,{crossTree:true});assert.equal(s.route.version,answer.versionId);s=M.restoreOrigin(b,s,0);assert.deepEqual(M.snapshot(s),before);M.validateState(b,s);});
test('global URLs require an installed map and the true global scope',()=>{const b=fixture();assert.throws(()=>M.validateRoute(b,{scope:'scope:all',tree:'g'}));M.installResearchMap(b);assert.throws(()=>M.validateRoute(b,{scope:'task:category-objectnav',tree:'g'}));assert.throws(()=>M.validateRoute(b,{scope:'scope:all',tree:'g',bench:'benchmark:habitat-objectnav'}));});
test('horizontal history values reject negative or non-finite positions while absent legacy fields remain valid',()=>{const b=fixture();M.installResearchMap(b);for(const value of [-20,Infinity,'10']){const s=M.initialState(b);M.getBucket(s).treeScrollLeftByTree.g=value;assert.throws(()=>M.validateState(b,s));}const s=M.initialState(b);delete M.getBucket(s).treeScrollLeftByTree;assert.equal(M.validateState(b,s),s);});
test('global general-goal links cannot pretend to be a selected paper or version',()=>{const b=fixture();M.installResearchMap(b);assert.throws(()=>M.validateRoute(b,{scope:'scope:all',tree:'g',node:'pos:g:fixture0',paper:'poni',version:'publication:poni:e83f98bb7132'}));assert.throws(()=>M.validateRoute(b,{scope:'scope:all',tree:'g',paper:'poni'}));});
function editorialFixture(){const b=fixture(),m=b.delivery.researchMap,id='display:research-map:directory:task',p='pos:g:directorytask';m.presentationEntities={[id]:{id,label:b.directoryGroups[0].label,kind:'editorial_directory_group',paperId:null,versionIds:[],claimIds:[],sourceRefs:[],detail:{sourceDirectoryGroupId:b.directoryGroups[0].id,description:'编辑阅读目录，不声明科学继承。'}}};m.positions[p]={id:p,entityId:id,label:m.presentationEntities[id].label,kind:'editorial_directory_group',tree:'g',scopeId:'scope:all',paperId:null,versionId:null,claimIds:[],parentId:'pos:g:fixture1',childIds:[],edgeSemantics:'editorial_navigation'};m.positions['pos:g:fixture1'].childIds=[p];return b;}
test('editorial navigation entities install separately without relabeling a scientific entity',()=>{const b=editorialFixture(),old=M.clone(b.entities);M.installResearchMap(b);for(const id of Object.keys(old))assert.deepEqual(b.entities[id],old[id]);assert.equal(b.entities['display:research-map:directory:task'].paperId,null);assert.equal(b.entities['legacy:nav:l'].label,old['legacy:nav:l'].label);});
for(const [name,mutate] of [['paper',e=>e.paperId='poni'],['version',e=>e.versionIds=['publication:poni:e83f98bb7132']],['claim',e=>e.claimIds=['injected']],['scientific body',e=>e.detail.answer='invented'],['false directory label',e=>e.label='new taxonomy']])test('editorial entity cannot claim '+name,()=>{const b=editorialFixture();mutate(b.delivery.researchMap.presentationEntities['display:research-map:directory:task']);const before=JSON.stringify(b.entities);assert.throws(()=>M.installResearchMap(b));assert.equal(JSON.stringify(b.entities),before);assert.equal(b.researchMap,undefined);});

test('source-reference labels reconstruct the exact global descriptor before installation',()=>{const b=fixture(),expected=M.clone(b.delivery.researchMap);b.delivery.researchMap.labelEncoding='source-reference/1';for(const p of Object.values(b.delivery.researchMap.positions)){delete p.label;p.labelRef='entityId.label';}M.installResearchMap(b);assert.deepEqual(b.researchMap,expected);});
for(const type of ['unknown','duplicate','wrong-paper'])test('invalid global title reference rejects atomically: '+type,()=>{const b=fixture(),m=b.delivery.researchMap;m.labelEncoding='source-reference/1';for(const p of Object.values(m.positions)){delete p.label;p.labelRef='entityId.label';}const p=m.positions[m.roots[0]];if(type==='unknown')p.labelRef='arbitrary.field';if(type==='duplicate')p.label='conflict';if(type==='wrong-paper'){p.labelRef='labelSourcePaperId.title';p.labelSourcePaperId='poni';p.paperId='semexp';}const old=JSON.stringify({positions:b.positions,entities:b.entities,forests:b.forests});assert.throws(()=>M.installResearchMap(b));assert.equal(JSON.stringify({positions:b.positions,entities:b.entities,forests:b.forests}),old);});

for(const [name,value] of [['unknown',['pos:g:missing']],['old-tree',[Object.keys(source.positions)[0]]],['duplicate',['pos:g:fixture0','pos:g:fixture0']],['non-array','pos:g:fixture0']])test('initial expansion rejects '+name+' without partial installation',()=>{const b=fixture();b.delivery.researchMap.initialExpandedIds=value;const before=JSON.stringify({positions:b.positions,entities:b.entities,forests:b.forests});assert.throws(()=>M.installResearchMap(b));assert.equal(JSON.stringify({positions:b.positions,entities:b.entities,forests:b.forests}),before);});

function versionTitleFixture(){
 const b=fixture(),map=b.delivery.researchMap,sourcePosition=b.positions['pos:l:a786031a24f0627d36943d'],id='pos:g:versiontitle';
 map.positions[id]={...M.clone(sourcePosition),id,tree:'g',scopeId:'scope:all',parentId:map.roots[0],childIds:[],labelSourcePaperId:sourcePosition.paperId};
 map.positions[map.roots[0]].childIds.push(id);map.labelEncoding='source-reference/1';
 for(const p of Object.values(map.positions)){delete p.label;p.labelRef='entityId.label';}
 map.positions[id].labelRef='labelSourceEntityId.label';map.positions[id].labelSourceEntityId='methods:paper:langmap26';
 return b;
}
test('version-bound paper entity title installs without changing historic science or source identity',()=>{
 const b=versionTitleFixture(),before=M.clone(b),expected='LangMap: A Human-Verified Benchmark for Hierarchical Open-Vocabulary Goal Navigation';
 M.installResearchMap(b);const p=b.positions['pos:g:versiontitle'];
 assert.equal(p.label,expected);assert.equal(p.entityId,'methods:pipeline-planavid');assert.equal(p.paperId,'langmap26');assert.equal(p.versionId,'arxiv:2602.02220v3');
 assert.equal(p.labelRef,undefined);assert.equal(p.labelSourceEntityId,undefined);
 for(const [id,position] of Object.entries(before.positions))assert.deepEqual(b.positions[id],position);
 for(const key of ['entities','papers','versions','analyses','template','statusGates'])assert.deepEqual(b[key],before[key]);
 assert.equal(b.papers.langmap26.title,'LangMap: A Hierarchical Benchmark for Open-Vocabulary Goal Navigation');
});
for(const mutation of ['missing-entity','other-paper','other-version','missing-version','unknown-version','unregistered-version','wrong-version-owner','wrong-kind','wrong-position-kind','wrong-source-paper','conflicting-legacy-source'])test('version-bound global title rejects atomically: '+mutation,()=>{
 const b=versionTitleFixture(),p=b.delivery.researchMap.positions['pos:g:versiontitle'];
 if(mutation==='missing-entity')p.labelSourceEntityId='missing';
 else if(mutation==='other-paper')p.labelSourceEntityId='methods:paper:cow';
 else if(mutation==='other-version')b.entities['methods:paper:langmap26'].versionIds=[];
 else if(mutation==='missing-version')p.versionId=null;
 else if(mutation==='unknown-version')p.versionId='unknown';
 else if(mutation==='unregistered-version')b.papers.langmap26.versionIds=b.papers.langmap26.versionIds.filter(v=>v!==p.versionId);
 else if(mutation==='wrong-version-owner')b.versions[p.versionId].paperId='cow';
 else if(mutation==='wrong-kind')b.entities['methods:paper:langmap26'].kind='pipeline_recipe';
 else if(mutation==='wrong-position-kind')p.kind='paper';
 else if(mutation==='wrong-source-paper')p.labelSourcePaperId='cow';
 else if(mutation==='conflicting-legacy-source')p.labelRef='entityId.label';
 const before=JSON.stringify(b);assert.throws(()=>M.installResearchMap(b));assert.equal(JSON.stringify(b),before);assert.equal(b.researchMap,undefined);
});
test('actual serialized version-title references roundtrip through the runtime decoder',()=>{
 const output=require('node:child_process').execFileSync('python3',['-c',"import json,sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;from navigation_transport import project;r=Path('.').resolve();data=project(p.payloads(r)[1],p.MODEL_SHA256);print(json.dumps({'index':data['index'],'map':data['researchMap']}))"],{cwd:root,encoding:'utf8',maxBuffer:14e6}),data=JSON.parse(output),b=data.index,before=M.clone(b.positions);
 const refs=Object.values(b.delivery.researchMap.positions).filter(p=>p.labelRef==='labelSourceEntityId.label');assert.equal(refs.length,4);
 M.installResearchMap(b);assert.deepEqual(b.researchMap,data.map);
 for(const [id,p] of Object.entries(before))assert.deepEqual(b.positions[id],p);
 for(const p of refs){assert.equal(b.positions[p.id].paperId,p.paperId);assert.equal(b.positions[p.id].versionId,p.versionId);assert.equal(b.positions[p.id].label,b.entities[p.labelSourceEntityId].label);}
});
