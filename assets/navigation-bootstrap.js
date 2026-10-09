/* Small inline watchdog: independent of both large reader scripts and data. */
(function () {
'use strict';
var root=document.getElementById('navigation-product'),loading=document.getElementById('np-loading'),message=document.getElementById('np-load-message'),retry=document.getElementById('np-retry'),fallback=document.getElementById('np-static-reading');
if(!root||!loading||!message||!retry)return;
var attempt=0,timer=null,failed=false,ready=false,retries=0,scripts=[],timeout=30000;
function status(text){message.textContent=text;}
function valid(id){return id===attempt&&!failed&&!ready;}
function fail(id,text){if(!valid(id))return;failed=true;clearTimeout(timer);root.setAttribute('data-load-state','failed');root.setAttribute('data-error','true');loading.hidden=false;fallback.hidden=false;document.getElementById('np-workspace').hidden=true;status(text+'。下方已审静态内容仍可阅读；不会借用其他论文或版本。');retry.hidden=retries>=2;retry.disabled=false;window.dispatchEvent(new CustomEvent('navigation-load-cancel',{detail:{attempt:id}}));}
function stage(id,text){if(valid(id)){root.setAttribute('data-load-state','loading');status(text);}}
function addScript(url,id,next){if(!valid(id))return;var s=document.createElement('script');s.src=url;s.async=true;s.setAttribute('data-np-attempt',String(id));s.onload=function(){if(valid(id)&&next)next();};s.onerror=function(){fail(id,'交互脚本未能加载');};scripts.push(s);document.head.appendChild(s);}
function start(){attempt++;failed=false;ready=false;root.removeAttribute('data-error');retry.hidden=true;retry.disabled=true;loading.hidden=false;fallback.hidden=false;scripts.forEach(function(s){s.remove();});scripts=[];clearTimeout(timer);var id=attempt;stage(id,'正在加载交互模块；可先阅读下方已审内容。');timer=setTimeout(function(){fail(id,'加载已超过30秒，已停止本次交互启动');},timeout);var launch=function(){addScript(root.getAttribute('data-app-url'),id);};if(window.NavigationProductModel)launch();else addScript(root.getAttribute('data-state-url'),id,launch);}
window.NavigationProductLoader={get attempt(){return attempt;},valid:valid,stage:stage,fail:fail,ready:function(id){if(!valid(id))return false;ready=true;clearTimeout(timer);root.setAttribute('data-load-state','ready');root.removeAttribute('data-error');loading.hidden=true;fallback.hidden=true;retry.hidden=true;return true;}};
retry.addEventListener('click',function(){if(!failed||retries>=2)return;retries++;start();});
window.addEventListener('error',function(event){var name=String(event.filename||'');if(/navigation-product(?:-model)?\.js/.test(name))fail(attempt,'交互模块执行失败');});
document.querySelectorAll('.np-skip,[data-workspace-jump]').forEach(function(link){link.addEventListener('click',function(event){if(ready)return;event.preventDefault();window.NavigationProductPendingJump=true;fallback.scrollIntoView({block:'start'});});});
start();
}());
