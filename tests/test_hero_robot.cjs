const fs=require('fs'),vm=require('vm'),assert=require('assert');
const dir=__dirname+'/../assets';
class El {
 constructor(tag,attrs={}){this.tagName=tag.toUpperCase();this.tag=tag;this.a=attrs;this.children=[];this.handlers={};this.isConnected=true;this.dataset=new Proxy({}, {get:(_,k)=>this.a['data-'+k.replace(/[A-Z]/g,s=>'-'+s.toLowerCase())],set:(_,k,v)=>(this.a['data-'+k.replace(/[A-Z]/g,s=>'-'+s.toLowerCase())]=String(v),true),deleteProperty:(_,k)=>(delete this.a['data-'+k.replace(/[A-Z]/g,s=>'-'+s.toLowerCase())],true)});}
 get attributes(){return Object.entries(this.a).map(([name,value])=>({name,value}));}get id(){return this.a.id;}set id(v){this.a.id=v;}get className(){return this.a.class;}set className(v){this.a.class=v;}
 getAttribute(k){return this.a[k]??null;}setAttribute(k,v){this.a[k]=String(v);}append(...els){for(const e of els){this.children.push(e);e.parent=this;}}remove(){this.parent.children=this.parent.children.filter(n=>n!==this);}
 matches(s){if(s==='*')return true;if(s[0]==='.')return (this.a.class||'').split(' ').includes(s.slice(1));let m=s.match(/^\[([^=\]]+)(?:="([^"]*)")?\]$/);return m ? m[2]===undefined ? m[1] in this.a:this.a[m[1]]===m[2]:false;}
 querySelectorAll(s){return this.children.flatMap(e=>[...(e.matches(s)?[e]:[]),...e.querySelectorAll(s)]);}querySelector(s){return this.querySelectorAll(s)[0]||null;}
 addEventListener(k,f){this.handlers[k]=f;}removeEventListener(k){delete this.handlers[k];}
}
function parse(source){let root=new El('document'),stack=[root]; for(const tok of source.match(/<[^>]+>|[^<]+/g)){if(tok.startsWith('<!--')||tok.startsWith('<?'))continue;if(tok.startsWith('</')){stack.pop();continue;}if(tok.startsWith('<')){let m=tok.match(/^<([\w:-]+)/);if(!m)continue;let attrs={};for(const a of tok.matchAll(/([\w:-]+)="([^"]*)"/g))attrs[a[1]]=a[2];let el=new El(m[1],attrs);stack.at(-1).append(el);if(!tok.endsWith('/>'))stack.push(el);}else if(tok.trim())stack.at(-1).textContent=tok;}return root.children[0];}
function serialize(el){return '<'+el.tag+Object.entries(el.a).map(([k,v])=>' '+k+'="'+v.replaceAll('&','&amp;').replaceAll('"','&quot;')+'"').join(' ')+'>'+ (el.textContent||'')+el.children.map(serialize).join('')+'</'+el.tag+'>';}
let svg=parse(fs.readFileSync(dir+'/hero-robot.svg','utf8')),root=new El('figure',{'class':'robot-vignette'});root.append(svg);
let document=new El('document');document.readyState='complete';document.hidden=false;document.createElement=t=>new El(t);document.append(root);
let media={};function matchMedia(s){return media[s]??(media[s]={matches:false,addEventListener(k,f){this.change=f;},removeEventListener(){}});}
let raf=new Map(),next=1,observer;class IO{constructor(cb){this.cb=cb;observer=this;}observe(){}disconnect(){}}
let window={matchMedia,IntersectionObserver:IO};
let context={document,window,IntersectionObserver:IO,requestAnimationFrame:f=>{let id=next++;raf.set(id,f);return id;},cancelAnimationFrame:id=>raf.delete(id),console};
vm.runInNewContext(fs.readFileSync(dir+'/hero-robot.js','utf8'),context);
assert.equal(raf.size,0,'wait until visible');observer.cb([{isIntersecting:true}]);assert.equal(raf.size,1);
const tick=n=>{let callbacks=[...raf.values()];raf.clear();callbacks.forEach(f=>f(n));};
function lengths(){for(let leg of svg.querySelectorAll('[data-leg]')){let key=leg.dataset.leg;let expected={'back-far':[56,56],'front-far':[57,57],'back-near':[60,60],'front-near':[59,60]}[key];['upper','lower'].forEach((s,i)=>{let el=leg.querySelector('[data-bone="'+s+'"]'),a=el.a;assert.ok(Math.abs(Math.hypot(a.x2-a.x1,a.y2-a.y1)-expected[i])<.004,key+' '+s);});}for(let [name,len] of [['upper',91],['lower',105]]){let a=svg.querySelector('[data-arm="'+name+'"]').a;assert.ok(Math.abs(Math.hypot(a.x2-a.x1,a.y2-a.y1)-len)<.004,'arm '+name);}}
let snapshots={0:'start',1500:'approach',4000:'recognize',7500:'reach',11500:'retreat'};for(let n=0;n<=28000;n+=100){tick(n);lengths();}
const toggle=root.querySelector('.robot-vignette__toggle');toggle.handlers.click();assert.equal(raf.size,0);assert.equal(toggle.a['aria-pressed'],'true');const paused=serialize(svg);tick(29000);assert.equal(serialize(svg),paused);toggle.handlers.click();assert.equal(raf.size,1);
document.hidden=true;document.handlers.visibilitychange();assert.equal(raf.size,0);document.hidden=false;document.handlers.visibilitychange();assert.equal(raf.size,1);
observer.cb([{isIntersecting:false}]);assert.equal(raf.size,0);observer.cb([{isIntersecting:true}]);assert.equal(raf.size,1);
media['(max-width: 767px)'].matches=true;media['(max-width: 767px)'].change();assert.equal(raf.size,0);assert.equal(toggle.hidden,true);assert.equal(root.dataset.static,'true');lengths();
media['(max-width: 767px)'].matches=false;media['(max-width: 767px)'].change();assert.equal(raf.size,1);media['(prefers-reduced-motion: reduce)'].matches=true;media['(prefers-reduced-motion: reduce)'].change();assert.equal(raf.size,0);assert.equal(toggle.hidden,true);
window.RoboPaperAtlasRobot.init();assert.equal(root.querySelectorAll('.robot-vignette__toggle').length,1);
root.robotVignetteDestroy();assert.equal(raf.size,0);assert.equal(root.querySelectorAll('.robot-vignette__toggle').length,0);window.RoboPaperAtlasRobot.init();assert.ok(!svg.a['aria-labelledby'].includes('undefined'));assert.equal(root.querySelectorAll('.robot-vignette__toggle').length,1);
console.log('PASS: 2 full loops, limb lengths fixed, pause/play, visibility, offscreen, mobile, reduced motion, idempotent init and destroy/reinit. This is a DOM mock, not a real browser.');
