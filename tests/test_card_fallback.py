import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from build import card,card_description
class CardFallbackTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.papers=json.loads((ROOT/'data/catalog.json').read_text())['papers'];cls.byid={p['id']:p for p in cls.papers}
 def test_deep_wbc_three_reports_and_formal_overlay(self):
  p=self.byid['rpa-0012'];s=card_description(p)
  self.assertIn('正式书目已核验（独立补充）',s);self.assertIn('已导入 3 份阶段阅读报告',s);self.assertIn('具体阅读范围见各报告',s)
  self.assertNotIn('尚待逐项核验',s);self.assertNotIn('阅读档案尚未导入',card(p));self.assertNotIn('全文已读',s)
 def test_unread_raw_records_remain_pending(self):
  p=copy.deepcopy(self.byid['rpa-0012']);p['verified_overlay']={};p['stages']={k:dict(v,status='pending') for k,v in p['stages'].items()}
  self.assertIn('尚待逐项核验',card_description(p));self.assertIn('阅读档案尚未导入',card_description(p))
  found=[p for p in self.papers if not p.get('summary') and not p.get('verified_overlay') and not p['citation_verified'] and all(s['status']!='imported' for s in p['stages'].values())]
  self.assertTrue(found)
  for p in found:self.assertIn('阅读档案尚未导入',card_description(p))
 def test_metadata_and_reading_counts_independent(self):
  p=copy.deepcopy(self.byid['rpa-0012']);p['stages']['stage3']['status']='pending';self.assertIn('已导入 2 份',card_description(p))
  p['verified_overlay']={};self.assertIn('尚待逐项核验',card_description(p));self.assertIn('已导入 2 份',card_description(p))
  p['citation_verified']=True;self.assertIn('原始书目来源已核验',card_description(p));self.assertNotIn('尚待逐项核验',card_description(p))
 def test_explicit_summaries_preserved_verbatim(self):
  for p in self.papers:
   if p.get('summary'):self.assertEqual(card_description(p),p['summary'])
  p=copy.deepcopy(self.byid['rpa-0012']);p['summary']='Existing author-facing summary.';self.assertEqual(card_description(p),p['summary'])
 def test_no_record_mutation(self):
  before=copy.deepcopy(self.papers)
  for p in self.papers:card(p)
  self.assertEqual(before,self.papers)
 def test_problem_translation_is_presentation_only(self):
  s=card(self.byid['rpa-0012']);self.assertIn('协调运动',s);self.assertNotIn('>Coordinated Motion<',s);self.assertIn('data-problem-label="协调运动"',s)
