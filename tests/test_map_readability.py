import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from map_page import map_data,map_html,problem_label
from atlas_taxonomy import atlas_projection
from reports import load_reports
class MapReadabilityTests(unittest.TestCase):
 def test_display_translation_does_not_change_taxonomy_or_source(self):
  catalog=json.loads((ROOT/'data/catalog.json').read_text());before=copy.deepcopy(catalog)
  taxonomy=atlas_projection(catalog['papers']);data=map_data(catalog,report_records=load_reports(ROOT))
  self.assertEqual(catalog,before)
  for old,new in zip(taxonomy['directions'],data['categories']):self.assertEqual(old,{k:v for k,v in new.items() if k!='displayLabel'})
  for old,new in zip(taxonomy['problems'],data['problems']):self.assertEqual(old,{k:v for k,v in new.items() if k!='displayLabel'})
  for p in data['papers']:self.assertEqual(p['classification'],taxonomy['placements'][p['id']])
  self.assertTrue(all(p['displayLabel']!=p['label'] for p in data['problems']))
  self.assertEqual(problem_label('Unreviewed new label'),'Unreviewed new label')
 def test_static_fallback_uses_the_same_translated_labels(self):
  catalog=json.loads((ROOT/'data/catalog.json').read_text());s=map_html(catalog,report_records=load_reports(ROOT))
  self.assertIn('具身导航<span>',s);self.assertIn('协调运动',s)
  self.assertIn('← 返回上一级',s);self.assertNotIn('← Back',s)
 def test_reading_text_and_mobile_resource_rows_have_explicit_rules(self):
  css=(ROOT/'assets/paper-map.css').read_text()
  for rule in ['.paper-map .map-list-copy strong{font-size:17px', '.paper-map .map-panel-welcome>p:not(.eyebrow),.paper-map .map-panel-summary{font-size:16px', '.paper-map .map-classification-evidence small,.paper-map .map-panel-note,.paper-map .map-original-tags-label{font-size:14px', '.paper-map .map-stage-list,.paper-map .map-resource-links{grid-template-columns:1fr}']:
   self.assertIn(rule,css)
