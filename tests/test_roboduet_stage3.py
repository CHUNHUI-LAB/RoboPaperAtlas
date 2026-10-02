"""One method report, strict passive-content guards and sixteen immutable predecessors."""
import copy,json,re,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import current_reader as current
from report_roboduet_stage3 import IDENTITY,POLICY_PATH,SECTION_IDS
from validate import expected_stage,validate_catalog
from build import details
FROZEN=json.loads((ROOT/'tests/fixtures/reports-before-roboduet-stage3.json').read_text())

class RoboDuetMethodTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if all(x[k]==v for k,v in IDENTITY.items()))
  cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/POLICY_PATH).read_text())
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.paper=next(x for x in cls.catalog['papers'] if x['id']=='rpa-0052')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();self.set_policy(self.raw)
 def set_policy(self,payload,**updates):
  (self.root/POLICY_PATH).write_text(json.dumps(dict(self.policy,document_sha256=r.sha(payload),**updates)))
 def admit(self,payload,**updates):self.set_policy(payload,**updates);return r.split_report(self.root,self.record,payload)
 def test_sixteen_historical_reports_are_byte_immutable(self):
  self.assertEqual(len(FROZEN),16);self.assertEqual(len(self.records),19)
  for rec in self.records:
   key='/'.join(rec[k] for k in ('paper_id','version','stage'))
   if key in {'rpa-0052/v1/stage3','rpa-0054/v1/stage1','rpa-0054/v1/stage2'}:continue
   self.assertEqual(rec['sha256'],FROZEN[key]);self.assertEqual(r.sha((ROOT/r.report_path(rec)).read_bytes()),FROZEN[key])
 def test_exact_reviewed_counts_and_source_scope(self):
  parsed=r._parse_html(self.record,self.raw,ROOT)
  self.assertEqual(tuple(parsed.section_ids),SECTION_IDS)
  self.assertEqual((parsed.math_count,parsed.svg_count,parsed.copy_count,parsed.focus_count,parsed.pre_count),(14,1,12,12,15))
  for text in ['正式出版PDF未取得/比对','59→56','100,000','2048','4096','tanh','腿策略在第二阶段继续学习','21.875%','11.67个百分点','公开页面视觉验收尚未完成','stop_flag=false','Copyright (c) 2024 Guoping Pan','ETH Zurich, Nikita Rudin','NVIDIA CORPORATION']:
   self.assertIn(text,self.text)
  for text in ['skill://','/workspace/','method-code-audit.md','reader-skill','<img','<iframe','data:application/pdf','方法与代码精读候选']:
   self.assertNotIn(text,self.text)
  self.assertEqual(self.policy['script_sha256'],'d6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
  self.assertIn('a7e1528215c048199f90cb69ceb7749a1d745f28',self.text);self.assertIn('6cf24d9b4cc3d8965762c2a606fa5734de5e58b9',self.text)
 def test_exact_identity_and_source_only(self):
  r.split_report(self.root,self.record,self.raw)
  for updates in [dict(paper_id='rpa-0053'),dict(stage='stage2',filename='writing-close-reading.html'),dict(version='v2'),dict(review_status='approved'),dict(source_sha256='0'*64),dict(pdf_url='https://example.com/a.pdf')]:
   with self.subTest(updates=updates),self.assertRaises(ValueError):r.split_report(self.root,dict(self.record,**updates),self.raw)
 def test_document_script_style_independently_pinned(self):
  for before,after in [(b'39/60',b'40/60'),(b'updatePosition();',b'alert(1);'),(b'--ink:#18212d',b'--ink:#000000')]:
   changed=self.raw.replace(before,after,1)
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,changed)
  for before,after,error in [(b'updatePosition();',b'alert(1);','script'),(b'--ink:#18212d',b'--ink:#000000','stylesheet')]:
   with self.assertRaisesRegex(ValueError,error):self.admit(self.raw.replace(before,after,1))
 def test_inert_math_svg_and_source_lines_remain_pinned_after_document_rehash(self):
  for changed in [self.raw.replace(b'<mn>0.00004</mn>',b'<mn>0.00005</mn>',1),self.raw.replace(b'fill="#f6f8fb"',b'fill="#ffffff"',1),self.raw.replace(b'>torch</span>',b'>evil</span>',1)]:
   self.assertTrue(changed != self.raw)
   with self.assertRaises(ValueError):self.admit(changed)
 def test_active_resources_and_structure_cannot_be_admitted_by_rehash(self):
  injections=[b'<script>alert(1)</script>',b'<svg onload="alert(1)"></svg>',b'<svg><foreignObject>x</foreignObject></svg>',b'<svg><use href="https://example.com/a.svg"></use></svg>',b'<math href="https://example.com/a"></math>',b'<iframe src="https://example.com"></iframe>',b'<img src="https://example.com/x.png">',b'<button type="submit" data-copy-code>Copy</button>',b'<p onclick="alert(1)">x</p>',b'<a href="file:///tmp/x">x</a>',b'<a href="../../../papers/rpa-0062/index.html">cross-paper</a>',b'<blockquote>unreviewed quote</blockquote>']
  for injection in injections:
   with self.subTest(injection=injection),self.assertRaises(ValueError):self.admit(self.raw.replace(b'</body>',injection+b'</body>'))
  for changed in [self.raw.replace(b'id="mapping"',b'id="framework"',1),self.raw.replace(b'data-copy-code',b'',1),re.sub(rb'<math\b.*?</math>',b'',self.raw,count=1,flags=re.S)]:
   with self.assertRaises(ValueError):self.admit(changed)
 def test_css_resource_guard_survives_approved_hash_updates(self):
  for css in [b'@import "https://example.com/x";',b'p{background:url(https://example.com/x)}',b'p{width:expression(alert(1))}']:
   changed=self.raw.replace(b'<style>',b'<style>'+css,1);style=re.search(rb'<style>(.*?)</style>',changed,re.S)[1]
   with self.assertRaisesRegex(ValueError,'CSS'):self.admit(changed,style_sha256=r.sha(style))
 def test_catalog_nine_current_stages_three_complete_papers(self):
  self.assertEqual(validate_catalog(self.catalog,self.records),95)
  self.assertEqual(sum(s['status']=='imported' for p in self.catalog['papers'] for s in p['stages'].values()),11)
  self.assertEqual(sum(all(s['status']=='imported' for s in p['stages'].values()) for p in self.catalog['papers']),3)
  self.assertFalse(self.paper['citation_verified']);self.assertEqual(self.paper['stages']['stage3'],expected_stage('rpa-0052','stage3',self.records))
  self.assertIn('方法与代码内容已审阅',details(self.paper))
  overlay=json.loads((ROOT/'data/classification.json').read_text());self.assertEqual(overlay['catalog_sha256'],r.sha((ROOT/'data/catalog.json').read_bytes()))
 def test_current_three_stage_navigation_preserves_all_article_script_style_bytes(self):
  for stage in ('stage1','stage2','stage3'):
   page=current.render(ROOT,self.paper,stage,self.records);source=(ROOT/self.paper['stages'][stage]['artifacts'][0]['path']).read_text()
   for target in ('stage1','stage2','stage3'):self.assertIn(f'href="{target}.html"',page)
   self.assertIn('href="../index.html#reading"',page)
   for tag in ('article','style','script'):self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>',page.replace(current.context_script(ROOT), ''),re.S),re.findall(rf'<{tag}\b.*?</{tag}>',source,re.S))
  with patch.dict(current.ROBO_FROZEN,{'stage3':dict(current.ROBO_FROZEN['stage3'],sha256='0'*64)}):
   with self.assertRaisesRegex(ValueError,'Unreviewed RoboDuet'):current.render(ROOT,self.paper,'stage3',self.records)
 def test_exact_packaged_controls_via_existing_python_discovery(self):
  result=subprocess.run(['node',str(ROOT/'tests/test_roboduet_stage3_controls.cjs')],cwd=ROOT,capture_output=True,text=True,timeout=20)
  self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main()
