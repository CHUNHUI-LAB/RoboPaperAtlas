/* Original procedural Atlas artwork. Star positions are abstract, not paper/citation data. */
(function () {
 'use strict';
 const TAU = Math.PI * 2;
 function makeStars(count = 3600) {
  let state = 721947;
  const random = () => ((state = (Math.imul(1664525, state) + 1013904223) >>> 0) / 4294967296);
  const normal = () => Math.sqrt(-2 * Math.log(Math.max(random(), .000001))) * Math.cos(TAU * random());
  const stars = [];
  for (let i = 0; i < count; i++) {
   const arm = i % 5, r = Math.pow(random(), .68), scattered = random() < .16;
   const theta = arm * TAU / 5 + 4.75 * Math.pow(r, .68) + normal() * (scattered ? .95 : .07 + .07 * r);
   const radius = 202 * r;
   stars.push({x: Math.cos(theta) * radius, y: Math.sin(theta) * radius,
    z: normal() * (3.5 + 10 * (1-r)), r, arm,
    size: .22 + Math.pow(random(), 4) * 1.13,
    light: .22 + .77 * Math.pow(random(), .8), phase: random() * TAU,
    color: random() < .12 ? 1 : random() < .14 ? 2 : 0});
  }
  for (let i = 0; i < 110; i++) {
   const r = 23 * Math.pow(random(), 1.5), a = random() * TAU;
   stars.push({x: Math.cos(a)*r, y:Math.sin(a)*r, z:normal()*5, r:r/202, arm:0,
    size:.35+random()*.9, light:.5+random()*.5, phase:random()*TAU, color:0});
  }
  return stars;
 }
 function project(star, seconds) {
  const a = seconds * .011 + .22, ca = Math.cos(a), sa = Math.sin(a);
  const x = star.x * ca - star.y * sa, y = star.x * sa + star.y * ca;
  const tilt = .77 + Math.sin(seconds * .018) * .028;
  const py = y * Math.cos(tilt) - star.z * Math.sin(tilt), depth = y * Math.sin(tilt) + star.z * Math.cos(tilt);
  const roll = -.56, perspective = 1 + depth / 1250;
  return {x:280 + (x * Math.cos(roll) - py * Math.sin(roll))*perspective,
   y:204 + (x * Math.sin(roll) + py * Math.cos(roll))*perspective,
   radius:star.size*(.9+depth/650), opacity:star.light*(.77+depth/950)*(.90+.10*Math.sin(seconds*.52+star.phase)), color:star.color};
 }
 const regions=[{key:'navigation',x:164,y:176,rx:57,ry:51},{key:'mobile-manipulation',x:198,y:104,rx:57,ry:51},{key:'wbc',x:281,y:97,rx:57,ry:51},{key:'locomotion',x:365,y:139,rx:57,ry:51},{key:'policy-learning',x:396,y:217,rx:57,ry:51},{key:'spatial-representations',x:352,y:294,rx:57,ry:51},{key:'general-ml',x:264,y:315,rx:57,ry:51},{key:'resources',x:183,y:271,rx:57,ry:51},{key:'cross-domain',x:279,y:204,rx:47,ry:43}];
 function focusProjection(p,weights){
  let x=p.x,y=p.y,local=0,total=0;
  weights.forEach((weight,i)=>{const r=regions[i],dx=p.x-r.x,dy=p.y-r.y,g=Math.exp(-.5*((dx/r.rx)**2+(dy/r.ry)**2));
   total+=weight;local+=weight*g;x+=dx*.72*weight*g;y+=dy*.72*weight*g;
  });
  const dx=x-p.x,dy=y-p.y,roomX=dx>=0?552-p.x:p.x-8,roomY=dy>=0?400-p.y:p.y-8;
  x=p.x+roomX*Math.tanh(dx/roomX);y=p.y+roomY*Math.tanh(dy/roomY);
  return {...p,x,y,radius:p.radius*(1+local*.42),opacity:Math.min(1,p.opacity*(1-total*.83+local*1.65)),local};
 }
 if (typeof module !== 'undefined' && module.exports) { module.exports = {makeStars, project, regions, focusProjection}; return; }
 const colors = ['227,237,246','153,221,199','187,169,232'];
 function initialize(root) {
  if (root.dataset.atlasInitialized) return;
  const canvas = root.querySelector('canvas');let ctx=null;try{ctx=canvas&&canvas.getContext('2d');}catch{} // Keep real topic/paper links usable without Canvas.
  root.dataset.atlasInitialized = 'true';
  const stars = makeStars(), toggle = root.querySelector('[data-atlas-toggle]');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)'), compact = window.matchMedia('(max-width: 767px)');
  const topicLinks=[...root.querySelectorAll('[data-atlas-topic]')],panels=[...root.querySelectorAll('[data-atlas-panel]')],overview=root.querySelector('.atlas-galaxy__overview'),status=root.querySelector('[data-atlas-status]');
  topicLinks.forEach(link=>{link.setAttribute('aria-expanded','false');link.setAttribute('aria-controls','atlas-panel-'+link.dataset.atlasTopic);});root.dataset.activeTopic='overview';
  let suppressFocus=false,active=null,hovered=null,focused=null,weights=regions.map(()=>0),targets=regions.map(()=>0);
  let userPaused=false, inView=!('IntersectionObserver' in window), elapsed=0, previous=null, lastPaint=0, frame=0, disposed=false;
  const sprites = ctx ? colors.map(color => {
   const sprite=document.createElement('canvas');sprite.width=sprite.height=48;
   const c=sprite.getContext('2d'),gradient=c.createRadialGradient(24,24,0,24,24,24);
   gradient.addColorStop(0,`rgba(${color},.85)`);gradient.addColorStop(.11,`rgba(${color},.38)`);gradient.addColorStop(.38,`rgba(${color},.065)`);gradient.addColorStop(1,`rgba(${color},0)`);
   c.fillStyle=gradient;c.fillRect(0,0,48,48);return sprite;
  }) : [];
  const staticMode=()=>reduced.matches||compact.matches;
  const canRun=()=>!!ctx&&!disposed&&!userPaused&&inView&&!document.hidden&&!staticMode();
  function draw(seconds) {
   if(!ctx)return;
   const width=canvas.clientWidth||560, height=canvas.clientHeight||408, dpr=Math.min(window.devicePixelRatio||1,2);
   const w=Math.round(width*dpr),h=Math.round(height*dpr);
   if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
   ctx.setTransform(w/560,0,0,h/408,0,0);ctx.clearRect(0,0,560,408);
   // A tiny luminous nucleus anchors the composition, without filling the negative space.
   const core=ctx.createRadialGradient(280,204,0,280,204,42);
   core.addColorStop(0,`rgba(220,234,249,${.10*(1-Math.min(1,weights.reduce((a,b)=>a+b,0))*.8)})`);core.addColorStop(.2,'rgba(174,197,224,.045)');core.addColorStop(1,'rgba(160,190,230,0)');
   ctx.fillStyle=core;ctx.fillRect(238,162,84,84);
   for(const s of stars){const p=focusProjection(project(s,seconds),weights);ctx.globalAlpha=p.opacity;
    if(s.size>1.02){const r=p.radius*(9+p.local*3);ctx.drawImage(sprites[p.color],p.x-r,p.y-r,r*2,r*2);}
    ctx.fillStyle=`rgb(${colors[p.color]})`;ctx.beginPath();ctx.arc(p.x,p.y,Math.max(.16,p.radius),0,TAU);ctx.fill();
   }
   ctx.globalAlpha=1;
  }
  function controls(){toggle.hidden=staticMode()||!ctx;toggle.setAttribute('aria-pressed',String(userPaused));toggle.textContent=userPaused?'播放星图':'暂停星图';root.dataset.paused=String(!canRun());root.dataset.static=String(staticMode());}
  function tick(now){frame=0;if(!root.isConnected){destroy();return;}if(!canRun()){previous=null;return;}
   const dt=previous===null?0:Math.min((now-previous)/1000,.1);elapsed+=dt;previous=now;const blend=1-Math.exp(-dt/0.19);weights=weights.map((w,i)=>w+(targets[i]-w)*blend);
   if(now-lastPaint>=32){draw(elapsed);lastPaint=now;}frame=requestAnimationFrame(tick);
  }
  function reconcile(){if(disposed)return;if(frame)cancelAnimationFrame(frame);frame=0;previous=null;controls();if(!canRun())weights=[...targets];draw(staticMode()?0:elapsed);if(canRun())frame=requestAnimationFrame(tick);}
  function select(key){
   if(disposed||active===key||key!==null&&!regions.some(r=>r.key===key))return;active=key;targets=regions.map(r=>Number(r.key===key));root.dataset.activeTopic=key||'overview';
   topicLinks.forEach(link=>{const selected=link.dataset.atlasTopic===key;link.classList.toggle('is-active',selected);link.setAttribute('aria-expanded',String(selected));});
   panels.forEach(panel=>{const selected=panel.dataset.atlasPanel===key;panel.classList.toggle('is-active',selected);panel.inert=!selected;panel.setAttribute('aria-hidden',String(!selected));});
   overview.classList.toggle('is-hidden',!!key);overview.setAttribute('aria-hidden',String(!!key));
   const selected=topicLinks.find(link=>link.dataset.atlasTopic===key);status.textContent=selected?selected.getAttribute('aria-label')+'，展示两个目录入口示例。':'';
   if(!canRun()){weights=[...targets];draw(staticMode()?0:elapsed);}
  }
  const onOver=e=>{if(document.activeElement?.closest('[data-atlas-panel]'))return;const link=e.target.closest('[data-atlas-topic]');if(link&&root.contains(link)){hovered=link.dataset.atlasTopic;select(hovered);}};
  const onLeave=()=>{hovered=null;select(focused);};
  const onFocus=e=>{if(suppressFocus)return;const link=e.target.closest('[data-atlas-topic]');if(link){focused=link.dataset.atlasTopic;select(focused);}else if(e.target.closest('[data-atlas-panel]')){focused=e.target.closest('[data-atlas-panel]').dataset.atlasPanel;select(focused);}};
  const onBlur=e=>{if(!root.contains(e.relatedTarget)){focused=null;select(hovered);}};
  const onKey=e=>{
   if(e.key==='Escape'&&active){e.preventDefault();const focusKey=e.target.closest('[data-atlas-topic]')?.dataset.atlasTopic||e.target.closest('[data-atlas-panel]')?.dataset.atlasPanel||active;const link=topicLinks.find(a=>a.dataset.atlasTopic===focusKey);hovered=null;focused=null;select(null);suppressFocus=true;link?.focus({preventScroll:true});suppressFocus=false;}
   else if(e.key==='ArrowDown'&&e.target.closest('[data-atlas-topic]')){e.preventDefault();focused=e.target.closest('[data-atlas-topic]').dataset.atlasTopic;select(focused);panels.find(p=>p.dataset.atlasPanel===active)?.querySelector('a')?.focus({preventScroll:true});}
   else if(e.key==='ArrowUp'&&e.target.closest('[data-atlas-panel]')&&active){e.preventDefault();topicLinks.find(a=>a.dataset.atlasTopic===active)?.focus({preventScroll:true});}
  };
  const onToggle=()=>{userPaused=!userPaused;reconcile();};
  const onResize=()=>{if(!disposed)draw(staticMode()?0:elapsed);};
  root.addEventListener('pointerover',onOver);root.addEventListener('pointerleave',onLeave);root.addEventListener('focusin',onFocus);root.addEventListener('focusout',onBlur);root.addEventListener('keydown',onKey);
  toggle.addEventListener('click',onToggle);document.addEventListener('visibilitychange',reconcile);
  reduced.addEventListener('change',reconcile);compact.addEventListener('change',reconcile);window.addEventListener('resize',onResize);
  const observer='IntersectionObserver' in window?new IntersectionObserver(entries=>{if(disposed)return;inView=entries.some(e=>e.isIntersecting);reconcile();},{threshold:.05}):null;
  if(observer)observer.observe(root);
  function destroy(){if(disposed)return;disposed=true;if(frame)cancelAnimationFrame(frame);frame=0;observer?.disconnect();toggle.removeEventListener('click',onToggle);document.removeEventListener('visibilitychange',reconcile);reduced.removeEventListener('change',reconcile);compact.removeEventListener('change',reconcile);window.removeEventListener('resize',onResize);root.removeEventListener('pointerover',onOver);root.removeEventListener('pointerleave',onLeave);root.removeEventListener('focusin',onFocus);root.removeEventListener('focusout',onBlur);root.removeEventListener('keydown',onKey);delete root.dataset.atlasInitialized;root.classList.remove('atlas-ready');root.classList.remove('atlas-interactive');topicLinks.forEach(a=>{a.classList.remove('is-active');a.removeAttribute('aria-expanded');});panels.forEach(p=>{p.classList.remove('is-active');p.inert=true;p.setAttribute('aria-hidden','true');});overview.classList.remove('is-hidden');overview.setAttribute('aria-hidden','false');status.textContent='';delete root.dataset.activeTopic;toggle.hidden=true;delete root.atlasDestroy;}
  root.atlasDestroy=destroy;draw(0);if(ctx)root.classList.add('atlas-ready');root.classList.add('atlas-interactive');reconcile();
 }
 const init=()=>document.querySelectorAll('.atlas-galaxy').forEach(initialize);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
