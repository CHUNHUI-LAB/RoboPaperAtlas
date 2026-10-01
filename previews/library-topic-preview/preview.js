'use strict';
/* The search model is independent of the shared public catalog and Atlas. */
const normalize = value => String(value ?? '').normalize('NFKC').toLowerCase().replace(/π/g,'pi').replace(/[^\p{L}\p{N}]+/gu,' ').trim().replace(/\s+/g,' ');
const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const METHOD_ALIASES = {'reinforcement learning':'rl','强化学习':'rl','whole body control':'wbc','全身控制':'wbc','model predictive control':'mpc','模型预测控制':'mpc','模仿学习':'imitation learning','扩散':'diffusion','动作分词方法':'action tokenization','流匹配':'flow matching'};
const PLATFORM_LABELS = {legged:'足式',quadruped:'四足',humanoid:'人形',wheeled:'轮式',mobile_manipulator:'移动机械臂',single_arm:'单臂',dual_arm:'双臂',fixed_base:'固定基座',dexterous_hand:'灵巧手',simulated_character:'仿真角色'};
const RESOURCE_LABELS = {benchmark:'评测基准',dataset:'数据集','data-collection':'数据采集接口','data-generator':'数据生成工具',simulator:'仿真器',software:'软件工具','deployment-software':'部署软件',tokenizer:'动作分词器'};
const TASK_LABELS = {'stylized-motion':'风格化运动',navigation:'导航','mobile-manipulation':'移动操作',manipulation:'操作','motion-control':'运动控制'};
const TASK_QUERIES = {'导航':'navigation','navigation':'navigation','移动操作':'mobile-manipulation','mobile manipulation':'mobile-manipulation','操作':'manipulation','manipulation':'manipulation','运动控制':'motion-control','motion control':'motion-control'};
const PROBLEM_QUERIES = {'动作分词':'action-representation','动作表示':'action-representation','action tokenization':'action-representation','action representation':'action-representation','场景表示':'scene-representation','scene representation':'scene-representation'};
const METHOD_LABELS = {rl:'强化学习 · RL',wbc:'全身控制 · WBC',mpc:'模型预测控制 · MPC','imitation learning':'模仿学习 · Imitation Learning',diffusion:'扩散 · Diffusion','flow matching':'流匹配 · Flow Matching','action tokenization':'动作分词 · Action Tokenization'};
const RELATION_LABELS = {research_object:'直接研究',downstream_execution_evaluation:'执行评测',qualitative_demonstration:'定性演示',data_or_component_testing:'数据／组件测试',training_data_context:'训练数据',adopted_component:'采用既有组件',resource_support:'资源支持',downstream_application:'下游应用'};
const DOMAIN_LABELS = {real_robot:'真实机器人',simulation:'仿真',robot_simulation:'机器人仿真',simulated_character:'仿真角色',physics_simulated_character:'物理仿真角色',physics_simulation_infrastructure:'物理仿真基础设施',gridworld_simulation:'网格环境仿真',simulated_embodied_navigation:'具身导航仿真'};
const canonicalMethod = value => METHOD_ALIASES[normalize(value)] || normalize(value);
const canonicalPlatform = value => Object.keys(PLATFORM_LABELS).find(key=>normalize(key)===normalize(value)||PLATFORM_LABELS[key]===normalize(value)) || normalize(value);
const canonicalResource = value => Object.keys(RESOURCE_LABELS).find(key=>normalize(key)===normalize(value)||RESOURCE_LABELS[key]===normalize(value)) || normalize(value);
const unique = values => [...new Set(values)];
function defaultState(){return {q:'',methods:[],platforms:[],resources:[],paper:''};}
function normalizeState(state={}) {return {q:String(state.q||''),methods:unique((state.methods||[]).map(canonicalMethod)),platforms:unique((state.platforms||[]).map(canonicalPlatform)),resources:unique((state.resources||[]).map(canonicalResource)),paper:String(state.paper||'')};}
function stateFromSearch(search){const p=new URLSearchParams(search);return normalizeState({q:p.get('q')||'',methods:p.getAll('method'),platforms:p.getAll('platform'),resources:p.getAll('resource'),paper:p.get('paper')||''});}
function stateToSearch(state){const s=normalizeState(state),p=new URLSearchParams();if(s.q)p.set('q',s.q);for(const [key,name] of [['methods','method'],['platforms','platform'],['resources','resource']])for(const value of [...s[key]].sort())p.append(name,value);if(s.paper)p.set('paper',s.paper);return p.toString()?'?'+p.toString():'';}
function toggleFilter(state,dimension,value){const s=normalizeState(state);if(!['methods','platforms','resources'].includes(dimension))return s;const v=dimension==='methods'?canonicalMethod(value):dimension==='platforms'?canonicalPlatform(value):canonicalResource(value);s[dimension]=s[dimension].includes(v)?s[dimension].filter(x=>x!==v):[...s[dimension],v];s.paper='';return s;}
function buildOptions(data){
 const counts=(getter,canonical,labels={})=>{const map=new Map();for(const r of data.records)for(const raw of unique(getter(r).map(canonical))){const current=map.get(raw)||{value:raw,label:labels[raw]||getter(r).find(x=>canonical(x)===raw)||raw,count:0};current.count++;map.set(raw,current);}return [...map.values()].sort((a,b)=>b.count-a.count||a.label.localeCompare(b.label));};
 return {methods:counts(r=>r.methods.map(m=>m.label),canonicalMethod,METHOD_LABELS),platforms:counts(r=>r.platforms.flatMap(p=>p.filter_keys),canonicalPlatform,PLATFORM_LABELS),resources:counts(r=>r.resources.map(x=>x.kind),canonicalResource,RESOURCE_LABELS)};
}
function interpretQuery(data,value){
 const q=normalize(value),methods=new Set(data.records.flatMap(r=>r.methods.map(m=>canonicalMethod(m.label))));
 if(TASK_QUERIES[q])return {kind:'task',value:TASK_QUERIES[q],label:TASK_LABELS[TASK_QUERIES[q]]};
 if(PROBLEM_QUERIES[q])return {kind:'problem',value:PROBLEM_QUERIES[q],label:value.trim()};
 if(q&&(METHOD_ALIASES[q]||methods.has(canonicalMethod(q))))return {kind:'method',value:canonicalMethod(q),label:METHOD_LABELS[canonicalMethod(q)]||value.trim()};
 const platform=canonicalPlatform(q);if(q&&Object.hasOwn(PLATFORM_LABELS,platform))return {kind:'platform',value:platform,label:PLATFORM_LABELS[platform]};
 const resource=canonicalResource(q);if(q&&Object.hasOwn(RESOURCE_LABELS,resource))return {kind:'resource',value:resource,label:RESOURCE_LABELS[resource]};
 return {kind:q?'text':'all',value:q,label:value.trim()};
}
function matchesFacet(have,want){return !want.length||want.some(x=>have.includes(x));}
function textFields(record){return [record.title,record.authors,record.short_name,...record.aliases,record.study_question,...record.problem_claims.map(x=>x.label),...record.methods.map(x=>x.label)];}
function taskReason(record,query,relations){
 // Wording only: every special explanation projects the record's cited claims.
 const key=record.id+':'+query.value;
 const exact={
  'rpa-0041:navigation':'研究语言导航，也单独测试视觉行走。',
  'anderson2018r2r:navigation':'定义视觉语言导航任务，提供 R2R 基准并评测初始代理。',
  'rpa-0027:navigation':'研究场景表示，用于导航，并报告导航环节成功率。',
  'rpa-0027:mobile-manipulation':'为移动操作提供场景表示，并做任务验证。',
  'rpa-0062:mobile-manipulation':'从示教学习操作策略，用全身控制在移动身体上执行。',
  'rpa-0052:mobile-manipulation':'让行走与操作策略协作，完成移动操作任务。',
  'rpa-0042:mobile-manipulation':'研究开放环境中的长时探索与移动操作。',
  'rpa-0016:mobile-manipulation':'用 UMI on Legs 数据测试动作分词；未据此验证移动操作执行。',
  'rpa-0016:navigation':'用导航数据测试动作分词；未据此验证导航策略执行。',
  'rpa-0016:manipulation':'动作分词方法，做过单臂／双臂操作策略评测。',
  'holoagent-0:mobile-manipulation':'研究导航与操作的技能编排；联合任务是实机定性演示，采用已有操作后端。'
 };
 let reason=exact[key]||relations[0]?.rationale||record.study_question;
 if(query.value==='manipulation'&&!relations.some(t=>t.task==='manipulation')&&relations.some(t=>t.task==='mobile-manipulation'))reason='移动操作属于操作任务：'+reason.replace(/[。.]$/,'')+'；不据此推断固定基座操作验证。';
 return reason;
}
function queryRecords(data,state={}){
 const s=normalizeState(state),query=interpretQuery(data,s.q),filters={methods:[...s.methods],platforms:[...s.platforms],resources:[...s.resources]};
 if(query.kind==='method')filters.methods.push(query.value);if(query.kind==='platform')filters.platforms.push(query.value);if(query.kind==='resource')filters.resources.push(query.value);
 const main=[],weak=[],uncertain=[],mainTypes=data.contract.main_task_relations;
 for(const record of data.records){
  if(!matchesFacet(record.methods.map(m=>canonicalMethod(m.label)),filters.methods)||!matchesFacet(record.platforms.flatMap(p=>p.filter_keys).map(canonicalPlatform),filters.platforms)||!matchesFacet(record.resources.map(r=>canonicalResource(r.kind)),filters.resources))continue;
  let relations=[],group='main',reason=record.study_question,evidence_ids=[...record.study_question_evidence_ids];
  if(query.kind==='task'){
   const tasks=[query.value,...(data.contract.hierarchy[query.value]||[])];relations=record.task_relations.filter(t=>tasks.includes(t.task));
   if(!relations.length){if(!record.unresolved_tasks.some(t=>tasks.includes(t)))continue;group='uncertain';reason='与'+query.label+'的关系尚待确认；可先查看论文研究问题与已有来源。';evidence_ids=[];}
   else {const mainRelations=relations.filter(t=>mainTypes.includes(t.relation));group=mainRelations.length?'main':'weak';const relevant=mainRelations.length?mainRelations:relations;reason=taskReason(record,query,relevant);evidence_ids=unique(relevant.flatMap(t=>t.evidence_ids));}
  }else if(query.kind==='problem'){
   const claims=record.problem_claims.filter(p=>p.problem_id===query.value);if(!claims.length)continue;reason=record.study_question;evidence_ids=unique(claims.flatMap(c=>c.evidence_ids));
  }else if(query.kind==='text'){
   const hay=normalize(textFields(record).join(' '));if(!query.value.split(' ').every(w=>hay.includes(w)))continue;
   const identity=normalize([record.title,record.authors,record.short_name,...record.aliases].join(' '));const inIdentity=query.value.split(' ').every(w=>identity.includes(w));reason=(inIdentity?'题名、作者或别名匹配；':'研究问题或方法匹配；')+record.study_question;
  }else if(query.kind==='method'){const matched=record.methods.filter(m=>filters.methods.includes(canonicalMethod(m.label)));reason='方法标注包含 '+matched.map(m=>m.label).join('／')+'；'+record.study_question;evidence_ids=unique(matched.flatMap(m=>m.evidence_ids));}
  else if(query.kind==='platform'){const matched=record.platforms.filter(p=>p.filter_keys.some(k=>filters.platforms.includes(canonicalPlatform(k))));reason='平台证据包含'+unique(matched.flatMap(p=>p.filter_keys).filter(k=>filters.platforms.includes(canonicalPlatform(k)))).map(k=>PLATFORM_LABELS[k]||k).join('／')+'；'+record.study_question;evidence_ids=unique(matched.flatMap(p=>p.evidence_ids));}
  else if(query.kind==='resource'){const matched=record.resources.filter(r=>filters.resources.includes(canonicalResource(r.kind)));reason='提供或研究'+unique(matched.map(r=>RESOURCE_LABELS[r.kind]||r.kind)).join('／')+'；'+record.study_question;evidence_ids=unique(matched.flatMap(r=>r.evidence_ids));}
  else if(filters.methods.length||filters.platforms.length||filters.resources.length){const parts=[];if(filters.methods.length)parts.push('方法：'+record.methods.filter(m=>filters.methods.includes(canonicalMethod(m.label))).map(m=>m.label).join('／'));if(filters.platforms.length)parts.push('平台：'+unique(record.platforms.flatMap(p=>p.filter_keys).filter(p=>filters.platforms.includes(canonicalPlatform(p)))).map(p=>PLATFORM_LABELS[p]||p).join('／'));if(filters.resources.length)parts.push('资源：'+record.resources.filter(r=>filters.resources.includes(canonicalResource(r.kind))).map(r=>RESOURCE_LABELS[r.kind]||r.kind).join('／'));reason=parts.join('；')+'。'+record.study_question;}
  evidence_ids=unique([...evidence_ids,...record.study_question_evidence_ids,...record.methods.filter(m=>filters.methods.includes(canonicalMethod(m.label))).flatMap(m=>m.evidence_ids),...record.platforms.filter(p=>p.filter_keys.some(k=>filters.platforms.includes(canonicalPlatform(k)))).flatMap(p=>p.evidence_ids),...record.resources.filter(r=>filters.resources.includes(canonicalResource(r.kind))).flatMap(r=>r.evidence_ids)]);
  const item={record,reason,evidence_ids,relations,group};({main,weak,uncertain}[group]).push(item);
 }
 return {main,weak,uncertain,query,counts:{main:main.length,weak:weak.length,uncertain:uncertain.length,unique_total:main.length+weak.length+uncertain.length}};
}
function safeSourceURL(value){try{const u=new URL(value);return u.protocol==='https:'&&!u.username&&!u.password?u.href:'';}catch{return '';}}
function authorText(record,compact=false){const authors=record.authors;if(!Array.isArray(authors))return authors||'作者待补充';return compact&&authors.length>3?authors.slice(0,3).join('、')+' 等':authors.join('、');}
function renderCard(item){const r=item.record,esc=escapeHTML;return `<article class="paper" data-paper="${esc(r.id)}"><div class="paper-content"><h3><button class="paper-title" type="button" data-open="${esc(r.id)}">${esc(r.title)}</button></h3><p class="paper-meta"><span class="paper-year" title="目录书目年份；不代表正式出版年已核验">${esc(r.bibliographic_year??'年份待核')}</span><span class="separator" aria-hidden="true">/</span>${esc(authorText(r,true))}</p><p class="rationale"><span class="rationale-label">${item.group==='weak'?'关联线索':item.group==='uncertain'?'待确认':'查找线索'}</span>${esc(item.reason)}</p></div><button class="paper-open" type="button" data-open="${esc(r.id)}" aria-label="查看 ${esc(r.title)} 的检索依据" tabindex="-1">↗</button></article>`;}
function renderDetail(record,item){
 const r=record,esc=escapeHTML,refs=ids=>unique(ids||[]).map(id=>`<a class="evidence-ref" href="#source-${esc(id)}" data-evidence="${esc(id)}" aria-label="查看来源 ${esc(id.slice(1))}">[${esc(id.slice(1))}]</a>`).join(''),list=values=>values.length?'<ul>'+values.map(v=>'<li>'+v+'</li>').join('')+'</ul>':'<p class="detail-empty">尚未建立此项标注，不代表论文没有涉及。</p>',section=(title,content,open=false)=>`<details class="detail-section"${open?' open':''}><summary>${title}</summary>${content}</details>`;
 return `<h2 id="detail-title" tabindex="-1">${esc(r.title)}</h2><p class="detail-meta">${esc(r.bibliographic_year??'年份待核')} · ${esc(authorText(r))}<br>年份沿用目录书目，不等同于已核验的正式出版年</p><p class="detail-reason">${esc(item?.reason||r.study_question)}${refs(item?.evidence_ids||r.study_question_evidence_ids)}</p><p class="detail-scope">以下是已有证据支持的部分标注，不是完整全文阅读记录。空缺表示尚不确定；任务、方法与使用的平台分别记录。</p>`+
 section('研究问题与任务关系',list(r.problem_claims.map(c=>`${esc(c.label)}：${esc(c.rationale)}${refs(c.evidence_ids)}`))+list(r.task_relations.map(t=>`${esc(TASK_LABELS[t.task]||t.task)} · ${esc(RELATION_LABELS[t.relation]||t.relation)}：${esc(t.rationale)}${refs(t.evidence_ids)}`))+(r.unresolved_tasks.length?`<p class="small">尚待确认：${r.unresolved_tasks.map(t=>esc(TASK_LABELS[t]||t)).join('、')}</p>`:'')+'<p class="small">移动操作可被“操作”查询包含，但不形成单独的固定基座操作证据。</p>')+
 section('方法与具体贡献',list(r.methods.map(m=>`${esc(m.label)}${refs(m.evidence_ids)}`))+'<p class="small">方法标签说明采用或讨论的方法家族，不自动表示由本文原创。</p>'+list(r.contributions.map(c=>`${esc(c.description)}${refs(c.evidence_ids)}`)))+
 section('平台与实验范围',list(r.platforms.map(p=>`${esc(p.name||p.configuration||p.morphology||'平台')} · ${p.filter_keys.map(k=>esc(PLATFORM_LABELS[k]||k)).join('／')}${refs(p.evidence_ids)}`))+list(r.execution_domains.map(d=>`${esc(DOMAIN_LABELS[d.domain]||d.domain)}${d.scope_note?'：'+esc(d.scope_note):''}${refs(d.evidence_ids)}`))+list(r.evaluation_contexts.map(c=>`${esc(c.label)}${refs(c.evidence_ids)}`))+'<p class="small">平台标注不自动推出该任务已在实机完成；具体范围以任务证据为准。</p>')+
 section('数据与工具资源',list(r.resources.map(x=>`${esc(RESOURCE_LABELS[x.kind]||x.kind)}${x.name?' · '+esc(x.name):''}${refs(x.evidence_ids)}`))+'<p class="small">资源类型不表示当前可下载或代码可运行，本页未重新核验发布可用性。</p>')+
 `<details id="detail-evidence" class="detail-section"><summary>查看来源与具体位置 <span class="small">${r.evidence.length}</span></summary><p class="small">以下说明为来源要点的概括，不是原文逐字引文。证据粒度可能仅为摘要或部分章节。</p>${r.evidence.map(e=>`<div class="evidence-item" id="source-${esc(e.id)}" tabindex="-1"><p class="source-location">[${esc(e.id.slice(1))}] ${esc(e.locator)}</p><p>${esc(e.finding)}</p>${e.urls.map(url=>{const safe=safeSourceURL(url);return safe?`<a class="source-link" href="${esc(safe)}" target="_blank" rel="noopener noreferrer">${esc(url)} ↗</a>`:'';}).join('<br>')}</div>`).join('')}</details>`;
}
if(typeof module!=='undefined')module.exports={normalize,escapeHTML,canonicalMethod,canonicalPlatform,canonicalResource,defaultState,normalizeState,stateFromSearch,stateToSearch,toggleFilter,buildOptions,interpretQuery,queryRecords,renderCard,renderDetail,safeSourceURL};
if(typeof document!=='undefined'){
 const $=id=>document.getElementById(id),esc=escapeHTML;
 fetch('topics.json').then(response=>{if(!response.ok)throw new Error('data');return response.json();}).then(data=>{
  let state=stateFromSearch(location.search),result,returnFocus='',returnScroll=0,closing=false;
  const options=buildOptions(data),records=new Map(data.records.map(r=>[r.id,r])),dialog=$('paper-dialog');
  const labelFor=(dimension,value)=>options[dimension].find(x=>x.value===value)?.label||value;
  const facetNames={methods:'方法',platforms:'平台',resources:'资源'};
  $('filter-groups').innerHTML=Object.entries(options).map(([dimension,values])=>`<fieldset><legend>${facetNames[dimension]}</legend>${dimension==='methods'?'<label class="sr-only" for="method-search">查找方法筛选项</label><input class="facet-search" id="method-search" type="text" placeholder="查找方法，如 RL、扩散">':''}<div class="facet-options"${dimension==='methods'?' id="method-options"':''}>${values.map(o=>`<label class="facet-option" data-filter-label="${esc(normalize(o.label))}"><input type="checkbox" data-dimension="${dimension}" value="${esc(o.value)}"><span>${esc(o.label)}</span><small aria-label="全库 ${o.count} 篇">${o.count}</small></label>`).join('')}</div></fieldset>`).join('');
  function writeURL(mode='replace'){history[mode+'State']({...history.state,libraryPreview:true,previewDetail:mode==='push'&&!!state.paper},'',location.pathname+stateToSearch(state));}
  function updateControls(){
   $('q').value=state.q;$('clear-query').hidden=!state.q;
   for(const input of $('filter-groups').querySelectorAll('input[type=checkbox]'))input.checked=state[input.dataset.dimension].includes(input.value);
   const total=state.methods.length+state.platforms.length+state.resources.length;$('filter-number').hidden=!total;$('filter-number').textContent=total;
   $('reset').hidden=!state.q&&!total;$('clear-facets').disabled=!total;
   const chips=[];if(state.q)chips.push(`<button type="button" data-remove-query aria-label="移除搜索 ${esc(state.q)}">搜索：${esc(state.q)}<span aria-hidden="true">×</span></button>`);
   for(const dim of ['methods','platforms','resources'])for(const value of state[dim])chips.push(`<button type="button" data-remove-dimension="${dim}" data-remove-value="${esc(value)}" aria-label="移除${facetNames[dim]} ${esc(labelFor(dim,value))}">${facetNames[dim]}：${esc(labelFor(dim,value))}<span aria-hidden="true">×</span></button>`);
   $('selected-filters').innerHTML=chips.join('');$('selected-filters').hidden=!chips.length;
  }
  function render(){
   result=queryRecords(data,state);updateControls();const all=!normalize(state.q)&&!state.methods.length&&!state.platforms.length&&!state.resources.length;
   $('count').innerHTML=`${all?'全部论文':'匹配论文'} <span>${result.counts.main}</span>`;
   $('query-note').textContent=result.query.kind==='task'?`按“${result.query.label}”的直接研究、执行评测和定性演示匹配；数据与工具关联另列。标注仍是部分覆盖。`:result.query.kind==='method'?'按已标注的方法精确匹配；方法标签不表示算法由本文原创。':result.query.kind==='platform'?'按平台证据匹配；未标注不代表未涉及，不推断任务已经实机完成。':result.query.kind==='resource'?'按资源类型匹配；下载、代码和当前发布可用性未重新核验。':'问题、方法和平台标注仍在逐步补充；95 篇均可按标题、作者与别名检索。';
   $('results').innerHTML=result.main.length?result.main.map(renderCard).join(''):'<div class="empty"><h3>没有匹配的论文</h3><p>试试论文名或缩写，也可以移除某个筛选条件。</p><button type="button" data-reset>查看全部 95 篇</button></div>';$('results').setAttribute('aria-busy','false');
   for(const [key,items] of [['weak',result.weak],['uncertain',result.uncertain]]){$(key+'-section').hidden=!items.length;$(key+'-count').textContent=items.length+' 篇';$(key+'-results').innerHTML=items.map(renderCard).join('');}
  }
  function openDetail(id,push=true){
   const record=records.get(id);if(!record)return;
   if(!dialog.open){returnFocus=id;returnScroll=window.scrollY;}
   state.paper=id;if(push)writeURL('push');const item=[...result.main,...result.weak,...result.uncertain].find(x=>x.record.id===id);
   $('detail-content').innerHTML=renderDetail(record,item);$('full-paper').href='../papers/'+encodeURIComponent(id)+'/';
   if(!dialog.open)dialog.showModal();document.body.classList.add('detail-open');dialog.scrollTop=0;$('detail-title').focus({preventScroll:true});
  }
  function finishClose(){closing=false;if(dialog.open)dialog.close();document.body.classList.remove('detail-open');const target=[...$('library').querySelectorAll('[data-open]')].find(el=>el.dataset.open===returnFocus);if(target)target.focus({preventScroll:true});window.scrollTo({top:returnScroll,behavior:'instant'});}
  function requestClose(){if(closing||!dialog.open)return;if(history.state?.previewDetail){closing=true;history.back();}else{state.paper='';writeURL();finishClose();}}
  function change(next,{focusSearch=false}={}){state={...normalizeState(next),paper:''};$('weak-section').open=false;$('uncertain-section').open=false;writeURL();render();if(focusSearch)$('q').focus();}
  function reset(){change(defaultState(),{focusSearch:true});$('filter-panel').hidden=true;$('more-filters').setAttribute('aria-expanded','false');$('method-search').value='';for(const label of $('method-options').children)label.hidden=false;}
  $('q').addEventListener('input',()=>change({...state,q:$('q').value}));$('searchform').addEventListener('submit',event=>{event.preventDefault();$('results').focus();});
  $('clear-query').addEventListener('click',()=>change({...state,q:''},{focusSearch:true}));$('reset').addEventListener('click',reset);
  $('clear-facets').addEventListener('click',()=>change({...state,methods:[],platforms:[],resources:[]}));
  $('more-filters').addEventListener('click',()=>{const open=$('more-filters').getAttribute('aria-expanded')!=='true';$('more-filters').setAttribute('aria-expanded',String(open));$('filter-panel').hidden=!open;});
  $('filter-groups').addEventListener('change',event=>{const input=event.target;if(input.dataset.dimension)change(toggleFilter(state,input.dataset.dimension,input.value));});
  $('method-search').addEventListener('input',()=>{const q=normalize($('method-search').value),method=canonicalMethod(q);for(const label of $('method-options').children){const input=label.querySelector('input');label.hidden=!!q&&!label.dataset.filterLabel.includes(q)&&input.value!==method;}});
  $('selected-filters').addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.hasAttribute('data-remove-query'))change({...state,q:''},{focusSearch:true});else if(b.dataset.removeDimension){const dim=b.dataset.removeDimension;change({...state,[dim]:state[dim].filter(v=>v!==b.dataset.removeValue)});$('more-filters').focus();}});
  $('library').addEventListener('click',event=>{const open=event.target.closest('[data-open]');if(open){openDetail(open.dataset.open);return;}const quick=event.target.closest('[data-query]');if(quick){change({...state,q:quick.dataset.query},{focusSearch:true});return;}if(event.target.closest('[data-reset]'))reset();});
  $('close-detail').addEventListener('click',requestClose);dialog.addEventListener('cancel',event=>{event.preventDefault();requestClose();});
  dialog.addEventListener('click',event=>{const link=event.target.closest('[data-evidence]');if(!link)return;event.preventDefault();$('detail-evidence').open=true;const target=$('source-'+link.dataset.evidence);target.scrollIntoView({block:'start',behavior:'instant'});target.focus({preventScroll:true});});
  document.addEventListener('keydown',event=>{const editing=event.target.isContentEditable||/INPUT|TEXTAREA|SELECT/.test(event.target.tagName);if(!dialog.open&&((event.key==='/'&&!editing)||((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='k'))){event.preventDefault();$('q').focus();$('q').select();}if(event.key==='Escape'&&!dialog.open&&$('more-filters').getAttribute('aria-expanded')==='true'){$('more-filters').setAttribute('aria-expanded','false');$('filter-panel').hidden=true;$('more-filters').focus();}});
  window.addEventListener('popstate',()=>{closing=false;state=stateFromSearch(location.search);render();if(state.paper&&records.has(state.paper))openDetail(state.paper,false);else finishClose();});
  render();if(state.paper&&records.has(state.paper))openDetail(state.paper,false);else if(state.paper){state.paper='';writeURL();}
 }).catch(()=>{$('count').textContent='论文暂时未能载入';$('results').setAttribute('aria-busy','false');$('results').innerHTML='<div class="empty"><p>请刷新后重试，或返回主站继续浏览。</p><a href="../">返回主站 →</a></div>';});
}
