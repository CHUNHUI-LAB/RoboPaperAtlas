"""The daily reading entry must not strand readers in an empty issue."""
import copy
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from briefs import load_archive as load_daily,section
from weekly_briefs import load_archive,daily_landing,home_overview,navigation

class RadarEntryTests(unittest.TestCase):
 def setUp(self):
  self.wi,self.wr=load_archive(ROOT);self.di,self.dr=load_daily(ROOT)
  # Fixed historical fixtures: future publications must not change this scenario.
  self.wi['latest']='2026-10-04';self.wr={k:v for k,v in self.wr.items() if k<='2026-10-04'}
  self.di['latest']='2026-10-05';self.dr={k:v for k,v in self.dr.items() if k<='2026-10-05'}
 def test_empty_daily_shows_actual_recent_themes_before_archive(self):
  before=copy.deepcopy((self.wi,self.wr,self.di,self.dr))
  page=daily_landing(self.wi,self.wr,self.di,self.dr)
  weekly=self.wr['2026-10-04'];daily=self.dr[self.di['latest']]
  self.assertIn('不是本期新增',page)
  self.assertIn(weekly['research_overview']['headline'],page)
  self.assertEqual(page.count('class="radar-theme"'),len(weekly['research_overview']['themes']))
  for record in (daily,weekly):
   self.assertIn(record['window']['start'],page);self.assertIn(record['window']['end'],page)
  self.assertIn('frontier/briefs/'+daily['date']+'/index.html',page)
  self.assertNotIn(daily['research_overview']['headline'],page)
  self.assertEqual((self.wi,self.wr,self.di,self.dr),before)
 def test_empty_daily_does_not_claim_weekly_counts_are_daily(self):
  page=daily_landing(self.wi,self.wr,self.di,self.dr)
  self.assertIn('最近24小时没有新增候选',page)
  self.assertIn('2026-10-04 / WEEKLY RESEARCH RADAR',page)
  self.assertIn('238 条候选',page)
  self.assertNotIn('2026-10-05 / WEEKLY RESEARCH RADAR',page)
 def test_daily_current_navigation_and_home_link(self):
  page=daily_landing(self.wi,self.wr,self.di,self.dr)
  self.assertEqual(page.count('aria-current="page"'),1)
  self.assertIn('frontier/daily/index.html" aria-current="page"',page)
  self.assertIn('frontier/index.html">近期研究概览',page)
  page=home_overview(self.wi,self.wr,self.di,self.dr)
  self.assertIn('frontier/index.html" aria-current="page"',page)
 def test_ready_daily_unchanged(self):
  di=copy.deepcopy(self.di);di['latest']='2026-09-30'
  self.assertEqual(daily_landing(self.wi,self.wr,di,self.dr),navigation('../../','daily')+section(self.dr[di['latest']],di,'../../',archive=True))
 def test_failed_daily_not_hidden_as_zero(self):
  for status in ('error','stale'):
   dr=copy.deepcopy(self.dr);dr[self.di['latest']]['status']=status
   self.assertEqual(daily_landing(self.wi,self.wr,self.di,dr),navigation('../../','daily')+section(dr[self.di['latest']],self.di,'../../',archive=True))
 def test_missing_weekly_falls_back_with_original_daily_date(self):
  page=daily_landing(None,{},self.di,self.dr)
  self.assertIn('历史日报',page);self.assertIn('不是当天新发现',page)
  self.assertIn('2026-10-01 / Research Radar',page)
 def test_no_material_with_candidates_does_not_claim_zero(self):
  dr=copy.deepcopy(self.dr);dr[self.di['latest']]['counts']['window_candidates']=3
  page=daily_landing(self.wi,self.wr,self.di,dr)
  self.assertNotIn('零候选记录',page)
  self.assertNotIn('没有新增候选',page)
  self.assertIn('窗口候选保留在完整日报',page)
 def test_no_usable_overview_honestly_unavailable(self):
  dr={self.di['latest']:self.dr[self.di['latest']]}
  page=daily_landing(None,{},self.di,dr)
  self.assertIn('近期研究总览暂不可用',page)
  self.assertNotIn('class="radar-theme"',page)
 def test_date_archive_preserves_zero_record(self):
  record=self.dr[self.di['latest']];page=section(record,self.di,'../../../',archive=True)
  self.assertIn(record['research_overview']['headline'],page)
  self.assertIn('0 条窗口候选',page)
  self.assertIn(record['window']['start'],page);self.assertIn(record['window']['end'],page)
 def test_build_wires_daily_landing_and_archive_overview_link(self):
  source=(ROOT/'scripts/build.py').read_text()
  self.assertIn("daily_landing(weekly_index,weekly_records,brief_index,brief_records,prefix='../../')",source)
  self.assertIn('← 返回近期研究概览',source)
  self.assertIn("radar_navigation('../../../',current='')",source)
if __name__=='__main__':unittest.main()
