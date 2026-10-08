"""Portable discovery entrypoint: frozen science, isolated publication and 31+38 contracts.

The JS suites use an in-memory DOM. None of these are real-browser acceptance.
"""
import copy
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import unquote, urlsplit, parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import radar_c2_preview as c2
import radar_tree_preview as old_c
import build_previews


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


# This file remains the exact initial release provenance, including evolving paths.
# Permanent CI consumes only its immutable historical projection below; whole-release
# comparisons belong to the sealed release evidence, not a universal source freeze.
PROTECTION_FIXTURE = 'tests/fixtures/radar-c2-protection.json'
PROTECTION_SHA256 = 'd552b96f14599c4eccb877ccde09b31ab477531ebb05991ac020afc2b07cd345'
SOURCE_DIRS = ('.github', 'assets', 'artifacts', 'candidates', 'data', 'docs',
               'previews', 'release_checks', 'scripts', 'submit-preview', 'tests')


def immutable_history(test, root):
    test.assertEqual(digest(root / PROTECTION_FIXTURE), PROTECTION_SHA256,
                     'Initial C2 release provenance must remain unchanged')
    protection = json.loads((root / PROTECTION_FIXTURE).read_text())
    test.assertEqual(len(protection['pr18']), 105)  # Historical path count only.
    for name, expected in protection['pr18'].items():
        # Reviewed v2 raw chunks, policies and historical evidence are immutable.
        # Pending gates, migration plans and print-QA metadata are current state,
        # not fixed raw history. Their report/CSS content keeps its existing v2
        # validator/test contracts; C2 must not freeze their workflow metadata.
        if name.startswith(('data/report-parts/', 'data/report-')) or name in (
                'candidates/navigation-stage1-v2-facts-audit.json',
                'candidates/navigation-stage1-v2-presentation-proof.json'):
            content = (root / name).read_bytes()
            actual = hashlib.sha1(b'blob ' + str(len(content)).encode() + b'\0' + content).hexdigest()
            test.assertEqual(actual, expected, 'Immutable raw history: ' + name)
    for name, expected in protection['preserved_sha256'].items():
        if name in ('previews/radar-trees-c/data/graph-data.json',
                    'previews/radar-trees-c/data/graph-data.js',
                    'previews/radar-trees-c/weekly-2026-10-04.html'):
            test.assertEqual(digest(root / name), expected, 'Immutable old-C archive: ' + name)
    # Old-C presentation/manifest can receive separately reviewed UI repairs. Its
    # own exact payload validator remains authoritative for current reviewed bytes.
    old_c.payloads(root)
    # The current catalog, registry, builders and test code are deliberately absent
    # from this fixed projection. C2's own runtime/review seals remain in payloads().


def source_hashes(root, outputs=()):
    # Walk EVERY current/future namespace, including top-level directory entries.
    # Never follow symlinks. Only known generated destinations, explicit temporary
    # build destinations, Git/dependencies and Python bytecode are outside inputs.
    excluded = {root / name for name in ('.git', 'node_modules', 'dist', 'repeat-dist', 'dist-test')}
    excluded.update(Path(output) for output in outputs)
    result = {}
    def visit(path):
        if path in excluded or path.name == '__pycache__' or path.suffix == '.pyc':
            return
        name = path.relative_to(root).as_posix()
        if path.is_symlink():
            result[name] = ('symlink', os.readlink(path))
        elif path.is_file():
            result[name] = ('file', digest(path))
        elif path.is_dir():
            result[name] = ('directory',)
            for child in sorted(path.iterdir()):
                visit(child)
        else:
            result[name] = ('special', stat.S_IFMT(path.lstat().st_mode))
    for path in sorted(root.iterdir()):
        visit(path)
    return result


def formal_counts(root):
    papers = json.loads((root / 'data/catalog.json').read_text())['papers']
    reports = json.loads((root / 'data/reports.json').read_text())['reports']
    return {'catalog_papers': len(papers), 'report_records': len(reports),
            'imported_stage_slots': sum(s.get('status') == 'imported'
                for paper in papers for s in paper['stages'].values())}


