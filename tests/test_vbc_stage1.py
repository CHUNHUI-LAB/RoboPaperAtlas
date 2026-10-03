"""One formal VBC first reading; nineteen prior records and 94 catalog peers frozen."""
import base64, hashlib, json, re, subprocess, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import current_reader as current
from report_vbc_stage1 import IDENTITY,POLICY_PATH,SECTION_IDS,EVIDENCE_IDS,FIGURE_IDS,IMAGE_HASHES
from validate import expected_stage,validate_catalog
from build import details,home

FROZEN=json.loads((ROOT/'tests/fixtures/reports-before-vbc-stage1.json').read_text())
RECORDS_FROZEN=json.loads((ROOT/'tests/fixtures/record-before-vbc-stage1-hashes.json').read_text())
CATALOG_FROZEN=json.loads((ROOT/'tests/fixtures/catalog-before-vbc-stage1-hashes.json').read_text())
def canonical(x):return r.sha(json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())

class VBCFirstTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if x['paper_id']=='rpa-0067')
  cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/POLICY_PATH).read_text())
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.paper=next(x for x in cls.catalog['papers']if x['id']=='rpa-0067')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();self.set_policy(self.raw)
 def set_policy(self,payload,**updates):
  (self.root/POLICY_PATH).write_text(json.dumps(dict(self.policy,document_sha256=r.sha(payload),**updates)))
 def admit(self,payload,**updates):self.set_policy(payload,**updates);return r.split_report(self.root,self.record,payload)
 def test_all_nineteen_historical_records_bytes_and_parts_unchanged(self):
  self.assertEqual((len(FROZEN),len(RECORDS_FROZEN),len(self.records)),(19,19,20))
  for rec in self.records:
   if rec['paper_id']=='rpa-0067':continue
   key='/'.join(rec[k]for k in ('paper_id','version','stage'))
   self.assertEqual(canonical(rec),RECORDS_FROZEN[key]);self.assertEqual(rec['sha256'],FROZEN[key])
   self.assertEqual(r.sha((ROOT/r.report_path(rec)).read_bytes()),FROZEN[key])
   for part in rec['parts']:self.assertEqual(r.sha((ROOT/r._parts_path(rec)/part['file']).read_bytes()),part['sha256'])
 def test_all_ninety_four_other_catalog_objects_unchanged(self):
  self.assertEqual(len(CATALOG_FROZEN),94)
  for paper in self.catalog['papers']:
   if paper['id']!='rpa-0067':self.assertEqual(canonical(paper),CATALOG_FROZEN[paper['id']])
 def test_twelve_sections_ten_crops_and_five_conclusions(self):
  parsed=r._parse_html(self.record,self.raw,ROOT)
  self.assertEqual(tuple(parsed.section_ids),SECTION_IDS);self.assertEqual(tuple(parsed.figure_ids),FIGURE_IDS)
  self.assertTrue(set(EVIDENCE_IDS)<=parsed.ids);self.assertEqual((parsed.image_count,parsed.input_count,parsed.summary_count),(10,10,5))
  self.assertEqual(len(IMAGE_HASHES),10)
  for term in ['81.87 ± 0.02','不将其改为 0.87','33 / 34','Average Success Times','正式出版年 2025','CoRL 2024','CC BY-NC 4.0','内容已独立审阅','公开页面视觉验收尚未完成','各自提供 mask 与 masked depth','对外力推扰的响应','作者在训练中把']:
   self.assertIn(term,self.text)
  for term in ['skill://','/workspace/','reader-skill','data:application/pdf','<iframe','<svg','训练/执行约束']:
   self.assertNotIn(term,self.text)
 def test_identity_source_and_review_state_are_closed(self):
  r.split_report(self.root,self.record,self.raw)
  for update in [dict(paper_id='rpa-0066'),dict(stage='stage2',filename='writing-close-reading.html'),dict(version='v2'),dict(source_sha256='0'*64),dict(review_status='approved'),dict(pdf_url='https://arxiv.org/pdf/2403.16967'),dict(source_url='https://wholebody-b1.github.io/')]:
   with self.subTest(update=update),self.assertRaises(ValueError):r.split_report(self.root,dict(self.record,**update),self.raw)
 def test_document_style_and_script_independently_pinned(self):
  for old,new in [(b'81.87',b'0.87'),(b'updatePosition();',b'alert(1);'),(b'--ink:#18212d',b'--ink:#000000')]:
   changed=self.raw.replace(old,new,1);self.assertNotEqual(changed,self.raw)
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,changed)
  for old,new,message in [(b'updatePosition();',b'alert(1);','script'),(b'--ink:#18212d',b'--ink:#000000','stylesheet')]:
   with self.assertRaisesRegex(ValueError,message):self.admit(self.raw.replace(old,new,1))
 def test_image_bytes_remain_pinned_after_document_rehash(self):
  match=re.search(rb'data:image/png;base64,([A-Za-z0-9+/=]+)',self.raw)
  data=base64.b64decode(match[1]);changed=base64.b64encode(data[:40]+bytes([data[40]^1])+data[41:])
  with self.assertRaisesRegex(ValueError,'figures'):self.admit(self.raw[:match.start(1)]+changed+self.raw[match.end(1):])
 def test_active_resources_and_structural_changes_rejected(self):
  for injection in [b'<script>alert(1)</script>',b'<script src="https://example.com/a"></script>',b'<iframe src="https://example.com/a"></iframe>',b'<img src="https://example.com/a.png">',b'<svg></svg>',b'<math></math>',b'<p onclick="alert(1)">x</p>',b'<button type="submit">x</button>',b'<input type="text">',b'<a href="file:///tmp/a">x</a>',b'<blockquote>x</blockquote>']:
   with self.subTest(injection=injection),self.assertRaises(ValueError):self.admit(self.raw.replace(b'</body>',injection+b'</body>'))
  for old,new in [(b'id="section-02"',b'id="section-01"'),(b'id="evidence-E03"',b'id="missing"'),(b'id="five-takeaways"',b'id="missing"'),(b'aria-controls="scroll-figure-01"',b'aria-controls="scroll-figure-99"')]:
   with self.assertRaises(ValueError):self.admit(self.raw.replace(old,new,1))
 def test_resource_css_rejected_even_if_style_is_rehashed(self):
  for css in [b'@import "https://example.com/a";',b'p{background:url(https://example.com/a)}',b'p{width:expression(alert(1))}']:
   changed=self.raw.replace(b'<style>',b'<style>'+css,1);style=re.search(rb'<style>(.*?)</style>',changed,re.S)[1]
   with self.assertRaisesRegex(ValueError,'CSS'):self.admit(changed,style_sha256=r.sha(style))
 def test_original_metadata_stage_scope_and_catalog_counts(self):
  self.assertEqual(validate_catalog(self.catalog,self.records),95)
  self.assertEqual(self.paper['original_metadata'],dict(title='Visual Whole-Body Control for Legged Loco-Manipulation',authors='Minghuan Liu 等',year=2024))
  self.assertFalse(self.paper['citation_verified']);self.assertEqual(self.paper['metadata_status'],'user_provided_unverified')
  self.assertEqual((self.paper['publication_year'],self.paper['preprint_year']),(2025,2024))
  self.assertEqual(self.paper['stages']['stage1'],expected_stage('rpa-0067','stage1',self.records))
  for stage in ('stage2','stage3'):self.assertEqual(self.paper['stages'][stage],{'status':'not_imported','artifacts':[]})
  self.assertEqual(sum(s['status']=='imported'for p in self.catalog['papers']for s in p['stages'].values()),12)
  self.assertEqual(sum(any(s['status']=='imported'for s in p['stages'].values())for p in self.catalog['papers']),5)
  self.assertEqual(sum(all(s['status']=='imported'for s in p['stages'].values())for p in self.catalog['papers']),3)
  self.assertIn('12 份报告已导入',home(self.catalog));self.assertIn('1 个已导入报告',details(self.paper))
  self.assertEqual(json.loads((ROOT/'data/classification.json').read_text())['catalog_sha256'],r.sha((ROOT/'data/catalog.json').read_bytes()))
 def test_current_view_preserves_scientific_body_and_return_context(self):
  page=current.render(ROOT,self.paper,'stage1',self.records)
  self.assertIn('href="stage1.html"',page);self.assertNotIn('href="stage2.html"',page);self.assertNotIn('href="stage3.html"',page)
  self.assertIn('href="../index.html#reading"',page);self.assertEqual(page.count(current.context_script(ROOT)),1)
  for tag in ('article','style','script'):self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>',page.replace(current.context_script(ROOT),''),re.S),re.findall(rf'<{tag}\b.*?</{tag}>',self.text,re.S))
  with patch.dict(current.VBC_FROZEN,{'stage1':dict(current.VBC_FROZEN['stage1'],sha256='0'*64)}):
   with self.assertRaisesRegex(ValueError,'Unreviewed VBC'):current.render(ROOT,self.paper,'stage1',self.records)
 def test_76_utf8_parts_and_only_one_public_html(self):
  self.assertEqual(len(self.record['parts']),76)
  for part in self.record['parts']:
   raw=(ROOT/r._parts_path(self.record)/part['file']).read_bytes();raw.decode('utf-8');self.assertLessEqual(len(raw),48000);self.assertEqual(r.sha(raw),part['sha256'])
  self.assertEqual(sorted(x.name for x in (ROOT/'artifacts/rpa-0067').rglob('*')if x.is_file()),['first-pass.html'])
 def test_packaged_reader_controls_in_python_discovery(self):
  result=subprocess.run(['node',str(ROOT/'tests/test_vbc_stage1_controls.cjs')],cwd=ROOT,capture_output=True,text=True,timeout=20)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
