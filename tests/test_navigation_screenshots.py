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
    def test_blank_png_rejected_and_nonblank_pixels_detected(self):
        def png(rows, width):
            def chunk(kind, data):
                return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
            return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, len(rows), 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows))) + chunk(b'IEND', b'')
        self.assertFalse(MODULE.png_has_visible_variation(png([bytes([255] * 90)] * 30, 30)))
        row = bytes(v for x in range(90) for v in ((x * 7) % 256, (x * 11) % 256, (x * 17) % 256))
        self.assertTrue(MODULE.png_has_visible_variation(png([row] * 90, 90)))

    def test_required_viewports(self):
        self.assertEqual(MODULE.VIEWPORTS, [(1440, 900), (1180, 757), (659, 757), (390, 844)])

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
