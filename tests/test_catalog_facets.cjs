'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
const counts={'navigation':18,'mobile-manipulation':19,'wbc':20,'locomotion':2,'policy-learning':21,'spatial-representations':3,'general-ml':4,'resources':7,'cross-domain':1};
const make=url=>{const f=fixture({htmlFile:'dist/index.html',url:url||'https://example.org/RoboPaperAtlas/index.html'});f.$$('option').forEach(o=>o.value=o.getAttribute('value')||'');f.runAsset('app.js');return f};
const select=(f,id,value)=>{f.$(id).value=value;f.$(id).emit('change')};
const visible=f=>f.$$('.paper-card').filter(c=>!c.hidden);
test('Library uses exact reviewed primaries shared with Atlas; canonical attributes remain intact',()=>{
 const f=make(),cards=f.$$('.paper-card'),before=cards.map(c=>[c.dataset.canonicalCategory,c.dataset.topics]);assert.equal(cards.length,95);
 for(const [topic,count]of Object.entries(counts)){
  f.click(`[data-topic="${topic}"]`);assert.match(f.$('#result-count').textContent,new RegExp(`找到 ${count} 篇论文`));assert.equal(visible(f).length,count);
  visible(f).forEach(c=>assert.equal(c.dataset.topics,topic));
 }
 assert.deepEqual(cards.map(c=>[c.dataset.canonicalCategory,c.dataset.topics]),before);assert.equal(cards.filter(c=>c.dataset.canonicalCategory==='foundations').length,31);
});
test('ODYSSEY and UMI appear under Mobile Manip. rather than broad WBC; WBC remains a separate method',()=>{
 const f=make('https://example.org/RoboPaperAtlas/index.html?topic=mobile-manipulation#catalog');
 for(const term of ['ODYSSEY','UMI-on-Legs'])assert(visible(f).some(c=>c.querySelector('h3').textContent.includes(term)));
 select(f,'#method-filter','WBC');assert(visible(f).some(c=>c.querySelector('h3').textContent.includes('UMI-on-Legs')));visible(f).forEach(c=>assert(c.dataset.methods.split('|').includes('WBC')));
});
test('method and resource filters are independent, intersect primary and survive query restoration',()=>{
 const f=make();const expected=f.$$('.paper-card').filter(c=>c.dataset.methods.split('|').includes('VLA')).length;
 select(f,'#method-filter','VLA');assert.equal(visible(f).length,expected);assert(f.location.search.includes('method=VLA'));
 f.setURL('https://example.org/RoboPaperAtlas/index.html?topic=resources&resource=simulator&view=list#catalog');assert(visible(f).length>0);visible(f).forEach(c=>{assert.equal(c.dataset.topics,'resources');assert(c.dataset.resources.split('|').includes('simulator'))});assert(f.$('#paper-grid').classList.contains('list-view'));
 f.window.emit('pageshow',{persisted:true});assert.equal(f.$('#resource-filter').value,'simulator');
});
test('rapid topic/method changes, empty results and reset restore all axes',()=>{
 const f=make();for(let i=0;i<50;i++){f.click(`[data-topic="${Object.keys(counts)[i%9]}"]`);select(f,'#method-filter',i%2?'VLA':'all')}
 f.click('[data-topic="cross-domain"]');select(f,'#resource-filter','simulator');assert(f.$('#empty-state').hidden===false);
 f.click('#reset-filters');assert.equal(f.$('#method-filter').value,'all');assert.equal(f.$('#resource-filter').value,'all');assert.equal(visible(f).length,24);assert.match(f.$('#result-count').textContent,/95/);
});
test('unknown query values safely reset and method chips clear their own axis',()=>{
 const f=make('https://example.org/RoboPaperAtlas/index.html?topic=unrecognized&method=not-a-method&resource=other#catalog');assert.equal(visible(f).length,24);assert.equal(f.$('#method-filter').value,'all');
 select(f,'#method-filter','VLA');const chip=f.$('#active-filters').children.find(c=>c.textContent.includes('方法：'));assert(chip);chip.emit('click');assert.equal(f.$('#method-filter').value,'all');assert.match(f.$('#result-count').textContent,/95/);
});
