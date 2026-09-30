'use strict';
(() => {
 document.querySelectorAll('.brief-reader').forEach(reader=>{
  const tabs=Array.from(reader.querySelectorAll('[data-brief-select]')),panels=Array.from(reader.querySelectorAll('[data-brief-panel]')),tablist=reader.querySelector('[role="tablist"]');
  if(!tabs.length)return;
  function select(tab){const id=tab.dataset.briefSelect;tabs.forEach(t=>{const active=t===tab;t.setAttribute('aria-selected',String(active));t.tabIndex=active?0:-1});panels.forEach(p=>{const active=p.dataset.briefPanel===id;p.classList.toggle('active',active);p.setAttribute('aria-hidden',String(!active));p.inert=!active})}
  tabs.forEach((tab,i)=>{tab.addEventListener('click',()=>select(tab));tab.addEventListener('keydown',e=>{if(!['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();let n=e.key==='Home'?0:e.key==='End'?tabs.length-1:(i+(['ArrowRight','ArrowDown'].includes(e.key)?1:-1)+tabs.length)%tabs.length;tabs[n].focus();select(tabs[n])})});
  const narrow=window.matchMedia('(max-width:767px)');const orient=()=>tablist.setAttribute('aria-orientation',narrow.matches?'horizontal':'vertical');narrow.addEventListener('change',orient);orient();reader.classList.add('is-interactive');tablist.hidden=false;select(tabs[0]);
 });
})();
