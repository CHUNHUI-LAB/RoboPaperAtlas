import unittest,json,copy,sys,hashlib,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from briefs import validate_brief,load_archive,section
from radar_overview import validate_overview,validate_snapshot,render
class RadarOverviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'data/radar-preview/2026-09-30.json').read_text());cls.old=json.loads((ROOT/'data/briefs/2026-09-30.json').read_text());cls.index=json.loads((ROOT/'data/briefs/index.json').read_text());cls.raw=(ROOT/'data/frontier.json').read_bytes();cls.feed=json.loads(cls.raw)
 def reject(self,fn):
  d=copy.deepcopy(self.data);fn(d)
  with self.assertRaises((ValueError,TypeError,KeyError)):validate_brief(d)
 def test_version10_and_archive_backward_compatibility(self):
  validate_brief(self.old);load_archive(ROOT);html=section(self.old,self.index)
  self.assertIn('本期摘要速览',html);self.assertNotIn('research-overview',html);self.assertEqual(self.old['schema_version'],'1.0')
  x=copy.deepcopy(self.old);x['research_overview']=self.data['research_overview']
  with self.assertRaises(ValueError):validate_brief(x)
 def test_preview_integrity_and_coverage(self):
  validate_brief(self.data);validate_snapshot(self.data,self.feed,hashlib.sha256(self.raw).hexdigest())
  o=self.data['research_overview'];self.assertEqual(len(o['candidate_records']),42);self.assertEqual(len(o['evidence_sources']),14)
  self.assertEqual(len({v for t in o['themes']for v in t['evidence_ids']}),13)
  self.assertEqual(self.data['counts']['complete_abstracts_checked_for_selection'],6)
 def test_boolean_counts_rejected(self):
  self.reject(lambda d:d['research_overview']['coverage'].update(count_denominator=True))
  self.reject(lambda d:d['research_overview']['topic_distribution'][0].update(count=True))
 def test_unknown_fields_rejected_at_each_boundary(self):
  paths=[lambda d:d['research_overview'],lambda d:d['research_overview']['coverage'],lambda d:d['research_overview']['themes'][0],lambda d:d['research_overview']['themes'][0]['method_routes'][0],lambda d:d['research_overview']['evidence_sources'][0],lambda d:d['research_overview']['candidate_records'][0]]
  for get in paths:
   with self.subTest(path=get):self.reject(lambda d:get(d).update(private_note='no'))
 def test_missing_duplicate_and_out_of_window_source_rejected(self):
  self.reject(lambda d:d['research_overview']['themes'][0]['evidence_ids'].append('9999.99999v1'))
  self.reject(lambda d:d['research_overview']['evidence_sources'].append(d['research_overview']['evidence_sources'][0]))
  self.reject(lambda d:d['research_overview']['candidate_records'][0].update(updated_at='2026-09-28T00:00:00Z'))
 def test_source_urls_versions_and_hashes_rejected(self):
  self.reject(lambda d:d['research_overview']['evidence_sources'][0].update(version_url='javascript:alert(1)'))
  self.reject(lambda d:d['research_overview']['evidence_sources'][0].update(source_url='https://arxiv.org/abs/0000.00000'))
  self.reject(lambda d:d['research_overview']['evidence_sources'][0].update(abstract_sha256='unknown'))
  self.reject(lambda d:d['research_overview']['evidence_sources'][0].update(abstract_chars=0))
 def test_no_fulltext_replication_or_trend_scope_in_11(self):
  self.reject(lambda d:d['research_overview']['coverage'].update(full_papers_read=1))
  self.reject(lambda d:d['research_overview']['coverage'].update(comparison_window_available=True))
  self.reject(lambda d:d['research_overview']['themes'][0].update(comparison_scope='field_wide_trend'))
  self.reject(lambda d:d['research_overview']['evidence_sources'][0].update(experiments_independently_verified=True))
 def test_distribution_exact_membership_and_new_revision_count(self):
  self.reject(lambda d:d['research_overview']['topic_distribution'][0].update(count=99))
  self.reject(lambda d:d['research_overview']['topic_distribution'][0]['candidate_ids'].append(d['research_overview']['topic_distribution'][0]['candidate_ids'][0]))
  self.reject(lambda d:d['research_overview']['topic_distribution'][0].update(new=0,revisions=3))
 def test_metadata_checked_against_actual_snapshot(self):
  d=copy.deepcopy(self.data);d['research_overview']['candidate_records'][0]['title']='Invented title'
  with self.assertRaises(ValueError):validate_snapshot(d,self.feed,hashlib.sha256(self.raw).hexdigest())
  with self.assertRaises(ValueError):validate_snapshot(self.data,self.feed,'0'*64)
 def test_caveats_are_window_scoped_and_not_silent_count_edits(self):
  o=self.data['research_overview'];self.assertEqual(len(o['keyword_caveats']),2)
  self.reject(lambda d:d['research_overview']['keyword_caveats'][0].update(issue='missed_match'))
  self.reject(lambda d:d['research_overview']['keyword_caveats'][0].update(evidence_basis='complete_abstract'))
  html=render(self.data,self.index,preview=True,prefix='../');self.assertIn('ContactExplorer',html);self.assertIn('InsightMap',html);self.assertIn('导航标签属于误匹配',html)
 def test_no_jargon_or_unsupported_human_feedback(self):
  o=self.data['research_overview'];text=json.dumps(o,ensure_ascii=False)
  self.assertNotIn('人工纠正',text);self.assertNotIn('人的纠正',text);self.assertNotIn('恢复信用',text);self.assertIn('纠正反馈',text);self.assertIn('估计动作对任务进展的贡献',text)
 def test_theme_routes_union_and_distinct_selection_scope(self):
  self.reject(lambda d:d['research_overview']['themes'][0]['method_routes'][0].update(evidence_ids=[]))
  self.reject(lambda d:d['research_overview']['themes'][0].update(evidence_ids=d['research_overview']['themes'][0]['evidence_ids'][:-1]))
  html=render(self.data,self.index,preview=True,prefix='../')
  self.assertLess(html.index('radar-editorial'),html.index('radar-window-counts'));self.assertLess(html.index('本期研究主线'),html.index('可进一步展开的摘要'))
  self.assertEqual(html.count('data-radar-candidate '),42);self.assertNotIn('role="tab"',html)
 def test_xss_escaping_in_editorial_fields(self):
  d=copy.deepcopy(self.data);d['research_overview']['themes'][0]['summary']='<img src=x onerror=alert(1)>'
  html=render(d,self.index,preview=True,prefix='../');self.assertNotIn('<img src=x',html);self.assertIn('&lt;img src=x',html)
 def test_no_material_error_and_stale_statuses(self):
  for status in ['no_material_update','error','stale']:
   d=copy.deepcopy(self.data);d['status']=status
   if status!='stale':
    d['new_papers']=[];d['revised_papers']=[];d['reading_priority']=[];d['counts']['selected_new']=0;d['counts']['selected_revisions']=0;d['research_overview']['themes']=[]
   validate_brief(d);html=render(d,self.index,preview=True,prefix='../');self.assertIn('class="radar-state"',html);self.assertLess(html.index('class="radar-state"'),html.index('class="radar-lead"'))
 def test_11_archive_is_self_contained_after_snapshot_changes(self):
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);(root/'data/briefs').mkdir(parents=True);raw=json.dumps(self.data,ensure_ascii=False).encode();(root/'data/briefs/2026-09-30.json').write_bytes(raw)
   index=copy.deepcopy(self.index);index['briefs'][0]['sha256']=hashlib.sha256(raw).hexdigest();(root/'data/briefs/index.json').write_text(json.dumps(index))
   (root/'data/frontier.json').write_text('{"papers":[]}')
   _,records=load_archive(root);self.assertEqual(records['2026-09-30']['schema_version'],'1.1')
 def test_historical_preview_does_not_block_a_later_daily_snapshot(self):
  from radar_preview import load
  with tempfile.TemporaryDirectory()as directory:
   root=Path(directory);(root/'data/radar-preview').mkdir(parents=True);shutil.copyfile(ROOT/'data/radar-preview/2026-09-30.json',root/'data/radar-preview/2026-09-30.json');(root/'data/frontier.json').write_text('{"papers":[]}')
   self.assertEqual(load(root)['counts']['window_candidates'],42)
 def test_production_11_links_archive_data_not_preview_path(self):
  html=section(self.data,self.index,prefix='../',archive=True);self.assertIn('../data/briefs/2026-09-30.json',html);self.assertNotIn('../data/radar-preview/',html);self.assertNotIn('新的概览尚未接入',html)
if __name__=='__main__':unittest.main()
