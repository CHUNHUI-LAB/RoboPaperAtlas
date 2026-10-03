"""Layout-only VBC v2: exact diff, reserved geometry, and immutable predecessors."""
import base64
import copy
import json
from pathlib import Path
import re
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reports as r
import current_reader as current
from report_vbc_stage1 import POLICIES, IMAGE_HASHES

BEFORE = json.loads((ROOT / 'tests/fixtures/vbc-before-layout-v2.json').read_text())
OLD_CSS = '.reader-stage1 .compact-figure .figure-scroll img{max-width:100%;width:auto;max-height:600px;margin:auto}'
NEW_CSS = OLD_CSS.replace('width:auto;', 'width:384px;')
OLD_NOTE = '<p class="reader-document-note">阅读报告 v1 · 核验日期 2026-10-03 · 内容已独立审阅；公开页面视觉验收尚未完成。用“作者表述 / 概括 / 直接观察”区分证据性质；E01–E10 是本页证据单元编号。原文内部的数值与计数异常均显式保留。</p>'
NEW_NOTE = OLD_NOTE.replace('阅读报告 v1', '阅读报告 v2').replace(' · 核验日期', ' · 仅修正 Fig. 2 懒加载前的尺寸占位，正文与图像未改 · 核验日期')


def canonical(value):
    return r.sha(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode())


