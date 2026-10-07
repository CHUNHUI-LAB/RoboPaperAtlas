'use strict';
(()=>{
 const root=document.querySelector('[data-radar-period]');if(!root)return;
 const themes=[...root.querySelectorAll('[data-radar-theme]')],papers=[...root.querySelectorAll('[data-radar-paper]')],views=[...root.querySelectorAll('[data-radar-view]')],choices=[...root.querySelectorAll('.radar-theme-choice')];
 const input=root.querySelector('#radar-candidate-search'),rows=[...root.querySelectorAll('[data-radar-candidate]')],count=root.querySelector('#radar-candidate-count'),empty=root.querySelector('#radar-candidate-empty');
 let state={view:'overview',theme:'',paper:'',q:'',origin:''};
 // UI position only, scoped to this exact dated window; never a read/completed flag.
 const positionKey='radar-position:'+root.dataset.radarPeriod+':'+root.dataset.radarDate;
 function remember(){try{window.sessionStorage?.setItem(positionKey,hash(state));}catch(_){/* Storage may be disabled. */}}
 const clean=s=>{
  s={view:s.view||'overview',theme:s.theme||'',paper:s.paper||'',q:(s.q||'').slice(0,300),origin:s.origin||''};
  if(!themes.some(t=>t.dataset.radarTheme===s.theme))s.theme='';
  const paper=papers.find(p=>p.dataset.radarPaper===s.paper);if(!paper)s.paper='';
  if(s.view==='paper'&&paper&&s.theme&&!(paper.dataset.paperThemes||'').split(' ').includes(s.theme))s.theme='';
  if(!['overview','theme','paper','candidates','evidence'].includes(s.view))s.view='overview';
  if(s.view==='theme'&&!s.theme||s.view==='paper'&&!s.paper)s.view='overview';
  if(!['theme','candidates','evidence'].includes(s.origin))s.origin=s.theme?'theme':'candidates';
  if(s.origin==='theme'&&!s.theme)s.origin='candidates';
  return s;
 };
 const read=()=>{
  const raw=location.hash.slice(1),p=new URLSearchParams(raw);
  if(raw.startsWith('theme-'))return clean({view:'theme',theme:raw.slice(6)});
  if(raw.startsWith('paper-'))return clean({view:'paper',paper:raw.slice(6)});
  if(raw==='radar-candidates'||raw==='radar-evidence')return clean({view:raw.slice(6)});
  return clean(Object.fromEntries(p));
 };
 const hash=s=>{const p=new URLSearchParams();p.set('view',s.view);for(const k of ['theme','paper','q','origin'])if(s[k])p.set(k,s[k]);return '#'+p.toString();};
 function search(){const terms=input.value.normalize('NFKC').toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);let found=0;for(const r of rows){r.hidden=!terms.every(t=>r.dataset.search.normalize('NFKC').includes(t));if(!r.hidden)found++;}count.textContent=found+' / '+rows.length+' 条窗口候选';empty.hidden=found!==0;}
 function focus(el){if(el){el.focus({preventScroll:true});el.scrollIntoView({block:'nearest'});}}
 function target(s){if(s.view==='theme')return document.getElementById('heading-'+s.theme);if(s.view==='paper')return document.getElementById('paper-heading-'+s.paper);return document.getElementById('radar-'+(s.view==='overview'?'overview':s.view)+'-heading');}
 function returnTarget(previous,next){
  if(previous.view==='paper'){
   const panel=next.view==='theme'?themes.find(t=>t.dataset.radarTheme===next.theme):views.find(v=>v.dataset.radarView===next.view);
   return panel&&[...panel.querySelectorAll('[data-radar-action="paper"]')].find(a=>a.dataset.paper===previous.paper);
  }
  if(next.view==='overview'&&previous.theme)return document.getElementById('choose-'+previous.theme);
  return null;
 }
 function render(moveFocus=false,previous=state){
  root.classList.add('radar-enhanced');root.classList.toggle('radar-focused',state.view!=='overview');
  for(const t of themes){const selected=state.view==='theme'&&t.dataset.radarTheme===state.theme;t.hidden=!selected;selected?t.setAttribute('open',''):t.removeAttribute('open');}
  for(const p of papers){const selected=state.view==='paper'&&p.dataset.radarPaper===state.paper;p.hidden=!selected;selected?p.setAttribute('open',''):p.removeAttribute('open');}
  for(const v of views){const selected=v.dataset.radarView===state.view;v.hidden=!selected;selected?v.setAttribute('open',''):v.removeAttribute('open');}
  for(const a of choices){if(state.view!=='overview'&&a.dataset.theme===state.theme)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');}
  input.value=state.q;search();
  // Enhanced hrefs also carry context when copied or opened in another tab.
  for(const a of root.querySelectorAll('[data-radar-action]')){
   const action=a.dataset.radarAction;let next={...state};
   if(action==='theme')next={...state,view:'theme',theme:a.dataset.theme,paper:'',origin:'theme'};
   else if(action==='paper')next={...state,view:'paper',paper:a.dataset.paper,theme:a.dataset.theme||'',origin:a.dataset.origin||state.view};
   else if(action==='return')next={...state,view:state.origin,paper:''};
   else next={...state,view:action,paper:'',...(action==='overview'?{theme:''}:{})};
   a.setAttribute('href',hash(clean(next)));
  }
  if(moveFocus)focus(returnTarget(previous,state)||target(state));
 }
 function navigate(next,replace=false){next=clean(next);if(hash(next)===hash(state))return;const previous=state;state=next;history[replace?'replaceState':'pushState'](null,'',hash(state));render(!replace,previous);remember();}
 root.addEventListener('click',event=>{
  const a=event.target.closest('[data-radar-action]');if(!a||event.button>0||event.metaKey||event.ctrlKey||event.shiftKey||event.altKey)return;
  const action=a.dataset.radarAction;event.preventDefault();let next={...state};
  if(action==='theme')next={...state,view:'theme',theme:a.dataset.theme,paper:'',origin:'theme'};
  else if(action==='paper')next={...state,view:'paper',paper:a.dataset.paper,theme:a.dataset.theme||'',origin:a.dataset.origin||state.view};
  else if(action==='return')next={...state,view:state.origin,paper:''};
  else next={...state,view:action,paper:'',...(action==='overview'?{theme:''}:{})};
  navigate(next);
 });
 // Anchors remain real URLs for no-script reading and modified-click navigation.
 root.addEventListener('keydown',event=>{if(event.defaultPrevented)return;if(event.key==='Escape'&&state.view!=='overview'){event.preventDefault();navigate({...state,view:state.view==='paper'?state.origin:'overview',paper:'',...(state.view==='paper'?{}:{theme:''})});return;}const a=event.target.closest('.radar-theme-choice');if(a&&event.key===' '){event.preventDefault();navigate({...state,view:'theme',theme:a.dataset.theme,paper:'',origin:'theme'});}});
 input.addEventListener('input',()=>navigate({...state,view:'candidates',q:input.value},true));
 input.addEventListener('keydown',event=>{if(event.key==='Escape'&&input.value){event.preventDefault();navigate({...state,view:'candidates',q:''},true);}});
 const restore=()=>{if(landmark())return;const next=read();if(hash(next)===hash(state)){revealDiscovery();return;}const previous=state;state=next;render(true,previous);remember();revealDiscovery();};
 function landmarkElement(){const id=location.hash.slice(1);if(!id||id.includes('=')||id.startsWith('theme-')||id.startsWith('paper-')||['radar-overview','radar-candidates','radar-evidence'].includes(id))return null;return document.getElementById(id);}
 function landmark(){const el=landmarkElement();if(!el)return false;revealDiscovery();el.setAttribute('tabindex','-1');focus(el);return true;}
 function revealDiscovery(){if(location.hash==='#frontier-grid'){const feed=document.getElementById('radar-discovery');if(feed)feed.setAttribute('open','');}}
 window.addEventListener('popstate',restore);window.addEventListener('hashchange',restore);window.addEventListener('pageshow',()=>{state=read();render();revealDiscovery();});
 if(!location.hash){try{const saved=window.sessionStorage?.getItem(positionKey);if(saved&&saved.startsWith('#view='))history.replaceState(null,'',saved);}catch(_){/* Fresh overview remains usable without storage. */}}
 state=read();render(!!location.hash&&!landmarkElement());landmark();revealDiscovery();remember();
})();
