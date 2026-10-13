"""Lossless checkpoint caching. A hit never omits a save or any observation."""
import ast
import copy
from contextlib import contextmanager
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('cached_navigation_screenshots', ROOT / 'scripts/navigation_screenshots.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def canonical(report):
    return (json.dumps(report, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def report_fixture():
    state = {'source': 'pos:l:原始方法', 'route': {'node': '原始', 'claim': '完整claim'},
             'runtime': {'expanded': ['原父', '子'], 'focus': '原父'},
             'history': {'expanded': ['原父', '子'], 'focus': '原父'},
             'scroll': {'tree': 0, 'reader': 160, 'window': 0},
             'originalDOM': {'tree': 'ref-1', 'reader': 'ref-2'},
             'proof': {'label': '完整原始文字', 'font': 15, 'visible': True}}
    audit = {'status': 'started', 'before': state,
             'actions': [{'kind': 'tree-key', 'before': state, 'after': copy.deepcopy(state),
                          'events': [{'type': 'keydown', 'trusted': True, 'key': 'Home'}]}]}
    return {'head': '精确head', 'captures': [{'name': '1440x900-method', 'childReadability': audit}],
            'methodChildReadabilityChecks': [audit], 'status': 'starting', 'empty': [],
            'scalars': [None, False, True, 0, 1, -1, 0.0, -0.0, 1.25, '引号"\n\\', float('inf')],
            'nestedKeys': {1: 'integer key', None: 'none key', 'true': True}}


class ReceiptSnapshotCacheTests(unittest.TestCase):
    def assert_saved(self, target, report):
        self.assertEqual(target.read_bytes(), canonical(report))
        self.assertEqual(list(json.loads(target.read_bytes())), list(report))
        self.assertEqual(list(target.parent.glob('.receipt.json.*.tmp')), [])

    def cache(self, path, **kwargs):
        cache = MODULE.ReceiptSnapshotCache(path, progress_every=0, **kwargs)
        self.addCleanup(cache.close)
        return cache

    def test_exact_original_json_bytes_and_every_checkpoint_survive_cache_hits(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture()
            cache = self.cache(target)
            for count in range(4):
                report['checkpoint'] = count
                cache(target, report)
                self.assert_saved(target, report)
                self.assertEqual(cache.stats['writes'], count + 1)
            self.assertGreater(cache.stats['hits'], 0)
            self.assertGreater(cache.stats['misses'], 0)
            self.assertFalse(any(key.startswith('$') for key in json.loads(target.read_bytes())))

    def test_nested_alias_late_events_and_original_source_binding_changes_are_not_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
            audit = report['methodChildReadabilityChecks'][0]
            mutations = [lambda: audit['actions'][0]['events'].append({'type': 'focusin', 'trusted': True}),
                         lambda: audit['actions'][0]['after']['route'].update(claim='另一完整claim'),
                         lambda: audit['before']['originalDOM'].update(reader='ref-replaced'),
                         lambda: audit['before']['scroll'].update(reader=161),
                         lambda: audit.update(status='verified_native_children', cleanedUp=True),
                         lambda: report.update(error='保留真实失败', status='failed')]
            cache(target, report)
            for change in mutations:
                misses = cache.stats['misses']; change(); cache(target, report)
                self.assert_saved(target, report)
                self.assertGreater(cache.stats['misses'], misses)
                decoded = json.loads(target.read_bytes())
                self.assertEqual(decoded['captures'][0]['childReadability'], decoded['methodChildReadabilityChecks'][0])

    def test_equal_python_values_with_distinct_json_types_cannot_false_hit(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target); report = {'values': [{'value': 0}]}
            for value in [0, False, 0.0, -0.0, 1, True, 1.0, None, '1', [], {}]:
                report['values'][0]['value'] = value
                cache(target, report)
                self.assert_saved(target, report)

    def test_append_reorder_delete_and_list_to_object_changes_preserve_complete_order(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target)
            report = {'observations': [{'id': 1}, {'id': 2}, {'id': 3}], 'old': {'source': 'original'}}
            cache(target, report)
            report['observations'].reverse(); cache(target, report); self.assert_saved(target, report)
            report['observations'].append({'id': 4}); cache(target, report); self.assert_saved(target, report)
            report['observations'].pop(1); del report['old']; cache(target, report); self.assert_saved(target, report)
            report['observations'] = {'sameKey': 'new shape'}; cache(target, report); self.assert_saved(target, report)
            self.assertEqual(set(cache.entries), {('observations', None)})

    def test_cache_budget_falls_back_without_dropping_data_or_growing_retained_files(self):
        for budget in (0, 100):
            with self.subTest(budget=budget), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'receipt.json'; cache = self.cache(target, max_cache_bytes=budget)
                report = {'small': 1, 'large': [{'text': '完整原文' * 2000}]}
                for count in range(3):
                    report['large'][0]['count'] = count; cache(target, report); self.assert_saved(target, report)
                    self.assertLessEqual(cache.bytes, budget)
                    self.assertEqual(sum(p.stat().st_size for p in cache.root.iterdir()), cache.bytes)

    def test_cached_payload_corruption_never_commits_and_next_write_can_preserve_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
            cache(target, report); prior = target.read_bytes()
            entry = cache.entries[('methodChildReadabilityChecks', 0)]
            entry[1].write_bytes(b'{"silentlyRemovedOriginalProof":true}')
            with self.assertRaisesRegex(RuntimeError, 'integrity'):
                cache(target, report)
            self.assertEqual(target.read_bytes(), prior)
            self.assertEqual(list(target.parent.glob('.receipt.json.*.tmp')), [])
            report.update(status='failed', error='observed cache corruption')
            cache(target, report); self.assert_saved(target, report)

    def test_auxiliary_cap_includes_staging_and_never_accumulates_uncached_items(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target, max_cache_bytes=4096)
            report = {'values': [{'text': 'first' * 40}, {'text': 'second' * 40}]}
            real_write = Path.write_bytes
            peaks = []
            def write(path, payload):
                result = real_write(path, payload)
                if path.parent == cache.root:
                    peaks.append(sum(p.stat().st_size for p in cache.root.iterdir()))
                    self.assertLessEqual(peaks[-1], cache.limit)
                return result
            with patch.object(Path, 'write_bytes', write):
                cache(target, report)
                report['values'][0]['text'] = 'replacement' * 80
                cache(target, report)
                report['uncached'] = [{'text': 'large' * 4000, 'number': i} for i in range(20)]
                cache(target, report)
            self.assert_saved(target, report)
            self.assertTrue(peaks)
            self.assertLessEqual(sum(p.stat().st_size for p in cache.root.iterdir()), cache.limit)

    def test_postcommit_cleanup_error_leaves_complete_new_checkpoint(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target)
            report = {'keep': 'original', 'remove': 'old record'}; cache(target, report)
            del report['remove']; report['keep'] = 'complete next checkpoint'
            real_remove = cache._remove
            def remove(entry):
                if entry[1].read_bytes() == b'"old record"':
                    raise OSError('postcommit cleanup stopped')
                real_remove(entry)
            with patch.object(cache, '_remove', side_effect=remove):
                with self.assertRaisesRegex(OSError, 'postcommit cleanup'):
                    cache(target, report)
            self.assert_saved(target, report)

    def test_partial_cleanup_stays_charged_across_near_budget_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target, max_cache_bytes=2048)
            report = {'retired': 'r' * 350, 'keep': 'k' * 100}; cache(target, report)
            stale = cache.entries[('retired', None)]; del report['retired']
            real_remove = cache._remove
            def remove(entry):
                if entry == stale:
                    entry[0].unlink(missing_ok=True)
                    raise OSError('partial retired cleanup')
                real_remove(entry)
            with patch.object(cache, '_remove', side_effect=remove):
                for value in ('new' * 150, 'changed' * 200):
                    report['next'] = value
                    with self.assertRaisesRegex(OSError, 'partial retired cleanup'):
                        cache(target, report)
                    self.assert_saved(target, report)
                    actual = sum(p.stat().st_size for p in cache.root.iterdir())
                    self.assertLessEqual(actual, cache.bytes)
                    self.assertLessEqual(cache.bytes, cache.limit)
                    self.assertIn(('retired', None), cache.entries)
            cache(target, report); self.assert_saved(target, report)
            self.assertNotIn(('retired', None), cache.entries)

    def test_failed_staging_cleanup_is_reserved_and_never_used_as_complete_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; cache = self.cache(target, max_cache_bytes=2048)
            report = {'state': 'first'}; cache(target, report); prior = target.read_bytes()
            report['state'] = 'changed' * 50
            real_write = Path.write_bytes
            def write(path, payload):
                if path.parent == cache.root and path.suffix == '.json':
                    real_write(path, payload[:10])
                    raise OSError('staging write stopped')
                return real_write(path, payload)
            real_remove = cache._remove
            def remove(entry):
                if not entry[5]:
                    raise OSError('staging cleanup stopped')
                real_remove(entry)
            with patch.object(Path, 'write_bytes', write), patch.object(cache, '_remove', side_effect=remove):
                with self.assertRaisesRegex(OSError, 'staging cleanup'):
                    cache(target, report)
            self.assertEqual(target.read_bytes(), prior)
            self.assertFalse(cache.entries[('state', None)][5])
            self.assertLessEqual(sum(p.stat().st_size for p in cache.root.iterdir()), cache.bytes)
            self.assertLessEqual(cache.bytes, cache.limit)
            cache(target, report); self.assert_saved(target, report)
            self.assertTrue(cache.entries[('state', None)][5])

    def test_corrupt_fingerprint_reencodes_the_current_observation_without_trusting_disk(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
            cache(target, report)
            cache.entries[('methodChildReadabilityChecks', 0)][0].write_bytes(b'not marshal input')
            cache(target, report); self.assert_saved(target, report)

    def test_replace_failure_preserves_prior_complete_receipt_then_retry_is_exact(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
            cache(target, report); prior = target.read_bytes(); report['status'] = 'next checkpoint'
            with patch.object(MODULE.os, 'replace', side_effect=OSError('replace stopped')):
                with self.assertRaisesRegex(OSError, 'replace stopped'):
                    cache(target, report)
            self.assertEqual(target.read_bytes(), prior)
            cache(target, report); self.assert_saved(target, report)

    def test_partial_write_close_failure_and_interrupt_do_not_publish_incomplete_state(self):
        real_factory = MODULE.tempfile.NamedTemporaryFile
        for fault in ('write', 'short-write', 'close', 'interrupt'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
                cache(target, report); prior = target.read_bytes(); report['status'] = 'new checkpoint'
                @contextmanager
                def factory(*args, **kwargs):
                    with real_factory(*args, **kwargs) as stream:
                        if fault in ('write', 'short-write'):
                            class Broken:
                                name = stream.name
                                def write(self, data):
                                    stream.write(data[:max(1, len(data) // 2)])
                                    if fault == 'write':
                                        raise OSError('partial write')
                                    return len(data) - 1
                            yield Broken()
                        else:
                            yield stream
                    if fault == 'close':
                        raise OSError('close stopped')
                    if fault == 'interrupt':
                        raise KeyboardInterrupt('checkpoint interrupted')
                with patch.object(MODULE.tempfile, 'NamedTemporaryFile', side_effect=factory):
                    with self.assertRaises((OSError, KeyboardInterrupt)):
                        cache(target, report)
                self.assertEqual(target.read_bytes(), prior)
                self.assertEqual(list(target.parent.glob('.receipt.json.*.tmp')), [])
                cache(target, report); self.assert_saved(target, report)

    def test_serialization_failure_preserves_prior_checkpoint_and_cache_cleanup_is_private(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; sentinel = Path(directory) / 'unrelated.txt'; sentinel.write_text('keep')
            report = report_fixture(); cache = self.cache(target); cache(target, report); prior = target.read_bytes()
            report['unsupported'] = {1, 2}
            with self.assertRaises(TypeError):
                cache(target, report)
            self.assertEqual(target.read_bytes(), prior)
            root = cache.root; cache.close(); self.assertFalse(root.exists()); self.assertEqual(sentinel.read_text(), 'keep')
            with self.assertRaises(ValueError):
                cache(target, {})

    def test_process_exit_before_atomic_replace_preserves_prior_or_absent_target(self):
        code = """
import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import navigation_screenshots as m
target=Path(sys.argv[2]);cache=m.ReceiptSnapshotCache(target,progress_every=0)
m.os.replace=lambda *args:os._exit(73)
cache(target,{'status':'new','observations':[{'complete':'完整'}]})
"""
        for prior in (None, {'status': 'previous complete checkpoint'}):
            with self.subTest(prior=prior), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'receipt.json'
                if prior is not None:
                    target.write_bytes(canonical(prior))
                result = subprocess.run([sys.executable, '-c', code, str(ROOT / 'scripts'), str(target)], timeout=15)
                self.assertEqual(result.returncode, 73)
                if prior is None:
                    self.assertFalse(target.exists())
                else:
                    self.assertEqual(target.read_bytes(), canonical(prior))

    def test_original_checkpoint_wrapper_all_103_save_sites_and_106_scenes_remain(self):
        source = ast.parse(Path(MODULE.__file__).read_text())
        saves = [n for n in ast.walk(source) if isinstance(n, ast.FunctionDef) and n.name == 'save']
        calls = [n for n in ast.walk(source) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']
        self.assertEqual(len(saves), 1); self.assertEqual(len(calls), 103)
        self.assertEqual(len(MODULE.VIEWPORTS) * len(MODULE.SCENE_NAMES), 106)
        main = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        bindings = [n for n in main.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'write_receipt' for t in n.targets)]
        self.assertEqual(len(bindings), 1); self.assertEqual(ast.dump(bindings[0].value), "Name(id='receipt_cache', ctx=Load())")
        closes = [n for n in ast.walk(main) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and isinstance(n.func.value, ast.Name) and n.func.value.id == 'receipt_cache' and n.func.attr == 'close']
        self.assertEqual(len(closes), 1)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; report = report_fixture(); cache = self.cache(target)
            namespace = {'out': Path(directory), 'report': report, 'write_receipt': cache}
            exec(compile(ast.fix_missing_locations(ast.Module(body=saves, type_ignores=[])), '<unchanged-save>', 'exec'), namespace)
            for count in range(3):
                report['checkpoint'] = count; namespace['save'](); self.assert_saved(target, report)
            self.assertEqual(cache.stats['writes'], 3)

    def test_cache_close_failure_occurs_after_original_browser_server_and_log_cleanup(self):
        from types import SimpleNamespace
        tree = ast.parse(Path(MODULE.__file__).read_text())
        main = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        original_try = next(n for n in reversed(main.body) if isinstance(n, ast.Try) and n.finalbody)
        function = ast.FunctionDef(name='cleanup', args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
                                   body=original_try.finalbody, decorator_list=[])
        events = []
        def close_cache():
            events.append('cache-close')
            raise OSError('cache close failed')
        namespace = dict(save=lambda: events.append('save'),
                         driver=SimpleNamespace(session=True, call=lambda *args: events.append('driver-delete')),
                         process=SimpleNamespace(terminate=lambda: events.append('terminate'), wait=lambda **kwargs: events.append('wait')),
                         server=SimpleNamespace(shutdown=lambda: events.append('shutdown'), server_close=lambda: events.append('server-close')),
                         logs=SimpleNamespace(close=lambda: events.append('logs-close')),
                         receipt_cache=SimpleNamespace(close=close_cache), subprocess=subprocess)
        exec(compile(ast.fix_missing_locations(ast.Module(body=[function], type_ignores=[])), '<actual-main-cleanup>', 'exec'), namespace)
        with self.assertRaisesRegex(OSError, 'cache close failed'):
            namespace['cleanup']()
        self.assertEqual(events, ['save', 'driver-delete', 'terminate', 'wait', 'shutdown', 'server-close', 'logs-close', 'cache-close'])


if __name__ == '__main__':
    unittest.main()
