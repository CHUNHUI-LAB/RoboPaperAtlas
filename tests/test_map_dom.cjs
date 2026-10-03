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
 assert.deepEqual(f.$('.map-stage-list').children.map(a=>a.href),[1,2,3].map(n=>`../papers/rpa-0012/reading/stage${n}.html`));assert(f.$('.map-edges').children.length<=8);
 f.click('#map-panel-close');f.step(1000);assert.equal(selected(f),'');assert.equal(f.raf.size,0);assert.equal(f.$('.map-edges').children.length,0);assert(!f.location.search.includes('paper='));
});
test('related-node selection and Back restore correct panel and URL',()=>{
 const f=fixture();pick(f,'Deep Whole-Body Control');const before=selected(f);f.click('[data-related-paper]');f.step();assert.notEqual(selected(f),before);f.goBack();assert.equal(selected(f),before);assert(f.location.search.includes('rpa-0012'));
});
test('category single-click counts, global search resets category, empty results recover',()=>{
 const f=fixture();for(const [topic,n]of[['navigation',18],['wbc',20],['mobile-manipulation',19],['policy-learning',21],['spatial-representations',3],['locomotion',2],['general-ml',4],['resources',7],['cross-domain',1],['all',95]]){f.click(`[data-map-topic="${topic}"]`);f.step();assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,95);assert.equal(f.$$('[data-map-row]').filter(row=>!row.hidden).length,n)}
 f.click('[data-map-topic="wbc"]');pick(f,'HarnessVLN');assert.match(selected(f),/HarnessVLN/);assert.equal(f.$('[data-map-topic="navigation"]').getAttribute('aria-pressed'),'true');
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
 const f=fixture({url:'https://example.org/RoboPaperAtlas/map/index.html?paper=rpa-0012&topic=navigation&q=not_present'});assert.match(selected(f),/Deep Whole-Body/);assert.equal(f.$('[data-map-topic="wbc"]').getAttribute('aria-pressed'),'true');assert.equal(f.$('#map-search').value,'');
 f.setURL('?paper=not_real&topic=bad&view=bad');assert.equal(selected(f),'');assert.equal(f.$('#paper-map').dataset.view,'map');assert.equal(f.$$('.map-node').filter(n=>!n.hidden).length,95);
});

test('empty search after selection cannot reuse stale suggestions; first Up selects last result',()=>{
 const f=fixture();pick(f,'whole-body');f.click('#map-panel-close');const input=f.$('#map-search');input.focus();input.emit('keydown',{key:'ArrowDown'});input.emit('keydown',{key:'ArrowUp'});input.emit('keydown',{key:'Enter'});assert.equal(selected(f),'');assert.equal(f.$('#map-suggestions').hidden,true);assert.equal(input.getAttribute('aria-activedescendant'),null);
 f.input('whole-body');const n=f.$('#map-suggestions').children.length;input.emit('keydown',{key:'ArrowUp'});assert.equal(input.getAttribute('aria-activedescendant'),`map-option-${n-1}`);input.emit('keydown',{key:'Escape'});input.emit('keydown',{key:'ArrowDown'});assert.equal(input.getAttribute('aria-activedescendant'),'map-option-0');
});

test('UMI reports route to current mixed-version readers and unimported papers stay disabled',()=>{
 const f=fixture();pick(f,'UMI-on-Legs');assert.match(selected(f),/UMI-on-Legs/);const rows=f.$('.map-stage-list').children;
 assert.equal(rows.length,3);assert(rows.every(a=>a.tagName==='A'));assert.deepEqual(rows.map(a=>a.href),['../papers/rpa-0062/reading/stage1.html','../papers/rpa-0062/reading/stage2.html','../papers/rpa-0062/reading/stage3.html']);
 pick(f,'Universal Manipulation Interface: In-The-Wild');assert(f.$('.map-stage-list').children.every(b=>b.disabled===true));
});

