"""Formal RoLoMa Stage1, exact passive content, and seventeen immutable predecessors."""
import base64,copy,hashlib,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import current_reader as current
from report_roloma_stage1 import IDENTITY,POLICY_PATH,SECTION_IDS,EVIDENCE_IDS,IMAGE_HASHES,MATH_HASH
from validate import expected_stage,validate_catalog
from build import details,home
from reading_index import render as reading_render
FROZEN=json.loads((ROOT/'tests/fixtures/reports-before-roloma-stage1.json').read_text())
CATALOG_FROZEN=json.loads((ROOT/'tests/fixtures/catalog-before-roloma-stage1-hashes.json').read_text())

def canonical(value):return r.sha(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())

class RoLoMaFirstTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if all(x[k]==v for k,v in IDENTITY.items()))
  cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/POLICY_PATH).read_text())
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.paper=next(x for x in cls.catalog['papers'] if x['id']=='rpa-0054')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();self.set_policy(self.raw)
 def set_policy(self,payload,**updates):
  (self.root/POLICY_PATH).write_text(json.dumps(dict(self.policy,document_sha256=r.sha(payload),**updates)))
 def admit(self,payload,**updates):self.set_policy(payload,**updates);return r.split_report(self.root,self.record,payload)
 def test_seventeen_reports_and_ninety_four_other_catalog_objects_unchanged(self):
  self.assertEqual(len(FROZEN),17);self.assertEqual(len(self.records),19);self.assertEqual(len(CATALOG_FROZEN),94)
  for rec in self.records:
   key='/'.join(rec[k] for k in ('paper_id','version','stage'))
   if key in {'rpa-0054/v1/stage1','rpa-0054/v1/stage2'}:continue
   self.assertEqual(rec['sha256'],FROZEN[key]);self.assertEqual(r.sha((ROOT/r.report_path(rec)).read_bytes()),FROZEN[key])
  for paper in self.catalog['papers']:
   if paper['id']!='rpa-0054':self.assertEqual(canonical(paper),CATALOG_FROZEN[paper['id']])
 def test_twelve_sections_eleven_figures_and_exact_five_conclusions(self):
  parsed=r._parse_html(self.record,self.raw,ROOT)
  self.assertEqual(tuple(parsed.section_ids),SECTION_IDS);self.assertTrue(set(EVIDENCE_IDS)<=parsed.ids)
  self.assertEqual((parsed.math_count,parsed.image_count,parsed.figure_count,parsed.input_count,parsed.summary_count),(1,11,11,11,5))
  self.assertEqual(len(IMAGE_HASHES),11)
  self.assertEqual(r.sha(re.search(rb'<math\b.*?</math>',self.raw,re.S)[0]),MATH_HASH)
  self.assertIn('应该记住的五件事 · E11',self.text)
  for value in ['CC BY 4.0','Version of Record','未逐段观看','不是必须依次执行','括号内数字','实时 MPC','5.1 kg','21–22%','约 100 N','最大化求和','公开页面视觉验收尚未完成']:
   self.assertIn(value,self.text)
  for value in ['skill://','/workspace/','reader-skill','data:application/pdf','<iframe','<svg','初读候选']:
   self.assertNotIn(value,self.text)
 def test_identity_and_formal_source_closed(self):
  r.split_report(self.root,self.record,self.raw)
  for update in [dict(paper_id='rpa-0053'),dict(stage='stage2',filename='writing-close-reading.html'),dict(version='v2'),dict(source_sha256='0'*64),dict(review_status='approved'),dict(pdf_url='https://arxiv.org/pdf/2203.01446'),dict(source_url='https://example.com/paper')]:
   with self.subTest(update=update),self.assertRaises(ValueError):r.split_report(self.root,dict(self.record,**update),self.raw)
 def test_document_style_and_controls_independently_pinned(self):
  for old,new in [(b'73\xe2\x80\x9376 N',b'99 N'),(b'updatePosition();',b'alert(1);'),(b'--ink:#18212d',b'--ink:#000000')]:
   changed=self.raw.replace(old,new,1);self.assertNotEqual(changed,self.raw)
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,changed)
  for old,new,message in [(b'updatePosition();',b'alert(1);','script'),(b'--ink:#18212d',b'--ink:#000000','stylesheet')]:
   with self.assertRaisesRegex(ValueError,message):self.admit(self.raw.replace(old,new,1))
 def test_math_and_licensed_figure_bytes_cannot_be_changed_by_document_rehash(self):
  with self.assertRaisesRegex(ValueError,'MathML'):self.admit(self.raw.replace(b'<mi>N</mi>',b'<mi>M</mi>',1))
  match=re.search(rb'data:image/jpeg;base64,([A-Za-z0-9+/=]+)',self.raw)
  data=base64.b64decode(match[1]);changed=base64.b64encode(data[:30]+bytes([data[30]^1])+data[31:])
  with self.assertRaisesRegex(ValueError,'figures'):self.admit(self.raw[:match.start(1)]+changed+self.raw[match.end(1):])
 def test_unsafe_resources_and_structural_changes_rejected_after_document_rehash(self):
  injections=[b'<script>alert(1)</script>',b'<script src="https://example.com/x"></script>',b'<iframe src="https://example.com"></iframe>',b'<img src="https://example.com/x.jpg">',b'<svg><use href="https://example.com/a"></use></svg>',b'<math href="https://example.com/a"></math>',b'<p onclick="alert(1)">x</p>',b'<button type="submit">Submit</button>',b'<input type="text">',b'<a href="file:///tmp/x">x</a>',b'<a href="../../../papers/rpa-0062/index.html">Other</a>',b'<blockquote>Unreviewed</blockquote>']
  for injection in injections:
   with self.subTest(injection=injection),self.assertRaises(ValueError):self.admit(self.raw.replace(b'</body>',injection+b'</body>'))
  for changed in [self.raw.replace(b'id="section-02"',b'id="section-01"',1),self.raw.replace(b'id="evidence-E11"',b'id="missing"',1),self.raw.replace(b'class="figure-size-switch"',b'class="evil"',1),self.raw.replace(b'aria-controls="figure-scroll-1"',b'aria-controls="figure-scroll-99"',1)]:
   with self.assertRaises(ValueError):self.admit(changed)
 def test_css_loading_rejected_even_with_updated_style_fingerprint(self):
  for css in [b'@import "https://example.com/x";',b'p{background:url(https://example.com/x)}',b'p{width:expression(alert(1))}']:
   changed=self.raw.replace(b'<style>',b'<style>'+css,1);style=re.search(rb'<style>(.*?)</style>',changed,re.S)[1]
   with self.assertRaisesRegex(ValueError,'CSS'):self.admit(changed,style_sha256=r.sha(style))
 def test_original_metadata_and_actual_stage_scope_preserved(self):
  self.assertEqual(validate_catalog(self.catalog,self.records),95)
  self.assertEqual(self.paper['original_metadata'],{'title':'RoLoMa: robust loco-manipulation for quadruped robots with arms','authors':'Henrique Ferrolho 等','year':2023})
  self.assertFalse(self.paper['citation_verified']);self.assertEqual(self.paper['metadata_status'],'user_provided_unverified')
  self.assertEqual(self.paper['verified_overlay']['publication_year'],2023);self.assertEqual(self.paper['pdf_kind'],'publisher')
  self.assertEqual(self.paper['stages']['stage1'],expected_stage('rpa-0054','stage1',self.records))
  self.assertEqual(self.paper['stages']['stage2'],expected_stage('rpa-0054','stage2',self.records));self.assertEqual(self.paper['stages']['stage3'],{'status':'not_imported','artifacts':[]})
  self.assertEqual(sum(any(s['status']=='imported' for s in p['stages'].values()) for p in self.catalog['papers']),4)
  self.assertEqual(sum(s['status']=='imported' for p in self.catalog['papers'] for s in p['stages'].values()),11)
  self.assertEqual(sum(all(s['status']=='imported' for s in p['stages'].values()) for p in self.catalog['papers']),3)
  self.assertIn('2 个已导入报告',details(self.paper));self.assertIn('11 份报告已导入',home(self.catalog))
  self.assertEqual(json.loads((ROOT/'data/classification.json').read_text())['catalog_sha256'],r.sha((ROOT/'data/catalog.json').read_bytes()))
 def test_current_view_preserves_article_style_script_figures_and_return_context(self):
  page=current.render(ROOT,self.paper,'stage1',self.records)
  self.assertIn('href="stage1.html"',page);self.assertIn('href="stage2.html"',page);self.assertNotIn('href="stage3.html"',page)
  self.assertIn('href="../index.html#reading"',page);self.assertEqual(page.count(current.context_script(ROOT)),1)
  for tag in ('article','style','script'):self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>',page.replace(current.context_script(ROOT),''),re.S),re.findall(rf'<{tag}\b.*?</{tag}>',self.text,re.S))
  with patch.dict(current.ROLOMA_FROZEN,{'stage1':dict(current.ROLOMA_FROZEN['stage1'],sha256='0'*64)}):
   with self.assertRaisesRegex(ValueError,'Unreviewed RoLoMa'):current.render(ROOT,self.paper,'stage1',self.records)
 def test_48000_byte_chunks_and_no_source_pdf_in_artifact_directory(self):
  self.assertEqual(len(self.record['parts']),48)
  for part in self.record['parts']:
   self.assertLessEqual(part['bytes'],48000);raw=(ROOT/r._parts_path(self.record)/part['file']).read_bytes();raw.decode('utf-8');self.assertEqual(r.sha(raw),part['sha256'])
  folder=ROOT/'artifacts/rpa-0054';self.assertEqual(sorted(p.name for p in folder.rglob('*') if p.is_file()),['first-pass.html','writing-close-reading.html'])
 def test_exact_packaged_reader_controls_in_python_discovery(self):
  result=subprocess.run(['node',str(ROOT/'tests/test_roloma_stage1_controls.cjs')],cwd=ROOT,capture_output=True,text=True,timeout=20)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
