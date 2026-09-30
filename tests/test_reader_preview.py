import html,json,re,sys,unittest
from pathlib import Path
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import shell,asset_url
from reader_preview import render,SOURCE_FILE,COMMIT,colored_lines
class CodeText(HTMLParser):
 def __init__(self):super().__init__();self.depth=0;self.lines=[];self.active=False
 def handle_starttag(self,t,a):
  d=dict(a)
  if self.active:self.depth+=1
  elif t=='span' and d.get('class')=='code-text':self.active=True;self.depth=1;self.lines.append('')
 def handle_endtag(self,t):
  if self.active:
   self.depth-=1
   if self.depth==0:self.active=False
 def handle_data(self,s):
  if self.active:self.lines[-1]+=s
class ReaderPreviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.source=(ROOT/SOURCE_FILE).read_text();cls.page=render(ROOT,shell,asset_url)
 def test_real_shared_shell_and_one_page_scope(self):
  self.assertIn('class="site-header"',self.page)
  for name in ['Library','Atlas','Radar']:self.assertIn('>'+name+'</a>',self.page)
  self.assertIn('Reader preview',self.page);self.assertIn('不会替换已发布报告',self.page);self.assertIn('已发布 v1',self.page)
 def test_all_nine_code_blocks_preserve_exact_source(self):
  source=re.findall(r'<pre><code>(.*?)</code></pre>',self.source,re.S);blocks=re.findall(r'<div class="code-reader".*?<pre[^>]*>(.*?)</pre>',self.page,re.S)
  self.assertEqual(len(blocks),9);self.assertEqual(len(source),9)
  for before,after in zip(source,blocks):
   p=CodeText();p.feed(after);self.assertEqual('\n'.join(p.lines),html.unescape(before))
 def test_real_source_line_numbers_and_static_color(self):
  for marker in ['code-pose_sequence-76-L76','code-pose_sequence-76-L87','code-wbc_node-967-L967','code-wbc_node-967-L976','tok-keyword','tok-string','tok-comment','tok-number','tok-call']:self.assertIn(marker,self.page)
  self.assertEqual(self.page.count('data-copy-code'),9);self.assertEqual(self.page.count('data-code-focus'),9)
 def test_upstream_pinned_links_are_preserved(self):
  refs=set(re.findall(r'href="(https://github.com/real-stanford/umi-on-legs/[^\"]+)"',self.source))
  for ref in refs:self.assertIn('href="'+ref+'"',self.page)
  self.assertIn(COMMIT,self.page)
 def test_images_reused_without_pixel_changes(self):
  images=lambda s:re.findall(r'<img[^>]+src="([^"]+)"',s)
  self.assertEqual(images(self.source),images(self.page));self.assertEqual(len(images(self.page)),6)
 def test_no_external_pdf_embed_or_execution(self):
  self.assertNotIn('<iframe',self.page);self.assertNotIn('<object',self.page);self.assertIn('未执行',self.page)
  js=(ROOT/'assets/reader-v2.js').read_text();self.assertNotIn('eval(',js);self.assertNotIn('innerHTML',js);self.assertNotIn('fetch(',js);self.assertIn('prefers-reduced-motion',js)
 def test_current_report_artifacts_stay_hash_identical(self):
  import hashlib
  records=json.loads((ROOT/'data/reports.json').read_text())['reports']
  for record in records:
   p=ROOT/'artifacts'/record['paper_id']/record['version']/record['filename'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),record['sha256'])
 def test_code_escaping_and_plain_text_roundtrip(self):
  raw='x = "<script>&hello" # comment';p=CodeText();p.feed('<span class="code-text">'+colored_lines(raw)[0]+'</span>');self.assertEqual(p.lines,[raw]);self.assertNotIn('<script>',colored_lines(raw)[0])
 def test_anchor_offset_is_single_and_toc_uses_computed_padding(self):
  css=(ROOT/'assets/reader-v2.css').read_text();js=(ROOT/'assets/reader-v2.js').read_text()
  self.assertIn('--reader-anchor-offset:144px',css);self.assertIn('.reader-article>section{scroll-margin-top:0;',css)
  self.assertNotIn('scroll-margin-top:144px',css);self.assertNotIn('scroll-padding-top:134px',css)
  self.assertIn('getComputedStyle(document.documentElement).scrollPaddingTop',js)
 def test_mobile_catalog_search_basis_fixed(self):
  css=(ROOT/'assets/experience.css').read_text();self.assertIn('.catalog-search-trigger{flex-basis:auto;',css)
if __name__=='__main__':unittest.main()
