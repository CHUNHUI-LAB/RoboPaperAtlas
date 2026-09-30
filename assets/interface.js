'use strict';
(() => {
 document.body.classList.add('js-ready');
 const root=document.body.dataset.root||'';
 const menu=document.querySelector('.mobile-menu'),nav=document.querySelector('#main-nav');
 function closeMenu(){menu.setAttribute('aria-expanded','false');nav.classList.remove('open')}
 menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open)});
 nav.addEventListener('click',e=>{if(e.target.closest('a'))closeMenu()});
 const dialog=document.querySelector('#search-dialog'),input=document.querySelector('#global-search-input'),results=document.querySelector('#global-search-results'),status=document.querySelector('#global-search-status');
 let index=null,pending=null,opener=null;
 function showResults(){
  results.replaceChildren();const allLink=document.querySelector('#global-all-results');allLink.href=root+'index.html'+(input.value.trim()?'?q='+encodeURIComponent(input.value.trim()):'')+'#catalog';allLink.textContent=input.value.trim()?'查看全部匹配结果 ↗':'进入完整目录 ↗';const query=input.value.trim().toLocaleLowerCase(),terms=query.split(/\s+/).filter(Boolean);
  if(!index){status.textContent='正在载入目录…';return}
  if(!terms.length){status.textContent='试试 HarnessVLN、whole-body、diffusion 或作者名';return}
  const matches=index.filter(p=>terms.every(t=>p.text.toLocaleLowerCase().includes(t)));
  status.textContent=matches.length?`找到 ${matches.length} 篇论文，显示前 ${Math.min(8,matches.length)} 篇`:'没有匹配论文，试试更短的关键词';
  for(const p of matches.slice(0,8)){
   const li=document.createElement('li'),a=document.createElement('a'),title=document.createElement('strong'),meta=document.createElement('span');
   a.href=root+'papers/'+encodeURIComponent(p.id)+'/index.html';title.textContent=p.title;meta.textContent=p.category+' · '+p.authors;a.append(title,meta);li.append(a);results.append(li);
  }
 }
 async function openSearch(){
  opener=document.activeElement;closeMenu();if(!dialog.open)dialog.showModal();input.focus();showResults();
  try{if(!index){pending=pending||fetch(root+'data/search-index.json?v='+encodeURIComponent(document.body.dataset.dataVersion||'1')).then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()});index=await pending}showResults()}
  catch(e){pending=null;status.textContent='搜索索引暂时无法载入，请使用下方完整目录入口'}
 }
 document.querySelectorAll('.global-search-trigger,[data-search-trigger]').forEach(b=>b.addEventListener('click',openSearch));
 document.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{if(dialog.open)return;if(opener&&opener.isConnected)opener.focus()});
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
 input.addEventListener('input',showResults);
 document.querySelector('#global-search-form').addEventListener('submit',e=>{e.preventDefault();results.querySelector('a')?.click()});
 dialog.addEventListener('keydown',e=>{
  if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dialog.close();return}
  if(!['ArrowDown','ArrowUp'].includes(e.key))return;
  const links=Array.from(results.querySelectorAll('a'));if(!links.length)return;
  e.preventDefault();let at=links.indexOf(document.activeElement);at=e.key==='ArrowDown'?Math.min(links.length-1,at+1):at-1;
  if(at<0)input.focus();else links[at].focus();
 },true);
 document.addEventListener('keydown',e=>{
  if(e.key==='/'&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&!['INPUT','TEXTAREA','SELECT'].includes(document.activeElement.tagName)&&!dialog.open&&!document.querySelector('#paper-drawer').open){e.preventDefault();openSearch()}
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();if(document.querySelector('#paper-drawer').open)return;dialog.open?dialog.close():openSearch()}
  if(e.key==='Escape'&&menu.getAttribute('aria-expanded')==='true'){closeMenu();menu.focus()}
 });
 let toastTimer;
 document.querySelector('.copy-page')?.addEventListener('click',async()=>{
  const toast=document.querySelector('.toast');
  try{await navigator.clipboard.writeText(window.location.href);toast.textContent='本页链接已复制'}catch(e){toast.textContent='无法自动复制，请从浏览器地址栏复制链接'}
  toast.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>toast.hidden=true,3500);
 });
 const sections=Array.from(document.querySelectorAll('.detail-section[id]')),toc=Array.from(document.querySelectorAll('.detail-toc a'));
 if(sections.length&&'IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{for(const entry of entries){if(entry.isIntersecting){toc.forEach(a=>{const active=a.hash==='#'+entry.target.id;a.classList.toggle('active',active);if(active)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current')})}}},{rootMargin:'-90px 0px -65% 0px'});sections.forEach(s=>observer.observe(s));
 }
})();

