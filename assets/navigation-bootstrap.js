/* Inline startup guard. The native trees are already usable before this code runs. */
(function () {
'use strict';
var root=document.getElementById('navigation-product'),loading=document.getElementById('np-loading'),message=document.getElementById('np-load-message'),retry=document.getElementById('np-retry'),fallback=document.getElementById('np-static-reading');
if(!root||!loading||!message||!retry)return;
var attempt=0,timer=null,failed=false,ready=false,retries=0,scripts=[],timeout=30000,started=0,phase='module_model',phaseLabel='',bytes=0,expected=0,inline=root.getAttribute('data-inline-start')==='1';
var box=document.createElement('details'),summary=document.createElement('summary'),diagnostic=document.createElement('pre'),copy=document.createElement('button');
box.className='np-load-diagnostics';box.hidden=true;summary.textContent='查看或复制加载诊断';diagnostic.id='np-load-diagnostic';copy.type='button';copy.textContent='复制诊断';box.append(summary,diagnostic,copy);loading.appendChild(box);
function snapshot(){return {schemaVersion:'navigation-load-diagnostic/1',phase:phase,elapsedMs:Math.max(0,Date.now()-started),receivedBytes:bytes,expectedBytes:expected,attempt:attempt,state:ready?'ready':failed?'failed':'loading',sourceModelSha256:root.getAttribute('data-model-sha'),indexSha256:root.getAttribute('data-index-sha')||null};}
function updateDiagnostic(){diagnostic.textContent=JSON.stringify(snapshot(),null,2);}
copy.addEventListener('click',function(){updateDiagnostic();var text=diagnostic.textContent;if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(text).catch(function(){var range=document.createRange();range.selectNodeContents(diagnostic);var selection=window.getSelection();selection.removeAllRanges();selection.addRange(range);});});
function status(text){message.textContent=text;}
function valid(id){return id===attempt&&!failed&&!ready;}
function fail(id,text){if(!valid(id))return;failed=true;clearTimeout(timer);root.setAttribute('data-load-state','failed');root.setAttribute('data-error','true');loading.hidden=false;fallback.hidden=false;document.getElementById('np-workspace').hidden=true;status(text+'；停在：'+phaseLabel+'（'+phase+'）。下方原生树仍可展开阅读。');box.hidden=false;updateDiagnostic();retry.hidden=retries>=2;retry.disabled=false;window.dispatchEvent(new CustomEvent('navigation-load-cancel',{detail:{attempt:id}}));}
function stage(id,text,code,metrics){if(valid(id)){phase=code||phase;phaseLabel=text;if(metrics){if(Number.isFinite(metrics.receivedBytes))bytes=metrics.receivedBytes;if(Number.isFinite(metrics.expectedBytes))expected=metrics.expectedBytes;}root.setAttribute('data-load-state','loading');root.setAttribute('data-load-phase',phase);status(text);}}
function addScript(url,id,next){if(!valid(id))return;var s=document.createElement('script');s.src=url;s.async=true;s.setAttribute('data-np-attempt',String(id));s.onload=function(){if(valid(id)&&next)next();};s.onerror=function(){fail(id,'交互脚本未能加载');};scripts.push(s);document.head.appendChild(s);}
function start(){attempt++;failed=false;ready=false;started=Date.now();bytes=0;expected=0;root.removeAttribute('data-error');retry.hidden=true;retry.disabled=true;loading.hidden=false;fallback.hidden=false;box.hidden=true;scripts.forEach(function(s){s.remove();});scripts=[];clearTimeout(timer);var id=attempt;stage(id,'正在准备交互模块；原生树无需等待即可展开。','module_model');timer=setTimeout(function(){fail(id,'加载已超过30秒，已停止本次交互启动');},timeout);
 if(inline){if(retries>0){var missing=!window.NavigationProductModel?'module_model':!window.NavigationContent?'module_content':typeof window.NavigationProductStart!=='function'?'module_app':null;if(missing){stage(id,'当前页面的交互模块不可执行',missing);fail(id,'请刷新页面重新获取模块；原生树仍可阅读');return;}}if(typeof window.NavigationProductStart==='function')window.NavigationProductStart();return;}
 var launch=function(){stage(id,'正在加载树阅读模块…','module_app');addScript(root.getAttribute('data-app-url'),id);};if(window.NavigationProductModel)launch();else addScript(root.getAttribute('data-state-url'),id,launch);
}
window.NavigationProductLoader={get attempt(){return attempt;},valid:valid,stage:stage,fail:fail,diagnostics:snapshot,ready:function(id){if(!valid(id))return false;ready=true;phase='ready';clearTimeout(timer);root.setAttribute('data-load-state','ready');root.setAttribute('data-load-phase','ready');root.removeAttribute('data-error');loading.hidden=true;fallback.hidden=true;retry.hidden=true;return true;}};
retry.addEventListener('click',function(){if(!failed||retries>=2)return;retries++;start();});
window.addEventListener('error',function(event){var name=String(event.filename||'');if(/navigation-product(?:-model)?\.js/.test(name)||(inline&&event.error))fail(attempt,'交互模块执行失败');});
document.querySelectorAll('.np-skip,[data-workspace-jump]').forEach(function(link){link.addEventListener('click',function(event){if(ready)return;event.preventDefault();window.NavigationProductPendingJump=true;fallback.scrollIntoView({block:'start'});});});
start();
}());
