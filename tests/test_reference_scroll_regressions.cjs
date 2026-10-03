'use strict';
// Targeted non-rendering regressions for the new scrollable constellation.
// These deliberately expose blockers; they are not screenshot acceptance.
const {test}=require('node:test');
const assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
function camera(f){const m=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/);return{x:+m[1],y:+m[2],k:+m[3]};}
function point(el){const m=el.getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);return{x:+m[1],y:+m[2]};}
function atDesktopWidth(width){const f=fixture({reduced:true});const canvas=f.$('.map-canvas-wrap');canvas.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,width,height:parseFloat(canvas.style.height)||1600});f.resizers[0].cb();return f;}
test('scrollable desktop galaxy contains the last real system and its label at 500px column width',()=>{
 const f=atDesktopWidth(500),c=camera(f),height=f.$('.map-canvas-wrap').getBoundingClientRect().height;
 for(const el of f.$$('.atlas-system')){const p=point(el),meta=el.querySelector('.atlas-navigation-meta');const bottom=c.y+(p.y+Number(meta.getAttribute('y')))*c.k;assert(bottom+16<=height,`${el.dataset.atlasSystem} label ends at ${bottom+16}, outside canvas ${height}`);}
});
test('fit restores the beginning of a scrolled galaxy',()=>{
 const f=fixture({reduced:true}),scroll=f.$('.map-explore');scroll.scrollTop=650;f.click('[data-camera="fit"]');assert.equal(scroll.scrollTop,0);
});
test('global search resets an old inner scroll before framing the results',()=>{
 const f=fixture({reduced:true}),scroll=f.$('.map-explore');scroll.scrollTop=650;f.input('whole-body');assert.equal(scroll.scrollTop,0);
});
test('history restores a visible galaxy rather than retaining the later inner scroll',()=>{
 const f=fixture({reduced:true}),scroll=f.$('.map-explore');f.click('[data-map-topic="wbc"]');scroll.scrollTop=200;f.goBack();assert.equal(f.$('#paper-map').dataset.level,'galaxy');assert.equal(scroll.scrollTop,0);
});
test('keyboard navigation reveals the newly focused offscreen direction',()=>{
 const f=atDesktopWidth(500),scroll=f.$('.map-explore');scroll.scrollTop=0;let el=f.$$('.atlas-system')[0];el.focus();
 for(let i=0;i<8;i++){el.emit('keydown',{key:'ArrowDown'});el=f.document.activeElement;}
 assert(el!==f.$$('.atlas-system')[0]);
 assert(scroll.scrollTop>0||el.scrolled,'Offscreen direction received preventScroll focus without scrollIntoView or scroll offset update');
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
 const f=fixture();const canvas=f.$('.map-canvas-wrap'),scroll=f.$('.map-explore');scroll.clientHeight=600;
 canvas.getBoundingClientRect=()=>({x:0,y:0,left:0,top:0,width:500,height:parseFloat(canvas.style.height)||2000});f.resizers[0].cb();
 f.click('[data-atlas-system="cross-domain"]');f.step();f.click('.map-drill-direction');f.step();f.$('#atlas-back').focus();f.click('#atlas-back');f.step();
 const active=f.document.activeElement;assert.equal(active.dataset.atlasSystem,'cross-domain');const c=camera(f),p=point(active),y=c.y+p.y*c.k;
 assert(y-27>=scroll.scrollTop&&y+105<=scroll.scrollTop+scroll.clientHeight,`restored system y=${y} is outside visible scroll ${scroll.scrollTop}..${scroll.scrollTop+scroll.clientHeight}`);
});
test('C composition places introduction in the star column and controls beside results',()=>{
 const f=fixture();assert(f.$('.map-star-heading').closest('.map-explore'));
 for(const selector of ['.map-toolbar','.map-topics','.atlas-navigation','.map-results-heading'])assert(f.$(selector).closest('.map-results-column'),selector+' is outside the results column');
 assert.equal(f.$$('.map-search-wrap').length,1);assert.equal(f.$$('#map-search').length,1);
});
test('all nine real topic controls remain unique and five extras use native disclosure',()=>{
 const f=fixture(),topics=f.$$('.map-topics')[0],extra=f.$('.map-extra-directions'),buttons=topics.querySelectorAll('[data-map-topic]');
 assert.equal(extra.tagName,'DETAILS');assert(extra.querySelector('summary'));assert.equal(extra.querySelectorAll('[data-map-topic]').length,5);
 assert.equal(buttons.length,10);assert.equal(new Set(buttons.map(b=>b.dataset.mapTopic)).size,10);
 for(const button of extra.querySelectorAll('[data-map-topic]')){f.click(`[data-map-topic="${button.dataset.mapTopic}"]`);assert(f.$$('[data-map-row]').some(row=>!row.hidden));assert.equal(button.getAttribute('aria-pressed'),'true');}
});
