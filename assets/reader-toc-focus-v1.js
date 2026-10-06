/* Presentation-only compatibility fix for the navigation Stage 1 v2 preview.
 * The fixed report and its inline runtime remain byte-identical. */
(() => {
 'use strict';
 const toc=document.querySelector('.reader-toc'),button=document.querySelector('.reader-toc-toggle');
 if(!toc||!button)return;
 let previousScroll=0;
 const originalMaxHeight=toc.style.maxHeight;
 // The fixed runtime centers offsetTop, which is not TOC-local in the F2
 // in-flow compact layout. Preserve the user's position before it runs.
 function rememberScroll(){if(toc.classList.contains('is-open'))previousScroll=toc.scrollTop;}
 button.addEventListener('click',rememberScroll,true);
 toc.addEventListener('scroll',rememberScroll,{passive:true});
 // Capture link activation before the fixed handler hides the panel.
 toc.addEventListener('click',rememberScroll,true);
 function reveal(){
  toc.style.maxHeight=originalMaxHeight;
  if(!toc.classList.contains('is-open'))return;
  const target=document.activeElement;
  if(!target||!toc.contains(target))return;
  const natural=toc.getBoundingClientRect(),viewport=document.documentElement.clientHeight;
  // The last row must also be reachable: a panel taller than the remaining
  // viewport cannot expose it even at its maximum scrollTop.
  const available=viewport-Math.max(natural.top,0)-8;
  if(available>0&&natural.height>available)toc.style.maxHeight=available+'px';
  toc.scrollTop=previousScroll;
  const box=toc.getBoundingClientRect(),link=target.getBoundingClientRect();
  // Use the intersection with the viewport: at 200% the in-flow TOC can
  // extend below the screen. Change only TOC scroll, never page/history.
  const top=Math.max(box.top+toc.clientTop,0)+6;
  const bottom=Math.min(box.top+toc.clientTop+toc.clientHeight,document.documentElement.clientHeight)-6;
  if(bottom<=top)return;
  const delta=link.top<top?link.top-top:link.bottom>bottom?Math.min(link.bottom-bottom,link.top-top):0;
  if(delta)toc.scrollTop+=delta;
  previousScroll=toc.scrollTop;
 }
 button.addEventListener('click',reveal);
 window.addEventListener('resize',()=>{rememberScroll();reveal();});
 // Escape, link activation, focus-out and media changes close through the
 // frozen runtime, not through our button listener. Restore presentation too.
 new MutationObserver(()=>{if(button.getAttribute('aria-expanded')!=='true')toc.style.maxHeight=originalMaxHeight;}).observe(button,{attributes:true,attributeFilter:['aria-expanded']});
})();
