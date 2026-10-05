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

    def test_previous_seven_sources_are_unchanged(self):
        canonical = json.dumps(self.pack['records'][:7], ensure_ascii=False,
                               sort_keys=True, separators=(',', ':'))
        self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(),
                         '97a136ccc742cc3e7eb0a6e8fee966275ff979216c6e58b58b2aa4cd0c50dee8')

    def test_source_identity_scope_and_cross_venue_references(self):
        self.assertEqual(len(self.records), 19)
        venues = {v['id'] for v in self.data['venues']}
        new = self.pack['records'][3:7]
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
        self.assertEqual(len(notes), 8)
        for note in notes:
            self.assertIn('编辑归纳', note['text'])
            self.assertGreaterEqual(len(note['source_record_ids']), 2)
            self.assertTrue(set(note['source_record_ids']) <= self.records.keys())
        script = (ROOT / 'submit-preview/app.js').read_text()
        self.assertIn('不是原作者共同结论或官方要求', script)

    def test_expansion_keeps_unknown_dates_and_record_level_summaries(self):
        self.assertEqual(len(self.pack['overview']['records']), 19)
        new = self.pack['records'][7:14]
        self.assertEqual(len(new), 7)
        self.assertEqual(len({r['source_url'] for r in self.pack['records']}), 19)
        for record in new:
            self.assertEqual(record['checked_at'], '2026-10-02')
            self.assertTrue(all(m.startswith('编辑启发：') for m in record['methods']))
        jfr = self.records['scirev-jfr-three-author-reports']
        self.assertIsNone(jfr['year'])
        self.assertIsNone(jfr['published_date'])
        self.assertEqual(len(jfr['cases']), 3)
        self.assertIn('作者独立性也无法确认', jfr['verification_limit'])
        self.assertIn('条数不等于独立作者', self.pack['overview']['evidence_note'])

    def test_corl_commenters_and_later_acceptance_remain_separate(self):
        corl = self.records['reddit-corl-2024-rebuttal-separated-cases']
        self.assertIn('没有说清录用渠道', corl['body_summary'])
        rejected = next(c for c in corl['comments'] if 'AddendumCold9417' in c['role'])
        self.assertIn('最终 CoRL 拒稿', rejected['summary'])
        followup = corl['comments'][-1]
        self.assertIn('没有明确最终渠道与日期', followup['summary'])
        self.assertTrue(followup['source_url'].endswith('/p1wfy0b/'))
        for rid in ('reddit-corl-2024-rebuttal-separated-cases',
                    'reddit-rss-2026-reviews-and-rebuttal', 'reddit-icra-2026-new-and-transfer'):
            self.assertIn('oz_zey', ' '.join(self.records[rid]['cautions']))

    def test_workshop_and_state_dates_cannot_be_promoted_to_stronger_claims(self):
        workshop = self.records['biradar-neurips-to-rss-workshop-2024']
        self.assertEqual(workshop['venue_scope'], 'workshop_not_main_conference')
        self.assertIsNone(workshop['published_date'])
        self.assertIn('这不是 RSS 主会录用', workshop['body_summary'])
        synopsis = next(s for s in self.pack['overview']['records'] if s['record_id'] == workshop['id'])
        self.assertIn('不是 RSS 主会接收', synopsis['preview_boundary'])
        self.assertEqual(len(workshop['supporting_sources']), 3)
        ijrr = self.records['ijrr-starscream-timeline-2026']
        self.assertEqual(len(ijrr['timeline']), 6)
        self.assertIn('未明确修回提交日', ijrr['timeline'][2]['event'])
        self.assertNotIn('2026-01-25 交回', ijrr['body_summary'])
        self.assertNotIn('sadeghi-corl-2018-review-count', self.records)

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
        # Resolving the closed initial submission does not resolve final-paper rules.
        self.assertEqual(edition['status'], 'reviewing')
        full = next(d for d in edition['deadlines'] if d['kind'] == 'full_paper')
        self.assertEqual(full['status'], 'verified')
        self.assertLess(full['date'], edition['checked_at'])
        self.assertEqual((full['date'], full['time'], full['timezone_label']),
                         ('2026-09-16', '23:59', 'PST'))
        for key in ('utc_offset', 'timezone_iana', 'utc_datetime'):
            self.assertIsNone(full[key])
        self.assertIn('maintenance-icra27-extension-20260916', full['source_ids'])
        self.assertFalse(any(d['kind'] == 'registration' for d in edition['deadlines']))
        for phrase in ('2025-03-06', '2027-02-06', '待定'):
            self.assertIn(phrase, ' '.join(edition['notes']))
        self.assertFalse(any(d['kind'] == 'camera_ready' for d in edition['deadlines']))


if __name__ == '__main__':
    unittest.main()