def generate_without_source_changes(test, root, generate, outputs=()):
    """The same pre/post contract wraps the real C2 writer and CI wrapper builds."""
    immutable_history(test, root)
    before_sources = source_hashes(root, outputs)
    before_counts = formal_counts(root)
    result = generate()
    test.assertEqual(formal_counts(root), before_counts,
                     'C2 generation changed formal catalog/report/Stage counts')
    test.assertEqual(source_hashes(root, outputs), before_sources,
                     'C2 generation changed repository inputs')
    immutable_history(test, root)
    return result


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
        for name in (c2.SOURCE, c2.INPUT_SOURCE, c2.RESEARCH_INPUT_SOURCE):
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
        self.assertEqual(len(before), 22)
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
    def test_immutable_raw_history_and_old_c_archive(self):
        immutable_history(self, ROOT)

    def test_c2_generation_preserves_current_sources_and_derived_counts(self):
        with tempfile.TemporaryDirectory(prefix='.c2-state-', dir=ROOT) as target:
            generate_without_source_changes(self, ROOT, lambda: c2.write_preview(ROOT, Path(target)),
                                            outputs=(Path(target),))
            c2.validate_output(ROOT, Path(target))

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
        self.assertEqual(len(c2.payloads(ROOT)), 22)
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
        # Deployment-neutral wording preserves the isolated route without claiming acceptance.
        self.assertIn('<title>具身导航研究三树 · RoboPaperAtlas</title>', entry)
        self.assertIn('<span class="local-badge">隔离预览</span>', entry)
        self.assertIn('class="skip" href="#global-map"', entry)
        self.assertIn('id="global-map" tabindex="-1"', entry)
        analysis = (source / 'analysis/c2.js').read_text()
        self.assertIn("<span>隔离预览 · '+esc(paper.version)+'</span>", analysis)
        for rendered_source in (entry, analysis):
            for transient_status in ('本地候选', '本地交互候选', '未发布', '未上线'):
                self.assertNotIn(transient_status, rendered_source)
        # Auxiliary scope moves into the requested native disclosure; it remains
        # in the document before navigation, and is never removed or rewritten.
        self.assertGreater(entry.index('data-c2-range='), entry.index('<details class="entry-help">'))
        self.assertLess(entry.index('data-c2-range='), entry.index('id="global-map"'))
        self.assertIn('<details class="entry-help"><summary>方法原文、收录范围与使用边界</summary>', entry)
        self.assertGreater(entry.index('data-c2-range='), entry.index('</header>'))
        self.assertEqual([urlsplit(p).path for p in htmls['index.html'].scripts], [
            'data/catalog.js', 'data/literature.js', 'data/challenge.js', 'model.js', 'app.js',
            'analysis/data/bundle.js', 'analysis/model.js', 'data/reference-complete.js', 'research.js',
            'data/research-graph.js', 'data/scoped-analysis.js', 'analysis/c2.js'])
        for name in c2.PUBLIC_FILES:
            if name.endswith('.jpg'):
                self.assertTrue((source / name).read_bytes().startswith(b'\xff\xd8'))
                continue
            text = (source / name).read_text()
            for forbidden in ('/workspace/', '/agent_notes/', 'dream_notes', 'localhost',
                              '127.0.0.1', 'tests/fixtures/', 'file://'):
                self.assertNotIn(forbidden, text, name)
            if name.endswith('.css'):
                self.assertNotRegex(text, r'@import\b|url\(\s*[\'"]?https?://')
    def test_complete_tree_topology_and_horizontal_geometry(self):
        run = subprocess.run(['node', str(ROOT / 'tests/test_complete_tree_atlas.cjs')],
                             check=True, capture_output=True, text=True, timeout=60)
        self.assertEqual(len(re.findall(r'^PASS ', run.stdout, re.M)), 15, run.stdout)

    def test_precise_tree_root_labels_and_bounds(self):
        run = subprocess.run(['node', str(ROOT / 'tests/test_tree_root_labels.cjs')],
                             check=True, capture_output=True, text=True, timeout=60)
        self.assertEqual(len(re.findall(r'^PASS ', run.stdout, re.M)), 7, run.stdout)

    def test_tree_label_bounds_and_complete_text(self):
        run = subprocess.run(['node', str(ROOT / 'tests/test_tree_label_bounds.cjs')],
                             check=True, capture_output=True, text=True, timeout=60)
        self.assertEqual(len(re.findall(r'^PASS ', run.stdout, re.M)), 7, run.stdout)

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
            for script in ('analysis/tests/global-first.test.cjs', 'tests/global-dual.test.cjs', 'tests/three-entry.test.cjs', 'tests/analysis-independent.test.cjs'):
                subprocess.run(['node', str(site / script)], check=True, capture_output=True,
                               text=True, timeout=60)
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
            def generate():
                subprocess.run([sys.executable, str(ROOT / 'scripts/build.py'), '--output', baseline],
                               check=True, capture_output=True, text=True, timeout=90)
                build_previews.write_preview(ROOT, Path(baseline))
                build_previews.write_submit_preview(ROOT, Path(baseline))
                subprocess.run([sys.executable, str(ROOT / 'scripts/build_previews.py'), '--output', integrated],
                               check=True, capture_output=True, text=True, timeout=90)
            generate_without_source_changes(self, ROOT, generate,
                                            outputs=(Path(baseline), Path(integrated)))
            hashes = lambda folder: {p.relative_to(folder).as_posix(): digest(p)
                                     for p in Path(folder).rglob('*') if p.is_file()}
            old, new = hashes(baseline), hashes(integrated)
            added = {n for n in new if n not in old}
            self.assertEqual(added, {c2.ROUTE + '/' + n for n in c2.PUBLIC_FILES})
            self.assertEqual(old, {n: h for n, h in new.items() if n not in added})
            c2.validate_output(ROOT, Path(integrated))


