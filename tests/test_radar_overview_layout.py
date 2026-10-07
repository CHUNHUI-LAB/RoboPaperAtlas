"""Run persistent overview and bounded-focus regressions in normal Python discovery."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RadarOverviewLayoutTests(unittest.TestCase):
    def test_persistent_overview_and_responsive_focus(self):
        run = subprocess.run(
            ['node', str(ROOT / 'tests/test_radar_overview_layout.cjs')],
            capture_output=True, text=True, timeout=120)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        self.assertEqual(run.stdout.count('PASS '), 9, run.stdout)
