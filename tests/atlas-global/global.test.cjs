const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const program=require('./program.cjs'),M=program.model,D=program.data,{fixture}=require('./dom_fixture.cjs');
test('95 unique canonical records have stable, finite, distinct coordinates independent of input order',()=>{assert.equal(D.papers.length,95);assert.equal(new Set(D.papers.map(p=>p.id)).size,95);const a=M.layout(D.papers),b=M.layout([...D.papers].reverse());assert.deepEqual(a,b);assert.equal(new Set(a.map(p=>p.x+','+p.y)).size,95);assert(a.every(p=>Number.isFinite(p.x)&&Number.isFinite(p.y)&&M.colors[p.category]));});
test('all titles, Chinese task/method names, authors and outside-pilot papers searchable',()=>{for(const p of D.papers)assert(M.search(p,p.title,'',''));for(const p of D.papers.filter(p=>p.methods.includes('RL')))assert(M.search(p,'强化学习','',''));assert.equal(D.papers.filter(p=>M.search(p,'ODYSSEY','','')).length,1)});
test('11 typed verified records retain 8 directed pairs and exact evidence',()=>{const n=M.neighborhood('rpa-0062',D.relations.edges);assert.equal(n.records.length,11);assert.equal(n.ids.size,9);assert.equal(M.pairs(n.records).length,8);assert(n.records.every(e=>e.directed&&e.evidence.every(v=>v.url.startsWith('https://')&&v.pdf_page>0)));assert.equal(n.records.filter(e=>e.type==='uses_method_or_resource').length,3)});
test('initial DOM renders all95 with no mandatory selected paper and no inferred edges',()=>{const f=fixture();assert.equal(f.$$('.node').length,95);assert.equal(f.$$('.edge').length,0);assert(f.$('#detail').hidden);assert.equal(f.window.AtlasDebug.getState().selected,null);assert.equal(f.$('#results').children.length,95)});
test('all95 initial projected coordinates fit desktop and mobile viewport',()=>{for(const opt of [{width:1440,height:900},{width:1024,height:768},{mobile:true,width:390,height:844}]){const f=fixture(opt),dbg=f.window.AtlasDebug;for(const p of dbg.nodes){const q=dbg.project(p);assert(q.x>0&&q.x<opt.width&&q.y>0&&q.y<opt.height,p.id+' '+JSON.stringify(q))}}});
test('selection retains95 nodes and yields8 evidence pairs, then unknown paper has honest empty state',()=>{const f=fixture();f.window.AtlasDebug.select('rpa-0062');f.step(600);assert.equal(f.$$('.node').length,95);assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.evidence').length,12);assert.match(f.$('#detail').textContent,/采用方法或资源/);f.window.AtlasDebug.select('rpa-0042');f.step(600);assert.equal(f.$$('.node').length,95);assert.equal(f.$$('.edge').length,0);assert.match(f.$('#detail').textContent,/关系尚未索引/)});
test('search dims nonmatching context, keeps selected exception, and overview clears state',()=>{const f=fixture();f.window.AtlasDebug.select('rpa-0062');f.input('ODYSSEY');assert.equal(f.$('#results').children.length,1);assert.equal(f.$$('.node').length,95);assert.match(f.$('#detail').textContent,/不符合筛选/);f.click('#overview');f.step(600);assert.equal(f.window.AtlasDebug.getState().selected,null);assert.equal(f.window.AtlasDebug.getState().matching.length,95);assert.equal(f.$$('.edge').length,0);assert(f.$('#detail').hidden);assert.equal(f.window.AtlasDebug.getState().camera.k,1)});
test('rapid selection, zoom interruption, and reset do not leave stale animations',()=>{const f=fixture();for(let i=0;i<10;i++){f.window.AtlasDebug.select('rpa-0062');f.window.AtlasDebug.select('rpa-0042')}assert.equal(f.raf.size,1);f.click('#plus');assert.equal(f.raf.size,0);f.click('#overview');f.step(600);assert.equal(f.raf.size,0);assert.equal(f.$$('.node').length,95)});
test('reduced-motion selection is immediate; input remains functional',()=>{const f=fixture({reduced:true,mobile:true});f.window.AtlasDebug.select('rpa-0062');assert.equal(f.raf.size,0);assert.equal(f.window.AtlasDebug.getState().camera.k,1.15);assert(f.$('#controls').classList.contains('collapsed'));f.click('#collapse');assert(!f.$('#controls').classList.contains('collapsed'));f.click('#collapse');assert(f.$('#controls').classList.contains('collapsed'))});
test('no external scripts, WebGL, copied reference assets, private paths or network calls ship',()=>{const html=program.html;assert(!/WebGL|THREE\.|googolstars|\/workspace\/|2026-09-30 21-48-59|<script[^>]+src=|\bfetch\s*\(|localStorage|XMLHttpRequest/.test(html));assert(!/\/\*(?:APP|DATA|MODEL|STYLE)\*\//.test(html))});

test('clicking a relation exposes its source details without changing the selected paper',()=>{const f=fixture();f.window.AtlasDebug.select('rpa-0062');f.step(600);f.click('.edge');assert(f.$$('.evidence').some(e=>e.open));assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');assert.equal(f.$$('.node').length,95)});

test('Close and Escape restore keyboard focus to the selected visible star, or Overview',()=>{const f=fixture();f.window.AtlasDebug.select('rpa-0062');const close=f.$('#detail').querySelector('button');close.focus();close.emit('click');assert(f.$('#detail').hidden);assert.equal(f.document.activeElement.dataset.id,'rpa-0062');f.window.AtlasDebug.select('rpa-0042');f.$('#detail').querySelector('button').focus();const event=f.window.emit('keydown',{key:'Escape'});assert(event.defaultPrevented);assert.equal(f.document.activeElement.dataset.id,'rpa-0042');assert(f.$('#detail').hidden);f.window.emit('keydown',{key:'Escape'});assert.equal(f.document.activeElement.id,'overview')});
test('Relation role button supports Space without scrolling the page',()=>{const f=fixture();f.window.AtlasDebug.select('rpa-0062');f.step(600);const event=f.$('.edge').emit('keydown',{key:' '});assert(event.defaultPrevented);assert(f.$$('.evidence').some(e=>e.open));assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062')});

test('four broad Chinese groups cover all95 with transparent overlaps and no primary reassignment',()=>{const expected={'navigation-space':29,'motion-manipulation':46,'robot-learning':48,'methods-resources':29};assert.equal(Object.keys(D.browseLabels).length,4);for(const[key,n]of Object.entries(expected))assert.equal(D.papers.filter(p=>M.search(p,'',key,'')).length,n);assert(D.papers.every(p=>p.navigation.groups.length));const od=D.papers.find(p=>p.label.includes('ODYSSEY'));assert.equal(od.classification.direction,'mobile-manipulation');assert(od.navigation.groups.includes('motion-manipulation'));for(const id of ['rpa-0008','rpa-0018','rpa-0046','rpa-0058'])assert.deepEqual(D.papers.find(p=>p.id===id).navigation.groups,['methods-resources'])});
test('browse and source-backed method filtering intersect without hiding all95 context',()=>{const f=fixture();f.$('#task').value='motion-manipulation';f.$('#method').value='WBC';f.window.AtlasDebug.filter();assert.equal(f.$$('.node').length,95);const state=f.window.AtlasDebug.getState();assert(state.matching.includes('rpa-0062'));state.matching.forEach(id=>assert(D.papers.find(p=>p.id===id).methods.includes('WBC')));assert.equal(f.$('#task').options.length,5)});

test('optional methods and resources form independent axes and clear together',()=>{const f=fixture();assert.equal(f.$('#commonMethods').children.length,6);const chip=f.$('#commonMethods').children.find(b=>b.dataset.method==='WBC');chip.emit('click');assert.equal(f.$('#method').value,'WBC');assert.equal(chip.getAttribute('aria-pressed'),'true');f.$('#resource').value='dataset';f.window.AtlasDebug.filter();f.window.AtlasDebug.getState().matching.forEach(id=>{const p=D.papers.find(p=>p.id===id);assert(p.methods.includes('WBC'));assert(p.classification.resourceKinds.includes('dataset'))});f.click('#clear');assert.equal(f.$('#resource').value,'');assert.equal(f.$('#method').value,'');assert.equal(f.window.AtlasDebug.getState().matching.length,95)});

test('null-primary resources remain resources in detail, not research directions',()=>{const f=fixture();for(const id of ['rpa-0022','rpa-0032','rpa-0039','rpa-0045','savva2019habitat','ramakrishnan2021hm3d','yadav2023hm3dsem']){const p=D.papers.find(p=>p.id===id);assert.equal(p.classification.direction,null);f.window.AtlasDebug.select(id);assert.match(f.$('#detail').textContent,/跨领域资源/)}f.window.AtlasDebug.select('holoagent-0');assert.match(f.$('#detail').textContent,/跨领域研究/)});
test('global text search uses order-independent AND terms like Library',()=>{const p=D.papers.find(p=>p.id==='rpa-0062');assert(M.search(p,'legs umi','',''));assert(M.search(p,'  umi   legs  ','',''));assert(!M.search(p,'umi nonexistentword','',''))});

test('UMI abbreviation includes original UMI without losing existing family matches',()=>{
 const matches=D.papers.filter(p=>M.search(p,'UMI','','')).map(p=>p.id);assert.equal(matches.length,3);
 for(const id of ['rpa-0064','rpa-0062','rpa-0017'])assert(matches.includes(id),id+' should match UMI');
 const f=fixture();f.input('UMI');for(const id of ['rpa-0064','rpa-0062','rpa-0017'])assert(f.window.AtlasDebug.getState().matching.includes(id));
});
test('narrow selection shows only selected and hovered or focused labels, retaining all relation evidence',()=>{
 const f=fixture({mobile:true,width:390,height:844,reduced:true});f.window.AtlasDebug.select('rpa-0062');
 const labels=()=>f.$$('.node-label').filter(n=>n.textContent);
 assert.equal(labels().length,1);assert.equal(labels()[0].parentElement.dataset.id,'rpa-0062');
 assert.equal(f.$$('.node').length,95);assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.relation').length,8);assert.equal(f.$$('.evidence').length,12);
 const other=f.$('.node[data-id="rpa-0064"]');other.emit('pointerenter',{clientX:150,clientY:200});assert.equal(labels().length,2);other.emit('pointerleave');assert.equal(labels().length,1);
 other.focus();assert.equal(labels().length,2);other.emit('blur',{bubbles:false});assert.equal(labels().length,1);
 f.context.innerWidth=1440;f.context.innerHeight=900;f.window.emit('resize');assert(labels().length>=5&&labels().length<=9);
 f.context.innerWidth=390;f.context.innerHeight=844;f.window.emit('resize');assert.equal(labels().length,1);assert.equal(f.$$('.edge').length,8);
});

const overlaps=(a,b)=>a.x<b.x+b.width+5&&a.x+a.width+5>b.x&&a.y<b.y+b.height+5&&a.y+a.height+5>b.y;

test('review prototype preserves the complete input dataset and relationship evidence byte-for-byte',()=>{
 const raw=program.html.match(/<script id="atlas-data" type="application\/json">([\s\S]*?)<\/script>/)[1];
 assert.equal(require('node:crypto').createHash('sha256').update(raw).digest('hex'),'1ae66d5bd377cbc623dff58f71221a9fcdd6e902e37eadf850f53e45e8ff114c');
});

test('selection and panel expansion never change global projection base or shuffle model coordinates',()=>{
 for(const size of [{width:1440,height:900},{width:1180,height:757},{mobile:true,width:390,height:844}]){
  const f=fixture(size),d=f.window.AtlasDebug,b=JSON.stringify(d.base()),points=JSON.stringify(d.nodes.map(n=>[n.id,n.x,n.y]));
  f.click('#collapse');assert.equal(JSON.stringify(d.base()),b);
  d.select('rpa-0062');f.step(600);assert.equal(JSON.stringify(d.base()),b);assert.equal(JSON.stringify(d.nodes.map(n=>[n.id,n.x,n.y])),points);
  f.click('#overview');f.step(600);assert.equal(JSON.stringify(d.base()),b);
 }
});

test('compact search is immediately available without opening a category panel; typing shows live results',()=>{
 const f=fixture();assert(f.$('#controls').classList.contains('collapsed'));assert.equal(f.$('#collapse').getAttribute('aria-expanded'),'false');
 f.input('ODYSSEY');assert(!f.$('#results').hidden);assert.equal(f.$('#results').children.length,1);assert.equal(f.$('#task').value,'');
 const result=f.$('#results').querySelector('button');result.emit('click');f.step(600);
 assert.match(f.$('#detail').textContent,/ODYSSEY/);assert(f.$('#results').hidden);assert.equal(f.$$('.node').length,95);
});

test('filter and result disclosures are exclusive and expose accurate state after repeated activation',()=>{
 const f=fixture();for(let i=0;i<3;i++){
  f.click('#collapse');assert.equal(f.$('#collapse').getAttribute('aria-expanded'),'true');assert(f.$('#results').hidden);
  f.click('#listToggle');assert.equal(f.$('#listToggle').getAttribute('aria-expanded'),'true');assert.equal(f.$('#collapse').getAttribute('aria-expanded'),'false');
  f.click('#listToggle');assert(f.$('#results').hidden);
 }
});

test('actual label-placement output has no pairwise collisions at desktop and narrow sizes',()=>{
 for(const size of [{width:1440,height:900},{width:1180,height:757},{width:1024,height:768},{mobile:true,width:500,height:757},{mobile:true,width:390,height:844}]){
  const f=fixture(size),d=f.window.AtlasDebug;d.select('rpa-0062');f.step(600);const labels=d.getLabels();assert(labels.some(l=>l.id==='rpa-0062'));
  for(let i=0;i<labels.length;i++)for(let j=i+1;j<labels.length;j++)assert(!overlaps(labels[i],labels[j]),labels[i].id+' / '+labels[j].id);
  assert(labels.every(l=>l.x>=12&&l.x+l.width<=size.width-12&&l.y>=80));
  if(size.mobile)assert.equal(labels.length,1);else assert(labels.length>=5);
  assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.evidence').length,12);
 }
});

test('narrow selection limits persistent labels and suppresses pointer tooltips without losing evidence',()=>{
 const f=fixture({mobile:true,width:390,height:844});f.window.AtlasDebug.select('rpa-0062');f.step(600);
 f.$('[data-id="rpa-0013"]').emit('pointerenter',{pointerType:'touch',clientX:220,clientY:320});assert(f.$('#tooltip').hidden);
 assert(f.window.AtlasDebug.getLabels().length<=2);assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.evidence').length,12);
});

test('decorative dust is finite, separately marked, noninteractive, and clearly disclosed',()=>{
 const f=fixture();const ambient=f.$('#ambient');assert.equal(ambient.getAttribute('aria-hidden'),'true');assert.equal(ambient.getAttribute('pointer-events'),'none');assert.equal(ambient.getAttribute('role'),'presentation');
 assert.equal(ambient.querySelectorAll('circle').length,780);assert.equal(ambient.querySelectorAll('[tabindex]').length,0);assert.equal(ambient.querySelectorAll('[data-id]').length,0);
 assert.equal(f.$$('.node').length,95);assert.match(f.$('#mapNotes').textContent,/不代表额外论文/);assert.match(f.$('#footer').textContent,/背景星尘仅作装饰/);assert.equal(f.raf.size,0);
});

test('reduced motion, selection changes, clear, and Escape finish with the exact 95-paper overview',()=>{
 const f=fixture({reduced:true,mobile:true,width:390,height:844});
 f.input('umi legs');f.$('#results').querySelector('button').emit('click');assert.equal(f.raf.size,0);
 f.click('#plus');f.input('doesnotexist');assert.equal(f.$('#results').children.length,1);assert.match(f.$('#results').textContent,/没有匹配/);
 f.click('#clear');assert.equal(f.window.AtlasDebug.getState().matching.length,95);
 f.window.emit('keydown',{key:'Escape'});assert(f.$('#detail').hidden);assert(f.$('#results').hidden);assert.equal(f.$$('.edge').length,0);assert.equal(f.$$('.node').length,95);assert.equal(f.raf.size,0);assert.equal(f.window.AtlasDebug.getState().camera.k,1);
});

test('dragging the field interrupts focus motion and does not activate a paper',()=>{
 const f=fixture();const d=f.window.AtlasDebug;d.select('rpa-0062');assert.equal(f.raf.size,1);
 f.$('#field').emit('pointerdown',{button:0,clientX:600,clientY:400});assert.equal(f.raf.size,0);
 f.window.emit('pointermove',{clientX:660,clientY:430});f.$('[data-id="rpa-0013"]').emit('click');assert.equal(d.getState().selected,'rpa-0062');
 f.window.emit('pointerup');f.$('[data-id="rpa-0013"]').emit('click');assert.equal(d.getState().selected,'rpa-0013');
});

test('native disclosure, focus targets, touch targets and motion override are present in shipped prototype',()=>{
 const h=program.html;assert.match(h,/aria-controls="filterPanel"/);assert.match(h,/aria-controls="results"/);assert.match(h,/min-height:44px/);assert.match(h,/@media\(prefers-reduced-motion:reduce\)/);assert.match(h,/animation:none!important/);
 assert(!/WebGL|THREE\.|<canvas|googolstars|\/workspace\/|\.mp4|reference-behavior/.test(h));
});

test('short narrow windows prioritize the readable detail and list rather than squeezing a tiny active map',()=>{
 const f=fixture({mobile:true,width:500,height:420,reduced:true});f.window.AtlasDebug.select('rpa-0062');
 assert(f.$('#detail').classList.contains('compact-read'));assert(f.$('#field').classList.contains('reading-mode'));assert.equal(f.$('#field').getAttribute('aria-hidden'),'true');assert.equal(f.$('#field').getAttribute('tabindex'),'-1');
 assert.equal(f.window.AtlasDebug.getLabels().length,0);assert(f.$$('.node').every(n=>n.getAttribute('tabindex')==='-1'));assert.equal(f.$$('.node').length,95);assert.match(f.$('#detail').textContent,/11 条记录/);
 f.input('ODYSSEY');assert.equal(f.$('#results').children.length,1);assert(!f.$('#results').hidden);
 f.click('#overview');assert(!f.$('#field').classList.contains('reading-mode'));assert.equal(f.$('#field').getAttribute('aria-hidden'),'false');assert.equal(f.$('#field').getAttribute('tabindex'),'0');assert(f.$$('.node').every(n=>n.getAttribute('tabindex')==='-1'));
});

test('Back and Forward restore paper selection and camera on the same preview path with a matching paper URL',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug,original=f.location.href;
 d.select('rpa-0062');const first=JSON.stringify(d.getState().camera);d.select('rpa-0013');const second=JSON.stringify(d.getState().camera);
 f.goBack();assert.equal(d.getState().selected,'rpa-0062');assert.equal(JSON.stringify(d.getState().camera),first);assert.equal(f.$$('.edge').length,8);assert.equal(new URL(f.location.href).pathname,new URL(original).pathname);assert.equal(new URL(f.location.href).searchParams.get('paper'),'rpa-0062');
 f.goBack();assert.equal(d.getState().selected,null);assert(f.$('#detail').hidden);assert.equal(d.getState().camera.k,1);
 f.goForward();assert.equal(d.getState().selected,'rpa-0062');f.goForward();assert.equal(d.getState().selected,'rpa-0013');assert.equal(JSON.stringify(d.getState().camera),second);assert.equal(new URL(f.location.href).pathname,new URL(original).pathname);assert.equal(new URL(f.location.href).searchParams.get('paper'),'rpa-0013');
});

test('keyboard paper selection, detail Close, and Back restore a real paper focus target',()=>{
 const f=fixture({reduced:true}),star=f.$('[data-id="rpa-0062"]');star.focus();const e=star.emit('keydown',{key:'Enter'});assert(e.defaultPrevented);assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');
 const close=f.$('#detail').querySelector('button');close.focus();close.emit('click');assert(f.$('#detail').hidden);assert.equal(f.document.activeElement.dataset.id,'rpa-0062');
 f.goBack();assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');assert.equal(f.document.activeElement.dataset.id,'rpa-0062');
 const other=f.$('[data-id="rpa-0013"]');const space=other.emit('keydown',{key:' '});assert(space.defaultPrevented);assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0013');
});

test('resizing after pan and zoom retains the camera rather than resetting the map',()=>{
 const f=fixture({reduced:true,width:1180,height:757}),d=f.window.AtlasDebug;d.select('rpa-0062');f.click('#plus');f.$('#field').emit('keydown',{key:'ArrowLeft'});const before=JSON.stringify(d.getState().camera);
 f.context.innerWidth=500;f.context.innerHeight=757;f.window.emit('resize');assert.equal(JSON.stringify(d.getState().camera),before);assert.equal(d.getState().selected,'rpa-0062');assert.equal(f.$$('.node').length,95);
 f.context.innerWidth=1180;f.window.emit('resize');assert.equal(JSON.stringify(d.getState().camera),before);
});


test('Back from a search result restores its query, complete matching list and previous map camera',()=>{
 const f=fixture({reduced:true});f.input('UMI');assert.equal(f.$('#results').children.length,3);f.click('#plus');const before=JSON.stringify(f.window.AtlasDebug.getState().camera);
 f.$('#results').querySelector('button').emit('click');assert(!f.$('#detail').hidden);f.goBack();assert(f.$('#detail').hidden);assert.equal(f.$('#query').value,'UMI');assert(!f.$('#results').hidden);assert.equal(f.$('#results').children.length,3);assert.equal(JSON.stringify(f.window.AtlasDebug.getState().camera),before);
});

// This test uses the known overlapping rectangles from source review, then checks
// the production stacking/inert contract for every sampled intersection point.
// It is a geometry-contract regression, not a browser screenshot or layout test.
test('500x420 selected ODYSSEY results win the overlapping detail hit region and support keyboard entry',()=>{
 const f=fixture({mobile:true,width:500,height:420,reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');f.input('ODYSSEY');
 const css=program.html.match(/<style>([\s\S]*?)<\/style>/)[1];
 const controlsZ=Number(css.match(/\.controls\.overlay-active\{z-index:(\d+)/)[1]);
 const detailZ=Number(css.match(/\.detail\{[^}]*z-index:(\d+)/)[1]);
 assert(controlsZ>detailZ);assert(f.$('#controls').classList.contains('overlay-active'));assert.equal(f.$('#detail').getAttribute('inert'),'');assert.match(css,/\.detail\[inert\]\{pointer-events:none\}/);
 const resultsRect={x:16,y:155,width:468,height:85},detailRect={x:12,y:155,width:476,height:190};
 const contains=(r,p)=>p.x>=r.x&&p.x<=r.x+r.width&&p.y>=r.y&&p.y<=r.y+r.height;
 const layers=[{id:'results',rect:resultsRect,z:controlsZ,canHit:!f.$('#results').hidden},{id:'detail',rect:detailRect,z:detailZ,canHit:f.$('#detail').getAttribute('inert')===null}];
 for(const point of [{x:30,y:160},{x:250,y:180},{x:475,y:225}]){assert(contains(resultsRect,point)&&contains(detailRect,point));assert.equal(layers.filter(l=>l.canHit&&contains(l.rect,point)).sort((a,b)=>b.z-a.z)[0].id,'results')}
 const key=f.$('#query').emit('keydown',{key:'ArrowDown'});assert(key.defaultPrevented);const result=f.$('#results').querySelector('button');assert.equal(f.document.activeElement,result);
 const enter=result.emit('keydown',{key:'Enter'});assert(enter.defaultPrevented);assert.match(f.$('#detail').textContent,/ODYSSEY/);assert(f.$('#results').hidden);assert(!f.$('#controls').classList.contains('overlay-active'));assert.equal(f.$('#detail').getAttribute('inert'),null);assert.equal(f.document.activeElement,f.$('#detail').querySelector('button'));
});

test('Escape dismisses the active search overlay without discarding the retained selected paper',()=>{
 const f=fixture({mobile:true,width:500,height:420,reduced:true});f.window.AtlasDebug.select('rpa-0062');f.input('ODYSSEY');const e=f.window.emit('keydown',{key:'Escape'});assert(e.defaultPrevented);assert(f.$('#results').hidden);assert.equal(f.$('#detail').getAttribute('inert'),null);assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');assert.equal(f.document.activeElement,f.$('#query'));
});

test('subsequent 1.38 zoom survives Back then Forward without adding a camera-only history entry',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');const count=f.historyStack.length;assert.equal(d.getState().camera.k,1.15);f.click('#plus');assert.equal(d.getState().camera.k,1.38);assert.equal(f.historyStack.length,count);
 f.goBack();assert.equal(d.getState().selected,null);f.goForward();assert.equal(d.getState().selected,'rpa-0062');assert.equal(d.getState().camera.k,1.38);assert.equal(f.historyStack.length,count);
});

test('user pointer pan and keyboard pan replace the current history snapshot',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');const count=f.historyStack.length;f.$('#field').emit('pointerdown',{button:0,clientX:500,clientY:400});f.window.emit('pointermove',{clientX:620,clientY:440});f.window.emit('pointerup');f.$('#field').emit('keydown',{key:'ArrowUp'});const view=JSON.stringify(d.getState().camera);assert.equal(f.historyStack.length,count);f.goBack();f.goForward();assert.equal(JSON.stringify(d.getState().camera),view);
});

test('20 repeated arrow keys and extreme pointer/wheel input share finite pan and zoom limits',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;for(let i=0;i<20;i++)f.$('#field').emit('keydown',{key:'ArrowLeft'});assert.equal(d.getState().camera.x,-1.3);for(let i=0;i<20;i++)f.$('#field').emit('keydown',{key:'ArrowUp'});assert.equal(d.getState().camera.y,-1);
 f.$('#field').emit('pointerdown',{button:0,clientX:500,clientY:400});f.window.emit('pointermove',{clientX:-1e9,clientY:-1e9});f.window.emit('pointerup');assert.equal(d.getState().camera.x,1.3);assert.equal(d.getState().camera.y,1);
 f.$('#field').emit('wheel',{deltaY:-1e6});assert(Number.isFinite(d.getState().camera.k));f.$('#field').emit('wheel',{deltaY:1e6});assert.equal(d.getState().camera.k,.65);assert.equal(f.historyStack.length,1);
});

test('malformed history camera cannot propagate null, NaN, Infinity or out-of-range values to render',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;
 for(const bad of [null,{x:NaN,y:Infinity,k:null},{x:-999,y:999,k:999},{x:'4',y:undefined,k:'2'},{x:0,y:0,k:-4}]){
  assert.doesNotThrow(()=>f.window.emit('popstate',{state:{atlasPreview:true,selected:'rpa-0062',camera:bad,filters:{query:42,task:null}}}));const c=d.getState().camera;assert(Object.values(c).every(Number.isFinite));assert(c.x>=-1.3&&c.x<=1.3&&c.y>=-1&&c.y<=1&&c.k>=.65&&c.k<=4);assert(!/NaN|Infinity|null/.test(f.$('#scale').textContent));
 }
 f.window.emit('popstate',{state:{atlasPreview:true,selected:'rpa-0062',camera:{x:NaN,y:Infinity,k:null}}});assert.equal(d.getState().camera.x,0);assert.equal(d.getState().camera.y,0);assert.equal(d.getState().camera.k,1);
});

test('selected-paper search and disclosure context survives immediate Back/Forward before the coalesced write',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');f.input('ODYSSEY');assert(!f.$('#results').hidden);const entries=f.historyStack.length;
 f.goBack();f.goForward();assert.equal(d.getState().selected,'rpa-0062');assert.equal(f.$('#query').value,'ODYSSEY');assert(!f.$('#results').hidden);assert.equal(f.$('#results').children.length,1);assert.equal(f.$('#detail').getAttribute('inert'),'');assert.equal(f.document.activeElement,f.$('#query'));assert.equal(f.historyStack.length,entries);
 f.click('#collapse');f.$('#method').value='WBC';f.$('#method').emit('change');f.goBack();f.goForward();assert.equal(f.$('#method').value,'WBC');assert.equal(f.$('#query').value,'ODYSSEY');assert(!f.$('#controls').classList.contains('collapsed'));assert(f.$('#results').hidden);
});

test('rapid pointer and wheel updates coalesce history writes while immediate Back/Forward retains the latest camera',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');const writes=f.historyWrites.length,entries=f.historyStack.length;
 f.$('#field').emit('pointerdown',{button:0,clientX:600,clientY:440});for(let i=1;i<=120;i++)f.window.emit('pointermove',{clientX:600+i,clientY:440+i/4});f.window.emit('pointerup');for(let i=0;i<30;i++)f.$('#field').emit('wheel',{deltaY:-1});
 const latest=JSON.stringify(d.getState().camera);assert(f.historyWrites.length-writes<=1);assert(f.timers.size<=1);assert.equal(f.historyStack.length,entries);
 f.goBack();f.goForward();assert.equal(JSON.stringify(d.getState().camera),latest);assert.equal(f.historyStack.length,entries);
 const beforeFlush=f.historyWrites.length;f.step(500);assert.equal(f.historyWrites.length,beforeFlush+1);assert.equal(JSON.stringify(f.context.history.state.camera),latest);assert.equal(f.timers.size,0);
});

test('leaving the page flushes the latest query/camera snapshot once and cancels a pending history timer',()=>{
 const f=fixture({reduced:true});f.window.AtlasDebug.select('rpa-0062');f.input('ODYSSEY');f.click('#plus');assert(f.timers.size<=1);const before=f.historyWrites.length;f.window.emit('pagehide');assert.equal(f.timers.size,0);assert.equal(f.historyWrites.length,before+1);assert.equal(f.context.history.state.filters.query,'ODYSSEY');assert.equal(f.context.history.state.camera.k,1.38);
});

test('the shipped type scale keeps primary controls readable and no supporting CSS text falls below 14px',()=>{
 const css=program.html.match(/<style>([\s\S]*?)<\/style>/)[1];
 const sizes=[...css.matchAll(/font-size:(\d+)px/g)].map(m=>Number(m[1]));assert(sizes.length>20);assert(sizes.every(n=>n>=14));
 assert.match(css,/\.search-row input\{font-size:18px/);assert.match(css,/\.status-row button\{font-size:16px;min-height:44px/);assert.match(css,/\.result-list button\{font-size:16px/);
 assert.match(css,/\.detail p,\.detail \.muted,\.relation \.evidence p\{font-size:18px/);assert.match(css,/\.links,\.evidence,\.relation button,\.relation details\{font-size:16px/);
 assert.match(css,/\.brand small\{font-size:14px/);assert.match(css,/\.detail h2\{font-size:22px/);assert.match(css,/\.detail h2\{font-size:20px/);
 const f=fixture({mobile:true,width:500,height:420,reduced:true});f.window.AtlasDebug.select('rpa-0062');assert(f.$('#brand').classList.contains('compact-hidden'));assert(f.$('#controls').classList.contains('compact-controls'));assert.equal(f.$('#mapNotes').parentElement.id,'filterPanel');
});

test('brand returns to the real catalog and a first-in-document skip link targets search',()=>{
 const f=fixture(),html=program.html;assert.equal(f.$('#catalogLink').getAttribute('href'),'../index.html#catalog');assert.match(f.$('#catalogLink').getAttribute('aria-label'),/返回论文目录/);assert.equal(f.$('#skipSearch').getAttribute('href'),'#query');
 assert(html.indexOf('id="skipSearch"')<html.indexOf('id="catalogLink"'));assert(html.indexOf('id="catalogLink"')<html.indexOf('id="field"'));assert(html.indexOf('id="field"')<html.indexOf('id="query"'));
 const url=f.location.href,event=f.$('#skipSearch').emit('click');assert(event.defaultPrevented);assert.equal(f.document.activeElement,f.$('#query'));assert.equal(f.location.href,url);
});

test('the graph has one sequential Tab stop; its 95 nodes and 8 evidence edges do not form a Tab gauntlet',()=>{
 const f=fixture({reduced:true}),field=f.$('#field');assert.equal(field.getAttribute('tabindex'),'0');assert.equal(f.$$('.node').length,95);assert(f.$$('.node').every(n=>n.getAttribute('tabindex')==='-1'));
 const isTab=e=>Number(e.getAttribute('tabindex'))>=0&&e.getAttribute('tabindex')!==null||e.tagName==='A'&&e.getAttribute('href')||['INPUT','BUTTON','SELECT'].includes(e.tagName);
 const ordered=f.$$(' *'.trim()).filter(e=>!e.closest('[hidden]')&&!e.closest('[inert]')&&!e.closest('.filter-panel')&&isTab(e));
 assert.deepEqual(ordered.slice(0,4).map(e=>e.id),['skipSearch','catalogLink','field','query']);
 f.window.AtlasDebug.select('rpa-0062');assert.equal(f.$$('.edge').length,8);assert(f.$$('.edge').every(e=>e.getAttribute('tabindex')==='-1'));assert.equal(field.querySelectorAll('[tabindex]').filter(e=>e.getAttribute('tabindex')==='0').length,0);
});

test('mouse node selection, keyboard reopening and Close focus restoration remain available without Tab-stopping every star',()=>{
 const f=fixture({reduced:true}),star=f.$('[data-id="rpa-0062"]');star.emit('click');assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');f.$('#detail').querySelector('button').emit('click');assert.equal(f.document.activeElement,star);assert.equal(star.getAttribute('tabindex'),'-1');
 const tab=star.emit('keydown',{key:'Tab'});assert(!tab.defaultPrevented);const enter=star.emit('keydown',{key:'Enter'});assert(enter.defaultPrevented);assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');
 f.$('#skipSearch').emit('click');f.input('ODYSSEY');f.$('#query').emit('keydown',{key:'ArrowDown'});const result=f.$('#results').querySelector('button');assert.equal(f.document.activeElement,result);result.emit('keydown',{key:'Enter'});assert.match(f.$('#detail').textContent,/ODYSSEY/);
});

test('detail leads with the existing short label while exact title and every method remain in a closed native disclosure',()=>{
 const f=fixture({reduced:true}),paper=program.data.papers.find(p=>p.id==='rpa-0062');f.window.AtlasDebug.select(paper.id);assert.equal(f.$('#detail').querySelector('h2').textContent,paper.label);
 const meta=f.$('#detail').querySelector('.paper-meta');assert.equal(meta.tagName,'DETAILS');assert.equal(meta.getAttribute('open'),null);assert.equal(meta.querySelector('.full-paper-title').textContent,paper.title);assert.equal(meta.querySelectorAll('.chip').length,paper.methods.length);assert.match(meta.querySelector('summary').textContent,/完整题名.*方法.*星图链接/);
 const star=f.$('[data-id="rpa-0062"]');assert(star.getAttribute('aria-label').includes(paper.title));
});

test('the verified-relation entry precedes metadata and jumps directly to a real related paper without changing selection',()=>{
 for(const options of [{reduced:true,width:1180,height:757},{reduced:true,mobile:true,width:500,height:420}]){
  const f=fixture(options);f.window.AtlasDebug.select('rpa-0062');const panel=f.$('#detail'),jump=panel.querySelector('.relation-jump'),meta=panel.querySelector('.paper-meta'),first=panel.querySelector('.relation').querySelector('button');
  assert(jump);assert.match(jump.textContent,/8 篇已核验关联 · 11 条记录/);assert(panel.children.indexOf(jump)<panel.children.indexOf(meta));assert.equal(panel.children.indexOf(jump),3);assert.equal(jump.getAttribute('aria-controls'),'related-rpa-0062');jump.emit('click');assert.equal(f.document.activeElement,first);assert(first.scrolled);assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0062');assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.evidence').length,12);
 }
});

test('unindexed papers retain honest relationship status and do not receive a fabricated relation entry',()=>{
 const f=fixture({reduced:true});f.window.AtlasDebug.select('rpa-0042');assert.equal(f.$('#detail').querySelector('.relation-jump'),null);assert.match(f.$('#detail').textContent,/关系尚未索引/);assert.equal(f.$$('.edge').length,0);assert(f.$('#detail').querySelector('.full-paper-title'));
});

test('deep-link patch preserves the accepted CSS and exact scientific data',()=>{
 const sha=value=>require('node:crypto').createHash('sha256').update(value).digest('hex'),css=program.html.match(/<style>([\s\S]*?)<\/style>/)[1];
 assert.equal(sha(css),'ef3a77811e454d09746be23aebf441cf6ceb655dfdda7a5433673a410867cb66');
 assert.equal(sha(program.html.match(/<script id="atlas-data" type="application\/json">([\s\S]*?)<\/script>/)[1]),'1ae66d5bd377cbc623dff58f71221a9fcdd6e902e37eadf850f53e45e8ff114c');
});

test('cold ?paper=rpa-0062 starts focused with all 95 papers and exactly the verified 8 pairs / 11 records',()=>{
 const url='https://example.org/RoboPaperAtlas/atlas-global-preview/?paper=rpa-0062',f=fixture({url,reduced:true}),d=f.window.AtlasDebug;
 assert.equal(d.getState().selected,'rpa-0062');assert.equal(d.getState().nodeCount,95);assert.equal(d.getState().matching.length,95);assert.equal(f.$$('.edge').length,8);assert.equal(f.$$('.relation').length,8);assert.equal(f.$$('.evidence').length,12);assert.equal(f.historyStack.length,1);assert.equal(f.location.href,url);assert.equal(d.getState().camera.k,1.15);assert.equal(f.raf.size,0);
});

test('the URL parser allowlists every current paper ID and rejects duplicates, case variants, empty and injected IDs',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;
 for(const p of program.data.papers)assert.equal(d.readPaperLocation('?paper='+encodeURIComponent(p.id)).id,p.id);
 for(const search of ['?paper=','?paper=RPA-0062','?paper=not-a-paper','?paper=rpa-0062&paper=rpa-0062','?paper=rpa-0062&paper=rpa-0013','?paper=%3Cimg%20src%3Dx%20onerror%3Dalert(1)%3E','?paper=javascript%3Aalert(1)']){assert.equal(d.readPaperLocation(search).id,null);assert.equal(d.readPaperLocation(search).invalid,true)}
 assert.equal(d.readPaperLocation('?paper=rpa%2D0062').id,'rpa-0062');assert.equal(d.readPaperLocation('').invalid,false);
});

test('invalid or duplicate cold-link IDs fall back to a clean 95-paper overview and ignore stale history selection',()=>{
 for(const search of ['?paper=not-a-paper','?paper=rpa-0062&paper=rpa-0013','?paper=%3Cscript%3E']){
  const f=fixture({url:'https://example.org/RoboPaperAtlas/atlas-global-preview/'+search+'&token=private#ignored',historyState:{atlasPreview:true,atlasEntry:7,selected:'rpa-0062',filters:{query:'ODYSSEY'},camera:{x:.2,y:.1,k:2}},reduced:true});
  assert.equal(f.window.AtlasDebug.getState().selected,null);assert.equal(f.window.AtlasDebug.getState().matching.length,95);assert.equal(f.$('#query').value,'');assert(f.$('#detail').hidden);assert.equal(f.$$('.edge').length,0);assert.equal(f.location.search,'');assert.equal(f.location.hash,'');assert.equal(f.historyStack.length,1);
 }
});

test('share URL is only the current origin/path and validated paper, without credentials, unknown parameters, hash, filters or camera',()=>{
 const f=fixture({url:'https://user:secret@example.org/RoboPaperAtlas/atlas-global-preview/?paper=rpa-0062&token=private&q=ODYSSEY&mode=debug#session-secret',reduced:true}),d=f.window.AtlasDebug;
 const expected='https://example.org/RoboPaperAtlas/atlas-global-preview/?paper=rpa-0062';assert.equal(d.paperURL('rpa-0062'),expected);assert.equal(f.$('#paperLink').value,expected);assert.equal(f.$('#paperLink').getAttribute('readonly'),'');f.$('#paperLink').focus();assert(f.$('#paperLink').selectionSelected);
 assert.equal(f.location.href,expected);assert.equal(d.paperURL('not-a-paper'),'https://example.org/RoboPaperAtlas/atlas-global-preview/');assert(!/clipboard|writeText|已复制/.test(program.source));
 const nested=fixture({url:'https://example.org//other.example/atlas/?paper=rpa-0062',reduced:true});assert.equal(new URL(nested.window.AtlasDebug.paperURL('rpa-0013')).origin,'https://example.org');
});

test('relationship navigation, Close and Overview update only paper selection on the canonical URL',()=>{
 const f=fixture({url:'https://example.org/atlas-global-preview/?paper=rpa-0062&unrelated=1#ignored',reduced:true}),d=f.window.AtlasDebug;
 f.$('#detail').querySelector('.relation').querySelector('button').emit('click');const other=d.getState().selected;assert.notEqual(other,'rpa-0062');assert.equal(new URL(f.location.href).searchParams.get('paper'),other);assert.equal(new URL(f.location.href).searchParams.size,1);
 f.$('#detail').querySelector('button').emit('click');assert.equal(d.getState().selected,null);assert.equal(f.location.search,'');assert.equal(f.location.hash,'');
 f.goBack();assert.equal(d.getState().selected,other);assert.equal(new URL(f.location.href).searchParams.get('paper'),other);f.goBack();assert.equal(d.getState().selected,'rpa-0062');
 f.click('#overview');assert.equal(f.location.search,'');assert.equal(d.getState().selected,null);
});

test('reload restores a matching selected-paper query, overlay and camera snapshot while URL wins over a mismatched snapshot',()=>{
 const url='https://example.org/atlas-global-preview/?paper=rpa-0062',f=fixture({url,reduced:true});f.input('ODYSSEY');f.click('#plus');f.window.emit('pagehide');const saved=JSON.parse(JSON.stringify(f.context.history.state));
 const reload=fixture({url:f.location.href,historyState:saved,reduced:true});assert.equal(reload.window.AtlasDebug.getState().selected,'rpa-0062');assert.equal(reload.$('#query').value,'ODYSSEY');assert(!reload.$('#results').hidden);assert.equal(reload.window.AtlasDebug.getState().camera.k,1.38);assert.equal(reload.$('#detail').getAttribute('inert'),'');
 const changed=fixture({url:'https://example.org/atlas-global-preview/?paper=rpa-0013',historyState:saved,reduced:true});assert.equal(changed.window.AtlasDebug.getState().selected,'rpa-0013');assert.equal(changed.$('#query').value,'');assert.equal(changed.window.AtlasDebug.getState().camera.k,1.15);
});

test('URL, selected paper and pending query/camera remain consistent through immediate Back/Forward',()=>{
 const f=fixture({url:'https://example.org/atlas-global-preview/?paper=rpa-0062',reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0013');f.input('ODYSSEY');f.click('#plus');const view=JSON.stringify(d.getState().camera),entries=f.historyStack.length;
 f.goBack();assert.equal(d.getState().selected,'rpa-0062');assert.equal(new URL(f.location.href).searchParams.get('paper'),'rpa-0062');
 f.goForward();assert.equal(d.getState().selected,'rpa-0013');assert.equal(new URL(f.location.href).searchParams.get('paper'),'rpa-0013');assert.equal(f.$('#query').value,'ODYSSEY');assert.equal(JSON.stringify(d.getState().camera),view);assert(!f.$('#results').hidden);assert.equal(f.historyStack.length,entries);
});

test('unowned or malformed popstate reads validated paper from URL and never selects a conflicting history ID',()=>{
 const f=fixture({url:'https://example.org/atlas-global-preview/?paper=rpa-0062',reduced:true});f.setURL('https://example.org/atlas-global-preview/?paper=rpa-0013&junk=1#secret');assert.equal(f.window.AtlasDebug.getState().selected,'rpa-0013');assert.equal(f.location.hash,'');assert.equal(new URL(f.location.href).searchParams.size,1);
 f.setURL('https://example.org/atlas-global-preview/?paper=not-allowed');assert.equal(f.window.AtlasDebug.getState().selected,null);assert.equal(f.window.AtlasDebug.getState().matching.length,95);assert.equal(f.location.search,'');
});

test('reselecting the same paper keeps one URL entry and stores the resulting closed-overlay focus camera',()=>{
 const f=fixture({reduced:true}),d=f.window.AtlasDebug;d.select('rpa-0062');f.click('#plus');f.input('ODYSSEY');const entries=f.historyStack.length;d.select('rpa-0062');assert.equal(f.historyStack.length,entries);assert(f.$('#results').hidden);assert.equal(d.getState().camera.k,1.15);
 f.goBack();f.goForward();assert.equal(d.getState().selected,'rpa-0062');assert.equal(d.getState().camera.k,1.15);assert.equal(f.$('#query').value,'ODYSSEY');assert(f.$('#results').hidden);assert.equal(new URL(f.location.href).searchParams.get('paper'),'rpa-0062');
});

test('non-web environments do not expose a local/private share URL or claim a successful clipboard operation',()=>{
 const f=fixture({url:'file:///tmp/example-atlas.html?paper=rpa-0062',reduced:true});assert.equal(f.window.AtlasDebug.paperURL('rpa-0062'),null);assert.equal(f.$('#paperLink'),null);assert.match(f.$('#detail').textContent,/无法生成网页分享链接/);assert(!f.$('#detail').textContent.includes('file:///'));assert(!f.$('#detail').textContent.includes('已复制'));
});
