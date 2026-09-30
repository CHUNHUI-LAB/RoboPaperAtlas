"""Lossless preview transport and public report-content boundary checks."""
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from reader_theme_preview import read_preview, write_preview, ROUTE


class Article(HTMLParser):
    def __init__(self, strict=True):
        super().__init__()
        self.strict = strict
        self.inside = False
        self.text, self.images, self.sections, self.ids, self.anchors = [], [], [], [], []
        self.scripts, self.styles = 0, 0
    def handle_starttag(self, tag, attrs):
        keys = [key for key, _ in attrs]
        if len(keys) != len(set(keys)):
            raise ValueError('Duplicate HTML attribute')
        data = dict(attrs)
        if 'id' in data:
            self.ids.append(data['id'])
        if data.get('href', '').startswith('#'):
            self.anchors.append(data['href'][1:])
        if tag == 'article' and data.get('class') == 'reader-article':
            self.inside = True
        if self.inside and tag == 'section':
            self.sections.append(data.get('id'))
        if self.inside and tag == 'img':
            self.images.append(data['src'])
        if tag == 'script':
            if self.strict and 'src' in data:
                raise ValueError('Preview requires no remote script')
            self.scripts += 1
        if tag == 'style': self.styles += 1
        if self.strict and tag in {'iframe', 'object', 'embed', 'form', 'video', 'audio'}:
            raise ValueError('Unexpected active preview element')
    def handle_endtag(self, tag):
        if tag == 'article': self.inside = False
    def handle_data(self, data):
        if self.inside: self.text.append(data)


class ReaderThemePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / 'data/reader-theme-preview-parts', self.root / 'data/reader-theme-preview-parts')
        self.index = self.root / 'data/reader-theme-preview-parts/manifest.json'
    def tearDown(self): self.temp.cleanup()
    def mutate(self, fn):
        data = json.loads(self.index.read_text()); fn(data)
        self.index.write_text(json.dumps(data))
    def test_exact_utf8_transport_and_isolated_route(self):
        manifest = json.loads(self.index.read_text())
        payload = read_preview(self.root)
        self.assertEqual(hashlib.sha256(payload).hexdigest(), manifest['sha256'])
        out = self.root / 'dist'; out.mkdir()
        self.assertEqual(write_preview(self.root, out), manifest['sha256'])
        self.assertEqual((out / ROUTE).read_bytes(), payload)
        self.assertEqual(len(manifest['parts']), 36)
        self.assertTrue(all(x['bytes'] <= 48000 for x in manifest['parts']))
    def test_article_text_and_all_images_equal_existing_v3(self):
        prior = Article(strict=False); prior.feed((ROOT / 'artifacts/rpa-0062/v3/first-pass.html').read_text())
        preview = Article(); preview.feed(read_preview(self.root).decode())
        normalize = lambda parts: ''.join(''.join(parts).replace('STAGE 01', '').split())
        self.assertEqual(normalize(prior.text), normalize(preview.text))
        self.assertEqual(preview.sections, [f'section-{i:02d}' for i in range(1, 13)])
        self.assertEqual(preview.images, prior.images)
        self.assertEqual(len(preview.images), 5)
        self.assertEqual(len(preview.ids), len(set(preview.ids)))
        self.assertTrue(set(preview.anchors) <= set(preview.ids))
        self.assertEqual(preview.scripts, 1)
        self.assertEqual(preview.styles, 1)
    def test_existing_catalog_and_report_registry_are_not_promoted(self):
        registry = (ROOT / 'data/reports.json').read_text()
        catalog = (ROOT / 'data/catalog.json').read_text()
        self.assertNotIn('reader-theme-preview', registry)
        self.assertNotIn('reader-theme-preview', catalog)
    def test_tamper_reorder_duplicate_manifest_fields_fail(self):
        part = self.root / 'data/reader-theme-preview-parts/part-001.txt'
        before = part.read_bytes(); part.write_bytes(before + b' ')
        with self.assertRaises(ValueError): read_preview(self.root)
        part.write_bytes(before); self.mutate(lambda x: x['parts'].reverse())
        with self.assertRaises(ValueError): read_preview(self.root)
        self.index.write_text('{"schema_version":1,"schema_version":1}')
        with self.assertRaises(ValueError): read_preview(self.root)
    def test_unlisted_route_traversal_and_symlinks_fail(self):
        for change in [lambda x: x.update(route='../index.html'), lambda x: x['parts'][0].update(path='../outside.txt')]:
            self.index.write_bytes((ROOT / 'data/reader-theme-preview-parts/manifest.json').read_bytes())
            self.mutate(change)
            with self.assertRaises(ValueError): read_preview(self.root)
        self.index.write_bytes((ROOT / 'data/reader-theme-preview-parts/manifest.json').read_bytes())
        part = self.root / 'data/reader-theme-preview-parts/part-001.txt'
        payload = part.read_bytes(); part.unlink()
        (self.root / 'outside.txt').write_bytes(payload); part.symlink_to(self.root / 'outside.txt')
        with self.assertRaises(ValueError): read_preview(self.root)
    def test_output_parent_and_target_symlinks_fail(self):
        out = self.root / 'dist'; out.mkdir()
        (out / 'reader-theme-preview').symlink_to(self.root / 'outside', target_is_directory=True)
        with self.assertRaises(ValueError): write_preview(self.root, out)


if __name__ == '__main__': unittest.main()
