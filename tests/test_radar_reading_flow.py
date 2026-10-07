"""Rendering/state contracts only. Real-browser first-screen QA is separate."""
import copy,json,sys,unittest,subprocess
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from briefs import load_archive,section
from weekly_briefs import load_archive as load_weekly,home_overview,render as weekly_render
class ReadingFlowTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.di,cls.dr=load_archive(ROOT);cls.wi,cls.wr=load_weekly(ROOT)
 def test_home_latest_daily_not_weekly(self):
  page=home_overview(self.wi,self.wr,self.di,self.dr);current=self.dr[self.di['latest']]
  self.assertIn('data-radar-period="daily"',page);self.assertIn(current['research_overview']['headline'],page)
  self.assertNotIn('data-radar-period="weekly"',page);self.assertIn('frontier/weekly/index.html',page)
 def test_stable_complete_navigation_and_no_default_expansion(self):
  for data,index,renderer in [(self.dr['2026-10-07'],self.di,section),(self.wr['2026-10-04'],self.wi,weekly_render)]:
   page=renderer(data,index,'../../../');themes=data['research_overview']['themes']
   self.assertEqual(page.count('class="radar-theme-choice"'),len(themes));self.assertNotIn('class="radar-theme" open',page)
   for theme in themes:
    self.assertIn('id="theme-'+theme['id']+'"',page);self.assertIn('data-theme="'+theme['id']+'"',page)
    self.assertIn(theme['summary'],page);self.assertIn(theme['shared_problem'],page);self.assertIn(theme['open_question'],page)
 def test_single_paper_identity_and_honest_selection_depth(self):
  data=self.dr['2026-10-07'];before=copy.deepcopy(data);page=section(data,self.di)
  self.assertEqual(page.count('class="radar-paper"'),24);self.assertEqual(page.count('data-radar-selection'),5)
  for row in data['research_overview']['candidate_records']:
   vid=row['versioned_id'];self.assertEqual(page.count('id="paper-'+vid+'"'),1);self.assertIn('href="https://arxiv.org/abs/'+vid+'"',page)
  self.assertIn('未保存独立摘要速览',page);self.assertEqual(data,before)
 def test_all_content_and_data_boundaries_retained(self):
  data=self.dr['2026-10-07'];page=section(data,self.di)
  for theme in data['research_overview']['themes']:
   for route in theme['method_routes']:self.assertIn(route['text'],page)
  for item in data['new_papers']+data['revised_papers']:
   for field in ['problem','author_proposal','relevance','evidence_limit']:self.assertIn(item[field],page)
  self.assertIn(data['research_overview']['executive_summary'],page);self.assertIn(data['source_snapshot']['sha256'],page)
  self.assertIn('0 / 0',page);self.assertEqual(page.count('data-radar-candidate data-search='),24)
 def test_state_dom_regressions(self):
  run=subprocess.run(['node',str(ROOT/'tests/test_radar_reading_flow.cjs')],capture_output=True,text=True,timeout=90)
  self.assertEqual(run.returncode,0,run.stdout+run.stderr)
if __name__=='__main__':unittest.main()
