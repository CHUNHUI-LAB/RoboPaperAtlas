'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
test('catalog uses all six shared facet memberships without mutating canonical categories',()=>{
 const f=fixture({htmlFile:'dist/index.html',url:'https://example.org/RoboPaperAtlas/index.html'});f.runAsset('app.js');
 const cards=f.$$('.paper-card'),before=cards.map(c=>[c.dataset.category,c.dataset.topics]);assert.equal(cards.length,95);
 for(const [topic,count]of[['navigation',26],['wbc',31],['vla',17],['methods',17],['sim-tools',8],['data-benchmarks',13]]){
  f.click(`[data-topic="${topic}"]`);assert.match(f.$('#result-count').textContent,new RegExp(`找到 ${count} 篇论文`));
  if(count>24)f.click('#load-more');assert.equal(cards.filter(c=>!c.hidden).length,count);
  cards.filter(c=>!c.hidden).forEach(c=>assert(c.dataset.topics.split(' ').includes(topic)));
 }
 assert.deepEqual(cards.map(c=>[c.dataset.category,c.dataset.topics]),before);assert.equal(cards.filter(c=>c.dataset.category==='foundations').length,31);
});
test('cross-tagged navigation method is reachable directly by either facet URL',()=>{
 for(const topic of ['navigation','methods']){
  const f=fixture({htmlFile:'dist/index.html',url:`https://example.org/RoboPaperAtlas/index.html?topic=${topic}#catalog`});f.runAsset('app.js');if(!f.$('#load-more').hidden)f.click('#load-more');
  const card=f.$$('.paper-card').find(c=>c.querySelector('h3').textContent.includes('Visual Language Maps'));assert(card&&!card.hidden);assert.equal(card.dataset.category,'foundations');
 }
});
