"""Source-backed profile coverage and additive schema boundaries."""
import copy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from submission_profiles import validate_submission_profiles, validate_experience_overview


class SubmissionProfileTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT/'submit-preview/data/venues.json').read_text())

    def test_complete_source_backed_profiles_and_experiences(self):
        self.assertEqual(validate_submission_profiles(self.data), 15)
        self.assertEqual(validate_experience_overview(self.data), 14)
        self.assertEqual(len(self.data['experiences']['editorial_synthesis']), 6)

    def test_legacy_envelope_is_explicitly_compatible_but_not_publishable(self):
        self.data.pop('venue_profiles')
        self.assertEqual(validate_submission_profiles(self.data, require_profiles=False), 0)
        with self.assertRaisesRegex(ValueError, 'Missing venue profiles'):
            validate_submission_profiles(self.data)

    def test_missing_duplicate_historical_and_unscoped_profiles_fail(self):
        for change in ('missing', 'duplicate', 'historical', 'field'):
            d = copy.deepcopy(self.data)
            profiles = d['venue_profiles']['profiles']
            if change == 'missing': profiles.pop()
            if change == 'duplicate': profiles[-1] = copy.deepcopy(profiles[0])
            if change == 'historical': profiles[-1]['venue_id'] = 'aaai'
            if change == 'field': profiles[0]['private_notes'] = 'not public'
            with self.subTest(change=change), self.assertRaises(ValueError):
                validate_submission_profiles(d)

    def test_sources_styles_dates_markup_and_section_keys_are_checked(self):
        mutations = [
            lambda p: p.update(checked_at='2026-02-30'),
            lambda p: p.update(teaser='<script>alert(1)</script>'),
            lambda p: p.update(teaser_source_ids=['unknown']),
            lambda p: p['sections'][2].update(evidence_kind='official'),
            lambda p: p['sections'][2].update(key='themes'),
            lambda p: p['sections'][2].update(source_ids=[]),
        ]
        for mutate in mutations:
            d = copy.deepcopy(self.data)
            mutate(d['venue_profiles']['profiles'][0])
            with self.assertRaises(ValueError): validate_submission_profiles(d)
        d = copy.deepcopy(self.data)
        sid = d['venue_profiles']['profiles'][0]['teaser_source_ids'][0]
        next(s for s in d['sources'] if s['id'] == sid)['url'] = 'https://localhost/private'
        with self.assertRaises(ValueError): validate_submission_profiles(d)

    def test_each_experience_summary_is_editorial_and_cannot_cross_source_identity(self):
        self.data['experiences']['overview']['records'][0]['record_id'] = 'unknown'
        with self.assertRaises(ValueError): validate_experience_overview(self.data)

    def test_experience_evidence_checks_optional_urls_dates_and_markup(self):
        mutations = [
            lambda rs: rs[-1]['supporting_sources'][0].update(url='javascript:alert(1)'),
            lambda rs: rs[-1]['supporting_sources'][0].update(role='<script>bad</script>'),
            lambda rs: rs[7]['timeline'][0].update(date='2025-02-30'),
            lambda rs: rs[-2]['cases'][0].update(sequence='<img src=x>'),
            lambda rs: rs[8]['comments'][-1].update(source_url='https://localhost/private'),
            lambda rs: rs[-1].update(id=rs[0]['id']),
            lambda rs: rs[-1].update(source_url=rs[0]['source_url']),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data['experiences']['records'])
            with self.assertRaises(ValueError):
                validate_experience_overview(data)

    def test_failed_fetch_is_never_policy_or_style_evidence(self):
        source = next(s for s in self.data['sources'] if s.get('access_status') == 'fetch_failed')
        profile = next(p for p in self.data['venue_profiles']['profiles'] if p['venue_id'] == 'jfr')
        profile['teaser_source_ids'].append(source['id'])
        with self.assertRaisesRegex(ValueError, 'Failed fetch'):
            validate_submission_profiles(self.data)

    def test_official_and_author_primary_evidence_keep_their_identity(self):
        kinds = {s['kind'] for s in self.data['sources'] if s.get('authority') == 'primary'}
        self.assertIn('author_project', kinds)
        self.assertIn('publisher_deposited_crossref', kinds)
        self.assertEqual(validate_submission_profiles(self.data), 15)

    def test_official_maintenance_preserves_unresolved_deadline_boundaries(self):
        self.assertEqual(self.data['checked_at'], self.data['maintenance_history'][-1]['checked_at'])
        history = self.data['maintenance_history']
        self.assertEqual(history[0]['previous_snapshot'], '2026-10-01')
        for previous, current in zip(history, history[1:]):
            self.assertEqual(current['previous_snapshot'], previous['checked_at'])
            self.assertLess(previous['checked_at'], current['checked_at'])
        editions = {e['id']: e for e in self.data['editions']}
        icra = editions['icra-2027']
        self.assertEqual(icra['status'], 'reviewing')
        self.assertEqual(next(d for d in icra['deadlines'] if d['kind'] == 'full_paper')['status'], 'verified')
        self.assertFalse(any(d['kind'] in {'camera_ready', 'registration'} for d in icra['deadlines']))
        self.assertIn('待定', ' '.join(icra['notes']))
        prior = history[-1]['prior_records']['icra-2027']
        self.assertEqual(prior['status'], 'needs_confirmation')
        self.assertEqual(next(d for d in prior['deadlines'] if d['kind'] == 'full_paper')['status'], 'conflicted')
        self.assertEqual(editions['iros-2027']['status'], 'source_unresolved')
        self.assertFalse(editions['iros-2027']['deadlines'])

    def test_special_issue_notices_do_not_become_regular_journal_deadlines(self):
        editions = {e['id']: e for e in self.data['editions']}
        notices = []
        for eid in ('ral-policy-20261001', 'auro-policy-20261001'):
            e = editions[eid]
            self.assertIsNone(e['edition_year'])
            self.assertFalse(e['deadlines'])
            notices.extend(e['special_issue_notices'])
        self.assertEqual(len(notices), 5)
        for notice in notices:
            self.assertFalse(notice['normalized_as_regular_deadline'])
            for item in notice['dates']:
                self.assertIsNone(item['time'])
                self.assertIsNone(item['timezone'])
        self.assertEqual(notices[0]['status'], 'announced_not_yet_accepting_per_timeline')

    def test_template_inspection_does_not_claim_rendering_or_future_editions(self):
        editions = {e['id']: e for e in self.data['editions']}
        corl = editions['corl-2026']
        self.assertEqual(corl['status'], 'post_decision')
        self.assertEqual({t['inspection']['role'] for t in corl['templates']}, {'initial_submission', 'camera_ready'})
        for eid in ('corl-2026', 'rss-2027', 'iclr-2027'):
            for template in editions[eid]['templates']:
                self.assertEqual(len(template['inspection']['sha256']), 64)
                self.assertIn('No compilation', template['inspection']['scope'])
        self.assertNotIn('corl-2027', editions)
        self.assertEqual(editions['cvpr-2027']['templates'][0]['status'], 'broken_404')

    def test_iclr_discussion_stays_distinct_from_private_reviewer_work(self):
        e = next(e for e in self.data['editions'] if e['id'] == 'iclr-2027')
        decision = next(d for d in e['deadlines'] if d['kind'] == 'decision')
        self.assertEqual((decision['timezone_label'], decision['utc_offset']), ('AoE', '-12:00'))
        self.assertEqual(decision['precision'], 'date')
        self.assertTrue(any(d['kind'] == 'reviews' and d['date'] == '2026-11-05' for d in e['deadlines']))
        self.assertFalse(any(d['date'] == '2026-11-19' for d in e['deadlines']))
        self.assertTrue(any('不是作者行动截止' in note for note in e['notes']))


if __name__ == '__main__': unittest.main()
