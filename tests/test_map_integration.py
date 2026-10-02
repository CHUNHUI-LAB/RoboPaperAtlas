import hashlib
import json
import re
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import shell,details,asset_url
from map_page import map_html,map_data
from reports import load_reports

class MapIntegrationTests(unittest.TestCase):
 def setUp(self):self.catalog=json.loads((ROOT/'data/catalog.json').read_text())
 def test_map_route_uses_same_shell_with_isolated_hashed_assets(self):
  body=map_html(self.catalog,css=asset_url('../','paper-map.css'),js=asset_url('../','paper-map.js'),report_records=load_reports(ROOT))
  page=shell('论文地图',body,prefix='../',page='map')
  self.assertIn('<title>RoboPaperAtlas</title>',page)
  self.assertIn('class="page-map"',page)
  self.assertIn('href="../map/index.html" aria-current="page"',page)
  self.assertIn('assets/experience.css?v=',page)
  self.assertIn('assets/paper-map.css?v=',page)
  self.assertIn('assets/paper-map.js?v=',page)
  self.assertNotIn('assets/hero-atlas.js',page)
  self.assertEqual(page.count('id="main"'),1)
 def test_detail_returns_to_selected_map_paper(self):
  for paper in self.catalog['papers']:
   page=details(paper)
   self.assertIn(f'../../map/index.html?paper={paper["id"]}',page)
 def test_nonpilot_catalog_records_unchanged(self):
  # Normalize reviewed Deep WBC and RoboDuet imports, then pin all unrelated fields.
  deep=next(p for p in self.catalog['papers'] if p['id']=='rpa-0012')
  self.assertEqual(deep['stages']['stage1']['status'],'imported')
  deep['stages']['stage1']={'status':'not_imported','artifacts':[]}
  deep['stages']['stage2']={'status':'not_imported','artifacts':[]}
  deep['stages']['stage3']={'status':'not_imported','artifacts':[]}
  robo=next(p for p in self.catalog['papers'] if p['id']=='rpa-0052')
  self.assertEqual(robo['stages']['stage1']['status'],'imported')
  robo['stages']['stage1']={'status':'not_imported','artifacts':[]}
  self.assertEqual(robo['stages']['stage2']['status'],'imported')
  robo['stages']['stage2']={'status':'not_imported','artifacts':[]}
  self.assertEqual(robo['stages']['stage3']['status'],'imported')
  robo['stages']['stage3']={'status':'not_imported','artifacts':[]}
  robo['verified_overlay']['verification_scope']='已核验出版方书目与官方来源，尚未开展全文精读或复现。'
  # Normalize the separately tested single-paper formal RoLoMa overlay.
  roloma=next(p for p in self.catalog['papers'] if p['id']=='rpa-0054')
  self.assertEqual(roloma['stages']['stage1']['status'],'imported')
  original=json.loads((ROOT/'tests/fixtures/roloma-before-registration.json').read_text())
  roloma.clear();roloma.update(original)
  payload=json.dumps([p for p in self.catalog['papers'] if p['id']!='rpa-0062'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
  self.assertEqual(hashlib.sha256(payload).hexdigest(),'efa2b769f740904ccac886cf8a5b0f821bc7184b1539451946d37490ad9dfb66')
 def test_verified_force_control_author_preserves_original(self):
  paper=next(p for p in self.catalog['papers'] if p['id']=='rpa-0026')
  self.assertEqual(paper['authors'],'Tomás Portela 等')
  self.assertEqual(paper['verified_overlay']['authors'][0],'Tifanny Portela')
  self.assertEqual(paper['doi'],'10.1109/ICRA57147.2024.10611066')
 def test_no_frontier_candidates_mixed_into_map(self):
  data=map_data(self.catalog,report_records=load_reports(ROOT));self.assertEqual(len(data['papers']),95)
  frontier=json.loads((ROOT/'data/frontier.json').read_text());self.assertEqual(len(frontier['papers']),frontier['coverage']['displayed_entries'])
  self.assertEqual({p['id'] for p in data['papers']},{p['id'] for p in self.catalog['papers']})
  self.assertTrue({p['canonical_id'] for p in frontier['papers']}.isdisjoint({p['id'] for p in data['papers']}))
  brief=json.loads((ROOT/'data/briefs/2026-09-30.json').read_text());self.assertEqual(len(brief['new_papers'])+len(brief['revised_papers']),5)
  index=json.loads((ROOT/'data/briefs/index.json').read_text());self.assertTrue(index['summary_automation_enabled'])
 def test_all_source_links_are_static_and_no_report_fabrication(self):
  text=(ROOT/'assets/paper-map.js').read_text()
  self.assertNotIn('innerHTML',text)
  self.assertNotIn('fetch(',text)
  self.assertIn('button.disabled = true',text)
  self.assertIn('shared-tags-inferred',text)
  self.assertNotIn('data-citation-count',text)
 def test_current_build_script_writes_standalone_map(self):
  script=(ROOT/'scripts/build.py').read_text()
  self.assertIn("(target/'map/index.html').write_text",script)
  self.assertIn("('map','map/index.html','Atlas')",script)
