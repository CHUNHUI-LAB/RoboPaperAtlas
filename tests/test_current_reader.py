import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import details
import current_reader as current
from reports import load_reports, report_path


class CurrentReaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.papers = json.loads((ROOT / 'data/catalog.json').read_text())['papers']
        cls.paper = next(p for p in cls.papers if p['id'] == 'rpa-0012')
        cls.records = load_reports(ROOT)

    def test_current_stages_keep_exact_scripts_styles_and_report_content(self):
        for stage, state in self.paper['stages'].items():
            page = current.render(ROOT, self.paper, stage, self.records)
            artifact = state['artifacts'][0]
            source = (ROOT / artifact['path']).read_text()
            self.assertIn(f'href="{stage}.html" aria-current="page"', page)
            self.assertNotIn('此阶段报告尚未提供', page)
            for target in self.paper['stages']:
                self.assertIn(f'href="{target}.html"', page)
            self.assertIn('href="../../../' + artifact['path'] + '"', page)
            self.assertNotIn('<iframe', page)
            self.assertIn('当前导航视图', page)
            for tag in ['script', 'style', 'article']:
                pattern = rf'<{tag}\b.*?</{tag}>'
                self.assertEqual(re.findall(pattern, page.replace(current.context_script(ROOT), ""), re.S), re.findall(pattern, source, re.S))

    def test_umi_current_stage1_to_stage2_uses_v4_without_history_rewrites(self):
        paper = next(p for p in self.papers if p['id'] == 'rpa-0062')
        for stage, version in [('stage1', 'v3'), ('stage2', 'v4'), ('stage3', 'v3')]:
            page = current.render(ROOT, paper, stage, self.records)
            source = (ROOT / paper['stages'][stage]['artifacts'][0]['path']).read_text()
            self.assertIn('基于固定报告 ' + version, page)
            self.assertIn('href="../index.html#reading"', page)
            self.assertIn('href="../../../' + paper['stages'][stage]['artifacts'][0]['path'] + '"', page)
            nav = re.search(r'<nav class="reader-stages".*?</nav>', page, re.S)[0]
            for target in ('stage1', 'stage2', 'stage3'):
                self.assertIn(f'href="{target}.html"', nav)
            for tag in ('article', 'script', 'style'):
                pattern = rf'<{tag}\b.*?</{tag}>'
                self.assertEqual(re.findall(pattern, page.replace(current.context_script(ROOT), ""), re.S), re.findall(pattern, source, re.S))
            if stage != 'stage2':
                self.assertIn('href="writing-close-reading.html"', source)
        self.assertEqual(current.entry_path('rpa-0062', 'stage2'), 'papers/rpa-0062/reading/stage2.html')
        self.assertEqual(current.entry_path('rpa-0052', 'stage1'), 'papers/rpa-0052/reading/stage1.html')
        for stage in ('stage1', 'stage2', 'stage3'):
            self.assertIn(f'href="../../papers/rpa-0062/reading/{stage}.html"', details(paper))
        with patch.dict(current.UMI_FROZEN, {'stage1': dict(current.UMI_FROZEN['stage1'], nav='<nav>unknown</nav>')}):
            with self.assertRaisesRegex(ValueError, 'signature'):
                current.render(ROOT, paper, 'stage1', self.records)
        with patch.dict(current.UMI_FROZEN, {'stage2': dict(current.UMI_FROZEN['stage2'], version='v3')}):
            with self.assertRaisesRegex(ValueError, 'Unreviewed UMI'):
                current.render(ROOT, paper, 'stage2', self.records)

    def test_one_hashed_navigation_runtime_is_added_only_to_current_views(self):
        script = current.context_script(ROOT)
        self.assertRegex(script, r'^<script src="../../../assets/catalog-navigation.js\?v=[0-9a-f]{12}" defer></script>$')
        for paper in self.papers:
            if paper['id'] not in current.CURRENT_READER_PAPERS:
                continue
            for stage in paper['stages']:
                page = current.render(ROOT, paper, stage, self.records)
                source = (ROOT / paper['stages'][stage]['artifacts'][0]['path']).read_text()
                self.assertEqual(page.count(script), 1)
                self.assertNotIn('catalog-navigation.js', source)
                for tag in ('article', 'script', 'style'):
                    pattern = rf'<{tag}\b.*?</{tag}>'
                    self.assertEqual(re.findall(pattern, page.replace(script, ''), re.S), re.findall(pattern, source, re.S))

    def test_umi_narrow_reader_has_a_visible_breadcrumb_return_outside_hidden_brand(self):
        paper = next(p for p in self.papers if p['id'] == 'rpa-0062')
        for stage in ('stage1', 'stage3'):
            page = current.render(ROOT, paper, stage, self.records)
            breadcrumb = re.search(r'<div class="reader-breadcrumb">.*?</div>', page, re.S)[0]
            self.assertIn('<a class="atlas-return" href="../index.html#reading">← 回到论文详情</a>', breadcrumb)
            self.assertNotIn('reader-paper-link', breadcrumb)
            self.assertNotIn('>Library</a>', breadcrumb)

    def test_missing_stage_is_disabled_and_not_written(self):
        paper = copy.deepcopy(self.paper)
        paper['stages']['stage3'] = {'status': 'not_imported', 'artifacts': []}
        page = current.render(ROOT, paper, 'stage1', self.records)
        self.assertIn('aria-disabled="true"><small>03 · 未完成</small>', page)
        self.assertNotIn('href="stage3.html"', page)
        with self.assertRaises(ValueError):
            current.render(ROOT, paper, 'stage3', self.records)
        with tempfile.TemporaryDirectory() as d:
            current.write_current_readers(ROOT, Path(d), [paper], self.records)
            self.assertEqual(len(list(Path(d).rglob('*.html'))), 2)

    def test_unknown_signature_and_source_hash_fail_closed(self):
        with patch.dict(current.FROZEN_NAV, {'stage1': '<nav>unknown</nav>'}):
            with self.assertRaisesRegex(ValueError, 'signature'):
                current.render(ROOT, self.paper, 'stage1', self.records)
        records = copy.deepcopy(self.records)
        next(r for r in records if r['paper_id'] == 'rpa-0012' and r['stage'] == 'stage1' and r['version'] == 'v2')['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'hash mismatch'):
            current.render(ROOT, self.paper, 'stage1', records)
        with self.assertRaisesRegex(ValueError, 'not registered'):
            current.render(ROOT, self.paper, 'stage1', [])

    def test_exact_output_validation_rejects_changes_or_extra_pages(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d)
            current.write_current_readers(ROOT, out, self.papers, self.records)
            self.assertEqual(len(current.validate_current_readers(ROOT, out, self.papers, self.records)), 9)
            dest = out / current.entry_path(self.paper['id'], 'stage1')
            original = dest.read_bytes()
            dest.write_bytes(original + b'<script>alert(1)</script>')
            with self.assertRaisesRegex(ValueError, 'output mismatch'):
                current.validate_current_readers(ROOT, out, self.papers, self.records)
            dest.write_bytes(original)
            (dest.parent / 'extra.html').write_text('extra')
            with self.assertRaisesRegex(ValueError, 'Unexpected current reader'):
                current.validate_current_readers(ROOT, out, self.papers, self.records)

    def test_missing_output_directory_fails_closed(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError, 'Missing or unsafe'):
                current.validate_current_readers(ROOT, Path(d), self.papers, self.records)
            self.assertEqual(current.validate_current_readers(ROOT, Path(d), self.papers, []), set())

    def test_detail_routes_and_original_hashes_preserved(self):
        page = details(self.paper)
        for stage, state in self.paper['stages'].items():
            self.assertIn(f'href="../../papers/rpa-0012/reading/{stage}.html"', page)
            for artifact in state['artifacts']:
                self.assertIn('href="../../' + artifact['path'] + '"', page)
        with tempfile.TemporaryDirectory() as d:
            current.write_current_readers(ROOT, Path(d), self.papers, self.records)
            self.assertEqual(len(list(Path(d).rglob('*.html'))), 9)
        for r in self.records:
            self.assertEqual(hashlib.sha256((ROOT / report_path(r)).read_bytes()).hexdigest(), r['sha256'])
