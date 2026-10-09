"""Additive, deployment-prefix-safe entry links without rewriting archive content."""
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import sys
import unittest
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build
import objectnav_reading_preview as objectnav
import radar_c2_preview as c2


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.links = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.links.append(dict(attrs))


class NavigationEntryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.home = build.home(json.loads((ROOT / 'data/catalog.json').read_text()))
        payload, data = objectnav.payloads(ROOT)
        cls.objectnav = objectnav.render(data, payload)
        cls.c2_payload = c2.payloads(ROOT)
        cls.archive = cls.c2_payload['index.html'].decode('utf8')

    def test_all_three_entries_resolve_under_site_prefix(self):
        for prefix in ('/', '/RoboPaperAtlas/'):
            base = 'https://example.org' + prefix
            expected = base + 'research/navigation/index.html'
            for route, text in (('index.html', self.home),
                                (c2.ROUTE + '/index.html', self.archive),
                                (objectnav.ROUTE + '/index.html', self.objectnav)):
                with self.subTest(prefix=prefix, route=route):
                    links = [a for a in Links(text).links
                             if 'research/navigation/' in a.get('href', '')]
                    self.assertEqual(len(links), 1)
                    self.assertFalse(links[0]['href'].startswith('/'))
                    self.assertEqual(urljoin(base + route, links[0]['href']), expected)
                    self.assertNotIn('target', links[0])
                    self.assertIn('导航研究地图 · 正式三树', text)

    def test_c2_preserves_all_sealed_content_and_route(self):
        self.assertEqual(c2.ROUTE, 'review/radar-c2-analysis')
        for name, content in self.c2_payload.items():
            original = (ROOT / c2.SOURCE / name).read_bytes()
            if name in ('index.html', 'analysis/c2.js'):
                text = content.decode('utf8')
                stripped, count = re.subn(
                    r'<a href="../../research/navigation/index.html" '
                    r'data-navigation-entry="formal" title="导航研究地图 · 正式三树">正式三树 →</a>',
                    '', text)
                self.assertEqual(count, 1)
                if name == 'index.html':
                    original_script = (ROOT / c2.SOURCE / 'analysis/c2.js').read_bytes()
                    old_version = c2.sha256(original_script)[:12]
                    new_version = c2.sha256(self.c2_payload['analysis/c2.js'])[:12]
                    self.assertNotEqual(old_version, new_version)
                    self.assertEqual(stripped.count('analysis/c2.js?v=' + new_version), 1)
                    stripped = stripped.replace('analysis/c2.js?v=' + new_version,
                                                'analysis/c2.js?v=' + old_version)
                self.assertEqual(stripped.encode('utf8'), original)
            else:
                self.assertEqual(content, original, name)
        self.assertEqual(c2.payloads(ROOT), self.c2_payload)

    def test_archive_link_uses_existing_header_without_layout_changes(self):
        script = self.c2_payload['analysis/c2.js'].decode('utf8')
        start = script.index('<header class="ft-top">')
        self.assertIn('data-navigation-entry="formal"', script[start:script.index('</header>', start)])
        self.assertNotIn('data-navigation-entry="layout"', self.archive)
        for prefix in ('/', '/RoboPaperAtlas/'):
            href = [a['href'] for a in Links(script).links
                    if a.get('data-navigation-entry') == 'formal']
            self.assertEqual(len(href), 1)
            self.assertEqual(urljoin('https://example.org' + prefix + c2.ROUTE + '/index.html', href[0]),
                             'https://example.org' + prefix + 'research/navigation/index.html')

    def test_objectnav_keeps_old_navigation_and_sections(self):
        links = [a.get('href') for a in Links(self.objectnav).links]
        self.assertEqual(links.count('../radar-c2-analysis/index.html'), 2)
        for section in ('overview', 'comparison', 'poni-evidence', 'analysis', 'sources'):
            self.assertIn('id="' + section + '"', self.objectnav)
        self.assertEqual(objectnav.ROUTE, 'review/objectnav-reading-v1')


if __name__ == '__main__':
    unittest.main()
