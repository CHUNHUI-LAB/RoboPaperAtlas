'use strict';
(() => {
 const menu=document.querySelector('.preview-menu');if(!menu)return;
 const summary=menu.querySelector('summary');
 document.addEventListener('click',e=>{if(menu.open&&!menu.contains(e.target))menu.open=false});
 menu.addEventListener('keydown',e=>{if(e.key==='Escape'&&menu.open){e.preventDefault();e.stopPropagation();menu.open=false;summary.focus()}});
 menu.querySelectorAll('a').forEach(a=>a.addEventListener('click',()=>menu.open=false));
})();

// Only letters near the pointer show their actual outline/control geometry.
(() => {
 const svg=document.querySelector('.preview-title-vector');if(!svg)return;
 const letters=Array.from(svg.querySelectorAll('.vector-letter'));
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)'),fine=window.matchMedia('(hover:hover) and (pointer:fine) and (min-width:768px)');
 function clear(){letters.forEach(g=>g.classList.remove('editing'))}
 svg.addEventListener('pointermove',e=>{if(reduced.matches||!fine.matches)return;const rect=svg.getBoundingClientRect();const x=(e.clientX-rect.left)*svg.viewBox.baseVal.width/rect.width;letters.forEach(g=>g.classList.toggle('editing',Math.abs(x-Number(g.dataset.center))<Number(g.dataset.span)*.5+20))});
 svg.addEventListener('pointerleave',clear);reduced.addEventListener('change',clear);fine.addEventListener('change',clear);
})();

// Exactly one text pane and one fixed-geometry media panel are active.
(() => {
 const items=Array.from(document.querySelectorAll('.preview-accordion-item')),media=Array.from(document.querySelectorAll('[data-media]'));
 if(!items.length)return;
 const buttons=items.map(item=>item.querySelector('[data-panel]'));
 function select(button){const selected=button.dataset.panel;items.forEach(item=>{const control=item.querySelector('[data-panel]'),copy=item.querySelector('.accordion-copy'),active=control.dataset.panel===selected;item.classList.toggle('active',active);control.setAttribute('aria-expanded',String(active));copy.inert=!active});media.forEach(img=>{const active=img.dataset.media===selected;img.classList.toggle('active',active);img.setAttribute('aria-hidden',String(!active))})}
 buttons.forEach((button,i)=>{button.addEventListener('click',()=>select(button));button.addEventListener('keydown',e=>{if(!['ArrowDown','ArrowUp','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?buttons.length-1:(i+(e.key==='ArrowDown'?1:-1)+buttons.length)%buttons.length;buttons[next].focus();select(buttons[next])})});
})();
