"""Small synthetic fixtures only: report transport and public HTML boundary."""
import base64
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reports as r

PNG = 'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX9sAAAAASUVORK5CYII='


def html(body='<h1 id="intro">安全报告</h1>', style='body { color: #222; }'):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>测试报告</title><style>' + style + '</style></head><body>' + body +
            '</body></html>').encode('utf-8')


def metadata(stage='stage1'):
    return {
        'paper_id': 'rpa-0062', 'stage': stage, 'version': 'v1',
        'filename': r.STAGE_FILES[stage], 'source_sha256': 'a' * 64,
        'source_edition': 'Synthetic test edition',
        'source_url': 'https://arxiv.org/abs/2407.10353',
        'pdf_url': 'https://arxiv.org/pdf/2407.10353',
        'created_at': '2026-09-30', 'review_status': 'approved',
        'rights_note': 'Synthetic original test content only.',
    }


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'data').mkdir()
        self.registry([])

    def registry(self, records):
        (self.root / 'data/reports.json').write_text(
            json.dumps({'schema_version': 1, 'reports': records}), encoding='utf-8')

    def add(self, payload=None, stage='stage1'):
        record = r.split_report(self.root, metadata(stage), payload or html())
        self.registry([record])
        return record

    def part(self, record, index=0):
        return self.root / r._parts_path(record) / record['parts'][index]['file']

    def rejected_record(self, field, value):
        record = self.add()
        record[field] = value
        self.registry([record])
        with self.assertRaises(ValueError):
            r.load_reports(self.root)

    def test_empty_registry(self):
        self.assertEqual(r.load_reports(self.root), [])
        self.assertEqual(r.assemble_reports(self.root), [])
        self.assertFalse((self.root / 'artifacts').exists())

    def test_exact_utf8_roundtrip_and_unchanged_registry(self):
        payload = html('<h1 id="intro">报告</h1><p>' + '雨🤖' * 16000 + '</p>')
        record = self.add(payload)
        original = (self.root / 'data/reports.json').read_bytes()
        self.assertGreater(len(record['parts']), 1)
        for part in record['parts']:
            raw = (self.root / r._parts_path(record) / part['file']).read_bytes()
            self.assertLessEqual(len(raw), 48000)
            raw.decode('utf-8')
            self.assertEqual(r.sha(raw), part['sha256'])
        self.assertEqual(r.load_reports(self.root), [record])
        self.assertFalse((self.root / 'artifacts').exists())
        self.assertEqual(r.assemble_reports(self.root), [record])
        target = self.root / r.report_path(record)
        self.assertEqual(target.read_bytes(), payload)
        self.assertEqual((self.root / 'data/reports.json').read_bytes(), original)
        self.assertEqual(set(record), r.RECORD_FIELDS)

    def test_split_does_not_edit_input_record_or_registry(self):
        meta = metadata()
        before = copy.deepcopy(meta)
        original = (self.root / 'data/reports.json').read_bytes()
        record = r.split_report(self.root, meta, html())
        self.assertEqual(meta, before)
        self.assertEqual((self.root / 'data/reports.json').read_bytes(), original)
        self.assertEqual(record['bytes'], len(html()))

    def test_manifest_metadata_strictness(self):
        cases = [('paper_id', '../rpa-0062'), ('paper_id', 'rpa-0063'), ('stage', 1),
                 ('version', 'v4'), ('filename', '../first-pass.html'),
                 ('review_status', 'pending'), ('created_at', '2026-02-30'),
                 ('created_at', '2026-09-30T00:00:00Z'), ('source_edition', ''),
                 ('rights_note', ' '), ('source_sha256', 'A' * 64), ('bytes', True),
                 ('source_url', 'https://example.com/'), ('pdf_url', 'http://arxiv.org/pdf/2407.10353'),
                 ('source_url', 'https://arxiv.org/abs/2407.10353?token=secret'),
                 ('private_path', '/private/example')]
        for field, value in cases:
            with self.subTest(field=field, value=value):
                self.rejected_record(field, value)
        record = self.add()
        del record['rights_note']
        self.registry([record])
        with self.assertRaises(ValueError):
            r.load_reports(self.root)

    def test_registry_envelope_and_duplicate_json_fields(self):
        invalid = [
            '{"schema_version":1,"schema_version":1,"reports":[]}',
            '{"schema_version":true,"reports":[]}',
            '{"schema_version":1,"reports":[],"path":"anything"}',
            '{"schema_version":1,"reports":{}}',
        ]
        for text in invalid:
            with self.subTest(text=text):
                (self.root / 'data/reports.json').write_text(text)
                with self.assertRaises(ValueError):
                    r.load_reports(self.root)

    def test_duplicate_reports_rejected(self):
        record = self.add()
        self.registry([record, record])
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            r.load_reports(self.root)

    def test_unknown_part_field_and_traversal_rejected(self):
        for field, value in [('file', '../outside.txt'), ('file', '/tmp/outside.txt'),
                             ('file', 'part-002.txt'), ('path', 'part-001.txt'), ('bytes', True)]:
            with self.subTest(field=field, value=value):
                record = self.add()
                record['parts'][0][field] = value
                self.registry([record])
                with self.assertRaises(ValueError):
                    r.load_reports(self.root)

    def test_missing_reordered_duplicate_parts_rejected(self):
        payload = html('<p>' + '中文' * 25000 + '</p>')
        for change in ('missing', 'reordered', 'duplicate'):
            with self.subTest(change=change):
                record = self.add(payload)
                if change == 'missing':
                    self.part(record).unlink()
                elif change == 'reordered':
                    record['parts'].reverse()
                else:
                    record['parts'][1] = dict(record['parts'][0])
                self.registry([record])
                with self.assertRaises(ValueError):
                    r.load_reports(self.root)

    def test_chunk_hash_length_limit_and_total_hash(self):
        record = self.add()
        self.part(record).write_bytes(html() + b' ')
        with self.assertRaises(ValueError):
            r.load_reports(self.root)
        record = self.add()
        record['sha256'] = '0' * 64
        self.registry([record])
        with self.assertRaises(ValueError):
            r.load_reports(self.root)
        record = self.add()
        record['parts'][0]['bytes'] = 48001
        record['bytes'] = 48001
        self.registry([record])
        with self.assertRaises(ValueError):
            r.load_reports(self.root)

    def test_invalid_utf8_and_utf8_split_inside_character(self):
        with self.assertRaises(ValueError):
            r.split_report(self.root, metadata(), html() + b'\xff')
        raw = html()
        split = raw.index('测试'.encode()) + 1
        record = self.add(raw)
        chunks = [raw[:split], raw[split:]]
        record['parts'] = []
        for index, chunk in enumerate(chunks, 1):
            name = f'part-{index:03d}.txt'
            (self.root / r._parts_path(record) / name).write_bytes(chunk)
            record['parts'].append({'file': name, 'bytes': len(chunk), 'sha256': r.sha(chunk)})
        self.registry([record])
        with self.assertRaisesRegex(ValueError, 'independently valid UTF-8'):
            r.load_reports(self.root)

    def test_symlinked_registry_chunk_directory_output_and_root(self):
        record = self.add()
        registry = self.root / 'data/reports.json'
        backup = self.root / 'backup.json'
        registry.rename(backup)
        registry.symlink_to(backup)
        with self.assertRaises(ValueError):
            r.load_reports(self.root)
        registry.unlink()
        backup.rename(registry)
        part = self.part(record)
        saved = self.root / 'saved.txt'
        part.rename(saved)
        part.symlink_to(saved)
        with self.assertRaises(ValueError):
            r.load_reports(self.root)
        with self.assertRaises(ValueError):
            r.split_report(self.root, metadata(), html())
        part.unlink()
        saved.rename(part)
        directory = part.parent
        moved = directory.with_name('moved')
        directory.rename(moved)
        directory.symlink_to(moved, target_is_directory=True)
        with self.assertRaises(ValueError):
            r.load_reports(self.root)
        directory.unlink()
        moved.rename(directory)
        (self.root / 'artifacts').symlink_to(self.root / 'data', target_is_directory=True)
        with self.assertRaises(ValueError):
            r.assemble_reports(self.root)
        link = self.root / 'root-link'
        link.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ValueError):
            r.load_reports(link)

    def test_symlinked_output_file_rejected_without_modifying_target(self):
        record = self.add()
        target = self.root / r.report_path(record)
        target.parent.mkdir(parents=True)
        innocent = self.root / 'innocent.txt'
        innocent.write_text('unchanged')
        target.symlink_to(innocent)
        with self.assertRaises(ValueError):
            r.assemble_reports(self.root)
        self.assertEqual(innocent.read_text(), 'unchanged')

    def test_safe_semantics_images_css_checkbox_and_links(self):
        body = ('<h1 id="intro">报告</h1><a href="#intro">目录</a>'
                '<a href="https://github.com/real-stanford/umi-on-legs">源代码</a>'
                '<a href="' + r.SITE_RETURN + '">回到目录</a>'
                '<details open><summary>细节</summary><p>说明</p></details>'
                '<input type="checkbox" id="zoom"><label for="zoom">放大</label>'
                '<img alt="测试" src="data:image/png;base64,' + PNG + '">')
        self.add(html(body, 'html { scroll-behavior: smooth; } @media (max-width:600px) { body { color: red; } }'))
        self.assertEqual(len(r.load_reports(self.root)), 1)

    def test_active_tags_attributes_and_bad_inputs_rejected(self):
        cases = ['<script>alert(1)</script>', '<iframe src="https://example.com"></iframe>',
                 '<object></object>', '<embed>', '<form></form>', '<base href="https://example.com">',
                 '<meta http-equiv="refresh" content="0;url=https://example.com">',
                 '<svg><a></a></svg>', '<math></math>', '<link rel="stylesheet" href="https://example.com">',
                 '<p onclick="alert(1)">x</p>', '<img src="https://example.com/a.png">',
                 '<input type="text">', '<input type>', '<input type="checkbox" formaction="https://example.com">',
                 '<a href="#intro" href="https://example.com">duplicate</a>',
                 '<meta charset="utf-7">', '<style type>body {color:red}</style>']
        for body in cases:
            with self.subTest(body=body), self.assertRaises(ValueError):
                r.split_report(self.root, metadata(), html(body))

    def test_unsafe_css_rejected_in_blocks_and_attributes(self):
        cases = ['@import "https://example.com/x.css";', 'p{background:url(https://example.com)}',
                 'p{background:u/**/rl(//example.com)}', 'p{background:u\\72l(//example.com)}',
                 'p{width:expression(alert(1))}', 'p{behavior:url(x)}', 'p{-moz-binding:url(x)}',
                 'p{background:image-set("//example.com/a.png" 1x)}', '@font-face{font-family:x;src:local(x)}']
        for css in cases:
            with self.subTest(css=css), self.assertRaises(ValueError):
                r.split_report(self.root, metadata(), html(style=css))
        with self.assertRaises(ValueError):
            r.split_report(self.root, metadata(), html('<p style="background:url(x)">x</p>'))

    def test_fake_invalid_or_mislabeled_images_rejected(self):
        cases = ['data:image/png;base64,not-base64!',
                 'data:image/png;base64,' + base64.b64encode(b'<svg></svg>').decode(),
                 'data:image/jpeg;base64,' + PNG,
                 'data:image/svg+xml;base64,' + base64.b64encode(b'<svg></svg>').decode(),
                 'data:image/gif;base64,R0lGODlh', 'data:image/png;base64,',
                 'data:image/png;base64,' + PNG + '\n']
        for src in cases:
            with self.subTest(src=src[:60]), self.assertRaises(ValueError):
                r.split_report(self.root, metadata(), html('<img src="' + src + '">'))

    def test_unsafe_links_and_unresolved_anchors_rejected(self):
        for href in ['javascript:alert(1)', 'data:text/html,hello', 'file:///tmp/a',
                     'http://example.com', '//example.com', '../first-pass.html',
                     '/first-pass.html', 'unknown.html', 'first-pass.html?x=1',
                     '#missing', '#%FF', '#bad%', 'https://127.0.0.1/a',
                     'https://example.com:444/a', r.SITE_RETURN + '#missing']:
            with self.subTest(href=href), self.assertRaises(ValueError):
                r.split_report(self.root, metadata(), html('<a href="' + href + '">x</a>'))
        with self.assertRaises(ValueError):
            r.split_report(self.root, metadata(), html('<p id="same">x</p><p id="same">y</p>'))

    def test_registry_cross_report_links_and_fragments(self):
        first = r.split_report(self.root, metadata(), html(
            '<a href="writing-close-reading.html#target">下一阶段</a>'))
        self.registry([first])
        with self.assertRaisesRegex(ValueError, 'absent'):
            r.load_reports(self.root)
        second = r.split_report(self.root, metadata('stage2'), html('<h1 id="target">写作</h1>'))
        self.registry([first, second])
        self.assertEqual(r.load_reports(self.root), [first, second])
        second = r.split_report(self.root, metadata('stage2'), html('<h1>没有目标</h1>'))
        self.registry([first, second])
        with self.assertRaisesRegex(ValueError, 'Unresolved sibling'):
            r.assemble_reports(self.root)
        self.assertFalse((self.root / 'artifacts').exists())

    def test_validation_finishes_before_any_artifact_write(self):
        first = r.split_report(self.root, metadata(), html())
        second = r.split_report(self.root, metadata('stage2'), html())
        self.part(second).write_bytes(b'tampered')
        self.registry([first, second])
        with self.assertRaises(ValueError):
            r.assemble_reports(self.root)
        self.assertFalse((self.root / 'artifacts').exists())


if __name__ == '__main__':
    unittest.main()
