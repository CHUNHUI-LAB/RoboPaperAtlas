"""Reading-path contrast on the paper/white surfaces; no pixel claim from CSSOM."""
import json
from pathlib import Path
import subprocess
import unittest


class ContextContrastTests(unittest.TestCase):
    def test_path_controls_remain_readable_on_toolbar_and_open_ancestry(self):
        root = Path(__file__).parents[1]
        script = r"""
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),css=JSON.parse(require('fs').readFileSync(0,'utf8'));
function contrast(f,b){const l=x=>x.map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((a,v,i)=>a+v*[.2126,.7152,.0722][i],0);return (Math.max(l(f),l(b))+.05)/(Math.min(l(f),l(b))+.05);}
function mediaActive(media,width,height){return media.map(query=>{if(['print','(prefers-reduced-motion:reduce)'].includes(query))return false;return query.split(/\s+and\s+/).map(part=>{const match=part.match(/^\((min|max)-(width|height):\s*(\d+)px\)$/);assert.ok(match,'unexpected media query '+query);const size=match[2]==='width'?width:height;return match[1]==='min'?size>=Number(match[3]):size<=Number(match[3]);}).every(Boolean);}).every(Boolean);}

const shortQuery='(min-width:1200px) and (max-height:950px)';
for(const[w,h,expected]of[[1199,949,false],[1200,949,true],[1200,950,true],[1200,951,false],[1440,900,true],[1920,1080,false]])assert.equal(mediaActive([shortQuery],w,h),expected,`${w}x${h}`);
assert.equal(mediaActive(['(max-width:1200px) and (min-height:950px)'],1200,950),true);
assert.equal(mediaActive(['print'],1440,900),false);assert.equal(mediaActive(['(prefers-reduced-motion:reduce)'],1440,900),false);
for(const q of['(orientation:landscape)','(min-width:1200px) and (hover:hover)','(min-width:9999px) and (unknown:1)','(max-height:950px) trailing','(min-width:1200px) or (max-height:950px)'])assert.throws(()=>mediaActive([q],1440,900),/unexpected media query/);
assert.throws(()=>mediaActive(['print','(unknown:1)'],1440,900),/unexpected media query/,'inactive media must not hide unknown syntax');
for(const [width,height] of [[1440,900],[1440,950],[1440,951],[1920,1080]]){
 const dom=new JSDOM('<style></style><main id="navigation-product" data-load-state="ready"><section class="np-workspace"><div class="np-workspace-bar"><nav id="np-global-context" class="np-global-context"><div class="np-context-group np-context-entry" data-path-kind="global-entry"><button class="np-crumb">领域</button><button class="np-crumb" id="audio">AudioGoal（声源目标导航）</button></div><details class="np-ancestry-disclosure" open><summary>挑战–思路树 · 原树路径</summary><div class="np-context-group np-context-local" data-path-kind="local-ancestry"><span class="np-context-label">挑战–思路树</span><button class="np-crumb" id="ancestor">完整原始问题</button></div></details></nav></div></section></main>');
 try{const w=dom.window,d=w.document,style=d.querySelector('style');style.textContent=css;const entries=[];
 function collect(rules,media=[]){for(const rule of rules)if(rule.media)collect(rule.cssRules,media.concat(rule.media.mediaText));else if(rule.selectorText)entries.push({rule,media});}collect(style.sheet.cssRules);

 style.textContent=entries.filter(({media})=>mediaActive(media,width,height)).map(({rule})=>rule.cssText).join('\n');
 function color(value){const m=value.match(/^rgba?\(([^)]+)\)$/);assert.ok(m,value);return m[1].split(',').map(Number);}
 function background(e){for(let p=e;p;p=p.parentElement){const c=color(w.getComputedStyle(p).backgroundColor);if(c.length===3||c[3]===1)return c.slice(0,3);assert.equal(c[3],0);}return [255,255,255];}
 const audio=d.getElementById('audio'),ancestor=d.getElementById('ancestor');
 assert.deepEqual(background(audio),[250,250,248]);assert.deepEqual(background(ancestor),[255,255,255]);
 for(const control of [audio,ancestor]){const foreground=color(w.getComputedStyle(control).color).slice(0,3);assert.ok(contrast(foreground,background(control))>=4.5,JSON.stringify({foreground,background:background(control)}));}
 assert.equal(audio.textContent,'AudioGoal（声源目标导航）');assert.equal(ancestor.textContent,'完整原始问题');assert.equal(w.getComputedStyle(ancestor).whiteSpace,'normal');assert.equal(w.getComputedStyle(ancestor).overflow,'visible');
 }finally{dom.window.close();}
}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps((root / 'assets/navigation-product.css').read_text()), text=True, capture_output=True, cwd=root)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


if __name__ == '__main__':
    unittest.main()
