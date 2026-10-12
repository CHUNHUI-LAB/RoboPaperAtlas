"""Desktop context contrast regression; CSS cascade, not browser pixel evidence."""
import json
from pathlib import Path
import subprocess
import unittest


class ContextContrastTests(unittest.TestCase):
    def test_desktop_crumb_cascade_is_readable_on_actual_gray_and_white_surfaces(self):
        root = Path(__file__).parents[1]
        script = r"""
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),css=JSON.parse(require('fs').readFileSync(0,'utf8'));
const selector='#navigation-product .np-global-context .np-crumb';
function contrast(f,b){const l=x=>x.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);return (Math.max(l(f),l(b))+.05)/(Math.min(l(f),l(b))+.05);}
for(const width of [1440,1920]){
 const dom=new JSDOM('<style></style><main id="navigation-product" data-load-state="ready"><section class="np-workspace"><div class="np-workspace-bar"><nav id="np-global-context" class="np-global-context"><div class="np-context-group np-context-entry" data-path-kind="global-entry"><button class="np-crumb">领域</button><button class="np-crumb" id="audio">AudioGoal（声源目标导航）</button></div><details class="np-ancestry-disclosure" open><summary>挑战–思路树 · 原树路径</summary><div class="np-context-group np-context-local" data-path-kind="local-ancestry"><span class="np-context-label">挑战–思路树</span><button class="np-crumb" id="ancestor">完整原始问题</button></div></details></nav></div></section></main>');
 try{const w=dom.window,d=w.document,style=d.querySelector('style');style.textContent=css;const entries=[];
 function collect(rules,media=[]){for(const rule of rules)if(rule.media)collect(rule.cssRules,media.concat(rule.media.mediaText));else if(rule.selectorText)entries.push({rule,media});}collect(style.sheet.cssRules);
 const overrides=entries.filter(({rule})=>rule.selectorText===selector&&rule.style.getPropertyValue('color'));
 assert.equal(overrides.length,1);assert.deepEqual(overrides[0].media,['(min-width:1200px)']);assert.equal(overrides[0].rule.style.getPropertyValue('color'),'#456170');
 const legacy=entries.find(({rule})=>rule.selectorText==='.np-global-context .np-crumb'&&rule.style.getPropertyValue('color')==='#637880');assert.ok(legacy);assert.ok(d.getElementById('audio').matches(legacy.rule.selectorText));
 function active(media){return media.every(q=>{const m=q.match(/^\((min|max)-width:\s*(\d+)px\)$/);if(m)return m[1]==='min'?width>=+m[2]:width<=+m[2];assert.ok(['print','(prefers-reduced-motion:reduce)'].includes(q),q);return false;});}
 const flattened=entries.filter(({media})=>active(media)).map(({rule})=>rule.cssText).join('\n');
 function install(value){style.textContent=flattened;const rule=[...style.sheet.cssRules].find(r=>r.selectorText===selector&&r.style.getPropertyValue('color'));if(value===null)rule.style.removeProperty('color');else rule.style.setProperty('color',value);style.textContent=[...style.sheet.cssRules].map(r=>r.cssText).join('\n');}
 function color(value){const m=value.match(/^rgba?\(([^)]+)\)$/);assert.ok(m,value);return m[1].split(',').map(Number);}
 function background(e){for(let p=e;p;p=p.parentElement){const c=color(w.getComputedStyle(p).backgroundColor);if(c.length===3||c[3]===1)return c.slice(0,3);assert.equal(c[3],0);}return [255,255,255];}
 function rgb(e){return color(w.getComputedStyle(e).color).slice(0,3);}
 const audio=d.getElementById('audio'),ancestor=d.getElementById('ancestor');
 install('#456170');assert.deepEqual(background(audio),[247,249,250],'actual toolbar surface is gray, not white');assert.deepEqual(background(ancestor),[255,255,255],'opened ancestry popover has its own white surface');
 for(const el of [audio,ancestor]){assert.deepEqual(rgb(el),[69,97,112]);assert.ok(contrast(rgb(el),background(el))>=4.5);}
 for(const value of [null,'#637880']){install(value);assert.deepEqual(rgb(audio),[99,120,128]);assert.ok(contrast(rgb(audio),[255,255,255])>=4.5,'white-only fixture would miss this regression');assert.ok(contrast(rgb(audio),background(audio))<4.5,'actual gray surface rejects the original tint');}
 install('#456170');assert.ok(contrast(rgb(audio),background(audio))>=4.5);assert.equal(audio.textContent,'AudioGoal（声源目标导航）');assert.equal(ancestor.textContent,'完整原始问题');
 }finally{dom.window.close();}
}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps((root / 'assets/navigation-product.css').read_text()), text=True, capture_output=True, cwd=root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
