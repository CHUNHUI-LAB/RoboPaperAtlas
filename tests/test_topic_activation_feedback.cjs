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
 const f=make();for(const [key,label,n]of [['motion-manipulation','运动与操作',46],['robot-learning','机器人学习',48],['navigation-space','导航与空间理解',29]]){
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
test('editorial page separates map and keeps every canonical paper accessible',()=>{
 const f=make();assert.equal(f.$('.library-galaxy-art'),null);assert.equal(f.$('.library-features'),null);
 assert.equal(f.$$('.paper-summary').length,95);assert.equal(f.$$('.paper-open').length,95);
 assert(f.$('a[href="map/index.html"]'));
});
