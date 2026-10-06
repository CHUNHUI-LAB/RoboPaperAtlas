(function(root,factory){const api=factory();if(typeof module==='object'&&module.exports)module.exports=api;if(root)root.AnalysisModel=api;})(typeof window!=='undefined'?window:null,function(){'use strict';
const ROOT='paper-analysis-tree',SECTIONS=['abstract','introduction','method','experiments','limitation'];
function build(schema,mapping,paperId='harnessvln'){
 const active=mapping&&mapping.paperId===paperId?mapping:null,nodes=new Map();
 for(const n of schema.nodes)nodes.set(n.id,{id:n.id,label:n.labelOriginal,parent:n.parentId,order:n.order,templateId:n.id,isInstance:false,contentTitle:active?.contentTitles?.[n.id]||'',source:n});
 if(active)for(const [i,n]of active.expandedNodes.entries()){const template=nodes.get(n.repeatOfSchemaNode),slot=nodes.get(n.expansionSlot);nodes.set(n.nodeId,{id:n.nodeId,label:n.labelOriginal,parent:n.parentId,order:n.parentId===template?.parent?(slot?.order??template?.order??0)+.01*(i+1):template?.order??i,templateId:n.repeatOfSchemaNode,isInstance:true,contentTitle:n.contentTitle||'',source:n});}
 const children=new Map();for(const n of nodes.values()){if(!children.has(n.parent))children.set(n.parent,[]);children.get(n.parent).push(n);}for(const xs of children.values())xs.sort((a,b)=>a.order-b.order);
 const answers=new Map((active?.answers||[]).map(a=>[a.nodeId,a])),questions=active?.unresolvedQuestions||[];return {paperId,schema,mapping:active,nodes,children,answers,questions};
}
const children=(m,id)=>m.children.get(id)||[];
function ancestors(m,id){const list=[],seen=new Set();while(m.nodes.has(id)&&!seen.has(id)){seen.add(id);list.unshift(id);id=m.nodes.get(id).parent;}return list;}
function sectionOf(m,id){return ancestors(m,id).find(id=>SECTIONS.includes(id))||null;}
function descendants(m,id){return children(m,id).flatMap(n=>[n.id,...descendants(m,n.id)]);}
function initial(m,returnContext=null){return {paperId:m.paperId,mobilePane:'focus',focus:'method',selected:m.nodes.has('method.module1.why')?'method.module1.why':'method',pages:{},drawer:null,drawerTab:'answer',directoryScope:'all',query:'',returnContext};}
function pageSize(m,focus){return children(m,focus).some(n=>children(m,n.id).length)?2:4;}
function branch(m,s){const all=children(m,s.focus),size=pageSize(m,s.focus),maxPage=Math.max(0,Math.ceil(all.length/size)-1),page=Math.min(Math.max(0,s.pages[s.focus]||0),maxPage);return {all,size,page,maxPage,items:all.slice(page*size,(page+1)*size)};}
function sanitize(m,s){s={...initial(m),...s,pages:{...(s?.pages||{})}};if(!m.nodes.has(s.focus))s.focus=ROOT;if(!m.nodes.has(s.selected))s.selected=s.focus;if(!['evidence','directory','unresolved','scope',null].includes(s.drawer))s.drawer=null;if(!['answer','sources','scope'].includes(s.drawerTab))s.drawerTab='answer';s.query=typeof s.query==='string'?s.query:'';return s;}
function locate(m,s,id){if(!m.nodes.has(id))return s;const next={...s,pages:{...s.pages},selected:id,drawer:null,mobilePane:'focus'};const route=ancestors(m,id);for(let i=1;i<route.length;i++){const parent=route[i-1],index=children(m,parent).findIndex(n=>n.id===route[i]);next.pages[parent]=Math.floor(index/pageSize(m,parent));}const n=m.nodes.get(id);next.focus=children(m,id).length?id:n.parent||id;const all=children(m,next.focus),size=pageSize(m,next.focus),index=all.findIndex(n=>n.id===id);if(index>=0)next.pages[next.focus]=Math.floor(index/size);return next;}
function reduce(m,s,a){const next={...s,pages:{...s.pages}};switch(a.type){
 case 'mobile-pane':next.mobilePane=a.pane==='overview'?'overview':'focus';break;
 case 'select':if(!m.nodes.has(a.id))return s;next.selected=a.id;break;
 case 'enter':return locate(m,s,a.id);
 case 'back':next.focus=m.nodes.get(s.focus)?.parent||ROOT;next.selected=s.focus;break;
 case 'page':next.pages[next.focus]=Math.max(0,a.page);next.selected=next.focus;break;
 case 'overview':next.focus=ROOT;next.selected=ROOT;next.drawer=null;break;
 case 'layer-directory':next.drawer='directory';next.directoryScope=s.focus;next.query='';break;
 case 'drawer':next.drawer=a.drawer;if(a.drawer==='directory')next.directoryScope='all';next.drawerTab=a.tab||'answer';if(a.id&&m.nodes.has(a.id))next.selected=a.id;break;
 case 'close':next.drawer=null;break;
 case 'tab':next.drawerTab=a.tab;break;
 case 'search':next.directoryScope='all';next.query=a.query;next.drawer='directory';break;
 default:return s;
 }return sanitize(m,next);}
function search(m,query=''){const q=query.toLocaleLowerCase().trim();return [ROOT,...descendants(m,ROOT)].map(id=>m.nodes.get(id)).filter(n=>!q||[n.label,n.contentTitle,n.id,m.answers.get(n.id)?.answer,...m.questions.filter(x=>x.nodeId===n.id).map(x=>x.question)].join(' ').toLocaleLowerCase().includes(q));}
function compactLabel(text,max=56){const str=String(text);return str.length>max?{text:str.slice(0,max)+'…',truncated:true}:{text:str,truncated:false};}
function previewLabel(text,width,lines=2){const maxUnits=Math.max(6,Math.floor((width-51)/17)*lines);let out='',used=0;for(const c of String(text).replace(/\s+/g,' ')){const u=/[\u0020-\u007e]/.test(c)?.52:1;if(used+u>maxUnits)return {text:out+'…',truncated:true};out+=c;used+=u;}return {text:out,truncated:false};}
function layout(m,s,width=820){const b=branch(m,s);if(width<580){const nodes=[{id:s.focus,x:16,y:24,w:Math.max(250,width-32),h:110,depth:0}],edges=[];b.items.forEach((n,i)=>{nodes.push({id:n.id,x:34,y:174+i*128,w:Math.max(230,width-56),h:104,depth:1,previewTotal:children(m,n.id).length,previewShown:0});edges.push({source:s.focus,target:n.id});});return {width:Math.max(width,298),height:Math.max(420,186+b.items.length*128),nodes,edges,branch:b,wide:false,vertical:true};}const wide=width>=720,pad=16,rootW=wide?144:Math.min(160,width*.37),midW=wide?218:Math.max(185,width-rootW-64),leafW=wide?Math.max(210,width-rootW-midW-132):0,gap=wide?50:32,midX=pad+rootW+gap,leafX=midX+midW+gap,nodes=[],edges=[];let y=32;
 const add=(id,x,y,w,h,depth)=>{const n={id,x,y,w,h,depth};nodes.push(n);return n;};
 for(const child of b.items){const grandchildren=wide?children(m,child.id).slice(0,4):[],h=Math.max(118,grandchildren.length*100+(grandchildren.length-1)*13),cy=y+h/2-48;const cn=add(child.id,midX,cy,midW,96,1);edges.push({source:s.focus,target:child.id});let gy=y;for(const g of grandchildren){add(g.id,leafX,gy,leafW,100,2);edges.push({source:child.id,target:g.id});gy+=113;}cn.previewTotal=children(m,child.id).length;cn.previewShown=grandchildren.length;y+=h+42;}
 const height=Math.max(480,y),root=add(s.focus,pad,height/2-55,rootW,110,0);return {width:wide?width:Math.max(width,midX+midW+pad),height,nodes,edges,branch:b,wide};}
function forWidth(m,s,width){const scene=layout(m,s,width);if(scene.nodes.some(n=>n.id===s.selected))return s;const located=locate(m,s,s.selected);return {...s,focus:located.focus,pages:located.pages};}
function overviewLayout(m,s=initial(m),mobile=false){
 const width=500,row=52,gap=20,visible=new Set([ROOT,...SECTIONS,...ancestors(m,s.selected)]),selected=m.nodes.get(s.selected),context=children(m,s.selected).length?s.selected:selected?.parent;
 if(context){const all=children(m,context),index=all.findIndex(n=>n.id===s.selected),start=index>=0?Math.floor(index/4)*4:0;all.slice(start,start+4).forEach(n=>visible.add(n.id));}
 const nodes=[],edges=[];let y=24;for(const section of SECTIONS){const extra=descendants(m,section).filter(id=>visible.has(id)),height=Math.max(row,extra.length*row);const rootY=y+height/2;nodes.push({id:section,x:122,y:rootY,w:148,h:40,depth:1,section});extra.forEach((id,i)=>{const depth=ancestors(m,id).length-1,x=282+Math.min(3,Math.max(0,depth-2))*15;nodes.push({id,x,y:y+i*row+row/2,w:width-x-10,h:40,depth,section});});y+=height+gap;}
 const height=y+4;nodes.unshift({id:ROOT,x:8,y:height/2,w:100,h:50,depth:0});const present=new Set(nodes.map(n=>n.id));for(const n of nodes){const parent=m.nodes.get(n.id)?.parent;if(parent&&present.has(parent))edges.push({source:parent,target:n.id});n.totalChildren=children(m,n.id).length;n.shownChildren=children(m,n.id).filter(c=>present.has(c.id)).length;n.foldedChildren=n.totalChildren-n.shownChildren;n.totalDescendants=descendants(m,n.id).length;}
 if(mobile){nodes.forEach((n,i)=>{n.x=14+n.depth*18;n.y=26+i*54;n.w=360-n.x-14;n.h=44;});return {width:360,height:nodes.length*54+20,row:54,nodes,edges,mobile:true,visibleCount:nodes.length,totalCount:m.nodes.size,foldedCount:m.nodes.size-nodes.length};}
 return {width,height,row,nodes,edges,mobile:false,visibleCount:nodes.length,totalCount:m.nodes.size,foldedCount:m.nodes.size-nodes.length};
}

function validate(m){const errors=[];if(m.schema.nodes.length!==59)errors.push('Original 59 template nodes changed');for(const n of m.nodes.values()){if(n.parent&&!m.nodes.has(n.parent))errors.push('Missing parent '+n.id);if(n.isInstance&&!m.nodes.has(n.templateId))errors.push('Missing template '+n.id);}for(const a of m.answers.values()){if(!m.nodes.has(a.nodeId))errors.push('Unknown answer node');if(a.state!==a.status)errors.push('State alias mismatch');if(!a.sourceLocators?.length)errors.push('Answer lacks source locator');}if(m.mapping){if(m.mapping.existingStageStateMutation!==false)errors.push('Stage mutation');if(m.questions.length!==6)errors.push('Unresolved questions lost');}return errors;}
return {ROOT,SECTIONS,build,children,ancestors,sectionOf,descendants,initial,pageSize,branch,sanitize,locate,reduce,search,compactLabel,previewLabel,layout,forWidth,overviewLayout,validate};
});
