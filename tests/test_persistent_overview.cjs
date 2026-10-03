'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
const visible=(f,s)=>f.$$(s).filter(el=>!el.hidden);
function choose(f){f.click('[data-map-topic="navigation"]');f.step();}
function drill(f){choose(f);f.click('.map-drill-direction');f.step();}
test('topic selection retains all real constellations and applies one selected plaque beside filtered rows',()=>{
 const f=fixture({reduced:true});choose(f);assert.equal(f.$('#paper-map').dataset.level,'galaxy');assert.equal(visible(f,'.map-node').length,95);assert.equal(visible(f,'.atlas-system').length,9);assert.equal(visible(f,'[data-map-row]').length,18);
 const selected=f.$('[data-atlas-system="navigation"]');assert.equal(selected.getAttribute('aria-pressed'),'true');assert.equal(selected.querySelector('.atlas-selection-plate').style.display,'');assert.equal(f.$$('.atlas-selection-plate').filter(p=>p.style.display!=='none').length,1);assert.equal(f.$('.map-drill-direction').hidden,false);assert.equal(f.raf.size,0);
});
test('explicit problem exploration and browser history preserve distinct overview and drill states',()=>{
 const f=fixture({reduced:true});drill(f);assert.equal(f.$('#paper-map').dataset.level,'system');assert(f.location.search.includes('explore=1'));assert.equal(visible(f,'.atlas-system').length,0);assert.equal(visible(f,'.map-node').length,18);assert(visible(f,'.atlas-problem').length>0);
 f.goBack();assert.equal(f.$('#paper-map').dataset.level,'galaxy');assert.equal(visible(f,'.atlas-system').length,9);assert.equal(visible(f,'[data-map-row]').length,18);f.goForward();assert.equal(f.$('#paper-map').dataset.level,'system');
});
test('clearing search after drilling restores an operable all-directions overview',()=>{
 const f=fixture({reduced:true});drill(f);f.input('whole-body');f.click('#map-search-clear');assert.equal(f.$('#paper-map').dataset.level,'galaxy');assert.equal(visible(f,'.atlas-system').length,9);assert(!f.location.search.includes('explore=1'));
});
test('back from a research problem returns to its visible parent problem system',()=>{
 const f=fixture({reduced:true});drill(f);const problem=visible(f,'.atlas-problem')[0];problem.focus();problem.emit('click');assert.equal(f.$('#paper-map').dataset.level,'problem');f.click('#atlas-back');assert.equal(f.$('#paper-map').dataset.level,'system');assert.equal(f.document.activeElement,problem);assert.equal(problem.hidden,false);
});
test('topic-filtered overview keyboard navigation targets systems, never paper stars',()=>{
 const f=fixture({reduced:true});choose(f);assert(f.$$('.map-node').every(el=>el.getAttribute('tabindex')==='-1'));
 const svg=f.$('#map-canvas');svg.focus();svg.emit('keydown',{key:'ArrowDown'});assert(f.document.activeElement.dataset.atlasSystem);assert.equal(f.$('#paper-map').dataset.level,'galaxy');
});
test('invalid drill URL does not create an empty system-less galaxy',()=>{
 for(const query of ['?explore=1','?topic=bad&explore=1','?topic=navigation&problem=bad']){const f=fixture({url:'https://example.org/RoboPaperAtlas/map/'+query,reduced:true});assert.equal(visible(f,'.atlas-system').length,9,query);}
});
test('explicit drill can return through topic overview before clearing the direction',()=>{
 const f=fixture({reduced:true});drill(f);f.click('#atlas-back');assert.equal(f.$('#paper-map').dataset.level,'galaxy');assert.equal(visible(f,'.atlas-system').length,9);assert.equal(visible(f,'[data-map-row]').length,18);assert.equal(f.$('[data-atlas-system="navigation"]').getAttribute('aria-pressed'),'true');f.click('[data-map-reset]');assert.equal(visible(f,'[data-map-row]').length,95);assert(!f.$$('.atlas-system').some(el=>el.getAttribute('aria-pressed')==='true'));
});

test('mobile list drill back keeps focus in visible paper results',()=>{
 const f=fixture({mobile:true,reduced:true});
 assert.equal(f.$('#paper-map').dataset.view,'list');
 f.click('[data-map-topic="navigation"]');f.click('.map-drill-direction');
 assert.equal(f.$('#paper-map').dataset.level,'system');
 f.$('#atlas-back').focus();f.click('#atlas-back');
 assert.equal(f.$('#paper-map').dataset.level,'galaxy');
 assert.equal(f.document.activeElement.closest('.map-canvas-wrap'),null);
 assert(f.document.activeElement.closest('[data-map-row]'));
 assert.equal(f.document.activeElement.closest('[data-map-row]').hidden,false);
});
