"""Local synthetic promotion-contract tests; passing does not approve a report."""
import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reports as r
import current_reader
import navigation_stage1_preview as preview
from report_navigation_stage1 import IDS, V2_FROZEN
from validate import expected_stage, validate_catalog

PENDING = ROOT / 'candidates/navigation-stage1-v2-pending.json'


def candidate_sources():
    manifest = json.loads(PENDING.read_text())
    assert manifest['status'] == 'pending_candidate'
    result = {}
    for record in manifest['reports']:
        assert record['review_status'] == 'pending_candidate'
        raw = b''.join((ROOT / r._parts_path(record) / p['file']).read_bytes() for p in record['parts'])
        result[record['paper_id']] = (record, raw)
    return result


def synthetic_record(record):
    # Test-only in-memory state, never a statement about completed review gates.
    return dict(record, review_status=r.expected_review_status(record))


class NavigationV2CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = candidate_sources()
        cls.original = preview.load_sources(ROOT)
        cls.historical = r.load_reports(ROOT)
        cls.catalog = json.loads((ROOT / 'data/catalog.json').read_text())

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='stage1-v2-synthetic-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        for pid in IDS:
            for version in ('v1', 'v2'):
                path = f'data/report-{pid}-stage1-{version}-policy.json'
                shutil.copyfile(ROOT / path, self.root / path)

    def rehashed_attack(self, pid, raw):
        path = self.root / f'data/report-{pid}-stage1-v2-policy.json'
        policy = json.loads(path.read_text())
        policy['document_sha256'] = r.sha(raw)
        for tag in ('style', 'script'):
            found = re.findall(fr'<{tag}>(.*?)</{tag}>'.encode(), raw, re.S)
            if len(found) == 1:
                policy[tag + '_sha256'] = r.sha(found[0])
        path.write_text(json.dumps(policy))
        return r.split_report(self.root, synthetic_record(self.sources[pid][0]), raw)

    def test_pending_is_outside_canonical_state(self):
        self.assertEqual(len(self.historical), 21)
        self.assertEqual(tuple(self.sources), IDS)
        self.assertFalse(any(x['paper_id'] in IDS for x in self.historical))
        for paper in self.catalog['papers']:
            if paper['id'] in IDS:
                for state in paper['stages'].values():
                    self.assertEqual(state, {'status': 'not_imported', 'artifacts': []})
        for candidate, raw in self.sources.values():
            with self.assertRaisesRegex(ValueError, 'review state'):
                r._validate_record(candidate)
            with self.assertRaises(ValueError):
                r.split_report(self.root, candidate, raw)
            self.assertNotIn('已独立审阅', re.search(rb'<title>.*?</title>', raw, re.S)[0].decode())

    def test_exact_version_status_contract_has_no_interchangeable_status(self):
        for pid, (candidate, raw) in self.sources.items():
            self.assertEqual(r.expected_review_status(candidate), 'content_approved')
            proposed = synthetic_record(candidate)
            parsed = r._parse_html(proposed, raw, ROOT)
            self.assertEqual((len(parsed.section_ids), parsed.summary_count), (12, 5))
            for bad in ('preview_pending', 'approved', 'pending_candidate', 'not_reviewed'):
                with self.subTest(pid=pid, bad=bad), self.assertRaises(ValueError):
                    r.split_report(self.root, dict(proposed, review_status=bad), raw)
        for original, raw in self.original:
            self.assertEqual(r.expected_review_status(original), 'preview_pending')
            for bad in ('content_approved', 'approved'):
                with self.assertRaises(ValueError):
                    r.split_report(self.root, dict(original, review_status=bad), raw)

    def test_unknown_version_stage_filename_paper_edition_source_rejected(self):
        for pid, (candidate, raw) in self.sources.items():
            proposed = synthetic_record(candidate)
            attacks = [dict(version='v3'), dict(version='v1'),
                       dict(stage='stage2', filename='writing-close-reading.html'),
                       dict(stage='stage3', filename='method-code-reading.html'),
                       dict(filename='writing-close-reading.html'), dict(paper_id='unreviewed'),
                       dict(source_edition='arXiv unversioned'), dict(source_sha256='0'*64),
                       dict(source_url=proposed['source_url'][:-1]+'9'),
                       dict(pdf_url=proposed['pdf_url'][:-1]+'9')]
            for change in attacks:
                with self.subTest(pid=pid, change=change), self.assertRaises(ValueError):
                    r.split_report(self.root, dict(proposed, **change), raw)

    def test_rehashing_policy_never_authorizes_changed_science_or_resources(self):
        attacks = [b'<script>alert(1)</script>', b'<script src="https://example.com/a"></script>',
                   b'<p onclick="alert(1)">x</p>', b'<img src="https://example.com/a.png">',
                   b'<iframe src="https://example.com"></iframe>', b'<svg></svg>',
                   b'<form></form>', b'<a href="javascript:alert(1)">x</a>',
                   b'<a href="file:///tmp/x">x</a>', b'<a href="https://127.0.0.1">x</a>',
                   b'<meta http-equiv="refresh" content="0;url=https://example.com">',
                   b'<p>unreviewed harmless prose is also rejected</p>']
        for pid, (candidate, raw) in self.sources.items():
            changes = [raw.replace(b'</body>', a+b'</body>') for a in attacks]
            changes += [raw.replace(b'id="section-01"', b'id="section-99"', 1),
                        raw.replace(b'updatePosition();', b'alert(1);', 1)]
            changes += [raw.replace(b'<style>', b'<style>'+css, 1) for css in
                        (b'@import "https://example.com/a";', b'p{background:url(https://example.com/a)}',
                         b'p{width:expression(alert(1))}')]
            for changed in changes:
                self.assertNotEqual(changed, raw)
                with self.subTest(pid=pid), self.assertRaisesRegex(ValueError, 'code-pinned'):
                    self.rehashed_attack(pid, changed)

    def test_part_integrity_utf8_and_boundaries(self):
        for pid, (record, raw) in self.sources.items():
            self.assertEqual(r.sha(raw), record['sha256'])
            self.assertEqual(len(raw), record['bytes'])
            for p in record['parts']:
                part = (ROOT / r._parts_path(record) / p['file']).read_bytes()
                part.decode('utf-8')
                self.assertLessEqual(len(part), 48000)
                self.assertEqual((len(part), r.sha(part)), (p['bytes'], p['sha256']))
            proposed = synthetic_record(record)
            split = r.split_report(self.root, proposed, raw)
            self.assertEqual(split, proposed)
            (self.root / 'data/reports.json').write_text(json.dumps({'schema_version': 1, 'reports': [split]}))
            self.assertEqual(r.load_reports(self.root), [split])
            partpath = self.root / r._parts_path(split) / split['parts'][0]['file']
            partpath.write_bytes(partpath.read_bytes()+b'x')
            with self.assertRaises(ValueError):
                r.load_reports(self.root)

    def test_isolated_synthetic_overlay_projects_only_three_stage1_additions(self):
        records = self.historical + [synthetic_record(x[0]) for x in self.sources.values()]
        catalog = copy.deepcopy(self.catalog)
        catalog['updated_at'] = '2026-10-05'
        for paper in catalog['papers']:
            if paper['id'] in IDS:
                paper['stages']['stage1'] = expected_stage(paper['id'], 'stage1', records)
        self.assertEqual(validate_catalog(catalog, records), 95)
        self.assertEqual(len(records), 24)
        imported = [p for p in catalog['papers'] if any(s['status']=='imported' for s in p['stages'].values())]
        self.assertEqual(len(imported), 8)
        self.assertEqual(sum(s['status']=='imported' for p in imported for s in p['stages'].values()), 15)
        self.assertEqual(sum(all(s['status']=='imported' for s in p['stages'].values()) for p in imported), 3)
        for before, after in zip(self.catalog['papers'], catalog['papers']):
            if before['id'] in IDS:
                restored = copy.deepcopy(after)
                restored['stages']['stage1'] = before['stages']['stage1']
                self.assertEqual(restored, before)
            else:
                self.assertEqual(before, after)
        self.assertEqual(records[:21], self.historical)
        shutil.copytree(ROOT / 'assets', self.root / 'assets')
        for pid, (candidate, raw) in self.sources.items():
            record = synthetic_record(candidate)
            r.split_report(self.root, record, raw)
            (self.root / 'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[record]}))
            r.assemble_reports(self.root)
            paper = next(p for p in catalog['papers'] if p['id']==pid)
            page = current_reader.render(self.root, paper, 'stage1', [record])
            self.assertIn('href="../../../artifacts/'+pid+'/v2/first-pass.html"', page)
            self.assertIn('href="../index.html#reading"', page)
            self.assertIn('catalog-navigation.js?v=', page)
            self.assertIn('href="stage1.html" aria-current="page"', page)
            self.assertNotIn('href="stage2.html"', page)
            self.assertNotIn('href="stage3.html"', page)
            self.assertEqual(re.findall(r'<section\b.*?</section>',page,re.S),re.findall(r'<section\b.*?</section>',raw.decode(),re.S))
            with self.assertRaisesRegex(ValueError, 'In-memory'):
                current_reader.render(self.root, paper, 'stage1', [record], preview_payload=raw)
        self.assertEqual(json.loads((ROOT/'data/catalog.json').read_text()),self.catalog)
        self.assertEqual(r.load_reports(ROOT),self.historical)

    def test_only_reviewed_scientific_sections_change_and_report_labels_are_v2(self):
        expected_changes = {'harnessvln': {5, 7}, 'navharness': {2, 8}, 'holoagent-0': {3, 4, 5, 7}}
        originals = {r['paper_id']: raw for r, raw in self.original}
        for pid, (_, raw) in self.sources.items():
            text = raw.decode()
            self.assertNotIn('阅读报告 v1', text)
            self.assertNotIn('报告 v1 · 集成预览', text)
            self.assertTrue('<p class="reader-footer">阅读报告 v2 · 指定原文版本与阅读范围见本页说明 · 不代表独立复现 · 原文及项目链接需联网</p>' in text, 'Final report footer must be neutral and stable')
            old_sections = re.findall(rb'<section\b.*?</section>', originals[pid], re.S)
            new_sections = re.findall(rb'<section\b.*?</section>', raw, re.S)
            self.assertEqual({i for i, (a, b) in enumerate(zip(old_sections, new_sections), 1) if a != b}, expected_changes[pid])
            for tag in ('script', 'math', 'figure'):
                pattern = fr'<{tag}\b.*?</{tag}>'.encode()
                self.assertEqual(re.findall(pattern, originals[pid], re.S), re.findall(pattern, raw, re.S))
            print_policy=json.loads((ROOT/'candidates/navigation-stage1-v2-print-policy.json').read_text())
            old_style=re.search(rb'<style>(.*?)</style>',originals[pid],re.S)[1]
            new_style=re.search(rb'<style>(.*?)</style>',raw,re.S)[1]
            self.assertEqual(new_style,old_style+print_policy['css'].encode())
            without_print_images=re.sub(rb'<img class="math-print-fallback [^>]*>',b'',raw)
            for pattern in (rb'<img\b[^>]*>', rb'<input\b[^>]*>'):
                self.assertEqual(re.findall(pattern, originals[pid], re.S), re.findall(pattern, without_print_images, re.S))

    def test_final_presentation_projection_reconstructs_independent_review_bytes(self):
        proof=json.loads((ROOT/'candidates/navigation-stage1-v2-presentation-proof.json').read_text())
        css=json.loads((ROOT/'candidates/navigation-stage1-v2-print-policy.json').read_text())['css']
        for audit in proof['reports']:
            rec,raw=self.sources[audit['paper_id']]
            self.assertEqual(r.sha(raw),audit['final_sha256'])
            text=raw.decode();self.assertEqual(text.count(css),1);text=text.replace(css,'',1)
            text,count=re.subn(r'<img class="math-print-fallback [^>]*>','',text)
            self.assertEqual(count,audit['print_image_count'])
            for change in reversed(audit['metadata_replacements']):
                self.assertEqual(text.count(change['after']),change['count'])
                text=text.replace(change['after'],change['before'])
            self.assertEqual(text.count(proof['final_footer']),1)
            text=text.replace(proof['final_footer'],proof['old_footer'],1)
            self.assertEqual(r.sha(text.encode()),audit['independently_reviewed_sha256'])

    def test_b_preview_payloads_remain_exactly_seven_and_v1(self):
        outputs = preview.output_payloads(ROOT)
        self.assertEqual(len(outputs), 7)
        for record, raw in self.original:
            self.assertEqual(outputs[f'{preview.BASE}/{record["paper_id"]}/first-pass.html'], raw)
            self.assertEqual(record['version'], 'v1')
            self.assertEqual(record['review_status'], 'preview_pending')
            self.assertNotEqual(raw, self.sources[record['paper_id']][1])


if __name__ == '__main__':
    unittest.main()
