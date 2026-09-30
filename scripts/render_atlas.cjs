/* Deterministic static fallback for JavaScript-disabled and unavailable Canvas contexts. */
const {makeStars,project}=require('../assets/hero-atlas.js');
const fs=require('fs'),path=require('path');
function render(){
 const groups=new Map(),colors=['#e3edf6','#99ddc7','#bba9e8'];
 for(const star of makeStars(2350)){const p=project(star,0),size=Math.round(p.radius*3)/3,alpha=Math.round(p.opacity*5)/5;
  const key=[p.color,Math.max(.33,size),Math.max(.2,alpha)].join(',');
  groups.set(key,(groups.get(key)||'')+`M${p.x.toFixed(1)} ${p.y.toFixed(1)}h.01`);
 }
 let svg='<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 560 408" fill="none"><defs><radialGradient id="core"><stop stop-color="#dceaf9" stop-opacity=".13"/><stop offset=".25" stop-color="#aec5e0" stop-opacity=".04"/><stop offset="1" stop-color="#a0bee6" stop-opacity="0"/></radialGradient></defs><circle cx="280" cy="204" r="42" fill="url(#core)"/>';
 for(const [key,d]of groups){const[c,s,a]=key.split(',');svg+=`<path d="${d}" stroke="${colors[c]}" stroke-width="${(Number(s)*2).toFixed(2)}" stroke-opacity="${a}" stroke-linecap="round"/>`;}
 return svg+'</svg>\n';
}
module.exports={render};
if(require.main===module){const target=path.join(__dirname,'../assets/hero-atlas.svg');fs.writeFileSync(target,render());console.log('Wrote deterministic original galaxy fallback.');}
