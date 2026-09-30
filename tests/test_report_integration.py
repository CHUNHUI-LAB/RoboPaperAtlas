import copy,hashlib,json,sys,unittest,tempfile,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from reports import load_reports,report_path,assemble_reports
from build import home,details,card,about
from validate import validate_catalog,validate_output
from map_page import map_data
class ReportIntegrationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=load_reports(ROOT);cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.paper=next(p for p in cls.catalog['papers'] if p['id']=='rpa-0062')
 def test_exact_approved_pilot(self):
  self.assertEqual(len(self.records),9);self.assertEqual({p['paper_id'] for p in self.records},{'rpa-0062'});self.assertEqual({p['stage'] for p in self.records},{'stage1','stage2','stage3'})
  self.assertEqual(validate_catalog(self.catalog,self.records),95)
 def test_unregistered_stage_cannot_publish(self):
  with self.assertRaises(ValueError):validate_catalog(self.catalog,[])
  changed=copy.deepcopy(self.catalog);next(p for p in changed['papers'] if p['id']=='rpa-0064')['stages']=self.paper['stages']
  with self.assertRaises(ValueError):validate_catalog(changed,self.records)
 def test_original_identity_and_year_preserved(self):
  self.assertEqual(self.paper['title'],'UMI on Legs: Making Manipulation Policies Mobile with Manipulation-Centric Whole-body Controllers');self.assertEqual(self.paper['bibliographic_year'],2024);self.assertEqual(self.paper['authors'],'Huy Ha 等');self.assertFalse(self.paper['citation_verified']);self.assertEqual(self.paper['publication_year'],2025);self.assertEqual(self.paper['pdf_kind'],'publisher')
 def test_actual_stage_links_and_truthful_counts(self):
  page=details(self.paper);self.assertIn('3 个已导入报告',page);self.assertNotIn('阅读报告尚未导入；本页不是',page);self.assertIn('未运行训练、仿真或硬件复现',page)
  for record in self.records:self.assertIn('../../'+report_path(record),page)
  self.assertIn('3 份阅读报告',card(self.paper));self.assertIn('3 份报告已导入',home(self.catalog));self.assertIn('当前已导入 3 份实际报告',about(3));self.assertIn('class="experience-route route-reading" href="papers/rpa-0062/index.html#reading"',home(self.catalog));self.assertIn('../papers/rpa-0062/index.html#reading',about(3))
 def test_all_other_papers_remain_unimported(self):
  for p in self.catalog['papers']:
   if p['id']=='rpa-0062':continue
   self.assertTrue(all(s=={'status':'not_imported','artifacts':[]} for s in p['stages'].values()));self.assertIn('0 个已导入报告',details(p))
 def test_actual_output_bytes_and_return_link(self):
  assemble_reports(ROOT)
  for r in self.records:
   raw=(ROOT/report_path(r)).read_bytes();self.assertEqual(len(raw),r['bytes']);self.assertEqual(hashlib.sha256(raw).hexdigest(),r['sha256'])
   if r['version']=='v1':self.assertNotEqual(r['sha256'],r['source_sha256']);self.assertIn('href="../../../papers/rpa-0062/index.html"',raw.decode())
   else:self.assertEqual(r['sha256'],r['source_sha256']);self.assertIn('href="https://chunhui-lab.github.io/RoboPaperAtlas/papers/rpa-0062/index.html"',raw.decode())
 def test_output_hash_and_allowlist_are_enforced(self):
  assemble_reports(ROOT)
  with tempfile.TemporaryDirectory() as d:
   output=Path(d);paper=output/'papers/rpa-0062/index.html';paper.parent.mkdir(parents=True);paper.write_text('<html><body>Paper</body></html>')
   for r in self.records:
    path=report_path(r);dest=output/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
   self.assertEqual(validate_output(output,self.records),10)
   changed=output/report_path(self.records[0]);changed.write_bytes(changed.read_bytes()+b' ')
   with self.assertRaises(ValueError):validate_output(output,self.records)
 def test_stage3_narrow_wrap_is_presentation_only(self):
  records={r['stage']:r for r in self.records if r['version']=='v1'}
  self.assertEqual(records['stage1']['sha256'],'2f1e5842f3aabc71f1fb7ab41bc82636f86a2a1dd9ac35e337853b9768c00702');self.assertEqual(records['stage2']['sha256'],'7eee3ea784be422b06ca6e357a48b947181fe50109b2530218f4304fe54ba3be')
  html=(ROOT/report_path(records['stage3'])).read_text();self.assertIn('@media(max-width:860px){.article p,.article li{overflow-wrap:anywhere}}',html);self.assertIn('overflow:auto',html)
 def test_map_stage_projection(self):
  projection=map_data(self.catalog,report_records=self.records);p=next(x for x in projection['papers'] if x['id']=='rpa-0062')
  for k in ['stage1','stage2','stage3']:self.assertEqual(p['stages'][k]['status'],'imported');self.assertEqual(len(p['stages'][k]['artifacts']),3)
if __name__=='__main__':unittest.main()
