'use strict';
(() => {
 const svg=document.querySelector('.experience-title .preview-title-vector');if(!svg)return;
 const letters=Array.from(svg.querySelectorAll('.vector-letter')),mode=window.matchMedia('(hover:hover) and (pointer:fine) and (min-width:768px)'),reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 const clear=()=>letters.forEach(g=>g.classList.remove('editing'));
 svg.addEventListener('pointermove',e=>{if(!mode.matches||reduced.matches)return;const rect=svg.getBoundingClientRect(),x=(e.clientX-rect.left)*svg.viewBox.baseVal.width/rect.width;letters.forEach(g=>g.classList.toggle('editing',Math.abs(x-Number(g.dataset.center))<Number(g.dataset.span)*.5+20))});svg.addEventListener('pointerleave',clear);mode.addEventListener('change',clear);reduced.addEventListener('change',clear);
})();
