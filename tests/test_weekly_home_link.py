"""Dated weekly entry is additive, state-honest and homepage-only."""
import copy, hashlib, sys, unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from weekly_briefs import load_archive, latest_weekly_link, home_overview, daily_landing
from briefs import load_archive as load_daily
class Links(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.active=None
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.active=[dict(attrs)['href'],'']
 def handle_data(self,text):
  if self.active is not None:self.active[1]+=text
 def handle_endtag(self,tag):
  if tag=='a' and self.active is not None:self.links.append(tuple(self.active));self.active=None
class WeeklyHomeLink(unittest.TestCase):
 def setUp(self):self.wi,self.wr=load_archive(ROOT);self.di,self.dr=load_daily(ROOT)
 def links(self,text):p=Links();p.feed(text);return p.links
 def test_ready_date_and_real_target(self):
  date=self.wi['latest']
  for prefix in ['../','../../']:
   links=self.links(latest_weekly_link(self.wi,self.wr,prefix));self.assertEqual(len(links),1)
   self.assertEqual(links[0][0],prefix+'frontier/weekly/'+date+'/index.html');self.assertIn('最新周报 · '+date,links[0][1]);self.assertTrue((ROOT/'data/weekly'/f'{date}.json').is_file())
 def test_missing_and_error(self):
  for index,records in [(None,{}),({},{}),({'latest':'2099-01-01'},self.wr)]:self.assertEqual(latest_weekly_link(index,records),'')
  wr=copy.deepcopy(self.wr);wr[self.wi['latest']]['status']='error';self.assertEqual(latest_weekly_link(self.wi,wr),'')
 def test_stale_and_no_material(self):
  for status,label in [('stale','更新未完成'),('no_material_update','无新增主线')]:
   wr=copy.deepcopy(self.wr);wr[self.wi['latest']]['status']=status;p=latest_weekly_link(self.wi,wr);self.assertIn(label,p);self.assertNotIn('最新周报',p)
 def test_failed_attempt_keeps_success_date(self):
  wi=copy.deepcopy(self.wi);wi['last_attempt']={'status':'error','attempted_at':'2099-01-01T00:00:00Z'}
  p=latest_weekly_link(wi,self.wr);self.assertIn('上次成功周报',p);self.assertIn(wi['latest'],p);self.assertNotIn('2099',p);self.assertNotIn('最新周报',p)
 def test_three_home_branches_and_daily_states_preserved(self):
  for state in ['ready','no_material_update','stale','error']:
   for themes in [True,False]:
    dr=copy.deepcopy(self.dr);current=dr[self.di['latest']];current['status']=state
    if not themes:
     for record in dr.values():record.get('research_overview',{})['themes']=[]
    before=copy.deepcopy((self.wi,self.wr,self.di,dr));plain=home_overview(None,{},self.di,dr);entry=latest_weekly_link(self.wi,self.wr)
    page=home_overview(self.wi,self.wr,self.di,dr);self.assertEqual(page.count(entry),1);self.assertEqual(page.replace(entry,''),plain);self.assertNotIn('data-radar-period="weekly"',page);self.assertEqual((self.wi,self.wr,self.di,dr),before)
 def test_daily_landing_unchanged(self):
  for state in ['ready','no_material_update','stale','error']:
   dr=copy.deepcopy(self.dr);dr[self.di['latest']]['status']=state
   self.assertEqual(daily_landing(self.wi,self.wr,self.di,dr),daily_landing(None,{},self.di,dr))
 def test_archive_bytes_and_inputs_unchanged(self):
  files=[p for d in ['data/weekly','data/briefs'] for p in (ROOT/d).rglob('*') if p.is_file()];before={p:hashlib.sha256(p.read_bytes()).hexdigest()for p in files};inputs=copy.deepcopy((self.wi,self.wr,self.di,self.dr))
  home_overview(self.wi,self.wr,self.di,self.dr);self.assertEqual((self.wi,self.wr,self.di,self.dr),inputs);self.assertEqual(before,{p:hashlib.sha256(p.read_bytes()).hexdigest()for p in files})
 def test_bad_or_mismatched_date_not_linked(self):
  wi={'latest':'../bad'};wr={'../bad':{'date':'../bad','status':'ready'}}
  with self.assertRaises(ValueError):latest_weekly_link(wi,wr)
  self.assertEqual(latest_weekly_link({'latest':'2026-10-18'},{'2026-10-18':{'date':'2026-10-11','status':'ready'}}),'')
if __name__=='__main__':unittest.main()
