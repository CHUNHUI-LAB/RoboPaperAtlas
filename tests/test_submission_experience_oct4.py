"""Strict regression and source boundaries for the October 4 experience append."""
import copy
import json
from pathlib import Path
import unittest

from submission_experience_history import (
    OCT4_IDS, OCT4_SYNTHESIS_IDS, PRE_APPEND_DATA_SHA256,
    canonical_sha256, project_before_oct4_experience_append,
)

ROOT = Path(__file__).resolve().parents[1]


class SubmissionExperienceOctober4Tests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'submit-preview/data/venues.json').read_text())
        self.pack = self.data['experiences']
        self.records = {r['id']: r for r in self.pack['records']}

    def assert_exact_preservation(self, data):
        restored = project_before_oct4_experience_append(data)
        # Complete unchanged ebd2e457 data, including all non-experience fields.
        self.assertEqual(canonical_sha256(restored), PRE_APPEND_DATA_SHA256)
        return restored

    def test_full_snapshot_reconstructs_without_mutating_candidate(self):
        before = copy.deepcopy(self.data)
        restored = self.assert_exact_preservation(self.data)
        self.assertEqual(self.data, before)
        self.assertEqual(len(restored['experiences']['records']), 14)
        self.assertEqual(len(restored['experiences']['overview']['records']), 14)
        self.assertEqual(len(restored['experiences']['editorial_synthesis']), 6)
        self.assertEqual(restored['experiences']['overview']['updated_at'], '2026-10-02')

    def test_projection_rejects_old_new_and_unrelated_mutations(self):
        mutations = {
            'old record changed': lambda d: d['experiences']['records'][0].update(body_summary='changed'),
            'old date refreshed': lambda d: d['experiences']['records'][7].update(checked_at='2026-10-04'),
            'old synopsis changed': lambda d: d['experiences']['overview']['records'][0].update(takeaway='changed'),
            'old synthesis changed': lambda d: d['experiences']['editorial_synthesis'][0].update(text='changed'),
            'old record removed': lambda d: d['experiences']['records'].pop(0),
            'new record removed': lambda d: d['experiences']['records'].pop(),
            'new record changed': lambda d: d['experiences']['records'][14].update(reading_scope='watched every video'),
            'new record duplicated': lambda d: d['experiences']['records'].append(copy.deepcopy(d['experiences']['records'][14])),
            'new records reordered': lambda d: d['experiences']['records'].__setitem__(slice(14, None), list(reversed(d['experiences']['records'][14:]))),
            'new synopsis changed': lambda d: d['experiences']['overview']['records'][14].update(takeaway='changed'),
            'new synopsis removed': lambda d: d['experiences']['overview']['records'].pop(),
            'new synthesis changed': lambda d: d['experiences']['editorial_synthesis'][-1].update(text='changed'),
            'new synthesis removed': lambda d: d['experiences']['editorial_synthesis'].pop(),
            'overview date rewritten': lambda d: d['experiences']['overview'].update(updated_at='2026-10-05'),
            'overview evidence changed': lambda d: d['experiences']['overview'].update(evidence_note='official requirements'),
            'official check changed': lambda d: d['experiences']['official_checks'][0].update(status='verified'),
            'experience envelope changed': lambda d: d['experiences'].update(checked_at='2026-10-04'),
            'history lost': lambda d: d['maintenance_history'][0]['preserved_boundaries'].pop(),
            'prior source rewritten': lambda d: next(h for h in d['maintenance_history'] if h['checked_at'] == '2026-10-04')['prior_records']['vp-ral-home'].update(claim_supported='changed'),
            'policy changed': lambda d: d['editions'][0]['notes'].append('new rule'),
            'source removed': lambda d: d['sources'].pop(),
            'publication removed': lambda d: d['publications'].pop(),
        }
        for name, mutate in mutations.items():
            with self.subTest(mutation=name):
                changed = copy.deepcopy(self.data)
                mutate(changed)
                self.assertNotEqual(changed, self.data, 'Ineffective negative control')
                with self.assertRaises(AssertionError):
                    self.assert_exact_preservation(changed)

    def test_new_batch_has_exact_identity_dates_and_editorial_scope(self):
        self.assertEqual(tuple(r['id'] for r in self.pack['records'][14:]), OCT4_IDS)
        self.assertEqual(tuple(s['id'] for s in self.pack['editorial_synthesis'][6:]), OCT4_SYNTHESIS_IDS)
        self.assertEqual(self.pack['overview']['updated_at'], '2026-10-04')
        for record in self.pack['records'][14:]:
            self.assertEqual(record['checked_at'], '2026-10-04')
            self.assertTrue(all(m.startswith('编辑启发：') for m in record['methods']))
            self.assertTrue(record['reading_scope'])
            self.assertTrue(record['verification_limit'])
            self.assertTrue(record['comment_scope_note'])
            self.assertTrue(record['cautions'])
            synopsis = next(s for s in self.pack['overview']['records'] if s['record_id'] == record['id'])
            self.assertEqual(synopsis['evidence_kind'], 'editorial_synthesis')
        for note in self.pack['editorial_synthesis'][6:]:
            self.assertTrue(note['text'].startswith('编辑归纳：'))
            self.assertTrue(set(note['source_record_ids']) <= set(OCT4_IDS))

    def test_teaching_source_reading_and_dates_are_bounded(self):
        tokekar = self.records[OCT4_IDS[0]]
        for phrase in ('45页PDF全部可提取文字', '查看第43页图像', '未观看讲座录像'):
            self.assertIn(phrase, tokekar['reading_scope'])
        self.assertEqual(tokekar['published_date_note'], '此为作者公开分享讲义的日期；PDF创建日期亦为同日，未核定讲座举行日或最早公开日期。')
        self.assertIn('旧截稿、页数', ' '.join(tokekar['cautions']))
        self.assertIn('不作为现行规则', ' '.join(tokekar['cautions']))
        milford = self.records[OCT4_IDS[1]]
        self.assertEqual((milford['year'], milford['published_date']), (2024, '2025-01-24'))
        self.assertIn('Full Video Notes', milford['reading_scope'])
        self.assertIn('未观看视频', milford['reading_scope'])
        self.assertIn('不是新增独立作者或录用样本', ' '.join(milford['cautions']))

    def test_republication_and_anonymous_outcome_limits_are_retained(self):
        zhang = self.records[OCT4_IDS[2]]
        self.assertEqual(zhang['source_author'], 'ChenJacker（Robook署名）')
        synopsis = next(s for s in self.pack['overview']['records'] if s['record_id'] == zhang['id'])
        self.assertEqual(synopsis['preview_boundary'], '适合检查指标与权衡；以Robook署名中文版本为依据，非投稿标准。')
        self.assertEqual(zhang['source_url'], 'https://www.robook.org/blog/zcj')
        self.assertIn('知乎中文原页未核读', zhang['reading_scope'])
        self.assertIn('不把', ' '.join(zhang['cautions']))
        reddit = self.records[OCT4_IDS[3]]
        self.assertEqual(reddit['source_type'], 'forum_anecdote')
        self.assertIsNone(reddit['published_date'])
        self.assertIsNone(reddit['year'])
        self.assertTrue(all(c['date'] == '绝对日期未核定' for c in reddit['comments']))
        self.assertIn('首批可见8条评论', reddit['reading_scope'])
        self.assertIn('未见后来改投或录用结果', reddit['verification_limit'])
        self.assertIn('发表年份与绝对日期未核定', reddit['published_date_note'])
        self.assertIn('页脚归档导航不作为帖子时间戳', reddit['published_date_note'])
        ye = self.records[OCT4_IDS[4]]
        self.assertEqual(ye['source_author'], '叶小飞（量子位编者按指认为原文作者；页面署名：丰色）')
        self.assertEqual(ye['source_url'], 'https://www.qbitai.com/2023/10/92009.html')
        self.assertIn('授权转载', ye['source_label'])
        self.assertIn('未读取知乎原页或评论', ye['reading_scope'])
        for phrase in ('排除对评审恶意的指控', '不把超长工作和短睡眠当成研究建议', '不按独立作者累加'):
            self.assertIn(phrase, ' '.join(ye['cautions']))


if __name__ == '__main__':
    unittest.main()
