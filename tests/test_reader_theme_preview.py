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
from reader_theme_preview import read_preview, write_preview, write_previews, ROUTE, PREVIEWS


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


class ScientificContent(HTMLParser):
    """Extract public prose and semantic records, ignoring presentation controls."""
    VOID = {'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self):
        super().__init__(); self.depth = 0; self.article = None; self.skip = None
        self.text, self.formulas, self.codes = [], [], []
        self.annotation = self.code = self.code_text = self.source = None
        self.source_data = ''
    def handle_starttag(self, tag, attrs):
        data = dict(attrs); classes = set(data.get('class','').split())
        if tag not in self.VOID: self.depth += 1
        if tag == 'article' and 'reader-article' in classes: self.article = self.depth
        if self.article:
            if self.skip is None and classes & {'eyebrow','code-reader'}: self.skip = self.depth
            if 'code-reader' in classes:
                self.code = (self.depth, {'id':data.get('id'), 'text':[], 'key_ids':[], 'links':[]})
            if self.code:
                if 'code-text' in classes: self.code_text = (self.depth, [])
                if 'is-key' in classes: self.code[1]['key_ids'].append(data.get('id'))
                if tag == 'a' and '#L' in data.get('href',''): self.code[1]['links'].append(data['href'])
            if tag == 'annotation' and data.get('encoding') == 'application/x-tex': self.annotation = (self.depth, [])
        if tag == 'script' and 'data-source-units' in data: self.source = self.depth
    def handle_endtag(self, tag):
        if self.annotation and self.annotation[0] == self.depth:
            self.formulas.append(''.join(self.annotation[1])); self.annotation = None
        if self.code_text and self.code_text[0] == self.depth:
            self.code[1]['text'].append(''.join(self.code_text[1])); self.code_text = None
        if self.code and self.code[0] == self.depth:
            self.codes.append(self.code[1]); self.code = None
        if self.source == self.depth: self.source = None
        if self.skip == self.depth: self.skip = None
        if self.article == self.depth: self.article = None
        self.depth -= 1
    def handle_data(self, data):
        if self.article and self.skip is None: self.text.append(data)
        if self.annotation: self.annotation[1].append(data)
        if self.code_text: self.code_text[1].append(data)
        if self.source: self.source_data += data


class ReaderThemePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        for directory in PREVIEWS.values():
            shutil.copytree(ROOT / 'data' / directory, self.root / 'data' / directory)
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

    def test_all_three_outputs_are_exact_and_independently_pinned(self):
        out = self.root / 'all-dist'; out.mkdir()
        digests = write_previews(self.root, out)
        self.assertEqual(set(digests), set(PREVIEWS))
        for route, directory in PREVIEWS.items():
            manifest = json.loads((self.root/'data'/directory/'manifest.json').read_text())
            payload = read_preview(self.root, route)
            self.assertEqual(digests[route], manifest['sha256'])
            self.assertEqual((out/route).read_bytes(), payload)
            self.assertTrue(all(part['bytes'] <= 48000 for part in manifest['parts']))
        self.assertEqual({str(p.relative_to(out)) for p in out.rglob('*.html')}, set(PREVIEWS))
    def test_every_stage_preserves_public_science_and_source_records(self):
        for route in PREVIEWS:
            name = Path(route).name
            prior_text = (ROOT/'artifacts/rpa-0062/v3'/name).read_text()
            candidate_text = read_preview(self.root, route).decode('utf8')
            stable_stages = {'first-pass.html': 'ab92db350f6796d77617c88717207d904b30a9ff725a295d7a4b049b5b17f110', 'method-code-reading.html': '36de961a6842a9dffa1b1d67b0d63e06841ca73937c4c0fc55d1fa6979bb9a88'}
            if name in stable_stages:
                self.assertEqual(hashlib.sha256(candidate_text.encode()).hexdigest(), stable_stages[name])
            prior, current = ScientificContent(), ScientificContent()
            prior.feed(prior_text); current.feed(candidate_text)
            normalize = lambda parts: ''.join(''.join(parts).split())
            if name != 'writing-close-reading.html':
                self.assertEqual(normalize(prior.text), normalize(current.text), name)
            self.assertEqual(prior.formulas, current.formulas)
            self.assertEqual(prior.codes, current.codes)
            prior_dom, current_dom = Article(strict=False), Article()
            prior_dom.feed(prior_text); current_dom.feed(candidate_text)
            self.assertEqual(prior_dom.images, current_dom.images)
            self.assertEqual(len(current_dom.ids), len(set(current_dom.ids)))
            self.assertTrue(set(current_dom.anchors) <= set(current_dom.ids))
            self.assertIn('content="atlas-reader-preview"', candidate_text)
            self.assertIn('name="robots" content="noindex,nofollow"', candidate_text)
            self.assertIn('class="atlas-site-header"', candidate_text)
            if name == 'writing-close-reading.html':
                from test_stage2_inline_quotes import assert_stage2_inline
                assert_stage2_inline(self, prior_text, candidate_text)
            elif name == 'method-code-reading.html':
                self.assertEqual(len(current.formulas), 54)
                self.assertEqual(len(current.codes), 9)
                self.assertEqual(len(current_dom.images), 6)
    def test_cross_route_substitution_and_unknown_route_fail(self):
        routes = list(PREVIEWS)
        destination = self.root/'data'/PREVIEWS[routes[1]]/'manifest.json'
        destination.write_bytes(self.index.read_bytes())
        with self.assertRaises(ValueError): read_preview(self.root, routes[1])
        with self.assertRaises(ValueError): read_preview(self.root, '../index.html')
        out = self.root/'blocked-dist'; out.mkdir()
        with self.assertRaises(ValueError): write_previews(self.root, out)
        self.assertEqual(list(out.iterdir()), [])
    def test_invalid_types_and_unknown_fields_fail_closed(self):
        original = self.index.read_bytes()
        for change in [lambda x:x.update(bytes=True), lambda x:x.update(sha256=None),
                       lambda x:x.update(extra='x'), lambda x:x['parts'][0].update(sha256=7),
                       lambda x:x.update(parts=[None])]:
            self.index.write_bytes(original); self.mutate(change)
            with self.assertRaises(ValueError): read_preview(self.root)
    def test_utf8_and_full_payload_hash_are_checked(self):
        manifest = json.loads(self.index.read_text())
        part = self.root/'data'/PREVIEWS[ROUTE]/manifest['parts'][0]['path']
        raw = part.read_bytes(); part.write_bytes(b'\xff'+raw[1:])
        with self.assertRaises(ValueError): read_preview(self.root)
        part.write_bytes(raw); self.mutate(lambda x:x.update(sha256='0'*64))
        with self.assertRaises(ValueError): read_preview(self.root)


if __name__ == '__main__': unittest.main()
