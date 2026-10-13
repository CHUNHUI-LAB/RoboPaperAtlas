'use strict';
// Viewport and keyboard regressions for the bounded constellation canvas.
// These are non-rendering checks; browser screenshots cover the final layout.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const {fixture}=require('./map_dom_fixture.cjs');
function camera(f){const m=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/);return{x:+m[1],y:+m[2],k:+m[3]};}
function point(el){const m=el.getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);return{x:+m[1],y:+m[2]};}
function atDesktopWidth(width){const f=fixture({reduced:true});const canvas=f.$('.map-canvas-wrap');canvas.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,width,height:parseFloat(canvas.style.height)||660});f.resizers[0].cb();return f;}
test('all nine system centers and labels fit the bounded desktop canvas',()=>{
 const f=atDesktopWidth(500),c=camera(f),height=f.$('.map-canvas-wrap').getBoundingClientRect().height;
 for(const el of f.$$('.atlas-system')){const p=point(el),meta=el.querySelector('.atlas-navigation-meta');const bottom=c.y+(p.y+Number(meta.getAttribute('y')))*c.k;assert(bottom+16<=height,`${el.dataset.atlasSystem} label ends at ${bottom+16}, outside canvas ${height}`);assert(p.x*c.k+c.x>=0&&p.x*c.k+c.x<=500);}
 assert(height<=660);
});
test('fit restores the full galaxy after camera panning without an internal scroll dependency',()=>{
 const f=fixture({reduced:true}),svg=f.$('#map-canvas'),before=f.$('.map-world').getAttribute('transform');
 svg.emit('pointerdown',{button:0,pointerType:'mouse',pointerId:1,clientX:100,clientY:100});svg.emit('pointermove',{pointerId:1,clientX:200,clientY:180});svg.emit('pointerup',{pointerId:1});
 assert.notEqual(f.$('.map-world').getAttribute('transform'),before);f.click('[data-camera="fit"]');assert.equal(f.$('.map-world').getAttribute('transform'),before);
});
test('keyboard navigation brings a focused direction inside the camera viewport',()=>{
 const f=atDesktopWidth(500);let el=f.$$('.atlas-system')[0];el.focus();
 for(let i=0;i<8;i++){el.emit('keydown',{key:'ArrowDown'});el=f.document.activeElement;}
 const c=camera(f),p=point(el),x=c.x+p.x*c.k,y=c.y+p.y*c.k;
 assert(el!==f.$$('.atlas-system')[0]);assert(x>=0&&x<=500);assert(y>=27&&y<=660-60);
});
function assertDistinctMobileTargets(f){
 const c=camera(f),systems=f.$$('.atlas-system');
 for(let i=0;i<systems.length;i++)for(let j=i+1;j<systems.length;j++){
  const a=point(systems[i]),b=point(systems[j]);
  assert(Math.abs(a.x-b.x)*c.k>=54||Math.abs(a.y-b.y)*c.k>=54,`${systems[i].dataset.atlasSystem} and ${systems[j].dataset.atlasSystem} have overlapping 54px navigation targets`);
 }
}
test('optional mobile overview has independently reachable system targets',()=>{
 const f=fixture({mobile:true,reduced:true});f.click('[data-map-view="map"]');assertDistinctMobileTargets(f);
});
test('desktop-to-mobile media transition recomputes independently reachable system targets',()=>{
 const f=fixture({reduced:true});const canvas=f.$('.map-canvas-wrap');canvas.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,width:350,height:420});
 f.changeMedia('(max-width: 760px)',true);f.click('[data-map-view="map"]');assertDistinctMobileTargets(f);
});
test('animated back navigation keeps the restored distant system focus visible',()=>{
 const f=fixture();const canvas=f.$('.map-canvas-wrap');
 canvas.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,width:500,height:parseFloat(canvas.style.height)||660});f.resizers[0].cb();
 f.click('[data-atlas-system="cross-domain"]');f.step();f.click('.map-drill-direction');f.step();f.$('#atlas-back').focus();f.click('#atlas-back');f.step();
 const active=f.document.activeElement;assert.equal(active.dataset.atlasSystem,'cross-domain');const c=camera(f),p=point(active),y=c.y+p.y*c.k;
 assert(y-27>=0&&y+65<=660);assert.equal(f.raf.size,0);
});
test('title and search/navigation controls remain above both columns and visible in list mode',()=>{
 const f=fixture({mobile:true});assert(f.$('.map-heading'));assert.equal(f.$('.map-heading').closest('.map-explore'),null);
 for(const selector of ['.map-toolbar','.map-topics','.atlas-navigation'])assert.equal(f.$(selector).closest('.map-workspace'),null);
 assert(f.$('.map-results-heading').closest('.map-results-column'));
 assert.equal(f.$$('.map-search-wrap').length,1);assert.equal(f.$$('#map-search').length,1);
});
test('all nine real topic controls are unique and immediately available without a submenu',()=>{
 const f=fixture(),topics=f.$$('.map-topics')[0],buttons=topics.querySelectorAll('[data-map-topic]');
 assert.equal(f.$('.map-extra-directions'),null);assert.equal(buttons.length,10);assert.equal(new Set(buttons.map(b=>b.dataset.mapTopic)).size,10);
 for(const button of buttons){f.click(`[data-map-topic="${button.dataset.mapTopic}"]`);assert(f.$$('[data-map-row]').some(row=>!row.hidden));assert.equal(button.getAttribute('aria-pressed'),'true');}
});
test('desktop map owns sixty percent of the split area and removes the inherited scroller',()=>{
 const css=fs.readFileSync(require('node:path').join(__dirname,'../assets/paper-map.css'),'utf8');
 assert.match(css,/grid-template-columns:minmax\(0,3fr\) minmax\(0,2fr\)/);assert(!css.includes('overflow-y:auto'));assert(!css.includes('.f2-theme'));
});
