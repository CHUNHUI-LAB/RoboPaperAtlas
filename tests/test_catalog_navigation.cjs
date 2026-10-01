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
