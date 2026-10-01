"""Immutable method-reader content, stage-scoped security and historical preservation."""
import hashlib,json,re,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
from build import details

class DeepWBCMethodTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=r.load_reports(ROOT);cls.record=next(x for x in cls.records if x['paper_id']=='rpa-0012' and x['stage']=='stage3');cls.raw=(ROOT/r.report_path(cls.record)).read_bytes();cls.text=cls.raw.decode();cls.policy=json.loads((ROOT/'data/report-rpa-0012-stage3-v1-policy.json').read_text())
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name);(self.root/'data').mkdir();(self.root/'data/reports.json').write_text(json.dumps({'schema_version':1,'reports':[]}));self.write_policy(self.policy)
 def write_policy(self,p):(self.root/'data/report-rpa-0012-stage3-v1-policy.json').write_text(json.dumps(p))
 def admit_mutation(self,raw,style=False):
  p=dict(self.policy);p['document_sha256']=r.sha(raw)
  if style:p['style_sha256']=r.sha(re.search(rb'<style>(.*?)</style>',raw,re.S)[1])
  self.write_policy(p);return r.split_report(self.root,self.record,raw)
 def test_exact_frozen_content_images_equations_and_code(self):
  self.assertEqual(r.sha(self.raw),'9cf7b7744b1fa9360cd3e72a329f637a26eb2a69240924a69095aa72012ed514')
  for pattern,count,digest in [(r'<math.*?</math>',9,'75a77f11c047d0ed6089d3a80e2a215cdf6c4013b2cd409d98fef045c15f6261'),(r'<pre.*?</pre>',23,'503e548804894d7ad8803ddced6d7f3a7f4ea79c75e1aa6b4e0d3a6da809559b'),(r'<img[^>]*>',4,'388bb83d76d6d20a9201b98561b39ab711b7b19303e521fe964d9df59f22fb47')]:
   values=re.findall(pattern,self.text,re.S);self.assertEqual(len(values),count);self.assertEqual(r.sha('\n'.join(values).encode()),digest)
  for t in ['ckyFi9zero','CHUNHUI-LAB','Copyright (c) 2021, ETH Zurich, Nikita Rudin','SIL OPEN FONT LICENSE','方法与代码内容已审阅','https://creativecommons.org/licenses/by/4.0/']:self.assertIn(t,self.text)
  self.assertNotIn('references/atlas-theme.md',self.text)
 def test_static_math_and_controls_parsed(self):
  p=r._parse_html(self.record,self.raw,ROOT);self.assertEqual((p.math_count,p.image_count,p.copy_count,p.focus_count),(9,4,11,11));self.assertEqual(self.policy['script_sha256'],'d6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
 def test_prior_deep_reports_immutable_and_all_three_links_present(self):
  previous={(x['stage'],x['version']):x['sha256'] for x in self.records if x['paper_id']=='rpa-0012' and x['stage']!='stage3'}
  self.assertEqual(previous,{('stage1','v1'):'d2d80d400328afe4adac2e94d4761ce87d51dcdb000c5bd7e5bca22e3be357b1',('stage1','v2'):'70c9a4ceb870685d2e332305d9a2906756185ef4a2ae0f94e62a93bafc9e3950',('stage2','v1'):'c1bba5cba6a489dd309d58a660131a6a1281e798fccb72bf2bcbcefa0bb9daa4'})
  for path in ['v2/first-pass.html','v1/writing-close-reading.html']:self.assertIn('https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0012/'+path,self.text)
  paper=next(x for x in json.loads((ROOT/'data/catalog.json').read_text())['papers'] if x['id']=='rpa-0012');page=details(paper);self.assertEqual(page.count('class="unavailable"'),0);self.assertIn('方法与代码内容已审阅',page);self.assertEqual(paper['stages']['stage3']['artifacts'][0]['review_status'],'content_approved')
 def test_other_versions_stages_papers_sources_rejected(self):
  for k,v in [('version','v2'),('paper_id','rpa-0062'),('stage','stage2'),('filename','writing-close-reading.html'),('source_sha256','0'*64),('review_status','approved')]:
   rec=dict(self.record);rec[k]=v
   with self.subTest(field=k),self.assertRaises(ValueError):r.split_report(self.root,rec,self.raw)
 def test_document_script_and_stylesheet_each_pinned(self):
  with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,self.raw.replace(b'<title>',b'<title>x',1))
  for a,b in [(b'updatePosition();',b'alert(1);'),(b'<style>',b'<style>p{color:red}')]:
   with self.assertRaises(ValueError):self.admit_mutation(self.raw.replace(a,b,1))
 def test_passive_math_and_code_cannot_load_or_execute(self):
  for injection in [b'<script>alert(1)</script>',b'<svg onload="alert(1)"></svg>',b'<svg><foreignObject><p>x</p></foreignObject></svg>',b'<svg><animate attributeName="x"></animate></svg>',b'<svg><use href="https://example.com/a.svg"></use></svg>',b'<math href="https://example.com/a"></math>',b'<annotation encoding="text/html">x</annotation>',b'<path d="javascript:alert(1)"></path>',b'<button type="submit" data-copy-code>Copy</button>',b'<span onclick="alert(1)">x</span>',b'<img src="https://example.com/x.png">',b'<style>p{background:url(https://example.com/x)}</style>']:
   with self.subTest(injection=injection),self.assertRaises(ValueError):self.admit_mutation(self.raw.replace(b'</body>',injection+b'</body>'))
 def test_font_and_css_guards_even_with_recomputed_policy(self):
  for css in [b'@import "https://example.com/x";',b'p{background:url(https://example.com/x)}',b'p{background:url(data:image/svg+xml;base64,PHN2Zz4=)}',b'p{width:expression(alert(1))}',b'p{background:url(data:font/woff2;base64,YmFk)}']:
   with self.subTest(css=css),self.assertRaises(ValueError):self.admit_mutation(self.raw.replace(b'<style>',b'<style>'+css,1),style=True)
 def test_missing_extra_and_external_font_rejected(self):
  font=re.search(rb'url\(data:font/woff2;base64,[^)]*\)',self.raw)[0]
  for replacement in [b'none',b'url(https://example.com/a.woff2)',font+b';src:'+font]:
   with self.assertRaises(ValueError):self.admit_mutation(self.raw.replace(font,replacement,1),style=True)
 def test_missing_required_math_or_code_is_rejected(self):
  for payload in [re.sub(rb'<math.*?</math>',b'',self.raw,count=1,flags=re.S),self.raw.replace(b'data-copy-code',b'',1),self.raw.replace(b'data-code-focus',b'',1)]:
   with self.assertRaises(ValueError):self.admit_mutation(payload)

if __name__=='__main__':unittest.main()
