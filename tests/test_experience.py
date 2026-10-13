import json,re,sys,unittest,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import home,shell,esc
from briefs import load_archive,section
class ExperienceTests(unittest.TestCase):
 def test_library_leads_with_editorial_content_then_search_and_results(self):
  data=json.loads((ROOT/'data/catalog.json').read_text());page=home(data)
  markers=['class="home-hero"','id="catalog"','id="search"','class="topic-filters"','id="catalog-results"','id="paper-grid"','class="reading-roadmap"']
  positions=[page.index(marker) for marker in markers]
  self.assertEqual(positions,sorted(positions))
  for marker in ['class="experience-hero"','class="experience-routes"']:
   self.assertNotIn(marker,page)
  self.assertIn(f'全部论文 · {len(data["papers"])} 篇',page)
  self.assertIn('data-default-view="list"',page)
  self.assertRegex(page,r'<input id="search"[^>]*type="search"')
  self.assertNotIn('data-search-trigger',page)
 def test_library_browse_controls_and_truthful_static_atlas_label(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertEqual(len(re.findall(r'data-topic="[^"]+"',page)),5)
  for key in ['navigation-space','motion-manipulation','robot-learning','methods-resources']:
   self.assertIn('data-topic="'+key+'"',page)
   self.assertIn('<option value="'+key+'">',page)
  self.assertIn('分组可交叉',page);self.assertIn('数量不可相加',page)
  self.assertNotIn('library-galaxy.webp?v=',page)
  self.assertIn('href="map/index.html"',page)
  self.assertNotIn('hero-robot',page);self.assertNotIn('robot-vignette',page)
 def test_editorial_rows_use_existing_summaries_and_real_routes(self):
  data=json.loads((ROOT/'data/catalog.json').read_text());page=home(data)
  self.assertNotIn('class="library-features"',page)
  self.assertEqual(page.count('data-classification-note='),len(data['papers']))
  self.assertNotIn('class="paper-summary"',page)
  for paper in data['papers']:
   self.assertIn('href="papers/'+paper['id']+'/index.html"',page)
   self.assertIn('data-preview="'+paper['id']+'"',page)
   if paper.get('summary'):self.assertIn(esc(paper['summary']),page)
  self.assertIn('来源核验与全文阅读分开记录',page)
 def test_library_theme_does_not_replace_other_page_themes(self):
  library=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertIn('site.css?v=',library);self.assertIn('library.js?v=',library)
  self.assertNotIn('library.css?v=',library)
  self.assertNotIn('experience.css?v=',library);self.assertNotIn('experience.js?v=',library)
  ordinary=shell('Atlas','<main id="main"></main>',prefix='../',page='map')
  self.assertIn('site.css?v=',ordinary);self.assertNotIn('library.css?v=',ordinary)
  self.assertNotIn('experience.css?v=',ordinary)
 def test_existing_preview_uses_preserved_base(self):
  page=shell('RoboPaperAtlas','<main id="main"></main>',prefix='../',page='preview')
  self.assertIn('preview-base.css?v=',page);self.assertNotIn('experience.css?v=',page);self.assertNotIn('hero-atlas.js?v=',page)
  self.assertNotIn('library.css?v=',page);self.assertNotIn('library.js?v=',page)
 def test_retained_atlas_runtime_suspends_and_goes_static(self):
  js=(ROOT/'assets/hero-atlas.js').read_text()
  for marker in ['prefers-reduced-motion','max-width: 767px','document.hidden','IntersectionObserver','userPaused','cancelAnimationFrame','atlasDestroy']:
   self.assertIn(marker,js)
 def test_daily_reader_preserves_evidence_and_states(self):
  index,records=load_archive(ROOT);out=section(json.loads((ROOT/'data/brief-history/2026-09-30-v1.0.json').read_text()),index,prefix='../')
  self.assertEqual(out.count('role="tab"'),5);self.assertEqual(out.count('role="tabpanel"'),5)
  self.assertIn('基于完整摘要',out);self.assertIn('相关性判断 · 推断',out);self.assertIn('未逐版比较',out)
  js=(ROOT/'assets/brief-reader.js').read_text();self.assertIn('p.inert=!active',js);self.assertNotIn('setTimeout',js)
 def test_editorial_visual_is_bounded_and_has_no_fake_data(self):
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertIn('content="light"',page)
  self.assertNotIn('class="library-galaxy-art"',page)
  self.assertEqual(page.count('class="paper-card library-paper"'),95)
  self.assertIn('12 份报告已导入',page)
  self.assertIn('data-star-count="840"',page)
  self.assertIn('星域为视觉示意，不表示论文引用关系',page)
  css=(ROOT/'assets/home-hero.css').read_text()
  self.assertIn('prefers-reduced-motion:reduce',css)
  self.assertIn('max-width:480px',css)
  self.assertNotIn('library-galaxy.js?v=',page)
 def test_galaxy_controller_regressions(self):
  result=subprocess.run(['node','--test','tests/test_library_galaxy.cjs'],cwd=ROOT,capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)
 def test_library_summaries_are_not_clipped_and_reduced_motion_is_explicit(self):
  css=(ROOT/'assets/site.css').read_text()
  self.assertIn('.f2-paper-description',css)
  self.assertNotIn('-webkit-line-clamp',css)
  self.assertIn('prefers-reduced-motion',css)
if __name__=='__main__':unittest.main()

