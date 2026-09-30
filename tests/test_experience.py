import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import home,shell
from briefs import load_archive,section
class ExperienceTests(unittest.TestCase):
 def test_colored_title_and_meaningful_scene(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  for marker in ['class="experience-title"','class="robot-vignette"','概念示意，非实验演示','viewBox="0 40 700 460"']:
   self.assertIn(marker,page)
  css=(ROOT/'assets/experience.css').read_text();self.assertIn('nth-of-type(n+5):nth-of-type(-n+9)',css);self.assertIn('nth-of-type(n+10)',css)
 def test_existing_preview_uses_preserved_base(self):
  page=shell('RoboPaperAtlas','<main id="main"></main>',prefix='../',page='preview')
  self.assertIn('preview-base.css?v=',page);self.assertNotIn('experience.css?v=',page);self.assertNotIn('hero-robot.js?v=',page)
 def test_robot_runtime_suspends_and_goes_static(self):
  js=(ROOT/'assets/hero-robot.js').read_text()
  for marker in ['prefers-reduced-motion','max-width: 767px','document.hidden','IntersectionObserver','userPaused','cancelAnimationFrame','robotVignetteDestroy']:
   self.assertIn(marker,js)
 def test_daily_reader_preserves_evidence_and_states(self):
  index,records=load_archive(ROOT);out=section(records[index['latest']],index,prefix='../')
  self.assertEqual(out.count('role="tab"'),5);self.assertEqual(out.count('role="tabpanel"'),5)
  self.assertIn('基于完整摘要',out);self.assertIn('相关性判断 · 推断',out);self.assertIn('未逐版比较',out)
  js=(ROOT/'assets/brief-reader.js').read_text();self.assertIn('p.inert=!active',js);self.assertNotIn('setTimeout',js)
 def test_mobile_no_cropped_robot_figure(self):
  css=(ROOT/'assets/experience.css').read_text();self.assertNotIn('max-height:250px;overflow:hidden',css)
if __name__=='__main__':unittest.main()