test('galaxy has95real paper stars and9distinct labeled navigation systems',()=>{
 const f=fixture();assert.equal(f.$$('.map-node').length,95);assert.equal(f.$$('.map-node-aura').length,95);assert.equal(f.$$('.map-node-dot').length,95);assert.equal(f.$$('.atlas-system').length,9);
 for(const text of ['具身导航','全身运动规划与控制','移动操作','策略学习','跨领域资源','跨领域研究'])assert(f.$$('.atlas-navigation-label').some(el=>el.textContent===text));
 assert.equal(f.$('#map-dot-grid'),null);assert.equal(f.$('.map-edges').children.length,0);
});
test('invisible star targets stay44px across zoom while paper marks stay equal-sized',()=>{
 const f=fixture();for(let i=0;i<8;i++){
  f.click(i%2?'[data-camera="out"]':'[data-camera="in"]');f.step();
  const transform=f.$('.map-world').getAttribute('transform');const k=Number(transform.match(/scale\(([^)]+)/)[1]);
  assert(f.$$('.map-node-hit').every(el=>Math.abs(Number(el.getAttribute('r'))*k*2-44)<.002));
  const radii=f.$$('.map-node-dot').map(el=>Number(el.getAttribute('r')));assert(radii.every(r=>r===radii[0]));
 }
});
test('overlapping44px targets select nearest actual star, independent of SVG paint order',()=>{
 const f=fixture(),svg=f.$('#map-canvas');f.click('[data-map-topic="wbc"]');f.step();f.click('.map-drill-direction');f.step();const world=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/);
 const node=f.$('[data-paper-id="rpa-0012"]'),point=node.getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);
 const clientX=Number(world[1])+Number(point[1])*Number(world[3]),clientY=Number(world[2])+Number(point[2])*Number(world[3]);
 // The simulated SVG hit target is intentionally the wrong star, as can occur with overlapping hit circles.
 const wrong=f.$('[data-paper-id="rpa-0001"]');svg.emit('pointerdown',{target:wrong,button:0,pointerType:'mouse',pointerId:7,clientX,clientY});svg.emit('pointerup',{pointerId:7});f.step();
 assert.match(selected(f),/Deep Whole-Body/);
});

test('closing or replacing selection restores equal default star sizes immediately',()=>{
 const f=fixture();pick(f,'Deep Whole-Body Control');f.click('#map-panel-close');
 const radii=f.$$('.map-node-dot').map(el=>Number(el.getAttribute('r')));assert(radii.every(r=>r===radii[0]));
 pick(f,'whole-body');f.input('navigation');const next=f.$$('.map-node-dot').map(el=>Number(el.getAttribute('r')));assert(next.every(r=>r===next[0]));
});

test('overlapping hit targets refresh nearest-star tooltip on pointermove and clear in empty space',()=>{
 const f=fixture(),svg=f.$('#map-canvas');f.click('[data-map-topic="navigation"]');f.step();f.click('.map-drill-direction');f.step();f.click('[data-camera="out"]');f.step();
 const world=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/);
 const point=id=>{const el=f.$(`[data-paper-id="${id}"]`),p=el.getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);return{clientX:Number(world[1])+Number(p[1])*Number(world[3]),clientY:Number(world[2])+Number(p[2])*Number(world[3])}};
 const oldTarget=f.$('[data-paper-id="agenticnav-tool-harness"]');oldTarget.emit('pointerover',{pointerType:'mouse',...point('agenticnav-tool-harness')});assert.match(f.$('.map-hover-card').textContent,/AgenticNav/);
 svg.emit('pointermove',{target:oldTarget,pointerType:'mouse',...point('harnessvln')});assert.match(f.$('.map-hover-card').textContent,/HarnessVLN/);
 svg.emit('pointermove',{target:oldTarget,pointerType:'mouse',clientX:-2000,clientY:-2000});assert.equal(f.$('.map-hover-card').hidden,true);
});


test('Deep WBC panel distinguishes verified formal year and scopes old bibliography notes',()=>{
 const f=fixture();pick(f,'Deep Whole-Body Control');
 const panel=f.$('#map-panel-content').textContent;
 assert(panel.includes('2023 · 正式出版年（独立核验）；2022 · 原始记录年'));
 assert(panel.includes('正式书目已核验（独立补充）'));
 assert(panel.includes('以下是 2026-09-30 的书目／链接核验记录；后续阅读范围见各阶段报告。'));
 assert(panel.includes('本次为书目与链接核验，未完成全文检查'));
 assert(panel.includes('未运行代码或独立复现'));
 for(const old of ['Author-linked','Source-supported classification','Classification sources','Primary source'])assert(!panel.includes(old));
 assert.equal(f.$('.map-stage-list').children.length,3);
 assert(f.$('.map-stage-list').children.every(a=>a.tagName==='A'));
});

