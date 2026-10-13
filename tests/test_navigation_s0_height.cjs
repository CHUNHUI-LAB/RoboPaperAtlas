'use strict';
// These are CSSOM and explicit budget regressions, not browser pixel approval.
// The unchanged exact-node/visibility/footer gates still run in Chrome CI.
const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {JSDOM}=require('jsdom'),root=path.resolve(__dirname,'..');
const css=fs.readFileSync(path.join(root,'assets/navigation-product.css'),'utf8'),site=fs.readFileSync(path.join(root,'assets/site.css'),'utf8');
const marker='/* The current identity and site chrome share the short desktop';
const split=css.indexOf(marker);assert.ok(split>0);
function match(query,width,height){return query.split(',').some(part=>{const tests=[...part.matchAll(/\((min|max)-(width|height):\s*(\d+)px\)/g)];return tests.length>0&&tests.every(([,bound,axis,n])=>bound==='min'?(axis==='width'?width:height)>=+n:(axis==='width'?width:height)<=+n)&&!part.includes('prefers-');});}
function fixture(width,height,home=true,compact=true){
 const dom=new JSDOM(`<main id="navigation-product" data-load-state="ready" data-reading-home="${home}"><section class="np-global-start"><nav class="np-global-navigation"><strong>导航研究地图</strong><details><summary>直接查找具体任务或条件</summary></details></nav></section><section id="np-workspace" class="np-workspace"><dl class="np-selection-context"><div class="np-context-field"><dt>当前虚拟阅读索引</dt><dd>全部来源与论文索引</dd></div><div class="np-context-field"><dt>当前路线</dt><dd>全局研究图</dd></div><div class="np-context-field"><dt>当前论文</dt><dd>尚未选择</dd></div><div class="np-context-field"><dt>来源版本</dt><dd>尚未选择</dd></div></dl><div class="np-workspace-bar"><div class="np-tabs"><button>全景</button><button>文献发展</button><button>困难与思路</button><button>论文解析</button></div><nav class="np-global-context"></nav><details class="np-reading-tools"><summary>阅读工具</summary></details><nav class="np-origin-trail"></nav><button id="np-overview-toggle" class="np-text-button">原全局树图</button><details class="np-identity-controls"><summary>论文身份与来源版本</summary></details><button id="np-graph-fullscreen">全屏查看</button></div><section id="np-reading-landing" class="np-reading-landing np-graphical-home"><div class="np-overview-map-toolbar"><details id="np-all-scopes"><summary>全部阅读范围与术语</summary></details><details id="np-overview-comparison"><summary>任务输入与完成要求</summary></details><details id="np-task-relations"><summary>7条有据对照与组合</summary></details><details id="np-overview-notes"><summary>范围说明</summary></details><button id="np-overview-analysis" class="np-text-button">单篇论文解析</button><button id="np-map-relations-toggle" class="np-text-button">显示全部关系</button></div><div class="np-overview-map"><button class="np-map-task"><span class="np-task-reading-contract">图文→飞行搜索</span><span class="np-task-reading-name">AVOS</span></button><button class="np-map-challenge">逐点语义冗余且缺少对象关系</button></div><div class="np-overview-footer"><div class="np-map-legend">实线：原目录父子</div><p class="np-overview-coverage np-map-coverage">选段覆盖，不代表全文精读</p></div></section></section></main>`),d=dom.window.document;
 const parse=d.createElement('style');parse.textContent=site+'\n'+(compact?css:css.slice(0,split));d.head.append(parse);
 function flatten(rules){return [...rules].flatMap(r=>r.media?(match(r.media.mediaText,width,height)?flatten(r.cssRules):[]):r.style?[r.cssText]:[]);}
 const active=flatten(parse.sheet.cssRules);parse.remove();const style=d.createElement('style');style.textContent=active.join('\n');d.head.append(style);
 const s=q=>dom.window.getComputedStyle(d.querySelector(q));return {dom,d,s,style};
}
const px=v=>parseFloat(v)||0;
const outer=(s,prefix='padding')=>px(s[prefix+'Top'])+px(s[prefix+'Bottom']);
test('short S0 shell only reclaims chrome spacing, preserving exact typography and node styles',()=>{
 const changed=['#navigation-product','.np-global-start','.np-selection-context','.np-context-field','.np-workspace-bar','.np-tabs','.np-overview-map-toolbar'];
 const text=['.np-global-navigation>details>summary','.np-selection-context dt','.np-selection-context dd','.np-tabs button','.np-reading-tools>summary','.np-identity-controls>summary','.np-overview-map-toolbar>details>summary','.np-task-reading-name','.np-task-reading-contract','.np-map-challenge','.np-map-legend','.np-map-coverage'];
 for(const [width,height,home,applies]of[[1440,900,true,true],[1920,1080,true,false],[1180,757,true,false],[1440,900,false,false]]){
  const before=fixture(width,height,home,false),after=fixture(width,height,home,true);try{
   assert.equal(after.d.querySelectorAll('.np-context-field dt').length,4);assert.equal(after.d.querySelectorAll('.np-context-field dd').length,4);assert.equal(after.d.querySelectorAll('.np-tabs button').length,4);assert.equal(after.d.querySelectorAll('.np-overview-map-toolbar>details>summary,.np-overview-map-toolbar>button').length,6);
   for(const q of text)for(const key of ['fontSize','fontWeight','lineHeight','color'])assert.equal(after.s(q)[key],before.s(q)[key],`${width}×${height} ${q} unchanged ${key}`);
   if(!applies){for(const q of changed)for(const key of ['display','height','paddingTop','paddingBottom','marginTop','marginBottom','flexDirection']){if(width>=1200&&q==='#navigation-product'&&['display','height','flexDirection'].includes(key))continue;if(width>=1200&&home&&q==='.np-overview-map-toolbar'&&key==='paddingBottom'){assert.equal(after.s(q)[key],'8px');assert.equal(before.s(q)[key],'12px');continue;}assert.equal(after.s(q)[key],before.s(q)[key],q+' unaffected outside short S0');}}
   else{assert.equal(after.s('.np-context-field').flexDirection,'row');assert.equal(after.s('.np-workspace-bar').display,'flex');assert.equal(after.s('.np-workspace-bar').flexWrap,'wrap');assert.equal(after.s('.np-tabs').width,'auto');assert.equal(after.s('.np-global-navigation>details>summary').paddingTop,'0px');assert.equal(after.s('.np-overview-map-toolbar>details>summary').paddingBottom,'0px');}
   for(const q of ['.np-map-task','.np-map-challenge','.np-overview-footer'])for(const key of ['minHeight','paddingTop','paddingBottom','marginTop','gap','flexShrink','overflow'])assert.equal(after.s(q)[key],before.s(q)[key],q+' unchanged scientific card/footer');
  }finally{before.dom.window.close();after.dom.window.close();}
 }
});
test('both approved desktop budgets reserve full 649px source map and original separate footer without shrinking text',()=>{
 for(const [width,height]of[[1440,900],[1920,1080]]){const x=fixture(width,height),s=x.s;try{
  // Real CI font sizes/line heights are already independently pinned. Model each
  // natural-flow row from those CSS declarations, without using product y values.
  const line=(selector,fallback)=>{const style=s(selector),v=style.lineHeight;return v.endsWith('px')?px(v):px(style.fontSize)*(px(v)||fallback);};
  const summary='.np-global-navigation>details>summary',global=Math.max(px(s('.np-global-start').minHeight),Math.max(line(summary,1.65)+outer(s(summary)),px(s(summary).minHeight))+outer(s('.np-global-start')));
  const identity=(height<=950?Math.max(line('.np-selection-context dt',1.5),line('.np-selection-context dd',1.5)):line('.np-selection-context dt',1.5)+line('.np-selection-context dd',1.5)+px(s('.np-context-field').gap))+outer(s('.np-selection-context'))+outer(s('.np-selection-context'),'margin')+1;
  const controlOuter=selector=>{const style=s(selector);return Math.max(px(style.minHeight),line(selector,1.65)+outer(style)+px(style.borderTopWidth)+px(style.borderBottomWidth));};
  const controls=['.np-tabs button','.np-reading-tools>summary','.np-identity-controls>summary','#np-overview-toggle','#np-graph-fullscreen'];
  const controlHeights=controls.map(q=>controlOuter(q)+(q==='.np-tabs button'?outer(s('.np-tabs')):0));
  const tabs=Math.max(px(s('.np-workspace-bar').height),...controlHeights);
  const overviewSelectors=['#np-all-scopes>summary','#np-overview-comparison>summary','#np-task-relations>summary','#np-overview-notes>summary','#np-overview-analysis','#np-map-relations-toggle'];
  const overview=Math.max(px(s('.np-overview-map-toolbar').minHeight),Math.max(...overviewSelectors.map(controlOuter))+outer(s('.np-overview-map-toolbar'))+1)+outer(s('.np-overview-map-toolbar'),'margin');
  const footer=line('.np-map-legend',1.45)+line('.np-map-coverage',1.45)+px(s('.np-overview-footer').gap)+outer(s('.np-overview-footer'),'margin');
  const landing=outer(s('.np-reading-landing'))+2,app=outer(s('#navigation-product')),header=65;
  const budget={header,global,identity,tabs,overview,footer,landing,app};if(height<=950)assert.ok(controlHeights.every(v=>v<=34),JSON.stringify({controls,controlHeights}));const available=height-Object.values(budget).reduce((a,b)=>a+b,0);
  assert.ok(available>=649,JSON.stringify({budget,available}));assert.ok(available<680,'budget must not fabricate spare viewport');
  assert.ok(available-30<649,'a genuinely taller header exhausts the budget');
  assert.equal(s('.np-overview-footer').marginTop,'12px');assert.equal(s('.np-overview-footer').flexShrink,'0');
  assert.equal(s('.np-overview-map').minHeight,'0');assert.equal(s('.np-reading-landing').overflow,'hidden');
 }finally{x.dom.window.close();}}
});
test('short-shell controller derives height from the actual application top, not the old fixed 128px offset',()=>{
 const source=fs.readFileSync(path.join(root,'assets/navigation-product.js'),'utf8');
 assert.ok(source.includes("window.innerHeight-app.getBoundingClientRect().top"));
 assert.ok(source.includes("else app.style.removeProperty('--np-workspace-shell-height')"));
 const declaration=css.slice(css.indexOf('@media (min-width:1200px) and (max-height:950px)',split));assert.ok(declaration.includes('@media (min-width:1200px) and (max-height:950px)'));
 for(const r of declaration.matchAll(/([^{}]+)\{([^{}]*)\}/g))if(!r[1].includes('@media')){assert.ok(r[1].includes('[data-reading-home=true]'));assert.ok(!/(?:font-size|font-weight|line-height|transform|zoom|display\s*:\s*none|visibility\s*:\s*hidden)/.test(r[2]));}
});

