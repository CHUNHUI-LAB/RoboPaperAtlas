"""Transport-only checks; actual Chrome pixels are produced in the PR job."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
import struct
import zlib
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('navigation_screenshots', Path(__file__).parents[1] / 'scripts/navigation_screenshots.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScreenshotChecks(unittest.TestCase):
    def test_context_paths_reject_mixed_ancestry_and_unreadable_links(self):
        import copy
        data = {'route': {'tree': 'c', 'node': 'pos:c:6dcc2ce43c02d908266f20'},
                'expectedIds': ['root-c', 'insight'], 'localIds': ['root-c', 'insight'],
                'localTrees': ['c', 'c'], 'globalIds': ['goal', 'scope'],
                'expectedGlobalIds': ['goal', 'scope'], 'globalSeparators': 0,
                'labels': ['全局入口', '挑战–思路树 · 当前路径'],
                'rows': [{'x': 20, 'y': 100, 'width': 900, 'height': 30}, {'x': 20, 'y': 134, 'width': 900, 'height': 30}],
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                'buttons': [{'uncovered': True, 'clipped': False, 'row': {'x': 20, 'y': 134, 'width': 900, 'height': 30}, 'rect': {'x': 90, 'y': 135, 'width': 200, 'height': 25}}]}
        MODULE.check_context_path(data)
        mutations = [lambda x: x['localIds'].insert(0, 'literature'),
                     lambda x: x['localTrees'].__setitem__(0, 'g'),
                     lambda x: x.__setitem__('globalSeparators', 1),
                     lambda x: x['rows'][1].__setitem__('y', 100),
                     lambda x: x['buttons'][0].__setitem__('uncovered', False),
                     lambda x: x['buttons'][0].__setitem__('clipped', True),
                     lambda x: x['rows'][1].__setitem__('y', 950),
                     lambda x: x['buttons'][0]['row'].__setitem__('width', 10)]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_context_path(bad)

    def test_cropped_root_and_low_contrast_are_rejected(self):
        viewport = {'x': 0, 'y': 0, 'width': 1440, 'height': 900}
        self.assertTrue(MODULE.rect_inside({'x': 10, 'y': 200, 'width': 350, 'height': 60}, viewport))
        self.assertFalse(MODULE.rect_inside({'x': 1200, 'y': 200, 'width': 350, 'height': 60}, viewport))
        self.assertFalse(MODULE.rect_inside({'x': 10, 'y': 870, 'width': 350, 'height': 60}, viewport))
        self.assertLess(MODULE.contrast_ratio([255, 255, 255], [234, 245, 240]), 4.5)
        self.assertGreater(MODULE.contrast_ratio([26, 52, 64], [234, 245, 240]), 4.5)

    def test_blank_png_rejected_and_nonblank_pixels_detected(self):
        def png(rows, width):
            def chunk(kind, data):
                return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
            return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, len(rows), 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows))) + chunk(b'IEND', b'')
        self.assertFalse(MODULE.png_has_visible_variation(png([bytes([255] * 90)] * 30, 30)))
        row = bytes(v for x in range(90) for v in ((x * 7) % 256, (x * 11) % 256, (x * 17) % 256))
        self.assertTrue(MODULE.png_has_visible_variation(png([row] * 90, 90)))

    def test_required_viewports(self):
        self.assertEqual(MODULE.VIEWPORTS, [(1440, 900), (1920, 1080)])

    def test_webdriver_envelope_and_loopback(self):
        driver = MODULE.Driver(12345)
        driver.session = 'test-session'
        with patch.object(MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"value":{"ok":true}}')) as opened:
            self.assertEqual(driver.js('return arguments[0]', 'value'), {'ok': True})
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url, 'http://127.0.0.1:12345/session/test-session/execute/sync')
        self.assertEqual(json.loads(request.data), {'script': 'return arguments[0]', 'args': ['value']})
        self.assertEqual(opened.call_args.kwargs['timeout'], 50)

    def test_webdriver_errors_are_not_accepted(self):
        driver = MODULE.Driver(12345)
        with patch.object(MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"value":{"error":"session not created","message":"launch failed"}}')):
            with self.assertRaisesRegex(RuntimeError, 'launch failed'):
                driver.request('POST', '/session', {})

    def test_wait_is_bounded_and_keeps_failures(self):
        with patch.object(MODULE.time, 'monotonic', side_effect=[0, 0, 2]), patch.object(MODULE.time, 'sleep'):
            with self.assertRaises(TimeoutError):
                MODULE.wait_for(lambda: False, timeout=1)
        with self.assertRaisesRegex(ValueError, 'failed'):
            MODULE.wait_for(lambda: (_ for _ in ()).throw(ValueError('failed')))


if __name__ == '__main__':
    unittest.main()
