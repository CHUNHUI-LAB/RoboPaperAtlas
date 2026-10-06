'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const code=fs.readFileSync(__dirname+'/../assets/reader-toc-focus-v1.js','utf8');
const manifest=require('../candidates/navigation-stage1-v2-pending.json');
const handlers=manifest.reports.map(r=>{
 const html=r.parts.map(p=>fs.readFileSync(`${__dirname}/../data/report-parts/${r.paper_id}/v2/stage1/${p.file}`,'utf8')).join('');
 return html.match(/tocButton\.addEventListener\('click',.*?\);(?=\n)/)[0];
});
assert.equal(new Set(handlers).size,1,'all three exact frozen reports share the measured faulty open handler');
function fixture({height=378,boxTop=239.59375,clientHeight=207,linkY=54.09375,scroll=0}={}){
 const captures=[],bubbles=[],resizes=[],observers=[],scrollListeners=[];let expanded=false;let open=false,scrollTop=scroll;const naturalHeight=clientHeight;const style={maxHeight:''};
 const doc={documentElement:{clientHeight:height},activeElement:null};
 const toc={style,addEventListener(event,fn){if(event==='scroll')scrollListeners.push(fn)},clientTop:0,get clientHeight(){return style.maxHeight?Math.min(naturalHeight,parseFloat(style.maxHeight)):naturalHeight},classList:{contains:()=>open,toggle:(_,value)=>{open=value}},contains:x=>x===link,getBoundingClientRect:()=>({top:boxTop,height:toc.clientHeight}),get scrollTop(){return open?scrollTop:0},set scrollTop(v){scrollTop=Math.max(0,Math.min(598-toc.clientHeight,v))}};
 toc.querySelector=()=>link;
 const link={offsetTop:Math.round(boxTop+linkY),focus(options){assert.equal(options.preventScroll,true);doc.activeElement=this},getBoundingClientRect:()=>({top:boxTop+linkY-scrollTop,bottom:boxTop+linkY-scrollTop+44})};
 const button={setAttribute(key,value){if(key==='aria-expanded')expanded=value==='true'},getAttribute:()=>String(expanded),addEventListener:(event,fn,capture)=>{assert.equal(event,'click');(capture?captures:bubbles).push(fn)}};
 doc.querySelector=s=>s==='.reader-toc'?toc:button;
 // Run the unchanged listener extracted from all three frozen source reports.
 const ctx={MutationObserver:class{constructor(fn){observers.push(fn)}observe(){}},window:{addEventListener:(event,fn)=>{assert.equal(event,'resize');resizes.push(fn)}},document:doc,toc,tocButton:button,tocLinks:[link],compact:{matches:true}};
 vm.runInNewContext(handlers[0],ctx);vm.runInNewContext(code,ctx);
 return {toc,doc,link,setScroll(value){toc.scrollTop=value;scrollListeners.forEach(f=>f())},legacyClick(){bubbles[0]()},closeThroughOriginalRuntime(){open=false;button.setAttribute('aria-expanded','false');observers.forEach(f=>f())},resize(newHeight){doc.documentElement.clientHeight=newHeight;resizes.forEach(f=>f())},click(){captures.forEach(f=>f());bubbles.forEach(f=>f())},visible(){const r=link.getBoundingClientRect();return r.top>=Math.max(boxTop,0)+6-0.001&&r.bottom<=Math.min(boxTop+toc.clientHeight,doc.documentElement.clientHeight)-6+0.001}};
}
test('unchanged legacy handler reproduces measured first-link clipping',()=>{const f=fixture();f.legacyClick();assert.equal(f.toc.scrollTop,190.5);assert.equal(f.link.getBoundingClientRect().top,103.1875);assert(!f.visible())});
test('200% observed offset-parent regression: first focus remains visible without page scroll',()=>{const f=fixture();f.click();assert(f.visible());assert.equal(f.toc.scrollTop,0);assert.equal(f.doc.activeElement,f.link)});
test('200% later current section reveals fully within viewport intersection, not just TOC box',()=>{const f=fixture({linkY:450});f.click();assert(f.visible());assert(f.toc.scrollTop>0)});
test('last section stays reachable when panel would extend below viewport',()=>{const f=fixture({linkY:544});f.click();assert(f.visible());assert(f.toc.clientHeight<207)});
test('resize recomputes height and closed/desktop resize removes the temporary cap',()=>{const f=fixture();f.click();assert(f.toc.style.maxHeight);f.resize(756);assert.equal(f.toc.style.maxHeight,'');f.resize(378);assert(f.toc.style.maxHeight);f.click();assert.equal(f.toc.style.maxHeight,'')});
test('Escape/link/focus-out close restores inline presentation via aria-expanded',()=>{for(const source of ['Escape','link','focus-out']){const f=fixture();f.click();assert(f.toc.style.maxHeight,source);f.closeThroughOriginalRuntime();assert.equal(f.toc.style.maxHeight,'',source)}});
test('already-visible previous TOC scroll is preserved across close/reopen',()=>{const f=fixture({linkY:250});f.click();f.setScroll(190);assert(f.visible());assert.equal(f.toc.scrollTop,190);f.click();assert.equal(f.toc.scrollTop,0,'display:none has no box');f.click();assert(f.visible());assert.equal(f.toc.scrollTop,190)});
test('Escape/link/focus-out closure preserves last visible scroll despite hidden getter zero',()=>{const f=fixture({linkY:250});f.click();f.setScroll(190);f.closeThroughOriginalRuntime();assert.equal(f.toc.scrollTop,0);f.click();assert(f.visible());assert.equal(f.toc.scrollTop,190)});
test('stale deep scroll adjusts only enough to expose earlier current section',()=>{const f=fixture();f.click();f.setScroll(190);f.click();f.click();assert(f.visible());assert(f.toc.scrollTop>0);assert(f.toc.scrollTop<190)});
test('100% tall layout also retains visible context',()=>{const f=fixture({height:756,boxTop:164,clientHeight:500,linkY:200});f.click();f.setScroll(50);f.click();f.click();assert(f.visible());assert.equal(f.toc.scrollTop,50)});
test('fully offscreen programmatic activation is bounded and does not claim visible focus',()=>{const f=fixture({boxTop:-400});f.click();assert(!f.visible());assert.equal(f.toc.scrollTop,0)});
test('layer does not intercept keyboard, focus, section navigation, history, or global scroll',()=>{assert(!/preventDefault|stopPropagation|stopImmediatePropagation|scrollIntoView|history\.|\.focus\(/.test(code.replace(/\/\/[^\n]*/g,'')));});
