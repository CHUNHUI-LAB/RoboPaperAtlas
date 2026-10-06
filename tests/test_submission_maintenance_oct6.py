"""NeurIPS post-decision supplement preserves every earlier source and status."""
import copy
import json
from pathlib import Path
import unittest
from submission_maintenance_oct6_history import project_before_oct6_maintenance

ROOT = Path(__file__).resolve().parents[1]


class October6MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'submit-preview/data/venues.json').read_text())

    def test_complete_baseline_reconstruction_and_no_input_mutation(self):
        before = copy.deepcopy(self.data)
        restored = project_before_oct6_maintenance(self.data)
        self.assertEqual(before, self.data)
        self.assertEqual(restored['checked_at'], '2026-10-04')
        self.assertEqual(restored['experiences'], self.data['experiences'])

    def test_registration_notification_and_final_deadline_are_not_conflated(self):
        edition = next(e for e in self.data['editions'] if e['id'] == 'neurips-2026')
        self.assertEqual(edition['status'], 'post_decision')
        self.assertEqual([d['kind'] for d in edition['deadlines']], ['abstract', 'full_paper', 'decision'])
        decision = edition['deadlines'][-1]
        self.assertEqual((decision['date'], decision['timezone_label'], decision['time'], decision['precision']),
                         ('2026-09-24', 'AoE', None, 'date'))
        notes = ' '.join(edition['notes'])
        for phrase in ('2026-10-06 17:00 UTC', '2026-10-30 AoE', 'Virtual Only Pass', '未给出具体终稿截止', '未下载或编译模板'):
            self.assertIn(phrase, notes)
        old = project_before_oct6_maintenance(self.data)
        old_edition = next(e for e in old['editions'] if e['id'] == edition['id'])
        self.assertEqual(edition['deadlines'][:2], old_edition['deadlines'])
        self.assertEqual(edition['templates'], old_edition['templates'])

    def test_strict_inverse_rejects_new_and_historical_mutations(self):
        mutations = [
            lambda d: d['maintenance_history'].pop(),
            lambda d: d['sources'].pop(),
            lambda d: d['sources'][-1].update(claim_supported='rewritten'),
            lambda d: d['experiences']['records'].pop(),
            lambda d: d['publications'].pop(),
            lambda d: next(e for e in d['editions'] if e['id'] == 'neurips-2026')['notes'].pop(),
            lambda d: d['maintenance_history'][-1]['prior_records']['neurips-2026'].update(status='open'),
        ]
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                changed = copy.deepcopy(self.data)
                mutate(changed)
                with self.assertRaises(AssertionError):
                    project_before_oct6_maintenance(changed)
