'use strict';
(()=>{
 if(matchMedia('(max-width:767px)').matches)document.querySelectorAll('.radar-theme').forEach(d=>d.removeAttribute('open'));
 const input=document.querySelector('#radar-candidate-search');if(!input)return;
 const rows=[...document.querySelectorAll('[data-radar-candidate]')],count=document.querySelector('#radar-candidate-count'),empty=document.querySelector('#radar-candidate-empty');
 const apply=()=>{const terms=input.value.normalize('NFKC').toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);let found=0;rows.forEach(row=>{row.hidden=!terms.every(t=>row.dataset.search.normalize('NFKC').includes(t));if(!row.hidden)found++;});count.textContent=found+' / '+rows.length+' 条窗口候选';empty.hidden=found!==0;};
 input.addEventListener('input',apply);input.addEventListener('keydown',e=>{if(e.key==='Escape'&&input.value){e.preventDefault();input.value='';apply();}});
 window.addEventListener('pageshow',apply);apply();
})();
