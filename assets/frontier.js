'use strict';
(() => {
 const grid=document.querySelector('#frontier-grid'); if(!grid) return;
 const cards=Array.from(grid.querySelectorAll('.frontier-card'));
 const select=document.querySelector('#frontier-topic'),count=document.querySelector('#frontier-count'),more=document.querySelector('#frontier-more'),empty=document.querySelector('#frontier-empty');
 let limit=20;
 function apply(reset=true){
  if(reset)limit=20;
  const value=select.value;
  const matched=cards.filter(c=>value==='all'||(value==='focused'?c.dataset.focus==='true':c.dataset.topics.split(' ').includes(value)));
  cards.forEach(c=>c.hidden=true);matched.forEach((c,i)=>c.hidden=i>=limit);
  count.textContent=`${matched.length} 条自动匹配候选 · 显示 ${Math.min(limit,matched.length)} 条`;
  more.hidden=matched.length<=limit;more.textContent=`显示更多候选（还剩 ${Math.max(0,matched.length-limit)} 条） ↓`;empty.hidden=matched.length!==0;
 }
 select.addEventListener('change',()=>apply());more.addEventListener('click',()=>{limit+=20;apply(false)});apply();
})();
