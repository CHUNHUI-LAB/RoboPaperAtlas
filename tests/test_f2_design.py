"""Presentation-only F2 integration and preservation checks; not browser pixel QA."""
import hashlib,json,re,sys,unittest
from html.parser import HTMLParser
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from build import home,details,shell
from reports import assemble_reports,report_path
from current_reader import render as reader,entry_path

class Links(HTMLParser):
 def __init__(self,text):
  super().__init__();self.links=[];self.feed(text)
 def handle_starttag(self,tag,attrs):
  attrs=dict(attrs)
  if tag=='link' and attrs.get('rel')=='stylesheet':self.links.append(attrs.get('href',''))

class F2DesignTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.data=json.loads((ROOT/'data/catalog.json').read_text());cls.records=assemble_reports(ROOT)
 def test_shared_theme_has_last_stylesheet_precedence(self):
  for page,prefix in [('catalog',''),('detail','../../'),('reading','../'),('map','../'),('frontier','../'),('submit','../'),('about','../')]:
   document=shell('test','<main id="main"></main>',prefix,page)
   self.assertIn('f2-theme',document)
   self.assertRegex(Links(document).links[-1],re.escape(prefix)+r'assets/f2.css\?v=[0-9a-f]{12}$')
 def test_catalog_preserves_all_95_ids_filters_and_real_descriptions(self):
  document=home(self.data)
  self.assertIn('<h1>论文库</h1>',document)
  self.assertEqual(document.count('class="paper-card library-paper"'),95)
  self.assertEqual(document.count('class="f2-paper-description"'),95)
  for paper in self.data['papers']:self.assertIn('data-preview="'+paper['id']+'"',document)
  for name in ['search','topic-select','direction-filter','method-filter','resource-filter','year-filter','status-filter','reading-filter','sort','reset-filters','clear-all-filters']:self.assertIn('id="'+name+'"',document)
 def test_paper_details_lead_with_real_resources_and_reading_path(self):
  for paper in self.data['papers']:
   page=details(paper)
   self.assertIn('class="f2-detail-resources"',page)
   self.assertLess(page.index('id="reading"'),page.index('id="overview"'))
   for state in paper['stages'].values():
    for artifact in state['artifacts']:self.assertIn('href="../../'+artifact['path']+'"',page)
 def test_live_readers_leave_figures_math_code_and_article_byte_identical(self):
  seen=0
  for paper in self.data['papers']:
   for stage,state in paper['stages'].items():
    if state['status']!='imported' or not entry_path(paper['id'],stage):continue
    fixed=(ROOT/state['artifacts'][0]['path']).read_text();live=reader(ROOT,paper,stage,self.records);seen+=1
    self.assertIn('f2-current-reader',live)
    self.assertRegex(Links(live).links[-1],r'../../../assets/f2.css\?v=[0-9a-f]{12}$')
    for tag in ['article','figure','img','svg','pre','style']:
     pattern=r'<img\b[^>]*>' if tag=='img' else rf'<{tag}\b.*?</{tag}>'
     self.assertEqual(re.findall(pattern,fixed,re.S),re.findall(pattern,live,re.S),(paper['id'],stage,tag))
  self.assertEqual(seen,12)
 def test_all_21_immutable_artifacts_match_registry(self):
  self.assertEqual(len(self.records),21)
  for record in self.records:self.assertEqual(hashlib.sha256((ROOT/report_path(record)).read_bytes()).hexdigest(),record['sha256'])
 def test_reader_collapsed_states_have_no_reserved_empty_layout(self):
  css=(ROOT/'assets/f2.css').read_text()
  self.assertIn('.f2-current-reader .reader-stage2.reader-source-collapsed .reader-grid{grid-template-columns:184px minmax(0,1fr)}',css)
  mobile=css[css.rfind('@media(max-width:767px)'):]
  self.assertIn('.f2-current-reader .reader-toc{display:none;position:static;',mobile)
  self.assertIn('.f2-current-reader .reader-toc.is-open{display:block;',mobile)
  self.assertIn('visibility:visible;opacity:1',mobile)
  self.assertIn('reader-stage2.reader-source-collapsed .reader-grid{display:block}',mobile)
 def test_svg_metadata_and_small_text_meet_minimum(self):
  self.assertIn('meta.style.fontSize = `${14 * scale}px`',(ROOT/'assets/paper-map.js').read_text())
  css=(ROOT/'assets/f2.css').read_text()
  self.assertIn('.f2-theme small{font-size:14px!important;line-height:1.65}',css)
  for rule in ['a.code-cite{font-size:14px',':is(th,td){font-size:16px','summary{font-size:16px']:
   self.assertIn('.f2-current-reader .reader-article '+rule,css)
  for marker in ['.code-language','.code-number','.code-toolbar a','.code-foot a','.reader-equation .math-label','figure label','figure summary','.reader-paper-link span','.reader-section-stepper>span']:
   self.assertIn('.f2-current-reader .reader-',css)
   self.assertIn(marker,css)
 def test_hosted_corrections_preserve_titles_and_focusable_results(self):
  css=(ROOT/'assets/f2.css').read_text()
  self.assertIn('.f2-theme .mobile-menu{width:auto;white-space:nowrap;flex-shrink:0}',css)
  document=home(self.data)
  self.assertIn('<div class="results-bar" id="catalog-results"><div class="catalog-heading">',document)
  self.assertEqual(document.count('id="catalog-title"'),1)
  self.assertIn("description.hidden = topic === 'all'",(ROOT/'assets/app.js').read_text())
  paper=next(p for p in self.data['papers'] if p['id']=='rpa-0062')
  page=details(paper)
  self.assertIn('<h1>UMI-on-Legs</h1>',page)
  self.assertIn('<p class="f2-full-paper-title">',page)
  self.assertIn(paper['verified_overlay']['title'],page)
 def test_live_reader_header_uses_shared_labels(self):
  paper=next(p for p in self.data['papers'] if p['id']=='rpa-0062')
  page=reader(ROOT,paper,'stage2',self.records)
  header=re.search(r'<header\b.*?</header>',page,re.S)[0]
  self.assertIn('>星图</a>',header);self.assertIn('>前沿动态</a>',header)
  self.assertNotIn('>Atlas</a>',header);self.assertNotIn('>Radar</a>',header)
  for current in self.data['papers']:
   for stage,state in current['stages'].items():
    if state['status']!='imported':continue
    h=re.search(r'<header\b.*?</header>',reader(ROOT,current,stage,self.records),re.S)[0]
    for legacy in ['Library','Atlas','Radar']:
     self.assertNotIn('>'+legacy+'</a>',h)
 def test_standard_headers_keep_archive_link_and_copy_is_not_external(self):
  for page in ['catalog','detail','map','frontier','reading','submit','about']:
   document=shell('test','<main id="main"></main>',prefix='../../',page=page,library=page=='catalog')
   nav=re.search(r'<nav id="main-nav".*?</nav>',document,re.S)[0]
   self.assertEqual(nav.count('reading/index.html'),1,page)
   for label in ['论文库','星图','前沿动态','阅读档案','投稿指南','关于与贡献']:
    self.assertIn(label,nav,page)
  document=details(self.data['papers'][0])
  self.assertIn('class="copy-page" type="button">复制本页链接</button>',document)
  self.assertNotIn('复制本页链接 ↗',document)
 def test_design_contract_and_no_external_fonts(self):
  css=(ROOT/'assets/f2.css').read_text()
  for contract in ['font-size:18px','font-size:16px','font-size:14px','line-height:1.65','min-height:44px','--f2-hover:160ms','--f2-panel:220ms','--f2-radius:8px','--f2-panel-radius:12px','prefers-reduced-motion:reduce',':focus-visible']:
   self.assertIn(contract,css)
  self.assertNotIn('@import',css);self.assertNotIn('@font-face',css);self.assertNotIn('https:',css)
  self.assertEqual(css.count('{'),css.count('}'))
if __name__=='__main__':unittest.main()
