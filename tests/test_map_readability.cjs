'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const {fixture}=require('./map_dom_fixture.cjs');
const cameraScale=f=>Number(f.$('.map-world').getAttribute('transform').match(/scale\(([^)]+)\)/)[1]);
const screenSize=(f,el)=>parseFloat(el.style.fontSize)*cameraScale(f);
test('map labels stay readable in screen space after zooming',()=>{
 const f=fixture({reduced:true});
 for(const step of [null,'[data-camera="in"]','[data-camera="out"]']){
  if(step)f.click(step);
  assert(Math.abs(screenSize(f,f.$('.atlas-system').querySelector('.atlas-navigation-label'))-19)<.01);
  assert(Math.abs(screenSize(f,f.$('.atlas-navigation-meta'))-13)<.01);
  assert(Math.abs(screenSize(f,f.$('.map-node-label'))-14)<.01);
 }
});
test('known navigation labels use Chinese while canonical taxonomy remains intact',()=>{
 const f=fixture({reduced:true});
 assert.match(f.$('#atlas-breadcrumbs').textContent,/全部方向/);
 assert.match(f.$('[data-atlas-system="navigation"]').textContent,/具身导航/);
 assert.match(f.$('[data-atlas-system="navigation"]').getAttribute('aria-label'),/具身导航。探索研究问题/);
 f.click('[data-atlas-system="wbc"]');
 assert.match(f.$('#atlas-level-description').textContent,/选择研究问题/);
 const data=JSON.parse(f.$('#paper-map-data').textContent);
 assert.equal(data.categories.find(c=>c.id==='wbc').label,'Motion & Control');
 assert.equal(data.problems.find(p=>p.label==='Coordinated Motion').displayLabel,'协调运动');
});
test('full-width Chinese label is covered by its navigation hit target',()=>{
 const f=fixture({reduced:true}),group=f.$('[data-atlas-system="wbc"]');
 const label=group.querySelector('.atlas-navigation-label'),hit=group.querySelector('.atlas-navigation-hit');
 const actualWidth=Number(hit.getAttribute('width'))*cameraScale(f);
 assert(actualWidth>=label.textContent.length*19);
});
test('paper heading leads panel while evidence and publication routing remain available',()=>{
 const f=fixture({url:'https://example.org/RoboPaperAtlas/map/?paper=rpa-0012',reduced:true}),content=f.$('#map-panel-content');
 assert.equal(content.children[0].id,'map-selected-title');
 assert.match(content.textContent,/分类.*编辑判断/);
 assert.match(content.textContent,/正式书目已核验（独立补充）/);
 assert.match(content.textContent,/2023 · 正式出版年（独立核验）；2022 · 原始记录年/);
 assert(f.$$('.map-stage-report').length===3);
});
test('enlarged Chinese direction labels stay within modeled narrow desktop canvases',()=>{
 const f=fixture({reduced:true});
 for(const width of [400,500,726]){
  f.$('.map-canvas-wrap').getBoundingClientRect=()=>({width,height:690});
  f.resizers.forEach(o=>o.cb());
  const camera=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/),k=Number(camera[3]),tx=Number(camera[1]);
  for(const group of f.$$('.atlas-system')){
   const x=Number(group.getAttribute('transform').match(/translate\(([-\d.]+)/)[1]);
   const label=group.querySelector('.atlas-navigation-label');
   const center=x*k+tx+Number(label.getAttribute('x'))*k,half=label.textContent.length*19/2;
   assert(center-half>=7.9 && center+half<=width-7.9,`${width}: ${label.textContent}`);
  }
 }
});
