'use strict';
// Production rendering fragments, not browser geometry or complete app startup.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const root=path.resolve(__dirname,'..'),source=fs.readFileSync(path.join(root,'assets/navigation-product.js'),'utf8'),model=fs.readFileSync(path.join(root,'assets/navigation-product-model.js'),'utf8');
const fixtures=JSON.parse(fs.readFileSync(path.join(__dirname,'fixtures/navigation_relation_locator.json'),'utf8'));
function declaration(text,name){const line=text.split('\n').find(x=>x.startsWith('function '+name+'('));assert.ok(line,name);return line;}
class Node {
 constructor(tag){this.tagName=tag;this.children=[];this.attributes={};this.value='';}
 appendChild(n){this.children.push(n);return n;}
 setAttribute(k,v){this.attributes[k]=v;}
 set textContent(v){this.value=String(v);this.children=[];}
 get textContent(){return this.value+this.children.map(n=>n.textContent).join('');}
 set innerHTML(_){throw Error('HTML interpretation is forbidden');}
}
const document={createElement:tag=>new Node(tag),createTextNode:text=>{const n=new Node('#text');n.textContent=text;return n;}};
const context=vm.createContext({document,URL});
const start=source.indexOf('function relationLocatorURL('),end=source.indexOf('function statusText(',start);
assert.ok(start>=0&&end>start,'production locator renderer missing');
vm.runInContext(declaration(model,'safeURL')+'\nvar M={safeURL};\n'+declaration(source,'el')+'\n'+source.slice(start,end),context);
function render(raw,index=0){const host=new Node('article');context.addRelationLocator(host,raw,index);assert.equal(host.children.length,1);return host.children[0];}
function links(p){return p.children.filter(n=>n.tagName==='a').map(n=>({text:n.textContent,url:n.attributes.href,target:n.attributes.target,rel:n.attributes.rel}));}
for(const fixture of fixtures)test('locator render: '+fixture.name,()=>{
 const p=render(fixture.raw,3);assert.equal(p.tagName,'p');assert.equal(p.attributes['data-task-relation-locator'],fixture.raw);assert.equal(p.attributes['data-task-relation-locator-index'],'3');
 assert.equal(p.textContent,fixture.expected.text);assert.deepEqual(links(p),fixture.expected.links);
 assert.ok(p.children.every(n=>n.tagName==='#text'||n.tagName==='a'));assert.ok(p.children.every(n=>n.children.length===0),'no hidden suffix or HTML nodes');
});
test('all source locator records remain immutable and wiring uses indexed renderer',()=>{
 const inventory=JSON.parse(source.match(/var TASK_READING_RELATIONS=(\[.*\]);/)[1]);const before=JSON.stringify(inventory);assert.equal(inventory.length,7);
 for(const relation of inventory)relation.locators.forEach((loc,index)=>{const p=render(loc.locator,index);assert.equal(p.attributes['data-task-relation-locator'],loc.locator);});
 assert.equal(JSON.stringify(inventory),before);
 assert.ok(source.includes('list(rel.locators).forEach(function(loc,index){addRelationLocator(row,loc.locator,index);'));
});
