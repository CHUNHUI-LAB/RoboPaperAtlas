"""The T-RO append preserves all prior public evidence and date semantics."""
import copy
import json
from pathlib import Path
import unittest
from submission_maintenance_oct8_history import project_before_oct8_maintenance
from submission_maintenance_oct6_history import project_before_oct6_maintenance

ROOT = Path(__file__).resolve().parents[1]


class October8MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'submit-preview/data/venues.json').read_text())

    def test_reversible_without_mutation_and_old_snapshot_still_supported(self):
        original = copy.deepcopy(self.data)
        old = project_before_oct8_maintenance(self.data)
        self.assertEqual(self.data, original)
        self.assertEqual(project_before_oct8_maintenance(old), old)
        self.assertEqual(project_before_oct6_maintenance(old), project_before_oct6_maintenance(self.data))
        for key in ('experiences', 'publications', 'presentations', 'venue_profiles'):
            self.assertEqual(self.data[key], old[key])

    def test_only_reviewed_tro_append(self):
        old = project_before_oct8_maintenance(self.data)
        edition = next(e for e in self.data['editions'] if e['id'] == 'tro-policy-20261001')
        prior = next(e for e in old['editions'] if e['id'] == edition['id'])
        self.assertEqual(edition['notes'][:-1], prior['notes'])
        self.assertEqual(edition['source_ids'][:-1], prior['source_ids'])
        self.assertEqual(edition['deadlines'], [])
        self.assertEqual(edition['checked_at'], prior['checked_at'])
        for phrase in ('270', 'communication items', '时区', '不是常规投稿截止', '一个月', '衔接未解释', '关键想法'):
            self.assertIn(phrase, edition['notes'][-1])

    def test_tampering_and_unknown_snapshots_fail_closed(self):
        mutations = [
            lambda d: d.update(checked_at='2026-10-09'),
            lambda d: d['sources'].pop(),
            lambda d: d['maintenance_history'].pop(),
            lambda d: d['sources'][-1].update(url='https://example.com/'),
            lambda d: d['experiences']['records'].pop(),
            lambda d: d['publications'].pop(),
            lambda d: d['editions'].reverse(),
            lambda d: next(e for e in d['editions'] if e['id'] == 'tro-policy-20261001')['notes'].pop(),
            lambda d: d['maintenance_history'][-1]['prior_records']['tro-policy-20261001'].update(status='open'),
            lambda d: next(h for h in d['maintenance_history'] if h['checked_at'] == '2026-10-06')['prior_records']['neurips-2026'].update(status='open'),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(self.data)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    project_before_oct8_maintenance(changed)
