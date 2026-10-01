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
                self.assertEqual(re.findall(pattern, page, re.S), re.findall(pattern, source, re.S))

    def test_missing_stage_is_disabled_and_not_written(self):
        paper = copy.deepcopy(self.paper)
        paper['stages']['stage3'] = {'status': 'not_imported', 'artifacts': []}
        page = current.render(ROOT, paper, 'stage1', self.records)
        self.assertIn('aria-disabled="true"><small>03</small>', page)
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
            self.assertEqual(len(current.validate_current_readers(ROOT, out, self.papers, self.records)), 3)
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
            self.assertEqual(len(list(Path(d).rglob('*.html'))), 3)
        for r in self.records:
            self.assertEqual(hashlib.sha256((ROOT / report_path(r)).read_bytes()).hexdigest(), r['sha256'])
