'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
const make=()=>{const f=fixture({htmlFile:'dist/index.html',url:'https://example.org/RoboPaperAtlas/'});f.$$('option').forEach(o=>o.value=o.getAttribute('value')||'');f.runAsset('app.js');return f};
test('topic activation exposes filtered result heading and gives keyboard focus',()=>{
 const f=make();f.click('[data-topic="navigation-space"]');
 assert.equal(f.$('#catalog-title').textContent,'导航与空间理解 · 29 篇论文');
 assert.equal(f.$('#catalog-results').scrolled,true);
 assert.equal(f.document.activeElement,f.$('#catalog-title'));
 assert.equal(f.$('#catalog-title').getAttribute('tabindex'),'-1');
 assert.match(f.location.search,/topic=navigation-space/);
 assert.equal(f.$('.library-features'),null);
 assert.equal(f.$('#clear-all-filters').hidden,false);
});
test('repeated topic switch and All update real counts without hiding records',()=>{
 const f=make();for(const [key,label,n]of [['motion-manipulation','运动与操作',46],['robot-learning','机器人学习',50],['navigation-space','导航与空间理解',29]]){
 f.click(`[data-topic="${key}"]`);assert.equal(f.$('#catalog-title').textContent,`${label} · ${n} 篇论文`);
 }
 f.click('[data-topic="all"]');assert.equal(f.$('#catalog-title').textContent,'全部论文 · 95 篇');assert.match(f.$('#result-count').textContent,/95/);assert.equal(f.$('#clear-all-filters').hidden,true);
});
test('history restoration updates the heading without triggering activation scroll',()=>{
 const f=make();f.$('#catalog-results').scrolled=false;
 f.setURL('https://example.org/RoboPaperAtlas/?topic=navigation-space');
 assert.equal(f.$('#catalog-title').textContent,'导航与空间理解 · 29 篇论文');
 assert.equal(f.$('#catalog-results').scrolled,false);
});

test('clear filters restores all results and keeps visible focus',()=>{
 const f=make();f.click('[data-topic="navigation-space"]');f.click('#clear-all-filters');
 assert.equal(f.$('#catalog-title').textContent,'全部论文 · 95 篇');
 assert.equal(f.$('#clear-all-filters').hidden,true);
 assert.equal(f.document.activeElement,f.$('#catalog-title'));
 assert.equal(f.location.search,'');
});
test('library keeps a single quick-view action and a direct title link for every canonical paper',()=>{
 const f=make();assert.equal(f.$('.library-galaxy-art'),null);assert.equal(f.$('.library-features'),null);
 assert.equal(f.$$('.library-paper').length,95);assert.equal(f.$$('[data-preview]').length,95);
 const titleLinks=f.$$('h3 > a[data-catalog-link]');assert.equal(titleLinks.length,95);
 assert(titleLinks.every(link=>link.closest('.library-paper')));
 assert.equal(new Set(f.$$('[data-preview]').map(button=>button.getAttribute('data-preview'))).size,95);
 assert(f.$('a[href="map/index.html"]'));
});
