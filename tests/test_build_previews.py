"""The opt-in wrapper must build once before appending its isolated route."""
import subprocess
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import build_previews


class BuildPreviewsTests(unittest.TestCase):
    def test_validates_then_builds_once_then_appends(self):
        order = []
        with patch.object(build_previews, 'safe_target', side_effect=lambda root, target: order.append('target') or target), patch.object(build_previews, 'validate_source', side_effect=lambda root: order.append('source')), patch.object(build_previews.subprocess, 'run', side_effect=lambda *a, **kw: order.append('build')) as run, patch.object(build_previews, 'write_preview', side_effect=lambda *a: order.append('preview')) as write:
            build_previews.main(['--output', 'dist-test'])
        self.assertEqual(order, ['target', 'source', 'build', 'preview'])
        run.assert_called_once_with([sys.executable, str(build_previews.ROOT / 'scripts/build.py'), '--output', 'dist-test'], check=True)
        write.assert_called_once_with(build_previews.ROOT, build_previews.ROOT / 'dist-test')

    def test_failed_base_build_does_not_append(self):
        with patch.object(build_previews, 'safe_target'), patch.object(build_previews, 'validate_source'), patch.object(build_previews.subprocess, 'run', side_effect=subprocess.CalledProcessError(1, 'build')), patch.object(build_previews, 'write_preview') as write:
            with self.assertRaises(subprocess.CalledProcessError):
                build_previews.main([])
        write.assert_not_called()


if __name__ == '__main__':
    unittest.main()
