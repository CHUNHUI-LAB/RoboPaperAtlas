'use strict';
// Minimal deterministic DOM model for behavioral tests, not a rendering engine.
// It parses the real generated map HTML and executes the production JS unchanged.
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function fixture(options={}){
 const rootDir=path.join(__dirname,'..');let now=0,url=new URL(options.url||'https://example.org/prototype/');
 let sequence=0;const raf=new Map(),timers=new Map(),historyWrites=[],observers=[],resizers=[],media={};let document;
 const decode=s=>s.replace(/&(?:amp|lt|gt|quot|#x27|#39);/g,x=>({'&amp;':'&','&lt;':'<','&gt;':'>','&quot;':'"','&#x27;':"'",'&#39;':"'"}[x]));
 class Element{
  constructor(tag){this.tagName=tag.toUpperCase();this.children=[];this.attributes={};this.parentElement=null;this.listeners={};this._text='';this.value='';this.scrollTop=0;this.style={setProperty(k,v){this[k]=v;}};
   this.dataset=new Proxy({}, {get:(_,key)=>this.getAttribute('data-'+String(key).replace(/[A-Z]/g,m=>'-'+m.toLowerCase())),set:(_,key,value)=>{this.setAttribute('data-'+String(key).replace(/[A-Z]/g,m=>'-'+m.toLowerCase()),value);return true}});
   this.classList={contains:n=>this.className.split(/\s+/).includes(n),add:(...names)=>{this.className=[...new Set([...this.className.split(/\s+/).filter(Boolean),...names])].join(' ')},remove:(...names)=>{this.className=this.className.split(/\s+/).filter(n=>!names.includes(n)).join(' ')},toggle:(n,force)=>{let b=force===undefined?!this.classList.contains(n):force;b?this.classList.add(n):this.classList.remove(n);return b}};
  }
  get className(){return this.attributes.class||''}set className(v){this.attributes.class=String(v)}
  get id(){return this.attributes.id||''}set id(v){this.attributes.id=v}
  get hidden(){return 'hidden'in this.attributes}set hidden(v){v?this.setAttribute('hidden',''):this.removeAttribute('hidden')}
  get isConnected(){let e=this;while(e){if(e===document)return true;e=e.parentElement}return false}
  get textContent(){return this._text+this.children.map(c=>c.textContent).join('')}set textContent(v){this.replaceChildren();this._text=String(v)}
  get options(){return this.children.filter(c=>c.tagName==='OPTION')}get selectedOptions(){return this.options.filter(c=>c.getAttribute('value')===this.value)}get firstChild(){return this.children[0]||null}get offsetWidth(){return 265}get offsetHeight(){return this.className.includes('hover')?80:0}
  setAttribute(k,v){this.attributes[k]=String(v)}getAttribute(k){return this.attributes[k]??null}removeAttribute(k){delete this.attributes[k]}
  append(...items){for(const item of items){if(item.parentElement)item.parentElement.children=item.parentElement.children.filter(x=>x!==item);item.parentElement=this;this.children.push(item)}}
  appendChild(item){this.append(item);return item}
  dispatchEvent(event){return this.emit(event.type,event)}
  replaceChildren(...items){this.children.forEach(c=>c.parentElement=null);this.children=[];this._text='';this.append(...items)}
  matches(selector){
   selector=selector.trim();const parts=selector.split('>');if(parts.length>1){const last=parts.pop();return this.matches(last)&&!!this.parentElement?.matches(parts.join('>'))}
   if(selector.endsWith(':last-child')){selector=selector.slice(0,-11);if(this.parentElement?.children.at(-1)!==this)return false}
   const attrs=[...selector.matchAll(/\[([^=\]]+)(?:=["']?([^\]"']+)["']?)?\]/g)];
   if(!attrs.every(([,key,val])=>key in this.attributes&&(val===undefined||this.attributes[key]===val)))return false;
   selector=selector.replace(/\[[^\]]+\]/g,'');
   const id=selector.match(/#([\w-]+)/);if(id&&this.id!==id[1])return false;
   for(const [,cls]of selector.matchAll(/\.([\w-]+)/g))if(!this.classList.contains(cls))return false;
   const tag=selector.match(/^[\w-]+/);return !tag||tag[0].toUpperCase()===this.tagName;
  }
  querySelectorAll(selector){const result=[];const visit=e=>{for(const child of e.children){if(child.matches(selector))result.push(child);visit(child)}};visit(this);return result}
  querySelector(selector){return this.querySelectorAll(selector)[0]||null}
  closest(selector){let e=this;while(e){if(e.matches(selector))return e;e=e.parentElement}return null}
  addEventListener(type,fn){(this.listeners[type]??=[]).push(fn)}removeEventListener(type,fn){this.listeners[type]=(this.listeners[type]||[]).filter(x=>x!==fn)}
  emit(type,input={}){const e={type,target:this,currentTarget:this,preventDefault(){this.defaultPrevented=true},stopPropagation(){this.stopped=true},...input};let at=this;while(at){e.currentTarget=at;for(const fn of(at.listeners[type]||[]))fn(e);if(at['on'+type])at['on'+type](e);if(e.stopped||input.bubbles===false)break;at=at.parentElement}return e}
  focus(){const old=document.activeElement;document.activeElement=this;if(old&&old!==this)old.emit('focusout');this.emit('focusin');this.emit('focus',{bubbles:false})}
  scrollIntoView(){this.scrolled=true}getAnimations(){return []}
  getBoundingClientRect(){return {x:0,y:0,left:0,top:0,width:this.closest('[hidden]')?0:options.mobile?350:970,height:this.closest('[hidden]')?0:options.mobile?470:690}}
  setPointerCapture(id){this.pointerCapture=id}hasPointerCapture(id){return this.pointerCapture===id}releasePointerCapture(id){delete this.pointerCapture;this.emit('lostpointercapture',{pointerId:id,bubbles:false})}
 }
 document=new Element('#document');document.activeElement=null;document.hidden=false;document.createElement=tag=>new Element(tag);document.createTextNode=text=>{const e=new Element('text');e.textContent=text;return e};document.createElementNS=(_,tag)=>new Element(tag);document.getElementById=id=>document.querySelector('#'+id);
 const html=require('./program.cjs').html.replace(/<style>[\s\S]*?<\/style>/g,'').replace(/<script>([\s\S]*?)<\/script>/g,''),stack=[document],voids=new Set(['meta','link','input','br','hr','img']);
 for(const match of html.matchAll(/<([^>]+)>|([^<]+)/g)){
  if(match[2]){stack.at(-1)._text+=decode(match[2]);continue}
  const tag=match[1];if(tag.startsWith('!'))continue;if(tag.startsWith('/')){if(stack.length>1)stack.pop();continue}
  const name=tag.split(/\s/)[0].replace(/\/$/,'');const el=new Element(name);
  for(const a of tag.slice(name.length).matchAll(/([^\s=\/]+)(?:\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s]+)))?/g))el.setAttribute(a[1],decode(a[2]??a[3]??a[4]??''));
  stack.at(-1).append(el);if(!voids.has(name)&&!tag.endsWith('/'))stack.push(el);
 }
 const window=new Element('#window');window.document=document;window.matchMedia=key=>media[key]??=(Object.assign(new Element('media'),{matches:key.includes('max-width')?!!options.mobile:!!options.reduced}));
 const historyStack=[url.href],historyStates=[{atlasIndex:0}];let historyIndex=0;
 const location={get href(){return url.href},get search(){return url.search},get origin(){return url.origin},get pathname(){return url.pathname},get hash(){return url.hash}};
 const history={get state(){return historyStates[historyIndex]},pushState(state,__,value){historyWrites.push({kind:'push',at:now});url=new URL(value,url);historyStack.splice(++historyIndex);historyStack.push(url.href);historyStates.splice(historyIndex);historyStates.push(state)},replaceState(state,__,value){historyWrites.push({kind:'replace',at:now});url=new URL(value,url);historyStack[historyIndex]=url.href;historyStates[historyIndex]=state},back(){if(historyIndex){url=new URL(historyStack[--historyIndex]);window.emit('popstate',{bubbles:false,state:historyStates[historyIndex]})}}};
 class IO{constructor(cb){this.cb=cb;observers.push(this)}observe(el){this.element=el}disconnect(){this.disconnected=true}}
 class RO{constructor(cb){this.cb=cb;resizers.push(this)}observe(el){this.element=el}disconnect(){}}
 const context={window,document,innerWidth:options.width||(options.mobile?390:1440),innerHeight:options.height||900,matchMedia:window.matchMedia,setTimeout:(fn,delay=0)=>{if(!delay){fn();return 0}const id=++sequence;timers.set(id,{fn,at:now+delay});return id},clearTimeout:id=>timers.delete(id),location,history,URL,URLSearchParams,Map,Set,CustomEvent:class{constructor(type){this.type=type}},performance:{now:()=>now},queueMicrotask:fn=>fn(),IntersectionObserver:IO,ResizeObserver:RO,
  requestAnimationFrame:fn=>{raf.set(++sequence,fn);return sequence},cancelAnimationFrame:id=>raf.delete(id)};
 window.IntersectionObserver=IO;window.ResizeObserver=RO;window.location=location;window.history=history;
 const source=require('./program.cjs').source;
 vm.runInNewContext(source,context);
 return {document,window,media,raf,timers,historyWrites,observers,resizers,location,historyStack,context,source,
  $(selector){return document.querySelector(selector)},$$(selector){return document.querySelectorAll(selector)},
  runAsset(name){vm.runInNewContext(fs.readFileSync(path.join(rootDir,'assets',name),'utf8'),context)},
  step(ms=400){now+=ms;const queue=[...raf.values()];raf.clear();queue.forEach(fn=>fn(now));for(const [id,timer]of [...timers])if(timer.at<=now){timers.delete(id);timer.fn()}},
  changeMedia(key,matches){media[key].matches=matches;media[key].emit('change',{bubbles:false})},
  goBack(){if(historyIndex){url=new URL(historyStack[--historyIndex]);window.emit('popstate',{bubbles:false,state:historyStates[historyIndex]})}},
  goForward(){if(historyIndex+1<historyStack.length){url=new URL(historyStack[++historyIndex]);window.emit('popstate',{bubbles:false,state:historyStates[historyIndex]})}},
  setURL(value){url=new URL(value,url);window.emit('popstate',{bubbles:false,state:historyStates[historyIndex]})},
  input(value){const el=document.getElementById('query');el.value=value;el.focus();el.emit('input')},
  click(selector){const el=document.querySelector(selector);if(!el)throw Error('Missing '+selector);el.emit('click',{button:0});return el},
 };
}
module.exports={fixture};