class VBCLayoutV2Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = r.load_reports(ROOT)
        cls.versions = {record['version']: record for record in cls.records if record['paper_id'] == 'rpa-0067'}
        cls.raw = {version: (ROOT / r.report_path(record)).read_bytes() for version, record in cls.versions.items()}
        cls.text = {version: raw.decode() for version, raw in cls.raw.items()}
        cls.catalog = json.loads((ROOT / 'data/catalog.json').read_text())
        cls.paper = next(p for p in cls.catalog['papers'] if p['id'] == 'rpa-0067')

    def test_exactly_five_reviewed_replacements_and_no_other_byte_changes(self):
        replacements = (
            (OLD_CSS, NEW_CSS),
            ('<title>VBC · 正式出版版第一遍初读 v1</title>', '<title>VBC · 正式出版版第一遍初读 v2</title>'),
            ('<p class="reader-kicker">STAGE 1 · 第一遍初读 · 正式出版版 / v1</p>', '<p class="reader-kicker">STAGE 1 · 第一遍初读 · 正式出版版 / v2</p>'),
            (OLD_NOTE, NEW_NOTE),
            ('RoboPaperAtlas · VBC 正式出版版第一遍初读 v1', 'RoboPaperAtlas · VBC 正式出版版第一遍初读 v2'),
        )
        expected = self.raw['v1']
        for old, new in replacements:
            self.assertEqual(expected.count(old.encode()), 1)
            expected = expected.replace(old.encode(), new.encode(), 1)
        self.assertEqual(expected, self.raw['v2'])
        self.assertEqual(r.sha(self.raw['v1']), '8ded597adad595ca8dd24dbdc6bc9d832ba6f26f8d5676fd867071c6b8a98320')
        self.assertEqual(r.sha(self.raw['v2']), '4db81619423125d9eeb6d2369ee56b764c81e40719cca55da224e8ee82b9c6d9')
        for tag in ('article', 'script'):
            self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>', self.text['v1'], re.S),
                             re.findall(rf'<{tag}\b.*?</{tag}>', self.text['v2'], re.S))

    def test_all_twenty_prior_records_and_412_parts_remain_exact(self):
        self.assertEqual(len(self.records), 21)
        self.assertEqual(self.records[-1]['version'], 'v2')
        self.assertEqual(canonical(self.records[:-1]), BEFORE['records_sha256'])
        prefix = (ROOT / 'data/reports.json').read_bytes()[:BEFORE['registry_prefix_bytes']]
        self.assertEqual(r.sha(prefix), BEFORE['registry_prefix_sha256'])
        paths = sorted((ROOT / 'data/report-parts').rglob('*.txt'))
        prior_parts = [(str(p.relative_to(ROOT)), r.sha(p.read_bytes())) for p in paths
                       if '/rpa-0067/v2/' not in str(p)]
        self.assertEqual(len(prior_parts), BEFORE['old_part_count'])
        self.assertEqual(canonical(prior_parts), BEFORE['old_parts_sha256'])
        for record in self.records[:-1]:
            self.assertEqual(r.sha((ROOT / r.report_path(record)).read_bytes()), record['sha256'])

    def test_lossless_repartition_reuses_73_complete_prior_blobs(self):
        chunks = {version: [(ROOT / r._parts_path(record) / part['file']).read_bytes()
                            for part in record['parts']] for version, record in self.versions.items()}
        self.assertEqual((len(chunks['v1']), len(chunks['v2'])), (76, 77))
        self.assertEqual(chunks['v2'][3:-1], chunks['v1'][2:-1])
        self.assertEqual(chunks['v2'][-1], chunks['v1'][-1].replace('RoboPaperAtlas · VBC 正式出版版第一遍初读 v1'.encode(), 'RoboPaperAtlas · VBC 正式出版版第一遍初读 v2'.encode()))
        self.assertEqual([len(x) for x in chunks['v2'][:3]], [48000, 48000, 73])
        self.assertEqual(b''.join(chunks['v2']), self.raw['v2'])
        for part, chunk in zip(self.versions['v2']['parts'], chunks['v2']):
            chunk.decode('utf-8')
            self.assertTrue(0 < len(chunk) <= 48000)
            self.assertEqual((len(chunk), r.sha(chunk)), (part['bytes'], part['sha256']))

    def test_intrinsic_width_reservation_preserves_images_controls_and_print_css(self):
        old, new = self.text['v1'], self.text['v2']
        self.assertIn(OLD_CSS, old)
        self.assertNotIn(OLD_CSS, new)
        self.assertEqual(new.count(NEW_CSS), 1)
        self.assertIn('.figure-scroll img{display:block;width:100%;height:auto;max-width:100%;margin:0 auto}', new)
        figures = re.findall(r'<figure\b[^>]*class="[^"]*compact-figure[^"]*".*?</figure>', new, re.S)
        self.assertEqual(len(figures), 1)
        self.assertIn('id="figure-02"', figures[0])
        image = re.search(r'<img\b[^>]*>', figures[0])[0]
        self.assertIn('width="384"', image)
        self.assertIn('height="579"', image)
        self.assertIn('loading="lazy"', image)
        self.assertIn('decoding="async"', image)
        png = base64.b64decode(re.search(r'data:image/png;base64,([A-Za-z0-9+/=]+)', image)[1], validate=True)
        self.assertEqual(struct.unpack('>II', png[16:24]), (384, 579))
        # Contract-level geometry only, not a browser QA assertion: definite CSS
        # width + HTML aspect ratio reserve the decoded size, including shrinkage.
        for available in (240, 304, 384, 500, 1040):
            width = min(384, available)
            self.assertLessEqual(width, available)
            self.assertEqual(width * 579 / 384, 579 if available >= 384 else available * 579 / 384)
        for pattern in (r'<img\b[^>]*>', r'<input\b[^>]*>', r'<label\b.*?</label>'):
            self.assertEqual(re.findall(pattern, old, re.S), re.findall(pattern, new, re.S))
        styles = [re.search(r'<style>(.*?)</style>', text, re.S)[1] for text in (old, new)]
        for pattern in (r'[^{}]*:checked[^{}]*\{[^{}]*\}', r'@media print\{[^\n]*'):
            self.assertEqual(re.findall(pattern, styles[0]), re.findall(pattern, styles[1]))
        images = re.findall(r'data:image/png;base64,([A-Za-z0-9+/=]+)', new)
        self.assertEqual(tuple(r.sha(base64.b64decode(x, validate=True)) for x in images), IMAGE_HASHES)

    def test_only_vbc_artifact_prepend_and_classification_hash_change(self):
        restored = copy.deepcopy(self.catalog)
        paper = next(p for p in restored['papers'] if p['id'] == 'rpa-0067')
        artifacts = paper['stages']['stage1']['artifacts']
        self.assertEqual([a['version'] for a in artifacts], ['v2', 'v1'])
        expected = dict(artifacts[1], version='v2', path='artifacts/rpa-0067/v2/first-pass.html', sha256=self.versions['v2']['sha256'])
        self.assertEqual(artifacts.pop(0), expected)
        self.assertEqual(canonical(paper), BEFORE['vbc_catalog_sha256'])
        self.assertEqual(r.sha((json.dumps(restored, ensure_ascii=False, indent=2) + '\n').encode()), BEFORE['catalog_sha256'])
        classification = json.loads((ROOT / 'data/classification.json').read_text())
        self.assertEqual(classification['catalog_sha256'], r.sha((ROOT / 'data/catalog.json').read_bytes()))
        classification['catalog_sha256'] = BEFORE['catalog_sha256']
        self.assertEqual(r.sha((json.dumps(classification, ensure_ascii=False, indent=2) + '\n').encode()), BEFORE['classification_sha256'])
        stages = [s for p in self.catalog['papers'] for s in p['stages'].values()]
        self.assertEqual(sum(s['status'] == 'imported' for s in stages), 12)
        self.assertEqual(sum(any(s['status'] == 'imported' for s in p['stages'].values()) for p in self.catalog['papers']), 5)
        self.assertEqual(sum(all(s['status'] == 'imported' for s in p['stages'].values()) for p in self.catalog['papers']), 3)

    def test_both_policies_are_closed_and_cannot_be_cross_applied(self):
        self.assertEqual([identity['version'] for identity, path in POLICIES], ['v1', 'v2'])
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'data').mkdir()
            for identity, path in POLICIES:
                (root / path).write_bytes((ROOT / path).read_bytes())
            for version, record in self.versions.items():
                r.split_report(root, record, self.raw[version])
                other = 'v1' if version == 'v2' else 'v2'
                with self.assertRaisesRegex(ValueError, 'fingerprint'):
                    r.split_report(root, record, self.raw[other])
                for updates in ({'version': 'v3'}, {'version': '../../v2'}, {'stage': 'stage2', 'filename': 'writing-close-reading.html'}, {'source_sha256': '0' * 64}):
                    with self.subTest(version=version, updates=updates), self.assertRaises(ValueError):
                        r.split_report(root, dict(record, **updates), self.raw[version])
            policy_path = POLICIES[1][1]
            policy = json.loads((root / policy_path).read_text())
            # Rehashing a changed document still cannot bypass style/script/image guards.
            for old, new, message in ((b'width:384px;', b'width:auto;', 'stylesheet'),
                                      (b'updatePosition();', b'alert(1);', 'script')):
                changed = self.raw['v2'].replace(old, new, 1)
                (root / policy_path).write_text(json.dumps(dict(policy, document_sha256=r.sha(changed))))
                with self.assertRaisesRegex(ValueError, message):
                    r.split_report(root, self.versions['v2'], changed)
            (root / policy_path).write_text(json.dumps(dict(policy, version='v1')))
            with self.assertRaisesRegex(ValueError, 'Wrong VBC reader policy'):
                r.split_report(root, self.versions['v2'], self.raw['v2'])

    def test_current_reader_is_v2_without_science_or_runtime_rewrites(self):
        page = current.render(ROOT, self.paper, 'stage1', self.records)
        self.assertEqual(current.VBC_FROZEN['stage1']['version'], 'v2')
        self.assertIn('artifacts/rpa-0067/v2/first-pass.html', page)
        self.assertIn('公开页面视觉验收尚未完成', page)
        self.assertIn('仅修正 Fig. 2 懒加载前的尺寸占位', page)
        for tag in ('article', 'style', 'script'):
            self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>', page.replace(current.context_script(ROOT), ''), re.S),
                             re.findall(rf'<{tag}\b.*?</{tag}>', self.text['v2'], re.S))


if __name__ == '__main__':
    unittest.main()
