"""Synthetic protocol/negative tests only; real scroll and pixels belong to PR Chrome."""
import copy
import gzip
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('disclosure_capture', ROOT / 'scripts/navigation_screenshots.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def source():
    return json.loads(gzip.decompress((ROOT / 'data/navigation-product/model.json.gz').read_bytes()))


def text_proof(text, area):
    fragment = dict(area, visible=True)
    return dict(text=text, renderedText=text, rect=area.copy(), visible=True, opaque=True, unscaled=True, clipped=False,
                fontSize=15, foreground=[32, 52, 63], background=[255, 255, 255], clipAreas=[], fragments=[fragment],
                textRuns=[dict(text=text, opaque=True, unscaled=True, fontSize=15, foreground=[32, 52, 63],
                               background=[255, 255, 255], clipAreas=[], fragments=[fragment.copy()])])


def focus(scope=None, summary=None):
    return dict(id='np-scope-entry-' + scope if scope else '', tag='BUTTON' if scope else 'SUMMARY', summaryFor=summary, scope=scope)


def fixture(expected, identity='np-all-scopes', width=1440):
    height = 900 if width == 1440 else 1080
    area = dict(x=16, y=150, width=width - 32, height=height - 154)
    def frame(name, rect, opened=False):
        client = dict(x=rect['x'] + 1, y=rect['y'] + 1, width=rect['width'] - 2, height=rect['height'] - 2)
        return dict(id=name, tag='DETAILS', open=opened, rect=rect, clientRect=client, top=0, left=0,
                    scrollHeight=2000, clientHeight=client['height'], scrollWidth=client['width'], clientWidth=client['width'],
                    maxTop=2000 - client['height'], overflowX='auto', overflowY='auto', paddingBottom=0,
                    maxHeight=str(rect['height']) + 'px', borderTop=1, borderRight=1, borderBottom=1, borderLeft=1,
                    opaque=True, unscaled=True)
    landing = frame('np-reading-landing', area)
    landing['paddingBottom'] = 4
    toolbar = frame('', dict(x=16, y=150, width=width - 32, height=28))
    panels = []
    for name, _, label in M.S0_TOOLBAR_LABELS[:4]:
        cap = min(324 if name == 'np-task-relations' else height - 240, height - 5 - 4 - 178)
        panel = frame(name, dict(x=17, y=178, width=1060 if name != 'np-task-relations' else 420, height=cap), name == identity)
        panel.update(count=1, topology=True, summary=text_proof(label, dict(x=28, y=180, width=200, height=24)))
        panels.append(panel)
    data = dict(ready='ready', home=True, route=dict(tree='g', scope='scope:all', node='original-root'), historyLength=20, scale=1,
                originTrail=[], historyOriginTrail=[], expanded=dict(g=['original-root']), selected=dict(g='original-root'), selectedRelation=None,
                window=dict(x=0, y=0), viewport=dict(x=0, y=0, width=width, height=height),
                stationaryAncestors=[dict(selector=s, top=0, left=0) for s in M.STATIONARY_SHELL_SELECTORS],
                landing=landing, toolbar=toolbar, panels=panels, focus=focus(summary=identity), directory=[],
                comparisonOrder=expected['comparisonOrder'].copy(), comparisonLast=None, requested=identity, targets=[])
    data['historyRoute'] = data['route'].copy()
    for row in expected['directory']:
        data['directory'].append(dict(row, domParent=row['parent'], id='np-scope-entry-' + row['scope'], tag='BUTTON', type='button', disabled=False, tabIndex=0))
    for spec in expected['targets'][identity]:
        data['targets'].append(dict(selector=spec['selector'], count=1, tag='A' if spec.get('url') else 'BUTTON', id='', scope=None,
                                    disabled=False, tabIndex=0, panel=identity, url=spec.get('url'),
                                    proof=text_proof(spec['text'], dict(x=30, y=240, width=390, height=24))))
    if identity == 'np-overview-comparison':
        data['comparisonLast'] = dict(id=expected['comparisonLast'], cells=5, rect=dict(x=30, y=240, width=1000, height=220))
    return data


class FakeDriver:
    """Executes the requested native protocol against explicit synthetic geometry."""
    def __init__(self, expected, failure=None):
        self.expected, self.failure = expected, failure
        self.open = {name: name == 'np-all-scopes' for name in M.DISCLOSURE_IDS}
        self.top = dict.fromkeys(M.DISCLOSURE_IDS, 0)
        self.active = focus(scope='task:dialnav')
        self.events, self.installed, self.stopped, self.calls = [], False, False, []
        self.owner = None
        self.wheel_count = dict.fromkeys(M.DISCLOSURE_IDS, 0)
        self.url, self.session = 'http://localhost', 'synthetic'

    def remaining(self):
        if self.failure == 'deadline':
            raise TimeoutError('fixed input deadline')
        return M.DISCLOSURE_AUDIT_SECONDS

    def snapshot(self, identity):
        data = fixture(self.expected, identity)
        for panel in data['panels']:
            panel['open'], panel['top'] = self.open[panel['id']], self.top[panel['id']]
            if self.failure == 'fitting' and panel['id'] in ('np-task-relations', 'np-overview-notes'):
                panel['scrollHeight'] = panel['clientHeight']; panel['maxTop'] = 0
        data['focus'] = self.active.copy()
        if self.failure == 'unknown-paint' and self.top[identity] > 0:
            data['targets'][-1]['proof']['background'] = []
        if self.failure == 'fractional-hidden-tail' and self.top[identity] > 0:
            data['targets'][-1]['proof']['visible'] = False
        return data

    def js(self, script, *args):
        if script == M.DISCLOSURE_SNAPSHOT_JS:
            return self.snapshot(args[0])
        if script != M.DISCLOSURE_PROBE_JS:
            raise AssertionError('Unexpected JS operation')
        mode = args[0]
        if mode == 'start':
            if self.failure == 'start-before-install':
                raise TimeoutError('original start request failure')
            self.owner = args[2]
            self.installed = True
            if self.failure == 'start-after-install':
                raise TimeoutError('original start response failure')
            return True
        if mode == 'reset':
            self.events = []
            return True
        if mode == 'stop':
            self.stopped = True
            absent = not self.installed
            self.installed = False
        else:
            absent = False
        return dict(owner=args[1], events=copy.deepcopy(self.events), overflow=0, limit=276, cleanedUp=mode == 'stop', absent=absent)

    def selector(self, selector):
        return selector

    def event(self, kind, target=None, key=None, panel=None):
        self.events.append(dict(type=kind, key=key, trusted=True, target=(target or self.active).copy(), panel=panel))

    def click(self, selector):
        name = selector.split(' > ')[0][1:]
        self.open[name] = True
        if self.failure == 'fractional-wheel':
            self.top[name] = 0.25
        self.active = focus(summary=name)
        self.event('click', panel=name)

    def settle(self):
        pass

    def call(self, method, path, payload):
        self.calls.append(copy.deepcopy(payload))
        self.assert_path = (method, path)
        assert self.assert_path == ('POST', '/actions')
        group = payload['actions'][0]
        if group['type'] == 'wheel':
            name = next(name for name, opened in self.open.items() if opened)
            if self.failure == 'action':
                raise ValueError('original native action error')
            target = dict(id=name, tag='DETAILS', summaryFor=None, scope=None)
            self.event('wheel', target, panel=name)
            if self.failure != 'no-progress':
                panel = next(p for p in self.snapshot(name)['panels'] if p['id'] == name)
                offset = {'fractional-end-high': .375, 'fractional-end-low': -.375,
                          'fractional-hidden-tail': .375, 'premature-end': -1.25}.get(self.failure, 0)
                prior = self.top[name]
                self.top[name] = max(0, min(panel['maxTop'] + offset, prior + group['actions'][0]['deltaY']))
                self.wheel_count[name] += 1
                if self.failure == 'unstable-boundary' and self.wheel_count[name] == 2:
                    self.top[name] -= .125
                if self.top[name] != prior:
                    self.event('scroll', target, panel=name)
            return
        for action in group['actions']:
            code, kind = action['value'], action['type']
            key = 'Tab' if code == '\ue004' else 'Escape'
            self.event('keydown' if kind == 'keyDown' else 'keyup', key=key)
            if kind == 'keyUp':
                continue
            if key == 'Escape':
                name = next(name for name, opened in self.open.items() if opened)
                self.open[name] = False
                self.top[name] = 0
                self.active = focus(summary=name)
                self.event('focusin', panel=name)
            else:
                rows = self.expected['directory']; ids = [row['scope'] for row in rows]
                index = ids.index(self.active['scope']) + 1 if self.active['scope'] in ids else 0
                self.active = focus(scope=ids[index])
                if self.failure == 'unreachable':
                    self.active = focus(summary='np-all-scopes')
                self.event('focusin', panel='np-all-scopes')
                if self.failure == 'fractional-wheel' and index == 0:
                    self.top['np-all-scopes'] = 0.25
                if index == len(ids) - 1:
                    panel = next(p for p in self.snapshot('np-all-scopes')['panels'] if p['id'] == 'np-all-scopes')
                    self.top['np-all-scopes'] = panel['maxTop'] + {'fractional-end-high': .375, 'fractional-end-low': -.375}.get(self.failure, 0)


class DisclosureBoundsChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.science = source()
        cls.expected = M.disclosure_expected(cls.science)

    def test_source_order_and_endpoints_are_independent_of_dom(self):
        expected = self.expected
        self.assertEqual(len(expected['directory']), 64)
        self.assertEqual(expected['directory'][-1]['scope'], 'scope:all')
        self.assertEqual(expected['comparisonLast'], 'task:language-objectnav')
        self.assertEqual(expected['comparisonOrder'], [row[0] for row in M.TASK_INDEX])
        self.assertEqual(expected['targets']['np-overview-notes'][0]['text'], M.DISCLOSURE_NOTES_END)
        self.assertEqual(len(expected['targets']['np-overview-comparison']), 10)

    def test_four_independent_caps_and_all_end_texts(self):
        for width in (1440, 1920):
            for identity in M.DISCLOSURE_IDS:
                data = fixture(self.expected, identity, width)
                M.check_disclosure_snapshot(data, self.expected)
                M.check_disclosure_targets(data, self.expected)
                panel = next(p for p in data['panels'] if p['id'] == identity)
                self.assertEqual(panel['rect']['height'], 324 if identity == 'np-task-relations' else data['viewport']['height'] - 240)

    def test_fractional_padding_edge_does_not_depend_on_rounded_clientheight_or_css_variable(self):
        good = fixture(self.expected)
        landing = good['landing']; landing['rect']['height'] = 500.390625
        panel = good['panels'][0]
        room = landing['rect']['y'] + landing['rect']['height'] - landing['borderBottom'] - landing['paddingBottom'] - panel['rect']['y']
        panel['rect']['height'] = room
        panel['maxHeight'] = 'min(660px, 467.390625px)'
        panel['clientHeight'] = round(room - 2); panel['clientRect']['height'] = panel['clientHeight']
        panel['maxTop'] = panel['scrollHeight'] - panel['clientHeight']
        # clientHeight is integer; the cap is the measured fractional padding edge.
        landing['clientHeight'] = round(landing['rect']['height'] - 2)
        landing['clientRect']['height'] = landing['clientHeight']
        M.check_disclosure_snapshot(good, self.expected)
        bad = copy.deepcopy(good); bad['panels'][0]['rect']['height'] += .125
        with self.assertRaises(RuntimeError): M.check_disclosure_snapshot(bad, self.expected)

    def test_outer81_wrong_source_overcap_clip_and_missing_panel_fail(self):
        good = fixture(self.expected)
        mutations = [lambda d: d['landing'].update(top=81), lambda d: d['window'].update(y=1),
                     lambda d: d['stationaryAncestors'][0].update(top=81), lambda d: d['directory'].reverse(),
                     lambda d: d['directory'][0].update(text='shortened'), lambda d: d['directory'][0].update(domParent='wrong'),
                     lambda d: d['comparisonOrder'].reverse(), lambda d: d['panels'].pop(),
                     lambda d: d['panels'][0]['rect'].update(height=700), lambda d: d['panels'][0]['rect'].update(height=661),
                     lambda d: d['panels'][0]['rect'].update(y=500), lambda d: d['panels'][0].update(overflowY='clip'),
                     lambda d: d['panels'][0].update(left=1), lambda d: d['panels'][0].update(count=2)]
        for mutate in mutations:
            bad = copy.deepcopy(good); mutate(bad)
            with self.assertRaises(RuntimeError):
                M.check_disclosure_snapshot(bad, self.expected)

    def test_unreadable_unknown_paint_missing_endpoint_and_incomplete_last_row_fail(self):
        for identity in M.DISCLOSURE_IDS:
            good = fixture(self.expected, identity)
            mutations = [lambda d: d['targets'][-1]['proof'].update(visible=False),
                         lambda d: d['targets'][-1]['proof'].update(fontSize=14),
                         lambda d: d['targets'][-1]['proof'].update(foreground=[]),
                         lambda d: d['targets'][-1]['proof'].update(background=[float('nan'), 0, 0]),
                         lambda d: d['targets'][-1]['proof']['textRuns'][0].update(background=[]),
                         lambda d: d['targets'][-1]['proof']['fragments'][0].update(y=1200),
                         lambda d: d['targets'][-1]['proof'].update(text='shortened'),
                         lambda d: d['targets'][-1].update(count=0)]
            for mutate in mutations:
                bad = copy.deepcopy(good); mutate(bad)
                with self.assertRaises(RuntimeError):
                    M.check_disclosure_targets(bad, self.expected)
        bad = fixture(self.expected, 'np-overview-comparison'); bad['comparisonLast']['cells'] = 4
        with self.assertRaises(RuntimeError): M.check_disclosure_targets(bad, self.expected)

    def run_audit(self, failure=None, save_failure=False, expect_failure=None):
        driver = FakeDriver(self.expected, failure); report = {}; saved = []
        def save():
            saved.append(copy.deepcopy(report))
            if save_failure and report.get('disclosureBoundsChecks', [{}])[0].get('actions', []) and any(
                    item.get('actionError') for item in report['disclosureBoundsChecks'][0]['actions']):
                raise OSError('diagnostic save failed')
        with patch.object(M, 'DisclosureBudgetDriver', side_effect=lambda *_: driver), patch.object(M, 'settle_s0_toolbar_paint', side_effect=lambda _driver, _report, save, _phase: save()):
            if expect_failure if expect_failure is not None else bool(failure):
                with self.assertRaises((RuntimeError, ValueError, TimeoutError)) as caught:
                    M.disclosure_bounds_checks(driver, report, save, '1440x900', self.science)
                return driver, report, saved, caught.exception
            M.disclosure_bounds_checks(driver, report, save, '1440x900', self.science)
        return driver, report, saved, None

    def test_actual_orchestration_batches_native_tabs_saves_and_closes_without_new_images(self):
        driver, report, saved, _ = self.run_audit()
        record = report['disclosureBoundsChecks'][0]
        self.assertEqual(record['status'], 'native_bounds_and_reachability_verified')
        self.assertEqual([a['count'] for a in record['actions'] if a['kind'] == 'tab'], [1, 63])
        self.assertEqual(sum(a['kind'] == 'open' for a in record['actions']), 4)
        self.assertEqual(sum(a['kind'] == 'escape' for a in record['actions']), 5)
        self.assertTrue(all(a['status'] == 'verified' and a['actionAcknowledged'] for a in record['actions']))
        self.assertTrue(driver.stopped)
        self.assertFalse(any(driver.open.values()))
        self.assertTrue(all('after' in a and 'events' in a for a in record['actions']))
        self.assertEqual(len(saved), len(record['actions']) * 4 + len(record['proofs']) + 4)
        self.assertEqual(record['checkpointTiming']['attempts'], len(saved))
        self.assertEqual(record['checkpointTiming']['completed'], len(saved))
        self.assertTrue(all(a['nativeActionSeconds'] >= 0 for a in record['actions']))
        self.assertEqual(record['budgetSeconds'], 420)

    def test_native_failure_unreachable_noop_deadline_and_unknown_paint_retain_trace(self):
        for failure in ('action', 'unreachable', 'no-progress', 'deadline', 'unknown-paint'):
            driver, report, saved, error = self.run_audit(failure)
            record = report['disclosureBoundsChecks'][0]
            self.assertEqual(record['status'], 'failed')
            self.assertTrue(saved)
            if failure != 'deadline': self.assertTrue(driver.stopped)
            if failure == 'action':
                self.assertIsInstance(error, ValueError)
                self.assertEqual(str(error), 'original native action error')
                self.assertEqual(record['actions'][-1]['status'], 'pending')
                self.assertFalse(record['actions'][-1]['actionAcknowledged'])
                self.assertIn('after', record['actions'][-1])

    def test_fractional_native_offsets_reach_both_ends_using_integer_wheel_and_real_clamping(self):
        _, report, _, _ = self.run_audit('fractional-wheel', expect_failure=False)
        actions = [a for a in report['disclosureBoundsChecks'][0]['actions'] if a['kind'] == 'wheel']
        fractional = [a for a in actions if next(p for p in a['before']['panels'] if p['id'] == a['panel'])['top'] == 0.25]
        self.assertTrue(any(a['delta'] < 0 for a in fractional))
        self.assertTrue(any(a['delta'] > 0 for a in fractional))
        for action in fractional:
            self.assertIs(type(action['delta']), int)
            panel = next(p for p in action['after']['panels'] if p['id'] == action['panel'])
            self.assertEqual(panel['top'], panel['maxTop'] if action['delta'] > 0 else 0)

    def test_fractional_real_endpoints_require_native_double_stability_and_full_tail_proof(self):
        for failure, offset in (('fractional-end-high', .375), ('fractional-end-low', -.375)):
            _, report, _, _ = self.run_audit(failure, expect_failure=False)
            record = report['disclosureBoundsChecks'][0]
            ends = [a for a in record['actions'] if a['kind'] == 'wheel-boundary']
            self.assertEqual(len(ends), 4)
            for item in ends:
                before = next(p for p in item['before']['panels'] if p['id'] == item['panel'])
                after = next(p for p in item['after']['panels'] if p['id'] == item['panel'])
                self.assertEqual(after['top'], before['top'])
                self.assertEqual(after['top'], after['maxTop'] + offset)
                self.assertFalse(any(e['type'] == 'scroll' for e in item['events']['events']))
            self.assertTrue(all(sum(a['kind'].startswith('wheel') and a['panel'] == identity for a in record['actions']) <= 4
                                for identity in M.DISCLOSURE_IDS))
        for failure in ('unstable-boundary', 'premature-end', 'fractional-hidden-tail'):
            _, report, saved, _ = self.run_audit(failure)
            self.assertEqual(report['disclosureBoundsChecks'][0]['status'], 'failed')
            self.assertTrue(saved)

    def test_boundary_wheel_cannot_stand_in_for_progress_or_hide_fractional_movement(self):
        _, report, _, _ = self.run_audit('fractional-end-high', expect_failure=False)
        item = next(a for a in report['disclosureBoundsChecks'][0]['actions'] if a['kind'] == 'wheel-boundary')
        M.check_disclosure_action(item, self.expected)
        for change in ('fractional-move', 'reverse', 'focus', 'untrusted', 'overflow', 'outer', 'premature'):
            bad = copy.deepcopy(item); after = next(p for p in bad['after']['panels'] if p['id'] == bad['panel'])
            if change == 'fractional-move': after['top'] -= .125
            elif change == 'reverse': bad['delta'] = -1
            elif change == 'focus': bad['after']['focus'] = focus(scope='wrong')
            elif change == 'untrusted': bad['events']['events'][0]['trusted'] = False
            elif change == 'overflow': bad['events']['overflow'] = 1
            elif change == 'outer': bad['after']['landing']['top'] = .125
            else:
                after['top'] = after['maxTop'] - 1.25
                next(p for p in bad['before']['panels'] if p['id'] == bad['panel'])['top'] = after['top']
            with self.assertRaises(RuntimeError): M.check_disclosure_action(bad, self.expected)
        bad = copy.deepcopy(item); bad['kind'] = 'wheel'
        with self.assertRaises(RuntimeError): M.check_disclosure_action(bad, self.expected)

    def test_checkpoint_timing_calls_original_exactly_once_and_keeps_write_failure(self):
        record = {'checkpointTiming': {'attempts': 0, 'completed': 0, 'seconds': 0., 'inProgress': False}}
        original = unittest.mock.Mock()
        measured = M.DisclosureCheckpointSave(original, record)
        with patch.object(M.time, 'monotonic', side_effect=[10, 13.25]): measured()
        original.assert_called_once_with()
        self.assertEqual(record['checkpointTiming'], dict(attempts=1, completed=1, seconds=3.25, inProgress=False))
        original.side_effect = OSError('original write failure')
        with patch.object(M.time, 'monotonic', side_effect=[20, 24]), self.assertRaisesRegex(OSError, 'original write failure'):
            measured()
        self.assertEqual(original.call_count, 2)
        self.assertEqual(record['checkpointTiming'], dict(attempts=2, completed=1, seconds=7.25, inProgress=False))

    def test_diagnostic_save_failure_cannot_replace_original_native_exception(self):
        _, report, _, error = self.run_audit('action', save_failure=True)
        self.assertIsInstance(error, ValueError)
        self.assertEqual(str(error), 'original native action error')
        self.assertIn('checkpointError', report['disclosureBoundsChecks'][0]['actions'][-1])

    def test_fitting_notes_and_selector_never_claim_positive_scroll(self):
        _, report, _, _ = self.run_audit('fitting', expect_failure=False)
        record = report['disclosureBoundsChecks'][0]
        self.assertEqual(record['status'], 'native_bounds_and_reachability_verified')
        self.assertFalse(any(a['kind'] == 'wheel' and a['panel'] in ('np-task-relations', 'np-overview-notes') for a in record['actions']))
        self.assertTrue(any(p['panel'] == 'np-overview-notes' for p in record['proofs']))

    def test_slow_checkpoint_exhausts_input_budget_before_any_native_action(self):
        driver = FakeDriver(self.expected); report = {}; elapsed = [0]
        def remaining():
            if elapsed[0] >= M.DISCLOSURE_AUDIT_SECONDS: raise TimeoutError('checkpoint consumed budget')
            return M.DISCLOSURE_AUDIT_SECONDS - elapsed[0]
        driver.remaining = remaining
        def save(): elapsed[0] += M.DISCLOSURE_AUDIT_SECONDS + 1
        with patch.object(M, 'DisclosureBudgetDriver', return_value=driver), patch.object(M.time, 'monotonic', side_effect=lambda: elapsed[0]):
            with self.assertRaisesRegex(TimeoutError, 'checkpoint consumed budget'):
                M.disclosure_bounds_checks(driver, report, save, '1440x900', self.science)
        self.assertEqual(report['disclosureBoundsChecks'][0]['status'], 'failed')
        self.assertEqual(report['disclosureBoundsChecks'][0]['actions'], [])
        self.assertEqual(driver.calls, [])
        self.assertTrue(report['disclosureBoundsChecks'][0]['budgetExhausted'])
        self.assertGreater(report['disclosureBoundsChecks'][0]['checkpointTiming']['seconds'], M.DISCLOSURE_AUDIT_SECONDS)

    def test_probe_start_lost_response_and_absent_install_both_cleanup_without_replacing_error(self):
        for failure, message, absent in (('start-after-install', 'original start response failure', False),
                                         ('start-before-install', 'original start request failure', True)):
            driver, report, _, error = self.run_audit(failure)
            record = report['disclosureBoundsChecks'][0]
            self.assertIsInstance(error, TimeoutError); self.assertEqual(str(error), message)
            self.assertFalse(record['probeStartAcknowledged'])
            self.assertTrue(driver.stopped); self.assertFalse(driver.installed)
            self.assertTrue(record['cleanup']['cleanedUp']); self.assertEqual(record['cleanup']['absent'], absent)
            self.assertEqual(record['cleanup']['owner'], record['probeOwner'])

    def test_probe_absent_cleanup_and_foreign_owner_are_exact_and_non_destructive(self):
        script = r"""
const assert=require('node:assert/strict'),probe=new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));
global.window={};const listeners=new Map();global.document={addEventListener:(k,f)=>listeners.set(k,f),removeEventListener:(k,f)=>{assert.equal(listeners.get(k),f);listeners.delete(k);}};
assert.equal(probe('stop','mine').absent,true);assert.equal(listeners.size,0);
probe('start',276,'other');assert.equal(listeners.size,6);
assert.throws(()=>probe('stop','mine'),/another observer owner/);assert.equal(window.__npDisclosureAudit.owner,'other');assert.equal(listeners.size,6);
assert.equal(probe('stop','other').cleanedUp,true);assert.equal(listeners.size,0);assert.equal(window.__npDisclosureAudit,undefined);
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps(M.DISCLOSURE_PROBE_JS), text=True, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_wrong_focus_untrusted_key_and_oversized_native_batch_fail(self):
        _, report, _, _ = self.run_audit()
        actions = report['disclosureBoundsChecks'][0]['actions']
        for kind in ('wheel', 'escape', 'tab'):
            good = next(a for a in actions if a['kind'] == kind)
            bad = copy.deepcopy(good); bad['after']['focus'] = focus(scope='wrong')
            with self.assertRaises(RuntimeError): M.check_disclosure_action(bad, self.expected)
            bad = copy.deepcopy(good); bad['events']['events'][0]['trusted'] = False
            with self.assertRaises(RuntimeError): M.check_disclosure_action(bad, self.expected)
        bad = copy.deepcopy(next(a for a in actions if a['kind'] == 'tab')); bad['count'] = 66
        with self.assertRaises(RuntimeError): M.check_disclosure_action(bad, self.expected)

    def test_new_deadline_bounds_only_new_transport_and_rechecks_after_response(self):
        original = type('Original', (), dict(url='http://localhost', session='synthetic'))()
        bounded = M.DisclosureBudgetDriver(original, 45)
        with patch.object(M.time, 'monotonic', return_value=45):
            with self.assertRaises(TimeoutError): bounded.remaining()
        with patch.object(M.time, 'monotonic', side_effect=[44, 46]), patch.object(M.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"value":true}')) as request:
            with self.assertRaises(TimeoutError): bounded.request('POST', '/anything', {})
            self.assertEqual(request.call_args.kwargs['timeout'], 1)

    def test_old106_pngs_guards_readonly_snapshots_and_failure_png_remain(self):
        import inspect
        code = inspect.getsource(M.main)
        before = "capture(prefix + '-12-directory-return', require_home=True)"
        extra = 'disclosure_bounds_checks(driver, report, save, prefix, science)'
        after = 'task_density_checks(driver, report, save, capture, prefix, base, science)'
        self.assertLess(code.index(before), code.index(extra)); self.assertLess(code.index(extra), code.index(after))
        self.assertEqual(len(M.SCENE_NAMES) * len(M.VIEWPORTS), 106)
        for required in ("for scope in ['task:coin', 'task:iign', 'task:dialnav']", "scrollIntoView({block:'center'})",
                         'check_s0_wheel(wheel_before', "closed['focus'] != 'np-relation-select-'", "out / 'failure.png'"):
            self.assertIn(required, code)
        for script in (M.DISCLOSURE_SNAPSHOT_JS, M.DISCLOSURE_PROBE_JS, inspect.getsource(M.disclosure_bounds_checks)):
            for forbidden in ('scrollTop=', 'scrollTop =', '.focus(', '.open=', '.open =', 'dispatchEvent(', '.style.', 'scrollIntoView(', '/refresh', '/url'):
                self.assertNotIn(forbidden, script)
        self.assertIn('timeout=50', inspect.getsource(M.Driver.request))
        self.assertIn("('scripts/navigation_screenshots.py', 'tests/test_navigation_screenshots.py', 'tests/test_navigation_disclosure_bounds.py')", code)

    def test_exact_browser_snapshot_and_probe_scripts_compile(self):
        for script in (M.DISCLOSURE_SNAPSHOT_JS, M.DISCLOSURE_PROBE_JS):
            parsed = subprocess.run(['node', '-e', "new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));"],
                                    input=json.dumps(script), text=True, capture_output=True, timeout=10)
            self.assertEqual(parsed.returncode, 0, parsed.stderr)


if __name__ == '__main__':
    unittest.main()
