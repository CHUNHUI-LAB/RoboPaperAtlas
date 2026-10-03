import json,sys,unittest,html,re,copy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from topic_labels import TOPIC_LABELS,TOPIC_HINTS,paper_topics,primary_topic,topic_counts,classification,method_tags,resource_kinds,taxonomy_search,validate_projection,validate_overlay,OVERLAY,TAXONOMY
from build import home,card,details,CATEGORIES,browse_groups
from discovery_facets import GROUPS,for_catalog,counts
from reports import load_reports
from map_page import map_data,map_html
COUNTS={'navigation':18,'mobile-manipulation':19,'wbc':20,'locomotion':2,'policy-learning':21,'spatial-representations':3,'general-ml':4,'resources':7,'cross-domain':1}
class ReviewedClassificationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.papers=cls.catalog['papers'];cls.reports=load_reports(ROOT)
 def test_labels_are_problem_axis_not_old_method_buckets(self):
  self.assertEqual(TOPIC_LABELS['wbc'],'Motion & Control');self.assertEqual(TOPIC_LABELS['mobile-manipulation'],'Mobile Manip.')
  self.assertNotIn('vla',TOPIC_LABELS);self.assertNotIn('methods',TOPIC_LABELS);self.assertEqual(set(CATEGORIES),set(COUNTS))
 def test_all_95_have_one_explicit_primary_and_remain_unchanged(self):
  before=json.dumps(self.papers,sort_keys=True)
  self.assertEqual(topic_counts(self.papers),COUNTS);self.assertEqual(sum(COUNTS.values()),95)
  for p in self.papers:self.assertEqual(len(paper_topics(p)),1);self.assertTrue(classification(p)['sources'])
  self.assertEqual(json.dumps(self.papers,sort_keys=True),before)
 def test_no_fallback_for_new_or_mismatched_paper(self):
  for p in [{'id':'unreviewed-new','category':'wbc'},dict(self.papers[0],category='vla')]:
   with self.assertRaises(ValueError):primary_topic(p)
 def test_umi_odyssey_mobile_while_deepwbc_control(self):
  by_id={p['id']:p for p in self.papers}
  for pid in ['rpa-0062','rpa-0070']:self.assertEqual(primary_topic(by_id[pid]),'mobile-manipulation')
  self.assertEqual(primary_topic(by_id['rpa-0012']),'wbc');self.assertIn('WBC',method_tags(by_id['rpa-0062']))
 def test_crossdomain_resources_not_forced_into_nav(self):
  by_id={p['id']:p for p in self.papers};self.assertEqual(primary_topic(by_id['holoagent-0']),'cross-domain');self.assertEqual(primary_topic(by_id['savva2019habitat']),'resources')
 def test_home_cards_details_map_agree(self):
  page=home(self.catalog);mapped=map_data(self.catalog,report_records=self.reports)
  groups=counts(for_catalog(self.papers,OVERLAY['records']))
  for key,label,_ in GROUPS:
   self.assertIn('data-atlas-topic="'+key+'"',page);self.assertIn('<span>'+html.escape(label)+'</span><b>'+str(groups[key]),page)
  for p,m in zip(self.papers,mapped['papers']):
   self.assertEqual(m['mapTopic'],primary_topic(p));self.assertIn('data-topics="'+' '.join(browse_groups(p))+'"',card(p))
   d=details(p);self.assertIn('研究问题与分类证据',d);self.assertIn(html.escape(classification(p)['problemLabel']),d)
 def test_evidence_does_not_promote_bibliography_or_reading(self):
  self.assertEqual(sum(p['citation_verified'] for p in self.papers),22);self.assertEqual(sum(classification(p)['needsReview'] for p in self.papers),4)
  self.assertEqual(sum(s['status']=='imported' for p in self.papers for s in p['stages'].values()),12)
  for p in self.papers:
   self.assertNotEqual(classification(p)['evidenceScope'],'catalog_title');self.assertIn('分类核查不代表全文精读',details(p))
 def test_method_resource_axes_and_search_text(self):
  page=home(self.catalog);self.assertIn('id="method-filter"',page);self.assertIn('id="resource-filter"',page)
  for p in self.papers:
   for t in method_tags(p):self.assertIn(t,taxonomy_search(p))
 def test_projection_rejects_unsafe_urls_and_method_separators(self):
  for field,value in [('sources',['javascript:alert(1)']),('resourceKinds',['unknown'])]:
   x=copy.deepcopy(TAXONOMY);next(iter(x['placements'].values()))[field]=value
   with self.assertRaises(ValueError):validate_projection(x)
  x=copy.deepcopy(TAXONOMY);next(v for v in x['placements'].values() if v['methodTags'])['methodTags'][0]['label']='a|b'
  with self.assertRaises(ValueError):validate_projection(x)
 def test_overlay_unknown_fields_and_stale_catalog_fail_closed(self):
  for mutate in [lambda x:x.update(private_note='no'),lambda x:x['records'][0].update(private_note='no'),lambda x:x.update(catalog_sha256='0'*64),lambda x:x['records'][0]['method_tags'][0].update(private_note='no')]:
   x=copy.deepcopy(OVERLAY);mutate(x)
   with self.assertRaises(ValueError):validate_overlay(x,self.papers)
 def test_frontier_discovery_tags_are_separate(self):
  from frontier_page import render
  from build import shell,link
  page=render(json.loads((ROOT/'data/frontier.json').read_text()),self.catalog,shell,link)
  self.assertIn('与 Library 中的研究问题分类分开',page);self.assertIn('value="whole_body_control"',page)
 def test_real_map_hierarchy_preserves_95_papers(self):
  data=map_data(self.catalog,report_records=self.reports);self.assertEqual(len(data['papers']),95)
  page=map_html(self.catalog,report_records=self.reports);self.assertIn('Atlas',page);self.assertIn('atlas-systems',page);self.assertEqual(page.count('data-map-paper='),95)
