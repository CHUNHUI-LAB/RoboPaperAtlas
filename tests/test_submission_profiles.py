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
        self.assertEqual(validate_experience_overview(self.data), 7)
        self.assertEqual(len(self.data['experiences']['editorial_synthesis']), 3)

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

    def test_new_profile_dates_do_not_rewrite_deadline_snapshot(self):
        self.assertEqual(self.data['checked_at'], '2026-10-01')
        editions = {e['id']: e for e in self.data['editions']}
        self.assertEqual(editions['icra-2027']['status'], 'needs_confirmation')
        self.assertEqual(editions['icra-2027']['deadlines'][0]['status'], 'conflicted')
        self.assertEqual(editions['iros-2027']['status'], 'source_unresolved')
        self.assertFalse(editions['iros-2027']['deadlines'])


if __name__ == '__main__': unittest.main()
