"""Live presentation integration and sealed-content protection, not pixel QA."""
import hashlib
import json
import re
import sys
import unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from build import home, details, shell
from reports import assemble_reports, report_path
from current_reader import render as reader, entry_path


class Links(HTMLParser):
    def __init__(self, text):
        super().__init__(); self.links = []; self.feed(text)
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'link' and attrs.get('rel') == 'stylesheet':
            self.links.append(attrs.get('href', ''))


class AtlasDesignTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / 'data/catalog.json').read_text())
        cls.records = assemble_reports(ROOT)

    def test_shared_shell_loads_one_public_theme_with_content_hash(self):
        for page, prefix in [('catalog', ''), ('detail', '../../'), ('reading', '../'), ('map', '../'), ('frontier', '../'), ('submit', '../'), ('about', '../')]:
            document = shell('test', '<main id="main"></main>', prefix, page)
            self.assertIn('atlas-theme', document)
            self.assertEqual(len(Links(document).links), 1)
            self.assertRegex(Links(document).links[0], re.escape(prefix) + r'assets/site.css\?v=[0-9a-f]{12}$')
            for legacy in ['assets/styles.css', 'assets/library.css', 'assets/library-editorial.css', 'assets/f2.css']:
                self.assertNotIn(legacy, document)
            self.assertIn('<title>test · RoboPaperAtlas</title>', document)

    def test_catalog_preserves_all_95_ids_filters_and_real_descriptions(self):
        document = home(self.data)
        self.assertIn('id="home-title"', document)
        self.assertEqual(document.count('class="paper-card library-paper"'), 95)
        self.assertEqual(document.count('class="f2-paper-description"'), 95)
        self.assertEqual(document.count('data-classification-note='), 95)
        self.assertNotIn('class="paper-summary"', document)
        for paper in self.data['papers']:
            self.assertIn('data-preview="' + paper['id'] + '"', document)
        for name in ['search', 'topic-select', 'direction-filter', 'method-filter', 'resource-filter', 'year-filter', 'status-filter', 'reading-filter', 'sort', 'reset-filters', 'clear-all-filters']:
            self.assertIn('id="' + name + '"', document)
        self.assertEqual(document.count('id="catalog-title"'), 1)

    def test_home_hero_examples_and_counts_come_from_current_catalog(self):
        document = home(self.data)
        hero = document[document.index('<section class="home-hero"'):document.index('<section class="catalog-section"')]
        self.assertIn('星域为视觉示意，不表示论文引用关系', hero)
        ids = {paper['id'] for paper in self.data['papers']}
        examples = re.findall(r'href="papers/([a-z0-9-]+)/index.html\?catalog=', hero)
        self.assertEqual(len(examples), 8)
        self.assertTrue(set(examples) <= ids)
        reports = sum(stage['status'] == 'imported' for paper in self.data['papers'] for stage in paper['stages'].values())
        covered = sum(any(stage['status'] == 'imported' for stage in paper['stages'].values()) for paper in self.data['papers'])
        self.assertIn(f'<dt>论文目录</dt><dd>{len(ids)}</dd>', hero)
        self.assertIn(f'<dt>有阅读档案的论文</dt><dd>{covered}</dd>', hero)
        self.assertIn(f'<dt>当前阶段报告</dt><dd>{reports}</dd>', hero)

    def test_paper_details_lead_with_real_resources_and_reading_path(self):
        for paper in self.data['papers']:
            page = details(paper)
            self.assertIn('class="f2-detail-resources"', page)
            self.assertIn('class="detail-research-question"', page)
            self.assertLess(page.index('id="reading"'), page.index('id="overview"'))
            for state in paper['stages'].values():
                for artifact in state['artifacts']:
                    self.assertIn('href="../../' + artifact['path'] + '"', page)

    def test_live_readers_leave_figures_math_code_and_article_byte_identical(self):
        seen = 0
        for paper in self.data['papers']:
            for stage, state in paper['stages'].items():
                if state['status'] != 'imported' or not entry_path(paper['id'], stage):
                    continue
                fixed = (ROOT / state['artifacts'][0]['path']).read_text()
                live = reader(ROOT, paper, stage, self.records); seen += 1
                self.assertIn('atlas-current-reader', live)
                self.assertRegex(Links(live).links[-1], r'../../../assets/reader-current.css\?v=[0-9a-f]{12}$')
                self.assertNotIn('assets/f2.css', live)
                for tag in ['article', 'figure', 'img', 'svg', 'pre', 'style']:
                    # The shared chrome adds a brand SVG; SVGs inside the article
                    # must remain exactly the same (the original article is also checked).
                    original_scope = re.search(r'<article\b.*?</article>', fixed, re.S)[0]
                    live_scope = re.search(r'<article\b.*?</article>', live, re.S)[0]
                    left, right = (original_scope, live_scope) if tag == 'svg' else (fixed, live)
                    pattern = r'<img\b[^>]*>' if tag == 'img' else rf'<{tag}\b.*?</{tag}>'
                    self.assertEqual(re.findall(pattern, left, re.S), re.findall(pattern, right, re.S), (paper['id'], stage, tag))
        self.assertEqual(seen, 12)

    def test_all_21_immutable_artifacts_match_registry(self):
        self.assertEqual(len(self.records), 21)
        for record in self.records:
            self.assertEqual(hashlib.sha256((ROOT / report_path(record)).read_bytes()).hexdigest(), record['sha256'])

    def test_live_reader_has_one_shared_header_and_one_search_dialog(self):
        for paper in self.data['papers']:
            for stage, state in paper['stages'].items():
                if state['status'] != 'imported':
                    continue
                page = reader(ROOT, paper, stage, self.records)
                header = re.search(r'<header\b.*?</header>', page, re.S)[0]
                for label in ['论文库', '研究地图', '研究星图', '导航研究地图', '前沿动态', '阅读档案']:
                    self.assertIn(label, header)
                for identifier in ['main-nav', 'search-dialog', 'paper-drawer']:
                    self.assertEqual(page.count('id="' + identifier + '"'), 1, (paper['id'], stage, identifier))
                for legacy in ['Library', 'Atlas', 'Radar']:
                    self.assertNotIn('>' + legacy + '</a>', header)

    def test_standard_headers_keep_archive_and_research_entries(self):
        for page in ['catalog', 'detail', 'map', 'frontier', 'reading', 'submit', 'about']:
            document = shell('test', '<main id="main"></main>', prefix='../../', page=page, library=page == 'catalog')
            nav = re.search(r'<nav id="main-nav".*?</nav>', document, re.S)[0]
            self.assertEqual(nav.count('reading/index.html'), 1, page)
            for label in ['论文库', '研究星图', '导航研究地图', '前沿动态', '阅读档案', '投稿指南', '关于与贡献']:
                self.assertIn(label, nav, page)
        document = details(self.data['papers'][0])
        self.assertIn('class="copy-page" type="button">复制本页链接</button>', document)
        self.assertNotIn('复制本页链接 ↗', document)

    def test_styles_remain_local_and_motion_can_be_reduced(self):
        for name in ['site.css', 'home-hero.css', 'reader-current.css']:
            css = (ROOT / 'assets' / name).read_text()
            self.assertNotIn('@import', css)
            self.assertNotIn('https:', css)
            self.assertEqual(css.count('{'), css.count('}'), name)
            self.assertIn('prefers-reduced-motion', css)
            self.assertIn(':focus-visible', css if name != 'reader-current.css' else (ROOT / 'assets/site.css').read_text())

if __name__ == '__main__':
    unittest.main()
