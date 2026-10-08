'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const code = fs.readFileSync(path.join(__dirname,'../previews/objectnav-reading-v1/reader.js'),'utf8');
function fixture(hash) {
  const events = {}, clicks = {};
  const parent = {tagName:'DETAILS',open:false,parentElement:null};
  const target = {tagName:'ARTICLE',parentElement:parent,attrs:{},focusCount:0,scrollCount:0,
    hasAttribute(k){return k in this.attrs;},setAttribute(k,v){this.attrs[k]=v;},
    focus(o){assert.equal(o.preventScroll,true);this.focusCount++;},
    scrollIntoView(o){assert.equal(o.behavior,'auto');this.scrollCount++;}};
  const second={...target,parentElement:null,attrs:{},focusCount:0,scrollCount:0};
  const window={location:{hash},addEventListener(k,fn){events[k]=fn;}};
  const document={getElementById(id){return {'analysis-ablation-core':target,comparison:second}[id]||null;},addEventListener(k,fn){clicks[k]=fn;}};
  vm.runInNewContext(code,{window,document});return{window,events,clicks,target,parent,second};
}
let f=fixture('#analysis-ablation-core');
assert.equal(f.parent.open,true);assert.equal(f.target.focusCount,1);assert.equal(f.target.attrs.tabindex,'-1');
f.window.location.hash='#comparison';f.events.hashchange();assert.equal(f.second.focusCount,1);
f.window.location.hash='#analysis-ablation-core';f.parent.open=false;f.events.hashchange();assert.equal(f.parent.open,true);assert.equal(f.target.focusCount,2);
f.clicks.click({target:{closest(){return{getAttribute(){return '#analysis-ablation-core';}};}}});assert.equal(f.target.focusCount,3);
f.events.pageshow({persisted:true});assert.equal(f.target.focusCount,3);
f.events.pageshow({persisted:false});assert.equal(f.target.focusCount,4);
for(const hash of ['','#does-not-exist','#%E0%A4%A','#%3Cscript%3E']){const g=fixture(hash);assert.equal(g.target.focusCount,0);assert.equal(g.parent.open,false);}
console.log('ObjectNav reader: deep-link expansion, focus, repeated anchor, history hash transitions, bfcache preservation, malformed/unknown hashes PASS (DOM fixture, not real browser).');
