"""Desktop sibling hit-box regression from ef5d capture 38443394019.

CSSOM and measured-coordinate arithmetic are not a substitute for Chrome.
The existing screenshot text/box gates remain the final rendered acceptance.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('toolbar_screenshots', ROOT / 'scripts/navigation_screenshots.py')
SCREENSHOTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREENSHOTS)
RULES = (
    '#navigation-product[data-reading-home=false] .np-ancestry-disclosure>summary {padding:2px 0;}',
    '#navigation-product[data-reading-home=false] .np-reading-tools>summary {min-height:34px;padding:2px 0;}',
    '#navigation-product[data-reading-home=false] .np-reading-tools[open]>div {top:calc(100% + 4px);}',
)
CASES = ((600, 900), (601, 900), (1199, 900), (1200, 900), (1440, 900), (1920, 1080))


def rect(x, y, w, h):
    return dict(x=x, y=y, width=w, height=h)


def pixels(value):
    if value == '0':
        return 0.0
    if not re.fullmatch(r'\d+(?:\.\d+)?px', value):
        raise ValueError('Unexpected fixed CSS length: ' + value)
    return float(value[:-2])


def height(style):
    font = pixels(style['font-size'])
    line = style['resolved-line-height']
    line = pixels(line) if line.endswith('px') else float(line) * font
    padding = pixels(style['padding-top']) + pixels(style['padding-bottom'])
    return max(pixels(style['min-height']), line + padding)


def anchor(value, box_height):
    if value == 'calc(100% + 4px)':
        return box_height + 4
    return pixels(value)


def measured_boxes(ancestry_height, tools_height):
    # Exact row centers and horizontal positions measured in the failing PNG.
    # The original tools top is rounded to the receipt's 1/64 CSS-pixel grid.
    snap = lambda value: math.floor(value * 64 + .5) / 64
    return (rect(279.8125, snap(242.890625 - ancestry_height / 2), 172.703125, ancestry_height),
            rect(355.0625, snap(278.890625 - tools_height / 2), 80.953125, tools_height))


def overlap(a, b):
    return min(a['x'] + a['width'], b['x'] + b['width']) > max(a['x'], b['x']) and min(a['y'] + a['height'], b['y'] + b['height']) > max(a['y'], b['y'])


def tools_proof(ancestry, tools):
    points = [(tools['x'] + tools['width'] * x, tools['y'] + tools['height'] * y)
              for x, y in ((.5, .5), (.1, .1), (.9, .1), (.1, .9), (.9, .9))]
    visible = all(not (ancestry['x'] <= x <= ancestry['x'] + ancestry['width'] and
                          ancestry['y'] <= y <= ancestry['y'] + ancestry['height']) for x, y in points)
    fragment = dict(rect(372, 268.703125, 64.015625, 19), visible=True)
    run = dict(text='阅读工具', opaque=True, unscaled=True, fontSize=16,
               foreground=[23, 26, 25], background=[250, 250, 248], fragments=[fragment], clipAreas=[])
    return dict(run, rect=tools, textRuns=[copy.deepcopy(run)], renderedText='阅读工具', visible=visible, clipped=False)


class ToolbarGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = (ROOT / 'assets/navigation-product.css').read_text()
        for rule in RULES:
            if css.count(rule) != 1:
                raise AssertionError('Missing bounded desktop sibling repair: ' + rule)
        before = css
        for rule in RULES:
            before = before.replace(rule, '')
        script = r"""
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
function active(queries,width,height){return queries.map(query=>{
 if(query==='print'||/^\(prefers-reduced-motion:\s*reduce\)$/.test(query))return false;
 return query.split(/\s+and\s+/).map(part=>{const m=part.match(/^\((min|max)-(width|height):\s*(\d+)px\)$/);assert.ok(m,'unknown media '+query);const n=m[2]==='width'?width:height;return m[1]==='min'?n>=+m[3]:n<=+m[3];}).every(Boolean);
}).every(Boolean);}
assert.throws(()=>active(['print','(unknown:1)'],1440,900),/unknown media/);
const rows=[], selectors={bar:'.np-workspace-bar',ancestry:'.np-ancestry-disclosure>summary',ancestryMenu:'.np-context-local',tools:'#np-reading-tools>summary',toolsMenu:'#np-reading-tools>div',identity:'.np-identity-controls>summary',origin:'.np-origin-trail summary',reader:'#np-reader-toggle',tab:'.np-tabs button'};
for(const [width,height]of input.cases)for(const home of ['false','true','missing'])for(const opened of [false,true])for(const version of ['old','new']){
 const open=opened?' open':'',homeAttr=home==='missing'?'':' data-reading-home="'+home+'"';
 const dom=new JSDOM('<style></style><main id="navigation-product" data-load-state="ready"'+homeAttr+'><section id="np-workspace" class="np-workspace"><div class="np-workspace-bar"><nav id="np-global-context" class="np-global-context" data-path-kind="local-context"><details class="np-ancestry-disclosure"'+open+'><summary>挑战–思路树 · 原树路径</summary><div class="np-context-group np-context-local"><button>完整原始问题</button></div></details></nav><div class="np-tabs"><button>困难与思路</button></div><details id="np-reading-tools" class="np-reading-tools"'+open+'><summary>阅读工具</summary><div><button>任务条件</button></div></details><details class="np-identity-controls"><summary>论文身份与来源版本</summary></details><div class="np-origin-trail"><details><summary>返回来源</summary></details></div><button id="np-reader-toggle">收起阅读栏</button></div></section></main>');
 try{
  const w=dom.window,d=w.document,style=d.querySelector('style');style.textContent=input.site+'\n'+input[version];const entries=[];
  function collect(rules,media=[]){for(const rule of rules)if(rule.media)collect(rule.cssRules,media.concat(rule.media.mediaText));else if(rule.selectorText)entries.push({rule,media});}collect(style.sheet.cssRules);
  style.textContent=entries.filter(e=>active(e.media,width,height)).map(e=>e.rule.cssText).join('\n');
  const styles={};for(const[key,selector]of Object.entries(selectors)){const s=w.getComputedStyle(d.querySelector(selector));styles[key]=Object.fromEntries([...new Set([...Array.from(s),'padding-top','padding-bottom','padding-left','padding-right','min-height','font-size','line-height'])].map(k=>[k,s.getPropertyValue(k)]));
   // JSDOM omits inherited line-height on descendants. Resolve that inherited
   // property from the actual ancestor cascade; do not invent a text metric.
   for(let p=d.querySelector(selector);p;p=p.parentElement){const value=w.getComputedStyle(p).lineHeight;if(value&&value!=='inherit'){styles[key]['resolved-line-height']=value;break;}}
   assert.ok(styles[key]['resolved-line-height'],'unresolved line-height '+selector);}
  rows.push({width,height,home,opened,version,styles});
 }finally{dom.window.close();}
}
process.stdout.write(JSON.stringify(rows));
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True, timeout=90,
                                input=json.dumps(dict(site=(ROOT / 'assets/site.css').read_text(), old=before, new=css, cases=CASES)))
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.styles = {(r['width'], r['height'], r['home'], r['opened'], r['version']): r['styles'] for r in json.loads(result.stdout)}

    def test_narrow_home_and_unclassified_cascades_are_exactly_unchanged(self):
        for width, h in CASES:
            for home in ('false', 'true', 'missing'):
                for opened in (False, True):
                    if width < 1200 or home != 'false':
                        with self.subTest(width=width, height=h, home=home, opened=opened):
                            self.assertEqual(self.styles[width, h, home, opened, 'new'], self.styles[width, h, home, opened, 'old'])

    def test_only_three_approved_declarations_change_in_ready_desktop(self):
        for width, h in CASES:
            if width < 1200:
                continue
            for opened in (False, True):
                old = self.styles[width, h, 'false', opened, 'old']
                new = copy.deepcopy(self.styles[width, h, 'false', opened, 'new'])
                for key in ('ancestry', 'tools'):
                    for prop in ('padding', 'padding-top', 'padding-bottom'):
                        new[key][prop] = old[key][prop]
                new['tools']['min-height'] = old['tools']['min-height']
                if opened:
                    new['toolsMenu']['top'] = old['toolsMenu']['top']
                self.assertEqual(new, old)

    def test_1440_and_1920_sibling_full_boxes_fit_original_rows_without_overlap(self):
        for width, h in ((1440, 900), (1920, 1080)):
            style = self.styles[width, h, 'false', False, 'new']
            self.assertEqual(style['bar']['grid-template-rows'], '36px 36px')
            self.assertEqual(style['bar']['height'], '84px')
            self.assertEqual(style['ancestry']['font-size'], '15px')
            self.assertEqual(style['tools']['font-size'], '16px')
            a, t = measured_boxes(height(style['ancestry']), height(style['tools']))
            self.assertEqual((a['height'], t['height']), (28, 34))
            self.assertFalse(overlap(a, t))
            self.assertEqual(t['y'] - a['y'] - a['height'], 5)
            # Also reject small edge collisions that five sample points could miss.
            tab = rect(257.046875, 261.890625, 80.015625, 34)
            self.assertFalse(overlap(a, tab))
            SCREENSHOTS.check_chrome_text(tools_proof(a, t), '阅读工具', 16, rect(0, 65, 1425, 835), rect(0, 0, width, h))

    def test_old_receipt_and_partial_repair_retain_true_overlap_negatives(self):
        a, t = measured_boxes(40.5, 44.390625)
        self.assertEqual(t['y'], 256.703125)
        self.assertEqual(a['y'] + a['height'] - t['y'], 6.4375)
        p = tools_proof(a, t)
        self.assertTrue(p['fragments'][0]['visible'])
        self.assertFalse(p['visible'])
        with self.assertRaisesRegex(RuntimeError, 'Desktop chrome text'):
            SCREENSHOTS.check_chrome_text(p, '阅读工具', 16, rect(0, 0, 1440, 900))
        # Shrinking only tools leaves the ancestry's 1.25px tab collision.
        a, t = measured_boxes(40.5, 34)
        self.assertTrue(overlap(a, rect(257.046875, 261.890625, 80.015625, 34)))
        self.assertEqual(a['y'] + a['height'] - 261.890625, 1.25)

    def test_open_menus_clear_their_own_full_triggers_by_four_pixels(self):
        for width, h in ((1440, 900), (1920, 1080)):
            s = self.styles[width, h, 'false', True, 'new']
            for control, menu in (('ancestry', 'ancestryMenu'), ('tools', 'toolsMenu')):
                box = height(s[control])
                self.assertEqual(anchor(s[menu]['top'], box) - box, 4)
            self.assertLess(anchor('30px', height(s['tools'])) - height(s['tools']), 0)

    def test_original_chrome_gate_still_rejects_restyled_clipped_or_covered_text(self):
        a, t = measured_boxes(28, 34)
        for mutate in (lambda p: p.update(visible=False), lambda p: p.update(fontSize=15),
                       lambda p: p.update(clipped=True), lambda p: p.update(text='工具'),
                       lambda p: p['fragments'][0].update(visible=False)):
            p = tools_proof(a, t)
            mutate(p)
            with self.assertRaises(RuntimeError):
                SCREENSHOTS.check_chrome_text(p, '阅读工具', 16, rect(0, 0, 1440, 900))


if __name__ == '__main__':
    unittest.main()