class RadarC2EvolutionControls(unittest.TestCase):
    """Mutate isolated repositories, then exercise the actual guarded C2 writer."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='c2-contract-control-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in SOURCE_DIRS:
            source = ROOT / name
            if source.is_dir():
                shutil.copytree(source, self.root / name,
                                ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))

    def generate(self):
        return generate_without_source_changes(self, self.root,
                    lambda: c2.write_preview(self.root, self.root / 'dist'))

    def generator_mutation(self, mutation):
        validate_output = c2.validate_output
        def mutated_output(*args, **kwargs):
            result = validate_output(*args, **kwargs)
            mutation()  # Run inside the real writer, after its own output validation.
            return result
        return patch.object(c2, 'validate_output', side_effect=mutated_output)

    def test_generator_mutating_existing_source_is_detected(self):
        path = self.root / 'scripts/navigation_stage1_v2_preview.py'
        before = path.read_bytes()
        with self.generator_mutation(lambda: path.write_bytes(before + b'\n# unintended generator write\n')):
            with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                self.generate()
        self.assertEqual(path.read_bytes(), before + b'\n# unintended generator write\n')
        self.assertEqual(len(c2.validate_output(self.root, self.root / 'dist')), len(c2.PUBLIC_FILES))

    def test_generator_mutating_future_source_namespace_is_detected(self):
        path = self.root / 'future-source-space/module.py'
        path.parent.mkdir()
        path.write_text('# independent future source\n')
        with self.generator_mutation(lambda: path.write_text('# unintended generator mutation\n')):
            with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                self.generate()

    def test_generator_creating_new_source_namespace_is_detected(self):
        path = self.root / 'new-source-space/module.py'
        def mutate():
            path.parent.mkdir()
            path.write_text('# unintended new source\n')
        with self.generator_mutation(mutate):
            with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                self.generate()

    def test_generator_replacing_top_level_source_with_symlink_is_detected(self):
        with tempfile.TemporaryDirectory(prefix='c2-external-source-') as outside:
            external = Path(outside) / 'docs'
            shutil.copytree(self.root / 'docs', external)
            def mutate():
                shutil.rmtree(self.root / 'docs')
                (self.root / 'docs').symlink_to(external, target_is_directory=True)
            with self.generator_mutation(mutate):
                with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                    self.generate()
            self.assertTrue((self.root / 'docs').is_symlink())

    def test_generator_promoting_stage_state_is_detected(self):
        path = self.root / 'data/catalog.json'
        catalog = json.loads(path.read_text())
        paper = next(p for p in catalog['papers']
                     if p['stages']['stage1']['status'] == 'not_imported')
        paper['stages']['stage1']['status'] = 'imported'
        before = formal_counts(self.root)
        with self.generator_mutation(lambda: path.write_text(json.dumps(catalog))):
            with self.assertRaisesRegex(AssertionError, 'C2 generation changed formal catalog/report/Stage counts'):
                self.generate()
        self.assertEqual(formal_counts(self.root)['imported_stage_slots'], before['imported_stage_slots'] + 1)

    def test_generator_rewriting_stage_metadata_without_count_change_is_detected(self):
        path = self.root / 'data/catalog.json'
        catalog = json.loads(path.read_text())
        stage = next(s for p in catalog['papers'] for s in p['stages'].values() if s['artifacts'])
        stage['artifacts'][0]['sha256'] = '0' * 64
        before = formal_counts(self.root)
        with self.generator_mutation(lambda: path.write_text(json.dumps(catalog))):
            with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                self.generate()
        self.assertEqual(formal_counts(self.root), before)

    def test_generator_adding_or_deleting_source_is_detected(self):
        for operation in ('add', 'delete'):
            with self.subTest(operation=operation):
                path = self.root / 'scripts/control-unintended.py'
                if operation == 'delete':
                    path.write_text('# pre-existing source\n')
                mutate = (lambda: path.write_text('# unintended source\n')) if operation == 'add' else path.unlink
                with self.generator_mutation(mutate):
                    with self.assertRaisesRegex(AssertionError, 'C2 generation changed repository inputs'):
                        self.generate()
                if path.exists():
                    path.unlink()

    def test_corrupt_immutable_raw_history_rejected_before_generation(self):
        protection = json.loads((self.root / PROTECTION_FIXTURE).read_text())
        name = next(n for n in protection['pr18'] if n.startswith('data/report-parts/'))
        path = self.root / name
        path.write_bytes(path.read_bytes() + b'\ncorrupt historical raw bytes\n')
        # The initial hash comes from reviewed history, never a post-attack snapshot.
        with patch.object(c2, 'write_preview', wraps=c2.write_preview) as writer:
            with self.assertRaisesRegex(AssertionError, 'Immutable raw history: '):
                self.generate()
            writer.assert_not_called()
        self.assertFalse((self.root / 'dist').exists())

    def test_corrupt_old_c_archive_rejected_before_generation(self):
        path = self.root / 'previews/radar-trees-c/weekly-2026-10-04.html'
        path.write_bytes(path.read_bytes() + b'<!-- corrupt archive -->')
        with patch.object(c2, 'write_preview', wraps=c2.write_preview) as writer:
            with self.assertRaisesRegex(AssertionError, 'Immutable old-C archive: '):
                self.generate()
            writer.assert_not_called()

    def test_independent_catalog_growth_is_allowed_before_generation(self):
        from validate import validate_catalog
        import reports
        path = self.root / 'data/catalog.json'
        catalog = json.loads(path.read_text())
        paper = copy.deepcopy(next(p for p in catalog['papers'] if p['original_metadata']
                      and all(s['status'] == 'not_imported' for s in p['stages'].values())))
        paper.update(id='c2-evolution-control', title='Independent synthetic catalog evolution control',
                     authors='Test-only synthetic metadata')
        paper['original_metadata'].update(title=paper['title'], authors=paper['authors'])
        before = formal_counts(self.root)
        catalog['papers'].append(paper)
        path.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n')
        records = reports.load_reports(self.root)
        self.assertEqual(validate_catalog(catalog, records), before['catalog_papers'] + 1)
        self.generate()
        self.assertEqual(formal_counts(self.root), dict(before, catalog_papers=before['catalog_papers'] + 1))
        self.assertEqual(c2.payloads(self.root), c2.payloads(ROOT))

    def test_independent_formal_import_is_allowed_in_synthetic_repository(self):
        # Simulate a separately approved import using an already code-pinned exact
        # report. This temporary assumption is NOT approval or publication of the
        # real pending candidate; its original manifest/provenance is untouched.
        import reports
        from validate import expected_stage, validate_catalog
        before = formal_counts(self.root)
        candidate = json.loads((self.root / 'candidates/navigation-stage1-v2-pending.json').read_text())['reports'][0]
        record = dict(candidate, review_status=reports.expected_review_status(candidate))
        registry_path = self.root / 'data/reports.json'
        registry = json.loads(registry_path.read_text())
        registry['reports'].append(record)
        registry_path.write_text(json.dumps(registry))
        records = reports.load_reports(self.root)  # Exact transport/security validation.
        path = self.root / 'data/catalog.json'
        catalog = json.loads(path.read_text())
        paper = next(p for p in catalog['papers'] if p['id'] == record['paper_id'])
        self.assertEqual(paper['stages'][record['stage']]['status'], 'not_imported')
        paper['stages'][record['stage']] = expected_stage(paper['id'], record['stage'], records)
        path.write_text(json.dumps(catalog))
        self.assertEqual(validate_catalog(catalog, records), before['catalog_papers'])
        self.generate()
        self.assertEqual(formal_counts(self.root), dict(before,
                         report_records=before['report_records'] + 1,
                         imported_stage_slots=before['imported_stage_slots'] + 1))
        self.assertEqual(c2.payloads(self.root), c2.payloads(ROOT))

    def test_independent_candidate_gate_evidence_update_is_allowed(self):
        import navigation_stage1_v2_preview as v2
        before_sources = v2.load_sources(self.root)
        path = self.root / v2.MANIFEST
        candidate = json.loads(path.read_text())
        candidate['gates']['control_evidence'] = 'synthetic_metadata_only_not_acceptance'
        path.write_text(json.dumps(candidate))
        path = self.root / 'candidates/navigation-stage1-v2-migration-plan.json'
        plan = json.loads(path.read_text())
        plan['required_gates']['control_evidence'] = 'synthetic_metadata_only_not_acceptance'
        path.write_text(json.dumps(plan))
        path = self.root / 'candidates/navigation-stage1-v2-print-policy.json'
        policy = json.loads(path.read_text())
        policy['control_evidence'] = 'synthetic_metadata_only_not_acceptance'
        path.write_text(json.dumps(policy))
        self.assertFalse(policy['chrome_native_print_verified'])
        self.assertEqual(candidate['status'], 'pending_candidate')
        self.assertEqual(v2.load_sources(self.root), before_sources)
        self.generate()
        self.assertEqual(c2.payloads(self.root), c2.payloads(ROOT))

    def test_independent_old_c_ui_repair_with_reviewed_manifest_is_allowed(self):
        source = self.root / old_c.SOURCE
        css = source / 'graph.css'
        css.write_bytes(css.read_bytes() + b'\nbutton:focus-visible { outline-offset: 3px; }\n')
        script = source / 'graph.js'
        script.write_bytes(script.read_bytes() + b'\n// Independent presentation maintenance control.\n')
        entry = source / 'index.html'
        text = entry.read_text()
        for name in ('graph.css', 'graph.js'):
            text, count = re.subn(re.escape(name) + r'\?v=([0-9a-f]+)',
                                 lambda match: name + '?v=' + digest(source / name)[:len(match[1])], text)
            self.assertEqual(count, 1)
        entry.write_text(text)
        # A stale/missing review hash is still rejected by the actual guard.
        with self.assertRaisesRegex(ValueError, 'Radar C reviewed source hash mismatch'):
            self.generate()
        manifest_path = self.root / old_c.MANIFEST
        manifest = json.loads(manifest_path.read_text())
        for name in ('graph.css', 'graph.js', 'index.html'):
            manifest['files'][name] = digest(source / name)
        manifest_path.write_text(json.dumps(manifest))
        self.assertEqual(len(old_c.payloads(self.root)), len(old_c.FILES))
        self.generate()
        self.assertEqual(c2.payloads(self.root), c2.payloads(ROOT))

    def test_independent_preview_generator_repair_is_allowed_before_generation(self):
        path = self.root / 'scripts/navigation_stage1_v2_preview.py'
        # A portable smoke control for the path that formerly failed PR18's hash
        # pin. Release evidence also tests the actual five-file reader-focus fix.
        path.write_bytes(path.read_bytes() + b'\n# Independent shell maintenance control.\n')
        compile(path.read_bytes(), str(path), 'exec')
        self.generate()
        self.assertEqual(c2.payloads(self.root), c2.payloads(ROOT))



class TaskOriginPresentationTests(unittest.TestCase):
    def test_existing_task_origin_records_and_priority_boundaries(self):
        # Evaluate production render helpers without bootstrap; no duplicate test implementation.
        program = r"""
