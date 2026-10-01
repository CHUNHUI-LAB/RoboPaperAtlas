"""Image-only correction with immutable v1 history and unchanged reading text."""
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from reports import load_reports,report_path
from validate import expected_stage

# Exact image outputs independently visually checked against the same PDF crops.
IMAGES = {
 'fig-1': (812,396,'23120b197630ca15e6136f5eba617db06969fb79618b1979cf28b776c1d65421'),
 'fig-2': (816,514,'4ea637c350079db6c7544c70c72871dd8f57fe6238646ca607fe0ac79ffa6b6f'),
 'fig-3': (376,330,'ad4ad7c92e438c6476d0f5c0225f2ebbfaa284ba7dbb223bcc7dcb5943fcb140'),
 'fig-4': (368,360,'7b770013e9b87cdd03bd600670956e955847be62c51654ffc1c96d0a2bbcc6f7'),
 'fig-5': (808,380,'69e0ecf838e31799eb8d9209cf3c7b60a69a01a5ab667ea3dd9366f85b340d5d'),
 'fig-6': (808,316,'0e7c9298bdf01a832513505164c8dd0a6f867d023292f6b2f87e193545c125b7'),
 'fig-7': (806,464,'42f15253a4a401a82c37f8fa940b57bac8fe29244ffccb8f195b3339c601c146'),
 'supp-fig-2': (812,354,'63c981704ea6397fafcfa7ed3a6d40c9b9dedbae9f6e76d784bb347b6a16b3b7'),
 'supp-fig-3': (732,370,'697540efd0c5a0ece6fb2213fe35b0b6e4317159a3842b519ad726ec51a8112a'),
}
class DeepWBCImageV2Tests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.records=load_reports(ROOT)
  cls.deep={x['version']:x for x in cls.records if x['paper_id']=='rpa-0012'}
  cls.pages={v:(ROOT/report_path(x)).read_text() for v,x in cls.deep.items()}
 def test_all_nine_images_match_reviewed_nonrotated_outputs(self):
  images=re.findall(r'<figure id="([^"]+)"><img src="data:image/png;base64,([^"]+)"',self.pages['v2'])
  self.assertEqual(len(images),9);self.assertEqual({n for n,_ in images},set(IMAGES))
  for name,data in images:
   raw=base64.b64decode(data,validate=True);w,h,digest=IMAGES[name]
   self.assertEqual(struct.unpack('>II',raw[16:24]),(w,h));self.assertEqual(hashlib.sha256(raw).hexdigest(),digest)
 def test_entire_nonimage_document_unchanged_except_version_badge(self):
  def normalize(s):return re.sub(r'data:image/png;base64,[A-Za-z0-9+/=]+','IMAGE_BYTES',s).replace('STAGE 1 · v2 · 初读内容已审阅','STAGE 1 · v1 · 初读内容已审阅')
  self.assertEqual(normalize(self.pages['v1']),normalize(self.pages['v2']))
  self.assertEqual(hashlib.sha256(normalize(self.pages['v2']).encode()).hexdigest(),'69fc16b1e988b6cc68998c16d00f155ef8564585073d018e0ee338b454990df0')
 def test_published_v1_and_script_remain_exact(self):
  self.assertEqual(hashlib.sha256(self.pages['v1'].encode()).hexdigest(),'d2d80d400328afe4adac2e94d4761ce87d51dcdb000c5bd7e5bca22e3be357b1')
  for v in ['v1','v2']:
   self.assertEqual(hashlib.sha256(re.search(r'<script>(.*?)</script>',self.pages[v],re.S)[1].encode()).hexdigest(),'d6a59075a1b640bb5abca8f6a34d32041ac211b68f959e20adaf51e5019d2798')
 def test_v2_is_current_with_v1_history_and_no_future_stage_promotion(self):
  cat=json.loads((ROOT/'data/catalog.json').read_text());p=next(x for x in cat['papers'] if x['id']=='rpa-0012')
  self.assertEqual(p['stages']['stage1'],expected_stage('rpa-0012','stage1',self.records))
  self.assertEqual([x['version'] for x in p['stages']['stage1']['artifacts']],['v2','v1'])
  for stage in ['stage2','stage3']:self.assertEqual(p['stages'][stage],{'status':'not_imported','artifacts':[]})
  self.assertEqual(len([x for x in self.records if x['paper_id']=='rpa-0062']),9)
 def test_policy_versions_are_separate_and_source_edition_is_unchanged(self):
  a=json.loads((ROOT/'data/report-rpa-0012-v1-policy.json').read_text());b=json.loads((ROOT/'data/report-rpa-0012-v2-policy.json').read_text())
  self.assertEqual(a['version'],'v1');self.assertEqual(b['version'],'v2');self.assertNotEqual(a['document_sha256'],b['document_sha256'])
  for k in ['source_pdf_sha256','script_sha256','title','paper_id','stage','filename']:self.assertEqual(a[k],b[k])
  for k in ['source_sha256','source_url','pdf_url','source_edition','review_status']:self.assertEqual(self.deep['v1'][k],self.deep['v2'][k])
  self.assertIn('仅更正九幅图',self.deep['v2']['rights_note'])

if __name__=='__main__':unittest.main()
