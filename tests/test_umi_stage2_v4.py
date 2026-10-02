"""The single reviewed v4 upgrade preserves frozen history and fails closed."""
import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reports
from report_umi_stage2 import IDENTITY, POLICY_PATH, UNIT_IDS, prepare
from reader_theme_preview import read_preview
from test_stage2_inline_quotes import Document
from validate import expected_stage

FROZEN_UMI = {
    'v1/stage1': '2f1e5842f3aabc71f1fb7ab41bc82636f86a2a1dd9ac35e337853b9768c00702',
    'v1/stage2': '7eee3ea784be422b06ca6e357a48b947181fe50109b2530218f4304fe54ba3be',
    'v1/stage3': '7dc4894d5592ac4b71e9f028c35999693d4cfb7ed3dfc20503c9c0db5732b117',
    'v2/stage1': '77133a73a6b5e33e371720ce23dc9d60125e17f5ecc6722fb4b5c05344f25aea',
    'v2/stage2': '7cf09af6dcac2c1409ce8c7b041466b4797d92b349dc6a8270be4fa8173c9b98',
    'v2/stage3': '1f541a7230af3ff47405dc6ac5affab6bfabe92d48b088c3a0accea75336c16d',
    'v3/stage1': '207e383ba08f684b4272dcee766fe2ab5db2613261430b88c28af27018143d2b',
    'v3/stage2': '4521147c364231d3a26f097aa5aa6def11e6050e32057432ed6860c2d5f04ffe',
    'v3/stage3': '2fa0b3f3a65fab738837d2c8a30c43a02473b5bf71ac61cbc5a670b3496e23e9',
}


