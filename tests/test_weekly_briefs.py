import copy,hashlib,json,shutil,sys,tempfile,unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from weekly_briefs import load_archive,validate_weekly,validate_snapshot,render,navigation,record_failed_attempt,home_overview
class WeeklyTests(unittest.TestCase):
 def setUp(self):
  self.index,self.records=load_archive(ROOT);self.record=copy.deepcopy(self.records['2026-10-04']);self.rows=self.record['research_overview'].pop('candidate_records');self.record.pop('candidate_ids')
 def check(self,data=None,rows=None):return validate_weekly(data or self.record,self.rows if rows is None else rows)
 def test_all_archive_records_dynamic(self):
  self.assertIn(self.index['latest'],self.records)
  for data in self.records.values():
   self.assertEqual(len(data['candidate_ids']),data['counts']['window_candidates']);self.assertEqual(data['counts']['new']+data['counts']['revisions'],data['counts']['window_candidates'])
 def test_source_coverage_and_public_contract(self):
  self.check();self.assertEqual((len(self.rows),len(self.record['research_overview']['themes']),len(self.record['research_overview']['evidence_sources'])),(238,4,11));self.assertEqual(self.record['counts']['new'],151);self.assertEqual(self.record['counts']['revisions'],87)
  text=json.dumps(self.record,ensure_ascii=False);self.assertNotIn('ReNav',text);self.assertNotIn('private',text);self.assertNotIn('abstract_excerpt',text)
 def test_count_and_source_version_mismatches_rejected(self):
  for change in [lambda d:d['counts'].update(new=True),lambda d:d['counts'].update(revisions=0),lambda d:d['research_overview']['coverage'].update(complete_abstracts_checked=10),lambda d:d['research_overview']['evidence_sources'][0].update(version_url='https://arxiv.org/abs/0000.00000v1'),lambda d:d['research_overview']['evidence_sources'][0].update(source_url='https://example.com/private'),lambda d:d['research_overview']['evidence_sources'][0].update(full_paper_read=True),lambda d:d['research_overview']['evidence_sources'][0].update(version_comparison_performed=True),lambda d:d['research_overview']['evidence_sources'][0].update(private_note='secret'),lambda d:d.update(private_note='secret')]:
   x=copy.deepcopy(self.record);change(x)
   with self.assertRaises(ValueError):self.check(x)
 def test_zero_no_material_and_failure_states(self):
  d=copy.deepcopy(self.record);d['counts']={k:0 for k in d['counts']};o=d['research_overview'];o['coverage'].update(candidate_metadata_screened=0,complete_abstracts_checked=0,count_denominator=0);o['evidence_sources']=[];o['themes']=[];o['keyword_caveats']=[]
  for t in o['topic_distribution']:t.update(count=0,new=0,revisions=0,candidate_ids=[])
  for status in ['no_material_update','error']:
   d['status']=status;self.check(d,[])
  d['status']='ready'
  with self.assertRaises(ValueError):self.check(d,[])
 def test_partial_stale_and_revision_without_diff(self):
  d=copy.deepcopy(self.record);d['source_snapshot'].update(status='limited',coverage_complete=False,coverage_truncated=True);self.check(d);page=render(self.check(d),self.index,'../../');self.assertIn('部分覆盖',page)
  old=d['window'].copy();d['status']='stale';d['generated_at']='2026-10-11T13:12:00Z';self.check(d);self.assertEqual(old,d['window']);self.assertIn('保留原始成功观察窗口',render(self.check(d),self.index,'../../'));self.assertIn('未对任何论文做版本差分',page)
 def test_window_and_manifest_paths(self):
  for change in [lambda d:d['window'].update(duration_hours=24),lambda d:d['window'].update(end='2026-10-05T12:41:03Z'),lambda d:d.update(candidate_manifest='../private.json')]:
   d=copy.deepcopy(self.record);change(d)
   with self.assertRaises(ValueError):self.check(d)
 def test_frozen_sources_survive_new_frontier_snapshot(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();shutil.copytree(ROOT/'data/weekly',root/'data/weekly');(root/'data/frontier.json').write_text('{}');self.assertEqual(len(load_archive(root)[1]['2026-10-04']['candidate_ids']),238)
 def test_integrity_unindexed_and_symlink_rejected(self):
  for kind in ['part','extra','symlink']:
   with tempfile.TemporaryDirectory() as tmp:
    root=Path(tmp);(root/'data').mkdir();shutil.copytree(ROOT/'data/weekly',root/'data/weekly');p=root/'data/weekly/2026-10-04/000.json'
    if kind=='part':p.write_text('[]')
    elif kind=='extra':(root/'data/weekly/private.json').write_text('{}')
    else:p.unlink();p.symlink_to(ROOT/'data/weekly/2026-10-04/000.json')
    with self.assertRaises(ValueError):load_archive(root)
 def test_next_week_zero_candidates_does_not_break_history(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();shutil.copytree(ROOT/'data/weekly',root/'data/weekly');base=root/'data/weekly';date='2026-10-11';d=copy.deepcopy(self.record);d.update(id='arxiv-weekly-'+date,date=date,status='no_material_update',generated_at='2026-10-11T13:00:00Z',candidate_manifest=date+'/manifest.json');d['window'].update(start='2026-10-04T12:41:03Z',end='2026-10-11T12:41:03Z');d['source_snapshot'].update(coverage_start=d['window']['start'],coverage_end=d['window']['end'],generated_at='2026-10-11T12:43:00Z',fetched_at='2026-10-11T12:42:00Z',sha256='a'*64);d['counts']={k:0 for k in d['counts']};o=d['research_overview'];o['coverage'].update(candidate_metadata_screened=0,complete_abstracts_checked=0,count_denominator=0);o.update(evidence_sources=[],themes=[],keyword_caveats=[],executive_summary='本周没有新增研究主线。')
   for t in o['topic_distribution']:t.update(count=0,new=0,revisions=0,candidate_ids=[])
   (base/date).mkdir();m=dict(schema_version='weekly-candidates-1.0',sha256=hashlib.sha256(b'[]').hexdigest(),count=0,parts=[]);mr=(json.dumps(m)+'\n').encode();(base/date/'manifest.json').write_bytes(mr);raw=(json.dumps(d,ensure_ascii=False)+'\n').encode();(base/(date+'.json')).write_bytes(raw);i=json.loads((base/'index.json').read_text());i['latest']=date;i['weeks'].append(dict(date=date,path=date+'.json',title=d['title'],status=d['status'],sha256=hashlib.sha256(raw).hexdigest(),candidate_manifest_sha256=hashlib.sha256(mr).hexdigest()));(base/'index.json').write_text(json.dumps(i));index,records=load_archive(root);self.assertEqual(records[index['latest']]['counts']['window_candidates'],0);self.assertEqual(records['2026-10-04']['counts']['window_candidates'],238);self.assertIn('本周没有新增研究主线',render(records[date],index,'../../'))
 def test_failed_attempt_preserves_success_hashes(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);(root/'data').mkdir();shutil.copytree(ROOT/'data/weekly',root/'data/weekly');before={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'data/weekly').rglob('*') if p.is_file() and p.name!='index.json'}
   record_failed_attempt(root,dict(status='error',attempted_at='2026-10-11T13:00:00Z',window_start='2026-10-04T12:41:03Z',window_end='2026-10-11T12:41:03Z',message='官方来源暂不可用'))
   after={str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/'data/weekly').rglob('*') if p.is_file() and p.name!='index.json'};self.assertEqual(before,after);i,r=load_archive(root);self.assertIn('最近周报更新失败',render(r[i['latest']],i,'../../'))
 def test_source_chronology_and_failed_no_material(self):
  for change in [lambda d:d['source_snapshot'].update(generated_at='2026-10-05T00:00:00Z'),lambda d:d['source_snapshot'].update(fetched_at='2026-10-05T00:00:00Z'),lambda d:d['research_overview']['evidence_sources'][0].update(checked_at='2026-10-05T00:00:00Z')]:
   d=copy.deepcopy(self.record);change(d)
   with self.assertRaises(ValueError):self.check(d)
  for state in ['error','stale']:
   d=copy.deepcopy(self.record);d['status']='no_material_update';d['research_overview']['themes']=[];d['source_snapshot']['status']=state
   with self.assertRaises(ValueError):self.check(d)
 def test_canonical_duplicate(self):
  rows=copy.deepcopy(self.rows);rows[1]['versioned_id']=rows[0]['versioned_id'].split('v')[0]+'v9'
  with self.assertRaises(ValueError):self.check(rows=rows)
 def test_matching_snapshot_cross_check(self):
  raw=(ROOT/'data/frontier.json').read_bytes();f=json.loads(raw);digest=hashlib.sha256(raw).hexdigest();validate_snapshot(self.record,self.rows,f,digest)
  changed=copy.deepcopy(self.rows);changed[0]['title']='Altered source title'
  with self.assertRaises(ValueError):validate_snapshot(self.record,changed,f,digest)
  with self.assertRaises(ValueError):validate_snapshot(self.record,self.rows,f,'0'*64)
  for field,value in [('query','different query'),('rule_version','different-rule'),('status','limited'),('coverage_complete',False),('coverage_start','2026-09-26T12:41:03Z')]:
   d=copy.deepcopy(self.record);d['source_snapshot'][field]=value
   with self.assertRaises(ValueError):validate_snapshot(d,self.rows,f,digest)
 def test_evidence_union_and_coverage_rejected(self):
  for change in [lambda d:d['research_overview']['themes'][0]['method_routes'][0].update(evidence_ids=[]),lambda d:d['research_overview']['themes'][0].update(evidence_ids=['0000.00000v1']),lambda d:d['source_snapshot'].update(coverage_start='2026-10-01T00:00:00Z'),lambda d:d['source_snapshot'].update(coverage_truncated=True),lambda d:d['source_snapshot'].update(status='error'),lambda d:d['research_overview']['coverage'].update(comparison_window_available=True)]:
   d=copy.deepcopy(self.record);change(d)
   with self.assertRaises(ValueError):self.check(d)
 def test_existing_three_column_css_child_contract(self):
  class Structure(HTMLParser):
   def __init__(self):super().__init__();self.stack=[];self.children={};self.targets=[]
   def handle_starttag(self,tag,attrs):
    attrs=dict(attrs);node={'tag':tag,'attrs':attrs,'children':[]}
    if self.stack:self.stack[-1]['children'].append(node)
    if tag in {'details','summary','li'}:self.targets.append(node)
    if tag not in {'link','br','meta','input','img','hr'}:self.stack.append(node)
   def handle_endtag(self,tag):
    if self.stack and self.stack[-1]['tag']==tag:self.stack.pop()
  parser=Structure();parser.feed(render(self.check(),self.index,'../../'));themes=[x for x in parser.targets if x['tag']=='details' and x['attrs'].get('class')=='radar-theme'];self.assertEqual(len(themes),4)
  for theme in themes:
   summary=theme['children'][0];self.assertEqual(summary['tag'],'summary');self.assertEqual([x['tag'] for x in summary['children']],['span','span','i']);self.assertEqual(summary['children'][1]['attrs']['class'],'radar-theme-copy')
  window=next(x for x in parser.targets if x['tag']=='details' and x['attrs'].get('class')=='radar-window-list');ul=next(x for x in window['children'] if x['tag']=='ul');self.assertEqual(len(ul['children']),238)
  for row in ul['children']:self.assertEqual([x['tag'] for x in row['children']],['span','a','small'])
 def test_home_prefers_weekly_and_compacts_empty_day(self):
  from briefs import load_archive as load_daily
  di,dr=load_daily(ROOT);di=copy.deepcopy(di);di['latest']='2026-10-04';page=home_overview(self.index,self.records,di,dr)
  self.assertIn('七天研究主线',page);self.assertIn('最近24小时没有新增候选',page);self.assertNotIn('本窗口没有需要新增的研究主题，不重复上期总结',page);self.assertIn('frontier/briefs/2026-10-04/index.html',page);self.assertIn('2026-09-27T12:41:03Z',page);self.assertIn('2026-10-04T12:41:03Z',page);self.assertIn('frontier/daily/index.html',page)
 def test_home_ready_daily_still_has_explicit_route(self):
  from briefs import load_archive as load_daily
  di,dr=load_daily(ROOT);di=copy.deepcopy(di);di['latest']='2026-09-30';page=home_overview(self.index,self.records,di,dr);self.assertIn('当天摘要已更新',page);self.assertIn('frontier/briefs/2026-09-30/index.html',page);self.assertIn('七天研究主线',page)
 def test_home_missing_or_failed_weekly_keeps_historical_window(self):
  from briefs import load_archive as load_daily
  di,dr=load_daily(ROOT);page=home_overview(None,{},di,dr);self.assertIn('历史日报',page);self.assertIn('不是当天新发现',page)
  wi=copy.deepcopy(self.index);wi['latest']='2026-10-11';wr=copy.deepcopy(self.records);failed=copy.deepcopy(wr['2026-10-04']);failed['date']='2026-10-11';failed['status']='error';failed['research_overview']['themes']=[];wr['2026-10-11']=failed;page=home_overview(wi,wr,di,dr);self.assertIn('最近周报更新未完成',page);self.assertIn('2026-09-27T12:41:03Z',page);self.assertIn('七天研究主线',page)
 def test_home_daily_failed_or_stale_is_not_zero_claim(self):
  from briefs import load_archive as load_daily
  di,dr=load_daily(ROOT);di=copy.deepcopy(di);di['latest']='2026-10-04'
  for state,label in [('error','当天更新失败'),('stale','当天更新未完成')]:
   records=copy.deepcopy(dr);records[di['latest']]['status']=state;page=home_overview(self.index,self.records,di,records);self.assertIn(label,page);self.assertNotIn('最近24小时没有新增候选',page);self.assertIn('七天研究主线',page)
 def test_build_mounts_explicit_daily_and_weekly_home(self):
  source=(ROOT/'scripts/build.py').read_text();self.assertIn('home_overview(weekly_index,weekly_records,brief_index,brief_records',source);self.assertIn("daily_folder=target/'frontier/daily'",source)
 def test_render_and_routing(self):
  page=render(self.check(),self.index,'../../../');self.assertIn('七天研究主线',page);self.assertIn('2026-09-27T12:41:03Z',page);self.assertIn('2026-10-04T12:41:03Z',page);self.assertEqual(page.count('class="radar-theme"'),4);off=copy.deepcopy(self.index);off['summary_automation_enabled']=False;on=copy.deepcopy(self.index);on['summary_automation_enabled']=True;self.assertIn('周报自动更新尚未启用',render(self.check(),off,'../../../'));self.assertIn('每周摘要更新已安排',render(self.check(),on,'../../../'));self.assertIn('frontier/weekly/index.html',navigation('../'));self.assertNotIn('ReNav',page)
if __name__=='__main__':unittest.main()
