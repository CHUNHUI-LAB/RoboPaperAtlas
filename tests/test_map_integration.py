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
  payload=json.dumps([p for p in self.catalog['papers'] if p['id']!='rpa-0062'],ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
  self.assertEqual(hashlib.sha256(payload).hexdigest(),'80641f528508872deb788c59e6957121766c363e1ff5b1a60611f79941cf742b')
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
