'use strict';
const assert=require('assert'),fs=require('fs'),vm=require('vm'),path=require('path');
const rootDir=path.join(__dirname,'..'),source=fs.readFileSync(rootDir+'/assets/hero-atlas.js','utf8');
const {makeStars,project}=require(rootDir+'/assets/hero-atlas.js');
assert.deepStrictEqual(makeStars(10),makeStars(10));assert.equal(makeStars().length,3710);
for(let t=0;t<600;t+=5)for(const s of makeStars(500)){const p=project(s,t);assert(Number.isFinite(p.x)&&Number.isFinite(p.y)&&p.radius>0);assert(p.x>15&&p.x<545&&p.y>5&&p.y<403,'projected bounds');assert(p.opacity>0&&p.opacity<=1);}
assert.equal(fs.readFileSync(rootDir+'/assets/hero-atlas.svg','utf8'),require(rootDir+'/scripts/render_atlas.cjs').render());
function fixture(noCanvas=false){
 const context2d={setTransform(){},clearRect(){this.paints=(this.paints||0)+1;},fillRect(){},createRadialGradient(){return{addColorStop(){}}},drawImage(){},beginPath(){},arc(){},fill(){}};
 const el=()=>({handlers:{},dataset:{},attributes:{},hidden:false,addEventListener(k,f){this.handlers[k]=f;},removeEventListener(k){delete this.handlers[k]},setAttribute(k,v){this.attributes[k]=v},classList:{add(){},remove(){}}});
 const toggle=el(),canvas={clientWidth:560,clientHeight:408,getContext:()=>noCanvas?null:context2d},root=el();root.isConnected=true;root.querySelector=s=>s==='canvas'?canvas:toggle;
 const document=el();document.readyState='complete';document.hidden=false;document.querySelectorAll=()=>[root];document.createElement=()=>({getContext:()=>context2d});
 const media={},raf=new Map();let next=0,observer;
 const window=el();window.devicePixelRatio=1;window.matchMedia=s=>media[s]||(media[s]={...el(),matches:false});
 class IO{constructor(cb){this.cb=cb;observer=this;}observe(){}disconnect(){this.disconnected=true;}}window.IntersectionObserver=IO;
 const c={document,window,IntersectionObserver:IO,requestAnimationFrame:f=>{raf.set(++next,f);return next;},cancelAnimationFrame:id=>raf.delete(id)};
 vm.runInNewContext(source,c);
 return {root,toggle,canvas,document,window,media,raf,observer,context2d,c,tick(n){const a=[...raf.values()];raf.clear();a.forEach(f=>f(n));}};
}
const a=fixture();assert.equal(a.raf.size,0);a.observer.cb([{isIntersecting:true}]);assert.equal(a.raf.size,1);
for(let n=0;n<1000;n+=16)a.tick(n);assert(a.context2d.paints>20&&a.context2d.paints<40,'paint capped about30fps');
a.toggle.handlers.click();assert.equal(a.raf.size,0);assert.equal(a.toggle.attributes['aria-pressed'],'true');
for(let i=0;i<50;i++){
 a.document.hidden=true;a.document.handlers.visibilitychange();a.document.hidden=false;a.document.handlers.visibilitychange();
 a.observer.cb([{isIntersecting:false}]);a.observer.cb([{isIntersecting:true}]);
 a.media['(max-width: 767px)'].matches=true;a.media['(max-width: 767px)'].handlers.change();
 a.media['(max-width: 767px)'].matches=false;a.media['(max-width: 767px)'].handlers.change();
 assert.equal(a.raf.size,0,'manual pause survives all transitions');
}
a.toggle.handlers.click();assert.equal(a.raf.size,1);
a.media['(prefers-reduced-motion: reduce)'].matches=true;a.media['(prefers-reduced-motion: reduce)'].handlers.change();assert.equal(a.raf.size,0);assert(a.toggle.hidden);
a.media['(prefers-reduced-motion: reduce)'].matches=false;a.media['(prefers-reduced-motion: reduce)'].handlers.change();assert.equal(a.raf.size,1);
for(let i=0;i<100;i++){a.toggle.handlers.click();assert.equal(a.raf.size,i%2?1:0);}
vm.runInNewContext(source,a.c);assert.equal(a.raf.size,1,'no duplicate initialization');
const callback=a.observer.cb,oldDestroy=a.root.atlasDestroy;a.root.atlasDestroy();assert.equal(a.raf.size,0);assert(a.toggle.hidden);const paints=a.context2d.paints;callback([{isIntersecting:true}]);assert.equal(a.raf.size,0);assert.equal(a.context2d.paints,paints,'queued callback does not redraw after teardown');
vm.runInNewContext(source,a.c);assert(a.root.dataset.atlasInitialized);assert.equal(a.raf.size,0);const newDestroy=a.root.atlasDestroy;oldDestroy();assert.equal(a.root.atlasDestroy,newDestroy);assert(a.root.dataset.atlasInitialized,'stale destroy cannot clear new instance');
const b=fixture(true);assert(!b.root.dataset.atlasInitialized);assert.equal(b.raf.size,0);
console.log('PASS Atlas: deterministic star math/fallback, bounds, ~30fps cap, repeated pause, hidden/offscreen/static lifecycle, reduced motion, duplicate init, teardown/reinit and no-Canvas fallback. DOM model; live rendering checked separately.');
