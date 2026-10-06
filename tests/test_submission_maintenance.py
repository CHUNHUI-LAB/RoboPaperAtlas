"""Exact preservation and stage boundaries for the 2026-10-04 public-source update."""
import copy
import hashlib
import json
from pathlib import Path
import unittest

from submission_experience_history import project_before_oct4_experience_append

ROOT = Path(__file__).resolve().parents[1]
UPDATE = '2026-10-04'
EXTENSION = 'maintenance-icra27-extension-20260916'
BASELINE_SHA256 = 'b0fc98df6596430a135c7930d15b4c627e2b0c9e444641aefcac0a57acc2ae2b'


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


class SubmissionMaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'submit-preview/data/venues.json').read_text())
        self.update = next(h for h in self.data['maintenance_history'] if h['checked_at'] == UPDATE)
        self.editions = {e['id']: e for e in self.data['editions']}
        self.prior = self.update['prior_records']

    def assert_baseline_reconstructs(self, data):
        restored = project_before_oct4_experience_append(data)
        history = restored['maintenance_history']
        self.assertEqual(history[-1]['checked_at'], UPDATE)
        update = history.pop()
        self.assertEqual(update['previous_snapshot'], history[-1]['checked_at'])
        prior = update['prior_records']
        self.assertEqual(set(prior), {'icra-2027', 'ral-policy-20261001',
                                     'vp-ral-home', 'venue-profile-ral'})
        for key in ('icra-2027', 'ral-policy-20261001'):
            index = next(i for i, e in enumerate(restored['editions']) if e['id'] == key)
            restored['editions'][index] = prior[key]
        source_index = next(i for i, s in enumerate(restored['sources']) if s['id'] == 'vp-ral-home')
        restored['sources'][source_index] = prior['vp-ral-home']
        self.assertEqual(sum(s['id'] == EXTENSION for s in restored['sources']), 1)
        restored['sources'] = [s for s in restored['sources'] if s['id'] != EXTENSION]
        profile_index = next(i for i, p in enumerate(restored['venue_profiles']['profiles']) if p['venue_id'] == 'ral')
        restored['venue_profiles']['profiles'][profile_index] = prior['venue-profile-ral']
        restored['checked_at'] = update['previous_snapshot']
        # Hash of the complete venues.json object at main a0feff3e. The strict
        # experience projection first verifies this later append before undoing
        # it; this original hash still covers every prior field and date.
        self.assertEqual(canonical_sha256(restored), BASELINE_SHA256)

    def test_complete_prior_snapshot_is_reconstructable(self):
        self.assert_baseline_reconstructs(self.data)

    def test_preservation_rejects_history_and_unrelated_data_loss(self):
        mutations = [
            lambda d: d['maintenance_history'][0]['preserved_boundaries'].pop(),
            lambda d: next(h for h in d['maintenance_history'] if h['checked_at'] == '2026-10-04')['prior_records']['vp-ral-home'].update(claim_supported='rewritten'),
            lambda d: d['experiences']['records'].pop(),
            lambda d: d['experiences']['overview']['records'][0].update(takeaway='rewritten'),
            lambda d: d['publications'].pop(),
            lambda d: d['editions'][1]['notes'].append('unrelated change'),
        ]
        for mutate in mutations:
            data = copy.deepcopy(self.data)
            mutate(data)
            with self.assertRaises(AssertionError):
                self.assert_baseline_reconstructs(data)

    def test_icra_resolution_is_limited_to_closed_initial_submission(self):
        current = copy.deepcopy(self.editions['icra-2027'])
        previous = self.prior['icra-2027']
        self.assertEqual(current['status'], 'reviewing')
        self.assertEqual(previous['status'], 'needs_confirmation')
        full = next(d for d in current['deadlines'] if d['kind'] == 'full_paper')
        before = next(d for d in previous['deadlines'] if d['kind'] == 'full_paper')
        self.assertEqual(full['status'], 'verified')
        self.assertEqual(before['status'], 'conflicted')
        self.assertEqual((full['date'], full['time'], full['timezone_label']),
                         ('2026-09-16', '23:59', 'PST'))
        self.assertLess(full['date'], current['checked_at'])
        self.assertEqual(full['checked_at'], UPDATE)
        self.assertEqual(full['source_ids'], ['icra27-cfp', EXTENSION, 'maintenance-icra27-cfp-details'])
        for key in ('utc_offset', 'timezone_iana', 'utc_datetime'):
            self.assertIsNone(full[key])
        source = next(s for s in self.data['sources'] if s['id'] == EXTENSION)
        self.assertEqual(source['url'], 'https://2027.ieee-icra.org/announcements/call-for-papers-submission-deadline-extended/')
        self.assertEqual(source['authority'], 'official')
        self.assertEqual(source['access_status'], 'source_text_observed')
        self.assertEqual(source['checked_at'], UPDATE)
        self.assertFalse(any(d['kind'] in {'camera_ready', 'registration'} for d in current['deadlines']))
        for phrase in ('2025-03-06', '2027-02-06', '待定'):
            self.assertIn(phrase, ' '.join(current['notes']))
        # All other deadline fields, notes and template evidence are unchanged.
        for key in ('status', 'source_ids', 'checked_at'):
            full[key] = before[key]
            current[key] = previous[key]
        current['notes'][0] = previous['notes'][0]
        self.assertEqual(current, previous)

    def test_ral_transfer_windows_never_become_submission_deadlines(self):
        ral = copy.deepcopy(self.editions['ral-policy-20261001'])
        previous = self.prior['ral-policy-20261001']
        self.assertEqual(ral['submission_mode'], 'rolling_verified')
        self.assertIsNone(ral['edition_year'])
        self.assertEqual(ral['deadlines'], [])
        self.assertEqual(self.editions['iros-2027']['status'], 'source_unresolved')
        self.assertEqual(self.editions['iros-2027']['deadlines'], [])
        note = ral['notes'].pop()
        for phrase in ('已录用非综述', 'ICRA 2027', '2026-03-01', '2026-12-31',
                       'IROS 2027', '2026-08-01', '2027-04-30', '270 天', '一个会议',
                       '不是 RA-L 常规投稿或会议首轮投稿截止', '时刻或时区', '加快或延迟评审'):
            self.assertIn(phrase, note)
        self.assertEqual(ral['source_ids'], previous['source_ids'] + ['vp-ral-home'])
        self.assertEqual(ral['checked_at'], UPDATE)
        ral['source_ids'] = previous['source_ids']
        ral['checked_at'] = previous['checked_at']
        self.assertEqual(ral, previous)

    def test_ral_profile_adds_eligibility_without_rewriting_other_sections(self):
        profile = copy.deepcopy(next(p for p in self.data['venue_profiles']['profiles'] if p['venue_id'] == 'ral'))
        prior = self.prior['venue-profile-ral']
        boundary = next(s for s in profile['sections'] if s['key'] == 'boundary')
        original = next(s for s in prior['sections'] if s['key'] == 'boundary')
        self.assertTrue(boundary['text'].startswith(original['text']))
        for phrase in ('已录用', '非综述', '270 天', '一个会议', '不是 RA-L 或会议的初投截止'):
            self.assertIn(phrase, boundary['text'])
        self.assertEqual(boundary['evidence_kind'], 'official')
        self.assertIn('vp-ral-home', boundary['source_ids'])
        self.assertIn('仅补核会议展示资格', profile['reference_note'])
        self.assertEqual(profile['checked_at'], UPDATE)
        boundary['text'] = original['text']
        profile['checked_at'] = prior['checked_at']
        profile['reference_note'] = prior['reference_note']
        self.assertEqual(profile, prior)


if __name__ == '__main__':
    unittest.main()
