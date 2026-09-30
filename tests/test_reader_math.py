import json,sys,unittest,hashlib,re,copy,subprocess,html
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from reader_math import apply_math
from reader_preview import SOURCE_FILE,render
from build import shell,asset_url
class ReaderMathTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.mapping=json.loads((ROOT/'data/reader-math.json').read_text());cls.source=(ROOT/SOURCE_FILE).read_text();cls.math=apply_math(cls.source,ROOT);cls.page=render(ROOT,shell,asset_url)
 def test_exact_count_and_static_accessible_output(self):
  self.assertEqual(len(self.mapping['entries']),48);self.assertEqual(sum(len(e['occurrences'])for e in self.mapping['entries']),54)
  self.assertEqual(self.math.count('<math '),54);self.assertEqual(self.math.count('encoding="application/x-tex"'),54)
  self.assertNotIn('katex-error',self.math);self.assertEqual(self.math.count('class="math-source"'),3)
 def test_paper_code_and_explanation_are_distinct(self):
  entries={e['id']:e for e in self.mapping['entries']}
  self.assertNotIn('4\\exp',entries['eq-paper']['latex']);self.assertNotIn('lVert',entries['eq-paper']['latex'])
  self.assertIn('4\\exp',entries['eq-code']['latex']);self.assertIn('\\rVert^{2}',entries['eq-code']['latex'])
  for text in ['论文指数表达式','左侧 r_pose 为本文记号','代码等价式','坐标变换 · 阅读解释']:self.assertIn(text,self.page)
 def test_approved_source_images_and_code_unchanged(self):
  for pattern in [r'<img[^>]+src="([^"]+)"',r'<pre><code>(.*?)</code></pre>']:
   self.assertEqual(re.findall(pattern,self.source,re.S),re.findall(pattern,self.math,re.S))
 def test_section_hash_binding_fails_if_content_changes(self):
  with self.assertRaises(ValueError):apply_math(self.source.replace('id="reward">','id="reward">x'),ROOT)
 def test_reversing_exact_typesetting_recovers_entire_source(self):
  current=self.math;cache=json.loads((ROOT/'data/reader-math-rendered.json').read_text())['rendered'];labels={'eq-relative':'坐标变换 · 阅读解释','eq-paper':'论文指数表达式 · 左侧 r_pose 为本文记号','eq-code':'代码等价式 · 默认配置权重 4'}
  for e in self.mapping['entries']:
   if e['display_mode']:replacement='<span class="math-label">'+html.escape(labels[e['id']])+'</span>'+cache[e['id']]+'<details class="math-source"><summary>查看 LaTeX 源码</summary><pre>'+html.escape(e['latex'])+'</pre></details>'
   else:replacement='<span class="math-inline" data-math-id="'+e['id']+'">'+cache[e['id']]+'</span>'
   self.assertEqual(current.count(replacement),len(e['occurrences']));current=current.replace(replacement,e['original_html'])
  u=self.mapping['renderer_description'];current=current.replace('class="reader-equation"','class="formula"').replace(u['replacement_html'],u['original_html'])
  self.assertEqual(current,self.source)
 def test_dependencies_pinned_and_local_fonts_complete(self):
  package=json.loads((ROOT/'package.json').read_text());lock=json.loads((ROOT/'package-lock.json').read_text());self.assertEqual(package['devDependencies'],{'katex':'0.18.9'})
  self.assertTrue(lock['packages']['node_modules/katex']['integrity'].startswith('sha512-'))
  css=(ROOT/'assets/vendor/katex/katex.min.css').read_text();refs=re.findall(r'url\(([^)]+)\)',css);self.assertTrue(refs)
  for ref in refs:self.assertTrue((ROOT/'assets/vendor/katex'/ref).is_file());self.assertTrue(ref.endswith('.woff2'))
  self.assertNotIn('https:',css);self.assertTrue((ROOT/'assets/vendor/katex/LICENSE.txt').is_file())
  self.assertNotIn('katex.min.js',self.page);self.assertTrue((ROOT/'assets/vendor/katex/OFL.txt').is_file());self.assertIn('Reserved Font Name',(ROOT/'assets/vendor/katex/FONT-NOTICES.txt').read_text())
 def test_only_renderer_description_prose_changes(self):
  update=self.mapping['renderer_description'];self.assertIn(update['replacement_html'],self.math)
  self.assertNotIn(update['original_html'],self.math)
 def test_layout_has_compact_toc_and_chapter_navigation(self):
  self.assertIn('class="reader-body"',self.page);self.assertIn('title="模块五',self.page)
  for marker in ['data-reader-previous','data-reader-next','reader-position']:self.assertIn(marker,self.page)
  self.assertLess(self.page.index('data-reader-next'),self.page.index('class="reader-grid"'));self.assertEqual(self.page.count('data-reader-next'),1)
  self.assertIn('getComputedStyle(document.documentElement).scrollPaddingTop',(ROOT/'assets/reader-v2.js').read_text())
 def test_safe_renderer_rejects_external_commands(self):
  script=(ROOT/'scripts/render_math.cjs').read_text()
  for marker in ['trust:false','throwOnError:true',"strict:'error'",'maxExpand:1000','includegraphics','0.18.9']:self.assertIn(marker,script)
if __name__=='__main__':unittest.main()