test('desktop height follows actual app top, clamps exhausted space and clears stale narrow styles',()=>{
 const source=fs.readFileSync(path.join(root,'assets/navigation-product.js'),'utf8');
 const fn=source.match(/^function syncDesktopWorkspaceHeight\([^]*?^\}/m)[0];
 const run=Function('app','window',fn+';syncDesktopWorkspaceHeight();');const values=new Map();
 const app={getBoundingClientRect:()=>({top:65}),style:{setProperty:(k,v)=>values.set(k,v),removeProperty:k=>values.delete(k)}};
 for(const [width,height,wanted]of[[1440,900,'835px'],[1920,1080,'1015px'],[1440,40,'0px']]){run(app,{innerWidth:width,innerHeight:height});assert.equal(values.get('--np-workspace-shell-height'),wanted);}
 run(app,{innerWidth:1180,innerHeight:757});assert.equal(values.has('--np-workspace-shell-height'),false);
});

test('explicit fullscreen keeps its independent viewport height instead of inherited flex remainder',()=>{
 const dom=new JSDOM('<style></style>');try{const style=dom.window.document.querySelector('style');style.textContent=css;
 const desktop=[...style.sheet.cssRules].filter(r=>r.media&&r.media.mediaText==='(min-width:1200px)').flatMap(r=>[...r.cssRules]);
 const rule=desktop.filter(r=>r.selectorText==='#navigation-product[data-load-state=ready] .np-workspace:fullscreen').at(-1);assert.ok(rule);
 assert.equal(rule.style.getPropertyValue('height'),'100dvh');assert.equal(rule.style.getPropertyValue('flex'),'0 0 auto');
 }finally{dom.window.close();}
});

test('fullscreen changes request geometry refresh even when viewport dimensions do not change',()=>{
 const source=fs.readFileSync(path.join(root,'assets/navigation-product.js'),'utf8');
 const start=source.indexOf('function(){',source.indexOf("document.addEventListener('fullscreenchange'"));assert.ok(start>0);let depth=0,end=start;for(;end<source.length;end++){if(source[end]==='{')depth++;if(source[end]==='}'&&--depth===0){end++;break;}}const callback=source.slice(start,end);let refreshes=0,focused=0;
 const control={textContent:'',focus:options=>{assert.deepEqual(options,{preventScroll:true});focused++;}};
 const doc={fullscreenElement:{}};const run=Function('document','by','refreshChromeHeight','return '+callback)(doc,()=>control,()=>refreshes++);
 run();assert.equal(refreshes,1);assert.equal(focused,0);assert.equal(control.textContent,'退出全屏');
 doc.fullscreenElement=null;run();assert.equal(refreshes,2);assert.equal(focused,1);assert.equal(control.textContent,'全屏查看');
});
