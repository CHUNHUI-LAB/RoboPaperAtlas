"""Immutable v2 readers: exact content, source alignment and offline security."""
import copy,hashlib,html,json,re,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports
from report_v2 import prepare,STYLE_NAMES,SCRIPT_NAMES
from test_reader_preview import CodeText
class ReaderDocumentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records={r['stage']:r for r in reports.load_reports(ROOT)if r['paper_id']=='rpa-0062' and r['version']=='v2'}
  cls.pages={s:(ROOT/reports.report_path(r)).read_text()for s,r in cls.records.items()}
  cls.policy=json.loads((ROOT/'data/report-v2-policy.json').read_text())
 def test_three_current_versions_with_history(self):
  from validate import expected_stage
  records=reports.load_reports(ROOT)
  for stage in self.records:
   self.assertEqual([a['version']for a in expected_stage('rpa-0062',stage,records)['artifacts']],['v3','v2','v1'])
  self.assertEqual(expected_stage('rpa-0064','stage1',records),{'status':'not_imported','artifacts':[]})
 def test_self_contained_figures_fonts_and_navigation(self):
  for stage,page in self.pages.items():
   self.assertNotRegex(page,r'<script[^>]+src=|<link[^>]+rel="stylesheet"|<iframe|<object')
   self.assertIn('Library</a>',page);self.assertIn('Atlas</a>',page);self.assertIn('Radar</a>',page)
   self.assertNotIn('Reader preview',page);self.assertIn('报告版本 v2',page)
   self.assertEqual(len(re.findall(r'<img\b',page)),{'stage1':5,'stage2':0,'stage3':6}[stage])
   for url in re.findall(r'url\(([^)]+)\)', ''.join(re.findall(r'<style[^>]*>(.*?)</style>',page,re.S))):self.assertTrue(url.startswith(('data:font/woff2;base64,','data:image/svg+xml;base64,')))
  self.assertEqual(self.pages['stage3'].count('data:font/woff2;base64,'),20)
  self.assertIn('SIL OPEN FONT LICENSE',self.pages['stage3']);self.assertIn('Permission is hereby granted',self.pages['stage3'])
 def test_source_alignment_covers_each_analysis_row(self):
  page=self.pages['stage2'];raw=re.search(r'<script type="application/json" data-source-units id="reader-source-units">(.*?)</script>',page,re.S)[1];units=json.loads(raw)
  rows=re.findall(r'<tr class="source-row" data-source-row="([^"]+)"',page)
  self.assertEqual(len(rows),37);self.assertEqual(set(rows),{u['id']for u in units});self.assertEqual(len(rows),len(set(rows)))
  self.assertEqual(sum(len((u['quote']or'').split())for u in units),16)
  for u in units:self.assertIn('data-source-unit="'+u['id']+'"',page);self.assertTrue(u['url'].endswith('#page='+str(u['page'])))
  self.assertIn('不提供句级自动高亮',page);self.assertIn('浏览器可能下载 PDF',page)
 def test_stage3_code_math_images_preserve_approved_content(self):
  old=(ROOT/'artifacts/rpa-0062/v1/method-code-reading.html').read_text();page=self.pages['stage3']
  raw=re.findall(r'<pre><code>(.*?)</code></pre>',old,re.S);blocks=re.findall(r'<div class="code-reader".*?<pre[^>]*>(.*?)</pre>',page,re.S)
  self.assertEqual(len(blocks),9)
  for before,after in zip(raw,blocks):
   p=CodeText();p.feed(after);self.assertEqual('\n'.join(p.lines),html.unescape(before))
  self.assertEqual(re.findall(r'<img[^>]+src="([^"]+)"',old),re.findall(r'<img[^>]+src="([^"]+)"',page))
  self.assertEqual(len(re.findall(r'<math\b',page)),54);self.assertEqual(len(re.findall(r'<annotation encoding="application/x-tex">',page)),54)
  for url in re.findall(r'href="(https://github.com/real-stanford/umi-on-legs/[^\"]+)"',old):self.assertIn('href="'+url+'"',page)
 def test_stage1_expansion_preserves_twelve_sections(self):
  page=self.pages['stage1'];self.assertEqual(len(re.findall(r'<section id=',page)),12)
  self.assertIn('上排为本文世界系跟踪，下排为机体系跟踪',page)
  for value in ['Table 1','Tables 2–4','Tables 5–6','Table 7']:self.assertTrue(value in page,value)
 def test_policy_and_asset_tampering_fail_closed(self):
  r=self.records['stage3'];raw=self.pages['stage3'].encode()
  with self.assertRaisesRegex(ValueError,'document fingerprint'):prepare(ROOT,r,raw+b' ')
  with tempfile.TemporaryDirectory()as d:
   root=Path(d);(root/'data').mkdir();policy=copy.deepcopy(self.policy)
   # Updating a document digest alone cannot authorize unreviewed code.
   changed=raw.replace(b"'use strict';",b"'use strict';alert(1);",1);policy['documents'][r['filename']]=reports.sha(changed)
   (root/'data/report-v2-policy.json').write_text(json.dumps(policy))
   with self.assertRaisesRegex(ValueError,'script fingerprint'):reports._parse_html(r,changed,root)
   # Neither a new tag/event handler nor external resource is allowed even with a new document digest.
   for payload in [b'<iframe src="https://example.com"></iframe>',b'<img src="https://example.com/a.png">',b'<p onclick="alert(1)">x</p>',b'<script>alert(1)</script>',b'<style>p{color:red}</style>']:
    changed=raw.replace(b'</body>',payload+b'</body>');policy=copy.deepcopy(self.policy);policy['documents'][r['filename']]=reports.sha(changed);(root/'data/report-v2-policy.json').write_text(json.dumps(policy))
    with self.assertRaises(ValueError):reports._parse_html(r,changed,root)
 def test_version_keying_preserves_all_sibling_links(self):
  self.assertEqual(len([x for x in reports.load_reports(ROOT) if x['paper_id']=='rpa-0062']),9)
  for r in self.records.values():
   page=self.pages[r['stage']]
   for other in reports.STAGE_FILES.values():
    if other!=r['filename']:self.assertIn('href="'+other+'"',page)
if __name__=='__main__':unittest.main()
