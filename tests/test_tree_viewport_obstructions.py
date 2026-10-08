import subprocess
import unittest
from pathlib import Path

class TreeViewportObstructionTests(unittest.TestCase):
    def test_observed_viewport_and_focus_regressions(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/test_tree_viewport_obstructions.cjs'], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
