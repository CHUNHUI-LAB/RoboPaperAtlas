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
 if (typeof module !== 'undefined' && module.exports) { module.exports = {makeStars, project}; return; }
 const colors = ['227,237,246','153,221,199','187,169,232'];
 function initialize(root) {
  if (root.dataset.atlasInitialized) return;
  const canvas = root.querySelector('canvas'), ctx = canvas && canvas.getContext('2d');
  if (!ctx) return; // The authored static star field and real topic links remain usable.
  root.dataset.atlasInitialized = 'true';
  const stars = makeStars(), toggle = root.querySelector('[data-atlas-toggle]');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)'), compact = window.matchMedia('(max-width: 767px)');
  let userPaused=false, inView=!('IntersectionObserver' in window), elapsed=0, previous=null, lastPaint=0, frame=0, disposed=false;
  const sprites = colors.map(color => {
   const sprite=document.createElement('canvas');sprite.width=sprite.height=48;
   const c=sprite.getContext('2d'),gradient=c.createRadialGradient(24,24,0,24,24,24);
   gradient.addColorStop(0,`rgba(${color},.85)`);gradient.addColorStop(.11,`rgba(${color},.38)`);gradient.addColorStop(.38,`rgba(${color},.065)`);gradient.addColorStop(1,`rgba(${color},0)`);
   c.fillStyle=gradient;c.fillRect(0,0,48,48);return sprite;
  });
  const staticMode=()=>reduced.matches||compact.matches;
  const canRun=()=>!disposed&&!userPaused&&inView&&!document.hidden&&!staticMode();
  function draw(seconds) {
   const width=canvas.clientWidth||560, height=canvas.clientHeight||408, dpr=Math.min(window.devicePixelRatio||1,2);
   const w=Math.round(width*dpr),h=Math.round(height*dpr);
   if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;}
   ctx.setTransform(w/560,0,0,h/408,0,0);ctx.clearRect(0,0,560,408);
   // A tiny luminous nucleus anchors the composition, without filling the negative space.
   const core=ctx.createRadialGradient(280,204,0,280,204,42);
   core.addColorStop(0,'rgba(220,234,249,.10)');core.addColorStop(.2,'rgba(174,197,224,.045)');core.addColorStop(1,'rgba(160,190,230,0)');
   ctx.fillStyle=core;ctx.fillRect(238,162,84,84);
   for(const s of stars){const p=project(s,seconds);ctx.globalAlpha=p.opacity;
    if(s.size>1.02){const r=p.radius*9;ctx.drawImage(sprites[p.color],p.x-r,p.y-r,r*2,r*2);}
    ctx.fillStyle=`rgb(${colors[p.color]})`;ctx.beginPath();ctx.arc(p.x,p.y,Math.max(.16,p.radius),0,TAU);ctx.fill();
   }
   ctx.globalAlpha=1;
  }
  function controls(){toggle.hidden=staticMode();toggle.setAttribute('aria-pressed',String(userPaused));toggle.textContent=userPaused?'播放星图':'暂停星图';root.dataset.paused=String(!canRun());root.dataset.static=String(staticMode());}
  function tick(now){frame=0;if(!root.isConnected){destroy();return;}if(!canRun()){previous=null;return;}
   if(previous!==null)elapsed+=Math.min((now-previous)/1000,.1);previous=now;
   if(now-lastPaint>=32){draw(elapsed);lastPaint=now;}frame=requestAnimationFrame(tick);
  }
  function reconcile(){if(disposed)return;if(frame)cancelAnimationFrame(frame);frame=0;previous=null;controls();draw(staticMode()?0:elapsed);if(canRun())frame=requestAnimationFrame(tick);}
  const onToggle=()=>{userPaused=!userPaused;reconcile();};
  const onResize=()=>{if(!disposed)draw(staticMode()?0:elapsed);};
  toggle.addEventListener('click',onToggle);document.addEventListener('visibilitychange',reconcile);
  reduced.addEventListener('change',reconcile);compact.addEventListener('change',reconcile);window.addEventListener('resize',onResize);
  const observer='IntersectionObserver' in window?new IntersectionObserver(entries=>{if(disposed)return;inView=entries.some(e=>e.isIntersecting);reconcile();},{threshold:.05}):null;
  if(observer)observer.observe(root);
  function destroy(){if(disposed)return;disposed=true;if(frame)cancelAnimationFrame(frame);frame=0;observer?.disconnect();toggle.removeEventListener('click',onToggle);document.removeEventListener('visibilitychange',reconcile);reduced.removeEventListener('change',reconcile);compact.removeEventListener('change',reconcile);window.removeEventListener('resize',onResize);delete root.dataset.atlasInitialized;root.classList.remove('atlas-ready');toggle.hidden=true;delete root.atlasDestroy;}
  root.atlasDestroy=destroy;draw(0);root.classList.add('atlas-ready');reconcile();
 }
 const init=()=>document.querySelectorAll('.atlas-galaxy').forEach(initialize);
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
