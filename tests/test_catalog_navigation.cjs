'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const api=require('../assets/catalog-navigation.js'),{fixture}=require('./map_dom_fixture.cjs');
const presentation=require('../assets/presentation.js'),papers=require('../data/catalog.json').papers;
const importedPapers=papers.filter(p=>Object.values(p.stages).some(s=>s.status==='imported'));
const importedStages=papers.reduce((n,p)=>n+Object.values(p.stages).filter(s=>s.status==='imported').length,0);
// Deterministic controller model. This does not establish native browser layout,
// focus trapping or real History API scheduling.
const make=(query='',storage=new Map())=>{
 const f=fixture({htmlFile:'dist/index.html',url:'https://example.org/RoboPaperAtlas/index.html'+query});
 f.$$('option').forEach(o=>o.value=o.getAttribute('value')||'');
 let sequence=0;const timers=new Map();
 f.context.setTimeout=(callback,ms)=>{timers.set(++sequence,{callback,ms});return sequence};
 f.context.clearTimeout=id=>timers.delete(id);
 f.flushTimers=()=>{const pending=[...timers.values()];timers.clear();pending.forEach(x=>x.callback())};f.timers=timers;
 f.window.scrollY=0;f.window.scrollTo=options=>{f.window.scrollY=options.top};
 f.window.sessionStorage={getItem:key=>storage.get(key)||null,setItem:(key,value)=>storage.set(key,String(value))};
 const history=f.window.history,push=history.pushState.bind(history),replace=history.replaceState.bind(history),back=f.goBack.bind(f),forward=f.goForward.bind(f),emit=f.window.emit.bind(f.window);
 const states=[null];let position=0;const copy=value=>value==null?value:JSON.parse(JSON.stringify(value));
 Object.defineProperty(history,'state',{get:()=>copy(states[position])});
 history.pushState=(state,unused,url)=>{push(state,unused,url);states.splice(++position);states.push(copy(state))};
 history.replaceState=(state,unused,url)=>{replace(state,unused,url);states[position]=copy(state)};
 f.goBack=()=>{if(position){position--;back()}};
 f.goForward=()=>{if(position+1<states.length){position++;forward()}};
 f.window.emit=(type,event={})=>emit(type,type==='popstate'?{state:history.state,...event}:event);
 f.runAsset('catalog-navigation.js');f.runAsset('app.js');return f;
};
const visible=f=>f.$$('.paper-card').filter(card=>!card.hidden);
const select=(f,id,value)=>{f.$(id).value=value;f.$(id).emit('change')};
const href=f=>f.$('.paper-card').querySelector('h3').querySelector('a').getAttribute('href');
test('catalogue detail and reading links retain q, filters, sort and view in bounded state',()=>{
 const q='?q=AgenticNav&topic=navigation-space&direction=navigation&method=VLM&year=2026&status=verified&sort=title&view=list&resource=dataset';
 const f=make(q),detail=href(f),encoded=new URL(detail,'https://example.org/RoboPaperAtlas/').searchParams.get('catalog');
 assert.equal(api.cleanQuery(q),encoded);
 const returnUrl=api.backHref('../../',new URL(detail,'https://example.org/RoboPaperAtlas/').search);
 assert.equal(returnUrl,'../../index.html?'+api.cleanQuery(q)+'#catalog');
 const reading=f.$('.card-report-link').getAttribute('href');assert(reading.endsWith('#reading'));assert(reading.includes('?catalog='));
});
test('changed filter, sort, view and back/popstate update existing detail hrefs without stale queries',()=>{
 const f=make('?q=UMI#catalog');f.$('#sort').value='title';f.$('#sort').emit('change');f.click('[data-view="cards"]');
 let query=new URL(href(f),'https://example.org/RoboPaperAtlas/').searchParams.get('catalog');assert.equal(new URLSearchParams(query).get('sort'),'title');assert.equal(new URLSearchParams(query).get('view'),'cards');
 f.setURL('?q=AgenticNav#catalog');query=new URL(href(f),'https://example.org/RoboPaperAtlas/').searchParams.get('catalog');assert.equal(query,'q=AgenticNav');
 f.click('#reset-filters');query=new URL(href(f),'https://example.org/RoboPaperAtlas/').searchParams.get('catalog');assert(!new URLSearchParams(query).has('q'));
});
test('direct paper access defaults to catalogue; encoded state decorates only marked detail back link',()=>{
 for(const search of ['', '?paper=x','?catalog='])assert.equal(api.backHref('../../',search),'../../index.html#catalog');
 const f=fixture({htmlFile:'dist/papers/agenticnav-tool-harness/index.html',url:'https://example.org/RoboPaperAtlas/papers/agenticnav-tool-harness/index.html?catalog=q%3DAgenticNav%26view%3Dlist'});f.runAsset('catalog-navigation.js');
 assert.equal(f.$('[data-catalog-back]').getAttribute('href'),'../../index.html?q=AgenticNav&view=list#catalog');
});
test('malicious destinations, unknown parameters, duplicate keys and control characters cannot redirect',()=>{
 for(const input of ['https://evil.example/x','//evil.example/x','javascript:alert(1)','return=https://evil.example&redirect=//evil.example','q=%00bad','q='+('a'.repeat(513))])assert.equal(api.backHref('../../','?catalog='+encodeURIComponent(input)),'../../index.html#catalog');
 const back=api.backHref('../../','?catalog='+encodeURIComponent('q=//evil.example&next=https://evil.example&view=bad&sort=bad&q=second'));
 assert.equal(back,'../../index.html?q=%2F%2Fevil.example#catalog');
 assert.equal(api.cleanQuery('q='+('x'.repeat(5000))),'');
 assert.equal(api.paperHref('papers/rpa-0012/index.html#reading','q=UMI'),'papers/rpa-0012/index.html?catalog=q%3DUMI#reading');
 for(const url of ['https://evil.example/x','//evil.example/papers/x/index.html','papers/../index.html','papers/rpa-0012/reading/stage1.html'])assert.equal(api.paperHref(url,'q=UMI'),url);
});
test('all current reader stages retain validated catalog context through repeated return journeys',()=>{
 const query='?catalog='+encodeURIComponent('q=RoboDuet&direction=manipulation&sort=title&view=list');
 const detail=fixture({htmlFile:'dist/papers/rpa-0052/index.html',url:'https://example.org/RoboPaperAtlas/papers/rpa-0052/index.html'+query});detail.runAsset('catalog-navigation.js');
 const anchors=detail.$('.stage-slots').querySelectorAll('a');
 for(const stage of ['stage1','stage2','stage3']){
  const href=anchors.find(a=>a.getAttribute('href').includes('/reading/'+stage)).getAttribute('href');assert.equal(new URL(href,'https://example.org/RoboPaperAtlas/').search,query);
  const f=fixture({htmlFile:'dist/papers/rpa-0052/reading/'+stage+'.html',url:'https://example.org/RoboPaperAtlas/papers/rpa-0052/reading/'+stage+'.html'+query});f.runAsset('catalog-navigation.js');
  for(const a of f.$('.reader-stages').querySelectorAll('a'))assert.equal(new URL(a.getAttribute('href'),'https://example.org/RoboPaperAtlas/').search,query);
  assert.equal(f.$('.atlas-return').getAttribute('href'),'../index.html'+query+'#reading');
  f.setURL('?catalog='+encodeURIComponent('q=UMI'));assert.equal(f.$('.atlas-return').getAttribute('href'),'../index.html?catalog=q%3DUMI#reading');
  f.setURL('?');assert.equal(f.$('.atlas-return').getAttribute('href'),'../index.html#reading');
 }
});
test('reader state never decorates history or accepts caller-supplied destinations',()=>{
 const search='?catalog='+encodeURIComponent('q=<script>alert(1)</script>&next=//evil.example&view=list');
 for(const href of ['stage1.html','stage2.html?catalog=stale','stage3.html','../index.html#reading','../../papers/rpa-0052/reading/stage3.html']){
  const out=api.readerHref(href,search),url=new URL(out,'https://example.org/RoboPaperAtlas/papers/rpa-0052/reading/');assert.equal(url.origin,'https://example.org');assert.equal(new URLSearchParams(url.searchParams.get('catalog')).get('q'),'<script>alert(1)</script>');assert(!out.includes('<script>'));assert(!out.includes('next='));assert.equal(api.readerHref(out,search),out);
 }
 for(const href of ['../../../artifacts/rpa-0052/v1/first-pass.html','https://evil.example/stage1.html','//evil.example/stage1.html','javascript:alert(1)','../stage3.html','stage4.html','stage1.html#bad/fragment'])assert.equal(api.readerHref(href,search),href);
 for(const query of ['q=%00bad','q='+('x'.repeat(513)),'next=//evil.example'])assert.equal(api.readerHref('stage1.html','?catalog='+encodeURIComponent(query)),'stage1.html');
});

