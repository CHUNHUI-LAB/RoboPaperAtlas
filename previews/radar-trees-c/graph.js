/* Public-only local projection. No fetch, external libraries, persistence or graph writes. */
(function (root, factory) {
  'use strict';
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  if (root && root.document) {
    root.RadarGraph = api;
    try { root.radarGraphApp = api.mount(root.document, root.RADAR_GRAPH_DATA); }
    catch (error) { const fallback = root.document.getElementById('load-error'); if (fallback) fallback.hidden = false; root.console?.error('Graph initialization failed:', error); }
  }
})(typeof window !== 'undefined' ? window : null, function () {
  'use strict';
  const representatives = {'route-runtime':'harnessvln','route-spatial-memory':'navharness','route-context':'agenticnav-tool-harness','route-learned-policy':'qwen-robotnav','route-protocol':'krantz2020vlnce'};
  const WIDTH = 1280, MAX_ZOOM = 4, NS = 'http://www.w3.org/2000/svg';
  const attrNames = {author_claim:'作者主张', direct_observation:'原文核读', curator_inference:'编辑推断', curator_summary:'编辑归纳', curator_organization:'编辑组织'};
  const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const safeId = value => String(value).replace(/[^a-zA-Z0-9_-]/g, '_');
  const initialState = () => ({mode:'baseline', task:'all', search:'', selected:null, context:null, expandedRoutes:new Set(), expandedGroups:new Set(), expandedChallenges:new Set(), focus:true, tab:'overview', zoom:1, selectionNotice:''});
  function readingScope(p) {
    const scope=p.read_scope||p.source_scope;
    if(scope==='section')return '指定正文段落';
    if(scope==='abstract'||scope==='primary_complete_abstract')return '完整摘要';
    if(scope==='metadata')return '书目线索';
    return '证据范围待说明';
  }
  function activePapers(data, state) { return state.mode === 'weekly' ? data.candidates : data.papers; }
  function filteredPapers(data, state) {
    const query = state.search.toLocaleLowerCase().trim();
    const labels = Object.fromEntries([...data.tasks,...data.routes].map(n=>[n.id,n.label+' '+n.subtitle]));
    return activePapers(data,state).filter(p => (state.task === 'all' || p.tasks.includes(state.task)) && (!query || [p.short_name,p.title,p.challenge,p.problem,p.insight,p.author_solution,p.pipeline,p.overview_zh,p.abstract_summary_zh,p.harness_relation?.basis,p.canonical_id,...p.tasks.map(x=>labels[x]),...p.routes.map(x=>labels[x])].join(' ').toLocaleLowerCase().includes(query)));
  }
  function coverageCounts(data, state, scene) {
    const total = new Set(activePapers(data,state).map(p=>p.canonical_id)).size;
    const matched = new Set(scene.papers.map(p=>p.canonical_id)).size;
    return {total, matched, visible:scene.uniqueVisible, acrossTrees:scene.allTreeUniqueVisible, collapsed:matched-scene.uniqueVisible, excluded:total-matched};
  }
  function reconcileSelection(data, state) {
    if(state.selected?.canonical && !filteredPapers(data,state).some(p=>p.canonical_id===state.selected.canonical)) {
      state.selected=null;state.context=null;state.tab='overview';
      state.selectionNotice='筛选变更已清除原选中论文；请在当前结果中重新选择。';
    }
  }
  function buildScene(data, state) {
    const papers = filteredPapers(data,state), byPaper = Object.fromEntries(papers.map(p=>[p.canonical_id,p]));
    const nodes=[],edges=[]; const selectedCanonical=state.selected?.canonical;
    const addNode = n => (nodes.push(n), n);
    const addEdge = (source,target,extra={}) => edges.push({id:source+'--'+target,source,target,attribution:'curator_organization',...extra});
    const shownRoutes = data.routes.filter(r=>state.task==='all'||data.task_routes.some(e=>e.source===state.task&&e.target===r.id));
    const visiblePapers=new Map();
    let leftY=45;
    for(const route of shownRoutes){
      const all=papers.filter(p=>p.routes.includes(route.id));
      const preferred = state.mode==='baseline' ? all.find(p=>p.canonical_id===representatives[route.id]) : null;
      let visible = state.expandedRoutes.has(route.id) ? all : (preferred?[preferred]:all.slice(0,1));
      if(selectedCanonical && all.some(p=>p.canonical_id===selectedCanonical) && !visible.some(p=>p.canonical_id===selectedCanonical)) visible.push(byPaper[selectedCanonical]);
      const block=Math.max(137,visible.length*86+12);
      const routeNode=addNode({id:route.id,kind:'route',label:route.label,subtitle:route.subtitle,x:218,y:leftY+block/2-54,w:184,h:108,full:route.full_label,total:all.length,visible:visible.length,expanded:state.expandedRoutes.has(route.id),canExpand:all.length>1});
      visible.forEach((p,i)=>{
        const entry=visiblePapers.get(p.canonical_id)||{paper:p,anchors:[]};
        entry.anchors.push(leftY+i*86+7);visiblePapers.set(p.canonical_id,entry);
      });
      leftY+=block+11;
    }
    // Aggregate the view by canonical identity; source memberships remain unchanged.
    let paperBottom=45;
    const entries=[...visiblePapers.values()].map(e=>({...e,anchor:e.anchors.reduce((a,b)=>a+b,0)/e.anchors.length})).sort((a,b)=>a.anchor-b.anchor||a.paper.canonical_id.localeCompare(b.paper.canonical_id));
    for(const {paper:p,anchor} of entries){
      const y=Math.max(anchor,paperBottom),routeIds=shownRoutes.filter(r=>p.routes.includes(r.id)).map(r=>r.id);
      const n=addNode({id:'paper-'+p.canonical_id,kind:'paper',routeIds,routeCount:p.routes.length,canonical:p.canonical_id,paper:p,label:p.short_name,subtitle:state.mode==='weekly'?p.versioned_id+' · 摘要候选':(p.year?p.year+' · ':'')+readingScope(p),x:443,y,w:195,h:68,candidate:state.mode==='weekly',full:p.title});
      routeIds.forEach(id=>{const placement=p.placements?.find(x=>x.node_id===id);addEdge(id,n.id,{candidate:state.mode==='weekly',partial:placement?.fit==='partial'});});
      paperBottom=y+86;
    }
    const leftHeight=Math.max(leftY+22,paperBottom+22);
    const shownTasks=data.tasks.filter(t=>state.task==='all'||t.id===state.task);
    shownTasks.forEach((task,i)=>{
      const y=shownTasks.length===1 ? leftHeight/2-34 : 76+i*Math.max(146,(leftHeight-200)/(shownTasks.length-1));
      addNode({id:task.id,kind:'task',label:task.label,subtitle:task.subtitle,x:20,y,w:171,h:72,full:task.full_label});
      data.task_routes.filter(e=>e.source===task.id&&shownRoutes.some(r=>r.id===e.target)).forEach(e=>addEdge(e.source,e.target));
    });
    let rightY=45;
    const groups=data.groups.filter(g=>papers.some(p=>p.groups.includes(g.id)));
    for(const group of groups){
      const all=papers.filter(p=>p.groups.includes(group.id));
      let visible=state.expandedGroups.has(group.id)?all:all.slice(0,1);
      if(selectedCanonical&&all.some(p=>p.canonical_id===selectedCanonical)&&!visible.some(p=>p.canonical_id===selectedCanonical)) visible.push(byPaper[selectedCanonical]);
      let childY=rightY; const groupChildren=[];
      for(const p of visible){
        const cid='challenge-'+group.id+'-'+p.canonical_id;
        const problem=p.mode==='weekly'?p.problem:p.challenge;
        const ch=addNode({id:cid,kind:'challenge',canonical:p.canonical_id,paper:p,label:problem,subtitle:p.short_name,x:971,y:childY,w:283,h:93,full:problem,expanded:state.expandedChallenges.has(p.canonical_id),canExpand:true,candidate:state.mode==='weekly'});
        groupChildren.push(ch); addEdge('group-'+group.id,cid,{candidate:state.mode==='weekly'});
        childY+=106;
        if(state.expandedChallenges.has(p.canonical_id)){
          const iid='insight-'+group.id+'-'+p.canonical_id, eid='evidence-'+group.id+'-'+p.canonical_id;
          addNode({id:iid,kind:'insight',canonical:p.canonical_id,paper:p,label:p.mode==='weekly'?p.author_solution:p.insight,subtitle:p.mode==='weekly'?'作者方案 · 摘要级':attrNames[p.insight_attribution]||'编辑归纳',x:986,y:childY,w:268,h:93,full:p.mode==='weekly'?p.author_solution:p.insight,candidate:state.mode==='weekly'});
          addEdge(cid,iid,{vertical:true,candidate:state.mode==='weekly'}); childY+=106;
          addNode({id:eid,kind:'evidence',canonical:p.canonical_id,paper:p,label:p.mode==='weekly'?'摘要证据 · 全文待核':p.evidence.length+' 条指定证据 · 未独立复现',subtitle:p.mode==='weekly'?'查看位置贴合度与后续核查':'查看来源段落与适用条件',x:1002,y:childY,w:252,h:60,candidate:state.mode==='weekly'});
          addEdge(iid,eid,{vertical:true,candidate:state.mode==='weekly'});childY+=77;
        }
      }
      const block=Math.max(145,childY-rightY+24);
      addNode({id:'group-'+group.id,kind:'group',group:group.id,label:group.label,subtitle:group.subtitle,x:719,y:rightY+Math.min(94,block/2)-51,w:196,h:108,full:group.note,total:all.length,visible:visible.length,expanded:state.expandedGroups.has(group.id),canExpand:all.length>1});
      rightY+=block+15;
    }
    // Every bridge joins the same canonical paper's two projections. No academic relations are inferred.
    for(const paperNode of nodes.filter(n=>n.kind==='paper')){
      const challenges=nodes.filter(n=>n.kind==='challenge'&&n.canonical===paperNode.canonical);
      for(const challenge of challenges) addEdge(paperNode.id,challenge.id,{cross:true,same_paper:paperNode.canonical,candidate:state.mode==='weekly'});
    }
    let related=new Set();
    const sel=state.selected;
    if(sel?.canonical && byPaper[sel.canonical]) related.add(sel.canonical);
    if(sel?.kind==='task') papers.filter(p=>p.tasks.includes(sel.id)).forEach(p=>related.add(p.canonical_id));
    if(sel?.kind==='route') papers.filter(p=>p.routes.includes(sel.id)).forEach(p=>related.add(p.canonical_id));
    if(sel?.kind==='group') papers.filter(p=>p.groups.includes(sel.group)).forEach(p=>related.add(p.canonical_id));
    const relevant=papers.filter(p=>related.has(p.canonical_id));
    const active=new Set();
    for(const node of nodes){
      if(node.canonical&&related.has(node.canonical))active.add(node.id);
      if(node.kind==='task'&&relevant.some(p=>p.tasks.includes(node.id)))active.add(node.id);
      if(node.kind==='route'&&relevant.some(p=>p.routes.includes(node.id)))active.add(node.id);
      if(node.kind==='group'&&relevant.some(p=>p.groups.includes(node.group)))active.add(node.id);
      node.selected=sel?.id&&nodes.some(n=>n.id===sel.id)?node.id===sel.id:node===nodes.find(n=>n.canonical===sel?.canonical&&n.kind===sel?.kind);
      node.active=active.has(node.id);
      node.dim=state.focus&&related.size>0&&!node.active;
    }
    edges.forEach(e=>{e.active=active.has(e.source)&&active.has(e.target);e.dim=state.focus&&related.size>0&&!e.active;});
    return {nodes,edges,papers,width:WIDTH,height:Math.max(670,leftHeight,rightY+20),methodRoutes:shownRoutes.filter(r=>papers.some(p=>p.routes.includes(r.id))).length,structuralRoutes:shownRoutes.length,routeLinks:edges.filter(e=>shownRoutes.some(r=>r.id===e.source)&&e.target.startsWith('paper-')).length,uniqueVisible:new Set(nodes.filter(n=>n.kind==='paper').map(n=>n.canonical)).size,allTreeUniqueVisible:new Set(nodes.filter(n=>n.canonical).map(n=>n.canonical)).size,empty:papers.length===0};
  }
  function wrapText(text, maxUnits, maxLines=3) {
    const out=[];let line='',units=0;
    for(const char of String(text??'')){
      const u=/[\u0020-\u007e]/.test(char)?.55:1;
      if(units+u>maxUnits&&line){out.push(line);line='';units=0;}
      line+=char;units+=u;
    }
    if(line)out.push(line);
    if(out.length>maxLines){out.length=maxLines;out[maxLines-1]=out[maxLines-1].replace(/.{1,2}$/u,'')+'…';}
    return out;
  }
  function computeFitZoom(viewportWidth, viewportHeight, sceneWidth, sceneHeight) {
    if(!(viewportWidth>0&&viewportHeight>0&&sceneWidth>0&&sceneHeight>0))return 1;
    return Math.min(1,(viewportHeight*sceneWidth)/(sceneHeight*viewportWidth));
  }
  function applyAction(state, action) {
    if(action.type==='mode'){
      if(state.mode===action.mode)return state;
      const next=initialState();next.mode=action.mode;Object.assign(state,next);
    }
    if(action.type==='overview'){const mode=state.mode;Object.assign(state,initialState());state.mode=mode;}
    if(action.type==='clearFilters'){state.search='';state.task='all';state.selectionNotice='';}
    if(action.type==='showAll'){
      action.data.routes.forEach(r=>state.expandedRoutes.add(r.id));
      action.data.groups.forEach(g=>state.expandedGroups.add(g.id));
    }
    if(action.type==='collapse'){
      state.expandedRoutes.clear();state.expandedGroups.clear();
      // Keep the selected paper and its evidence branch visible in representative mode.
    }
    if(action.type==='backDirection'&&state.context){state.selected={...state.context};state.tab='overview';state.selectionNotice='';}
    if(action.type==='select'||action.type==='toggle'){
      const n=action.node;
      if(action.type==='select'){
        const same=state.selected?.kind===n.kind&&state.selected?.id===n.id&&state.selected?.canonical===n.canonical;
        state.selectionNotice='';state.selected={kind:n.kind,id:n.id,canonical:n.canonical,group:n.group};
        if(['task','route','group'].includes(n.kind))state.context={kind:n.kind,id:n.id,group:n.group};
        if(n.canonical&&n.paper){
          const c=state.context,p=n.paper;
          const fits=c&&(c.kind==='task'?p.tasks.includes(c.id):c.kind==='route'?p.routes.includes(c.id):p.groups.includes(c.group));
          if(!fits)state.context=p.routes.length?{kind:'route',id:p.routes[0]}:null;
        }
        if(!same)state.tab=n.kind==='evidence'?'evidence':'overview';
      }
      if(action.type==='toggle'&&n.kind==='route')state.expandedRoutes.has(n.id)?state.expandedRoutes.delete(n.id):state.expandedRoutes.add(n.id);
      if(action.type==='toggle'&&n.kind==='group')state.expandedGroups.has(n.group)?state.expandedGroups.delete(n.group):state.expandedGroups.add(n.group);
      if(action.type==='toggle'&&n.kind==='challenge'){
        state.expandedChallenges.has(n.canonical)?state.expandedChallenges.delete(n.canonical):state.expandedChallenges.add(n.canonical);
        if(!state.expandedChallenges.has(n.canonical)&&state.selected?.canonical===n.canonical&&['insight','evidence'].includes(state.selected.kind)){state.selected={kind:'challenge',id:n.id,canonical:n.canonical};state.tab='overview';}
      }
      if(action.type==='select'&&n.kind==='paper')state.expandedChallenges.add(n.canonical);
    }
    if(action.type==='clear'){state.selected=null;state.context=null;state.tab='overview';state.selectionNotice='';}
    if(action.type==='zoom')state.zoom=Math.max(.65,Math.min(MAX_ZOOM,Math.round(action.value*100)/100));
    return state;
  }
  function mount(doc,data) {
    if(!data||data.schema!=='radar-c-view/1')throw new Error('Missing graph-data.js');
    let state=initialState(),scene;
    const $=id=>doc.getElementById(id);
    const svg=$('research-graph');
    const kindNames={task:'任务',route:'方法路线',paper:'论文',group:'编辑归组',challenge:'本文问题',insight:'解决思路',evidence:'证据'};
    const reduced=()=>doc.defaultView?.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    const behavior=()=>reduced()?'instant':'auto'; // Reveal content immediately, without motion.
    const element=(tag,attrs={},parent)=>{const el=doc.createElementNS(NS,tag);Object.entries(attrs).forEach(([key,value])=>el.setAttribute(key,String(value)));if(parent)parent.appendChild(el);return el;};
    const putText=(parent,text,x,y,cls)=>{const t=element('text',{x,y,class:cls},parent);t.textContent=text;return t;};
    const icons={task:'M1 15 8 1 15 15 8 11Z',route:'M1 2 6 0 11 3 16 1V15L11 17 6 14 1 16ZM6 0V14M11 3V17',paper:'M2 0H10L15 5V18H2ZM10 0V5H15M5 9H12M5 12H12',group:'M8 0A7 7 0 0 1 12 13V17H4V13A7 7 0 0 1 8 0M5 20H11',challenge:'M8 1A8 8 0 1 1 7.99 1M8 5V10L12 12',insight:'M2 3H15M2 8H15M2 13H15M-2 3H-1M-2 8H-1M-2 13H-1',evidence:'M2 0H10L15 5V18H2ZM10 0V5H15M5 10 7 12 12 7'};
    const section=(title,content,attribution='')=>`<section class="detail-section"><h3>${escape(title)}${attribution?`<span class="attribution">${escape(attribution)}</span>`:''}</h3>${content}</section>`;
    const paragraph=text=>`<p>${escape(text)}</p>`;
    const list=items=>`<ul>${items.map(t=>`<li>${escape(t)}</li>`).join('')}</ul>`;
    const source=p=>`<a class="source-button" href="${escape(p.source_url)}" target="_blank" rel="noopener noreferrer">阅读固定版本原文 ↗</a>`;
    const paperButtons=papers=>papers.map(p=>`<button class="paper-button" type="button" data-paper-id="${escape(p.canonical_id)}">${escape(p.short_name)}<span>${escape(p.mode==='weekly'?p.versioned_id+' · 摘要候选':p.version+' · '+readingScope(p))}</span></button>`).join('');
    function renderDetails(){
      const sel=state.selected,p=sel?.canonical?scene.papers.find(p=>p.canonical_id===sel.canonical):null;
      $('detail-tabs').hidden=!p;
      $('detail-title').textContent=sel?'选中'+kindNames[sel.kind]:'研究总览';
      const picked=scene.nodes.find(n=>n.id===sel?.id)||scene.nodes.find(n=>n.canonical===sel?.canonical&&n.kind===sel?.kind);
      const memberships=p?data.routes.filter(r=>p.routes.includes(r.id)).map(r=>r.label):[];
      $('current-path').textContent=sel?'当前：'+(p?p.short_name+' · '+kindNames[sel.kind]+'；所属路线：'+memberships.join(' / '):(picked?.label||kindNames[sel.kind])):'当前：总览 → 选择一个方向 → 选择论文 → 核对证据';
      const context=state.context;
      const contextNode=context&&scene.nodes.find(n=>n.id===context.id);
      $('back-to-direction').hidden=!p||!contextNode;
      $('back-to-direction').textContent=contextNode?'← 返回'+contextNode.label:'← 返回方向';
      $('show-details').disabled=!sel;
      $('locate-selection').disabled=!sel;
      if(!p){
        let title='探索这张地图',subtitle='导航领域首个试点',content='';
        if(sel?.kind==='route'){const r=data.routes.find(r=>r.id===sel.id);title=r.label;subtitle='现有方法路线 · 编辑组织';content=section('路线范围',paragraph(r.full_label))+section('当前范围内的论文',paperButtons(scene.papers.filter(p=>p.routes.includes(sel.id))));}
        else if(sel?.kind==='task'){const t=data.tasks.find(t=>t.id===sel.id);title=t.label;subtitle=t.full_label;content=section('任务下的论文',paperButtons(scene.papers.filter(p=>p.tasks.includes(sel.id))));}
        else if(sel?.kind==='group'){const g=data.groups.find(g=>g.id===sel.group);title=g.label;subtitle='编辑归组 · 非学术关系';content=section('分组说明',paragraph(g.note))+section('同组论文分别核证',paperButtons(scene.papers.filter(p=>p.groups.includes(g.id))));}
        else {
          title='从一个方向开始';subtitle='总览 → 方向 → 论文 → 证据';
          content=section('选择研究方向',data.routes.map(r=>`<button class="paper-button direction-button" type="button" data-direction-id="${escape(r.id)}">${escape(r.label)}<span>${scene.papers.filter(p=>p.routes.includes(r.id)).length} 篇匹配论文 · 查看方向与完整列表</span></button>`).join(''));
          content+=section('折叠只是收起显示',paragraph(`本范围共收录 ${coverageCounts(data,state,scene).total} 篇独立论文；默认每个方向先展示代表项。使用“显示全部匹配论文”可展开当前筛选结果。隐藏项仍收录，方向数和路线关联数都不是论文数。`));
        }
        if(state.selectionNotice)content=section('选择已随筛选更新',paragraph(state.selectionNotice))+content;
        $('selection-summary').innerHTML=`<div class="selection-card"><span class="selection-type">${escape(subtitle)}</span><h3>${escape(title)}</h3><p>图中连接只表示编辑组织；每篇论文只显示一个节点，多条路线可连入</p></div>`;
        $('detail-content').innerHTML=content+section('证据边界',paragraph('关联图不新增引用、采用、比较或因果关系。未建分支只是当前组织覆盖缺口，不能据此认定研究空白。'));
      } else {
        const weekly=p.mode==='weekly';
        $('selection-summary').innerHTML=`<div class="selection-card"><span class="selection-type"><span>${weekly?'本期摘要候选':'领域基线 · '+escape(readingScope(p))}</span><span>${weekly?escape(data.weekly.date)+' 周窗':'同篇关联'}</span></span><h3>${escape(p.short_name)}</h3><p>${escape(weekly?p.versioned_id:p.version)}</p><p class="projection-note">所属路线（${p.routes.length}）：${escape(memberships.join(" / "))}；图中仅一个论文节点</p><div class="id-label">统一论文 ID：${escape(p.canonical_id)}</div></div>`;
        let content='';
        if(state.tab==='overview'){
          content=p.abstract_summary_zh?section('摘要中文概述',paragraph(p.abstract_summary_zh),'编辑归纳'):(p.overview_zh?section(p.overview_label_zh||'研究概述',paragraph(p.overview_zh)+paragraph(p.overview_scope_note_zh||''),'编辑归纳'): '');
          content+=section('本文问题',paragraph(weekly?p.problem:p.challenge),weekly?'编辑问题归纳':'编辑归纳');
          content+=section(weekly?'作者方案':'解决思路',paragraph(weekly?p.author_solution:p.insight),weekly?'作者主张 · 摘要':attrNames[p.insight_attribution]||'编辑归纳');
          if(!weekly)content+=section('方法路径',paragraph(p.pipeline));
          content+=section('证据状态',`<span class="status-badge ${weekly?'warning':''}">${weekly?'候选位置 · 仅完整摘要':escape(readingScope(p))+' · 非全文阅读'}</span>`+paragraph(weekly?'本轮未读全文、未比较版本、未独立复现实验；位置贴合度不是学术关系。':(p.read_scope==='section'?data.core_definition:'本条仅支持上述证据范围，不提升为正文阅读')+'；未独立复现实验。'));
          if(p.harness_relation){
            const relation=p.harness_relation,labels={direct_harness:'直接 Harness / 运行框架',supporting_method:'可支撑 Harness 的方法',benchmark_protocol:'评测基准 / 协议',unclassified_candidate:'待分类候选'};
            content+=section('与 Harness 的关系',paragraph(labels[relation.kind]||'关系待核')+paragraph(relation.basis||''),'编辑组织');
          }
          content+=source(p);
        } else if(state.tab==='evidence'){
          if(weekly){content=section('已核来源',paragraph(p.title)+`<span class="locator">${escape(p.locator)} · 核查 ${escape(p.fresh_checked_at)}</span>`+paragraph('primary_complete_abstract · 原始事件 '+p.event_at));
            content+=section('位置候选',p.placements.map(m=>{const n=[...data.tasks,...data.routes].find(n=>n.id===m.node_id);return `<div class="placement"><b>${escape(n?.label||m.node_id)}</b><span class="fit-label">${m.fit==='partial'?'部分贴合':'直接贴合'} · 编辑组织</span><p>${escape(m.why)}</p></div>`;}).join(''));
            content+=section('证据没有覆盖',list(['全文未读','修订前后未比较','实验未独立核验','未新增学术关系']));
          } else {
            content=section('指定原文证据',p.evidence.map(e=>`<div class="evidence-card"><span class="attribution">${escape(attrNames[e.attribution]||e.attribution)}</span><p>${escape(e.statement)}</p><a class="locator" href="${escape(p.source_url)}" target="_blank" rel="noopener noreferrer">${escape(e.locator)} ↗</a></div>`).join(''));
            content+=section('实际阅读范围',list(p.read_locations));
            content+=section('未读与未验证',list(p.not_read));
          }
          content+=source(p);
        } else {
          if(weekly){content=section('比较与适用边界',list(p.comparison_limits));content+=section('下一步核查',list(p.next_checks),'尚未执行');
            if(p.branch_proposals.length)content+=section('待建分支候选',p.branch_proposals.map(b=>`<div class="evidence-card"><p><b>${escape(b.label)}</b></p><p>${escape(b.why)}</p><span class="locator">未创建 · 组织覆盖缺口，非研究空白</span></div>`).join(''));
          } else {content=section('任务与条件',paragraph(p.task)+list(p.conditions));content+=section('适用与比较边界',paragraph(p.limits));content+=section('待核问题',paragraph(p.open_question),'编辑提出 · 非新颖性结论');}
          content+=paragraph('图中跨树连接的是同一论文的两种阅读入口；不意味着另一篇论文已解决了这里的问题。')+source(p);
        }
        $('detail-content').innerHTML=content;
      }
      doc.querySelectorAll('[data-tab]').forEach(b=>{const chosen=b.dataset.tab===state.tab;b.setAttribute('aria-selected',String(chosen));b.setAttribute('tabindex',chosen?'0':'-1');});
      $('detail-content').setAttribute('aria-labelledby','tab-'+state.tab);
    }
    function renderGraph(){
      scene=buildScene(data,state);
      while(svg.lastChild)svg.removeChild(svg.lastChild);
      const title=element('title',{id:'graph-title'},svg);title.textContent='导航领域首个试点：文献脉络与 Challenge–Insight 双树';
      const desc=element('desc',{id:'graph-desc'},svg);desc.textContent='所有连线均为编辑组织。跨树线仅连同一论文，不是引用、采用或因果关系。点击卡片查看详情；使用独立的展开或收起按钮逐层展开。';
      const defs=element('defs',{},svg), filter=element('filter',{id:'selected-shadow',x:'-15%',y:'-30%',width:'140%',height:'170%'},defs);element('feDropShadow',{dx:0,dy:2,stdDeviation:3,'flood-color':'#bd442a','flood-opacity':'.11'},filter);
      svg.setAttribute('viewBox',`0 0 ${WIDTH} ${scene.height}`);
      element('line',{x1:676,y1:14,x2:676,y2:scene.height-12,class:'graph-split'},svg);
      putText(svg,'任务',27,23,'graph-group-label');putText(svg,'方法路线',224,23,'graph-group-label');putText(svg,'论文 · 去重显示',449,23,'graph-group-label');putText(svg,'编辑归组',725,23,'graph-group-label');putText(svg,'本文问题 / 思路 / 证据',977,23,'graph-group-label');
      const edgeLayer=element('g',{'aria-hidden':'true'},svg), nodeLayer=element('g',{},svg);
      const byId=Object.fromEntries(scene.nodes.map(n=>[n.id,n]));
      scene.edges.sort((a,b)=>Number(a.active)-Number(b.active)).forEach(e=>{
        const s=byId[e.source],t=byId[e.target];if(!s||!t)return;
        let d;
        if(e.vertical){const x=t.x+13;d=`M ${s.x+13} ${s.y+s.h} C ${s.x+13} ${s.y+s.h+13}, ${x} ${t.y-13}, ${x} ${t.y}`;}
        else {const x=s.x+s.w,y=s.y+s.h/2,tx=t.x,ty=t.y+t.h/2;const mid=e.cross?x+(tx-x)*.56:(x+tx)/2;d=`M ${x} ${y} C ${mid} ${y}, ${mid} ${ty}, ${tx} ${ty}`;}
        element('path',{d,class:['graph-edge',e.active?'active':'',e.dim?'dim':'',e.cross?'cross':'',e.partial?'partial':'',e.candidate?'candidate':''].join(' '),'data-source':e.source,'data-target':e.target,'data-edge-semantics':'curator_organization',...(e.same_paper?{'data-same-paper':e.same_paper}:{})},edgeLayer);
      });
      scene.nodes.forEach(n=>{
        const classes=['graph-node',n.kind,n.active?'active':'',n.dim?'dim':'',n.selected?'selected':'',n.candidate?'candidate':''].join(' ');
        const label=n.label+(n.subtitle?'，'+n.subtitle:'')+'，查看'+kindNames[n.kind]+'详情'+(n.routeCount>1?'，所属 '+n.routeCount+' 条路线':'');
        const g=element('g',{id:'node-'+safeId(n.id),class:classes,transform:`translate(${n.x} ${n.y})`,role:'button',tabindex:0,'aria-label':label,'aria-pressed':String(n.selected),'data-node-id':n.id,'data-kind':n.kind,...(n.canonical?{'data-canonical-id':n.canonical}:{})},nodeLayer);
        const tt=element('title',{},g);tt.textContent=(n.full||n.label)+(n.partial?' · 此位置仅部分贴合':'');
        element('rect',{x:0,y:0,width:n.w,height:n.h,rx:n.kind==='task'?14:8,class:'node-body'},g);
        element('path',{d:icons[n.kind]||icons.paper,transform:`translate(13 ${n.kind==='challenge'||n.kind==='insight'?31:24})`,class:'node-icon'},g);
        const long=n.kind==='challenge'||n.kind==='insight';
        if(long)putText(g,n.kind==='challenge'?'本文问题':'解决思路',40,17,'node-kicker');
        const max=(n.w-55)/14;
        const lines=wrapText(n.label,max,long?3:2);
        const start=long?36:(lines.length>1?26:29);
        lines.forEach((text,i)=>putText(g,text,40,start+i*17,'node-label'));
        if(n.subtitle)putText(g,wrapText(n.subtitle,(n.w-55)/11,1)[0],40,['route','group'].includes(n.kind)?62:n.h-10,'node-subtitle');
        if(n.kind==='paper'&&n.routeCount>1)putText(g,n.routeCount+' 条所属路线',40,13,'projection-badge');
        putText(g,'查看',n.w-29,13,'node-action-hint');
        if(n.total!==undefined)putText(g,`显示 ${n.visible} / ${n.total} 篇`,12,n.h-13,'node-count');
        if(n.partial)element('circle',{cx:n.w-10,cy:n.h-11,r:3,fill:'#b78654'},g);
        const choose=()=>{applyAction(state,{type:'select',node:n});render();const fresh=$('node-'+safeId(n.id));fresh?.focus?.({preventScroll:true});};
        g.addEventListener('click',choose);g.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();choose();}});
        if(n.canExpand){
          const toggle=element('g',{id:'expand-'+safeId(n.id),class:'node-expand',role:'button',tabindex:0,'aria-label':(n.expanded?'收起':'展开')+n.label+(n.total!==undefined?'，当前显示 '+n.visible+' / '+n.total+' 篇':''),'aria-expanded':String(Boolean(n.expanded)),transform:`translate(${n.x+n.w-68} ${n.y+(['route','group'].includes(n.kind)?n.h-30:2)})`},nodeLayer);
          element('rect',{width:65,height:26,rx:4},toggle);putText(toggle,n.expanded?'− 收起':'+ 展开',7,18,'expand-label');
          const expand=()=>{applyAction(state,{type:'toggle',node:n});render();$('expand-'+safeId(n.id))?.focus?.({preventScroll:true});};
          toggle.addEventListener('click',expand);toggle.addEventListener('keydown',event=>{if(event.key==='Enter'||event.key===' '){event.preventDefault();expand();}});
        }
      });
      $('graph-empty').hidden=!scene.empty;
      const counts=coverageCounts(data,state,scene);
      $('visible-count').textContent=`左树 ${scene.uniqueVisible} 篇独立论文 · 全图涉及 ${scene.allTreeUniqueVisible} 篇 · ${scene.methodRoutes} 条有匹配论文的方法路线（主干 ${scene.structuralRoutes}） · ${scene.routeLinks} 次论文与路线归属`;
      $('count-total').textContent=counts.total+' 篇';$('count-matched').textContent=counts.matched+' 篇';$('count-visible').textContent=counts.visible+' 篇';
      $('coverage-note').textContent=(counts.collapsed?`${counts.collapsed} 篇匹配论文在左树因折叠暂未显示论文节点，仍在本范围收录。`:'当前匹配论文均已显示左树论文节点。')+(counts.excluded?`另有 ${counts.excluded} 篇被筛选排除。`:'未使用筛选排除论文。')+` 全图当前涉及 ${counts.acrossTrees} 篇（含右树问题卡），与左树论文节点数分别统计；均按论文 ID 去重。`;
      $('show-all-papers').textContent=`显示全部匹配论文（${counts.matched}）`;
      $('show-all-papers').disabled=counts.matched===0||counts.collapsed===0;
      $('clear-filters-toolbar').disabled=state.task==='all'&&!state.search;
      $('filter-summary').textContent=state.task==='all'&&!state.search?'筛选：全部任务 · 无关键词':`筛选：${data.tasks.find(t=>t.id===state.task)?.label||'全部任务'}${state.search?' · “'+state.search+'”':''}`;

      applyZoom();
    }
    function applyZoom(){svg.style.minWidth='0';svg.style.width=state.zoom*100+'%';$('zoom-level').textContent=Math.round(state.zoom*100)+'%';$('zoom-out').disabled=state.zoom<=.65;$('zoom-in').disabled=state.zoom>=MAX_ZOOM;}
    function fitZoom(){const viewport=$('graph-viewport');state.zoom=Math.max(computeFitZoom(viewport.clientWidth,viewport.clientHeight,WIDTH,scene.height),viewport.clientWidth?WIDTH*.95/viewport.clientWidth:1);applyZoom();viewport.scrollLeft=0;viewport.scrollTop=0;}
    function locateSelection(){
      const viewport=$('graph-viewport'),sel=state.selected;if(!sel||!viewport.clientWidth)return;
      const related=scene.nodes.filter(n=>n.canonical===sel.canonical&&['challenge','insight','evidence'].includes(n.kind));
      const chosen=scene.nodes.find(n=>n.id===sel.id)||scene.nodes.find(n=>n.selected);
      const targets=sel.canonical&&related.length?related:(chosen?[chosen]:[]);if(!targets.length)return;
      const stackHeight=Math.max(...targets.map(n=>n.y+n.h))-Math.min(...targets.map(n=>n.y));
      let scale=viewport.clientWidth*state.zoom/WIDTH;
      if(stackHeight*scale>viewport.clientHeight-40&&scale>.95){scale=Math.max(.95,(viewport.clientHeight-40)/stackHeight);state.zoom=scale*WIDTH/viewport.clientWidth;applyZoom();}
      const top=Math.min(...targets.map(n=>n.y))*scale,bottom=Math.max(...targets.map(n=>n.y+n.h))*scale;
      const left=Math.min(...targets.map(n=>n.x))*scale,right=Math.max(...targets.map(n=>n.x+n.w))*scale;
      const scrollTop=Math.max(0,top-20),scrollLeft=Math.max(0,right-viewport.clientWidth+20);
      if(top<viewport.scrollTop+16||bottom>viewport.scrollTop+viewport.clientHeight-16||left<viewport.scrollLeft||right>viewport.scrollLeft+viewport.clientWidth){
        if(viewport.scrollTo)viewport.scrollTo({top:scrollTop,left:scrollLeft,behavior:behavior()});else{viewport.scrollTop=scrollTop;viewport.scrollLeft=scrollLeft;}
      }
    }
    function render(){
      reconcileSelection(data,state);
      renderGraph();renderDetails();
      doc.querySelectorAll('[data-mode]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.mode===state.mode)));
      $('scope-label').innerHTML='<i class="status-dot"></i>'+escape(state.mode==='weekly'?`${data.weekly.date} 周窗 · ${data.candidates.length} 篇摘要位置候选`:`导航领域试点 · ${data.papers.length} 篇图谱记录 · 证据范围逐篇说明`);
      $('baseline-count').textContent=data.papers.length;$('weekly-count').textContent=data.candidates.length;
      $('period-counts').textContent=`日报快照 ${data.daily.date}：${data.daily.candidate_count} 条候选 · 周窗快照 ${data.weekly.date}：${data.weekly.candidate_count} 条候选 / ${data.weekly.abstract_count} 条摘要 / ${data.candidates.length} 篇定位 / ${data.weekly.unmapped_abstracts.length} 篇未定位`;

      $('graph-search').value=state.search;$('task-filter').value=state.task;$('focus-path').checked=state.focus;
    }
    data.tasks.forEach(t=>{const option=doc.createElement('option');option.value=t.id;option.textContent=t.label+' · '+t.subtitle;$('task-filter').appendChild(option);});
    doc.querySelectorAll('[data-mode]').forEach(b=>b.addEventListener('click',()=>{if(state.mode===b.dataset.mode)return;applyAction(state,{type:'mode',mode:b.dataset.mode});render();fitZoom();}));
    doc.querySelectorAll('[data-tab]').forEach(b=>{b.addEventListener('click',()=>{state.tab=b.dataset.tab;renderDetails();});b.addEventListener('keydown',event=>{if(!['ArrowRight','ArrowLeft','Home','End'].includes(event.key))return;event.preventDefault();const tabs=['overview','evidence','conditions'];let ix=tabs.indexOf(state.tab);ix=event.key==='Home'?0:event.key==='End'?2:(ix+(event.key==='ArrowRight'?1:2))%3;state.tab=tabs[ix];renderDetails();$('tab-'+state.tab).focus();});});
    $('graph-search').addEventListener('input',()=>{state.search=$('graph-search').value;render();});
    $('graph-search').addEventListener('keydown',event=>{if(event.key==='Escape'){state.search='';render();}});
    $('task-filter').addEventListener('change',()=>{state.task=$('task-filter').value;render();});
    $('focus-path').addEventListener('change',()=>{state.focus=$('focus-path').checked;render();});
    $('clear-selection').addEventListener('click',()=>{applyAction(state,{type:'clear'});render();});
    const clearFilters=()=>{applyAction(state,{type:'clearFilters'});render();};
    $('clear-filters').addEventListener('click',clearFilters);
    $('clear-filters-toolbar').addEventListener('click',clearFilters);
    $('show-all-papers').addEventListener('click',()=>{applyAction(state,{type:'showAll',data});render();});
    $('collapse-papers').addEventListener('click',()=>{applyAction(state,{type:'collapse'});render();});
    $('back-to-direction').addEventListener('click',()=>{applyAction(state,{type:'backDirection'});render();$('node-'+safeId(state.selected?.id))?.focus?.({preventScroll:true});});
    $('show-details').addEventListener('click',()=>{$('detail-panel').scrollIntoView?.({behavior:behavior(),block:'start'});$('detail-content').focus?.({preventScroll:true});});
    const overview=()=>{applyAction(state,{type:'overview'});render();fitZoom();};
    $('return-overview').addEventListener('click',overview);
    $('zoom-in').addEventListener('click',()=>{applyAction(state,{type:'zoom',value:state.zoom+.15});applyZoom();});
    $('zoom-out').addEventListener('click',()=>{applyAction(state,{type:'zoom',value:state.zoom-.15});applyZoom();});
    $('zoom-fit').addEventListener('click',fitZoom);
    $('locate-selection').addEventListener('click',locateSelection);
    $('graph-reset').addEventListener('click',overview);
    $('graph-viewport').addEventListener('keydown',event=>{if(event.key==='Escape'){event.preventDefault();const id=event.target.getAttribute?.('id');applyAction(state,{type:'clear'});render();(id&&$(id)||$('graph-viewport')).focus?.({preventScroll:true});}});
    $('detail-content').addEventListener('click',event=>{
      const direction=event.target.closest?.('[data-direction-id]');
      if(direction){const n=scene.nodes.find(n=>n.id===direction.dataset.directionId);if(n){applyAction(state,{type:'select',node:n});render();$('detail-content').focus?.({preventScroll:true});}return;}
      const button=event.target.closest?.('[data-paper-id]');if(!button)return;const p=activePapers(data,state).find(p=>p.canonical_id===button.dataset.paperId);if(p){applyAction(state,{type:'select',node:{id:'paper-'+p.canonical_id,kind:'paper',canonical:p.canonical_id,paper:p}});render();$('detail-content').focus?.({preventScroll:true});}});
    $('scope-details').addEventListener('click',()=>{$('scope-notes').open=true;$('scope-notes').scrollIntoView?.({behavior:behavior(),block:'start'});});
    $('scope-note-content').innerHTML=paragraph(`导航领域试点：当前图谱基线 ${data.papers.length} 篇，周窗定位 ${data.candidates.length} 篇。页首总收录仅指当前切换范围的图谱论文，不是正式 Library 总量。合并基线与本期，按论文 ID 去重共 ${new Set([...data.papers,...data.candidates].map(p=>p.canonical_id)).size} 篇；同篇可在两种范围保留各自证据版本，两个数量不能直接相加。逐篇证据范围在详情中说明；收录不等于全文阅读。`)+paragraph(`日报快照 ${data.daily.date}：${data.daily.candidate_count} 条候选。周窗快照 ${data.weekly.date}：${data.weekly.candidate_count} 条候选 / ${data.weekly.abstract_count} 条摘要证据，其中 ${data.candidates.length} 篇定位，${data.weekly.unmapped_abstracts.length} 篇摘要未定位。`)+paragraph(`周窗（UTC，updated_at）：${data.weekly.window.start} 至 ${data.weekly.window.end}。`)+list(data.limitations)+`<h3>本轮未定位的 ${data.weekly.unmapped_abstracts.length} 篇摘要</h3><ul>${data.weekly.unmapped_abstracts.map(p=>`<li><a href="https://arxiv.org/abs/${escape(p.versioned_id)}" target="_blank" rel="noopener noreferrer">${escape(p.versioned_id)}</a>：${escape(p.reason)}</li>`).join('')}</ul>`+paragraph('未定位不是不相关或已排除；待建分支不自动加入图中，也不是研究空白。')+`<p><a href="${escape(data.method_reference.url)}" target="_blank" rel="noopener noreferrer">${escape(data.method_reference.label)}</a>：${escape(data.method_reference.note)}</p>`;
    $('method-reference').href=data.method_reference.url;
    render();fitZoom();
    $('load-error').hidden=true;
    return {getState:()=>state,getScene:()=>scene,render,selectPaper:canonical=>{const p=activePapers(data,state).find(p=>p.canonical_id===canonical);if(p){applyAction(state,{type:'select',node:{id:'paper-'+canonical,kind:'paper',canonical,paper:p}});render();}}};
  }
  return {initialState,readingScope,activePapers,filteredPapers,coverageCounts,reconcileSelection,buildScene,applyAction,computeFitZoom,wrapText,mount};
});
