const fs=require('fs'),vm=require('vm'),assert=require('assert');
const doc={activeElement:null};
const cls=()=>({values:new Set(),add(v){this.values.add(v)},toggle(v,on){on?this.values.add(v):this.values.delete(v)},contains(v){return this.values.has(v)}});
const buttons=Array.from({length:5},(_,i)=>({dataset:{briefSelect:'paper-'+i},attrs:{},events:{},tabIndex:0,setAttribute(k,v){this.attrs[k]=v},addEventListener(k,f){this.events[k]=f},focus(){doc.activeElement=this}}));
const panels=buttons.map(b=>({dataset:{briefPanel:b.dataset.briefSelect},attrs:{},classList:cls(),inert:false,setAttribute(k,v){this.attrs[k]=v}}));
const tablist={hidden:true,attrs:{},setAttribute(k,v){this.attrs[k]=v}};
const reader={classList:cls(),querySelectorAll(s){return s==='[data-brief-select]'?buttons:panels},querySelector(){return tablist}};
doc.querySelectorAll=()=>[reader];
const media={matches:false,addEventListener(k,f){this.changed=f}};
vm.runInNewContext(fs.readFileSync(__dirname+'/../assets/brief-reader.js','utf8'),{document:doc,window:{matchMedia:()=>media}});
function selected(i){assert.equal(buttons.filter(b=>b.attrs['aria-selected']==='true').length,1);assert.equal(panels.filter(p=>p.classList.contains('active')).length,1);assert.equal(buttons[i].attrs['aria-selected'],'true');assert.equal(panels[i].inert,false);panels.forEach((p,j)=>assert.equal(p.attrs['aria-hidden'],String(i!==j)));}
selected(0);assert.equal(tablist.hidden,false);assert.equal(tablist.attrs['aria-orientation'],'vertical');
for(let n=0;n<150;n++){buttons[n%5].events.click();selected(n%5)}
buttons[4].events.keydown({key:'Home',preventDefault(){}});selected(0);assert.equal(doc.activeElement,buttons[0]);
buttons[0].events.keydown({key:'ArrowLeft',preventDefault(){}});selected(4);
media.matches=true;media.changed();assert.equal(tablist.attrs['aria-orientation'],'horizontal');selected(4);
buttons[4].events.keydown({key:'ArrowRight',preventDefault(){}});selected(0);
console.log('PASS: 150 selections, exactly one active panel, inert/ARIA, keyboard focus, responsive orientation without reset. DOM mock only.');
