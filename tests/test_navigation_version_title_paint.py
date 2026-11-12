"""Native-title paint protocol regression tests, not real-browser acceptance."""
import copy
import base64
import inspect
import json
from pathlib import Path
import subprocess
import struct
import tempfile
import unittest
from unittest.mock import patch

import test_navigation_screenshots as existing

MODULE = existing.MODULE


class NativeVersionTitlePaintChecks(unittest.TestCase):
    def probe(self, **case):
        script = r"""
const {JSDOM}=require('jsdom'),input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case;
const dom=new JSDOM('<main class="native-main"><details data-native-position="title" open><summary id="title">Full original title<span>role</span></summary></details></main><aside id="outside"></aside>');
global.document=dom.window.document;
const summary=document.querySelector('summary'),selector='[data-native-position="title"] > summary';
let now=0,nextId=1,queue=[],answer=null,callbacks=0,inspections=0;
global.performance={now:()=>now};
global.setTimeout=(fn,delay)=>{const id=nextId++;queue.push({id,at:now+delay,fn});return id;};
global.clearTimeout=id=>{queue=queue.filter(t=>t.id!==id);};
global.requestAnimationFrame=fn=>c.frozenFrames?nextId++:setTimeout(fn,16);
global.cancelAnimationFrame=clearTimeout;
class Transition{
 constructor(start,end){this.start=start;this.end=end;this.transitionProperty='background-color';this.effect={target:summary,getComputedTiming:()=>({duration:c.infinite?Infinity:end-start,endTime:c.infinite?Infinity:end-start})};}
 get playState(){return c.paused?'paused':now<this.end||c.stuck||c.pending?'running':'finished';}
 get pending(){return !!c.pending;}
 get currentTime(){return c.pending?null:Math.min(now-this.start,this.end-this.start);}
 get playbackRate(){return c.reverse?-1:1;}
 finish(){throw Error('Must not finish animation');}
 cancel(){throw Error('Must not cancel animation');}
}
global.CSSTransition=Transition;
let transitions=c.none?[]:c.replacement?[new Transition(0,48),new Transition(48,208)]:[new Transition(0,160)];
for(const e of document.querySelectorAll('*'))e.getAnimations=()=>[];
document.getElementById('outside').getAnimations=()=>{throw Error('Unrelated surface inspected');};
summary.getAnimations=opts=>{inspections++;if(!opts||typeof opts.subtree!=='boolean')throw Error('Explicit animation scope missing');
 if(c.churn)transitions.push(new Transition(now,now+1));
 return transitions.filter(a=>a.start<=now&&(now<a.end||c.stuck||c.pending||c.paused||c.infinite||c.reverse));};
global.getComputedStyle=e=>{
 const running=!c.none&&now<(c.replacement?208:160),active=e===summary;
 const backgroundColor=active&&c.unknown?'color(display-p3 1 1 1)':active&&(running||c.alpha)?'rgba(240, 244, 239, 0.42)':active&&c.hoverIn?'rgb(240, 244, 239)':e===document.body?'rgb(250, 250, 248)':'rgba(0, 0, 0, 0)';
 return {color:c.lowContrast?'rgb(245, 245, 245)':'rgb(23, 26, 25)',backgroundColor,
  borderTopColor:'rgb(49, 92, 75)',borderRightColor:'rgb(49, 92, 75)',borderBottomColor:'rgb(49, 92, 75)',borderLeftColor:'rgb(49, 92, 75)'};
};
if(c.unsupported)global.CSSTransition=undefined;
if(c.missing)summary.remove();
if(c.duplicate)summary.after(summary.cloneNode(true));
if(c.disappear)setTimeout(()=>summary.remove(),48);
if(c.replaceRoot)setTimeout(()=>{const replacement=summary.cloneNode(true);replacement.getAnimations=summary.getAnimations;summary.replaceWith(replacement);},48);
const raw=()=>new Function(input.diagnostic+'\nreturn nativeVersionTitlePaint(arguments[0]);')(summary);
const colors=()=>new Function(input.visual+'\nreturn {background:bg(arguments[0]),foreground:color(getComputedStyle(arguments[0]).color).rgb};')(summary);
const before=raw(),beforeColors=colors();
new Function(input.script)(2000,selector,value=>{answer=value;callbacks++;});
let steps=0;while(queue.length&&steps++<1000){queue.sort((a,b)=>a.at-b.at||a.id-b.id);const item=queue.shift();now=item.at;item.fn();}
if(!answer||steps>=1000)throw Error('Unbounded native paint settlement');
process.stdout.write(JSON.stringify({answer,callbacks,inspections,before,beforeColors,after:raw(),afterColors:colors()}));
dom.window.close();
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps(dict(
            case=case, script=MODULE.VERSION_TITLE_PAINT_SETTLE_JS,
            diagnostic=MODULE.VERSION_TITLE_PAINT_DIAGNOSTIC_JS, visual=MODULE.VISUAL_GEOMETRY)),
            text=True, capture_output=True, cwd=Path(__file__).parents[1], timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def fixture(self):
        # Reuse the original independent title/source fixture and all its gates.
        if not hasattr(existing.VersionTitleCaptureChecks, 'expected'):
            import gzip
            import sys
            with patch.object(sys, 'path', [str(Path(__file__).parents[1] / 'scripts'), *sys.path]):
                science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
                existing.VersionTitleCaptureChecks.expected = MODULE.version_title_expected(science)
        return existing.VersionTitleCaptureChecks.fixture()

    def test_transient_alpha_settles_naturally_with_original_raw_diagnostics(self):
        data = self.probe()
        self.assertEqual(data['beforeColors']['background'], [])
        self.assertEqual(data['answer']['status'], 'settled')
        self.assertEqual(data['answer']['elapsedMs'], 176)
        self.assertEqual(data['callbacks'], 1)
        self.assertEqual(data['answer']['scopeSelector'], '[data-native-position="title"] > summary')
        self.assertEqual(data['before']['layers'][0]['backgroundColor'], 'rgba(240, 244, 239, 0.42)')
        self.assertEqual(data['after']['layers'][0]['backgroundColor'], 'rgba(0, 0, 0, 0)')
        self.assertEqual(data['afterColors']['background'], [250, 250, 248])
        self.assertEqual(data['after']['transitions'], [])
        self.assertIsNone(data['after']['error'])
        self.assertEqual(len(data['answer']['observedTransitions']), 1)

    def test_no_transition_and_replacement_have_bounded_quiet_frames(self):
        for case, elapsed, count in ((dict(none=True), 32, 0), (dict(replacement=True), 224, 2)):
            with self.subTest(case=case):
                result = self.probe(**case)['answer']
                self.assertEqual(result['status'], 'settled')
                self.assertEqual(result['elapsedMs'], elapsed)
                self.assertEqual(len(result['observedTransitions']), count)

    def test_hover_in_preserves_the_actual_opaque_background(self):
        data = self.probe(hoverIn=True)
        self.assertEqual(data['answer']['status'], 'settled')
        self.assertEqual(data['beforeColors']['background'], [])
        self.assertEqual(data['afterColors']['background'], [240, 244, 239])
        self.assertEqual(data['after']['layers'][0]['backgroundColor'], 'rgb(240, 244, 239)')

    def test_stuck_pending_and_frozen_frames_timeout_without_retry(self):
        for case in (dict(stuck=True), dict(pending=True), dict(frozenFrames=True)):
            with self.subTest(case=case):
                data = self.probe(**case)
                self.assertEqual(data['answer']['status'], 'timeout')
                self.assertEqual(data['answer']['elapsedMs'], 2000)
                self.assertEqual(data['callbacks'], 1)

    def test_invalid_timing_identity_and_missing_api_fail_closed(self):
        for case in (dict(infinite=True), dict(paused=True), dict(reverse=True), dict(unsupported=True),
                     dict(missing=True), dict(duplicate=True), dict(disappear=True), dict(replaceRoot=True), dict(churn=True)):
            with self.subTest(case=case):
                data = self.probe(**case)
                self.assertEqual(data['answer']['status'], 'error')
                self.assertLess(data['answer']['elapsedMs'], 2000)
                self.assertEqual(data['callbacks'], 1)

    def test_unknown_color_persistent_alpha_and_low_contrast_still_fail_original_gate(self):
        for case in (dict(unknown=True), dict(alpha=True), dict(lowContrast=True)):
            with self.subTest(case=case):
                result = self.probe(**case)
                self.assertEqual(result['answer']['status'], 'settled')
                data, expected = self.fixture()
                for proof in (data['title'], *data['title']['textRuns']):
                    proof.update(result['afterColors'])
                with self.assertRaises(RuntimeError):
                    MODULE.check_version_title_capture(data, expected, require_navigation=False)

    def test_settled_paint_does_not_exempt_occlusion_or_geometry(self):
        for mutate in (lambda p:p.update(visible=False), lambda p:p.update(opaque=False),
                       lambda p:p.update(unscaled=False), lambda p:p.update(fontSize=15),
                       lambda p:p.update(clipped=True), lambda p:p['rect'].update(y=899)):
            data, expected = self.fixture()
            mutate(data['title'])
            with self.assertRaises(RuntimeError):
                MODULE.check_version_title_capture(data, expected, require_navigation=False)

    def test_png_bracket_requires_identical_dom_and_no_active_or_unknown_paint(self):
        data, _ = self.fixture()
        data['paint'] = dict(layers=[dict(tag='SUMMARY', color='rgb(23, 26, 25)', backgroundColor='rgba(0, 0, 0, 0)')], transitions=[], error=None)
        MODULE.check_version_title_capture_stability(data, copy.deepcopy(data))
        for mutate in (lambda d:d['paint'].update(error='unavailable'), lambda d:d['paint'].update(transitions=[dict(playState='running')]),
                       lambda d:d['paint'].update(layers=[]), lambda d:d.pop('paint'),
                       lambda d:d['paint']['layers'][0].update(backgroundColor='rgb(240, 244, 239)'),
                       lambda d:d['title']['rect'].update(y=351), lambda d:d.update(focusedSummary=False),
                       lambda d:d['title'].update(renderedText='changed'), lambda d:d.update(windowScroll=401)):
            after = copy.deepcopy(data); mutate(after)
            with self.assertRaises(RuntimeError):
                MODULE.check_version_title_capture_stability(data, after)

    def test_equal_but_active_or_unknown_paint_cannot_pass_by_equality(self):
        data, _ = self.fixture()
        for paint in (dict(layers=[{}],transitions=[],error='unavailable'),
                      dict(layers=[],transitions=[],error=None),
                      *(dict(layers=[{}],transitions=[dict(playState=state,pending=pending)],error=None)
                        for state,pending in (('running',False),('paused',False),('idle',True)))):
            data['paint'] = paint
            with self.subTest(paint=paint), self.assertRaises(RuntimeError):
                MODULE.check_version_title_capture_stability(data,copy.deepcopy(data))

    def test_timeout_receipt_is_saved_before_failure_with_exact_scope_and_budget(self):
        good = self.probe(none=True)['answer']
        selector = good['scopeSelector']
        test = self
        class Driver:
            def __init__(self, value): self.value = value
            def call(self, method, path, payload):
                test.assertEqual((method, path), ('POST', '/execute/async'))
                test.assertEqual(payload, dict(script=MODULE.VERSION_TITLE_PAINT_SETTLE_JS, args=[2000, selector]))
                return self.value
        mutations = (lambda d:None, lambda d:d.update(status='timeout'), lambda d:d.update(scopeSelector='other'),
                     lambda d:d.update(timeoutMs=9999), lambda d:d.update(elapsedMs=2000), lambda d:d.update(elapsedMs=float('nan')),
                     lambda d:d.update(elapsedMs=True), lambda d:d.update(before=None), lambda d:d.update(after=None))
        for i, mutate in enumerate(mutations):
            value=copy.deepcopy(good); mutate(value); report={}; saved=[]
            call=lambda:MODULE.settle_version_title_paint(Driver(value),report,lambda:saved.append(copy.deepcopy(report)),'langmap',selector)
            if i:
                with self.assertRaises(RuntimeError): call()
            else: self.assertEqual(call(), value)
            self.assertEqual(saved, [report])

    def test_capture_order_has_one_wait_then_png_bracket_and_original_gate(self):
        source = inspect.getsource(MODULE.version_title_checks)
        start=source.index('settle_version_title_paint(')
        before=source.index('data = driver.js(VERSION_TITLE_SNAPSHOT_JS',start)
        screenshot=source.index("driver.call('GET', '/screenshot')",before)
        after=source.index('after_capture = driver.js(VERSION_TITLE_SNAPSHOT_JS',screenshot)
        save=source.index('save()',after)
        stable=source.index('check_version_title_capture_stability(',save)
        gate=source.index('check_version_title_capture(data, expected, require_navigation=False)',stable)
        self.assertLess(start,before);self.assertLess(before,screenshot);self.assertLess(screenshot,after)
        self.assertLess(after,save);self.assertLess(save,stable);self.assertLess(stable,gate)
        self.assertEqual(source.count('settle_version_title_paint('),1)
        self.assertNotIn('settle(',source[screenshot:after])
        for forbidden in ('.finish(', '.cancel(', '.style', 'sleep(', 'time.sleep', 'check_task_route_proof'):
            self.assertNotIn(forbidden, inspect.getsource(MODULE.settle_version_title_paint))

    def test_actual_capture_flow_saves_both_sides_before_rejecting_drift_or_bad_proof(self):
        class StopAfterNativeGate(Exception): pass
        test = self
        for case in ('stable', 'png-color-change', 'png-focus-change', 'unknown-background', 'covered', 'post-unavailable'):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as tmp:
                data, expected = self.fixture()
                # Keep exactly the browser-snapshot fields; transport evidence is
                # supplied separately by the fake protocol, as in the real flow.
                for key in ('sourceBinding', 'nativeActions', 'renderedFonts', 'pngDimensions',
                            'pixelVariation', 'screenshotSha256', 'console', 'networkFailures', 'enhancedNavigation'):
                    data.pop(key, None)
                data['paint'] = dict(layers=[dict(tag='SUMMARY', color='rgb(24, 49, 61)', backgroundColor='rgb(251, 252, 249)')], transitions=[], error=None)
                if case == 'unknown-background':
                    data['title']['background'] = []
                    data['title']['textRuns'][0]['background'] = []
                if case == 'covered': data['title']['visible'] = False
                post = copy.deepcopy(data)
                if case == 'png-color-change': post['paint']['layers'][0]['backgroundColor'] = 'rgb(240, 244, 239)'
                if case == 'png-focus-change': post['focusedSummary'] = False
                events=[]
                class Driver:
                    def __init__(self): self.snapshots=0
                    def settle(self): events.append('frames')
                    def selector(self, selector): return selector
                    def click(self, selector):
                        if selector.endswith(' > .native-body > p > a'):
                            events.append('native-link')
                            raise StopAfterNativeGate()
                        events.append('summary-click')
                    def js(self, script, *args):
                        if script == MODULE.VERSION_TITLE_SNAPSHOT_JS:
                            events.append('pre' if self.snapshots == 0 else 'post')
                            if self.snapshots and case == 'post-unavailable':
                                raise RuntimeError('Exact native title occurrence missing or duplicated')
                            value=copy.deepcopy(data if self.snapshots == 0 else post)
                            self.snapshots+=1
                            return value
                        if 'scrollIntoView' in script: events.append('scroll'); return None
                        if 'return n[0].open;' in script: return False
                        if 'return document.querySelector(arguments[0]).open;' in script: return True
                        raise AssertionError('Unexpected JS: '+script)
                    def cdp(self, command, params):
                        if command == 'DOM.getDocument': return dict(root=dict(nodeId=1))
                        if command == 'DOM.querySelector': return dict(nodeId=2)
                        if command == 'CSS.getPlatformFontsForNode':
                            events.append('fonts')
                            return dict(fonts=[dict(familyName='Noto Sans',glyphCount=80)])
                        raise AssertionError(command)
                    def call(self, method, path, payload=None):
                        if path == '/url': events.append('url'); return None
                        if path == '/execute/async':
                            events.append('paint-wait')
                            test.assertEqual(payload['script'], MODULE.VERSION_TITLE_PAINT_SETTLE_JS)
                            return dict(status='settled',scopeSelector=payload['args'][1],timeoutMs=2000,elapsedMs=32,
                                        before=dict(colors=[data['paint']['layers'][0]]),after=dict(colors=[data['paint']['layers'][0]]))
                        if path == '/screenshot':
                            events.append('png')
                            return base64.b64encode(b'\x89PNG\r\n\x1a\n'+b'\x00'*8+struct.pack('>II',1440,900)).decode()
                        if path == '/log': return []
                        raise AssertionError(path)
                report={'captures':[]}; saved=[]
                def save():
                    events.append('save')
                    saved.append(copy.deepcopy(report))
                with patch.object(MODULE,'version_title_expected',return_value=[expected]), patch.object(MODULE,'png_has_visible_variation',return_value=True):
                    wanted=StopAfterNativeGate if case == 'stable' else RuntimeError
                    with self.assertRaises(wanted):
                        MODULE.version_title_checks(Driver(),report,save,'1440x900','http://fixture/',{},Path(tmp))
                start=events.index('paint-wait')
                self.assertEqual([e for e in events[start:] if e in ('pre','post','png','paint-wait','frames','fonts')],
                                 ['paint-wait','pre','png','post'])
                self.assertLess(events.index('fonts'),start)
                captured=saved[-1]['captures'][0]
                self.assertEqual(captured['captureAfter'],dict(snapshotError='Exact native title occurrence missing or duplicated') if case == 'post-unavailable' else post)
                self.assertEqual(captured['title'],data['title'])
                self.assertEqual(saved[-1]['versionTitlePaintSettles'][0]['settle']['status'],'settled')
                self.assertEqual((Path(tmp)/(captured['name']+'.png')).read_bytes()[:8],b'\x89PNG\r\n\x1a\n')
                self.assertEqual('native-link' in events,case == 'stable')


if __name__ == '__main__':
    unittest.main()
