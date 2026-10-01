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
            self.assertEqual(len(json.loads((target/'submit-preview/data/venues.json').read_text())['experiences']['records']), 3)
            page = (target/'submit/index.html').read_text()
            self.assertEqual(page.count('id="main-nav"'), 1)
            self.assertEqual(page.count('id="main"'), 1)
            self.assertIn('../submit-preview/app.js?v=', page)
            self.assertIn('class="submission-module"', page)
            for element in ('nav-venues', 'nav-papers', 'query', 'workspace', 'detail', 'papers-view'):
                self.assertEqual(page.count(f'id="{element}"'), 1)
            self.assertNotIn('独立预览', page)

    def test_canonical_fetch_uses_script_location(self):
        self.assertIn("fetch(new URL('data/venues.json', document.currentScript.src))",
                      (ROOT/'submit-preview/app.js').read_text())


if __name__ == '__main__':
    unittest.main()
