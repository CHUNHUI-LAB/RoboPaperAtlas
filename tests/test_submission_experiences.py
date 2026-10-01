"""Evidence boundaries for the independently read submission-source expansion."""
import hashlib
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class SubmissionExperienceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'submit-preview/data/venues.json').read_text())
        cls.pack = cls.data['experiences']
        cls.records = {r['id']: r for r in cls.pack['records']}

    def test_original_ral_records_are_unchanged(self):
        original = self.pack['records'][:3]
        canonical = json.dumps(original, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),
                         '7ce493a0f54c76835e145ef9498a8630b215e81d01ccd645c46c0c00ef38f399')
        self.assertEqual({r['source_type'] for r in original}, {'first_person_self_report'})

    def test_source_identity_scope_and_cross_venue_references(self):
        self.assertEqual(len(self.records), 7)
        venues = {v['id'] for v in self.data['venues']}
        new = self.pack['records'][3:]
        self.assertEqual([r['source_type'] for r in new],
                         ['author_advice', 'author_advice', 'reviewer_self_report', 'forum_anecdote'])
        for record in new:
            self.assertTrue(record['source_url'].startswith('https://'))
            self.assertEqual(record['checked_at'], '2026-10-01')
            self.assertIn(record['venue_id'], record['venue_ids'])
            self.assertTrue(set(record['venue_ids']) <= venues)
            for key in ('source_label', 'evidence_label', 'reading_scope', 'verification_limit',
                        'body_summary', 'methods', 'cautions'):
                self.assertTrue(record[key])
        self.assertIn('未观看视频', self.records['milford-robotics-paper-structure-2023']['reading_scope'])
        self.assertIn('2026 年 7 月停止更新', self.records['seita-reviewing-load-2022']['reading_scope'])
        reddit = self.records['reddit-icra-iros-transfer-1u91k6s']
        self.assertIsNone(reddit['year'])
        self.assertIsNone(reddit['published_date'])
        self.assertIn('绝对日期未核定', reddit['published_date_note'])
        self.assertEqual(len(reddit['comments']), 3)

    def test_editorial_synthesis_has_provenance_and_no_fabricated_consensus(self):
        notes = self.pack['editorial_synthesis']
        self.assertEqual(len(notes), 3)
        for note in notes:
            self.assertIn('编辑归纳', note['text'])
            self.assertGreaterEqual(len(note['source_record_ids']), 2)
            self.assertTrue(set(note['source_record_ids']) <= self.records.keys())
        script = (ROOT / 'submit-preview/app.js').read_text()
        self.assertIn('不是原作者共同结论或官方要求', script)

    def test_official_length_conflict_does_not_create_deadline_or_policy(self):
        checks = self.pack['official_checks']
        self.assertEqual(len(checks), 1)
        check = checks[0]
        self.assertEqual(check['status'], 'unresolved_final_instructions')
        self.assertEqual(check['venue_ids'], ['icra'])
        self.assertIn('完整论文最多 8 页，包含参考文献', check['summary'])
        for phrase in ('ICRA 2025', '2025-03-06', '6+n', '不把', '不据此设置提醒'):
            self.assertIn(phrase, check['conflict'])
        self.assertEqual(len(check['links']), 2)
        self.assertNotIn('deadlines', check)
        edition = next(e for e in self.data['editions'] if e['id'] == 'icra-2027')
        self.assertEqual(edition['status'], 'needs_confirmation')
        self.assertEqual(edition['deadlines'][0]['status'], 'conflicted')
        self.assertFalse(any(d['kind'] == 'camera_ready' for d in edition['deadlines']))


if __name__ == '__main__':
    unittest.main()