const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const root=process.cwd(),file=root+'/previews/radar-c2-analysis/app.js';
const src=fs.readFileSync(file,'utf8'),cut=src.indexOf('function renderTree(');
assert(cut>0);
const context={window:{TreeModel:{}},document:{},Map,console};
vm.createContext(context);
vm.runInContext(src.slice(0,cut)+`window.originTest={statusLabel,contractHtml,setEvidence:entries=>{model={trees:{l:{evidence:new Map(entries)}}};}};})();`,context);
const api=context.window.originTest,task=origin=>({type:'task_contract',origin});
api.setEvidence([]);
const negative=task({title:'OVON',first_claim_scope:'不授予所有开放词汇导航首创',read_url:'https://arxiv.org/html/2409.14296v1'});
assert(!api.statusLabel(negative).includes('作者限定的首创声明'));
assert(api.statusLabel(negative).includes('首创未核实'));
assert(api.contractHtml(negative).includes('不授予所有开放词汇导航首创'));
assert(!api.contractHtml(negative).includes('<b>作者首创声明的范围：</b>'));
for(const origin of [{},{title:''},{title:' ',first_claim_scope:'some text'},{milestones:[]},{milestones:[{}]}]){
 assert.equal(api.statusLabel(task(origin)),'起源 / 首创待核');
 assert(api.contractHtml(task(origin)).includes('原始定义来源待核'));
}
const raw=fs.readFileSync(root+'/previews/radar-c2-analysis/data/literature.js','utf8');
vm.runInContext(raw,context);
const data=context.window.LITERATURE_TREE;api.setEvidence(data.evidence.map(e=>[e.evidence_id,e]));
for(const id of ['task-vln-iterative','task-goat-sequence','task-open-eqa-active','task-open-eqa-memory','task-multion','task-embodiedqa-classic']){
 const node=data.nodes.find(n=>n.node_id===id),html=api.contractHtml(node);
 assert(html.includes('任务 / 协议来源记录'),id);assert(!html.includes('原始定义来源待核'),id);
 assert(html.includes('href="https://'),id);assert(!html.includes('[object Object]'),id);
 assert(api.statusLabel(node).includes('首创未核实'),id);
}
const goat=api.contractHtml(data.nodes.find(n=>n.node_id==='task-goat-sequence'));
assert(goat.includes('https://www.roboticsproceedings.org/rss20/p073.pdf'));
assert(goat.includes('Khanna_GOAT-Bench_A_Benchmark_for_Multi-Modal_Lifelong_Navigation'));
const unknown=data.nodes.find(n=>n.node_id==='task-lmee');
assert(api.contractHtml(unknown).includes('原始定义来源待核'));
const missing=task({milestones:[{name:'Unlinked task',task_definition:{summary:'Defined task',source_id:'missing'},benchmark_origin:{summary:'Benchmark'}}]});
assert(api.contractHtml(missing).includes('来源链接待补'));assert(!api.contractHtml(missing).includes('href='));
const positive=task({title:'R2R',first_claim_scope:'作者声称首个真实建筑benchmark',read_url:'https://example.org/paper'});
assert(api.statusLabel(positive).includes('首创未核实'));assert(api.contractHtml(positive).includes('作者声称首个真实建筑benchmark'));
const unsafe=api.contractHtml(task({title:'<script>alert(1)</script>',read_url:'javascript:alert(1)'}));
assert(unsafe.includes('&lt;script&gt;'));assert(!unsafe.includes('href="javascript:'));
assert.equal(api.statusLabel({type:'paper_ref'}),'');assert.equal(api.statusLabel({type:'module',status:'pending'}),'待核候选');
console.log('PASS negative/empty/multiple/nested/pending/missing/positive/escaping task origins');
"""
        result = subprocess.run(['node', '-e', program], cwd=ROOT, text=True,
                                capture_output=True, check=True)
        self.assertIn('PASS negative/empty/multiple/nested/pending/missing/positive/escaping', result.stdout)

if __name__ == '__main__':
    unittest.main()
