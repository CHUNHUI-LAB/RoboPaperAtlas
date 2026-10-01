'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {fixture}=require('./map_dom_fixture.cjs'),{hierarchyLayout,fitCamera}=require('../assets/paper-map.js');
const html=fs.readFileSync(require('node:path').join(__dirname,'../dist/map/index.html'),'utf8');
const data=JSON.parse(html.match(/<script type="application\/json" id="paper-map-data">(.*?)<\/script>/s)[1]);
const level=f=>f.$('#paper-map').dataset.level;
test('hierarchy positions remain deterministic under paper order and contain every unique ID',()=>{
 const a=hierarchyLayout(data.papers,data.categories,data.problems),b=hierarchyLayout(data.papers.slice().reverse(),data.categories,data.problems);
 assert.deepEqual(a,b);assert.equal(a.nodes.length,95);assert.equal(new Set(a.nodes.map(p=>p.id)).size,95);
 const centers=Object.values(a.systems).flatMap(p=>[{x:p.x-360,y:p.y-280},{x:p.x+360,y:p.y+280}]);
 for(const[w,h]of[[335,490],[970,690]]){const c=fitCamera(centers,w,h);for(const p of centers)assert(p.x*c.k+c.x>=0&&p.x*c.k+c.x<=w&&p.y*c.k+c.y>=0&&p.y*c.k+c.y<=h)}
});
test('galaxy to system to problem to paper preserves breadcrumbs and returns one level at a time',()=>{
 const f=fixture();assert.equal(level(f),'galaxy');f.click('[data-atlas-system="mobile-manipulation"]');f.step();assert.equal(level(f),'system');
 const problem=f.$$('.atlas-problem').find(x=>!x.hidden);problem.emit('click',{button:0});f.step();assert.equal(level(f),'problem');assert.equal(f.$('#atlas-breadcrumbs').children.length,3);
 const star=f.$$('.map-node').find(x=>!x.hidden);star.emit('click',{button:0});f.step();assert(f.$('#map-selected-title'));f.click('#atlas-back');assert.equal(f.$('#map-selected-title'),null);assert.equal(level(f),'problem');
 f.click('#atlas-back');f.step();assert.equal(level(f),'system');f.click('#atlas-back');f.step();assert.equal(level(f),'galaxy');assert.equal(f.raf.size,0);
});
test('browser history restores a drilled problem and newer navigation cancels old camera',()=>{
 const f=fixture();f.click('[data-atlas-system="navigation"]');const p=f.$$('.atlas-problem').find(x=>!x.hidden);p.emit('click',{button:0});const id=p.dataset.atlasProblem;
 f.click('[data-map-topic="resources"]');f.step();f.goBack();assert.equal(level(f),'problem');assert(f.location.search.includes(encodeURIComponent(id)));assert.equal(f.raf.size,0);
 f.click('[data-atlas-crumb="all"]');f.step();assert.equal(level(f),'galaxy');assert.equal(f.$('#map-selected-title'),null);
});
test('root canvas keyboard enters systems, never an arbitrary hidden paper',()=>{
 const f=fixture(),svg=f.$('#map-canvas');svg.focus();svg.emit('keydown',{key:'Enter'});assert.equal(f.$('#map-selected-title'),null);assert(f.document.activeElement.classList.contains('atlas-system'));assert.equal(f.raf.size,0);
 f.document.activeElement.emit('keydown',{key:'Enter'});assert.equal(level(f),'system');assert(f.document.activeElement.classList.contains('atlas-problem'));
 f.document.activeElement.emit('keydown',{key:'Enter'});assert.equal(level(f),'problem');assert(f.document.activeElement.classList.contains('map-node'));
 f.document.activeElement.emit('keydown',{key:'Escape'});assert.equal(level(f),'system');assert(f.document.activeElement.classList.contains('atlas-problem'));
});
test('all pending placements expose evidence and resources stay distinct from cross-domain research',()=>{
 const f=fixture();for(const p of data.papers.filter(p=>p.classification.needsReview)){
  f.setURL('?paper='+p.id);assert.match(f.$('.map-classification-evidence').textContent,/分类待复核/);assert.match(f.$('.map-classification-evidence').textContent,/证据范围：/);
 }
 f.setURL('?paper=holoagent-0');assert.match(f.$('#atlas-breadcrumbs').textContent,/跨领域研究/);assert(!f.$('#atlas-breadcrumbs').textContent.includes('跨领域资源'));
 f.setURL('?paper=savva2019habitat');assert.match(f.$('#atlas-breadcrumbs').textContent,/跨领域资源/);
});
test('search reaches all95 regardless of the current system and restores exact problem',()=>{
 const f=fixture({reduced:true});for(const p of data.papers){f.setURL('?topic=resources');f.input(p.title);f.$('#map-search').emit('keydown',{key:'Enter'});assert.equal(f.$('#map-selected-title')?.textContent,p.title);assert.equal(level(f),'problem');}
});
test('global URL search normalizes away a conflicting direction and problem',()=>{
 const f=fixture({url:'https://example.org/map/?topic=navigation&problem=navigation%2Fnav-goal&q=whole-body'});
 assert.equal(level(f),'search');assert(f.$$('.map-node').filter(n=>!n.hidden).length>0);assert.equal(f.$('[data-map-topic="all"]').getAttribute('aria-pressed'),'true');assert(!f.location.search.includes('topic='));
});
test('new navigation cancels captured paper click before pointer release',()=>{
 const f=fixture(),svg=f.$('#map-canvas');f.click('[data-map-topic="navigation"]');f.step();const star=f.$$('.map-node').find(n=>!n.hidden);
 svg.emit('pointerdown',{target:star,button:0,pointerType:'mouse',pointerId:4});assert.equal(svg.hasPointerCapture(4),true);
 f.click('[data-map-topic="resources"]');svg.emit('pointerup',{pointerId:4});f.step();assert.equal(f.$('#map-selected-title'),null);assert.equal(f.$('[data-map-topic="resources"]').getAttribute('aria-pressed'),'true');assert.equal(svg.hasPointerCapture(4),false);
});
test('Back and Forward retain connected visible focus after replacing a paper panel',()=>{
 const f=fixture();f.input('Deep Whole-Body Control');f.$('#map-search').emit('keydown',{key:'Enter'});f.click('[data-related-paper]');
 f.goBack();assert(f.document.activeElement.isConnected);assert(!f.document.activeElement.closest('[hidden]'));assert.equal(f.document.activeElement.id,'map-selected-title');
 f.goForward();assert(f.document.activeElement.isConnected);assert(!f.document.activeElement.closest('[hidden]'));assert.equal(f.document.activeElement.id,'map-selected-title');
});
test('list breadcrumbs and history keep focus on visible list controls',()=>{
 const f=fixture({mobile:true});f.click('[data-map-topic="navigation"]');const crumb=f.$('#atlas-breadcrumbs').children[0];crumb.focus();crumb.emit('click',{button:0});
 assert(f.document.activeElement.isConnected);assert(!f.document.activeElement.closest('[hidden]'));assert.equal(f.document.activeElement.tagName,'A');
 f.goBack();assert(f.document.activeElement.isConnected);assert(!f.document.activeElement.closest('[hidden]'));
});
test('pending classification notes meet readable contrast on both list and dark map panels',()=>{
 const css=fs.readFileSync(require('node:path').join(__dirname,'../assets/paper-map.css'),'utf8');
 const dark=css.match(/\.map-classification-pending\{color:(#[0-9a-f]{6})!important\}/i)?.[1];
 const light=css.match(/\.paper-map\[data-view=list\] \.map-classification-pending\{color:(#[0-9a-f]{6})!important\}/i)?.[1];
 const luminance=hex=>{const c=hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return c[0]*.2126+c[1]*.7152+c[2]*.0722};
 const contrast=(a,b)=>{const x=luminance(a),y=luminance(b);return(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
 assert(dark&&light);assert(contrast(dark,'#0c1017')>=4.5);assert(contrast(light,'#ffffff')>=4.5);
});

test('original inferred tags are explicitly separated from source-supported method components',()=>{
 const f=fixture({url:'https://example.org/map/?paper=rpa-0062'});
 assert.match(f.$('.map-original-tags-label').textContent,/原始编目标签/);
 assert.match(f.$('#map-panel-content').textContent,/不是已核验方法标签或引用关系/);
 const data=JSON.parse(f.$('#paper-map-data').textContent),p=data.papers.find(p=>p.id==='rpa-0062');
 assert(p.classification.methodTags.some(t=>t.evidence_scope==='formal paper sections 3.1–3.2'));
});
