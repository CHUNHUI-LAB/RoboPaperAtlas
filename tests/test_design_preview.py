import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from design_preview import render
from build import shell,card,asset_url
class PreviewTests(unittest.TestCase):
 def test_labeled_bounded_preview(self):
  html=render(json.loads((ROOT/'data/catalog.json').read_text()),shell,card,asset_url)
  self.assertIn('设计预览',html);self.assertIn('不改变现有论文目录',html)
  self.assertIn('href="../papers/harnessvln/index.html"',html)
  self.assertNotIn('<canvas',html);self.assertNotIn('motion-toggle',html)
  self.assertIn('data-search-trigger',html);self.assertIn('class="preview-menu"',html)
 def test_route_scoped_styles(self):
  css=(ROOT/'assets/design-preview.css').read_text();self.assertIn('.page-preview',css)
  js=(ROOT/'assets/design-preview.js').read_text();self.assertIn("e.key==='Escape'",js)
if __name__=='__main__':unittest.main()

class ReferenceInteractionTests(unittest.TestCase):
 def test_three_stationary_image_cards(self):
  html=render(json.loads((ROOT/'data/catalog.json').read_text()),shell,card,asset_url)
  self.assertEqual(html.count('class="preview-destination"'),3)
  self.assertEqual(html.count('class="destination-art"'),3)
 def test_real_glyph_paths_and_controls(self):
  svg=(ROOT/'assets/preview-title.svg').read_text()
  self.assertEqual(svg.count('class="vector-letter"'),len('RoboPaperAtlas'))
  self.assertIn('class="glyph-outline"',svg);self.assertIn('class="glyph-handles"',svg)
  self.assertTrue((ROOT/'docs/licenses/dejavu-fonts.txt').exists())
 def test_accordion_uses_direct_state_no_stale_timer(self):
  js=(ROOT/'assets/design-preview.js').read_text()
  self.assertIn("control.setAttribute('aria-expanded',String(active))",js)
  self.assertIn('copy.inert=!active',js)
  self.assertNotIn('setTimeout',js)
  self.assertIn("img.setAttribute('aria-hidden',String(!active))",js)
 def test_motion_is_local_and_has_static_modes(self):
  css=(ROOT/'assets/design-preview.css').read_text()
  self.assertIn('prefers-reduced-motion:reduce',css)
  self.assertIn('hover:none',css)
  self.assertNotIn('translateY(',css)
