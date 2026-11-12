"""Independent regression guards for visible locator rendering and provenance."""
import copy
import importlib.util
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location('navigation_screenshots_locator', ROOT / 'scripts/navigation_screenshots.py')
nav = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(nav)
RAW_88 = '已核原始摘要/引言；reset位置、tour reposition精确协议待核。[paper](https://arxiv.org/abs/2210.03087)'
URL_88 = 'https://arxiv.org/abs/2210.03087'


def link(label, url):
    return {'text': label + '（' + url + '；新标签页）', 'url': url,
            'target': '_blank', 'rel': 'noopener noreferrer'}


def relations():
    source = (ROOT / 'assets/navigation-product.js').read_text()
    match = re.search(r'var TASK_READING_RELATIONS=(\[.*?\]);', source)
    if not match:
        raise AssertionError('Original relation inventory missing')
    return json.loads(match.group(1))


def proof(kind, text, relation_id, source=None, locator=None):
    frame = {'x': 0, 'y': 0, 'width': 1200, 'height': 900}
    rect = {'x': 10, 'y': 10, 'width': 1000, 'height': 20}
    fragment = dict(rect, visible=True)
    run = {'text': text, 'opaque': True, 'unscaled': True, 'fontSize': 16,
           'foreground': [0, 0, 0], 'background': [255, 255, 255],
           'fragments': [fragment], 'clipAreas': []}
    result = {'kind': kind, 'text': text, 'renderedText': text,
              'visible': True, 'opaque': True, 'unscaled': True, 'fontSize': 16,
              'clipped': False, 'foreground': [0, 0, 0], 'background': [255, 255, 255],
              'rect': rect, 'viewport': frame, 'panelClientRect': frame,
              'panelId': 'np-overview-relation-panel', 'panelContains': True,
              'relationId': relation_id, 'clipAreas': [], 'fragments': [fragment],
              'textRuns': [run], 'sourceRecord': source, 'locatorRecord': locator,
              'accessibilitySuffix': None, 'elementTag': 'P'}
    if kind == 'source':
        result.update(elementTag='A', accessibleText=text + '（新标签页）',
                      accessibilitySuffix={'tag': 'SPAN', 'className': 'np-sr', 'text': '（新标签页）'})
    return result


def valid_evidence(expected):
    rid = expected['id']
    specs = [{'kind': 'heading', 'text': expected['proposedLabel']}]
    specs += [nav.relation_locator_spec(loc, i) for i, loc in enumerate(expected['locators'])]
    for ref in expected['sourceRefs']:
        source = {'id': ref['sourceId'], 'url': ref['url'], 'version': ref['versionId'], 'status': ref['versionStatus']}
        status = {'snapshot_not_version_pinned': '未固定全文快照', 'fixed_arxiv_version_url': '来源URL限定版本'}.get(ref['versionStatus'], ref['versionStatus'])
        specs += [{'kind': 'source', 'text': '原文来源 · ' + (ref.get('descriptor') or ref['sourceId']), 'source': source},
                  {'kind': 'status', 'text': ' · ' + status, 'source': source}]
    proofs = [proof(s['kind'], s['text'], rid, s.get('source'), s.get('locatorRecord')) for s in specs]
    return {'id': rid, 'type': expected['relationType'], 'from': expected['from'], 'to': expected['to'],
            'open': True, 'focus': 'np-map-relation-evidence-' + rid,
            'route': {'tree': 'g'}, 'beforeRoute': {'tree': 'g'},
            'sources': [s['source'] for s in specs if s['kind'] == 'source'],
            'text': '\n'.join(p['text'] for p in proofs), 'visibleProofs': proofs}


