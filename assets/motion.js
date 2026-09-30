
'use strict';
// Keep the selected topic marker synchronized without decorative motion.
(() => {
 const tabs=document.querySelector('.topic-filters'),indicator=document.querySelector('.topic-indicator');
 function update(){if(!tabs||!indicator)return;const active=tabs.querySelector('[aria-pressed="true"]');if(active){indicator.style.width=active.offsetWidth+'px';indicator.style.transform=`translateX(${active.offsetLeft}px)`}}
 document.addEventListener('catalog:updated',update);window.addEventListener('resize',update);update();
})();
