"""Graph reading hydration is a strict, stage-only derived-output transform."""
import copy
import hashlib
import json
import re
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import global_preview
import preview_artifacts
import preview_reading

PREVIEWS = ((global_preview, 'atlas-data'), (preview_artifacts, 'prototype-data'))


def data_match(payload, data_id):
    return re.search(r'<script id="' + data_id
                     + r'" type="application/json">(.*?)</script>', payload.decode(), re.S)


def data_of(payload, data_id):
    return json.loads(data_match(payload, data_id)[1])


def with_data(payload, data_id, data):
    text = payload.decode()
    match = data_match(payload, data_id)
    return (text[:match.start(1)] + json.dumps(data, ensure_ascii=False)
            + text[match.end(1):]).encode()


def mask_stages(payload, data_id):
    """Independent fixture oracle: mask only stage arrays in the JSON block."""
    text = payload.decode()
    match = data_match(payload, data_id)
    source = match[1]
    spans = []
    for field in re.finditer(r'"stages"\s*:\s*', source):
        _, end = json.JSONDecoder().raw_decode(source, field.end())
        spans.append((match.start(1) + field.end(), match.start(1) + end))
    if len(spans) != 95:
        raise AssertionError('Fixture must contain exactly 95 stage arrays')
    for start, end in reversed(spans):
        text = text[:start] + '[]' + text[end:]
    return text.encode()


class PreviewReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'data/catalog.json').read_text())
        cls.registry = json.loads((ROOT / 'data/reports.json').read_text())['reports']
        cls.stages = preview_reading.reading_stages(ROOT)
        cls.sources = {key: module.read_preview(ROOT) for module, key in PREVIEWS}
        cls.outputs = {key: preview_reading.hydrate_reading_stages(payload, ROOT, key)
                       for key, payload in cls.sources.items()}

    def test_all_95_ids_map_to_exact_canonical_stages_and_complete_history(self):
        canonical = {p['id']: p for p in self.catalog['papers']}
        for _, key in PREVIEWS:
            with self.subTest(preview=key):
                papers = data_of(self.outputs[key], key)['papers']
                self.assertEqual(len(papers), 95)
                self.assertEqual({p['id'] for p in papers}, set(canonical))
                self.assertEqual(sum(s['status'] == 'imported' for p in papers
                                     for s in p['stages']), 12)
                self.assertEqual(sum(len(s['links']) for p in papers
                                     for s in p['stages']), 21)
                self.assertEqual(sum(any(s['status'] == 'imported' for s in p['stages'])
                                     for p in papers), 5)
                for paper in papers:
                    expected = []
                    for number in (1, 2, 3):
                        stage = canonical[paper['id']]['stages'][f'stage{number}']
                        expected.append({'number': number, 'status': stage['status'],
                                         'links': [preview_reading.SITE_ROOT + a['path']
                                                   for a in stage['artifacts']]})
                    self.assertEqual(paper['stages'], expected)

    def test_latest_versions_and_v1_history_are_preserved(self):
        expected = {
            'rpa-0062': [['v3', 'v2', 'v1'], ['v4', 'v3', 'v2', 'v1'], ['v3', 'v2', 'v1']],
            'rpa-0012': [['v2', 'v1'], ['v1'], ['v1']],
            'rpa-0052': [['v1'], ['v1'], ['v1']],
            'rpa-0054': [['v1'], ['v1'], []],
            'rpa-0067': [['v2', 'v1'], [], []],
        }
        for _, key in PREVIEWS:
            by_id = {p['id']: p for p in data_of(self.outputs[key], key)['papers']}
            for paper_id, versions in expected.items():
                self.assertEqual([[url.split('/')[-2] for url in s['links']]
                                  for s in by_id[paper_id]['stages']], versions)

    def test_preview_versions_match_current_map_detail_and_reading_archive(self):
        from build import details, shell, esc, display_title, STAGES
        from current_reader import entry_path, render as render_current
        from map_page import map_data
        from reading_index import render as render_archive
        from reports import load_reports

        records = load_reports(ROOT)
        graph = map_data(self.catalog, report_records=records)
        by_id = {paper['id']: paper for paper in graph['papers']}
        archive = render_archive(self.catalog, shell, esc, display_title, STAGES)
        self.assertEqual(graph['relationMode'], 'topic-only')
        self.assertEqual(graph['verifiedRelations'], [])
        current_count = 0
        fixed_count = 0
        for paper in self.catalog['papers']:
            detail = details(paper)
            for index, stage in enumerate(('stage1', 'stage2', 'stage3')):
                canonical = paper['stages'][stage]
                projected = by_id[paper['id']]['stages'][stage]
                preview = self.stages[paper['id']][index]
                self.assertEqual(projected['status'], preview['status'])
                self.assertEqual(
                    [preview_reading.SITE_ROOT + a['url'][3:]
                     for a in projected['artifacts']], preview['links'])
                if canonical['status'] != 'imported':
                    self.assertEqual(projected['artifacts'], [])
                    continue
                current_count += 1
                artifact = canonical['artifacts'][0]
                current_path = entry_path(paper['id'], stage)
                self.assertIsNotNone(current_path)
                self.assertIn(f'href="../../{current_path}"', detail)
                self.assertIn(f'href="../{current_path}"', archive)
                current = render_current(ROOT, paper, stage, records)
                self.assertIn(f'href="../../../{artifact["path"]}"', current)
                self.assertIn('基于固定报告 ' + artifact['version'], current)
                self.assertEqual(projected['artifacts'][0]['version'], artifact['version'])
                for fixed in canonical['artifacts']:
                    fixed_count += 1
                    self.assertIn(f'href="../../{fixed["path"]}"', detail)
                    self.assertIn(f'href="../{fixed["path"]}"', archive)
                    self.assertIn(preview_reading.SITE_ROOT + fixed['path'], preview['links'])
        self.assertEqual((current_count, fixed_count), (12, 21))

    def test_all_non_stage_bytes_relations_classification_and_source_links_unchanged(self):
        for _, key in PREVIEWS:
            source, output = self.sources[key], self.outputs[key]
            self.assertNotEqual(source, output)
            self.assertEqual(mask_stages(source, key), mask_stages(output, key))
            before, after = data_of(source, key), data_of(output, key)
            self.assertEqual(before['relations'], after['relations'])
            self.assertEqual(sum(p['classification']['needsReview'] for p in after['papers']), 4)
            for paper_before, paper_after in zip(before['papers'], after['papers']):
                paper_before.pop('stages'); paper_after.pop('stages')
            self.assertEqual(before, after)

    def test_mapping_uses_ids_not_array_position_and_preserves_input_order(self):
        for _, key in PREVIEWS:
            data = data_of(self.sources[key], key)
            data['papers'].reverse()
            payload = with_data(self.sources[key], key, data)
            with patch.object(preview_reading, 'reading_stages', return_value=self.stages):
                output = preview_reading.hydrate_reading_stages(payload, ROOT, key)
            papers = data_of(output, key)['papers']
            self.assertEqual([p['id'] for p in papers], [p['id'] for p in data['papers']])
            for paper in papers:
                self.assertEqual(paper['stages'], self.stages[paper['id']])
            self.assertEqual(mask_stages(payload, key), mask_stages(output, key))

    def test_missing_duplicate_unknown_and_invalid_preview_ids_fail_closed(self):
        mutations = (
            lambda d: d['papers'].pop(),
            lambda d: d['papers'].append(copy.deepcopy(d['papers'][0])),
            lambda d: d['papers'][0].update(id=d['papers'][1]['id']),
            lambda d: d['papers'][0].pop('id'),
            lambda d: d['papers'][0].update(id='rpa-9999'),
            lambda d: d['papers'][0].update(id='../rpa-0001'),
            lambda d: d['papers'][0].update(id=None),
            lambda d: d['papers'][0].update(id=1),
            lambda d: d['papers'][0].update(id=[]),
            lambda d: d['papers'][0].pop('stages'),
            lambda d: d['papers'].__setitem__(0, 'invalid'),
            lambda d: d.update(papers={}),
        )
        for _, key in PREVIEWS:
            for mutation in mutations:
                data = data_of(self.sources[key], key); mutation(data)
                with self.subTest(preview=key, mutation=mutation):
                    with patch.object(preview_reading, 'reading_stages', return_value=self.stages):
                        with self.assertRaises(ValueError):
                            preview_reading.hydrate_reading_stages(
                                with_data(self.sources[key], key, data), ROOT, key)

    def test_duplicate_json_fields_invalid_constants_or_data_blocks_fail(self):
        for _, key in PREVIEWS:
            source = self.sources[key]
            match = data_match(source, key)
            block = match[0].encode()
            for payload in (
                    source.replace(b'"papers":[', b'"papers":[],"papers":[', 1),
                    source.replace(b'"id":"rpa-0001"', b'"id":"rpa-0001","id":"rpa-0001"', 1),
                    source.replace(b'"year":2022', b'"year":NaN', 1),
                    source + block,
                    source.replace(block, b'')):
                with self.subTest(preview=key):
                    with self.assertRaises(ValueError):
                        preview_reading.hydrate_reading_stages(payload, ROOT, key)

    def test_escaped_member_names_whitespace_and_unicode_are_supported(self):
        key = 'prototype-data'
        data = data_of(self.sources[key], key)
        data['papers'][0]['title'] = '中文 { "stages": [] } </script-like> & é'
        source = with_data(self.sources[key], key, data).decode()
        source = source.replace('"papers":', '"\\u0070apers" :').replace('"stages":', '"\\u0073tages" :')
        with patch.object(preview_reading, 'reading_stages', return_value=self.stages):
            output = preview_reading.hydrate_reading_stages(source.encode(), ROOT, key)
        actual = data_of(output, key)
        self.assertEqual(actual['papers'][0]['title'], data['papers'][0]['title'])
        for paper in actual['papers']:
            self.assertEqual(paper['stages'], self.stages[paper['id']])
        self.assertIn(b'"\\u0070apers" :', output)
        self.assertEqual(output.count(b'"\\u0073tages" :'), 95)

    def test_repeated_hydration_is_deterministic_and_idempotent(self):
        for _, key in PREVIEWS:
            with patch.object(preview_reading, 'reading_stages', return_value=self.stages):
                self.assertEqual(preview_reading.hydrate_reading_stages(
                    self.outputs[key], ROOT, key), self.outputs[key])

    def test_builders_authenticate_source_before_hydration_and_leave_inputs_unchanged(self):
        paths = [p for name in ('atlas-global-preview-parts', 'atlas-preview-parts', 'report-parts')
                 for p in (ROOT / 'data' / name).rglob('*') if p.is_file()]
        paths += [ROOT / 'data/catalog.json', ROOT / 'data/reports.json']
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
        with tempfile.TemporaryDirectory() as temporary:
            for module, key in PREVIEWS:
                returned = module.write_preview(ROOT, temporary)
                output = (Path(temporary) / module.ROUTE).read_bytes()
                self.assertEqual(output, self.outputs[key])
                self.assertEqual(returned, hashlib.sha256(output).hexdigest())
                target = Path(temporary) / module.ROUTE
                target.write_bytes(b'previous output')
                with patch.object(module, 'read_preview', side_effect=ValueError('integrity mismatch')):
                    with patch.object(module, 'hydrate_reading_stages') as hydrate:
                        with self.assertRaisesRegex(ValueError, 'integrity mismatch'):
                            module.write_preview(ROOT, temporary)
                        hydrate.assert_not_called()
                self.assertEqual(target.read_bytes(), b'previous output')
                with patch.object(module, 'hydrate_reading_stages', side_effect=ValueError('invalid IDs')):
                    with self.assertRaisesRegex(ValueError, 'invalid IDs'):
                        module.write_preview(ROOT, temporary)
                self.assertEqual(target.read_bytes(), b'previous output')
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})

    def test_invalid_canonical_ids_and_registry_mismatch_fail_closed(self):
        catalog_mutations = (
            lambda c: c['papers'][0].pop('id'),
            lambda c: c['papers'][0].update(id='unsafe/id'),
            lambda c: c['papers'][0].update(id=c['papers'][1]['id']),
            lambda c: c['papers'].pop(0),
            lambda c: c['papers'][0]['stages']['stage1'].update(status='imported'),
        )
        for mutation in catalog_mutations:
            catalog = copy.deepcopy(self.catalog); mutation(catalog)
            with patch.object(preview_reading, '_read_json', return_value=catalog):
                with patch.object(preview_reading, 'load_reports', return_value=self.registry):
                    with self.assertRaises(ValueError):
                        preview_reading.hydrate_reading_stages(
                            self.sources['atlas-data'], ROOT, 'atlas-data')
        for records in (self.registry[:-1], self.registry + [self.registry[0]]):
            with patch.object(preview_reading, 'load_reports', return_value=records):
                with self.assertRaises(ValueError):
                    preview_reading.reading_stages(ROOT)

    def test_report_chunk_tamper_and_missing_registry_fail_before_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(ROOT / 'data/atlas-preview-parts', root / 'data/atlas-preview-parts')
            shutil.copyfile(ROOT / 'data/catalog.json', root / 'data/catalog.json')
            with self.assertRaises(ValueError):
                preview_artifacts.write_preview(root, root / 'dist')
            self.assertFalse((root / 'dist' / preview_artifacts.ROUTE).exists())
            shutil.copyfile(ROOT / 'data/reports.json', root / 'data/reports.json')
            shutil.copytree(ROOT / 'data/report-parts', root / 'data/report-parts')
            for policy in (ROOT / 'data').glob('report-*-policy.json'):
                shutil.copyfile(policy, root / 'data' / policy.name)
            # Validate the fixture before corrupting the first registered chunk.
            preview_reading.reading_stages(root)
            part = root / 'data/report-parts/rpa-0062/v1/stage1/part-001.txt'
            part.write_bytes(b'!' + part.read_bytes()[1:])
            with self.assertRaisesRegex(ValueError, 'SHA-256 mismatch'):
                preview_artifacts.write_preview(root, root / 'dist')
            self.assertFalse((root / 'dist' / preview_artifacts.ROUTE).exists())


if __name__ == '__main__':
    unittest.main()
