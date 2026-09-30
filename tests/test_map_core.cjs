'use strict';
const test = require('node:test'), assert = require('node:assert/strict');
const fs = require('node:fs'), path = require('node:path');
const core = require('../assets/paper-map.js');
const fixture = require('./fixtures/topics.json');
const source = process.env.ATLAS_SOURCE || path.join(__dirname, '..');
const catalog = JSON.parse(fs.readFileSync(path.join(source, 'data/catalog.json'), 'utf8'));
const papers = catalog.papers.map(p => ({...p, shortName:p.short_name, title:p.verified_overlay?.title || p.title, authors:Array.isArray(p.authors)?p.authors.join(', '):p.authors}));

test('all 95 papers get exactly one finite stable position', () => {
  const nodes = core.layout(papers);
  assert.equal(nodes.length, 95); assert.equal(new Set(nodes.map(p => p.id)).size, 95);
  nodes.forEach(p => assert.ok(Number.isFinite(p.x) && Number.isFinite(p.y)));
  assert.deepEqual(core.layout(papers.slice().reverse()), nodes);
});
test('layout keeps source category and tags unchanged', () => {
  const before = JSON.stringify(papers); const nodes = core.layout(papers);
  assert.equal(JSON.stringify(papers), before);
  nodes.forEach(n => {const p = papers.find(p => p.id === n.id);assert.equal(n.category,p.category);assert.deepEqual(n.tags,p.tags)});
});
test('layout has no node collisions within a category', () => {
  const nodes = core.layout(papers);
  for (let i=0;i<nodes.length;i++) for (let j=i+1;j<nodes.length;j++) if(nodes[i].category===nodes[j].category) assert.ok(Math.hypot(nodes[i].x-nodes[j].x,nodes[i].y-nodes[j].y)>39);
});
test('search normalizes case, unicode and multiple terms', () => {
  assert.equal(core.search(fixture, 'ＮＡＶＩＧＡＴＩＯＮ author').length, 2);
  assert.deepEqual(core.search(fixture, 'other control').map(p=>p.id),['fixture-c']);
  assert.equal(core.search(fixture,'no such paper').length,0);
  assert.equal(core.search(fixture,'').length,fixture.length);
});
test('relations contain only literal shared tags and are bounded', () => {
  const result=core.related(fixture,'fixture-a');
  assert.equal(result.mode,'shared-tags'); assert.equal(result.total,2);
  assert.deepEqual(result.items.map(p=>p.paper.id),['fixture-b','fixture-c']);
  assert.deepEqual(result.items[0].sharedTags,['navigation','shared']);
  assert.ok(core.related(papers,'rpa-0009').items.length<=8);
  for(const p of papers){const r=core.related(papers,p.id);assert.ok(r.items.length<=8);if(r.mode==='shared-tags')r.items.forEach(i=>assert.ok(i.sharedTags.length>0))}
});
test('missing tags use only category fallback, not invented theme edges', () => {
  const result=core.related(fixture,'fixture-e');
  assert.equal(result.mode,'category-only');assert.deepEqual(result.items.map(p=>p.paper.id),['fixture-f']);
  assert.deepEqual(result.items[0].sharedTags,[]);
  assert.equal(core.related(fixture,'missing').mode,'none');
});
test('fit includes all nodes at desktop and narrow dimensions',()=>{
  const nodes=core.layout(papers);
  for(const [w,h] of [[980,690],[530,660],[335,470]]){
    const camera=core.fitCamera(nodes,w,h);assert.ok(camera.k>=.08&&camera.k<=1.55);
    assert.ok(Number.isFinite(camera.x)&&Number.isFinite(camera.y));
    nodes.forEach(p=>{const x=p.x*camera.k+camera.x,y=p.y*camera.k+camera.y;assert.ok(x>=0&&x<=w);assert.ok(y>=0&&y<=h)});
  }
});
test('empty and single-node fit remain finite',()=>{
  for(const nodes of [[],core.layout(fixture).slice(0,1)])for(const [w,h]of[[330,470],[1,1]]){const c=core.fitCamera(nodes,w,h);assert.ok(Object.values(c).every(Number.isFinite))}
});
test('keyboard neighbor honors direction with no self loop',()=>{
  const nodes=core.layout(fixture),p=nodes[0];
  for(const [key,sign,axis] of [['ArrowRight',1,'x'],['ArrowLeft',-1,'x'],['ArrowUp',-1,'y'],['ArrowDown',1,'y']]){
    const n=core.nearest(nodes,p,key);if(n){assert.notEqual(n.id,p.id);assert.ok((n[axis]-p[axis])*sign>0)}
  }
});
test('implementation does not fetch or run model/API calls',()=>{
  const js=fs.readFileSync(path.join(__dirname,'../assets/paper-map.js'),'utf8');
  assert.ok(!/\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage|eval\s*\(|new Function/.test(js));
  assert.ok(js.includes("if (!event.ctrlKey && !event.metaKey) return"));
  assert.ok(js.includes('cancelAnimationFrame'));
  assert.ok(js.includes("prefers-reduced-motion: reduce"));
  assert.ok(js.includes('visibilitychange'));
});

test('region geometry is configurable without changing or guessing paper categories',()=>{
 const regions=core.regionsFor(['a','b','c','d','e','f']);assert.equal(Object.keys(regions).length,6);
 assert.deepEqual(core.regionsFor(),core.CENTERS);
 const records=[{id:'test-only',category:'f',title:'Geometry fixture',tags:[]}],before=JSON.stringify(records);
 const plotted=core.layout(records,regions);assert.equal(plotted.length,1);assert.equal(plotted[0].category,'f');assert.equal(JSON.stringify(records),before);
});

test('six-region full fit includes every paper at narrow optional-map width',()=>{
 const six=['navigation','wbc','vla','methods','sim-tools','data-benchmarks'];const regions=core.regionsFor(six);
 const records=Array.from({length:95},(_,i)=>({id:'fixture-'+String(i).padStart(3,'0'),category:six[i%6],tags:[]}));const nodes=core.layout(records,regions);
 for(const [w,h]of[[335,490],[970,720]]){const c=core.fitCamera(nodes,w,h);nodes.forEach(p=>{assert(p.x*c.k+c.x>=0&&p.x*c.k+c.x<=w);assert(p.y*c.k+c.y>=0&&p.y*c.k+c.y<=h)});}
});
