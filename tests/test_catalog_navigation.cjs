'use strict';
const {test}=require('node:test'),assert=require('node:assert/strict');
const api=require('../assets/catalog-navigation.js'),{fixture}=require('./map_dom_fixture.cjs');
const make=query=>{const f=fixture({htmlFile:'dist/index.html',url:'https://example.org/RoboPaperAtlas/index.html'+query});f.$$('option').forEach(o=>o.value=o.getAttribute('value')||'');f.runAsset('catalog-navigation.js');f.runAsset('app.js');return f};
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
 const f=make('?q=UMI#catalog');f.$('#sort').value='title';f.$('#sort').emit('change');f.click('[data-view="list"]');
 let query=new URL(href(f),'https://example.org/RoboPaperAtlas/').searchParams.get('catalog');assert.equal(new URLSearchParams(query).get('sort'),'title');assert.equal(new URLSearchParams(query).get('view'),'list');
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

test('all nine current views decorate their actual paper-return control, including UMI branded links',()=>{
 for(const paper of ['rpa-0012','rpa-0052','rpa-0062'])for(const stage of ['stage1','stage2','stage3']){
  const f=fixture({htmlFile:`dist/papers/${paper}/reading/${stage}.html`,url:`https://example.org/RoboPaperAtlas/papers/${paper}/reading/${stage}.html?catalog=q%3Drobot`});f.runAsset('catalog-navigation.js');
  const back=f.$('.atlas-return')||f.$('.reader-paper-link');assert.equal(back.getAttribute('href'),'../index.html?catalog=q%3Drobot#reading',paper+' '+stage);
  if(paper==='rpa-0062'&&stage!=='stage2'){const crumb=f.$('.reader-breadcrumb').querySelector('a');assert.equal(crumb.getAttribute('href'),'../index.html?catalog=q%3Drobot#reading');assert.equal(crumb.getAttribute('class'),'atlas-return');}
  f.setURL('?');assert.equal(back.getAttribute('href'),'../index.html#reading');
 }
});
