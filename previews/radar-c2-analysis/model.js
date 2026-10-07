/* Local-only view model: academic claims are supplied by audited data, never inferred here. */
(function(root,factory){'use strict';const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.TreeModel=api;})(typeof window!=='undefined'?window:null,function(){
'use strict';
const unique=xs=>[...new Set(xs)];
const PAGE_SIZE=4, CATALOG_PAGE_SIZE=10;
const clone=s=>JSON.parse(JSON.stringify(s));
const stableId=parts=>'path-'+[...parts.join('|')].reduce((h,c)=>Math.imul(h^c.charCodeAt(0),16777619)>>>0,2166136261).toString(36);

// Reading groups are a view projection, not academic nodes or mutually-exclusive axes.
const taskMap={
 groups:[
  {id:'route',label:'沿路线指令导航',question:'给路线，让机器人理解并执行',example:'“穿过客厅，在走廊尽头右转”',role:'核心主线',sections:[
   {label:'单条路线指令',note:'图导航与连续环境是动作条件；不是两种目标语义',ids:['task-vln-graph','task-vln-ce']},
   {label:'多条指令共享场景经验',note:'IVLN 延长记忆边界；同时包含图导航和连续环境协议',ids:['task-vln-iterative']}]},
  {id:'goal',label:'按目标条件导航',question:'给目标条件，让机器人搜索、定位或到达',example:'“找一把椅子” · “去这张照片里的位置”',role:'核心主线',sections:[
   {label:'用类别名指定目标',note:'以下是可交叉的协议入口：开放类别与目标发放顺序不是互斥任务',ids:['task-object-category','task-object-open','task-multion','task-multigoal-object']},
   {label:'用图像指定目标',note:'单目标与目标序列分别看；MemoNav 两种都有评测',ids:['task-imagegoal-multigoal']},
   {label:'用对象或房间描述指定目标',note:'指代粒度与预建地图是不同条件；不能互相替代评测',ids:['task-reverie-nav-only','task-language-map-goal']},
   {label:'混合输入的目标序列',note:'GOAT 组合类别、图像、描述；不是第四种互斥目标类型',ids:['task-goat-sequence']}]},
  {id:'related',label:'问答与复合执行',question:'移动可以取证，最终还要回答或执行任务',example:'“我刚才经过的桌上有什么？”',role:'关联任务',sections:[
   {label:'主动移动取证，再回答或判断',note:'成功终点是回答或存在性判断；不统一按导航到达计分',ids:['task-embodiedqa-classic','task-open-eqa-active','task-eqa-active-other','task-evidence-existence']},
   {label:'从既定经历回答，不主动导航',note:'可检验记忆表示；QA 分数不代表导航成功',ids:['task-open-eqa-memory','task-spatiotemporal-qa']},
   {label:'连接两侧的桥梁：LMEE',note:'先多目标导航，再依据记忆问答；任务、基准与方法分角色',ids:['task-lmee']},
   {label:'含导航的复合机器人任务',note:'导航是子技能；图是方法表示，不能放进任务名称',ids:['task-robot-task-planning']}]}],
 labels:{'task-vln-graph':'R2R · 沿路线在图上移动','task-vln-ce':'VLN-CE · 在连续环境执行路线','task-vln-iterative':'IVLN · 多条指令共享经验','task-object-category':'ObjectNav · 找指定类别','task-object-open':'HM3D-OVON · 开放类别目标','task-multion':'MultiON · 按给定顺序逐个找','task-multigoal-object':'SayNav · 同时给三类，自定顺序找','task-imagegoal-multigoal':'ImageNav · 单图像 / 多图像目标','task-reverie-nav-only':'REVERIE · 当前仅导航子任务','task-language-map-goal':'预建地图 · 按空间描述检索目标','task-goat-sequence':'GOAT / GOAT-Bench · 混合目标序列','task-embodiedqa-classic':'EmbodiedQA · 移动后回答','task-open-eqa-active':'OpenEQA A-EQA · 主动问答','task-eqa-active-other':'HM-EQA / MT-HM3D / EXPRESS','task-evidence-existence':'SafeVantage · 主动存在性判断','task-open-eqa-memory':'OpenEQA EM-EQA · 经历问答','task-spatiotemporal-qa':'NaVQA · 时空经历问答','task-lmee':'LMEE · 导航后进行记忆问答','task-robot-task-planning':'SayPlan 等 · 含导航的复合执行'},
 groupFor(id){return this.groups.find(g=>g.sections.some(s=>s.ids.includes(id)))?.id||null;},
 group(id){return this.groups.find(g=>g.id===id)||null;},
 label(id){return this.labels[id]||id;},
 stats(model){const t=model.trees.l;return {nodes:t.nodes.size,paths:t.paths.length,edges:(t.raw.edges||[]).length,contracts:[...t.nodes.values()].filter(n=>n.type==='task_contract').length,papers:new Set(t.paths.map(p=>p.paperId)).size};}
};

function initialState(){return {view:'trees',globalTree:'l',analysisPaper:'harnessvln',taskGroup:null,taskVariant:null,query:'',lFacet:'pipeline',l:[],c:[],pages:{l:0,c:0,catalog:0},branchPages:{},paper:null,tab:'evidence',origin:null};}
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
 if(!taskMap.group(state.taskGroup))state.taskGroup=null;if(state.l.length)state.taskGroup=taskMap.groupFor(state.l[0]);if(typeof state.taskVariant!=='string'||!model.trees.l.nodes.get(state.l[0])?.protocol_variants?.some(v=>v.id===state.taskVariant&&(!state.paper||!v.paper_ids||v.paper_ids.includes(state.paper))))state.taskVariant=null;
 state.pages.catalog=Math.max(0,Number(state.pages.catalog)||0);if(!model.papers.has(state.paper))state.paper=null;
 if(!state.paper)state.origin=null;else if(state.origin&&(!['l','c'].includes(state.origin.key)||!Array.isArray(state.origin.path)||!model.trees[state.origin.key].paths.some(p=>p.paperId===state.paper&&p.nodeIds.length===state.origin.path.length&&startsWith(p.nodeIds,state.origin.path))))state.origin=null;return state;
}
function reduce(model,state,action){
 const next=clone(state);
 switch(action.type){
 case 'overview':return initialState();
 case 'taskGroup':if(!taskMap.group(action.id))return state;next.taskGroup=action.id;next.taskVariant=null;next.l=[];next.pages.l=0;next.view='trees';next.globalTree='l';next.paper=null;next.origin=null;break;
 case 'global':next.taskGroup=null;next.taskVariant=null;next.view='trees';if(['l','c'].includes(next.globalTree)){rememberPage(next,next.globalTree);next[next.globalTree]=[];next.pages[next.globalTree]=0;}next.paper=null;next.origin=null;break;
 case 'analysisPaper':if(!model.papers.has(action.id))return state;next.analysisPaper=action.id;break;
 case 'globalTree':if(!['l','c','a'].includes(action.key))return state;next.globalTree=action.key;next.view='trees';break;
 case 'locate':{const key=action.key,t=atlas.paths(model,key),n=t.by.get(action.id);if(!n)return state;if(n.id===t.root){next[key]=[];next.paper=null;next.origin=null;break;}if(key==='l'){const facetNode=n.path.map(id=>model.trees.l.nodes.get(id)).find(node=>node.type==='pipeline'||node.type==='representation');if(facetNode)next.lFacet=facetNode.type;}rememberPage(next,key);next[key]=n.type==='paper_ref'?n.path.slice(0,-1):n.path;next.globalTree=key;next.view='trees';next.paper=n.type==='paper_ref'?n.paperId:null;next.origin=next.paper?{key,path:n.path}:null;for(let depth=0;depth<n.path.length;depth++){const prefix=n.path.slice(0,depth),index=children(model.trees[key],prefix,key==='l'?next.lFacet:undefined).findIndex(item=>item.node.id===n.path[depth]);next.branchPages[pageKey(key,prefix)]=Math.max(0,Math.floor(index/PAGE_SIZE));}restorePage(next,key);break;}
 case 'root':{const key=action.key;if(!['l','c'].includes(key)||!rootOverview(model,key,key==='l'?next.lFacet:undefined).some(x=>x.node.id===action.id))return state;rememberPage(next,key);next[key]=[action.id];if(key==='l'){next.taskGroup=taskMap.groupFor(action.id);next.taskVariant=action.variant||null;}restorePage(next,key);next.view='trees';next.globalTree=key;next.paper=null;next.origin=null;break;}
 case 'view':next.view=action.view;break;
 case 'facet':rememberPage(next,'l');next.lFacet=action.facet;next.l=next.l.slice(0,1);next.paper=null;next.origin=null;restorePage(next,'l');break;
 case 'search':next.query=action.query;next.view='catalog';next.pages.catalog=0;if(next.paper&&!catalogResults(model,next.query).some(p=>p.canonical_id===next.paper)){next.paper=null;next.origin=null;}break;
 case 'clearSearch':next.query='';next.pages.catalog=0;break;
 case 'page':{const key=action.key,page=Math.max(0,action.page);if(key!=='catalog'&&Number.isInteger(action.depth)&&action.depth>=1&&action.depth<next[key].length){next.branchPages[pageKey(key,next[key].slice(0,action.depth))]=page;}else{next.pages[key]=page;if(key!=='catalog')rememberPage(next,key);}break;}
 case 'enter':{const k=action.key,n=model.trees[k].nodes.get(action.id),prefix=Number.isInteger(action.depth)&&action.depth>=1&&action.depth<=next[k].length?next[k].slice(0,action.depth):next[k];if(!children(model.trees[k],prefix,k==='l'?next.lFacet:undefined).some(x=>x.node.id===action.id))return state;rememberPage(next,k);next[k]=prefix;if(n.type==='paper_ref'){next.paper=n.paper_id;next.tab='evidence';next.origin={key:k,path:[...next[k],action.id]};}else{next[k].push(action.id);next.paper=null;next.origin=null;restorePage(next,k);}break;}
 case 'back':{const k=action.key;rememberPage(next,k);next[k].pop();next.paper=null;next.origin=null;restorePage(next,k);break;}
 case 'crumb':if(action.key==='l'&&action.depth===0){next.taskGroup=null;next.taskVariant=null;}rememberPage(next,action.key);next[action.key]=next[action.key].slice(0,action.depth);next.paper=null;next.origin=null;restorePage(next,action.key);break;
 case 'paper':if(!model.papers.has(action.id))return state;next.paper=action.id;next.tab=next.paper===state.paper?state.tab:'evidence';next.origin=action.origin||null;break;
 case 'evidence':{const tree=model.trees[action.key],p=tree?.paths.find(p=>p.id===action.id);if(!p||!startsWith(p.nodeIds,next[action.key]||[])||!next[action.key]?.length)return state;next.paper=p.paperId;next.tab='evidence';next.origin={key:action.key,path:p.nodeIds,preserveContext:true};break;}
 case 'closePaper':next.paper=null;next.origin=null;break;
 case 'tab':next.tab=action.tab;break;
 case 'path':{const p=model.trees[action.key].paths.find(p=>p.id===action.id);if(!p)return state;next.tab='evidence';next.view='trees';next.globalTree=action.key;if(action.key==='l'&&p.viewKind!=='protocol')next.lFacet=p.viewKind;rememberPage(next,action.key);next[action.key]=p.nodeIds.slice(0,-1);for(let depth=0;depth<p.nodeIds.length;depth++){const prefix=p.nodeIds.slice(0,depth),items=children(model.trees[action.key],prefix,action.key==='l'?next.lFacet:undefined),index=items.findIndex(item=>item.node.id===p.nodeIds[depth]);next.branchPages[pageKey(action.key,prefix)]=Math.max(0,Math.floor(index/PAGE_SIZE));}restorePage(next,action.key);next.paper=p.paperId;next.origin={key:action.key,path:p.nodeIds};break;}
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

// Shared, display-only complete-tree topology and layout. Occurrence IDs are
// navigation addresses, not new scientific nodes or canonical paper records.
const atlas=(function(){
 const UI_ROOT='ui-root',escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
 function finish(nodes,root,kind){const by=new Map(nodes.map(n=>[n.id,n]));for(const n of nodes){n.children=[];}for(const n of nodes)if(n.parent)by.get(n.parent).children.push(n.id);return {nodes,by,root,kind};}
 function paths(model,key){const tree=model.trees[key],nodes=[{id:UI_ROOT,sourceId:null,label:'UI 根 · '+(key==='l'?'文献脉络':'难点与解法'),type:'ui_root',parent:null,path:[]}],seen=new Map([[UI_ROOT,nodes[0]]]);
  function add(route,path){let parent=UI_ROOT;for(let depth=0;depth<route.length;depth++){const prefix=route.slice(0,depth+1),id=stableId([key,...prefix]);let n=seen.get(id);if(!n){const source=tree.nodes.get(route[depth]);n={id,sourceId:source.id,label:source.label,type:source.type,parent,path:prefix,facet:path?.viewKind||'pipeline',pathId:path?.id||null,paperId:source.paper_id||null};seen.set(id,n);nodes.push(n);}parent=id;}}
  for(const item of rootOverview(model,key))add([item.node.id]);for(const p of tree.paths)add(p.nodeIds,p);const out=finish(nodes,UI_ROOT,key);out.pathCount=tree.paths.length;out.paperCount=new Set(tree.paths.map(p=>p.paperId)).size;out.sourceCount=new Set(nodes.map(n=>n.sourceId).filter(Boolean)).size;return out;
 }
 function analysis(m){const nodes=[...m.nodes.values()].map(n=>({id:n.id,sourceId:n.id,label:n.label,contentTitle:n.contentTitle,type:n.isInstance?'instance':n.parent?'question':'analysis_root',parent:n.parent,path:[],paperId:m.paperId}));const root=nodes.find(n=>!n.parent).id,out=finish(nodes,root,'a');for(const n of out.nodes){let at=n;while(at){n.path.unshift(at.id);at=out.by.get(at.parent);}}return out;}
 // Display names do not rename any source node, path, or stable occurrence ID.
 function displayLabel(t,n){return n.id===t.root?({l:'文献脉络',c:'挑战与思路',a:'论文解析'}[t.kind]||n.label):n.label;}
 function route(t,id){const out=[];while(t.by.has(id)){out.unshift(id);id=t.by.get(id).parent;}return out;}

 const modes=new Map();
 function descendantsOf(t,id){return t.by.get(id).children.flatMap(child=>[child,...descendantsOf(t,child)]);}
 function compactText(text,units=20){let out='',used=0;for(const c of String(text).replace(/\s+/g,' ')){used+=/[\u0020-\u007e]/.test(c)?.52:1;if(used>units-1.1)return out+'…';out+=c;}return out;}
 // Conservative proportional advances keep wide Latin scientific names inside
 // their label boxes without changing fonts or truncating source text. These
 // bounds leave room for sans-serif fallback differences; local glyph checks
 // cover the exported labels, but do not claim arbitrary-font browser acceptance.
 function labelUnits(text){return [...String(text)].reduce((n,c)=>n+(/[MWmw@%&]/.test(c)?1.05:/[ilI.,:;!'| ]/.test(c)?.4:/[A-Z]/.test(c)?.85:/[a-z0-9]/.test(c)?.65:/[\u0020-\u007e]/.test(c)?.75:1),0);}
 function lines(text,width,font=13){
  const max=Math.max(1,(width-16)/font),result=[];
  for(const paragraph of String(text).split('\n')){
   let line='',used=0;
   const tokens=paragraph.match(/[A-Za-z0-9][A-Za-z0-9_:/+.-]*|[^\n]/g)||[''];
   for(const token of tokens){
    // Prefer scientific-name boundaries in an overlong slash/colon chain;
    // only split characters when a single component cannot fit by itself.
    const parts=labelUnits(token)<=max?[token]:token.match(/[^/:]+[/:]?|[/:]/g)||[token];
    for(const part of parts){const units=labelUnits(part);
     if(units<=max){if(used+units>max&&line){result.push(line);line='';used=0;}line+=part;used+=units;}
     else for(const c of part){const u=labelUnits(c);if(used+u>max&&line){result.push(line);line='';used=0;}line+=c;used+=u;}
    }
   }
   result.push(line);
  }
  return result;
 }
 function visibleIds(t,selected,mode){if(mode==='full')return new Set(t.nodes.map(n=>n.id));const shown=new Set([t.root,...t.by.get(t.root).children]),routeIds=route(t,selected);let expansion=routeIds.slice(1);if(!expansion.length){let n=t.by.get(t.root).children.find(id=>t.by.get(id).children.length);while(n){expansion.push(n);n=t.by.get(n).children[0];}}
  for(const id of expansion){shown.add(id);const n=t.by.get(id),next=expansion.find(c=>t.by.get(c).parent===id),children=n.children.slice(0,2);if(next&&!children.includes(next))children.push(next);for(const child of children)shown.add(child);}return shown;
 }
 function layout(t,{width=720,selected=t.root,mode='semantic'}={}){
  const sourceDepth=n=>route(t,n.id).length-1,columnOf=n=>t.kind==='l'&&n.type==='paper_ref'?4:sourceDepth(n),allDepth=Math.max(...t.nodes.map(columnOf)),visible=visibleIds(t,selected,mode),full=mode==='full',safe=full?Math.max(1180,width):Math.max(560,width),pad=12,rootWidth=90,left=pad+rootWidth+20,colWidth=full?230:Math.min(155,(safe-left-30)/Math.max(1,allDepth)),step=(safe-left-colWidth-pad)/Math.max(1,allDepth-1),nodes=[],edges=[],measures=new Map();
  for(const n of t.nodes){if(!visible.has(n.id))continue;const depth=sourceDepth(n),column=columnOf(n),children=n.children.filter(id=>visible.has(id)),hidden=n.children.length-children.length,ls=lines(displayLabel(t,n),depth===0?rootWidth:colWidth,full?14:13),labelLines=ls,hiddenIds=n.children.filter(id=>!visible.has(id)),types=new Map(),units={pipeline:'条流程',representation:'种表示',module:'个模块',paper_ref:'条论文路径',protocol:'个协议来源',challenge:'个难点',insight:'种解法',question:'个问题',instance:'个模板实例'};for(const id of hiddenIds){const type=t.by.get(id).type;types.set(type,(types.get(type)||0)+1);}const foldedLabel='还有'+[...types].map(([type,count])=>count+(units[type]||'个原节点')).join('、'),foldLines=hidden?lines(foldedLabel,colWidth,10):[],h=Math.max(32,labelLines.length*(full?19:18)+foldLines.length*12+14);measures.set(n.id,{id:n.id,sourceId:n.sourceId,depth,column,w:depth===0?rootWidth:colWidth,h,labelLines,foldLines,foldedLabel,children,hidden,foldedDescendants:descendantsOf(t,n.id).filter(id=>!visible.has(id)).length});}
  function span(id){const n=measures.get(id);n.span=Math.max(n.h+(full?9:4),n.children.reduce((sum,child)=>sum+span(child),0));return n.span;}const total=span(t.root);
  function place(id,top){const n=measures.get(id),source=t.by.get(id),pos={...n,x:n.depth===0?pad:left+(n.column-1)*step,y:top+(n.span-n.h)/2,type:source.type,label:displayLabel(t,source),root:n.depth===1};nodes.push(pos);if(source.parent)edges.push({source:source.parent,target:id});let y=top+(n.span-n.children.reduce((sum,c)=>sum+measures.get(c).span,0))/2;for(const child of n.children){place(child,y);y+=measures.get(child).span;}}
  place(t.root,42);return {width:safe,height:Math.max(360,total+54),nodes,edges,columnPositions:Array.from({length:allDepth},(_,i)=>left+i*step),maxDepth:allDepth,mode,visibleCount:nodes.length,totalCount:t.nodes.length,foldedCount:t.nodes.length-nodes.length};
 }
 function edge(a,b){const x=a.x+a.w,y=a.y+a.h/2,mid=(x+b.x)/2;return 'M'+x+','+y+' H'+mid+' V'+(b.y+b.h/2)+' H'+b.x;}
 function svg(t,selected=t.root,view=t.kind,options={}){const mode=options.mode||modes.get(view)||'semantic',scene=layout(t,{selected,mode}),by=new Map(scene.nodes.map(n=>[n.id,n])),active=new Set(route(t,selected)),current=by.has(selected)?selected:t.root;
  const labels=t.kind==='l'?['任务','流程 / 表示 / 协议','模块','论文']:t.kind==='c'?['Challenge','Insight','论文']:['五个主枝','研究问题','子问题','细项'];
  let html='<svg class="atlas-svg" viewBox="0 0 '+scene.width+' '+scene.height+'"'+(mode==='full'?' style="width:'+scene.width+'px;height:'+scene.height+'px"':'')+' role="group" aria-label="'+escape(displayLabel(t,t.by.get(t.root)))+'完整来源树的'+(mode==='full'?'全部展开':'语义主骨架')+'，方向键沿父子兄弟浏览，回车定位" data-atlas-view="'+view+'" data-mode="'+mode+'" data-node-count="'+scene.nodes.length+'" data-total-count="'+t.nodes.length+'" data-edge-count="'+scene.edges.length+'"><g class="atlas-column-labels" aria-hidden="true">';
  for(let i=1;i<=scene.maxDepth;i++){const x=scene.columnPositions[i-1];html+='<text data-column="'+i+'" x="'+x+'" y="22">'+escape(labels[i-1]||'细项')+'</text>';}
  html+='</g><g class="atlas-edges" aria-hidden="true">';for(const e of scene.edges)html+='<path data-source="'+escape(e.source)+'" data-target="'+escape(e.target)+'" class="'+(active.has(e.source)&&active.has(e.target)?'active':'')+'" d="'+edge(by.get(e.source),by.get(e.target))+'"/>';
  html+='</g><g class="atlas-vertices">';for(const pos of scene.nodes){const n=t.by.get(pos.id),isCurrent=pos.id===current,classes=(pos.depth===1?'atlas-root ':'')+(isCurrent?'current ':active.has(pos.id)?'ancestor ':'')+(n.type==='paper_ref'?'paper ':'')+(n.type==='instance'?'instance':'');
   html+='<g class="atlas-vertex '+classes+'" role="button" tabindex="'+(isCurrent?'0':'-1')+'" data-atlas-view="'+view+'" data-atlas-id="'+escape(n.id)+'" data-source-id="'+escape(n.sourceId||'')+'" aria-label="'+escape(displayLabel(t,n).replace(/\s+/g,' ')+(pos.depth===0?'，全树起点':'')+'，'+n.children.length+' 个直接子节点，'+pos.foldedDescendants+' 个下层节点折叠')+'"'+(isCurrent?' aria-current="true"':'')+'><title>'+escape(displayLabel(t,n))+'</title>';
   {html+='<rect class="atlas-label-bg" x="'+pos.x+'" y="'+pos.y+'" width="'+pos.w+'" height="'+pos.h+'" rx="3"/>';pos.labelLines.forEach((line,i)=>{html+='<text class="atlas-node-label" x="'+(pos.x+7)+'" y="'+(pos.y+18+i*(mode==='full'?19:18))+'">'+escape(line)+'</text>';});if(pos.hidden)pos.foldLines.forEach((line,i)=>{html+='<text class="atlas-fold-label" x="'+(pos.x+7)+'" y="'+(pos.y+18+pos.labelLines.length*(mode==='full'?19:18)+i*12)+'">'+escape(line)+'</text>';});}
   html+='</g>';
  }return html+'</g></svg>';
 }
 function html(t,{selected=t.root,view=t.kind}={}){const chosen=t.by.get(selected)||t.by.get(t.root),roots=t.by.get(t.root).children,mode=modes.get(view)||'semantic',scene=layout(t,{selected,mode});return '<div class="complete-atlas '+(mode==='full'?'atlas-full':'atlas-semantic')+'" data-atlas-container="'+view+'"><div class="atlas-tools"><label>主枝 <select data-atlas-root="'+view+'" aria-label="选择完整树的主枝"><option value="'+escape(t.root)+'">全树 · '+roots.length+' 个主枝</option>'+roots.map(id=>'<option value="'+escape(id)+'" '+(route(t,selected).includes(id)?'selected':'')+'>'+escape(t.by.get(id).label.replace(/\s+/g,' '))+'</option>').join('')+'</select></label><button type="button" data-atlas-mode="'+view+'" data-mode="'+(mode==='full'?'semantic':'full')+'">'+(mode==='full'?'主骨架':'完整展开')+'</button><button type="button" data-atlas-reset="'+view+'">回全局</button></div><div class="atlas-fit">'+svg(t,selected,view,{mode})+'</div><div class="atlas-caption"><span class="atlas-current-dot" aria-hidden="true"></span><span data-atlas-caption="'+view+'">'+escape(chosen.id===t.root?'全局 · '+roots.length+(t.kind==='l'?' 个任务':t.kind==='c'?' 个共同难点':' 个主枝')+(t.paperCount?' · '+t.paperCount+' 篇唯一论文':''):chosen.label.replace(/\s+/g,' '))+'</span></div><div class="atlas-legend">'+(mode==='full'?'全部 '+t.nodes.length+' 位置已展开，可横纵滚动核对；并非同时全部可见':'主骨架 '+scene.visibleCount+' / '+t.nodes.length+' 位置 · '+scene.foldedCount+' 位置折叠')+' · 朱红为当前路径'+(t.kind==='a'?'':' · 总览起点仅连接原始根')+'</div></div>';}
 function readableLayout(items,root,{width=820}={}){
  const by=new Map(items.map(n=>[n.id,{...n,children:[...n.children]}])),pad=14,gap=34,maxDepth=Math.max(...items.map(n=>n.depth)),columns=maxDepth+1,safe=Math.max(220,Math.floor(width)),vertical=safe<pad*2+160*columns+gap*maxDepth,colWidth=Math.min(270,(safe-pad*2-gap*maxDepth)/columns),indent=Math.min(18,(safe-pad*2-160)/Math.max(1,maxDepth)),nodes=[],edges=[];
  for(const n of by.values()){const w=vertical?safe-pad*2-n.depth*indent:colWidth,labelLines=lines(n.label,w-18,15),subLines=n.contentTitle?lines(n.contentTitle,w-18,12):[];Object.assign(n,{w,h:n.continuation?Math.max(40,16+lines('原图省略占位 · 查看原题',w-18,12).length*17):Math.max(44,16+labelLines.length*21+subLines.length*17+(n.isInstance?14:0)),labelLines,subLines});}
  if(vertical){let y=pad;function outline(id,parent){const v=by.get(id);nodes.push({...v,x:pad+v.depth*indent,y});if(parent)edges.push({source:parent,target:id});y+=v.h+14;for(const child of v.children)outline(child,id);}outline(root,null);return {width:safe,height:y+pad,nodes,edges,wide:false,vertical:true};}
  function measure(id){const n=by.get(id);n.span=Math.max(n.h+14,n.children.reduce((sum,c)=>sum+measure(c),0));return n.span;}const span=measure(root);
  function place(id,top,parent){const v=by.get(id),n={...v,x:pad+v.depth*(colWidth+gap),y:top+(v.span-v.h)/2};nodes.push(n);if(parent)edges.push({source:parent,target:id});let y=top+(v.span-v.children.reduce((sum,c)=>sum+by.get(c).span,0))/2;for(const child of v.children){place(child,y,id);y+=by.get(child).span;}}place(root,pad,null);return {width:safe,height:span+pad*2,nodes,edges,wide:true,vertical:false};
 }
 function setMode(view,mode){modes.set(view,mode==='full'?'full':'semantic');}
 function bind(doc,getTree,onSelect,onMode){if(doc.__completeAtlasBound)return;doc.__completeAtlasBound=true;
  function reveal(view,id){const t=getTree(view),container=doc.querySelector('[data-atlas-container="'+view+'"]'),region=container?.querySelector('.atlas-fit'),svg=container?.querySelector('.atlas-svg');if(!t||!region||!svg)return;const mode=svg.getAttribute('data-mode'),scene=layout(t,{selected:id,mode}),n=scene.nodes.find(n=>n.id===id);if(!n)return;const scale=mode==='full'?1:(svg.clientWidth||scene.width)/scene.width,top=n.y*scale,left=n.x*scale;if(top<region.scrollTop||top+n.h*scale>region.scrollTop+(region.clientHeight||620))region.scrollTop=Math.max(0,top-60);if(mode==='full'&&(left<region.scrollLeft||left+n.w>region.scrollLeft+(region.clientWidth||680)))region.scrollLeft=Math.max(0,left-30);}
  function choose(view,id){const t=getTree(view);if(t?.by.has(id)){onSelect(view,t.by.get(id));reveal(view,id);}}
  doc.addEventListener('click',event=>{const mode=event.target.closest('[data-atlas-mode]');if(mode){setMode(mode.dataset.atlasMode,mode.dataset.mode);onMode?.(mode.dataset.atlasMode);const button=doc.querySelector('[data-atlas-mode="'+mode.dataset.atlasMode+'"]');button?.focus({preventScroll:true});const current=doc.querySelector('[data-atlas-view="'+mode.dataset.atlasMode+'"][aria-current="true"]');if(current)reveal(mode.dataset.atlasMode,current.dataset.atlasId);return;}const reset=event.target.closest('[data-atlas-reset]');if(reset){const t=getTree(reset.dataset.atlasReset);if(t){setMode(reset.dataset.atlasReset,'semantic');choose(reset.dataset.atlasReset,t.root);onMode?.(reset.dataset.atlasReset);doc.querySelector('[data-atlas-view="'+reset.dataset.atlasReset+'"][data-atlas-id="'+t.root+'"]')?.focus({preventScroll:true});}return;}const target=event.target.closest('[data-atlas-id]');if(target)choose(target.dataset.atlasView,target.dataset.atlasId);});
  doc.addEventListener('change',event=>{if(event.target.matches('[data-atlas-root]'))choose(event.target.dataset.atlasRoot,event.target.value);});
  doc.addEventListener('keydown',event=>{const el=event.target.closest('[data-atlas-id]');if(!el)return;const t=getTree(el.dataset.atlasView),n=t?.by.get(el.dataset.atlasId);if(!n)return;if(['Enter',' '].includes(event.key)){event.preventDefault();choose(el.dataset.atlasView,n.id);return;}if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home','Escape'].includes(event.key))return;event.preventDefault();const siblings=t.by.get(n.parent)?.children||[t.root],index=siblings.indexOf(n.id),id=event.key==='ArrowLeft'?n.parent||n.id:event.key==='ArrowRight'?n.children[0]||n.id:event.key==='ArrowUp'?siblings[Math.max(0,index-1)]:event.key==='ArrowDown'?siblings[Math.min(siblings.length-1,index+1)]:t.root;let target=[...doc.querySelectorAll('[data-atlas-id]')].find(x=>x.dataset.atlasView===el.dataset.atlasView&&x.dataset.atlasId===id);if(!target){choose(el.dataset.atlasView,id);target=[...doc.querySelectorAll('[data-atlas-id]')].find(x=>x.dataset.atlasView===el.dataset.atlasView&&x.dataset.atlasId===id);}if(target){el.setAttribute('tabindex','-1');target.setAttribute('tabindex','0');target.focus({preventScroll:true});const caption=doc.querySelector('[data-atlas-caption="'+el.dataset.atlasView+'"]');if(caption)caption.textContent=displayLabel(t,t.by.get(id)).replace(/\s+/g,' ');}if(event.key==='Escape')choose(el.dataset.atlasView,t.root);});
  doc.addEventListener('mouseover',event=>{const el=event.target.closest('[data-atlas-id]'),t=el&&getTree(el.dataset.atlasView);if(t?.by.has(el.dataset.atlasId)){const caption=doc.querySelector('[data-atlas-caption="'+el.dataset.atlasView+'"]');if(caption)caption.textContent=displayLabel(t,t.by.get(el.dataset.atlasId)).replace(/\s+/g,' ');}});
 }
 return {UI_ROOT,paths,analysis,displayLabel,route,descendantsOf,labelUnits,lines,visibleIds,readableLayout,layout,edge,svg,html,bind,setMode};
})();
return {taskMap,atlas,PAGE_SIZE,CATALOG_PAGE_SIZE,pageKey,initialState,normalizeLiterature,normalizeChallenge,buildModel,startsWith,matchingPaths,children,branch,rootOverview,pathsForPaper,catalogResults,coverage,sanitizeState,reduce,serialize,deserialize,validate};
});
