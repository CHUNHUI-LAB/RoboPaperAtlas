import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from topic_labels import TOPIC_LABELS,TOPIC_HINTS,paper_topics,primary_topic,topic_counts,FOUNDATION_FACETS
from build import home,card,details,CATEGORIES
from reports import load_reports
from map_page import map_data,map_html

class TopicLabelsTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text())
  cls.reports=load_reports(ROOT)
 def test_short_labels_stable_ids(self):
  self.assertEqual(TOPIC_LABELS,{'navigation':'Embodied Nav','wbc':'WBC','vla':'VLA','methods':'Methods','sim-tools':'Sim & Tools','data-benchmarks':'Data & Benchmarks'})
  self.assertEqual(set(CATEGORIES),set(TOPIC_LABELS))
  self.assertEqual([v[0] for v in CATEGORIES.values()],list(TOPIC_LABELS.values()))
 def test_home_and_catalog_share_labels_and_bilingual_hints(self):
  page=home(self.catalog)
  for key,label in TOPIC_LABELS.items():
   self.assertIn('data-atlas-topic="'+key+'"',page)
   self.assertIn('title="'+TOPIC_HINTS[key].replace('&','&amp;')+'"',page)
   self.assertIn('>'+label+'<small>',page)
   self.assertIn('<span>'+label+'</span><b>',page)
 def test_map_projection_keeps_full_names_and_chinese(self):
  data=map_data(self.catalog,report_records=self.reports)
  for c in data['categories']:
   self.assertEqual(c['label'],TOPIC_LABELS[c['id']]);self.assertTrue(c['english']);self.assertTrue(c['chinese'])
 def test_detail_preserves_full_topic_meaning(self):
  for key in TOPIC_LABELS:
   paper=next(p for p in self.catalog['papers'] if primary_topic(p)==key)
   page=details(paper)
   self.assertIn('class="detail-topic-description"',page)
   self.assertIn(TOPIC_HINTS[key].replace('&','&amp;'),page)
 def test_galaxy_has_real_stars_no_grid_or_fake_relations(self):
  page=map_html(self.catalog,report_records=self.reports)
  self.assertIn('map-nebula',page);self.assertIn('map-star-glow',page);self.assertNotIn('map-dot-grid',page)
  self.assertIn('星云辉光仅为背景',page);self.assertIn('不是引用或方法继承',page)
  self.assertEqual(page.count('data-map-paper='),95)

class PresentationFacetIntegrityTests(unittest.TestCase):
 def setUp(self):self.papers=json.loads((ROOT/'data/catalog.json').read_text())['papers']
 def test_all_foundation_records_have_explicit_mapping_and_no_extras(self):
  self.assertEqual({p['id'] for p in self.papers if p['category']=='foundations'},set(FOUNDATION_FACETS))
  self.assertEqual(len(FOUNDATION_FACETS),31)
 def test_original_categories_and_tags_are_unchanged_by_facets(self):
  before=json.dumps(self.papers,ensure_ascii=False,sort_keys=True)
  for p in self.papers:self.assertTrue(paper_topics(p));self.assertIn(primary_topic(p),TOPIC_LABELS)
  self.assertEqual(json.dumps(self.papers,ensure_ascii=False,sort_keys=True),before)
 def test_overlap_counts_match_all_surfaces_without_extra_stars(self):
  self.assertEqual(topic_counts(self.papers),{'navigation':26,'wbc':31,'vla':17,'methods':17,'sim-tools':8,'data-benchmarks':13})
  self.assertEqual({t:sum(primary_topic(p)==t for p in self.papers)for t in TOPIC_LABELS},{'navigation':16,'wbc':31,'vla':17,'methods':13,'sim-tools':7,'data-benchmarks':11})
 def test_ambiguous_records_keep_multiple_facets(self):
  expected={'rpa-0017':{'sim-tools','data-benchmarks'},'rpa-0044':{'data-benchmarks','methods'},'rpa-0053':{'data-benchmarks','sim-tools'},'savva2019habitat':{'sim-tools','navigation','data-benchmarks'},'krantz2020vlnce':{'data-benchmarks','navigation','methods'},'krantz2023ivln':{'data-benchmarks','navigation','methods'}}
  for pid,facets in expected.items():self.assertEqual(set(FOUNDATION_FACETS[pid]),facets)
 def test_unknown_new_foundation_record_requires_explicit_review(self):
  with self.assertRaises(ValueError):paper_topics({'id':'unreviewed-new','category':'foundations'})

 def test_frontier_keeps_query_tags_distinct_from_display_facets(self):
  from frontier_page import render
  from build import shell,link
  feed=json.loads((ROOT/'data/frontier.json').read_text());page=render(feed,{'papers':self.papers},shell,link)
  self.assertIn('候选查询标签',page)
  self.assertIn('与论文目录的六个展示主题分开',page)
  self.assertIn('value="whole_body_control"',page)
  self.assertIn('value="navigation_agents"',page)
  self.assertNotIn('value="sim-tools"',page)

 def test_preserved_preview_does_not_deny_live_umi_reports(self):
  from design_preview import render
  from build import shell,card,asset_url
  page=render({'papers':self.papers},shell,card,asset_url)
  self.assertIn('HarnessVLN 示例的三个阶段均未导入',page)
  self.assertIn('UMI-on-Legs 已有三阶段报告',page)
  self.assertNotIn('阅读报告仍未导入',page)
