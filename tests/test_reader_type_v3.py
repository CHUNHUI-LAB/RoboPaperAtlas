import json,re,sys,hashlib,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from reports import load_reports,report_path
class ReaderTypeV3Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records=load_reports(ROOT);cls.bykey={(r['version'],r['stage']):r for r in cls.records if r['paper_id']=='rpa-0062'}
 def page(self,v,s):return(ROOT/report_path(self.bykey[(v,s)])).read_text()
 def test_content_figures_math_code_and_titles_are_exact(self):
  for stage in ['stage1','stage2','stage3']:
   a,b=self.page('v2',stage),self.page('v3',stage)
   article=lambda s:re.search(r'<article class="reader-article">(.*?)</article>',s,re.S)[1]
   self.assertEqual(hashlib.sha256(article(a).encode()).hexdigest(),hashlib.sha256(article(b).encode()).hexdigest())
   oldcss=re.search(r'<style data-report-style="reader-v2.css">(.*?)</style>',a,re.S)[1];newcss=re.search(r'<style data-report-style="reader-v2.css">(.*?)</style>',b,re.S)[1]
   title_rules=lambda css:[r[0]for r in re.finditer(r'[^{}]*(?:h1|h2|h3)[^{}]*\{[^{}]*\}',css)]
   self.assertEqual(title_rules(oldcss),title_rules(newcss));self.assertIn('font:17px/1.85 var(--font)',newcss)
   self.assertIn('.code-reader pre{font-size:12px;',newcss);self.assertIn('.reader-article figcaption{font-size:12px}',newcss)
   self.assertIn('报告版本 v3',b);self.assertIn('历史报告 v2',b)
 def test_source_button_specificity_and_contrast(self):
  css=(ROOT/'assets/reader-document.css').read_text();self.assertIn('.reader-page a.source-open,.reader-page a.source-open:hover,.reader-page a.source-open:focus-visible{color:#f2fff7;',css)
  def lum(h):
   x=[int(h[i:i+2],16)/255 for i in (0,2,4)];x=[v/12.92 if v<=.04045 else((v+.055)/1.055)**2.4 for v in x];return sum(a*b for a,b in zip(x,[.2126,.7152,.0722]))
  for background in ['173c2b','23513c']:self.assertGreater((lum('f2fff7')+.05)/(lum(background)+.05),7)
 def test_prior_artifacts_remain_hash_pinned_with_stage2_v4(self):
  for r in self.records:self.assertEqual(hashlib.sha256((ROOT/report_path(r)).read_bytes()).hexdigest(),r['sha256'])
  paper=next(p for p in json.loads((ROOT/'data/catalog.json').read_text())['papers']if p['id']=='rpa-0062')
  for key,s in paper['stages'].items():self.assertEqual([a['version']for a in s['artifacts']],(['v4'] if key=='stage2' else [])+['v3','v2','v1'])
