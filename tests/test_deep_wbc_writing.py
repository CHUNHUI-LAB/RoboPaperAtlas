"""Content-reviewed Stage 2 candidate; exact quotes and stage-scoped security."""
import copy,hashlib,json,re,shutil,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
from report_deep_wbc import WRITING_UNIT_IDS
from build import details
from test_reports import metadata,html

class DeepWBCWritingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if x['paper_id']=='rpa-0012' and x['stage']=='stage2')
  cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/'data/report-rpa-0012-stage2-v1-policy.json').read_text())
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir()
  (self.root/'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[]}));self.write_policy(self.policy)
 def write_policy(self,policy):(self.root/'data/report-rpa-0012-stage2-v1-policy.json').write_text(json.dumps(policy))
 def test_exact_frozen_quotes_creator_credit_license_and_public_identity(self):
  quotes=re.findall(r'<blockquote[^>]*>.*?</blockquote>',self.text,re.S)
  self.assertEqual(len(quotes),45);self.assertEqual(hashlib.sha256('\n'.join(quotes).encode()).hexdigest(),'49cf3224558973b6f9577a0a5f00d5bdc4ceeedc63fde7a0e9bc03b95337982b')
  self.assertEqual(r.sha(self.raw),'c1bba5cba6a489dd309d58a660131a6a1281e798fccb72bf2bcbcefa0bb9daa4')
  for t in ['ckyFi9zero','CHUNHUI-LAB','https://creativecommons.org/licenses/by/4.0/','https://proceedings.mlr.press/pmlr-license-agreement.html','写作内容已审阅']:self.assertIn(t,self.text)
  for t in ['references/atlas-theme.md','private-atlas','name="generator"']:self.assertNotIn(t,self.text)
 def test_all45_units_exactly_present_and_script_stays_pinned(self):
  p=r._parse_html(self.record,self.raw,ROOT);self.assertEqual(p.source_rows,WRITING_UNIT_IDS);self.assertEqual(p.quote_count,45)
  self.assertEqual(self.policy['script_sha256'],'d6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
  self.assertEqual(self.record['source_sha256'],'96751c541e226404e10820771bd26dc97ced5770fe30520e3bba6db78743536b')
 def test_same_version_filename_does_not_collide_across_papers(self):
  umi=r.split_report(self.root,metadata('stage2'),html('<h1>UMI writing fixture</h1>'));deep=r.split_report(self.root,self.record,self.raw)
  (self.root/'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[umi,deep]}));r.assemble_reports(self.root)
  self.assertEqual((self.root/r.report_path(deep)).read_bytes(),self.raw);self.assertEqual((self.root/r.report_path(umi)).read_bytes(),html('<h1>UMI writing fixture</h1>'))
 def test_stage2_v2_stage3_wrong_identity_and_source_remain_closed(self):
  for k,v in [('version','v2'),('stage','stage3'),('paper_id','rpa-0062'),('filename','first-pass.html'),('review_status','approved'),('source_url','https://proceedings.mlr.press/v270/ha25a.html')]:
   rec=dict(self.record);rec[k]=v
   with self.subTest(field=k),self.assertRaises(ValueError):r.split_report(self.root,rec,self.raw)
 def test_mutated_quote_title_or_script_cannot_pass_document_policy(self):
  for a,b in [(b'lang="en"',b'lang="zh"'),(b'updatePosition();',b'alert(1);'),(b'<title>',b'<title>Other paper ')]:
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,self.raw.replace(a,b,1))
 def test_strict_parser_rejects_active_html_and_missing_units_even_if_document_hash_changes(self):
  bad=[self.raw.replace(b'</body>',x+b'</body>') for x in [b'<script>alert(1)</script>',b'<img src="https://example.com/img.png">',b'<style>p{background:url(https://example.com/x)}</style>',b'<p onclick="alert(1)">x</p>',b'<a href="../v2/writing-close-reading.html">x</a>']]
  bad += [self.raw.replace(b'data-source-row="A1"',b'data-source-row="A2"',1),self.raw.replace(b'data-source-row="A1"',b'data-source-row="UNKNOWN"',1),re.sub(rb'<blockquote[^>]*>.*?</blockquote>',b'',self.raw,count=1,flags=re.S)]
  for payload in bad:
   policy=dict(self.policy);policy['document_sha256']=r.sha(payload);self.write_policy(policy)
   with self.assertRaises(ValueError):r.split_report(self.root,self.record,payload)
 def test_prior_bytes_and_disabled_link_in_immutable_stage2_preserved(self):
  stage1=[x for x in self.records if x['paper_id']=='rpa-0012' and x['stage']=='stage1'];self.assertEqual({x['version']:x['sha256'] for x in stage1},{'v1':'d2d80d400328afe4adac2e94d4761ce87d51dcdb000c5bd7e5bca22e3be357b1','v2':'70c9a4ceb870685d2e332305d9a2906756185ef4a2ae0f94e62a93bafc9e3950'})
  paper=next(x for x in json.loads((ROOT/'data/catalog.json').read_text())['papers'] if x['id']=='rpa-0012');page=details(paper)
  self.assertEqual(paper['stages']['stage3']['status'],'imported');self.assertEqual(page.count('class="unavailable"'),0)
  self.assertIn('初读内容已审阅',page);self.assertIn('写作内容已审阅',page);self.assertIn('../../artifacts/rpa-0012/v1/writing-close-reading.html',page)
  self.assertIn('https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0012/v2/first-pass.html',self.text)
  self.assertIn('<span aria-disabled="true" title="此阶段报告尚未提供"><small>03</small>方法与代码</span>',self.text)

if __name__=='__main__':unittest.main()