test('all current views decorate their actual paper-return control, including UMI branded links',()=>{
 for(const p of importedPapers)for(const report of presentation.currentReports(p)){
  const paper=p.id,stage=report.stage;
  const f=fixture({htmlFile:`dist/papers/${paper}/reading/${stage}.html`,url:`https://example.org/RoboPaperAtlas/papers/${paper}/reading/${stage}.html?catalog=q%3Drobot`});f.runAsset('catalog-navigation.js');
  const back=f.$('.atlas-return')||f.$('.reader-paper-link');assert.equal(back.getAttribute('href'),'../index.html?catalog=q%3Drobot#reading',paper+' '+stage);
  if(paper==='rpa-0062'&&stage!=='stage2'){const crumb=f.$('.reader-breadcrumb').querySelector('a');assert.equal(crumb.getAttribute('href'),'../index.html?catalog=q%3Drobot#reading');assert.equal(crumb.getAttribute('class'),'atlas-return');}
  f.setURL('?');assert.equal(back.getAttribute('href'),'../index.html#reading');
 }
});

test('Library default list and five discrete filter changes are reversible without duplicate entries',()=>{
 const f=make();assert(f.$('#paper-grid').classList.contains('list-view'));
 f.click('[data-topic="all"]');f.click('[data-view="list"]');assert.equal(f.historyStack.length,1);
 f.click('[data-topic="robot-learning"]');select(f,'#method-filter','VLA');select(f,'#year-filter','2025');select(f,'#sort','title');f.click('[data-view="cards"]');
 assert.equal(f.historyStack.length,6);assert.equal(new URLSearchParams(f.location.search).get('view'),'cards');
 f.goBack();assert(f.$('#paper-grid').classList.contains('list-view'));assert.equal(f.$('#sort').value,'title');
 f.goBack();assert.equal(f.$('#sort').value,'curated');assert.equal(f.$('#year-filter').value,'2025');
 f.goBack();assert.equal(f.$('#year-filter').value,'all');assert.equal(f.$('#method-filter').value,'VLA');
 f.goBack();assert.equal(f.$('#method-filter').value,'all');assert.equal(new URLSearchParams(f.location.search).get('topic'),'robot-learning');
 f.goBack();assert.equal(visible(f).length,24);assert.equal(new URLSearchParams(f.location.search).get('topic'),null);
 f.goForward();assert.equal(new URLSearchParams(f.location.search).get('topic'),'robot-learning');
});

