'use strict';
const normalize = s => String(s||'').normalize('NFKC').toLowerCase().replace(/π/g,'pi').replace(/[\s\-_]/g,'');
function filterRecords(records,state){return records.filter(r=>{
 const topic=!state.topic||r.research_topics.includes(state.topic)||(state.related&&r.related_topics.includes(state.topic));
 const hay=normalize([r.title,r.short_name,r.authors,...r.aliases,...r.methods,...r.tags].join(' '));
 const words=String(state.q||'').trim().split(/\s+/).filter(Boolean).map(normalize);
 return topic&&words.every(word=>hay.includes(word))&&(!state.method||r.methods.includes(state.method))&&(!state.morph||r.morphology.includes(state.morph))&&(!state.role||r.artifact_roles.includes(state.role));
});}
const escapeHTML=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
if(typeof module!=='undefined')module.exports={normalize,filterRecords,escapeHTML};
if(typeof document!=='undefined'){
 const $=id=>document.getElementById(id), esc=escapeHTML;
 fetch('topics.json').then(r=>{if(!r.ok)throw Error('data');return r.json()}).then(data=>{
 let topic='';const topicName=id=>data.topics.find(t=>t.id===id)?.label||id;
 $('topics').innerHTML=[{id:'',label:'全部论文',english:'All 95 records'},...data.topics].map(t=>`<button type="button" data-topic="${t.id}" aria-pressed="${!t.id}">${esc(t.label)}<small>${esc(t.english)}</small></button>`).join('');
 const methods=[...new Set(data.records.flatMap(r=>r.methods))].sort();$('method').innerHTML+=[...methods].map(m=>`<option>${esc(m)}</option>`).join('');
 function render(){
 const state={topic,q:$('q').value,method:$('method').value,morph:$('morph').value,role:$('role').value,related:$('includeRelated').checked};const list=filterRecords(data.records,state);
 $('count').textContent=`${list.length} 篇${topic?' · '+topicName(topic):' · 全库检索'}`;
 $('boundary').textContent=topic?data.topics.find(t=>t.id===topic).boundary:'主题选择可跳过。基础算法、平台与尚未做主题整理的论文都保留在默认全库中。';
 $('results').innerHTML=list.length?list.map(r=>{const research=r.research_topics.length,unknown=r.curation==='not_curated';const relatedInTopic=topic&&!r.research_topics.includes(topic);let status=unknown?'尚未做主题整理':relatedInTopic?'相关工作／资源':research?'主题研究样本':'基础资源';
 return `<article class="paper"><div class="state"><strong>${status}</strong>${r.artifact_roles.includes('resource')&&research?'<br>兼有资源贡献':''}</div><div><h3><a href="../papers/${encodeURIComponent(r.id)}/">${esc(r.title)} ↗</a></h3><div>${r.research_topics.map(t=>`<span class="chip">${esc(topicName(t))}</span>`).join('')}${r.related_topics.map(t=>`<span class="chip">相关：${esc(topicName(t))}</span>`).join('')}</div>${unknown?'':`<p class="rationale">${esc(r.note)}</p>`}${r.methods.length?`<details><summary>方法标签</summary><p>${r.methods.map(esc).join(' · ')}</p></details>`:''}${r.evidence.length?`<details><summary>归属依据与来源</summary><p>复用既有核查；范围见各来源说明。</p>${r.evidence.map(e=>`<a href="${esc(e.url)}" target="_blank" rel="noopener">${esc(e.url)} ↗</a><span>${esc(e.scope)}${e.locator?' · '+esc(e.locator):''}</span>`).join('')}</details>`:''}</div></article>`;}).join(''):'<p class="empty">没有匹配论文。试试清除筛选，或用论文完整名称搜索。</p>';
 }
 $('topics').addEventListener('click',e=>{const b=e.target.closest('button');if(!b)return;topic=b.dataset.topic;for(const x of $('topics').children)x.setAttribute('aria-pressed',String(x===b));render();});
 for(const id of ['q','method','morph','role','includeRelated'])$(id).addEventListener('input',render);
 $('searchform').addEventListener('submit',e=>e.preventDefault());$('reset').addEventListener('click',()=>{topic='';for(const id of ['q','method','morph','role'])$(id).value='';$('includeRelated').checked=true;for(const b of $('topics').children)b.setAttribute('aria-pressed',String(!b.dataset.topic));render();});render();
 }).catch(()=>{$('count').textContent='预览数据未能加载';$('results').textContent='请从本地 HTTP 预览打开此页面，或返回原站浏览论文。';});
}
