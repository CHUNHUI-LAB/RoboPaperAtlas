"""Current reading navigation must expose every imported stage exactly once."""
import copy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import STAGES, display_title, esc, home, shell
from reading_index import render
import current_reader
from reports import load_reports


class ReadingIndexTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads((ROOT / 'data/catalog.json').read_text())

    def page(self, data=None):
        return render(data or self.catalog, shell, esc, display_title, STAGES)

    def test_current_stages_count_once_and_historical_versions_stay_in_detail(self):
        page = self.page()
        self.assertIn('4 篇论文 · 10 份已导入阶段报告', page)
        self.assertEqual(page.count('class="reading-stage-link"'), 10)
        self.assertEqual(page.count('class="reading-stage unavailable"'), 2)
        for paper in self.catalog['papers']:
            for stage, state in paper['stages'].items():
                if state['status'] != 'imported':
                    continue
                path = current_reader.entry_path(paper['id'], stage) or state['artifacts'][0]['path']
                self.assertEqual(page.count(f'href="../{path}"'), 1)
                for old in state['artifacts'][1:]:
                    self.assertNotIn(f'href="../{old["path"]}"', page)
            if any(s['status'] == 'imported' for s in paper['stages'].values()):
                self.assertIn(f'href="../papers/{paper["id"]}/index.html#reading"', page)
        self.assertIn('class="experience-route route-reading" href="reading/index.html"', home(self.catalog))
        self.assertIn('阅读完成不等于独立复现', page)

    def test_empty_registry_does_not_invent_reports(self):
        data = copy.deepcopy(self.catalog)
        for paper in data['papers']:
            paper['stages'] = {key: {'status': 'not_imported', 'artifacts': []} for key in paper['stages']}
        page = self.page(data)
        self.assertIn('0 篇论文 · 0 份已导入阶段报告', page)
        self.assertIn('阅读报告尚未导入', page)
        self.assertNotIn('class="reading-stage-link"', page)

    def test_display_fields_are_escaped(self):
        data = copy.deepcopy(self.catalog)
        paper = next(p for p in data['papers'] if p['id'] == 'rpa-0012')
        paper['verified_overlay']['title'] = '<script>bad()</script>'
        paper['stages']['stage1']['artifacts'][0]['source_edition'] = '<img src=x>'
        page = self.page(data)
        self.assertIn('&lt;script&gt;bad()&lt;/script&gt;', page)
        self.assertIn('&lt;img src=x&gt;', page)
        self.assertNotIn('<script>bad()', page)

    def test_all_live_deep_wbc_stages_return_to_same_paper(self):
        paper = next(p for p in self.catalog['papers'] if p['id'] == 'rpa-0012')
        records = load_reports(ROOT)
        for stage in paper['stages']:
            page = current_reader.render(ROOT, paper, stage, records)
            self.assertIn('<a class="atlas-return" href="../index.html#reading">回到论文详情</a>', page)
            self.assertNotIn('>回到论文目录</a>', page)
        with patch.dict(current_reader.FROZEN_RETURN, {'stage1': '<a>unknown</a>'}):
            with self.assertRaisesRegex(ValueError, 'signature'):
                current_reader.render(ROOT, paper, 'stage1', records)


if __name__ == '__main__':
    unittest.main()