// Contextual quick view keeps the reading flow on the catalogue.
(() => {
 const drawer=document.querySelector('#paper-drawer');if(!drawer)return;
 const root=document.body.dataset.root||'',body=document.querySelector('#drawer-body'),close=document.querySelector('.drawer-close');
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');let catalog=null,pending=null,opener=null,requestId=0,closing=false,closeEpoch=0;
 const text=(tag,content,className)=>{const el=document.createElement(tag);el.textContent=content;if(className)el.className=className;return el};
 function safeLink(url,label,className){const a=document.createElement('a');try{const u=new URL(url,window.location.href);if(!['http:','https:'].includes(u.protocol))return null;a.href=u.href}catch(e){return null}a.textContent=label;a.className=className||'';return a}
 function dismiss(){if(closing||!drawer.open)return;closing=true;requestId++;closeEpoch++;drawer.close();closing=false}
 drawer.addEventListener('close',()=>{if(drawer.open)return;if(opener?.isConnected)opener.focus()});
 drawer.addEventListener('cancel',e=>{e.preventDefault();dismiss()});
 drawer.addEventListener('keydown',e=>{if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dismiss()}},true);
 drawer.addEventListener('click',e=>{if(e.target===drawer){const r=drawer.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dismiss()}});
 close.addEventListener('click',dismiss);
 async function show(button){
  opener=button;closeEpoch++;drawer.getAnimations().forEach(a=>a.cancel());closing=false;const current=++requestId,id=button.dataset.preview;body.replaceChildren(text('h2','正在载入论文…'));body.firstChild.id='drawer-title';if(!drawer.open)drawer.showModal();close.focus();
  try{
   if(!catalog){pending=pending||fetch(root+'data/catalog.json?v='+encodeURIComponent(document.body.dataset.dataVersion||'1')).then(r=>{if(!r.ok)throw new Error('Fetch failed');return r.json()});catalog=await pending}
   if(current!==requestId||!drawer.open)return;
   const p=catalog.papers.find(p=>p.id===id);if(!p)throw new Error('Paper unavailable');
   const overlay=p.verified_overlay||{},title=overlay.title||p.title,a=overlay.authors||p.authors,authors=Array.isArray(a)?a.join(', '):a;
   body.replaceChildren();body.append(text('p',(p.bibliographic_year||'年份待核验')+' · '+(p.citation_verified?'来源已核验':'原始书目待核验'),'drawer-kicker'));
   const h=text('h2',title);h.id='drawer-title';body.append(h,text('p',authors,'drawer-authors'),text('p',p.summary||'已收录原始书目，题名、作者与年份尚待来源核验。','drawer-summary'));
   if(button.dataset.directionLabel)body.append(text('p',button.dataset.directionLabel+' / '+button.dataset.problemLabel,'drawer-taxonomy'));
   const resources=document.createElement('div');resources.className='drawer-resources';
   for(const [url,label] of [[p.pdf_url,p.pdf_kind==='publisher'?'出版方 PDF ↗':'预印本替代 PDF ↗'],[p.paper_url,'出版 / 论文页面 ↗'],[p.project_url,'官方项目 ↗']]){if(url){const a=safeLink(url,label);if(a){a.target='_blank';a.rel='noopener noreferrer';resources.append(a)}}}
   if(resources.children.length)body.append(resources);
   const reports=document.createElement('div');reports.className='drawer-resources';
   for(const [i,name]of ['初读','写作精读','方法精读'].entries()){const stage=p.stages?.['stage'+(i+1)],artifact=stage?.status==='imported'?stage.artifacts[0]:null;if(artifact&&/^artifacts\/rpa-0062\/v[12]\/(first-pass|writing-close-reading|method-code-reading)\.html$/.test(artifact.path)){const a=safeLink(root+artifact.path,'S'+(i+1)+' '+name+' ↗');if(a)reports.append(a)}}
   if(reports.children.length)body.append(reports);
   body.append(text('p',reports.children.length?'已导入独立阅读报告。代码分析有明确范围，不代表已运行实验或独立复现。':'阅读档案尚未导入。来源核验不代表已完成论文阅读、代码审计或独立复现。','drawer-note'));
   if(p.pdf_note)body.append(text('p',p.pdf_note,'drawer-note'));
   const full=safeLink(root+'papers/'+encodeURIComponent(id)+'/index.html','打开完整详情 ↗','primary-link');if(full)body.append(full);
  }catch(e){pending=null;if(current!==requestId)return;body.replaceChildren();const h=text('h2','暂时无法载入速览');h.id='drawer-title';body.append(h,text('p','可以直接打开完整论文详情。','drawer-summary'));const a=safeLink(root+'papers/'+encodeURIComponent(id)+'/index.html','打开完整详情 ↗','primary-link');if(a)body.append(a)}
 }
 document.querySelectorAll('[data-preview]').forEach(button=>button.addEventListener('click',()=>show(button)));
})();
