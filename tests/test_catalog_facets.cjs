'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
const counts={'navigation-space':29,'motion-manipulation':46,'robot-learning':48,'methods-resources':29};
const make=url=>{const f=fixture({htmlFile:'dist/index.html',url:url||'https://example.org/RoboPaperAtlas/index.html'});f.$$('option').forEach(o=>o.value=o.getAttribute('value')||'');f.runAsset('app.js');return f};
const select=(f,id,value)=>{f.$(id).value=value;f.$(id).emit('change')};
const visible=f=>f.$$('.paper-card').filter(c=>!c.hidden);
test('Library shows only All plus4Chinese browse groups; counts overlap without reassigning primaries',()=>{
 const f=make(),cards=f.$$('.paper-card'),before=cards.map(c=>[c.dataset.canonicalCategory,c.dataset.category,c.dataset.topics]);assert.equal(cards.length,95);assert.equal(f.$$('[data-topic]').length,5);
 for(const [topic,count]of Object.entries(counts)){f.click(`[data-topic="${topic}"]`);assert.match(f.$('#result-count').textContent,new RegExp(`找到 ${count} 篇论文`));f.click('#load-more');assert.equal(visible(f).length,count);visible(f).forEach(c=>assert(c.dataset.topics.split(' ').includes(topic)))}
 assert.deepEqual(cards.map(c=>[c.dataset.canonicalCategory,c.dataset.category,c.dataset.topics]),before);assert.equal(cards.filter(c=>c.dataset.canonicalCategory==='foundations').length,31);assert(cards.every(c=>c.dataset.topics));
});
test('legacy Mobile Manip. link still means19 exact papers and optional WBC method never reclassifies ODYSSEY',()=>{
 const f=make('https://example.org/RoboPaperAtlas/index.html?topic=mobile-manipulation#catalog');assert.equal(f.$('#direction-filter').value,'mobile-manipulation');assert.equal(visible(f).length,19);
 for(const term of ['ODYSSEY','UMI-on-Legs'])assert(visible(f).some(c=>c.querySelector('h3').textContent.includes(term)));
 select(f,'#method-filter','WBC');assert(visible(f).some(c=>c.querySelector('h3').textContent.includes('UMI-on-Legs')));visible(f).forEach(c=>{assert(c.dataset.methods.split('|').includes('WBC'));assert.equal(c.dataset.category,'mobile-manipulation')});assert(f.location.search.includes('direction=mobile-manipulation'));
});
test('common method chips expand names and toggle optional method filter',()=>{
 const f=make();assert.equal(f.$$('[data-method-chip]').length,6);const b=f.$('[data-method-chip="MPC"]');assert(b.textContent.includes('模型预测控制'));b.emit('click');assert.equal(f.$('#method-filter').value,'MPC');assert.equal(b.getAttribute('aria-pressed'),'true');visible(f).forEach(c=>assert(c.dataset.methods.split('|').includes('MPC')));b.emit('click');assert.equal(f.$('#method-filter').value,'all');
});
test('method and resources intersect independent groups/directions and survive Back/BFCache',()=>{
 const f=make();select(f,'#method-filter','VLA');assert.equal(visible(f).length,13);
 f.setURL('https://example.org/RoboPaperAtlas/index.html?topic=resources&resource=simulator&view=list#catalog');assert(visible(f).length>0);visible(f).forEach(c=>{assert.equal(c.dataset.category,'resources');assert(c.dataset.resources.split('|').includes('simulator'))});assert(f.$('#paper-grid').classList.contains('list-view'));f.window.emit('pageshow',{persisted:true});assert.equal(f.$('#resource-filter').value,'simulator');assert.equal(f.$('#direction-filter').value,'resources');
 f.setURL('https://example.org/RoboPaperAtlas/index.html?topic=motion-manipulation&method=WBC');assert.equal(f.$('#direction-filter').value,'all');visible(f).forEach(c=>assert(c.dataset.topics.includes('motion-manipulation')));
});
test('rapid multi-axis changes, empty results and reset preserve all95 searchable records',()=>{
 const f=make();for(let i=0;i<50;i++){f.click(`[data-topic="${Object.keys(counts)[i%4]}"]`);select(f,'#method-filter',i%2?'VLA':'all')}
 f.click('[data-topic="all"]');select(f,'#method-filter','all');select(f,'#direction-filter','cross-domain');select(f,'#resource-filter','simulator');assert(f.$('#empty-state').hidden===false);f.click('#reset-filters');for(const id of ['method','resource','direction'])assert.equal(f.$('#'+id+'-filter').value,'all');assert.equal(visible(f).length,24);assert.match(f.$('#result-count').textContent,/95/);
});
test('unknown values reset safely; individual chips clear only their own axis',()=>{
 const f=make('https://example.org/RoboPaperAtlas/index.html?topic=bad&direction=bad&method=bad&resource=bad');assert.equal(visible(f).length,24);select(f,'#method-filter','VLA');const chip=f.$('#active-filters').children.find(c=>c.textContent.includes('方法：'));chip.emit('click');assert.equal(f.$('#method-filter').value,'all');assert.match(f.$('#result-count').textContent,/95/);
});
