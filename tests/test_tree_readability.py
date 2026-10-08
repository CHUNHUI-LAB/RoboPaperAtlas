import subprocess
import unittest
from pathlib import Path

class TreeReadabilityTests(unittest.TestCase):
    def test_complete_labels_and_clear_ancestry(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/test_tree_readability.cjs'], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
