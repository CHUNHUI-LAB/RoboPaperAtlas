"""The initial public preview must not promote any canonical reading state."""
import hashlib,json,re,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import reports as r
import navigation_stage1_preview as preview
BASE=json.loads((ROOT/'tests/fixtures/navigation-preview-baseline.json').read_text())
sha=lambda raw:hashlib.sha256(raw).hexdigest()
class IsolatedPreview(unittest.TestCase):
 def test_exact_four_additive_runtime_files_only(self):
  changed={name for name,h in BASE['source_sha256'].items()if sha((ROOT/name).read_bytes())!=h}
  self.assertEqual(changed,{'scripts/build.py','scripts/current_reader.py','scripts/reports.py','scripts/validate.py'})
 def test_canonical_catalog_reports_radar_classification_unchanged(self):
  for name,h in BASE['source_sha256'].items():
   if name.startswith(('data/','.github/','assets/')):self.assertEqual(sha((ROOT/name).read_bytes()),h,name)
  records=r.load_reports(ROOT);self.assertEqual(len(records),21)
  catalog=json.loads((ROOT/'data/catalog.json').read_text())
  for p in catalog['papers']:
   if p['id']in preview.IDS:self.assertTrue(all(v=={'status':'not_imported','artifacts':[]}for v in p['stages'].values()))
 def test_every_existing_output_retained_except_declared_cache_marker(self):
  for name,h in BASE['output_normalized_sha256'].items():
   p=ROOT/'dist'/name;self.assertTrue(p.is_file(),name);raw=p.read_bytes()
   if p.suffix=='.html':raw=re.sub(rb'data-data-version="[0-9a-f]{12}"',b'data-data-version="BASELINE-VERSION"',raw)
   self.assertEqual(sha(raw),h,name)
 def test_exactly_seven_new_outputs_no_pdf_or_extra_artifact(self):
  old=set(BASE['output_sha256']);new={str(p.relative_to(ROOT/'dist'))for p in(ROOT/'dist').rglob('*')if p.is_file()}
  expected=set(preview.output_payloads(ROOT));self.assertEqual(new-old,expected);self.assertEqual(old-new,set());self.assertEqual(len(expected),7)
  artifacts={str(p.relative_to(ROOT/'dist'))for p in(ROOT/'dist/artifacts').rglob('*')if p.is_file()}
  self.assertEqual(artifacts,{r.report_path(x)for x in r.load_reports(ROOT)})
  self.assertFalse(any(name.endswith('.pdf')for name in expected))
if __name__=='__main__':unittest.main()
