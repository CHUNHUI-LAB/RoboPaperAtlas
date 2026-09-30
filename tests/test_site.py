import copy, json, sys, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from validate import validate_catalog,check_url,validate_frontier
from build import esc,details
from reports import load_reports
from validate import expected_stage
class SiteTests(unittest.TestCase):
 def setUp(self):self.data=json.loads((ROOT/'data/catalog.json').read_text());self.reports=load_reports(ROOT)
 def test_catalog(self):self.assertEqual(validate_catalog(self.data,self.reports),95)
 def test_exact_original_count(self):self.assertEqual(sum(p['original_metadata'] is not None for p in self.data['papers']),73)
 def test_no_fake_stages(self):
  for p in self.data['papers']:
   for key,s in p['stages'].items():self.assertEqual(s,expected_stage(p['id'],key,self.reports))
  self.assertEqual([p['id'] for p in self.data['papers'] if any(s['status']=='imported' for s in p['stages'].values())],['rpa-0062'] if self.reports else [])
 def test_overlay_keeps_original_unverified(self):self.assertTrue(all(not p['citation_verified'] for p in self.data['papers'] if p['original_metadata']))
 def test_ids_reject_traversal(self):
  self.data['papers'][0]['id']='../../bad'
  with self.assertRaises(ValueError):validate_catalog(self.data,self.reports)
 def test_extra_fields_rejected(self):
  self.data['papers'][0]['unapproved_field']='x'
  with self.assertRaises(ValueError):validate_catalog(self.data,self.reports)
 def test_url_schemes(self):
  for u in ['javascript:alert(1)','data:text/html,hi','http://example.org/','https://u:p@example.org/','https://127.0.0.1/x','https://localhost./','https://2130706433/','https://0x7f000001/','https://example.org/a\nb']:
   with self.subTest(u=u):
    with self.assertRaises(ValueError):check_url(u)
 def test_escaping(self):self.assertEqual(esc('<script>"'), '&lt;script&gt;&quot;')
 def test_omninav_distinct(self):self.assertEqual(len([p for p in self.data['papers'] if p['id'].startswith('omninav')]),2)
 def test_harness_fixed_version(self):self.assertTrue(next(p for p in self.data['papers'] if p['id']=='harnessvln')['pdf_url'].endswith('v3'))
 def test_publisher_priority(self):
  for rid in ['rpa-0040','omninav-amap','anderson2018r2r']:
   self.assertEqual(next(p for p in self.data['papers'] if p['id']==rid)['pdf_kind'],'publisher')
 def test_stale_frontier_builds(self):
  feed=json.loads((ROOT/'data/frontier.json').read_text()); feed['status']='stale'; feed['attempted_coverage']=feed['coverage']; feed['attempted_collection']=feed['collection']; validate_frontier(feed)
 def test_frontier(self):validate_frontier(json.loads((ROOT/'data/frontier.json').read_text()))
if __name__=='__main__':unittest.main()

class InterfaceTests(unittest.TestCase):
 def test_dialog_accessibility_markup(self):
  from build import home
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  for marker in ['<dialog id="search-dialog"','aria-labelledby="search-title"','aria-controls="main-nav"','id="active-filters"','data-view="list"']:
   self.assertIn(marker,page)
  self.assertNotIn('<section class="hero">',page)
 def test_detail_navigation_targets(self):
  paper=json.loads((ROOT/'data/catalog.json').read_text())['papers'][0]
  page=details(paper)
  for ident in ['overview','reading','versions','sources']:
   self.assertIn('id="'+ident+'"',page)
   self.assertIn('href="#'+ident+'"',page)
 def test_new_interactions_use_safe_dom(self):
  js=(ROOT/'assets/interface.js').read_text()
  self.assertNotIn('innerHTML',js)
  self.assertIn('textContent=p.title',js)
  self.assertIn('dialog.showModal()',js)
  self.assertIn("dialog.addEventListener('close'",js)

class DialogEscapeRegression(unittest.TestCase):
 def test_escape_is_explicit_and_before_arrow_navigation(self):
  js=(ROOT/'assets/interface.js').read_text()
  start=js.index("dialog.addEventListener('keydown'")
  end=js.index("document.addEventListener('keydown'",start)
  handler=js[start:end]
  self.assertIn("if(e.key==='Escape'){e.preventDefault();e.stopPropagation();dialog.close();return}",handler)
  self.assertIn("},true);",handler)
  self.assertLess(handler.index("e.key==='Escape'"),handler.index("['ArrowDown'"))

class EditorialInterfaceTests(unittest.TestCase):
 def test_single_search_entry_and_editorial_home(self):
  from build import home
  page=home(json.loads((ROOT/'data/catalog.json').read_text()))
  self.assertIn('class="experience-hero"',page)
  self.assertNotIn('id="coordinate-field"',page)
  self.assertNotIn('id="motion-toggle"',page)
  self.assertIn('<title>RoboPaperAtlas</title>',page)
  self.assertIn('class="paper-grid"',page)
  self.assertNotIn('class="catalog-sidebar"',page)
  self.assertNotIn('class="research-routes"',page)
  self.assertIn('<input id="search" type="hidden"',page)
 def test_assets_have_real_content_hash(self):
  from build import asset_url
  import hashlib
  for name in ['styles.css','app.js','interface.js','frontier.js','motion.js']:
   expected=hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest()[:12]
   self.assertEqual(asset_url('../../',name),'../../assets/'+name+'?v='+expected)
 def test_drawer_has_safe_dom_and_escape(self):
  js=(ROOT/'assets/interface.js').read_text()
  self.assertNotIn('innerHTML',js)
  self.assertIn("drawer.addEventListener('cancel'",js)
  self.assertIn('current!==requestId',js)
  self.assertIn("if(closing||!drawer.open)return",js)
  self.assertIn('drawer.getAnimations().forEach(a=>a.cancel())',js)
 def test_no_decorative_canvas_or_row_motion(self):
  js=(ROOT/'assets/motion.js').read_text()
  self.assertNotIn('requestAnimationFrame',js)
  self.assertNotIn('getContext',js)
  interface=(ROOT/'assets/interface.js').read_text()
  self.assertNotIn('drawer.animate',interface)
