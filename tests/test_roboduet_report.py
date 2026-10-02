import copy,json,re,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
from validate import validate_catalog,expected_stage
from build import details
class RoboDuetReportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.rec=next(x for x in cls.records if x['paper_id']=='rpa-0052');cls.payload=b''.join((ROOT/r._parts_path(cls.rec)/p['file']).read_bytes()for p in cls.rec['parts']);cls.catalog=json.loads((ROOT/'data/catalog.json').read_text())
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();shutil.copyfile(ROOT/'data/report-rpa-0052-v1-policy.json',self.root/'data/report-rpa-0052-v1-policy.json')
 def test_original_stage1_identity_remains_narrow(self):
  r.split_report(self.root,self.rec,self.payload)
  for k,v in [('paper_id','rpa-0053'),('stage','stage2'),('version','v2'),('review_status','approved'),('source_url','https://example.com/paper'),('pdf_url','https://example.com/paper.pdf'),('source_sha256','0'*64)]:
   with self.subTest(k=k),self.assertRaises(ValueError):r.split_report(self.root,dict(self.rec,**{k:v}),self.payload)
 def test_registry_rehash_cannot_approve_changed_text_or_script(self):
  for changed in [self.payload.replace(b'39/60',b'40/60'),self.payload.replace(b'</body>',b'<script>alert(1)</script></body>'),self.payload.replace(b'updatePosition();',b'alert(1);',1)]:
   self.assertNotEqual(changed,self.payload)
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.rec,changed)
 def test_known_script_hash_remains_independent(self):
  payload=self.payload.replace(b'updatePosition();',b'alert(1);',1);policy=json.loads((self.root/'data/report-rpa-0052-v1-policy.json').read_text());policy['document_sha256']=r.sha(payload);(self.root/'data/report-rpa-0052-v1-policy.json').write_text(json.dumps(policy))
  with self.assertRaisesRegex(ValueError,'script'):r.split_report(self.root,self.rec,payload)
 def test_strict_guards_even_after_document_review(self):
  for inject in ['<img src="https://example.com/image.png">','<p onclick="alert(1)">bad</p>','<style>p{background:url(https://example.com/x)}</style>','<iframe src="https://example.com"></iframe>','<a href="../../../papers/rpa-0062/index.html">cross paper</a>','<a href="../v2/first-pass.html">cross version</a>']:
   payload=self.payload.replace(b'</body>',inject.encode()+b'</body>');policy=json.loads((ROOT/'data/report-rpa-0052-v1-policy.json').read_text());policy['document_sha256']=r.sha(payload);(self.root/'data/report-rpa-0052-v1-policy.json').write_text(json.dumps(policy))
   with self.subTest(inject=inject),self.assertRaises(ValueError):r.split_report(self.root,self.rec,payload)
 def test_coverage_sources_numbers_and_no_private_material(self):
  s=self.payload.decode()
  for i in range(1,13):self.assertIn(f'id="section-{i:02}"',s)
  for i in range(1,8):self.assertIn(f'id="fig-{i}"',s)
  for t in ['39/60','32/60','21.875%','11.67','23%','0.1075','98.20%','99.96%','IEEE 正式版等同性未核验','未读实现、未运行实验']:self.assertIn(t,s)
  for t in ['private-atlas','Skill','skill://','references/atlas-theme','/workspace/','<img','<iframe','v1-candidate']:self.assertNotIn(t,s)
  self.assertEqual(len(re.findall(r'<li>',s.split('id="section-11"')[1].split('</section>')[0])),5)
 def test_catalog_scope_with_all_three_reviewed_stages(self):
  self.assertEqual(validate_catalog(self.catalog,self.records),95);p=next(x for x in self.catalog['papers']if x['id']=='rpa-0052')
  self.assertFalse(p['citation_verified']);self.assertEqual(p['original_metadata']['year'],2025);self.assertEqual(p['stages']['stage1'],expected_stage('rpa-0052','stage1',self.records))
  self.assertEqual(p['stages']['stage2'],expected_stage('rpa-0052','stage2',self.records));self.assertEqual(p['stages']['stage3'],expected_stage('rpa-0052','stage3',self.records))
  page=details(p);self.assertIn('3 个已导入报告',page);self.assertIn('初读内容已审阅',page);self.assertIn('../../artifacts/rpa-0052/v1/first-pass.html',page)
 def test_original_source_not_in_artifacts(self):
  p=ROOT/'artifacts/rpa-0052';self.assertEqual(sorted(x.name for x in p.rglob('*')if x.is_file()),['first-pass.html','method-code-reading.html','writing-close-reading.html']);self.assertNotEqual(self.rec['source_sha256'],self.rec['sha256'])
if __name__=='__main__':unittest.main()
