(function(root,factory){const shared=typeof module==='object'&&module.exports?require('../model.js').atlas:root?.TreeModel?.atlas;const api=factory(shared);if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.AnalysisModel=api;})(typeof window!=='undefined'?window:null,function(T){'use strict';
const ROOT='paper-analysis-tree',SECTIONS=['abstract','introduction','method','experiments','limitation'];
function build(schema,mapping,paperId='harnessvln',resources={}){
 const candidate=mapping?.paperId?mapping:mapping?.[paperId],active=candidate?.paperId===paperId?candidate:null,nodes=new Map();
 for(const n of schema.nodes)nodes.set(n.id,{id:n.id,label:n.labelOriginal,parent:n.parentId,order:n.order,templateId:n.id,isInstance:false,contentTitle:active?.contentTitles?.[n.id]||'',source:n});
 if(active)for(const [i,n]of active.expandedNodes.entries()){const template=nodes.get(n.repeatOfSchemaNode),slot=nodes.get(n.expansionSlot);nodes.set(n.nodeId,{id:n.nodeId,label:n.labelOriginal,parent:n.parentId,order:n.parentId===template?.parent?(slot?.order??template?.order??0)+.01*(i+1):template?.order??i,templateId:n.repeatOfSchemaNode,isInstance:true,contentTitle:n.contentTitle||'',source:n});}
 const children=new Map();for(const n of nodes.values()){if(!children.has(n.parent))children.set(n.parent,[]);children.get(n.parent).push(n);}for(const xs of children.values())xs.sort((a,b)=>a.order-b.order);
 const answers=new Map((active?.answers||[]).map(a=>[a.nodeId,a])),questions=active?.unresolvedQuestions||[],ledger=resources.ledgersByPaperId?.[paperId]||null;return {paperId,schema,mapping:active,nodes,children,answers,questions,ledger,evidence:new Map((ledger?.records||[]).map(r=>[r.evidenceRecordId||r.id,r]))};
}
function mappingFor(bundle,paperId){return bundle?.mappingsByPaperId?.[paperId]||(bundle?.mapping?.paperId===paperId?bundle.mapping:null);}
function fromBundle(bundle,paperId='harnessvln'){return build(bundle.schema,mappingFor(bundle,paperId),paperId,bundle);}
function counts(m){return {original:m.schema.nodes.length,instances:m.mapping?.expandedNodes.length||0,nodes:m.nodes.size,answers:m.answers.size,unknowns:m.questions.length,implementationUnknown:[...m.answers.values()].filter(a=>a.codeEvidence?.status==='not_reviewed_implementation_unknown').length,implementationVerified:[...m.answers.values()].filter(a=>a.codeEvidence?.status==='implementation_verified').length};}
function questionsFor(m,id){const a=m.answers.get(id),gaps=new Set(a?.sourceGapIds||[]);return m.questions.filter(q=>q.nodeId===id||q.id&&gaps.has(q.id));}
function searchQuestions(m,query=''){const q=query.toLocaleLowerCase().trim();return m.questions.filter(x=>!q||JSON.stringify(x).toLocaleLowerCase().includes(q));}
const children=(m,id)=>m.children.get(id)||[];
function ancestors(m,id){const list=[],seen=new Set();while(m.nodes.has(id)&&!seen.has(id)){seen.add(id);list.unshift(id);id=m.nodes.get(id).parent;}return list;}
function sectionOf(m,id){return ancestors(m,id).find(id=>SECTIONS.includes(id))||null;}
function descendants(m,id){return children(m,id).flatMap(n=>[n.id,...descendants(m,n.id)]);}
function initial(m,returnContext=null){return {paperId:m.paperId,mobilePane:'overview',focus:ROOT,selected:ROOT,pages:{},drawer:null,drawerTab:'answer',directoryScope:'all',query:'',questionId:null,returnContext};}
function pageSize(m,focus){return focus===ROOT?5:4;}
function isContinuation(n){return n.label.trim()==='...';}
function branch(m,s){const all=children(m,s.focus),size=pageSize(m,s.focus),substantive=all.filter(n=>!isContinuation(n)),maxPage=Math.max(0,Math.ceil(substantive.length/size)-1),page=Math.min(Math.max(0,s.pages[s.focus]||0),maxPage);let index=0;const items=all.filter(n=>{const itemPage=Math.min(maxPage,Math.floor(index/size));if(!isContinuation(n))index++;return itemPage===page;});return {all,size,page,maxPage,items,substantiveTotal:substantive.length,continuationCount:all.length-substantive.length};}
function pageFor(m,parent,id){const all=children(m,parent),index=all.findIndex(n=>n.id===id),size=pageSize(m,parent),before=all.slice(0,Math.max(0,index)).filter(n=>!isContinuation(n)).length,maxPage=Math.max(0,Math.ceil(all.filter(n=>!isContinuation(n)).length/size)-1);return Math.min(maxPage,Math.floor(before/size));}
function sanitize(m,s){s={...initial(m),...s,pages:{...(s?.pages||{})}};if(!m.nodes.has(s.focus))s.focus=ROOT;if(!m.nodes.has(s.selected))s.selected=s.focus;if(!['evidence','directory','unresolved','scope',null].includes(s.drawer))s.drawer=null;if(!['answer','sources','scope'].includes(s.drawerTab))s.drawerTab='answer';s.query=typeof s.query==='string'?s.query:'';if(!m.questions?.some(q=>q.id===s.questionId))s.questionId=null;return s;}
function locate(m,s,id){if(!m.nodes.has(id))return s;const next={...s,pages:{...s.pages},selected:id,drawer:null,mobilePane:'focus'};const route=ancestors(m,id);for(let i=1;i<route.length;i++){const parent=route[i-1],index=children(m,parent).findIndex(n=>n.id===route[i]);next.pages[parent]=pageFor(m,parent,route[i]);}const n=m.nodes.get(id);next.focus=children(m,id).length?id:n.parent||id;const all=children(m,next.focus),size=pageSize(m,next.focus),index=all.findIndex(n=>n.id===id);if(index>=0)next.pages[next.focus]=pageFor(m,next.focus,id);return next;}
function reduce(m,s,a){const next={...s,pages:{...s.pages}};switch(a.type){
 case 'mobile-pane':next.mobilePane=a.pane==='overview'?'overview':'focus';break;
 case 'select':if(!m.nodes.has(a.id))return s;next.selected=a.id;break;
 case 'enter':return locate(m,s,a.id);
 case 'back':next.focus=m.nodes.get(s.focus)?.parent||ROOT;next.selected=s.focus;break;
 case 'collapse':if(!m.nodes.has(a.id))return s;next.focus=m.nodes.get(a.id)?.parent||ROOT;next.selected=a.id;next.drawer=null;break;
 case 'page':next.pages[next.focus]=Math.max(0,a.page);next.selected=next.focus;break;
 case 'overview':next.focus=ROOT;next.selected=ROOT;next.drawer=null;break;
 case 'layer-directory':next.drawer='directory';next.directoryScope=s.focus;next.query='';break;
 case 'gap':if(!m.questions.some(q=>q.id===a.id))return s;next.drawer='unresolved';next.questionId=a.id;break;
 case 'drawer':next.questionId=null;next.drawer=a.drawer;if(a.drawer==='directory')next.directoryScope='all';next.drawerTab=a.tab||'answer';if(a.id&&m.nodes.has(a.id))next.selected=a.id;break;
 case 'close':next.drawer=null;break;
 case 'tab':next.drawerTab=a.tab;break;
 case 'search':next.directoryScope='all';next.query=a.query;next.drawer='directory';break;
 default:return s;
 }return sanitize(m,next);}
function search(m,query=''){const q=query.toLocaleLowerCase().trim();return [ROOT,...descendants(m,ROOT)].map(id=>m.nodes.get(id)).filter(n=>!q||[n.label,n.contentTitle,n.id,m.answers.get(n.id)?.answer,...questionsFor(m,n.id).map(x=>x.question||x.topic+' '+x.detail)].join(' ').toLocaleLowerCase().includes(q));}
function compactLabel(text,max=56){const str=String(text);return str.length>max?{text:str.slice(0,max)+'…',truncated:true}:{text:str,truncated:false};}
function previewLabel(text,width,lines=2){const maxUnits=Math.max(6,Math.floor((width-51)/17)*lines);let out='',used=0;for(const c of String(text).replace(/\s+/g,' ')){const u=/[\u0020-\u007e]/.test(c)?.52:1;if(used+u>maxUnits)return {text:out+'…',truncated:true};out+=c;used+=u;}return {text:out,truncated:false};}
function layout(m,s,width=820){
 // Expand from focus only; selected marks the reading position independently.
 // Horizontal text vertices use complete labels and internally scroll on narrow
 // screens. Ancestors and the page of siblings stay in the same connected tree.
 const root=sectionOf(m,s.focus)||ROOT,expanded=new Set(ancestors(m,s.focus)),routeIds=ancestors(m,s.focus),visible=new Map(),pad=14,gap=34;
 function collect(id,depth){const n=m.nodes.get(id),out={id,depth,children:[]};visible.set(id,out);if(expanded.has(id)){const group=branch(m,{...s,focus:id}),items=[...group.items],next=routeIds.find(child=>m.nodes.get(child)?.parent===id);if(next&&!items.some(n=>n.id===next)){items.push(m.nodes.get(next));items.sort((a,b)=>children(m,id).indexOf(a)-children(m,id).indexOf(b));}for(const child of items){out.children.push(child.id);collect(child.id,depth+1);}}}collect(root,0);
 const items=[...visible.values()].map(item=>{const n=m.nodes.get(item.id);return {...item,label:n.label,contentTitle:n.contentTitle,isInstance:n.isInstance,continuation:isContinuation(n),previewTotal:children(m,n.id).length,previewShown:item.children.length};});
 return {...T.readableLayout(items,root,{width}),branch:branch(m,s)};
}

function forWidth(m,s,width){if(layout(m,s,width).nodes.some(n=>n.id===s.selected))return s;const located=locate(m,s,s.selected);return {...s,focus:located.focus,pages:located.pages};}
function overviewLayout(m,s=initial(m),mobile=false){
 const tree=T.analysis(m),scene=T.layout(tree,{width:mobile?360:720,selected:s.selected,mode:'full'});
 for(const n of scene.nodes){n.totalChildren=children(m,n.id).length;n.shownChildren=n.totalChildren;n.foldedChildren=0;n.totalDescendants=descendants(m,n.id).length;}
 return {...scene,mobile,visibleCount:m.nodes.size,totalCount:m.nodes.size,foldedCount:0};
}

function validate(m){const errors=[];if(m.schema.nodes.length!==59)errors.push('Original 59 template nodes changed');for(const n of m.nodes.values()){if(n.parent&&!m.nodes.has(n.parent))errors.push('Missing parent '+n.id);if(n.isInstance&&(!m.nodes.has(n.templateId)||!m.schema.nodes.some(x=>x.id===n.source.expansionSlot)))errors.push('Missing template or expansion slot '+n.id);}
 for(const a of m.answers.values()){if(!m.nodes.has(a.nodeId))errors.push('Unknown answer node');if(a.state!==a.status)errors.push('State alias mismatch');if(!a.sourceLocators?.length)errors.push('Answer lacks source locator');for(const gap of a.sourceGapIds||[])if(!m.questions.some(q=>q.id===gap))errors.push('Unknown source gap '+gap);for(const id of a.evidenceRecordIds||[])if(m.ledger&&!m.evidence.has(id))errors.push('Missing paper-scoped evidence '+id);}
 if(m.mapping){if(m.mapping.existingStageStateMutation!==false)errors.push('Stage mutation');if(m.answers.size!==m.mapping.answers.length)errors.push('Duplicate answer nodes');if(m.nodes.size!==m.schema.nodes.length+m.mapping.expandedNodes.length)errors.push('Duplicate instance nodes');const expected={harnessvln:[13,47,6],navharness:[18,51,12]}[m.paperId];if(m.mapping.analysisKind==='partial_selected_section_analysis'){if(m.mapping.expandedNodes.length||m.nodes.size!==59)errors.push('Scoped analysis changes template');}else if(!expected||JSON.stringify([m.mapping.expandedNodes.length,m.answers.size,m.questions.length])!==JSON.stringify(expected))errors.push('Reviewed paper contract changed');if(m.paperId==='navharness'){if(m.mapping.sourceVersion!=='2609.34276v1')errors.push('NavHarness fixed identity changed');const status={};for(const a of m.answers.values())status[a.status]=(status[a.status]||0)+1;if(status.evidence_linked!==43||status.author_claim_only!==6||status.partially_reported!==2)errors.push('NavHarness claim status changed');if(counts(m).implementationUnknown!==20||counts(m).implementationVerified!==0)errors.push('Implementation boundary changed');if(new Set(m.questions.map(q=>q.id)).size!==12||m.questions.some((q,i)=>q.id!=='U'+String(i+1).padStart(2,'0')||!q.topic||!q.detail||!q.status||q.nodeId))errors.push('Unknown question contract changed');}
 for(const q of m.questions){if(q.nodeId&&!m.nodes.has(q.nodeId))errors.push('Unknown question node');for(const id of q.evidenceRecordIds||[])if(m.ledger&&!m.evidence.has(id))errors.push('Unknown question evidence '+id);}if(m.ledger?.paperId!==undefined&&m.ledger.paperId!==m.paperId)errors.push('Cross-paper ledger');}
 return errors;}
return {ROOT,SECTIONS,isContinuation,pageFor,build,fromBundle,mappingFor,counts,questionsFor,searchQuestions,children,ancestors,sectionOf,descendants,initial,pageSize,branch,sanitize,locate,reduce,search,compactLabel,previewLabel,layout,forWidth,overviewLayout,validate};
});
