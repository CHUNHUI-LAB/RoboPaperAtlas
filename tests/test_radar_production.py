import json,hashlib,sys,tempfile,unittest,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from briefs import load_archive,section
from brief_history import load,DIGEST,RELATIVE,build as build_history
from frontier_page import render
from build import shell,link
class RadarProductionTests(unittest.TestCase):
 def test_current_radar_promotes_accepted_overview_first(self):
  index,records=load_archive(ROOT);data=records[index['latest']];self.assertEqual(data['schema_version'],'1.1')
  content=section(data,index,prefix='../');page=render(json.loads((ROOT/'data/frontier.json').read_text()),json.loads((ROOT/'data/catalog.json').read_text()),shell,link,content,overview=True)
  self.assertNotIn('class="frontier-heading"',page);self.assertLess(page.index('class="radar-lead"'),page.index('class="frontier-grid"'))
  self.assertEqual(page.count('data-radar-candidate data-search='),42);self.assertEqual(page.count('class="frontier-card"'),253)
  self.assertIn('每日摘要更新已安排',page);self.assertNotIn('新的概览尚未接入',page)
  self.assertIn('../frontier/briefs/2026-09-30/index.html',page);self.assertIn('../frontier/briefs/2026-09-30/v1/index.html',page)
 def test_initial_published_snapshot_is_exact_and_readable(self):
  old=load(ROOT);self.assertEqual(old['schema_version'],'1.0');self.assertEqual(hashlib.sha256((ROOT/RELATIVE).read_bytes()).hexdigest(),DIGEST)
  index,_=load_archive(ROOT);out=section(old,index,prefix='../../../../',archive=True)
  self.assertEqual(out.count('role="tabpanel"'),5)
 def test_historical_input_cannot_be_changed_or_redirected(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);p=root/RELATIVE;p.parent.mkdir(parents=True);shutil.copyfile(ROOT/RELATIVE,p);self.assertEqual(load(root)['schema_version'],'1.0')
   p.write_bytes(p.read_bytes()+b' ')
   with self.assertRaises(ValueError):load(root)

class HistoricalPresentationTests(unittest.TestCase):
 def test_history_footer_and_current_link_are_truthful(self):
  index,_=load_archive(ROOT)
  with tempfile.TemporaryDirectory()as tmp:
   build_history(ROOT,Path(tmp),shell,index)
   page=(Path(tmp)/'frontier/briefs/2026-09-30/v1/index.html').read_text()
   self.assertNotIn('以下为最后一次发布内容',page)
   self.assertIn('历史摘要快照，不代表当前版本',page)
   self.assertIn('../../../../data/brief-history/2026-09-30-v1.0.json',page)
   self.assertNotIn('frontier/briefs/2026-09-30/index.html" aria-current="page"',page)
   self.assertEqual((Path(tmp)/RELATIVE).read_bytes(),(ROOT/RELATIVE).read_bytes())