test('loaded results and scroll survive Back and explicit detail-return navigation',()=>{
 const storage=new Map(),f=make('?view=cards#catalog',storage);f.click('#load-more');assert.equal(visible(f).length,48);assert.equal(f.historyStack.length,1);
 f.window.scrollY=915;select(f,'#method-filter','VLA');f.goBack();assert.equal(visible(f).length,48);assert.equal(f.window.scrollY,915);
 f.window.emit('pagehide');const returned=make('?view=cards#catalog',storage);assert.equal(visible(returned).length,48);assert.equal(returned.window.scrollY,915);
});

test('debounced search respects IME, cancels pending Back work and cannot collapse cleared results later',()=>{
 const f=make(),input=f.$('#search');input.focus();input.emit('compositionstart');input.value='机器人';input.emit('input');assert.equal(f.timers.size,0);
 const escape=input.emit('keydown',{key:'Escape',isComposing:true});assert(!escape.defaultPrevented);assert.equal(input.value,'机器人');
 input.emit('compositionend');assert.equal(f.timers.size,1);assert([...f.timers.values()].every(x=>x.ms>=150&&x.ms<=200));f.flushTimers();assert.equal(new URLSearchParams(f.location.search).get('q'),'机器人');
 input.value='UMI';input.emit('input');f.goBack();f.flushTimers();assert.equal(input.value,'');assert.equal(f.historyStack.length,2);assert.equal(f.location.search,'');
 input.value='robot';input.emit('input');f.flushTimers();input.value='robotics';input.emit('input');f.$('#active-filters').querySelector('button').emit('click');f.click('#load-more');f.flushTimers();assert.equal(visible(f).length,48);
});

