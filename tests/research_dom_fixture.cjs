'use strict';
// Adapt existing deterministic DOM test fixture to actual HTML script loading. Not a browser.
const fs=require('node:fs'),path=require('node:path'),Module=require('node:module');
module.exports=function actualFixture(root,options={}){
 const base=path.join(root,'previews/radar-c2-analysis'),file=path.join(root,'tests/fixtures/radar-c2-analysis/analysis/tests/dom_fixture.cjs');
 let text=fs.readFileSync(file,'utf8');
 const scripts=[...fs.readFileSync(base+'/index.html','utf8').matchAll(/<script[^>]*src="([^\"]+)"/g)].map(x=>x[1].split('?')[0]);
 text=text.replace("const root=path.resolve(__dirname,'../..');",'const root='+JSON.stringify(base)+';');
 text=text.replace(/for\(const file of \['data\/catalog.js'[^\n]*?\]\)/,'for(const file of '+JSON.stringify(scripts)+')');
 const m=new Module(file,module);m.filename=file;m.paths=module.paths;m._compile(text,file);return m.exports.fixture(options);
};
module.exports.visibleText=function visibleText(el){if(!el||el.hidden)return '';if(el.tagName==='DETAILS'&&!('open' in el.attributes))return visibleText(el.children.find(c=>c.tagName==='SUMMARY'));return (el._text||'')+' '+el.children.map(visibleText).join(' ');};
