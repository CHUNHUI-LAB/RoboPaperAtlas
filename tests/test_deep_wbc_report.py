import copy
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
from build import details, about
from validate import validate_catalog, expected_stage
from test_reports import metadata, html

class DeepWBCReportTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.registry=json.loads((ROOT/'data/reports.json').read_text())
  cls.record=next(x for x in cls.registry['reports'] if x['paper_id']=='rpa-0012')
  cls.payload=b''.join((ROOT/r._parts_path(cls.record)/p['file']).read_bytes() for p in cls.record['parts'])
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text())
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name);(self.root/'data').mkdir()
  shutil.copyfile(ROOT/'data/report-rpa-0012-v1-policy.json',self.root/'data/report-rpa-0012-v1-policy.json')
  self.write_registry([])
 def write_registry(self,records):
  (self.root/'data/reports.json').write_text(json.dumps(dict(schema_version=1,reports=records)))
 def add_deep(self):return r.split_report(self.root,self.record,self.payload)
 def test_cross_paper_same_version_filename_has_distinct_bytes_and_paths(self):
  umi=r.split_report(self.root,metadata(),html('<h1 id="umi-only">UMI fixture</h1>'));deep=self.add_deep();self.write_registry([umi,deep]);r.assemble_reports(self.root)
  self.assertEqual((self.root/r.report_path(umi)).read_bytes(),html('<h1 id="umi-only">UMI fixture</h1>'))
  self.assertEqual((self.root/r.report_path(deep)).read_bytes(),self.payload)
  self.assertNotEqual(r.report_path(umi),r.report_path(deep));self.assertEqual(len(r.load_reports(self.root)),2)
 def test_sibling_links_cannot_resolve_in_other_paper(self):
  umi=r.split_report(self.root,metadata(),html('<h1 id="umi-only">UMI</h1>'))
  stage2=r.split_report(self.root,metadata('stage2'),html('<a href="first-pass.html#section-01">Wrong paper fragment</a>'))
  self.write_registry([umi,stage2,self.add_deep()])
  with self.assertRaisesRegex(ValueError,'Unresolved sibling'):r.assemble_reports(self.root)
  self.assertFalse((self.root/'artifacts').exists())
 def test_explicit_identity_sources_review_state_and_future_stages_are_closed(self):
  for key,value in [('paper_id','rpa-0013'),('stage','stage3'),('version','v3'),('review_status','approved'),('review_status','browser_approved'),('source_url',metadata()['source_url']),('pdf_url',metadata()['pdf_url']),('source_sha256','a'*64),('filename','../first-pass.html')]:
   with self.subTest(key=key,value=value):
    rec=dict(self.record);rec[key]=value
    with self.assertRaises(ValueError):r.split_report(self.root,rec,self.payload)
  umi=metadata();umi['review_status']='content_approved'
  with self.assertRaises(ValueError):r.split_report(self.root,umi,html())
 def test_modified_document_and_inline_script_cannot_be_rehashed_into_approval(self):
  for payload in [self.payload.replace(b'updatePosition();',b'alert(1);',1),self.payload.replace(b'</body>',b'<script>alert(1)</script></body>'),self.payload.replace(b'<title>',b'<title>Wrong paper '),self.payload.replace(b'https://proceedings.mlr.press/v205/fu23a/fu23a.pdf',b'https://example.com/other.pdf')]:
   with self.assertRaisesRegex(ValueError,'fingerprint'):r.split_report(self.root,self.record,payload)
 def test_strict_html_guards_remain_after_document_fingerprint(self):
  for injection in ['<script src="https://example.com/x.js"></script>','<img src="https://example.com/a.png">','<p onclick="alert(1)">x</p>','<style>p{background:url(https://example.com/a)}</style>','<a href="../../../papers/rpa-0062/index.html">Other paper</a>','<a href="../v2/first-pass.html">Other version</a>']:
   payload=self.payload.replace(b'</body>',injection.encode()+b'</body>');policy=json.loads((ROOT/'data/report-rpa-0012-v1-policy.json').read_text());policy['document_sha256']=r.sha(payload);(self.root/'data/report-rpa-0012-v1-policy.json').write_text(json.dumps(policy))
   with self.subTest(injection=injection),self.assertRaises(ValueError):r.split_report(self.root,self.record,payload)
 def test_paper_specific_return_path_does_not_expand_legacy_allowlist(self):
  with self.assertRaises(ValueError):r.split_report(self.root,metadata(),html('<a href="../../../papers/rpa-0012/index.html">Wrong paper</a>'))
  deep=self.add_deep();self.write_registry([deep]);self.assertEqual(r.load_reports(self.root),[deep])
  self.assertIn(b'href="../../../papers/rpa-0012/index.html"',self.payload)
  self.assertNotIn(b'private-atlas',self.payload);self.assertNotIn(b'references/atlas-theme.md',self.payload)
 def test_stage_metadata_public_page_and_actual_stage_links(self):
  records=r.load_reports(ROOT);self.assertEqual(len(records),20);self.assertEqual(validate_catalog(self.catalog,records),95)
  paper=next(x for x in self.catalog['papers'] if x['id']=='rpa-0012')
  self.assertEqual(paper['stages']['stage1'],expected_stage('rpa-0012','stage1',records));self.assertEqual(paper['stages']['stage1']['artifacts'][0]['review_status'],'content_approved')
  self.assertEqual(paper['stages']['stage3'],expected_stage('rpa-0012','stage3',records))
  page=details(paper);self.assertIn('3 个已导入报告',page);self.assertIn('初读内容已审阅',page);self.assertEqual(page.count('class="unavailable"'),0);self.assertIn('../../artifacts/rpa-0012/v1/first-pass.html',page)
  self.assertIn('writing-close-reading.html',page);self.assertIn('method-code-reading.html',page)
  page=about(5,records);self.assertIn('../papers/rpa-0012/index.html#reading',page);self.assertIn('../papers/rpa-0062/index.html#reading',page)
 def test_source_pdf_and_content_fingerprints_are_explicit(self):
  self.assertEqual(self.record['source_sha256'],'96751c541e226404e10820771bd26dc97ced5770fe30520e3bba6db78743536b')
  self.assertEqual(self.record['sha256'],hashlib.sha256(self.payload).hexdigest());self.assertNotEqual(self.record['sha256'],self.record['source_sha256'])
  self.assertEqual(self.record['review_status'],'content_approved')

if __name__=='__main__':unittest.main()
