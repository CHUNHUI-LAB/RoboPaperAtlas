/* Reader controls only: no models, analytics, remote scripts or automatic PDF fetch. */
(() => {
 'use strict';
 const page=document.querySelector('.reader-page');if(!page)return;
 const reduced=matchMedia('(prefers-reduced-motion: reduce)'),toc=page.querySelector('.reader-toc'),tocButton=page.querySelector('.reader-toc-toggle');
 const sections=[...page.querySelectorAll('.reader-article>section[id]')],tocLinks=[...toc.querySelectorAll('a[href^="#"]')];
 let frame=0,toastTimer=0,toast=document.querySelector('.reader-toast');
 function announce(message){clearTimeout(toastTimer);toast.textContent=message;toast.hidden=false;toastTimer=setTimeout(()=>{toast.hidden=true;},2400);}
 function updatePosition(){frame=0;let current=sections[0];for(const section of sections){if(section.getBoundingClientRect().top<=175)current=section;else break;}tocLinks.forEach(link=>{const active=link.hash==='#'+current?.id;link.classList.toggle('is-current',active);if(active)link.setAttribute('aria-current','location');else link.removeAttribute('aria-current');});}
 const schedule=()=>{if(!frame&&!document.hidden)frame=requestAnimationFrame(updatePosition);};
 window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);window.addEventListener('hashchange',schedule);window.addEventListener('pageshow',schedule);
 document.addEventListener('visibilitychange',()=>{if(document.hidden){cancelAnimationFrame(frame);frame=0;}else schedule();});
 function closeToc(restore=false){toc.classList.remove('is-open');tocButton.setAttribute('aria-expanded','false');if(restore)tocButton.focus();}
 tocButton.addEventListener('click',()=>{const open=!toc.classList.contains('is-open');toc.classList.toggle('is-open',open);tocButton.setAttribute('aria-expanded',String(open));if(open)(toc.querySelector('.is-current')||tocLinks[0])?.focus();});
 tocLinks.forEach(link=>link.addEventListener('click',()=>{closeToc();if(matchMedia('(max-width:767px)').matches)document.getElementById(link.hash.slice(1))?.focus({preventScroll:true});}));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&toc.classList.contains('is-open')&&!document.querySelector('dialog[open]')){e.preventDefault();closeToc(true);}});
 document.addEventListener('focusin',e=>{if(toc.classList.contains('is-open')&&e.target!==tocButton&&!toc.contains(e.target))closeToc();});
 const copies=new WeakMap();
 page.querySelectorAll('[data-copy-code]').forEach(button=>button.addEventListener('click',async()=>{
  const holder=button.closest('.code-reader'),lines=[...holder.querySelectorAll('.code-text')].map(line=>line.textContent),token=(copies.get(button)||0)+1;copies.set(button,token);
  try{await navigator.clipboard.writeText(lines.join('\n'));if(copies.get(button)===token&&button.isConnected)announce('代码片段已复制，未包含行号');}
  catch{if(copies.get(button)===token&&button.isConnected)announce('未能访问剪贴板，可在代码框中手动选择复制');}
 }));
 page.querySelectorAll('[data-code-focus]').forEach(button=>button.addEventListener('click',()=>{
  const holder=button.closest('.code-reader'),active=!holder.classList.contains('is-focused');holder.classList.toggle('is-focused',active);button.setAttribute('aria-pressed',String(active));
  const pre=holder.querySelector('pre'),first=holder.querySelector('.code-line.is-key');
  if(active&&first)pre.scrollTo({top:Math.max(0,first.offsetTop-pre.clientHeight/3),behavior:reduced.matches?'auto':'smooth'});
 }));
 const sourceData=page.querySelector('[data-source-units]');
 if(sourceData){
  let units=[];try{units=JSON.parse(sourceData.textContent);}catch{};
  const panel=page.querySelector('.reader-source-panel'),rows=page.querySelectorAll('[data-source-row]'),buttons=page.querySelectorAll('[data-source-unit]');let selected=0;
  const show=(id,scroll=false)=>{const index=units.findIndex(x=>x.id===id);if(index<0)return;selected=index;const unit=units[index];
   panel.querySelector('[data-source-id]').textContent=unit.id;panel.querySelector('[data-source-location]').textContent=unit.location;panel.querySelector('[data-source-paraphrase]').textContent=unit.paraphrase;
   const quote=panel.querySelector('[data-source-quote]');quote.hidden=!unit.quote;quote.textContent=unit.quote||'';
   const a=panel.querySelector('[data-source-open]');a.href=unit.url;a.textContent='打开 / 下载正式 PDF · 第'+unit.page+'页 ↗';
   panel.querySelector('[data-source-previous]').disabled=index===0;panel.querySelector('[data-source-next]').disabled=index===units.length-1;
   rows.forEach(row=>row.classList.toggle('is-current',row.dataset.sourceRow===id));buttons.forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.sourceUnit===id)));
   if(scroll)page.querySelector('[data-source-row="'+CSS.escape(id)+'"]')?.scrollIntoView({block:'start',behavior:reduced.matches?'auto':'smooth'});
  };
  buttons.forEach(b=>b.addEventListener('click',()=>{show(b.dataset.sourceUnit);if(innerWidth<=1050){const unit=units.find(x=>x.id===b.dataset.sourceUnit);announce(unit?.location||'已选择原文位置');}}));
  panel.querySelector('[data-source-previous]').addEventListener('click',()=>show(units[Math.max(0,selected-1)].id,true));panel.querySelector('[data-source-next]').addEventListener('click',()=>show(units[Math.min(units.length-1,selected+1)].id,true));
  const toggle=page.querySelector('[data-source-toggle]');toggle?.addEventListener('click',()=>{const off=page.classList.toggle('reader-source-collapsed');toggle.setAttribute('aria-pressed',String(!off));});if(units.length)show(units[0].id);
 }
 updatePosition();
})();
