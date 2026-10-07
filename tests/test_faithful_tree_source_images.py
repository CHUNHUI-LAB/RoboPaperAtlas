import subprocess
import unittest
from pathlib import Path
class FaithfulTreeSourceImageGate(unittest.TestCase):
    def test_original_image_bytes_are_present_and_exact(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run(['node', 'tests/test_faithful_tree_source_images.cjs'], cwd=root, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
