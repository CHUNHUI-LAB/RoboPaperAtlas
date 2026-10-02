'use strict';
// DOM-model regressions for the exact script packaged in the new report.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const html = fs.readFileSync(__dirname + '/../artifacts/rpa-0052/v1/method-code-reading.html', 'utf8');
const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length, 1);
let focused, document;
function el() { return {
  events: {}, attrs: {}, disabled: false, hidden: false, textContent: '',
  classList: { values: new Set(), add(v){this.values.add(v)}, remove(v){this.values.delete(v)}, contains(v){return this.values.has(v)}, toggle(v, on){on ??= !this.values.has(v);on ? this.values.add(v) : this.values.delete(v);return on} },
  addEventListener(name, fn){this.events[name] = fn}, emit(name, e = {}){return this.events[name]?.(e)},
  setAttribute(k,v){this.attrs[k]=v}, removeAttribute(k){delete this.attrs[k]},
  contains(v){return this === v}, focus(options){focused=this;document.activeElement=this;this.focusOptions=options}
}; }
const previous=el(), next=el(), position=el(), label=el(), toggle=el(), toast=el();
const sections=Array.from({length:8},(_,i)=>({...el(),id:'section-'+i,top:156+i*700,getBoundingClientRect(){return {top:this.top}},scrollIntoView(opts){this.scrollOptions=opts}}));
const links=sections.map((s,i)=>({...el(),hash:'#'+s.id,textContent:'Section '+i,offsetTop:i*40}));
const toc={...el(),clientHeight:160,querySelectorAll:()=>links,querySelector:()=>links.find(x=>x.classList.contains('is-current')),contains:x=>links.includes(x)};
const header={getBoundingClientRect:()=>({height:68})},bar={getBoundingClientRect:()=>({height:60})};
const copies=[el(),el()],focusCode=[el(),el()],pending=[];
const holders=copies.map((b,i)=>({...el(),querySelectorAll:()=>[{textContent:'    def f():'},{textContent:'        return 1'}],querySelector:q=>q==='pre'?{clientHeight:300,scrollTo(o){holders[i].scrollOptions=o}}:{offsetTop:230}}));copies.forEach((b,i)=>{b.closest=()=>holders[i];b.isConnected=true});focusCode.forEach((b,i)=>b.closest=()=>holders[i]);
const navigator={clipboard:{writeText(text){return new Promise((resolve,reject)=>pending.push({text,resolve,reject}))}}};
const page={querySelector:s=>({'.reader-toc':toc,'.reader-toc-toggle':toggle,'.reader-position':position,'[data-reader-previous]':previous,'[data-reader-next]':next,'[data-reader-section-label]':label,'.reader-stagebar':bar})[s] || null,querySelectorAll:s=>s==='.reader-article>section[id]'?sections:s==='[data-copy-code]'?copies:s==='[data-code-focus]'?focusCode:[]};
const css={};document={...el(),hidden:false,documentElement:{scrollHeight:10000,style:{setProperty(k,v){css[k]=v}}},querySelector:s=>s==='.reader-page'?page:s==='.reader-toast'?toast:s==='.atlas-site-header'?header:null};
const window={...el(),scrollY:0,innerHeight:800};let mobile=false,reduced=false;const mediaEvents={},frames=new Map();let seq=0;
const history=[];const context={document,window,console,navigator,history:{pushState(a,b,hash){history.push(hash)}},matchMedia:q=>({get matches(){return q.includes('reduce')?reduced:mobile},addEventListener(event,fn){mediaEvents[q]=fn}}),getComputedStyle:node=>node===document.documentElement?{scrollPaddingTop:'144px'}:{scrollMarginTop:'12px'},requestAnimationFrame:fn=>{frames.set(++seq,fn);return seq},cancelAnimationFrame:id=>frames.delete(id),setTimeout:()=>++seq,clearTimeout:()=>{}};
vm.runInNewContext(scripts[0][1],context);
function flush(){const pending=[...frames.values()];frames.clear();pending.forEach(fn=>fn())}
function land(index){sections.forEach((s,i)=>s.top=156+(i-index)*700)}
assert.equal(position.textContent,'01 / 08');assert(previous.disabled);assert.equal(css['--reader-anchor-offset'],'144px');
next.emit('click');next.emit('click');previous.emit('click');
assert.equal(position.textContent,'02 / 08');assert.equal(focused,sections[1]);assert.equal(focused.focusOptions.preventScroll,true);
window.emit('scrollend');flush();assert.equal(position.textContent,'02 / 08','stale completion does not settle newer navigation');
land(1);window.emit('scroll');flush();assert.equal(position.textContent,'02 / 08');
links[5].emit('click',{preventDefault(){},button:0});assert.equal(history.at(-1),'#section-5');assert.equal(position.textContent,'06 / 08');assert.equal(focused,sections[5]);
mobile=true;mediaEvents['(max-width:767px)']();assert(toc.inert);
toggle.emit('click');assert.equal(toggle.attrs['aria-expanded'],'true');assert.equal(focused,links[5]);assert(!toc.inert);
document.emit('keydown',{key:'Escape',preventDefault(){}});assert.equal(toggle.attrs['aria-expanded'],'false');assert.equal(focused,toggle);assert(toc.inert);
toggle.emit('click');document.emit('focusin',{target:next});assert.equal(toggle.attrs['aria-expanded'],'false');
land(2);window.emit('wheel');flush();assert.equal(position.textContent,'03 / 08','manual intent interrupts programmatic section');
next.emit('click');land(1);window.emit('hashchange');flush();assert.equal(position.textContent,'02 / 08','history navigation recalculates section state');
land(5);window.emit('hashchange');flush();assert.equal(position.textContent,'06 / 08');
reduced=true;next.emit('click');assert.equal(sections[6].scrollOptions.behavior,'auto');
window.emit('scroll');document.hidden=true;document.emit('visibilitychange');assert.equal(frames.size,0);
document.hidden=false;document.emit('visibilitychange');assert.equal(frames.size,1);flush();
land(7);window.scrollY=9200;window.emit('wheel');flush();assert.equal(position.textContent,'08 / 08');assert(next.disabled);
console.log('PASS RoboDuet candidate inherited Atlas script: repeated/interrupted navigation, stale scrollend, TOC history, mobile focus/Escape, reduced motion, hidden state and end boundary (DOM model)');

(async()=>{
 const a=copies[0].emit('click'),b=copies[0].emit('click');assert.equal(pending[0].text,'    def f():\n        return 1');
 pending[1].resolve();await b;assert(toast.textContent.includes('已复制'));pending[0].reject();await a;assert(toast.textContent.includes('已复制'));
 const denied=copies[1].emit('click');pending[2].reject();await denied;assert(toast.textContent.includes('手动选择复制'));
 focusCode[0].emit('click');assert.equal(focusCode[0].attrs['aria-pressed'],'true');assert.equal(holders[0].scrollOptions.behavior,'auto');
 focusCode[0].emit('click');assert.equal(focusCode[0].attrs['aria-pressed'],'false');
 console.log('PASS exact report script: indentation-preserving copy, permission failure fallback, stale completion and reduced-motion code focus (DOM model)');
})().catch(e=>{console.error(e);process.exitCode=1});