function screenStar(f,id){const world=f.$('.map-world').getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\) scale\(([-\d.]+)\)/),point=f.$(`[data-paper-id="${id}"]`).getAttribute('transform').match(/translate\(([-\d.]+) ([-\d.]+)\)/);return{clientX:Number(world[1])+Number(point[1])*Number(world[3]),clientY:Number(world[2])+Number(point[2])*Number(world[3])}}
function pointerPick(f,point,target){const svg=f.$('#map-canvas');svg.emit('pointermove',{target:target||svg,pointerType:'mouse',...point});const hover=f.$('.map-hover-card').textContent;svg.emit('pointerdown',{target:target||svg,button:0,pointerType:'mouse',pointerId:77,...point});svg.emit('pointerup',{pointerId:77,...point});return hover}
const labelFixture=()=>fixture({url:'https://example.org/RoboPaperAtlas/map/index.html?topic=navigation&problem=navigation%2Fnav-language',reduced:true});
test('visible paper label and star share actual screen-coordinate hover and selection',()=>{
 for(const target of ['star','text']){const f=labelFixture(),id='agenticnav-tool-harness',node=f.$(`[data-paper-id="${id}"]`),label=node.querySelector('.map-node-label');assert(node.classList.contains('is-label'));
 const b=label.getBoundingClientRect(),point=target==='star'?screenStar(f,id):{clientX:b.left+b.width*.65,clientY:b.top+b.height/2};
 assert.match(pointerPick(f,point,label),/AgenticNav/);assert.match(selected(f),/AgenticNav/);assert(f.location.search.includes('paper=agenticnav-tool-harness'));
 }
});
test('hidden labels have no ghost targets, and visible label hit tracks zoom and pan',()=>{
 const f=labelFixture(),node=f.$('[data-paper-id="agenticnav-tool-harness"]'),label=node.querySelector('.map-node-label');
 for(const action of ['[data-camera="in"]','[data-camera="out"]']){f.click(action);const b=label.getBoundingClientRect(),point={clientX:b.left+b.width*.65,clientY:b.top+b.height/2};assert.match(pointerPick(f,point,label),/AgenticNav/);f.click('#map-panel-close')}
 const svg=f.$('#map-canvas');svg.emit('pointerdown',{button:0,pointerType:'mouse',pointerId:2,clientX:50,clientY:50});svg.emit('pointermove',{pointerId:2,clientX:65,clientY:60});svg.emit('pointerup',{pointerId:2});
 const afterPan=label.getBoundingClientRect();assert.match(pointerPick(f,{clientX:afterPan.left+afterPan.width*.65,clientY:afterPan.top+afterPan.height/2},label),/AgenticNav/);f.click('#map-panel-close');
 // Suppressed by collision policy: the former text rectangle is not a target.
 const b=label.getBoundingClientRect();node.classList.remove('is-label');f.document.activeElement=f.$('#map-canvas');pointerPick(f,{clientX:b.left+b.width*.8,clientY:b.top+b.height/2},label);assert.equal(selected(f),'');assert(f.$('.map-hover-card').hidden);
});
test('overlapping visible text chooses nearest star with stable ID tie break, not DOM target order',()=>{
 const f=labelFixture(),a=f.$('[data-paper-id="agenticnav-tool-harness"]'),b=f.$('[data-paper-id="krantz2020vlnce"]');
 const box={left:780,top:170,right:900,bottom:195,width:120,height:25};for(const node of[a,b]){node.classList.add('is-label');node.querySelector('.map-node-label').getBoundingClientRect=()=>box}
 const point={clientX:840,clientY:182},expected=[a,b].map(n=>({id:n.dataset.paperId,...screenStar(f,n.dataset.paperId)})).sort((a,b)=>Math.hypot(a.clientX-point.clientX,a.clientY-point.clientY)-Math.hypot(b.clientX-point.clientX,b.clientY-point.clientY)||a.id.localeCompare(b.id))[0].id;
 pointerPick(f,point,a.querySelector('.map-node-label'));assert.equal(new URLSearchParams(f.location.search).get('paper'),expected);
});
test('canvas clipping rejects off-canvas label coordinates',()=>{
 const f=labelFixture(),node=f.$('[data-paper-id="agenticnav-tool-harness"]');node.classList.add('is-label');node.querySelector('.map-node-label').getBoundingClientRect=()=>({left:-100,right:100,top:100,bottom:125,width:200,height:25});pointerPick(f,{clientX:-20,clientY:112},node);assert.equal(selected(f),'');assert(f.$('.map-hover-card').hidden);
});

// Split-view regression checks run in the established map CI suite.
require('./test_split_starmap.cjs');

// Keep reference-C regressions in the existing CI entry point.
require('./test_reference_scroll_regressions.cjs');
require('./test_persistent_overview.cjs');