class UMIStage2V4Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = reports.load_reports(ROOT)
        cls.record = next(r for r in cls.records if all(r[k] == v for k, v in IDENTITY.items()))
        cls.raw = (ROOT / reports.report_path(cls.record)).read_bytes()
        cls.page = cls.raw.decode()
        cls.tree = Document(cls.page).root
        cls.policy = json.loads((ROOT / POLICY_PATH).read_text())

    def test_only_stage2_receives_v4_and_history_remains(self):
        new = [r for r in self.records if r['paper_id'] == 'rpa-0062' and r['version'] == 'v4']
        self.assertEqual(new, [self.record])
        for stage in reports.STAGE_FILES:
            versions = [r['version'] for r in expected_stage('rpa-0062', stage, self.records)['artifacts']]
            self.assertEqual(versions, (['v4'] if stage == 'stage2' else []) + ['v3', 'v2', 'v1'])
        for stage in ('stage1', 'stage3'):
            with self.assertRaisesRegex(ValueError, 'identity'):
                reports.report_path(dict(self.record, stage=stage, filename=reports.STAGE_FILES[stage]))
        self.assertIn('报告版本 v4', self.page)
        self.assertIn('并非新增一次全文重读', self.page)
        for version in ('v1', 'v2', 'v3'):
            self.assertIn(f'artifacts/rpa-0062/{version}/writing-close-reading.html', self.page)
        self.assertNotIn('此页为阅读主题预览', self.page)

    def test_all_original_umi_bytes_and_hashes_are_immutable(self):
        prior = [r for r in self.records if r['paper_id'] == 'rpa-0062' and r['version'] != 'v4']
        self.assertEqual({r['version'] + '/' + r['stage']: r['sha256'] for r in prior}, FROZEN_UMI)
        for record in prior:
            self.assertEqual(hashlib.sha256((ROOT / reports.report_path(record)).read_bytes()).hexdigest(),
                             FROZEN_UMI[record['version'] + '/' + record['stage']])

    def test_visible_pairs_retain_every_source_excerpt_and_location(self):
        preview = Document(read_preview(ROOT, 'reader-theme-preview/umi-on-legs/writing-close-reading.html').decode()).root
        pairs = [n for n in self.tree.nodes() if n.has('source-unit-parallel')]
        prior = [n for n in preview.nodes() if n.has('source-unit-parallel')]
        self.assertEqual(tuple(n.attrs['id'] for n in pairs), UNIT_IDS)
        words = 0
        for pair, old in zip(pairs, prior):
            nodes = list(pair.nodes())
            self.assertFalse(any(n.tag == 'details' or 'hidden' in n.attrs for n in [pair, *nodes, *pair.ancestors()]))
            for cls in ('source-excerpt', 'source-pair-heading', 'source-citation'):
                self.assertEqual(next(n.text() for n in nodes if n.has(cls)),
                                 next(n.text() for n in old.nodes() if n.has(cls)))
            quote = next(n for n in nodes if n.has('source-excerpt'))
            self.assertEqual((quote.tag, quote.attrs['lang']), ('blockquote', 'en'))
            words += len(quote.text().split())
            self.assertIn('整理者译意', next(n.text() for n in nodes if n.has('source-gloss')))
            self.assertIn('[推断]', next(n.text() for n in nodes if n.has('source-writing')))
            citation = next(n for n in nodes if n.has('source-citation'))
            urls = [n.attrs['href'] for n in citation.nodes() if n.tag == 'a']
            page = 1 if pair.attrs['id'].startswith(('A', 'P1-')) else 8 if pair.attrs['id'].startswith('C') else 2
            self.assertEqual(urls, [self.record['pdf_url'] + '#page=' + str(page), '#excerpt-attribution'])
        self.assertEqual(words, 857)
        self.assertFalse(any(n.has('reader-source-panel') or 'data-source-units' in n.attrs for n in self.tree.nodes()))

    def test_license_attribution_and_modification_notices_remain(self):
        note = next(n for n in self.tree.nodes() if n.attrs.get('id') == 'excerpt-attribution')
        for phrase in ('Huy Ha', 'Yihuai Gao', 'Zipeng Fu', 'Jie Tan', 'Shuran Song',
                       '5254–5270', 'CC BY 4.0', '不代表作者背书', '未查看作者签字',
                       'PDF 本身未印 CC 标记', 'PDF 连字', '不润色原句'):
            self.assertIn(phrase, note.text())
        urls = {n.attrs['href'] for n in note.nodes() if n.tag == 'a'}
        self.assertTrue({'https://proceedings.mlr.press/v270/ha25a.html',
                         'https://proceedings.mlr.press/pmlr-license-agreement.html',
                         'https://creativecommons.org/licenses/by/4.0/',
                         'https://2024.corl.org/contributions/instruction-for-authors'} <= urls)
        self.assertEqual(self.record['source_sha256'], '0228e01b083d2fca2cf260115271d0f2c7718844b31799a61ccc34c78762d971')
        self.assertNotEqual(self.record['source_sha256'], self.record['sha256'])
        self.assertNotRegex(self.page, r'<(?:img|iframe|object|embed)\b|data:application/pdf|file:|/workspace/|/private/')

    def test_corrected_grammar_and_author_claim_boundaries(self):
        row = next(n for n in self.tree.nodes() if n.attrs.get('id') == 'P1-S5')
        self.assertIn('28词 · 仅被动', row.text())
        self.assertIn('2 (8.7%)</td><td>1 (4.3%)', self.page)
        self.assertNotIn('P1-S3与P1-S5包含被动瓶颈陈述和主动原因解释', self.page)
        for phrase in ('已有研究基础', '为何通常依赖机器人形态', '尚无得到共同体一致认可',
                       '写作分析不自动把它当因果证明', '不能误读成已做到任意策略即插即用'):
            self.assertIn(phrase, self.page)

    def test_exact_packaged_interaction_script(self):
        result = subprocess.run(['node', str(ROOT / 'tests/test_umi_stage2_controls.cjs')], capture_output=True, text=True, timeout=20)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_security_boundary_rejects_document_asset_and_source_tampering(self):
        with self.assertRaisesRegex(ValueError, 'document fingerprint'):
            prepare(ROOT, self.record, self.raw + b' ')
        with self.assertRaisesRegex(ValueError, 'source PDF fingerprint'):
            prepare(ROOT, dict(self.record, source_sha256='a' * 64), self.raw)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'data').mkdir()
            def check(changed, message=None):
                policy = dict(self.policy, document_sha256=reports.sha(changed))
                (root / POLICY_PATH).write_text(json.dumps(policy))
                with self.assertRaisesRegex(ValueError, message or '.'):
                    reports._parse_html(self.record, changed, root)
            check(self.raw.replace(b"'use strict';", b"'use strict';alert(1);", 1), 'reader-controls script')
            check(self.raw.replace(b'--ink:#18212d', b'--ink:#18212e', 1), 'reader stylesheet')
            for payload in (b'<iframe src="https://example.com"></iframe>',
                            b'<img src="https://example.com/a.png">',
                            b'<p onclick="alert(1)">x</p>', b'<script>alert(1)</script>',
                            b'<style>p{color:red}</style>',
                            b'<style type="text/css">p{color:red}</style>',
                            b'<a href="../v9/a.html">x</a>'):
                check(self.raw.replace(b'</body>', payload + b'</body>'))
            check(self.raw.replace(b'data-source-row="A1"', b'data-source-row="A2"', 1), 'source unit')


if __name__ == '__main__':
    unittest.main()
