/* Local-only view model: academic claims are supplied by audited data, never inferred here. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.TreeModel=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const unique=xs=>[...new Set(xs)];
const PAGE_SIZE=4, CATALOG_PAGE_SIZE=10;
const clone=s=>JSON.parse(JSON.stringify(s));
const stableId=parts=>'path-'+[...parts.join('|')].reduce((h,c)=>Math.imul(h^c.charCodeAt(0),16777619)>>>0,2166136261).toString(36);
function initialState(){return {view:'trees',globalTree:'l',analysisPaper:'harnessvln',query:'',lFacet:'pipeline',l:[],c:[],pages:{l:0,c:0,catalog:0},branchPages:{},paper:null,tab:'evidence',origin:null};}
function normalizeLiterature(raw={}){
 const nodes=new Map((raw.nodes||[]).map(n=>[n.node_id,{...n,id:n.node_id,label:n.label||n.title,type:n.type}]));
 const paths=(raw.paths||[]).map((p,i)=>({id:p.path_id||p.id||stableId([p.paper_id||p.canonical_id,...(p.node_ids||p.path||p.nodes||[])]),nodeIds:p.node_ids||p.path||p.nodes||[],paperId:p.paper_id||p.canonical_id,evidenceIds:p.evidence_ids||[],status:p.status||p.mapping_status||'',viewKind:p.view_kind||'pipeline',implementationVariant:raw.implementation_variants?.[p.implementation_variant_ref]||null,raw:p})).filter(p=>p.nodeIds.length&&p.nodeIds.every(id=>typeof id==='string'&&nodes.has(id)));
 return {kind:'literature',nodes,paths,evidence:new Map((raw.evidence||[]).map(e=>[e.evidence_id,e])),raw};
}
function normalizeChallenge(raw={}){
 const nodes=new Map(),paths=[];
 for(const c of raw.challenges||[])nodes.set(c.challenge_id,{...c,id:c.challenge_id,label:c.title,type:'challenge',evidence_ids:[]});
 for(const i of raw.insights||[]){
  nodes.set(i.insight_id,{...i,id:i.insight_id,label:i.title,type:'insight',evidence_ids:unique([...(i.variants||[]).flatMap(v=>v.evidence_refs||[]),...(i.rationale?.author_rationale_anchors||[])])});
  for(const [index,v] of (i.variants||[]).entries()){
   const ref='paper:'+v.paper_id;if(!nodes.has(ref))nodes.set(ref,{id:ref,type:'paper_ref',paper_id:v.paper_id,label:v.paper_id});
   paths.push({id:i.insight_id+':'+v.paper_id+':'+index,nodeIds:[i.challenge_id,i.insight_id,ref],paperId:v.paper_id,evidenceIds:v.evidence_refs||[],status:v.mapping_status,variant:v,raw:v});
  }
 }
 return {kind:'challenge',nodes,paths,evidence:new Map((raw.evidence||[]).map(e=>[e.evidence_id,e])),raw};
}
function buildModel(catalog,literature,challenge){
 const papers=new Map((catalog.papers||[]).map(p=>[p.canonical_id,p]));
 const trees={l:normalizeLiterature(literature),c:normalizeChallenge(challenge)};
 for(const tree of Object.values(trees)){tree.paths=tree.paths.filter(p=>papers.has(p.paperId));for(const node of tree.nodes.values())if(node.type==='paper_ref')node.label=papers.get(node.paper_id)?.short_name||node.label;}
 return {catalog,papers,trees};
}
function pageKey(key,path){return key+'|'+path.join('>');}
function rememberPage(state,key){state.branchPages[pageKey(key,state[key])]=state.pages[key]||0;}
function restorePage(state,key){state.pages[key]=state.branchPages[pageKey(key,state[key])]||0;}
function startsWith(a,b){return b.length<=a.length&&b.every((v,i)=>a[i]===v);}
function matchingPaths(tree,prefix=[],facet){return tree.paths.filter(p=>(!facet||p.viewKind===facet||p.viewKind==='protocol')&&startsWith(p.nodeIds,prefix));}
function children(tree,prefix=[],facet){
 const paths=matchingPaths(tree,prefix,facet),ids=tree.kind==='literature'&&!prefix.length?[...tree.nodes.values()].filter(n=>n.type==='task_contract').map(n=>n.id):unique(paths.filter(p=>p.nodeIds.length>prefix.length).map(p=>p.nodeIds[prefix.length]));
 return ids.map(id=>({node:tree.nodes.get(id),paths:paths.filter(p=>p.nodeIds[prefix.length]===id),paperIds:unique(paths.filter(p=>p.nodeIds[prefix.length]===id).map(p=>p.paperId))}));
}
function branch(model,state,key){const tree=model.trees[key],prefix=state[key],facet=key==='l'?state.lFacet:undefined,all=children(tree,prefix,facet),maxPage=Math.max(0,Math.ceil(all.length/PAGE_SIZE)-1),page=Math.min(state.pages[key]||0,maxPage);return {tree,prefix,all,page,maxPage,total:all.length,items:all.slice(page*PAGE_SIZE,(page+1)*PAGE_SIZE),parent:tree.nodes.get(prefix.at(-1)),paperCount:unique(matchingPaths(tree,prefix,facet).map(p=>p.paperId)).length};}
// Display aggregates only: keep source task roots, paths, and evidence untouched.
function rootOverview(model,key,facet){
 const tree=model.trees[key];return children(tree,[],key==='l'?facet:undefined).map(item=>({...item,
  childCount:unique(item.paths.map(p=>p.nodeIds[1]).filter(Boolean)).length,
  moduleCount:unique(item.paths.flatMap(p=>p.nodeIds.filter(id=>tree.nodes.get(id)?.type==='module'))).length
 }));
}
function pathsForPaper(model,paperId){return ['l','c'].flatMap(key=>model.trees[key].paths.filter(p=>p.paperId===paperId).map(p=>({...p,key,labels:p.nodeIds.map(id=>model.trees[key].nodes.get(id)?.label||id)})));}
function catalogResults(model,query=''){
 const q=query.trim().toLocaleLowerCase();if(!q)return [...model.papers.values()];
 return [...model.papers.values()].filter(p=>[p.short_name,p.title,p.canonical_id,p.version,p.overview_zh,p.abstract_summary_zh,p.pipeline,p.representation,p.module,p.challenge,p.insight,...(p.evidence||[]).map(e=>e.statement),...pathsForPaper(model,p.canonical_id).flatMap(p=>p.labels)].join(' ').toLocaleLowerCase().includes(q));
}
function coverage(model){const l=unique(model.trees.l.paths.map(p=>p.paperId)),c=unique(model.trees.c.paths.map(p=>p.paperId));return {catalog:model.papers.size,literature:l.length,challenge:c.length,both:l.filter(id=>c.includes(id)).length,unmapped:[...model.papers.keys()].filter(id=>!l.includes(id)&&!c.includes(id)).length};}
function sanitizeState(model,raw){
 const state={...initialState(),...raw,pages:{...initialState().pages,...raw?.pages},branchPages:{...(raw?.branchPages||{})}};
 state.view=['trees','catalog'].includes(state.view)?state.view:'trees';state.globalTree=['l','c','a'].includes(state.globalTree)?state.globalTree:'l';state.analysisPaper=model.papers.has(state.analysisPaper)?state.analysisPaper:'harnessvln';state.lFacet=['pipeline','representation'].includes(state.lFacet)?state.lFacet:'pipeline';state.tab=['overview','evidence','paths','analysis'].includes(state.tab)?state.tab:'evidence';state.query=typeof state.query==='string'?state.query.slice(0,500):'';
 for(const key of ['l','c']){state[key]=Array.isArray(state[key])?state[key]:[];while(state[key].length&&!matchingPaths(model.trees[key],state[key],key==='l'?state.lFacet:undefined).length&&!(key==='l'&&state[key].length===1&&model.trees.l.nodes.get(state[key][0])?.type==='task_contract'))state[key].pop();state.pages[key]=Math.max(0,Number(state.pages[key])||0);}
 state.pages.catalog=Math.max(0,Number(state.pages.catalog)||0);if(!model.papers.has(state.paper))state.paper=null;
 if(!state.paper)state.origin=null;else if(state.origin&&(!['l','c'].includes(state.origin.key)||!Array.isArray(state.origin.path)||!model.trees[state.origin.key].paths.some(p=>p.paperId===state.paper&&p.nodeIds.length===state.origin.path.length&&startsWith(p.nodeIds,state.origin.path))))state.origin=null;return state;
}
function reduce(model,state,action){
 const next=clone(state);
 switch(action.type){
 case 'overview':return initialState();
 case 'global':next.view='trees';break;
 case 'analysisPaper':if(!model.papers.has(action.id))return state;next.analysisPaper=action.id;break;
 case 'globalTree':if(!['l','c','a'].includes(action.key))return state;next.globalTree=action.key;next.view='trees';break;
 case 'root':{const key=action.key;if(!['l','c'].includes(key)||!rootOverview(model,key,key==='l'?next.lFacet:undefined).some(x=>x.node.id===action.id))return state;rememberPage(next,key);next[key]=[action.id];restorePage(next,key);next.view='trees';next.globalTree=key;break;}
 case 'view':next.view=action.view;break;
 case 'facet':rememberPage(next,'l');next.lFacet=action.facet;next.l=next.l.slice(0,1);restorePage(next,'l');break;
 case 'search':next.query=action.query;next.view='catalog';next.pages.catalog=0;if(next.paper&&!catalogResults(model,next.query).some(p=>p.canonical_id===next.paper)){next.paper=null;next.origin=null;}break;
 case 'clearSearch':next.query='';next.pages.catalog=0;break;
 case 'page':next.pages[action.key]=Math.max(0,action.page);if(action.key!=='catalog')rememberPage(next,action.key);break;
 case 'enter':{const k=action.key,n=model.trees[k].nodes.get(action.id);if(!children(model.trees[k],next[k],k==='l'?next.lFacet:undefined).some(x=>x.node.id===action.id))return state;if(n.type==='paper_ref'){next.paper=n.paper_id;next.tab='evidence';next.origin={key:k,path:[...next[k],action.id]};}else{rememberPage(next,k);next[k].push(action.id);restorePage(next,k);}break;}
 case 'back':{const k=action.key;rememberPage(next,k);next[k].pop();restorePage(next,k);break;}
 case 'crumb':rememberPage(next,action.key);next[action.key]=next[action.key].slice(0,action.depth);restorePage(next,action.key);break;
 case 'paper':if(!model.papers.has(action.id))return state;next.paper=action.id;next.tab=next.paper===state.paper?state.tab:'evidence';next.origin=action.origin||null;break;
 case 'closePaper':next.paper=null;next.origin=null;break;
 case 'tab':next.tab=action.tab;break;
 case 'path':{const p=model.trees[action.key].paths.find(p=>p.id===action.id);if(!p)return state;next.view='trees';next.globalTree=action.key;if(action.key==='l'&&p.viewKind!=='protocol')next.lFacet=p.viewKind;rememberPage(next,action.key);next[action.key]=p.nodeIds.slice(0,-1);for(let depth=0;depth<p.nodeIds.length;depth++){const prefix=p.nodeIds.slice(0,depth),items=children(model.trees[action.key],prefix,action.key==='l'?next.lFacet:undefined),index=items.findIndex(item=>item.node.id===p.nodeIds[depth]);next.branchPages[pageKey(action.key,prefix)]=Math.max(0,Math.floor(index/PAGE_SIZE));}restorePage(next,action.key);next.paper=p.paperId;next.origin={key:action.key,path:p.nodeIds};break;}
 default:return state;
 }
 return sanitizeState(model,next);
}
function serialize(state){return '#state='+encodeURIComponent(JSON.stringify(state));}
function deserialize(model,hash){try{return sanitizeState(model,JSON.parse(decodeURIComponent(String(hash).replace(/^#state=/,''))));}catch{return initialState();}}
function validate(model){
 const errors=[];
 for(const [key,tree] of Object.entries(model.trees)){for(const p of tree.raw.paths||[]){const ids=p.node_ids||p.path||p.nodes||[];if(!ids.length||ids.some(id=>!tree.nodes.has(id)))errors.push(key+': invalid raw path nodes');if(!model.papers.has(p.paper_id||p.canonical_id))errors.push(key+': unknown raw path paper');}for(const i of tree.raw.insights||[])for(const v of i.variants||[])if(!model.papers.has(v.paper_id))errors.push(key+': unknown insight paper');}

 if(model.papers.size!==model.catalog.source_count)errors.push('Catalog count mismatch');
 for(const [key,tree] of Object.entries(model.trees)){
  const ids=new Set();for(const p of tree.paths){if(ids.has(p.id))errors.push(key+': duplicate path '+p.id);ids.add(p.id);if(!model.papers.has(p.paperId))errors.push(key+': dangling paper');if(p.raw.implementation_variant_ref&&(!p.implementationVariant||p.implementationVariant.paper_id!==p.paperId))errors.push(key+': unresolved implementation variant '+p.raw.implementation_variant_ref);for(const id of p.nodeIds)if(!tree.nodes.has(id))errors.push(key+': dangling node '+id);if(tree.nodes.get(p.nodeIds.at(-1))?.type!=='paper_ref')errors.push(key+': path must end in canonical paper reference');for(const e of p.evidenceIds)if(!tree.evidence.has(e))errors.push(key+': dangling evidence '+e);}
  if(tree.raw.academic_edges?.length||tree.raw.academic_inheritance_edges?.length)errors.push(key+': academic edges not supported by this navigation prototype');
 }
 return errors;
}
return {PAGE_SIZE,CATALOG_PAGE_SIZE,pageKey,initialState,normalizeLiterature,normalizeChallenge,buildModel,startsWith,matchingPaths,children,branch,rootOverview,pathsForPaper,catalogResults,coverage,sanitizeState,reduce,serialize,deserialize,validate};
});
