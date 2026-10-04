'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {search,neighborhood,positions}=require('./program.cjs').core,{fixture}=require('./dom_fixture.cjs');
const data=require('./program.cjs').data;
test('verified pilot has exactly eight unique pairs and11 typed primary-source records',()=>{
 const g=neighborhood(data.papers,data.relations.edges,'rpa-0062');assert.equal(g.pairs.length,8);assert.equal(g.papers.length,9);assert.equal(g.pairs.flatMap(p=>p.records).length,11);assert.equal(g.pairs.filter(p=>p.records.length===2).length,3);
 assert.equal(g.pairs.flatMap(p=>p.records).filter(r=>r.type==='same_task').length,0);assert(g.pairs.every(p=>p.records.every(r=>r.directed&&r.evidence.every(e=>e.url.startsWith('https://')&&e.pdf_page))));
});
test('neighbor order and positions are deterministic without modifying source records',()=>{
 const before=JSON.stringify(data),a=neighborhood(data.papers,data.relations.edges,'rpa-0062'),b=neighborhood(data.papers.slice().reverse(),data.relations.edges.slice().reverse(),'rpa-0062');
 assert.deepEqual(a,b);assert.deepEqual(positions(a,'rpa-0062'),positions(b,'rpa-0062'));assert.equal(JSON.stringify(data),before);assert.equal(new Set(a.papers.map(p=>p.id)).size,9);
});
test('citation versus explicit adoption filtering keeps one line per paper pair',()=>{
 assert.equal(neighborhood(data.papers,data.relations.edges,'rpa-0062',['cites']).pairs.length,8);
 const g=neighborhood(data.papers,data.relations.edges,'rpa-0062',['uses_method_or_resource']);assert.equal(g.pairs.length,3);assert(g.pairs.every(p=>p.records.length===1));
 assert.equal(neighborhood(data.papers,data.relations.edges,'rpa-0062',[]).pairs.length,0);
});
test('unindexed ODYSSEY has no invented verified edges; task inference is explicit and bounded',()=>{
 assert.equal(neighborhood(data.papers,data.relations.edges,'rpa-0042').pairs.length,0);
 const g=neighborhood(data.papers,data.relations.edges,'rpa-0042',['same_task']);assert(g.pairs.length>0&&g.pairs.length<=4);assert(g.pairs.every(p=>p.records.every(r=>r.type==='same_task'&&!r.directed&&r.status==='editorial_inference')));
});
test('all95 titles are searchable and task/method intersections are independent',()=>{
 assert.equal(data.papers.length,95);for(const p of data.papers)assert.equal(search(data.papers,p.title)[0].id,p.id);
 for(const task of Object.keys(data.tasks))for(const method of Object.keys(data.methods))assert(search(data.papers,'',task,method).every(p=>p.tasks.includes(task)&&p.methods.includes(method)));
});
test('default view has9named nodes,8clickable collapsed connections and selected-paper context',()=>{
 const f=fixture();assert.equal(f.$$('.node').length,9);assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.edge-label').length,8);assert.equal(f.$('#inspection-title').textContent,'UMI on Legs');assert.equal(f.$('.result').getAttribute('aria-current'),'true');assert.equal(f.$$('#results')[0].children.length,95);
 assert(f.$$('.node').every(n=>n.querySelector('strong').textContent));assert.match(f.$('#graph-subtitle').textContent,/11/);
});
test('edge click shows both citation and adoption evidence without conflating them',()=>{
 const f=fixture();f.click('[data-pair="rpa-0013~rpa-0062"]');assert.match(f.$('#inspector').textContent,/参考文献 \[2\]/);assert.match(f.$('#inspector').textContent,/采用方法或资源/);assert.match(f.$('#inspector').textContent,/PDF 第 3 页/);assert(f.$$('#inspector')[0].querySelectorAll('a').some(a=>a.href.endsWith('#page=3')));assert.equal(f.document.activeElement.id,'inspection-title');
 f.click('#back-paper');assert.equal(f.$('#inspection-title').textContent,'UMI on Legs');assert(f.document.activeElement.isConnected);
});
test('select paper, relation, Back and Forward restore correct connected focus',()=>{
 const f=fixture();f.click('[data-pair="rpa-0013~rpa-0062"]');f.click('[data-paper="rpa-0013"]');assert.equal(f.$('#inspection-title').textContent,'Diffusion Policy');f.goBack();assert.match(f.$('#inspection-title').textContent,/UMI on Legs → Diffusion Policy/);assert(f.document.activeElement.isConnected);f.goForward();assert.equal(f.$('#inspection-title').textContent,'Diffusion Policy');assert.equal(f.$('#back').disabled,false);
});
test('global search and full-name filters never require entering a hierarchy',()=>{
 const f=fixture();f.input('ODYSSEY');assert.equal(f.$('#results').children.length,1);f.$('#search').emit('keydown',{key:'Enter'});assert.equal(f.$('#inspection-title').textContent,'ODYSSEY');assert.equal(f.$$('.edge').length,0);assert.match(f.$('#graph-subtitle').textContent,/尚未索引/);
 f.click('#nav-query');assert.equal(f.$('#task').value,'vln');assert(f.$('#results').children.length>0);assert.equal(f.$('#method').value,'all');f.click('[data-seed="rpa-0062"]');assert.equal(f.$('#results').children.length,95);assert.equal(f.$$('.edge').length,8);
});
test('relation toggles and rapid replacement leave no stale evidence or animations',()=>{
 const f=fixture();for(let i=0;i<15;i++){f.click('[data-pair="rpa-0013~rpa-0062"]');f.click('#back-paper');f.click('[data-zoom="in"]');f.click('[data-seed="rpa-0062"]');}f.step(1000);assert.equal(f.raf.size,0);assert.equal(f.$('#inspection-title').textContent,'UMI on Legs');
 const cites=f.$('[data-type="cites"]');cites.checked=false;cites.emit('change');assert.equal(f.$$('.edge').length,3);assert(f.$$('.edge-label').every(e=>e.textContent==='采用'));
});
test('drag is immediate, ordinary wheel scrolls, hidden and new selection cancel camera',()=>{
 const f=fixture(),graph=f.$('#graph');graph.emit('pointerdown',{button:0,pointerType:'mouse',pointerId:1,clientX:20,clientY:20});graph.emit('pointermove',{pointerId:1,clientX:45,clientY:35});assert.match(f.$('#world').style.transform,/25px,15px/);assert.equal(f.raf.size,0);graph.emit('pointerup',{pointerId:1});
 const before=f.$('#world').style.transform,e=graph.emit('wheel',{deltaY:100,clientX:20,clientY:20});assert(!e.defaultPrevented);assert.equal(f.$('#world').style.transform,before);
 f.click('[data-zoom="in"]');assert.equal(f.raf.size,1);f.document.hidden=true;f.document.emit('visibilitychange');assert.equal(f.raf.size,0);f.document.hidden=false;f.click('[data-zoom="in"]');f.click('[data-paper="rpa-0013"]');assert.equal(f.raf.size,0);
});
test('mobile begins with results and evidence, with an explicit optional graph',()=>{
 const f=fixture({mobile:true});assert.equal(f.$('#workspace').dataset.mobileGraph,'false');assert.equal(f.$('#mobile-graph').getAttribute('aria-expanded'),'false');f.click('#mobile-graph');assert.equal(f.$('#workspace').dataset.mobileGraph,'true');f.click('[data-paper="rpa-0013"]');assert(f.$('#inspector').scrolled);assert.equal(f.$('#inspection-title').textContent,'Diffusion Policy');
});
test('invalid URLs fail closed and imported Stage availability remains factual',()=>{
 const f=fixture({url:'https://example.org/prototype/?paper=unknown&method=wrong&task=wrong&relation=fake'});assert.equal(f.$('#inspection-title').textContent,'UMI on Legs');assert.equal(f.$('.stage-links').children.filter(x=>x.tagName==='A').length,3);f.click('[data-paper="rpa-0013"]');assert(f.$('.stage-links').children.every(x=>x.tagName==='SPAN'));
});
test('all five imported papers expose exact current versions and incomplete stages remain unavailable',()=>{
 const catalog=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../../data/catalog.json'),'utf8'));
 let imported=0;
 for(const paper of catalog.papers.filter(p=>Object.values(p.stages).some(s=>s.status==='imported'))){
  const f=fixture({url:`https://example.org/prototype/?paper=${paper.id}`}),links=f.$('.stage-links').children;
  assert.equal(links.length,3);
  for(let index=0;index<3;index++){
   const stage=paper.stages[`stage${index+1}`],link=links[index];
   if(stage.status==='imported'){
    imported++;assert.equal(link.tagName,'A');
    assert.equal(link.href,'https://chunhui-lab.github.io/RoboPaperAtlas/'+stage.artifacts[0].path);
   }else{assert.equal(link.tagName,'SPAN');assert.match(link.textContent,/尚未导入/);}
  }
 }
 assert.equal(imported,12);
});
test('production script has no network, model, physics or persistent tracking calls',()=>{
 const s=require('./program.cjs').source;assert(!/\bfetch\s*\(|XMLHttpRequest|WebSocket|sendBeacon|localStorage|eval\s*\(/.test(s));
});

test('Chinese full task and method names work in search and years keep their source basis',()=>{
 assert.equal(search(data.papers,'强化学习').length,data.papers.filter(p=>p.methods.includes('RL')).length);
 assert.equal(search(data.papers,'视觉语言导航').length,data.papers.filter(p=>p.tasks.includes('vln')).length);
 assert.equal(data.papers.find(p=>p.id==='rpa-0012').yearLabel,'2022 · 原始记录年');
 const f=fixture();assert(f.$$('.node').every(n=>/记录年|出版年|预印本年|待核验/.test(n.querySelector('small').textContent)));
});
test('offscreen and reduced motion stop zoom transitions immediately',()=>{
 const f=fixture();f.click('[data-zoom="in"]');assert.equal(f.raf.size,1);f.observers[0].cb([{isIntersecting:false}]);assert.equal(f.raf.size,0);f.observers[0].cb([{isIntersecting:true}]);f.click('[data-zoom="in"]');f.changeMedia('(prefers-reduced-motion:reduce)',true);assert.equal(f.raf.size,0);f.click('[data-zoom="in"]');assert.equal(f.raf.size,0);
});

test('inference matches classification problem groups and stays undirected in text and ARIA',()=>{
 const f=fixture({url:'https://example.org/prototype/?paper=savva2019habitat&types=same_task'});
 const edge=f.$$('.edge')[0];assert(edge);assert(!edge.getAttribute('aria-label').includes('→'));assert(edge.getAttribute('aria-label').includes('同问题组'));
 f.click('.edge');assert(!f.$('#inspection-title').textContent.includes('→'));assert(f.$('#inspector').textContent.includes('分类问题组')||f.$('#inspector').textContent.includes('同问题组'));
 const source=require('./program.cjs').source;assert(source.includes('或已标明的论文段落'));
});
test('small supporting texts retain contrast on dark surfaces',()=>{
 const css=require('./program.cjs').css;for(const old of ['#607994','#627e9b','#5e7692','#667e9a'])assert(!css.includes('color:'+old));
 const lum=h=>{const rgb=[0,2,4].map(i=>parseInt(h.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return rgb.reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0)};assert((lum('91a8c0')+.05)/(lum('152335')+.05)>=4.5);
});
