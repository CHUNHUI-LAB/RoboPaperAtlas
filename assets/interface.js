'use strict';
(() => {
 const root=document.body.dataset.root||'';
 const menu=document.querySelector('.mobile-menu'),nav=document.querySelector('#main-nav');
 function closeMenu(){menu.setAttribute('aria-expanded','false');nav.classList.remove('open')}
 menu.addEventListener('click',()=>{const open=menu.getAttribute('aria-expanded')!=='true';menu.setAttribute('aria-expanded',String(open));nav.classList.toggle('open',open)});
 nav.addEventListener('click',e=>{if(e.target.closest('a'))closeMenu()});
 const dialog=document.querySelector('#search-dialog'),input=document.querySelector('#global-search-input'),results=document.querySelector('#global-search-results'),status=document.querySelector('#global-search-status');
 let index=null,pending=null,opener=null;
 function showResults(){
  results.replaceChildren();const query=input.value.trim().toLocaleLowerCase(),terms=query.split(/\s+/).filter(Boolean);
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
  try{if(!index){pending=pending||fetch(root+'data/search-index.json').then(r=>{if(!r.ok)throw new Error('HTTP '+r.status);return r.json()});index=await pending}showResults()}
  catch(e){pending=null;status.textContent='搜索索引暂时无法载入，请使用下方完整目录入口'}
 }
 document.querySelector('.global-search-trigger').addEventListener('click',openSearch);
 document.querySelector('.dialog-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>{if(opener&&opener.isConnected)opener.focus()});
 dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()}});
 input.addEventListener('input',showResults);
 document.querySelector('#global-search-form').addEventListener('submit',e=>{e.preventDefault();results.querySelector('a')?.click()});
 dialog.addEventListener('keydown',e=>{
  if(!['ArrowDown','ArrowUp'].includes(e.key))return;
  const links=Array.from(results.querySelectorAll('a'));if(!links.length)return;
  e.preventDefault();let at=links.indexOf(document.activeElement);at=e.key==='ArrowDown'?Math.min(links.length-1,at+1):at-1;
  if(at<0)input.focus();else links[at].focus();
 });
 document.addEventListener('keydown',e=>{
  if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='k'){e.preventDefault();dialog.open?dialog.close():openSearch()}
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
