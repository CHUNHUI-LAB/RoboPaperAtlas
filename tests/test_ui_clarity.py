import copy,hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import CATEGORIES,details,card,home
from topic_labels import TOPIC_CHINESE,classification
from presentation import overlay_status,metadata_label,doi_label,translate,edition_label,map_year_label
class UIClarityTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.catalog=json.loads((ROOT/'data/catalog.json').read_text());cls.byid={p['id']:p for p in cls.catalog['papers']}
 def test_chinese_primary_labels_keep_ids(self):
  self.assertEqual(set(CATEGORIES),set(TOPIC_CHINESE))
  for key,(label,_) in CATEGORIES.items():self.assertEqual(label,TOPIC_CHINESE[key])
  self.assertEqual(CATEGORIES['mobile-manipulation'][0],'移动操作');self.assertEqual(CATEGORIES['wbc'][0],'全身运动规划与控制')
  for pid in ['rpa-0070','rpa-0012']:
   p=self.byid[pid];self.assertIn(TOPIC_CHINESE[classification(p)['direction']],details(p))
 def test_metadata_scopes_are_separate_without_mutating_paper(self):
  p=self.byid['rpa-0012'];old=copy.deepcopy(p);s=details(p)
  self.assertIn('正式书目已核验（独立补充）',s);self.assertIn('原始书目：</strong>保留原始记录，尚未核验',s)
  self.assertIn('书目核验的两个范围',s);self.assertFalse(p['citation_verified']);self.assertEqual(p,old)
 def test_preprint_does_not_become_formal(self):
  p=copy.deepcopy(self.byid['rpa-0002']);self.assertEqual(metadata_label(p),'原始书目待核验')
  p['verified_overlay']['title']=p['title'];self.assertIn('正式出版未确认',metadata_label(p));self.assertNotIn('正式书目已核验',metadata_label(p))
  p=copy.deepcopy(self.byid['rpa-0012']);p['verified_overlay']={};self.assertIsNone(overlay_status(p));self.assertEqual(metadata_label(p),'原始书目待核验')
 def test_doi_absence_requires_explicit_note_and_primary_source(self):
  p=copy.deepcopy(self.byid['rpa-0012']);self.assertIn('PMLR 出版记录未列出 DOI',doi_label(p))
  p['notes']=[];self.assertEqual(doi_label(p),'尚未核验')
  p=copy.deepcopy(self.byid['rpa-0012']);p['sources']=[];self.assertEqual(doi_label(p),'尚未核验')
  p['doi']='10.1000/example';self.assertEqual(doi_label(p),'10.1000/example')
 def test_edition_and_reading_scope_not_conflated(self):
  s=details(self.byid['rpa-0012']);self.assertIn('已导入报告所用版本',s);self.assertIn('不据此推定全文阅读完成',s)
  self.assertIn('以下是 2026-09-30 的书目／链接核验记录；后续阅读范围见各阶段报告',s)
  self.assertIn('Stage 2 · v1：',s);self.assertIn('正式出版版：摘要、引言、讨论与局限',s)
  self.assertIn('Stage 3 · v1：',s);self.assertIn('方法与代码内容已审阅',s)
 def test_explicit_translations_preserve_qualifiers(self):
  p=self.byid['rpa-0012'];s=details(p)
  for phrase in ['会议／首次预印本年份为 2022','PMLR 正式引用年份为 2023','核验时旧项目链接','未运行代码或独立复现','腿式移动操作机器人的统一控制器']:
   self.assertIn(phrase,s)
  self.assertEqual(translate('new unfamiliar source note'),'new unfamiliar source note')
  self.assertEqual(edition_label('version_of_record'),'正式出版版本')
 def test_filter_retains_raw_record_semantics(self):
  self.assertIn('<label>原始书目核验状态<select id="status-filter">',home(self.catalog));self.assertIn('data-status="pending"',card(self.byid['rpa-0012']))
  self.assertEqual(sum(p['citation_verified'] for p in self.catalog['papers']),22)
  self.assertEqual(sum('data-status="verified"' in card(p) for p in self.catalog['papers']),22)
  self.assertIn('核验状态筛选只依据原始书目记录',home(self.catalog))
 def test_catalog_classification_and_reports_match_reviewed_roboduet_stage3_integration(self):
  expected={'data/catalog.json':'b10ba7d6451e698ea45c63c23fa336bda7cee13456b083bc70da40d2712dd247','data/classification.json':'9963a2f814fce16362ef039eaf44b6a49297594191904f09d8fca178506958e3','data/reports.json':'56902af42e1c975d8b627a589d7e11833fc8d2f3f9db760c6db3e061d79f216b'}
  for name,sha in expected.items():self.assertEqual(hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),sha)

 def test_map_year_label_requires_complete_formal_overlay(self):
  p=copy.deepcopy(self.byid['rpa-0012'])
  self.assertEqual(map_year_label(p),'2023 · 正式出版年（独立核验）；2022 · 原始记录年')
  p['verified_overlay']={};self.assertEqual(map_year_label(p),'2022 · 原始记录年')
  p['bibliographic_year']=None;self.assertEqual(map_year_label(p),'年份待核验')
  p=copy.deepcopy(self.byid['rpa-0012']);p['verified_overlay']['authors']=[]
  self.assertNotIn('独立核验',map_year_label(p))
  p=copy.deepcopy(self.byid['rpa-0012']);p['publication_status']='preprint_metadata_verified_publication_unresolved'
  self.assertNotIn('正式出版年',map_year_label(p))
