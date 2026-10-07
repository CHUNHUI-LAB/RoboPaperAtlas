import subprocess
import unittest
from pathlib import Path
class FaithfulTreeCanvasTests(unittest.TestCase):
    def test_actual_source_and_dom_contracts(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/test_faithful_tree_canvas.cjs'], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