class LocatorDisplayTests(unittest.TestCase):
    def test_public_javascript_fixture_parity(self):
        path = ROOT / 'tests/fixtures/navigation_relation_locator.json'
        fixtures = json.loads(path.read_text())
        self.assertTrue(fixtures, 'Shared static display fixtures must not be empty')
        for case in fixtures:
            with self.subTest(case=case['name']):
                self.assertEqual(nav.relation_locator_display(case['raw']), case['expected'])

    def test_relation_88_original_and_display(self):
        expected = relations()[0]
        self.assertEqual(expected['id'], 'tasks:relation:88')
        self.assertEqual(expected['locators'][0]['locator'], RAW_88)
        self.assertEqual(expected['sourceRefs'][0]['locator'], RAW_88)
        display = nav.relation_locator_display(RAW_88)
        anchor = link('paper', URL_88)
        self.assertEqual(display, {'text': RAW_88.split('[paper]')[0] + anchor['text'], 'links': [anchor]})
        self.assertEqual(nav.relation_locator_spec(expected['locators'][0], 0), {
            'kind': 'locator', 'text': display['text'],
            'locatorRecord': {'index': 0, 'raw': RAW_88, 'links': [anchor]}})

    def test_plain_original_text_unchanged(self):
        for raw in ('', '§3、tour表、t-nDTW定义、Appendix B', '  正文\n原文\t保持  ', '<b>literal & text</b>'):
            with self.subTest(raw=raw):
                self.assertEqual(nav.relation_locator_display(raw), {'text': raw, 'links': []})

    def test_unsafe_and_malformed_remain_literal(self):
        cases = ['[x](javascript:alert(1))', '[x](data:text/html,hello)', '[x](mailto:a@example.com)',
                 '[x](https://user:password@example.com/a)', '[x](http://user@example.com/a)',
                 '[x](//example.com/a)', '[x](/relative)', '[x](https://)',
                 '[x](https://example.com/a b)', '[x](https://example.com/a',
                 '[[x]](https://example.com)', '[x](https://example.com/a(b))',
                 '[x](https://example.com "title")', '[](https://example.com)']
        for raw in cases:
            with self.subTest(raw=raw):
                self.assertEqual(nav.relation_locator_display(raw), {'text': raw, 'links': []})

    def test_multiple_links_keep_order_and_surrounding_text(self):
        first, second = link('same', 'https://example.com/a?x=1&y=2#part'), link('same', 'http://example.org/b')
        raw = '前[same](https://example.com/a?x=1&y=2#part)，中[same](http://example.org/b)。后'
        self.assertEqual(nav.relation_locator_display(raw), {'text': '前' + first['text'] + '，中' + second['text'] + '。后', 'links': [first, second]})

    def test_all_original_relations_pass_complete_evidence(self):
        for expected in relations():
            with self.subTest(relation=expected['id']):
                nav.check_relation_evidence(valid_evidence(expected), expected)

    def test_locator_identity_and_links_are_required(self):
        expected = relations()[0]
        mutations = {
            'wrong raw': lambda p: p['locatorRecord'].__setitem__('raw', RAW_88 + 'wrong'),
            'wrong index': lambda p: p['locatorRecord'].__setitem__('index', 1),
            'missing links': lambda p: p['locatorRecord'].__setitem__('links', []),
            'wrong url': lambda p: p['locatorRecord']['links'][0].__setitem__('url', 'https://wrong.example/'),
            'wrong target': lambda p: p['locatorRecord']['links'][0].__setitem__('target', '_self'),
            'wrong rel': lambda p: p['locatorRecord']['links'][0].__setitem__('rel', ''),
            'missing record': lambda p: p.pop('locatorRecord'),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                data = valid_evidence(expected)
                mutate(data['visibleProofs'][1])
                with self.assertRaises(RuntimeError):
                    nav.check_relation_evidence(data, expected)

    def test_duplicate_label_link_order_is_evidence_identity(self):
        expected = copy.deepcopy(relations()[0])
        expected['locators'][0]['locator'] = '[same](https://example.com/a) + [same](https://example.com/b)'
        data = valid_evidence(expected)
        nav.check_relation_evidence(data, expected)
        data['visibleProofs'][1]['locatorRecord']['links'].reverse()
        with self.assertRaises(RuntimeError):
            nav.check_relation_evidence(data, expected)

    def test_visibility_geometry_and_source_gates_remain_strict(self):
        expected = relations()[0]
        mutations = {
            'hidden': lambda d: d['visibleProofs'][1].__setitem__('visible', False),
            'clipped': lambda d: d['visibleProofs'][1].__setitem__('clipped', True),
            'hidden run': lambda d: d['visibleProofs'][1]['textRuns'][0]['fragments'][0].__setitem__('visible', False),
            'offscreen': lambda d: d['visibleProofs'][1]['rect'].__setitem__('x', 2000),
            'wrong panel': lambda d: d['visibleProofs'][1].__setitem__('panelContains', False),
            'wrong source': lambda d: d['sources'][0].__setitem__('id', 'wrong'),
            'wrong version': lambda d: d['sources'][0].__setitem__('version', 'wrong'),
            'lost qualifier': lambda d: d['visibleProofs'][1].__setitem__('text', 'paper'),
            'hidden raw fallback': lambda d: d['visibleProofs'][1].__setitem__('renderedText', RAW_88),
            'missing proof': lambda d: d['visibleProofs'].pop(),
        }
        for name, mutate in mutations.items():
            with self.subTest(case=name):
                data = copy.deepcopy(valid_evidence(expected))
                mutate(data)
                with self.assertRaises(RuntimeError):
                    nav.check_relation_evidence(data, expected)


if __name__ == '__main__':
    unittest.main()
