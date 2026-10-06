'use strict';
// Deliberately a deterministic in-memory DOM contract, not a browser or visual renderer.
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
function fixture(options={}){
 const root=path.resolve(__dirname,'..');let document,url=new URL(options.url||'https://example.test/local-only/');
 const decode=s=>s.replace(/&(?:amp|lt|gt|quot|#39);/g,x=>({'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&#39;':"'"}[x]));
 class Element{
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.dataset={};this.parentElement=null;this.listeners={};this._text='';this._html='';this.value='';this.scrollTop=0;this.style={};this.classList={contains:n=>this.className.split(/\s+/).includes(n),toggle:(n,on)=>{const names=new Set(this.className.split(/\s+/).filter(Boolean));on?names.add(n):names.delete(n);this.className=[...names].join(' ')}};}
  get id(){return this.attributes.id||'';}get className(){return this.attributes.class||'';}set className(v){this.attributes.class=String(v);}
  get hidden(){return 'hidden'in this.attributes;}set hidden(v){v?this.setAttribute('hidden',''):this.removeAttribute('hidden');}
  get disabled(){return 'disabled'in this.attributes;}get textContent(){return this._text+this.children.map(c=>c.textContent).join('');}set textContent(v){this.children=[];this._text=String(v);}
  get innerHTML(){return this._html;}set innerHTML(v){this.children=[];this._text='';this._html=String(v);parseInto(this,String(v));}
  setAttribute(k,v){this.attributes[k]=String(v);if(k.startsWith('data-'))this.dataset[k.slice(5).replace(/-([a-z])/g,(_,c)=>c.toUpperCase())]=String(v);}getAttribute(k){return this.attributes[k]??null;}removeAttribute(k){delete this.attributes[k];}
  appendChild(el){el.parentElement=this;this.children.push(el);return el;}
  matches(selector){selector=selector.trim();if(selector.includes(','))return selector.split(',').some(s=>this.matches(s));const attrs=[...selector.matchAll(/\[([^=\]]+)(?:=["']?([^\]"']+)["']?)?\]/g)];if(!attrs.every(([,k,v])=>k in this.attributes&&(v===undefined||this.attributes[k]===v)))return false;selector=selector.replace(/\[[^\]]+\]/g,'');const id=selector.match(/#([\w-]+)/);if(id&&this.id!==id[1])return false;for(const [,c]of selector.matchAll(/\.([\w-]+)/g))if(!this.classList.contains(c))return false;const tag=selector.match(/^[\w-]+/);return !tag||tag[0].toUpperCase()===this.tagName;}
  querySelectorAll(s){const out=[];const walk=e=>{for(const c of e.children){if(c.matches(s))out.push(c);walk(c);}};walk(this);return out;}querySelector(s){return this.querySelectorAll(s)[0]||null;}closest(s){let el=this;while(el){if(el.matches(s))return el;el=el.parentElement;}return null;}
  addEventListener(k,fn){(this.listeners[k]??=[]).push(fn);}emit(k,input={}){const ev={type:k,target:this,preventDefault(){this.defaultPrevented=true;},...input};let at=this;while(at){for(const fn of at.listeners[k]||[])fn(ev);at=at.parentElement;}return ev;}
  focus(){document.activeElement=this;}scrollIntoView(){this.scrolled=true;}
 }
 function parseInto(parent,html){const stack=[parent],voids=new Set(['meta','link','input','br','hr','img']);for(const m of html.matchAll(/<([^>]+)>|([^<]+)/g)){if(m[2]){const t=new Element('#text');t._text=decode(m[2]);stack.at(-1).appendChild(t);continue;}const tag=m[1];if(tag.startsWith('!'))continue;if(tag.startsWith('/')){if(stack.length>1)stack.pop();continue;}const name=tag.split(/\s/)[0].replace(/\/$/,'');const el=new Element(name);for(const a of tag.slice(name.length).matchAll(/([^\s=\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s]+)))?/g))el.setAttribute(a[1],decode(a[2]??a[3]??a[4]??''));stack.at(-1).appendChild(el);if(!voids.has(name)&&!tag.endsWith('/'))stack.push(el);}}
 document=new Element('#document');document.activeElement=null;document.getElementById=id=>document.querySelector('#'+id);parseInto(document,fs.readFileSync(path.join(root,'index.html'),'utf8'));
 const window=new Element('#window');window.document=document;document.defaultView=window;document.body=document.querySelector('body');window.innerWidth=options.width||1448;window.innerHeight=options.height||1088;window.scrollY=0;window.scrollTo=(x,y)=>window.scrollY=y;window.matchMedia=q=>({matches:q.includes('max-width')?!!options.mobile:false});const stack=[url.href],states=[null];let i=0;
 window.location={get hash(){return url.hash;}};window.history={pushState(state,__,value){url=new URL(value,url);stack.splice(++i);stack.push(url.href);states.splice(i);states.push(state);},replaceState(state,__,value){url=new URL(value,url);stack[i]=url.href;states[i]=state;}};
 const errors=[],context={window,document,URL,Map,Set,JSON,setTimeout,clearTimeout,console:{error:e=>errors.push(String(e))}};
 for(const file of ['data/catalog.js','data/literature.js','data/challenge.js','model.js','app.js','analysis/data/bundle.js','analysis/model.js','analysis/c2.js'])vm.runInNewContext(fs.readFileSync(path.join(root,file),'utf8'),context,{filename:file});
 return {document,window,errors,historyStack:stack,app:window.NavigationPrototype,c2:window.AnalysisC2,$:s=>document.querySelector(s),$$:s=>document.querySelectorAll(s),click(s){const el=document.querySelector(s);if(!el)throw Error('Missing '+s);el.emit('click');return el;},back(){if(i){url=new URL(stack[--i]);window.emit('popstate',{state:states[i]});}},forward(){if(i+1<stack.length){url=new URL(stack[++i]);window.emit('popstate',{state:states[i]});}},url:()=>url.href};
}
module.exports={fixture};
