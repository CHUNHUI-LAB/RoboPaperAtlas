"""A reviewed author-manuscript Stage 2 adds one report, without rewriting history."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reports
import current_reader as current
from report_roboduet_stage2 import IDENTITY, POLICY_PATH, SECTION_IDS, UNIT_IDS, QUOTES
from validate import expected_stage, validate_catalog
from build import details

FROZEN = json.loads((ROOT / 'tests/fixtures/reports-before-roboduet-stage2.json').read_text())


class RoboDuetStage2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = reports.load_reports(ROOT)
        cls.record = next(r for r in cls.records if all(r[k] == v for k, v in IDENTITY.items()))
        cls.raw = (ROOT / reports.report_path(cls.record)).read_bytes()
        cls.page = cls.raw.decode()
        cls.policy = json.loads((ROOT / POLICY_PATH).read_text())
        cls.catalog = json.loads((ROOT / 'data/catalog.json').read_text())
        cls.paper = next(p for p in cls.catalog['papers'] if p['id'] == 'rpa-0052')

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / 'data').mkdir()
        shutil.copyfile(ROOT / POLICY_PATH, self.root / POLICY_PATH)

    def set_policy(self, payload, **updates):
        policy = dict(self.policy, document_sha256=reports.sha(payload), **updates)
        (self.root / POLICY_PATH).write_text(json.dumps(policy))

    def test_one_new_report_and_all_existing_bytes_are_immutable(self):
        self.assertEqual(len(self.records), len(FROZEN) + 2)
        for record in self.records:
            key = '/'.join(record[k] for k in ('paper_id', 'version', 'stage'))
            if key in ('rpa-0052/v1/stage2', 'rpa-0052/v1/stage3'):
                continue
            self.assertEqual(record['sha256'], FROZEN[key])
            self.assertEqual(reports.sha((ROOT / reports.report_path(record)).read_bytes()), FROZEN[key])
        self.assertEqual(self.record['source_sha256'],
                         next(r for r in self.records if r['paper_id'] == 'rpa-0052' and r['stage'] == 'stage1')['source_sha256'])

    def test_only_this_exact_stage_identity_and_source_are_allowed(self):
        reports.split_report(self.root, self.record, self.raw)
        for updates in [dict(paper_id='rpa-0053'), dict(stage='stage3', filename='method-code-reading.html'),
                        dict(version='v2'), dict(review_status='approved'), dict(source_sha256='0' * 64),
                        dict(source_url='https://example.com/paper'), dict(pdf_url='https://example.com/paper.pdf')]:
            with self.subTest(updates=updates), self.assertRaises(ValueError):
                reports.split_report(self.root, dict(self.record, **updates), self.raw)

    def test_hashes_pin_document_style_and_script_independently(self):
        changes = [self.raw.replace(b'39/60', b'40/60'),
                   self.raw.replace(b'updatePosition();', b'alert(1);', 1),
                   self.raw.replace(b'--ink:#18212d', b'--ink:#000000', 1)]
        for changed in changes:
            self.assertNotEqual(changed, self.raw)
            with self.assertRaisesRegex(ValueError, 'fingerprint'):
                reports.split_report(self.root, self.record, changed)
        self.set_policy(changes[1])
        with self.assertRaisesRegex(ValueError, 'script'):
            reports.split_report(self.root, self.record, changes[1])
        self.set_policy(changes[2])
        with self.assertRaisesRegex(ValueError, 'stylesheet'):
            reports.split_report(self.root, self.record, changes[2])

    def test_parser_rejects_active_resources_and_quote_or_unit_changes(self):
        injections = ['<img src="https://example.com/a.png">',
                      '<p onclick="alert(1)">bad</p>',
                      '<iframe src="https://example.com"></iframe>',
                      '<a href="file:///tmp/a">bad</a>',
                      '<a href="../../../papers/rpa-0062/index.html">cross paper</a>',
                      '<div data-source-row="arbitrary">bad</div>',
                      '<blockquote class="source-excerpt" lang="en" data-verbatim="paper">Extra quote.</blockquote>']
        changes = [self.raw.replace(b'</body>', i.encode() + b'</body>') for i in injections]
        changes += [self.raw.replace(QUOTES[0].encode(), b'This is a longer different original quotation.'),
                    self.raw.replace(b'data-source-row="A1"', b'data-source-row="A2"', 1),
                    self.raw.replace(b'data-source-row="A1"', b'data-source-row="unknown"', 1),
                    self.raw.replace(b'id="abstract"', b'id="structure"', 1),
                    self.raw.replace(b'We argue</blockquote>', b'<b>We argue</b></blockquote>')]
        for changed in changes:
            self.set_policy(changed)
            with self.subTest(changed=reports.sha(changed)), self.assertRaises(ValueError):
                reports.split_report(self.root, self.record, changed)
        css = re.search(r'<style>(.*?)</style>', self.page, re.S)[1] + '\np{background:url(https://example.com/x)}'
        changed = re.sub(r'<style>.*?</style>', '<style>' + css + '</style>', self.page, flags=re.S).encode()
        self.set_policy(changed, style_sha256=reports.sha(css.encode()))
        with self.assertRaisesRegex(ValueError, 'CSS'):
            reports.split_report(self.root, self.record, changed)

    def test_coverage_quotation_budget_and_source_boundaries(self):
        self.assertEqual(tuple(re.findall(r'<section id="(.*?)"', self.page)), SECTION_IDS)
        self.assertEqual(tuple(re.findall(r'<div[^>]*data-source-row="(.*?)"', self.page)), UNIT_IDS)
        quotes = re.findall(r'<blockquote class="source-excerpt" lang="en" data-verbatim="paper">(.*?)</blockquote>', self.page, re.S)
        self.assertEqual(tuple(quotes), QUOTES)
        self.assertEqual(sum(len(q.split()) for q in quotes), 10)
        for text in ['作者八页稿', '不能称为正式稿精读', '浏览器视觉验收尚未完成',
                     '共32句', '共710词', '450词', '23%', '39/60', '32/60', '21.875%',
                     '11.67个百分点', '同步训练', '并非现在完成时', '两个同指主语',
                     '共享同一个完成时助动词', '引言混合类为2/20，其他类为1/20']:
            self.assertIn(text, self.page)
        for text in ['skill://', '/workspace/', 'evidence-review.md', 'private-sentence-index',
                     'reader-skill', '<img', '<iframe', 'data:application/pdf', '搭配不够整齐',
                     '臂受补偿', '写作精读候选', 'rpa-0062']:
            self.assertNotIn(text, self.page)
        self.assertIn('<small>03 · 未完成</small>方法与代码', self.page)
        self.assertNotIn('.reader-stages a{font-size:11px}', self.page)

    def test_catalog_status_counts_and_classification_metadata(self):
        self.assertEqual(validate_catalog(self.catalog, self.records), 95)
        self.assertEqual(sum(s['status'] == 'imported' for p in self.catalog['papers'] for s in p['stages'].values()), 9)
        self.assertEqual(sum(all(s['status'] == 'imported' for s in p['stages'].values()) for p in self.catalog['papers']), 3)
        self.assertFalse(self.paper['citation_verified'])
        self.assertEqual(self.paper['stages']['stage2'], expected_stage('rpa-0052', 'stage2', self.records))
        self.assertEqual(self.paper['stages']['stage3'], expected_stage('rpa-0052', 'stage3', self.records))
        self.assertIn('写作内容已审阅', details(self.paper))
        overlay = json.loads((ROOT / 'data/classification.json').read_text())
        self.assertEqual(overlay['catalog_sha256'], reports.sha((ROOT / 'data/catalog.json').read_bytes()))

    def test_exact_packaged_interaction_script(self):
        result = subprocess.run(
            ['node', str(ROOT / 'tests/test_roboduet_stage2_controls.cjs')],
            cwd=ROOT, capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_navigation_adds_both_stages_without_rewriting_history(self):
        for stage in ('stage1', 'stage2'):
            page = current.render(ROOT, self.paper, stage, self.records)
            source = (ROOT / self.paper['stages'][stage]['artifacts'][0]['path']).read_text()
            self.assertIn('href="stage1.html"', page)
            self.assertIn('href="stage2.html"', page)
            self.assertIn('href="stage3.html"', page)
            self.assertIn('href="../index.html#reading"', page)
            for tag in ('article', 'script', 'style'):
                self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>', source, re.S),
                                 re.findall(rf'<{tag}\b.*?</{tag}>', page.replace(current.context_script(ROOT), ''), re.S))
        self.assertIn('方法与代码', current.render(ROOT, self.paper, 'stage3', self.records))
        with patch.dict(current.ROBO_FROZEN, {'stage2': dict(current.ROBO_FROZEN['stage2'], sha256='0' * 64)}):
            with self.assertRaisesRegex(ValueError, 'Unreviewed RoboDuet'):
                current.render(ROOT, self.paper, 'stage2', self.records)
        with tempfile.TemporaryDirectory() as target:
            current.write_current_readers(ROOT, Path(target), [self.paper], self.records)
            files = sorted(str(p.relative_to(target)) for p in Path(target).rglob('*.html'))
            self.assertEqual(files, ['papers/rpa-0052/reading/stage1.html', 'papers/rpa-0052/reading/stage2.html', 'papers/rpa-0052/reading/stage3.html'])

if __name__ == '__main__':
    unittest.main()