test('reading state stays separate from source status and editorial links carry current context',()=>{
 const f=make('?view=cards#catalog');select(f,'#reading-filter','imported');assert.equal(visible(f).length,importedPapers.length);assert.equal(f.$('#status-filter').value,'all');
 select(f,'#status-filter','pending');assert.equal(visible(f).length,importedPapers.filter(p=>!p.citation_verified).length);select(f,'#status-filter','verified');const verified=importedPapers.filter(p=>p.citation_verified).length;assert.equal(visible(f).length,verified);assert.equal(f.$('#empty-state').hidden,verified!==0);
 const feature=f.$('[data-catalog-link]'),query=new URL(feature.getAttribute('href'),'https://example.org/').searchParams.get('catalog');assert.equal(new URLSearchParams(query).get('reading'),'imported');assert.equal(new URLSearchParams(query).get('view'),'cards');
 assert.equal(api.cleanQuery('reading=bogus'),'');assert.equal(api.cleanQuery('reading=imported'),'reading=imported');assert.equal(api.cleanQuery('reading=not-imported'),'reading=not-imported');
});

test('all report quick-view entries use current readers without changing immutable source identities',()=>{
 const reports=papers.flatMap(p=>presentation.currentReports(p));assert.equal(reports.length,importedStages);
 for(const paper of importedPapers)assert.equal(reports.filter(r=>r.path.includes('/'+paper.id+'/')).length,Object.values(paper.stages).filter(s=>s.status==='imported').length);
 const search='?catalog='+encodeURIComponent('q=robot&reading=imported&view=cards');
 for(const report of reports){assert.match(report.path,/^papers\/[a-z0-9-]+\/reading\/stage[123]\.html$/);const href=api.readerHref(report.path,search);assert.equal(new URLSearchParams(new URL(href,'https://example.org/').searchParams.get('catalog')).get('reading'),'imported')}
 for(const paper of papers)for(const stage of Object.values(paper.stages))for(const artifact of stage.artifacts)assert.equal(api.readerHref(artifact.path,search),artifact.path);
});

// The final load button disappears; focus must follow the current sorted results.
test('last load-more batch focuses its first new result after title/year/reading filters',()=>{
 for(const query of ['?sort=title#catalog','?sort=newest&year=unknown#catalog','?sort=title&year=unknown&reading=not-imported#catalog']){
  const f=make(query),visible=()=>f.$$('.paper-card').filter(c=>!c.hidden);
  assert(!f.$('#load-more').hidden,query+' must exercise another batch');
  let batches=0;
  while(!f.$('#load-more').hidden){
   const previous=new Set(visible());f.click('#load-more');batches++;
   const added=visible().filter(card=>!previous.has(card));assert(added.length>0);
   if(f.$('#load-more').hidden)assert.equal(f.document.activeElement,added[0].querySelector('h3').querySelector('a'),query);
   assert(batches<10);
  }
 }
});

test('load-more and view changes commit a pending search at its first batch',()=>{
 for(const action of ['#load-more','[data-view="cards"]']){
  const f=make('#catalog');f.click('#load-more');assert.equal(visible(f).length,48);
  const input=f.$('#search');input.value='robot';input.emit('input');f.click(action);
  assert(new URLSearchParams(f.location.search).get('q')==='robot');assert(visible(f).length<=24);
  const count=visible(f).length;f.flushTimers();assert.equal(visible(f).length,count);
  if(action==='#load-more')assert.equal(f.document.activeElement,input);
 }
});

test('overlong search is normalized before matching and round-trips to the same results',()=>{
 const f=make('#catalog'),input=f.$('#search');input.value='robot'+' '.repeat(507)+'nonexistentxyz';input.emit('input');f.flushTimers();
 assert.equal(input.value.length,512);const initial=visible(f).map(c=>c.dataset.title),url=f.location.search;
 const restored=make(url+'#catalog');assert.deepEqual(visible(restored).map(c=>c.dataset.title),initial);
 assert.equal(new URLSearchParams(url).get('q'),'robot');
});

test('encoded Chinese queries fit the bounded envelope without weakening decoded limits',()=>{
 const query=new URLSearchParams({q:'机'.repeat(512),reading:'imported',view:'cards'}).toString();
 assert(query.length>4096);assert.equal(new URLSearchParams(api.cleanQuery(query)).get('q'),'机'.repeat(512));
 assert.equal(api.cleanQuery(new URLSearchParams({q:'机'.repeat(513)}).toString()),'');
 assert.equal(api.cleanQuery('q='+('x'.repeat(8192))), '');
});
