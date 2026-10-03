"""Licensed RoLoMa writing pairs, strict identity and eighteen immutable predecessors."""
import copy,hashlib,html,json,re,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import current_reader as current
from report_roloma_stage2 import IDENTITY,POLICY_PATH,UNIT_IDS,QUOTE_HASHES,SECTION_IDS,MATH_HASH
from validate import expected_stage,validate_catalog
from build import details,home
FROZEN=json.loads((ROOT/'tests/fixtures/reports-before-roloma-stage2.json').read_text())
CATALOG_FROZEN=json.loads((ROOT/'tests/fixtures/catalog-before-roloma-stage2-hashes.json').read_text())

def canonical(v):return r.sha(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode())

class RoLoMaWritingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if all(x[k]==v for k,v in IDENTITY.items()))
  cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/POLICY_PATH).read_text())
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.paper=next(p for p in cls.catalog['papers'] if p['id']=='rpa-0054')
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();self.set_policy(self.raw)
 def set_policy(self,payload,**updates):(self.root/POLICY_PATH).write_text(json.dumps(dict(self.policy,document_sha256=r.sha(payload),**updates)))
 def admit(self,payload,**updates):self.set_policy(payload,**updates);return r.split_report(self.root,self.record,payload)
 def test_all_eighteen_prior_records_and_chunks_are_immutable(self):
  self.assertEqual(len(FROZEN),18);self.assertEqual(len(self.records),20)
  for rec in self.records:
   key='/'.join(rec[k] for k in ('paper_id','version','stage'))
   if key in {'rpa-0054/v1/stage2','rpa-0067/v1/stage1'}:continue
   self.assertEqual(rec['sha256'],FROZEN[key]);self.assertEqual(r.sha((ROOT/r.report_path(rec)).read_bytes()),FROZEN[key])
   for part in rec['parts']:self.assertEqual(r.sha((ROOT/r._parts_path(rec)/part['file']).read_bytes()),part['sha256'])
  first=next(x for x in self.records if x['paper_id']=='rpa-0054' and x['stage']=='stage1')
  self.assertEqual(len(first['parts']),48);self.assertEqual(first['source_sha256'],self.record['source_sha256'])
 def test_ninety_four_other_catalog_objects_are_unchanged(self):
  self.assertEqual(len(CATALOG_FROZEN),94)
  for p in self.catalog['papers']:
   if p['id'] not in {'rpa-0054','rpa-0067'}:self.assertEqual(canonical(p),CATALOG_FROZEN[p['id']])
 def test_exact_pairs_sections_and_licensed_source_not_a_full_pdf(self):
  parsed=r._parse_html(self.record,self.raw,ROOT)
  self.assertEqual(tuple(parsed.source_rows),UNIT_IDS);self.assertEqual(len(UNIT_IDS),36)
  self.assertEqual(tuple(parsed.section_ids),SECTION_IDS);self.assertEqual(len(QUOTE_HASHES),36)
  self.assertEqual(tuple(r.sha(q.encode()) for q in parsed.quotes),QUOTE_HASHES)
  self.assertEqual(parsed.math_count,1);self.assertEqual(r.sha(re.search(rb'<math\b.*?</math>',self.raw,re.S)[0]),MATH_HASH)
  for term in ['CC BY 4.0','Henrique Ferrolho','Vladimir Ivan','Wolfgang Merkt','Ioannis Havoutis','Sethu Vijayakumar','957词','170','551','236','§3.6','§6.2','不含§6.1–6.4未来工作四小节','三个采样方向','接触序列与时刻','原作者不对本页分析背书','公开页面视觉验收尚未完成']:
   self.assertIn(term,self.text)
  for term in ['skill://','/workspace/','data:application/pdf','<img','<iframe','<svg','候选','rpa-0062']:
   self.assertNotIn(term,self.text)
 def test_scoped_word_counts_recompute_from_exact_original_sentences(self):
  parsed=r._parse_html(self.record,self.raw,ROOT)
  refs=[r'\(Murphy et al\. 2012; Zimmermann et al\. 2021; Ma et al\. 2022\)',r'\(Prete & Mansard, 2016; Xin et al\., 2018; Sleiman et al\., 2021; Ma et al\., 2022\)',r'\(2020\)',r'\(2021\)',r'\(i\)',r'\(ii\)']
  counts=[]
  for q in parsed.quotes:
   for pat in refs:q=re.sub(pat,'',q)
   q=q.replace('—',' ').replace('–',' ');counts.append(sum(bool(re.search('[A-Za-z0-9]',w)) for w in q.split()))
  self.assertEqual([sum(counts[:8]),sum(counts[8:26]),sum(counts[26:])],[170,551,236])
  self.assertEqual(sum(counts),957)
 def test_exact_identity_and_formal_source_fail_closed(self):
  r.split_report(self.root,self.record,self.raw)
  for update in [dict(paper_id='rpa-0053'),dict(stage='stage3',filename='method-code-reading.html'),dict(version='v2'),dict(source_sha256='0'*64),dict(review_status='approved'),dict(pdf_url='https://arxiv.org/pdf/2203.01446'),dict(source_url='https://example.com/paper')]:
   with self.subTest(update=update),self.assertRaises(ValueError):r.split_report(self.root,dict(self.record,**update),self.raw)
 def test_document_style_script_and_math_independently_pinned(self):
  for old,new,msg in [(b'updatePosition();',b'alert(1);','script'),(b'--ink:#18212d',b'--ink:#000000','stylesheet'),(b'<mi>N</mi>',b'<mi>M</mi>','MathML')]:
   changed=self.raw.replace(old,new,1);self.assertNotEqual(changed,self.raw)
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,changed)
   with self.assertRaisesRegex(ValueError,msg):self.admit(changed)
 def test_quotes_and_unit_structure_cannot_change_under_document_rehash(self):
  changes=[self.raw.replace(b'Deployment of robotic systems',b'Unsafe invented source statement',1),self.raw.replace(b'data-source-row="A1"',b'data-source-row="A2"',1),self.raw.replace(b'id="abstract"',b'id="structure"',1),self.raw.replace(b'<blockquote class="source-excerpt" lang="en" data-verbatim="paper">',b'<blockquote class="source-excerpt" lang="en" data-verbatim="paper"><b>',1)]
  for changed in changes:
   with self.subTest(hash=r.sha(changed)),self.assertRaises(ValueError):self.admit(changed)
 def test_active_resources_and_unsafe_math_rejected_after_rehash(self):
  injections=[b'<script>alert(1)</script>',b'<script src="https://example.com/x"></script>',b'<iframe src="https://example.com"></iframe>',b'<img src="https://example.com/x.jpg">',b'<svg><use href="https://example.com/a"></use></svg>',b'<math href="https://example.com/a"></math>',b'<p onclick="alert(1)">x</p>',b'<button type="submit">Submit</button>',b'<input type="text">',b'<a href="file:///tmp/x">x</a>',b'<a href="../../../papers/rpa-0062/index.html">Other</a>',b'<blockquote>Unreviewed</blockquote>']
  for injection in injections:
   with self.subTest(injection=injection),self.assertRaises(ValueError):self.admit(self.raw.replace(b'</body>',injection+b'</body>'))
  for css in [b'@import "https://example.com/x";',b'p{background:url(https://example.com/x)}']:
   changed=self.raw.replace(b'<style>',b'<style>'+css,1);style=re.search(rb'<style>(.*?)</style>',changed,re.S)[1]
   with self.assertRaisesRegex(ValueError,'CSS'):self.admit(changed,style_sha256=r.sha(style))
 def test_eleven_current_stages_four_papers_only_three_complete(self):
  self.assertEqual(validate_catalog(self.catalog,self.records),95)
  self.assertEqual(sum(s['status']=='imported' for p in self.catalog['papers'] for s in p['stages'].values()),12)
  self.assertEqual(sum(any(s['status']=='imported' for s in p['stages'].values()) for p in self.catalog['papers']),5)
  self.assertEqual(sum(all(s['status']=='imported' for s in p['stages'].values()) for p in self.catalog['papers']),3)
  self.assertFalse(self.paper['citation_verified']);self.assertEqual(self.paper['metadata_status'],'user_provided_unverified')
  self.assertEqual(self.paper['stages']['stage2'],expected_stage('rpa-0054','stage2',self.records));self.assertEqual(self.paper['stages']['stage3'],{'status':'not_imported','artifacts':[]})
  self.assertIn('2 个已导入报告',details(self.paper));self.assertIn('12 份报告已导入',home(self.catalog))
  self.assertEqual(json.loads((ROOT/'data/classification.json').read_text())['catalog_sha256'],r.sha((ROOT/'data/catalog.json').read_bytes()))
 def test_current_views_link_two_stages_and_keep_context_and_article(self):
  for stage in ('stage1','stage2'):
   rec=next(x for x in self.records if x['paper_id']=='rpa-0054' and x['stage']==stage)
   original=(ROOT/r.report_path(rec)).read_text();page=current.render(ROOT,self.paper,stage,self.records)
   self.assertIn('href="stage1.html"',page);self.assertIn('href="stage2.html"',page);self.assertNotIn('href="stage3.html"',page)
   self.assertIn('aria-disabled="true"><small>03 · 未完成</small>',page)
   self.assertIn('href="../index.html#reading"',page);self.assertEqual(page.count(current.context_script(ROOT)),1)
   for tag in ('article','style','script'):self.assertEqual(re.findall(rf'<{tag}\b.*?</{tag}>',page.replace(current.context_script(ROOT),''),re.S),re.findall(rf'<{tag}\b.*?</{tag}>',original,re.S))
  with patch.dict(current.ROLOMA_FROZEN,{'stage2':dict(current.ROLOMA_FROZEN['stage2'],sha256='0'*64)}):
   with self.assertRaisesRegex(ValueError,'Unreviewed RoLoMa'):current.render(ROOT,self.paper,'stage2',self.records)
 def test_four_chunks_and_no_unregistered_artifact(self):
  self.assertEqual(len(self.record['parts']),4)
  for part in self.record['parts']:self.assertLessEqual(part['bytes'],48000)
  self.assertEqual(sorted(p.name for p in (ROOT/'artifacts/rpa-0054').rglob('*') if p.is_file()),['first-pass.html','writing-close-reading.html'])
 def test_packaged_reader_controls_in_full_discovery(self):
  p=subprocess.run(['node',str(ROOT/'tests/test_roloma_stage2_controls.cjs')],cwd=ROOT,capture_output=True,text=True,timeout=20)
  self.assertEqual(p.returncode,0,p.stdout+p.stderr)

if __name__=='__main__':unittest.main()
