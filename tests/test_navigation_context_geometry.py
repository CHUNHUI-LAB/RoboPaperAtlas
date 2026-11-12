"""Context anchoring regression from run 38438954302; CSSOM is not pixel evidence.

The failing Chrome receipt measured a 40.5px summary and an 8.5px panel
overlap. These tests apply the actual CSS anchor to those measurements and
taller triggers, then retain the unchanged screenshot readability checker.
Only a new Chrome capture can establish the final rendered geometry.
"""
import copy
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('context_geometry_screenshots', ROOT / 'scripts/navigation_screenshots.py')
SCREENSHOTS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCREENSHOTS)
SELECTOR = '.np-ancestry-disclosure[open]>.np-context-local'
ANCHOR = '@media (min-width:1200px) { ' + SELECTOR + ' {top:calc(100% + 4px);} }'


def rect(x, y, width, height):
    return dict(x=x, y=y, width=width, height=height)


def resolved_top(value, parent_height):
    """Resolve only the two CSS expressions involved in this regression."""
    fixed = re.fullmatch(r'(\d+(?:\.\d+)?)px', value)
    relative = re.fullmatch(r'calc\(100% \+ (\d+(?:\.\d+)?)px\)', value)
    if fixed:
        return float(fixed[1])
    if relative:
        return parent_height + float(relative[1])
    raise ValueError('Unsupported anchor expression: ' + value)


def contains(area, x, y):
    return area['x'] <= x <= area['x'] + area['width'] and area['y'] <= y <= area['y'] + area['height']


def fixture(top, summary_height=40.5, width=1440, opened=True):
    # Exact failing summary coordinates and dimensions from the Chrome receipt.
    summary = rect(279.8125, 222.640625, 172.703125, summary_height)
    entry = rect(16, summary['y'] + (summary_height - 28) / 2, 253.8125, 28)
    popover = rect(summary['x'], summary['y'] + resolved_top(top, summary_height), 820, 90)
    points = [(summary['x'] + summary['width'] * x, summary['y'] + summary_height * y)
              for x, y in ((.5, .5), (.1, .1), (.9, .1), (.1, .9), (.9, .9))]

    def proof(text, area):
        return dict(text=text, rect=area, visible=True, opaque=True, unscaled=True, clipped=False,
                    fontSize=15, foreground=[45, 82, 67], background=[250, 250, 248],
                    fragments=[dict(area, visible=True)])

    def button(id_, text, area):
        result = proof(text, area)
        if not opened:
            result.update(visible=False, fragments=[])
        return dict(id=id_, text=text, title=text, aria=text, proof=result)

    summary_proof = proof('挑战–思路树 · 原树路径', summary)
    summary_proof['visible'] = not opened or all(not contains(popover, x, y) for x, y in points)
    # The original failure retained fully visible text despite the covered box.
    summary_proof['fragments'] = [dict(rect(295.703125, 233.640625, 156.8125, 18), visible=True)]
    globals_ = [dict(id='goal', proof=proof('领域', rect(20, entry['y'] + 2, 35, 24))),
                dict(id='scope', proof=proof('AudioGoal', rect(60, entry['y'] + 2, 200, 24)))]
    return dict(route=dict(tree='c', node='pos:c:6dcc2ce43c02d908266f20'),
                expectedIds=['root-c', 'insight'], localIds=['root-c', 'insight'], localTrees=['c', 'c'],
                expectedGlobalIds=['goal', 'scope'], globalIds=['goal', 'scope'], globalSeparators=0,
                labels=['领域', '挑战–思路树'], viewport=rect(0, 0, width, 900),
                desktopDisclosure=dict(tag='DETAILS', open=opened, summary=summary_proof,
                    compactRows=[entry, summary], popover=popover,
                    localLabel=proof('挑战–思路树', rect(popover['x'] + 14, popover['y'] + 14, 120, 24)),
                    expectedLocalLabels=['完整原始任务', '完整原始问题'], globalButtons=globals_,
                    localButtons=[button('root-c', '完整原始任务', rect(popover['x'] + 150, popover['y'] + 14, 250, 24)),
                                  button('insight', '完整原始问题', rect(popover['x'] + 14, popover['y'] + 48, 700, 24))]))


class ContextGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        css = (ROOT / 'assets/navigation-product.css').read_text()
        if css.count(ANCHOR) != 1:
            raise AssertionError('Desktop popover must anchor below the actual disclosure height')
        script = r"""
const assert=require('node:assert/strict'),{JSDOM}=require('jsdom');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
function active(queries,width,height){return queries.map(query=>{
 if(query==='print'||/^\(prefers-reduced-motion:\s*reduce\)$/.test(query))return false;
 return query.split(/\s+and\s+/).map(part=>{
  const m=part.match(/^\((min|max)-(width|height):\s*(\d+)px\)$/);assert.ok(m,'unknown media '+query);
  const actual=m[2]==='width'?width:height;return m[1]==='min'?actual>=+m[3]:actual<=+m[3];
 }).every(Boolean);
}).every(Boolean);}
assert.throws(()=>active(['print','(unknown:1)'],1440,900),/unknown media/);
const rows=[];
for(const width of [600,601,1199,1200,1440,1920])for(const opened of [false,true])for(const version of ['old','new']){
 const dom=new JSDOM('<style></style><main id="navigation-product" data-load-state="ready"><section class="np-workspace"><div class="np-workspace-bar"><nav id="np-global-context" class="np-global-context"><details class="np-ancestry-disclosure" '+(opened?'open':'')+'><summary>挑战–思路树 · 原树路径</summary><div class="np-context-group np-context-local" data-path-kind="local-ancestry"><span class="np-context-label">挑战–思路树</span><button class="np-crumb">完整原始问题</button></div></details></nav></div></section></main>');
 try{
  const w=dom.window,d=w.document,style=d.querySelector('style');style.textContent=input.site+'\n'+input[version];
  const rules=[];function collect(list,media=[]){for(const rule of list){if(rule.media)collect(rule.cssRules,media.concat(rule.media.mediaText));else if(rule.selectorText)rules.push({rule,media});}}collect(style.sheet.cssRules);
  style.textContent=rules.filter(x=>active(x.media,width,900)).map(x=>x.rule.cssText).join('\n');
  function computed(selector){const s=w.getComputedStyle(d.querySelector(selector));return Object.fromEntries([...new Set([...Array.from(s),'padding-top','padding-bottom'])].map(k=>[k,s.getPropertyValue(k)]));}
  rows.push({width,opened,version,summary:computed('summary'),details:computed('details'),popover:computed('.np-context-local'),crumb:computed('.np-crumb')});
 }finally{dom.window.close();}
}
process.stdout.write(JSON.stringify(rows));
"""
        result = subprocess.run(['node', '-e', script], cwd=ROOT, text=True, capture_output=True,
                                input=json.dumps(dict(site=(ROOT / 'assets/site.css').read_text(),
                                                      old=css.replace(ANCHOR, ''), new=css)), timeout=60)
        if result.returncode:
            raise AssertionError(result.stdout + result.stderr)
        cls.styles = {(x['width'], x['opened'], x['version']): x for x in json.loads(result.stdout)}

    def test_only_open_desktop_top_changes_in_actual_cascade(self):
        for width in (600, 601, 1199, 1200, 1440, 1920):
            for opened in (False, True):
                with self.subTest(width=width, opened=opened):
                    old = copy.deepcopy(self.styles[width, opened, 'old'])
                    new = copy.deepcopy(self.styles[width, opened, 'new'])
                    del old['version'], new['version']
                    if opened and width >= 1200:
                        self.assertEqual(old['popover']['top'], '32px')
                        self.assertEqual(new['popover']['top'], 'calc(100% + 4px)')
                        new['popover']['top'] = old['popover']['top']
                    self.assertEqual(new, old)
        mobile = self.styles[600, True, 'new']['popover']
        self.assertEqual(mobile['position'], 'fixed')
        self.assertEqual(mobile['top'], 'calc(var(--site-header-height,64px) + 12px)')

    def test_real_summary_height_keeps_font_padding_and_box(self):
        for width in (1200, 1440, 1920):
            style = self.styles[width, True, 'new']['summary']
            self.assertEqual(style['font-size'], '15px')
            self.assertEqual(style['line-height'], '1.5')
            self.assertEqual(style['min-height'], '28px')
            self.assertEqual(style['padding-top'], '9px')
            self.assertEqual(style['padding-bottom'], '9px')
            self.assertEqual(15 * 1.5 + 9 + 9, 40.5)
            self.assertEqual(self.styles[width, True, 'new']['details']['position'], 'relative')
            self.assertEqual(self.styles[width, True, 'new']['popover']['position'], 'absolute')

    def test_old_32px_anchor_reproduces_real_8_5px_overlap_and_gate_failure(self):
        data = fixture('32px')
        d = data['desktopDisclosure']
        self.assertEqual(d['popover']['y'], 254.640625)
        self.assertEqual(d['summary']['rect']['y'] + d['summary']['rect']['height'] - d['popover']['y'], 8.5)
        self.assertTrue(d['summary']['fragments'][0]['visible'])
        self.assertFalse(d['summary']['visible'])
        with self.assertRaisesRegex(RuntimeError, 'summary is hidden, covered or misplaced'):
            SCREENSHOTS.check_context_path(data)

    def test_actual_and_wrapped_summary_anchor_preserves_open_close_reopen_gates(self):
        for width in (1200, 1440, 1920):
            top = self.styles[width, True, 'new']['popover']['top']
            # 28 is the old assumed box; 40.5 is measured; 63 and 85.5 model
            # two/three 22.5px lines with the unchanged 18px vertical padding.
            for height in (28, 40.5, 63, 85.5):
                for opened in (False, True, False, True, False):
                    with self.subTest(width=width, height=height, opened=opened):
                        data = fixture(top, height, width, opened)
                        d = data['desktopDisclosure']
                        self.assertEqual(d['popover']['y'] - d['summary']['rect']['y'] - height, 4)
                        # Fit the unwrapped text rectangle into the legacy 28px
                        # reference box; measured 40.5px coordinates stay exact.
                        if height == 28:
                            d['summary']['fragments'][0]['y'] = d['summary']['rect']['y'] + 5
                        SCREENSHOTS.check_context_path(data)
        self.assertEqual(fixture('calc(100% + 4px)')['desktopDisclosure']['popover']['y'], 267.140625)

    def test_unmodified_checker_still_rejects_cover_clip_font_and_ancestry_errors(self):
        mutations = [lambda d: d['summary'].update(visible=False),
                     lambda d: d['summary'].update(fontSize=14),
                     lambda d: d['summary']['fragments'][0].update(visible=False),
                     lambda d: d['localButtons'][0]['proof'].update(clipped=True),
                     lambda d: d['localButtons'][0].update(text='缩写'),
                     lambda d: d['popover'].update(y=880)]
        for mutate in mutations:
            data = fixture('calc(100% + 4px)')
            mutate(data['desktopDisclosure'])
            with self.assertRaises(RuntimeError):
                SCREENSHOTS.check_context_path(data)
        with self.assertRaises(ValueError):
            resolved_top('auto', 40.5)


if __name__ == '__main__':
    unittest.main()
