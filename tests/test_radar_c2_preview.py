"""Portable discovery entrypoint: frozen science, isolated publication and 31+38 contracts.

The JS suites use an in-memory DOM. None of these are real-browser acceptance.
"""
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import radar_c2_preview as c2
import build_previews


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class HTML(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids, self.refs, self.scripts = set(), [], []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs: self.ids.add(attrs['id'])
        for key in ('src', 'href'):
            if key in attrs: self.refs.append((tag, key, attrs[key]))
        if tag == 'script' and 'src' in attrs: self.scripts.append(attrs['src'])


class RadarC2SafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in (c2.SOURCE, c2.INPUT_SOURCE):
            shutil.copytree(ROOT / name, self.root / name)
        for name in (c2.MANIFEST, 'previews/radar-trees-c/data/graph-data.json'):
            dest = self.root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
    def mutate_manifest(self, fn):
        path = self.root / c2.MANIFEST
        manifest = json.loads(path.read_text())
        fn(manifest)
        path.write_text(json.dumps(manifest))
    def test_exact_allowlist_hashes_and_repeat(self):
        before = c2.payloads(self.root)
        for _ in range(2):
            self.assertEqual(set(c2.write_preview(self.root, self.root / 'dist')), c2.PUBLIC_FILES)
            self.assertEqual(c2.validate_output(self.root, self.root / 'dist'), sorted(before))
        self.assertEqual(len(before), 14)
    def test_missing_public_source(self):
        (self.root / c2.SOURCE / 'index.html').unlink()
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_extra_public_source(self):
        (self.root / c2.SOURCE / 'private.json').write_text('{}')
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_changed_public_source(self):
        (self.root / c2.SOURCE / 'app.js').write_text('changed')
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_review_input_change_rejected(self):
        (self.root / c2.INPUT_SOURCE / 'analysis/data/mapping.json').write_text('{}')
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_manifest_cannot_expand_public_allowlist(self):
        self.mutate_manifest(lambda m: m['public_files'].update({'private.json': '0' * 64}))
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_manifest_cannot_expand_review_allowlist(self):
        self.mutate_manifest(lambda m: m['review_inputs'].update({'extra.json': '0' * 64}))
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_acceptance_cannot_be_promoted(self):
        self.mutate_manifest(lambda m: m.update(real_browser='PASS'))
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_source_symlink(self):
        path = self.root / c2.SOURCE / 'index.html'; path.unlink()
        path.symlink_to(ROOT / c2.SOURCE / 'index.html')
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_source_fifo(self):
        path = self.root / c2.SOURCE / 'index.html'; path.unlink(); os.mkfifo(path)
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_manifest_fifo(self):
        path = self.root / c2.MANIFEST; path.unlink(); os.mkfifo(path)
        with self.assertRaises(ValueError): c2.payloads(self.root)
    def test_output_symlink(self):
        (self.root / 'dist').symlink_to(self.root / c2.SOURCE, target_is_directory=True)
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
    def test_output_file_and_directory_symlinks(self):
        c2.write_preview(self.root, self.root / 'dist')
        path = self.root / 'dist' / c2.ROUTE / 'index.html'; path.unlink()
        path.symlink_to(self.root / c2.SOURCE / 'index.html')
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
        path.unlink(); path.write_text('bad')
        folder = self.root / 'dist' / c2.ROUTE / 'data'; shutil.rmtree(folder)
        folder.symlink_to(self.root / c2.SOURCE / 'data', target_is_directory=True)
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
    def test_output_fifo_rejected_preflight(self):
        c2.write_preview(self.root, self.root / 'dist')
        path = self.root / 'dist' / c2.ROUTE / 'index.html'; path.unlink(); os.mkfifo(path)
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
    def test_output_extra_and_missing_rejected_preflight(self):
        c2.write_preview(self.root, self.root / 'dist')
        path = self.root / 'dist' / c2.ROUTE / 'private.txt'; path.write_text('private')
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
        path.unlink(); (path.parent / 'index.html').unlink()
        with self.assertRaises(ValueError): c2.validate_preview(self.root, self.root / 'dist')
    def test_output_hardlink_does_not_mutate_original(self):
        c2.write_preview(self.root, self.root / 'dist')
        original = self.root / 'keep.txt'; original.write_text('keep')
        path = self.root / 'dist' / c2.ROUTE / 'index.html'; path.unlink(); os.link(original, path)
        c2.write_preview(self.root, self.root / 'dist')
        self.assertEqual(original.read_text(), 'keep')
    def test_changed_output_detected(self):
        c2.write_preview(self.root, self.root / 'dist')
        (self.root / 'dist' / c2.ROUTE / 'index.html').write_text('changed')
        with self.assertRaises(ValueError): c2.validate_output(self.root, self.root / 'dist')
    def test_overlap_outside_and_source_namespace_protection(self):
        for target in (self.root, self.root.parent / 'escape', self.root / c2.SOURCE,
                       self.root / 'previews', self.root / c2.SOURCE / 'nested',
                       self.root / 'tests', self.root / 'scripts', self.root / 'release_checks'):
            with self.subTest(target=target), self.assertRaises(ValueError):
                c2.validate_preview(self.root, target)
    def test_invalid_c2_stops_wrapper_before_build_clean(self):
        dest = self.root / 'dist'; dest.mkdir(); marker = dest / 'keep'; marker.write_text('keep')
        (self.root / c2.SOURCE / 'app.js').write_text('changed')
        with patch.object(build_previews, 'ROOT', self.root), \
             patch.object(build_previews, 'validate_source'), \
             patch.object(build_previews, 'validate_submit_source'), \
             patch.object(build_previews.subprocess, 'run') as run:
            with self.assertRaises(ValueError): build_previews.main(['--output', 'dist'])
            run.assert_not_called()
        self.assertEqual(marker.read_text(), 'keep')
    def test_actual_wrapper_stops_before_build_clean(self):
        for name in ('scripts/build_previews.py', 'scripts/build_topic_preview.py',
                     'scripts/radar_c2_preview.py', 'scripts/build.py', 'data/catalog.json'):
            dest = self.root / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        for name in ('submit-preview', 'previews/library-topic-preview'):
            shutil.copytree(ROOT / name, self.root / name)
        dest = self.root / 'dist'; dest.mkdir(); (dest / 'keep').write_text('keep')
        (self.root / c2.SOURCE / 'app.js').write_text('changed')
        run = subprocess.run([sys.executable, str(self.root / 'scripts/build_previews.py')],
                             cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('C2 reviewed hash mismatch', run.stderr)
        self.assertEqual((dest / 'keep').read_text(), 'keep')


class RadarC2ContractTests(unittest.TestCase):
    def test_all_105_pr18_paths_and_old_c_formal_data_are_unchanged(self):
        protection = json.loads((ROOT / 'tests/fixtures/radar-c2-protection.json').read_text())
        self.assertEqual(len(protection['pr18']), 105)
        for name, expected in protection['pr18'].items():
            content = (ROOT / name).read_bytes()
            actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            self.assertEqual(actual, expected, name)
        for name, expected in protection['preserved_sha256'].items():
            self.assertEqual(digest(ROOT / name), expected, name)
        catalog = json.loads((ROOT / 'data/catalog.json').read_text())['papers']
        reports = json.loads((ROOT / 'data/reports.json').read_text())
        self.assertEqual(len(catalog), 95)
        self.assertEqual(len(reports['reports']), 21)
        self.assertEqual(sum(s.get('status') == 'imported' for p in catalog
                             for s in p['stages'].values()), 12)
    def test_range_is_independently_derived_and_retains_weekly_only(self):
        graph = json.loads((ROOT / 'previews/radar-trees-c/data/graph-data.json').read_text())
        stats = c2.range_stats(graph)
        self.assertEqual([stats[k] for k in ('baseline_count', 'weekly_count', 'unique_count',
                         'overlap_count', 'weekly_only_count')], [39, 6, 43, 2, 4])
        self.assertEqual(stats['weekly_only_ids'], ['arxiv:2609.37187', 'arxiv:2609.37353',
                                                   'arxiv:2609.39166', 'arxiv:2609.39579'])
        catalog = json.loads((ROOT / c2.INPUT_SOURCE / 'data/catalog.json').read_text())
        self.assertEqual(catalog['papers'], graph['papers'])
        self.assertTrue(set(stats['weekly_only_ids']).isdisjoint(p['canonical_id'] for p in catalog['papers']))
        self.assertEqual(len(c2.payloads(ROOT)), 14)
    def test_local_resources_anchors_cache_and_script_order(self):
        source = ROOT / c2.SOURCE
        htmls = {n: HTML((source / n).read_text()) for n in c2.PUBLIC_FILES if n.endswith('.html')}
        for name, parsed in htmls.items():
            for tag, attr, raw in parsed.refs:
                url = urlsplit(raw)
                if url.scheme or url.netloc:
                    self.assertNotEqual(tag, 'script', raw)
                    continue
                target = (source / name).parent / unquote(url.path) if url.path else source / name
                target = target.resolve()
                if 'radar-trees-c/' in raw:
                    # Source namespaces are siblings just as the output routes are.
                    self.assertTrue(target.is_file(), raw)
                else:
                    relative = target.relative_to(source).as_posix()
                    self.assertIn(relative, c2.PUBLIC_FILES, raw)
                    if url.fragment and not url.fragment.startswith(('state=', 'analysis=')):
                        self.assertIn(unquote(url.fragment), htmls[relative].ids, raw)
                if tag in ('script', 'link') and url.path.endswith(('.js', '.css')):
                    self.assertEqual(parse_qs(url.query).get('v'), [digest(target)[:12]], raw)
        entry = (source / 'index.html').read_text()
        self.assertLess(entry.index('data-c2-range='), entry.index('<main>'))
        self.assertGreater(entry.index('data-c2-range='), entry.index('</header>'))
        self.assertEqual([urlsplit(p).path for p in htmls['index.html'].scripts], [
            'data/catalog.js', 'data/literature.js', 'data/challenge.js', 'model.js', 'app.js',
            'analysis/data/bundle.js', 'analysis/model.js', 'analysis/c2.js'])
        for name in c2.PUBLIC_FILES:
            text = (source / name).read_text()
            for forbidden in ('/workspace/', '/agent_notes/', 'dream_notes', 'localhost',
                              '127.0.0.1', 'tests/fixtures/', 'file://'):
                self.assertNotIn(forbidden, text, name)
            if name.endswith('.css'):
                self.assertNotRegex(text, r'@import\b|url\(\s*[\'"]?https?://')
    def test_portable_31_plus_38_regressions_run_on_temporary_copy(self):
        before = {str(p): digest(p) for base in (c2.SOURCE, c2.INPUT_SOURCE)
                  for p in (ROOT / base).rglob('*') if p.is_file()}
        with tempfile.TemporaryDirectory() as temp:
            site = Path(temp) / 'site'
            shutil.copytree(ROOT / c2.SOURCE, site)
            shutil.copytree(ROOT / c2.INPUT_SOURCE, site, dirs_exist_ok=True)
            for script, count in (('tests/navigation.test.cjs', 31), ('analysis/tests/c2.test.cjs', 38)):
                run = subprocess.run(['node', str(site / script)], check=True, capture_output=True,
                                     text=True, timeout=60)
                self.assertEqual(len(re.findall(r'^PASS ', run.stdout, re.M)), count, run.stdout)
                report = json.loads((site / script).with_name('report.json').read_text())
                self.assertEqual(report['checks'], count)
            run = subprocess.run(['node', str(site / 'tests/integration.test.cjs')], check=True,
                                 capture_output=True, text=True, timeout=30)
            self.assertEqual(len(re.findall(r'^PASS ', run.stdout, re.M)), 2, run.stdout)
            before_bundle = (site / 'analysis/data/bundle.js').read_bytes()
            subprocess.run([sys.executable, str(site / 'analysis/build_bundle.py')],
                           check=True, capture_output=True, text=True)
            self.assertEqual((site / 'analysis/data/bundle.js').read_bytes(), before_bundle)
        self.assertEqual(before, {str(p): digest(p) for base in (c2.SOURCE, c2.INPUT_SOURCE)
                                for p in (ROOT / base).rglob('*') if p.is_file()})
    def test_wrapper_output_delta_is_only_new_route(self):
        # Compare the same current source through the original build+preview steps
        # against the CI wrapper; generated data must already be prepared as in CI.
        with tempfile.TemporaryDirectory(prefix='.c2-baseline-', dir=ROOT) as baseline, \
             tempfile.TemporaryDirectory(prefix='.c2-integrated-', dir=ROOT) as integrated:
            subprocess.run([sys.executable, str(ROOT / 'scripts/build.py'), '--output', baseline],
                           check=True, capture_output=True, text=True, timeout=90)
            build_previews.write_preview(ROOT, Path(baseline))
            build_previews.write_submit_preview(ROOT, Path(baseline))
            subprocess.run([sys.executable, str(ROOT / 'scripts/build_previews.py'), '--output', integrated],
                           check=True, capture_output=True, text=True, timeout=90)
            hashes = lambda folder: {p.relative_to(folder).as_posix(): digest(p)
                                     for p in Path(folder).rglob('*') if p.is_file()}
            old, new = hashes(baseline), hashes(integrated)
            added = {n for n in new if n not in old}
            self.assertEqual(added, {c2.ROUTE + '/' + n for n in c2.PUBLIC_FILES})
            self.assertEqual(old, {n: h for n, h in new.items() if n not in added})
            c2.validate_output(ROOT, Path(integrated))


if __name__ == '__main__':
    unittest.main()
