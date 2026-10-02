import json
from pathlib import Path
import re
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from submission_page import scoped_styles, write_submission
from build import shell


class SubmissionIntegrationTests(unittest.TestCase):
    def test_navigation_uses_stable_path_at_every_depth(self):
        for prefix in ('', '../', '../../', '../../../', '/RoboPaperAtlas/'):
            page = shell('test', '<main id="main"></main>', prefix=prefix, page='submit')
            self.assertIn(f'href="{prefix}submit/index.html" aria-current="page">Submit</a>', page)

    def test_scope_and_media(self):
        css = scoped_styles(':root{--x:1}body{margin:0}nav a{color:red}@media(max-width:700px){header{height:auto}main{padding:1px}}')
        self.assertIn('.submission-module{--x:1}', css)
        self.assertIn('.submission-module nav a{', css)
        self.assertIn('@media(max-width:700px){.submission-module header{', css)
        for selectors in re.findall(r'([^{}]+)\{', css):
            self.assertTrue(selectors.startswith(('.submission-module', '@media')))
        with self.assertRaises(ValueError):
            scoped_styles('@import "https://example.com/style.css";')

    def test_single_source_and_common_shell(self):
        with tempfile.TemporaryDirectory(prefix='submission-test-', dir=ROOT) as tmp:
            target = Path(tmp)
            write_submission(ROOT, target, shell)
            self.assertEqual((target/'submit-preview/data/venues.json').read_bytes(),
                             (ROOT/'submit-preview/data/venues.json').read_bytes())
            self.assertFalse((target/'submit/data').exists())
            self.assertEqual(len(json.loads((target/'submit-preview/data/venues.json').read_text())['experiences']['records']), 7)
            page = (target/'submit/index.html').read_text()
            self.assertEqual(page.count('id="main-nav"'), 1)
            self.assertEqual(page.count('id="main"'), 1)
            self.assertIn('../submit-preview/app.js?v=', page)
            self.assertIn('class="submission-module"', page)
            for element in ('nav-venues', 'nav-experiences', 'nav-deadlines', 'nav-papers', 'query', 'workspace', 'detail', 'papers-view', 'experiences-view', 'deadlines-view', 'retry-load'):
                self.assertEqual(page.count(f'id="{element}"'), 1)
            self.assertNotIn('独立预览', page)
            self.assertEqual(page.count('class="submission-tabs"'), 1)
            self.assertNotIn('start-routes', page)

    def test_readable_task_entries_and_unselected_initial_state(self):
        html = (ROOT/'submit-preview/index.html').read_text()
        for text in ('找会议 / 期刊', '看投稿经验', '查截止日期', '跨来源准备要点'):
            self.assertIn(text, html)
        self.assertIn('id="workspace" class="workspace" tabindex="-1" hidden', html)
        css = (ROOT/'submit-preview/style.css').read_text()
        self.assertNotIn('height:680px', css)
        self.assertIn('.venue-grid{grid-template-columns:1fr', css)
        self.assertIn('prefers-reduced-motion:reduce', css)
        self.assertIn('transition:none!important', css)
        self.assertIn('summary:focus-visible', css)

    def test_canonical_fetch_uses_script_location(self):
        self.assertIn("fetch(new URL('data/venues.json', document.currentScript.src))",
                      (ROOT/'submit-preview/app.js').read_text())


if __name__ == '__main__':
    unittest.main()
