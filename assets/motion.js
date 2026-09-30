'use strict';
(() => {
 const reduced=window.matchMedia('(prefers-reduced-motion: reduce)');
 const tabs=document.querySelector('.topic-filters'),indicator=document.querySelector('.topic-indicator');
 function underline(){if(!tabs||!indicator)return;const active=tabs.querySelector('[aria-pressed="true"]');if(active){indicator.style.width=active.offsetWidth+'px';indicator.style.transform=`translateX(${active.offsetLeft}px)`}}
 document.addEventListener('catalog:updated',()=>{underline();if(!reduced.matches){const grid=document.querySelector('#paper-grid');grid?.getAnimations().forEach(a=>a.cancel());grid?.animate([{opacity:.5},{opacity:1}],{duration:160,easing:'ease-out'})}});
 window.addEventListener('resize',underline);underline();
 const hero=document.querySelector('.atlas-hero'),canvas=document.querySelector('#coordinate-field'),toggle=document.querySelector('#motion-toggle');
 if(!hero||!canvas)return;
 const ctx=canvas.getContext('2d');if(!ctx)return;
 const desktop=window.matchMedia('(min-width:768px)');let w=1,h=1,visible=true,paused=false,frame=0,tick=0,last=0,px=0,py=0,tx=0,ty=0;
 const points=Array.from({length:270},(_,i)=>{const a=i*2.399963229728653;const y=1-2*(i+.5)/270;const r=Math.sqrt(1-y*y);return [Math.cos(a)*r,y,Math.sin(a)*r]});
 function resize(){const r=hero.getBoundingClientRect(),dpr=Math.min(window.devicePixelRatio||1,1.75);w=r.width;h=r.height;canvas.width=Math.round(w*dpr);canvas.height=Math.round(h*dpr);ctx.setTransform(dpr,0,0,dpr,0,0);draw();sync()}
 function project(x,y,z,angle){const ca=Math.cos(angle),sa=Math.sin(angle);let xx=x*ca-z*sa,zz=x*sa+z*ca;const pitch=.32;const yy=y*Math.cos(pitch)-zz*Math.sin(pitch);zz=y*Math.sin(pitch)+zz*Math.cos(pitch);const scale=1/(1-zz*.14),radius=Math.min(h*.34,w*.23);return [w*.775+xx*radius*scale+px,h*.47+yy*radius*scale+py,zz,scale]}
 function draw(){
  ctx.clearRect(0,0,w,h);if(!desktop.matches)return;
  const angle=tick*.000013+.32;const projected=points.map(p=>project(...p,angle)).sort((a,b)=>a[2]-b[2]);
  // Original abstract coordinate field. It encodes no paper counts or relationships.
  for(let orbit=0;orbit<3;orbit++){
   ctx.beginPath();for(let i=0;i<=120;i++){const a=i*Math.PI*2/120;let x=Math.cos(a)*1.24,y=Math.sin(a)*1.24,z=0;if(orbit===1){z=y*.87;y*=.49}else if(orbit===2){z=x*.8;x*=.6;y*=.84}const p=project(x,y,z,angle+orbit*.4);i?ctx.lineTo(p[0],p[1]):ctx.moveTo(p[0],p[1])}ctx.strokeStyle=`rgba(153,173,198,${orbit===0?.16:.095})`;ctx.lineWidth=.6;ctx.stroke();
  }
  for(const p of projected){const alpha=.14+(p[2]+1)*.24;ctx.fillStyle=`rgba(207,222,240,${alpha})`;ctx.beginPath();ctx.arc(p[0],p[1],(.65+(p[2]+1)*.38)*p[3],0,Math.PI*2);ctx.fill()}
  const c=project(0,0,0,angle);ctx.strokeStyle='rgba(199,215,235,.23)';ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(c[0]-11,c[1]);ctx.lineTo(c[0]+11,c[1]);ctx.moveTo(c[0],c[1]-11);ctx.lineTo(c[0],c[1]+11);ctx.stroke();
 }
 function running(){return desktop.matches&&!reduced.matches&&!paused&&visible&&!document.hidden}
 function loop(now){frame=0;if(!running()){draw();return}const dt=last?Math.min(now-last,45):16;last=now;tick+=dt;px+=(tx-px)*.06;py+=(ty-py)*.06;draw();frame=requestAnimationFrame(loop)}
 function sync(){toggle.hidden=!desktop.matches||reduced.matches;toggle.setAttribute('aria-pressed',String(paused));toggle.textContent=paused?'播放动画 ▷':'暂停动画 Ⅱ';if(frame&&!running()){cancelAnimationFrame(frame);frame=0;last=0;draw()}else if(!frame&&running()){last=0;frame=requestAnimationFrame(loop)}else draw()}
 hero.addEventListener('pointermove',e=>{if(reduced.matches)return;const r=hero.getBoundingClientRect();tx=Math.max(-8,Math.min(8,((e.clientX-r.left)/r.width-.5)*16));ty=Math.max(-8,Math.min(8,((e.clientY-r.top)/r.height-.5)*16))});
 hero.addEventListener('pointerleave',()=>{tx=0;ty=0});toggle.addEventListener('click',()=>{paused=!paused;sync()});
 document.addEventListener('visibilitychange',sync);reduced.addEventListener('change',sync);desktop.addEventListener('change',resize);
 if('IntersectionObserver'in window)new IntersectionObserver(entries=>{visible=entries[0].isIntersecting;sync()},{threshold:0}).observe(hero);
 if('ResizeObserver'in window)new ResizeObserver(resize).observe(hero);else window.addEventListener('resize',resize);
 resize();
})();
