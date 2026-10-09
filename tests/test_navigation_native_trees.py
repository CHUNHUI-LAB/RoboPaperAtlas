"""Native HTML contract tests: actual topology/content, not JS or pixel claims."""
import copy
import gzip
import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import unittest
from urllib.parse import parse_qs

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from navigation_native_trees import render_native_trees, DEFAULT_SCOPE, PONI_VERSION, TEXT_FIELDS, PIPELINE_FIELDS, _text, _safe_url


class DOM(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.nodes, self.stack, self.text = [], [], []
        self.feed(text)
    def handle_starttag(self, tag, attrs):
        node = {'tag': tag, 'attrs': dict(attrs), 'parent': self.stack[-1] if self.stack else None}
        self.nodes.append(node)
        if tag not in ('br', 'hr', 'img', 'input', 'meta', 'link'):
            self.stack.append(node)
    def handle_endtag(self, tag):
        if not self.stack or self.stack[-1]['tag'] != tag:
            raise AssertionError('Unbalanced native HTML: ' + tag)
        self.stack.pop()
    def handle_data(self, data):
        self.text.append(data)


class NativeTreeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((ROOT / 'data/navigation-product/model.json.gz').read_bytes())
        cls.model = json.loads(cls.raw)
        cls.html = render_native_trees(cls.model)
        cls.dom = DOM(cls.html)
        cls.positions = [n for n in cls.dom.nodes if 'data-native-position' in n['attrs']]

    def test_frozen_science_is_unchanged(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c')
        before = json.dumps(self.model, sort_keys=True)
        self.assertEqual(render_native_trees(self.model), self.html)
        self.assertEqual(json.dumps(self.model, sort_keys=True), before)

    def test_complete_real_default_forests_and_original_analysis_hierarchy(self):
        counts = {tree: sum(n['attrs']['data-native-tree'] == tree for n in self.positions) for tree in ('l', 'c', 'a')}
        self.assertEqual(counts, {'l': 33, 'c': 31, 'a': 59})
        self.assertEqual(len({n['attrs']['data-native-position'] for n in self.positions}), 123)
        for node in self.positions:
            p = self.model['positions'][node['attrs']['data-native-position']]
            parent = node['parent']
            while parent and 'data-native-position' not in parent['attrs']:
                parent = parent['parent']
            self.assertEqual(parent['attrs']['data-native-position'] if parent else None, p['parentId'])
            self.assertEqual(node['tag'], 'details')
            self.assertEqual('open' in node['attrs'], p['parentId'] is None)
        analysis = [n for n in self.positions if n['attrs']['data-native-tree'] == 'a']
        self.assertEqual({n['attrs']['data-original-node'] for n in analysis}, set(self.model['template']['nodeIds']))
        self.assertEqual(sum(n['attrs']['data-native-answer'] == 'answered' for n in analysis), 22)

    def test_real_children_precede_optional_root_prose(self):
        for tree in ('l', 'c'):
            root = self.model['positions'][self.model['forests'][DEFAULT_SCOPE][tree][0]]
            start = self.html.index('data-native-position="' + root['id'] + '"')
            child = self.html.index('data-native-position="' + root['childIds'][0] + '"', start)
            # The root summary is followed directly by genuine child positions.
            self.assertNotIn('class="np-native-content"', self.html[start:child])

    def test_no_script_required_and_selection_scope_is_explicit(self):
        self.assertFalse(any(n['tag'] in ('script', 'select', 'button', 'iframe') for n in self.dom.nodes))
        self.assertIn('不是全领域目录', self.html)
        self.assertIn('选择 PONI · CVPR 2022 accepted proceedings', self.html)
        choices = [n for n in self.dom.nodes if n['attrs'].get('class') == 'np-native-analysis-choice']
        self.assertEqual(len(choices), 1)
        self.assertNotIn('open', choices[0]['attrs'])
        self.assertIn('22 个节点已填', self.html)
        self.assertIn('37 个结构／未填节点', self.html)

    def test_original_notes_remain_exact_and_long_boundary_is_collapsed(self):
        text = ''.join(self.dom.text)
        for template in self.model['template']['nodes']:
            for key in ('note', 'structural_note'):
                if template.get(key):
                    self.assertIn(template[key], text)
        self.assertIn('不是隐瞒真实方法缺陷的建议', text)
        boundary = next(n for n in self.dom.nodes if n['attrs'].get('class') == 'np-native-boundary')
        self.assertNotIn('open', boundary['attrs'])
        self.assertIn('默认 ObjectNav 原生树；全部研究入口需增强加载。', text)

    def test_every_enhanced_link_has_exact_valid_identity(self):
        links = [n['attrs']['href'] for n in self.dom.nodes if 'data-native-enhanced-link' in n['attrs']]
        self.assertEqual(len(links), 123)
        for href in links:
            query = {k: v[0] for k, v in parse_qs(href[1:]).items()}
            p = self.model['positions'][query['node']]
            self.assertEqual(query['scope'], DEFAULT_SCOPE)
            self.assertEqual(query['tree'], p['tree'])
            self.assertEqual(query.get('paper'), p.get('paperId'))
            self.assertEqual(query.get('version'), p.get('versionId'))
        script = "const fs=require('fs'),z=require('zlib'),M=require('./assets/navigation-product-model.js');const b=JSON.parse(z.gunzipSync(fs.readFileSync('data/navigation-product/model.json.gz')));for(const h of JSON.parse(fs.readFileSync(0,'utf8')))M.validateRoute(b,M.parseRoute(b,h));"
        subprocess.run(['node', '-e', script], cwd=ROOT, input=json.dumps(links), text=True, check=True)

    def test_scientific_text_and_partial_answers_are_exact_not_borrowed(self):
        text = ''.join(self.dom.text)
        for node in self.positions:
            p = self.model['positions'][node['attrs']['data-native-position']]
            self.assertIn(p['label'], text)
            d = self.model['entities'][p['entityId']].get('detail', {})
            if p['kind'] == 'analysis_answer':
                self.assertEqual(p['paperId'], 'poni')
                self.assertEqual(p['versionId'], PONI_VERSION)
                self.assertIn(d['answer'].get('text') or d['answer']['answer'], text)
            elif p['tree'] != 'a':
                for key, _ in TEXT_FIELDS:
                    if _text(d.get(key)):
                        self.assertIn(_text(d[key]), text)
                for key, _ in PIPELINE_FIELDS:
                    if _text(d.get('pipeline', {}).get(key)):
                        self.assertIn(_text(d['pipeline'][key]), text)
        self.assertIn('未填写不表示原论文没有讨论', text)
        self.assertIn('完整附录/补充材料', text)
        self.assertIn('独立实验复现', text)

    def test_href_safety_and_escaping_do_not_dump_unlisted_private_fields(self):
        model = copy.deepcopy(self.model)
        root = model['positions'][model['forests'][DEFAULT_SCOPE]['l'][0]]
        root['label'] = '<script>alert(1)</script>" onmouseover="bad'
        entity = model['entities'][root['entityId']]
        entity['detail']['definition'] = '<img src=x onerror=bad>'
        entity['detail']['private_debug_mapping'] = 'PRIVATE-SENTINEL'
        entity['sourceRefs'] = [{'url': url, 'descriptor': '<bad>'} for url in ['javascript:alert(1)', 'data:text/html,x', '//evil.example/x', 'https://user:secret@example.org/x', 'https://example.org/\nx', 'https:\\evil.example']]
        html = render_native_trees(model); dom = DOM(html)
        self.assertNotIn('PRIVATE-SENTINEL', html)
        self.assertNotIn('<script>', html)
        self.assertFalse(any(n['tag'] == 'img' or any(k.startswith('on') for k in n['attrs']) for n in dom.nodes))
        self.assertIn('&lt;script&gt;', html)
        for node in dom.nodes:
            href = node['attrs'].get('href')
            if href and not href.startswith('#nav=1&'):
                self.assertEqual(_safe_url(href), href)

    def test_reject_cross_version_answer_and_broken_topology(self):
        model = copy.deepcopy(self.model)
        target = next(p for p in model['positions'].values() if p['kind'] == 'analysis_answer' and p.get('paperId') == 'poni')
        target['versionId'] = 'wrong-version'
        with self.assertRaises(ValueError):
            render_native_trees(model)
        model = copy.deepcopy(self.model)
        root = model['positions'][model['forests'][DEFAULT_SCOPE]['l'][0]]
        root['childIds'].append(root['id'])
        with self.assertRaises(ValueError):
            render_native_trees(model)


if __name__ == '__main__':
    unittest.main()
