'use strict';
const assert=require('node:assert/strict'),{fixture}=require('../analysis/tests/dom_fixture.cjs');
let count=0;function test(name,fn){fn();count++;console.log('PASS '+name);}
test('explicit tree-to-C2 entry starts at top and return restores original window scroll',()=>{
 const f=fixture();f.app.dispatch({type:'paper',id:'harnessvln'});f.window.scrollY=320;
 const context=f.app.getContext();assert.equal(context.windowY,320);
 f.c2.open('harnessvln',context);assert.equal(f.window.scrollY,0);
 f.c2.returnToTrees();assert.equal(f.window.scrollY,320);
});
test('history-based C2 restore restores each prior document reading position',()=>{
 const f=fixture();f.c2.open('harnessvln',f.app.getContext());
 f.window.scrollY=260;f.c2.dispatch({type:'enter',id:'method.module4'});f.window.scrollY=180;
 f.back();assert(f.c2.isOpen());assert.equal(f.window.scrollY,260);
 f.forward();assert.equal(f.window.scrollY,180);
});
console.log(count+' integration checks passed; in-memory DOM only, real browser NOT_RUN.');
