import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import home,shell
from briefs import load_archive,section
class ExperienceTests(unittest.TestCase):
 def test_colored_title_and_meaningful_scene(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  for marker in ['class="experience-title"','class="atlas-galaxy"','知识星图 · 抽象视觉，非引用关系','data-atlas-toggle']:
   self.assertIn(marker,page)
  css=(ROOT/'assets/experience.css').read_text();self.assertIn('nth-of-type(n+5):nth-of-type(-n+9)',css);self.assertIn('nth-of-type(n+10)',css)
 def test_atlas_topics_and_truthful_label(self):
  from html.parser import HTMLParser
  data=json.loads((ROOT/'data/catalog.json').read_text());page=home(data)
  for key in ['navigation-space','motion-manipulation','robot-learning','methods-resources']:
   self.assertIn('index.html?topic='+key+'#catalog',page)
  self.assertIn('非引用关系',page);self.assertIn('hero-atlas.svg?v=',page)
  self.assertNotIn('hero-robot',page);self.assertNotIn('robot-vignette',page)
 def test_topic_paper_examples_are_real_and_labeled(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertEqual(page.count('data-atlas-panel="'),4);self.assertEqual(page.count('data-atlas-topic="'),4)
  for key in ['navigation-space','motion-manipulation','robot-learning','methods-resources']:self.assertIn('id="atlas-panel-'+key+'"',page)
  for pid in ['rpa-0062']:self.assertIn('papers/'+pid+'/index.html',page)
  self.assertIn('条匹配 · 可交叉',page);self.assertIn('书目待核验',page)
 def test_existing_preview_uses_preserved_base(self):
  page=shell('RoboPaperAtlas','<main id="main"></main>',prefix='../',page='preview')
  self.assertIn('preview-base.css?v=',page);self.assertNotIn('experience.css?v=',page);self.assertNotIn('hero-atlas.js?v=',page)
 def test_atlas_runtime_suspends_and_goes_static(self):
  js=(ROOT/'assets/hero-atlas.js').read_text()
  for marker in ['prefers-reduced-motion','max-width: 767px','document.hidden','IntersectionObserver','userPaused','cancelAnimationFrame','atlasDestroy']:
   self.assertIn(marker,js)
 def test_daily_reader_preserves_evidence_and_states(self):
  index,records=load_archive(ROOT);out=section(json.loads((ROOT/'data/brief-history/2026-09-30-v1.0.json').read_text()),index,prefix='../')
  self.assertEqual(out.count('role="tab"'),5);self.assertEqual(out.count('role="tabpanel"'),5)
  self.assertIn('基于完整摘要',out);self.assertIn('相关性判断 · 推断',out);self.assertIn('未逐版比较',out)
  js=(ROOT/'assets/brief-reader.js').read_text();self.assertIn('p.inert=!active',js);self.assertNotIn('setTimeout',js)
 def test_mobile_no_cropped_hero_figure(self):
  css=(ROOT/'assets/experience.css').read_text();self.assertNotIn('max-height:250px;overflow:hidden',css)
if __name__=='__main__':unittest.main()
