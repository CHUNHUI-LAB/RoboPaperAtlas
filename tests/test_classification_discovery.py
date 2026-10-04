"""Regression tests for evidence-backed discovery without reclassification."""
import copy
import html
import json
import re
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import card, details, home
from catalog_search import classification_search, browse_groups
from discovery_facets import method_label
from map_page import map_data
from reports import load_reports
from topic_labels import classification, primary_topic, method_tags, TOPIC_CHINESE

class ClassificationDiscoveryTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text())
  cls.papers={p['id']:p for p in cls.catalog['papers']}
  cls.records={r['id']:r for r in json.loads((ROOT/'data/classification.json').read_text())['records']}
  cls.mapped={p['id']:p for p in map_data(cls.catalog,report_records=load_reports(ROOT))['papers']}
 def test_rl_components_add_discovery_without_changing_primary(self):
  for pid,direction in [('rpa-0050','locomotion'),('rpa-0052','wbc')]:
   p=self.papers[pid];r=self.records[pid]
   self.assertEqual(primary_topic(p),direction)
   self.assertIn('robot-learning',browse_groups(p));self.assertIn('motion-manipulation',browse_groups(p))
   self.assertEqual(method_tags(p).count('RL'),1)
   tag=next(t for t in r['method_tags'] if t['label']=='RL')
   self.assertRegex(tag['source'],r'^https://arxiv.org/html/\d{4}\.\d{4,5}v\d+#S')
   self.assertIn('2026-10-04',tag['evidence_scope']);self.assertFalse(r['full_paper_read'])
   self.assertIn('targeted component check',r['method_evidence_note'])
 def test_shared_classification_projection_covers_all_catalog_entries(self):
  before=copy.deepcopy(self.catalog)
  for pid,p in self.papers.items():
   projected=self.mapped[pid]['classificationSearch']
   self.assertEqual(projected,classification_search(p))
   self.assertIn(html.escape(projected.casefold(),quote=True),card(p))
   for tag in method_tags(p):
    self.assertIn(tag,projected);self.assertIn(method_label(tag),projected)
  self.assertEqual(before,self.catalog)
 def test_chinese_methods_render_without_mutating_canonical_tags(self):
  for pid,p in self.papers.items():
   before=copy.deepcopy(classification(p))
   for tag in method_tags(p):
    label=method_label(tag)
    self.assertEqual(self.mapped[pid]['display']['methodLabels'][tag],label)
    self.assertIn(html.escape(label),details(p))
   self.assertEqual(before,classification(p))
  self.assertEqual(method_label('Unknown future method'),'Unknown future method')
 def test_secondary_directions_are_visible_but_not_primary_filters(self):
  secondary_papers=[p for p in self.papers.values() if classification(p)['secondaryDirections']]
  self.assertTrue(secondary_papers)
  for p in secondary_papers:
   rendered=details(p)
   for direction in classification(p)['secondaryDirections']:
    self.assertIn(TOPIC_CHINESE[direction],rendered)
   self.assertIn('data-category="'+primary_topic(p)+'"',card(p))
  source=(ROOT/'assets/app.js').read_text()
  self.assertIn('c.dataset.category === direction.value',source)
  page=home(self.catalog);self.assertIn('主研究方向<select',page);self.assertNotIn('细分研究方向',page)
 def test_negative_foundation_entries_do_not_gain_robot_learning(self):
  for pid in ['rpa-0008','rpa-0018','rpa-0046','rpa-0058']:
   self.assertNotIn('robot-learning',browse_groups(self.papers[pid]))
 def test_map_projection_preserves_canonical_tags_and_stage_status(self):
  for pid,p in self.papers.items():
   m=self.mapped[pid]
   self.assertEqual(m['tags'],p['tags']);self.assertEqual(m['category'],p['category'])
   self.assertEqual(m['sourceChecked'],p['citation_verified'])
   self.assertEqual(m['topics'],[primary_topic(p)])
   for stage,value in p['stages'].items():self.assertEqual(m['stages'][stage]['status'],value['status'])
