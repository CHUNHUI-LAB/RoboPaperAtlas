'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
function selected(f){return f.$('#map-selected-title')?.textContent||''}
function pick(f,query){f.input(query);f.$('#map-search').emit('keydown',{key:'Enter'});f.step();}

test('real map markup initializes all95nodes, stable camera, no initial relation edges',()=>{
 const f=fixture();assert.equal(f.$('#paper-map').dataset.view,'map');assert.equal(f.$$('.map-node').length,95);assert.equal(f.$('.map-toolbar').hidden,false);assert.equal(f.$('.map-edges').children.length,0);
 const transform=f.$('.map-world').getAttribute('transform');f.step(2000);assert.equal(f.$('.map-world').getAttribute('transform'),transform);assert.equal(f.raf.size,0);
});
test('search-to-selection uses actual PDF and Stage states, closes with no stale callback',()=>{
 const f=fixture();pick(f,'Deep Whole-Body Control');assert.match(selected(f),/Deep Whole-Body/);
 const links=f.$('.map-resource-links').children;assert(links.some(a=>a.href==='https://proceedings.mlr.press/v205/fu23a/fu23a.pdf'));
 assert(f.$('.map-stage-list').children.every(b=>b.disabled===true));assert(f.$('.map-edges').children.length<=8);
 f.click('#map-panel-close');f.step(1000);assert.equal(selected(f),'');assert.equal(f.raf.size,0);assert.equal(f.$('.map-edges').children.length,0);assert(!f.location.search.includes('paper='));
});
test('related-node selection and Back restore correct panel and URL',()=>{
 const f=fixture();pick(f,'Deep Whole-Body Control');const before=selected(f);f.click('[data-related-paper]');f.step();assert.notEqual(selected(f),before);f.goBack();assert.equal(selected(f),before);assert(f.location.search.includes('rpa-0012'));
});
test('category single-click counts, global search resets category, empty results recover',()=>{
 const f=fixture();for(const [topic,n]of[['navigation',16],['wbc',31],['vla',17],['foundations',31],['all',95]]){f.click(`[data-map-topic="${topic}"]`);f.step();assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,n)}
 f.click('[data-map-topic="wbc"]');pick(f,'HarnessVLN');assert.match(selected(f),/HarnessVLN/);assert.equal(f.$('[data-map-topic="all"]').getAttribute('aria-pressed'),'true');
 f.input('q_not_present');f.step();assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,0);assert.equal(f.$('.map-empty').hidden,false);f.click('[data-map-reset]');f.step();assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,95);
});
test('rapid selection-close-search and map-list switches leave no animations or stale panel',()=>{
 const f=fixture();for(let i=0;i<25;i++){f.input(i%2?'navigation':'whole-body');f.$('#map-search').emit('keydown',{key:'Enter'});f.click('#map-panel-close');f.click('[data-map-view="list"]');f.click('[data-map-view="map"]')}
 f.step(2000);assert.equal(selected(f),'');assert.equal(f.raf.size,0);assert.equal(f.$('#map-suggestions').hidden,true);assert.equal(f.$('.map-panel-selected').hidden,true);
});
test('camera cancels on hidden/offscreen/reduced motion and reflow',()=>{
 const f=fixture();f.click('[data-camera="in"]');assert.equal(f.raf.size,1);f.document.hidden=true;f.document.emit('visibilitychange');assert.equal(f.raf.size,0);f.document.hidden=false;f.document.emit('visibilitychange');
 f.click('[data-camera="in"]');assert.equal(f.raf.size,1);f.observers[0].cb([{isIntersecting:false}]);assert.equal(f.raf.size,0);f.observers[0].cb([{isIntersecting:true}]);
 f.click('[data-camera="in"]');f.changeMedia('(prefers-reduced-motion: reduce)',true);assert.equal(f.raf.size,0);f.click('[data-camera="in"]');assert.equal(f.raf.size,0);
 f.changeMedia('(prefers-reduced-motion: reduce)',false);f.click('[data-camera="in"]');f.resizers[0].cb();assert.equal(f.raf.size,0);
});
test('direct drag is synchronous and normal wheel is not intercepted',()=>{
 const f=fixture(),svg=f.$('#map-canvas');const before=f.$('.map-world').getAttribute('transform');
 svg.emit('pointerdown',{button:0,pointerType:'mouse',pointerId:1,clientX:100,clientY:100});svg.emit('pointermove',{pointerId:1,clientX:140,clientY:120});
 assert.notEqual(f.$('.map-world').getAttribute('transform'),before);assert.equal(f.raf.size,0);svg.emit('pointerup',{pointerId:1});
 const dragged=f.$('.map-world').getAttribute('transform');const wheel=svg.emit('wheel',{deltaY:100,clientX:200,clientY:200});assert(!wheel.defaultPrevented);assert.equal(f.$('.map-world').getAttribute('transform'),dragged);
 const zoom=svg.emit('wheel',{ctrlKey:true,deltaY:100,clientX:200,clientY:200});assert(zoom.defaultPrevented);assert.notEqual(f.$('.map-world').getAttribute('transform'),dragged);
});
test('keyboard search combobox, node arrows and Escape do not trap focus',()=>{
 const f=fixture();f.input('whole-body');const input=f.$('#map-search');input.emit('keydown',{key:'ArrowDown'});assert(input.getAttribute('aria-activedescendant'));input.emit('keydown',{key:'Enter'});assert.equal(f.document.activeElement.id,'map-selected-title');
 f.document.activeElement.emit('keydown',{key:'Escape'});assert.equal(selected(f),'');assert(f.document.activeElement.classList.contains('map-node'));
 const svg=f.$('#map-canvas');f.document.activeElement.emit('keydown',{key:'ArrowRight'});f.step();f.document.activeElement.emit('keydown',{key:'Enter'});assert(selected(f));assert.equal(f.document.activeElement.id,'map-selected-title');
});
test('mobile defaults to full list and can opt into map without changing records',()=>{
 const f=fixture({mobile:true});assert.equal(f.$('#paper-map').dataset.view,'list');assert.equal(f.$('.map-canvas-wrap').hidden,true);assert.equal(f.$$('.map-paper-list')[0].children.filter(c=>!c.hidden).length,95);
 f.click('[data-map-paper="rpa-0012"]');assert.match(selected(f),/Deep Whole-Body/);assert(f.$('.map-sidebar').scrolled);f.click('#map-panel-close');f.click('[data-map-view="map"]');assert.equal(f.$('.map-canvas-wrap').hidden,false);
 const camera=f.$('.map-world').getAttribute('transform');f.$('#map-canvas').emit('pointerdown',{pointerType:'touch',button:0,pointerId:2,clientX:100,clientY:100});f.$('#map-canvas').emit('pointermove',{pointerId:2,clientX:130,clientY:130});assert.equal(f.$('.map-world').getAttribute('transform'),camera);
});
test('unknown query params and cross-category links cannot leave an invisible selected node',()=>{
 const f=fixture({url:'https://example.org/RoboPaperAtlas/map/index.html?paper=rpa-0012&topic=navigation&q=not_present'});assert.match(selected(f),/Deep Whole-Body/);assert.equal(f.$('[data-map-topic="all"]').getAttribute('aria-pressed'),'true');assert.equal(f.$('#map-search').value,'');
 f.setURL('?paper=not_real&topic=bad&view=bad');assert.equal(selected(f),'');assert.equal(f.$('#paper-map').dataset.view,'map');assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,95);
});

test('empty search after selection cannot reuse stale suggestions; first Up selects last result',()=>{
 const f=fixture();pick(f,'whole-body');f.click('#map-panel-close');const input=f.$('#map-search');input.focus();input.emit('keydown',{key:'ArrowDown'});input.emit('keydown',{key:'ArrowUp'});input.emit('keydown',{key:'Enter'});assert.equal(selected(f),'');assert.equal(f.$('#map-suggestions').hidden,true);assert.equal(input.getAttribute('aria-activedescendant'),null);
 f.input('whole-body');const n=f.$('#map-suggestions').children.length;input.emit('keydown',{key:'ArrowUp'});assert.equal(input.getAttribute('aria-activedescendant'),`map-option-${n-1}`);input.emit('keydown',{key:'Escape'});input.emit('keydown',{key:'ArrowDown'});assert.equal(input.getAttribute('aria-activedescendant'),'map-option-0');
});
