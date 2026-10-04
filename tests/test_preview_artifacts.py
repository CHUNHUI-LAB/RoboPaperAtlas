import unittest,json,hashlib,tempfile,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from preview_artifacts import read_preview,write_preview,ROUTE
from preview_reading import hydrate_reading_stages
class PreviewArtifactTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name);shutil.copytree(ROOT/'data/atlas-preview-parts',self.root/'data/atlas-preview-parts');self.index=self.root/'data/atlas-preview-parts/manifest.json'
 def tearDown(self):self.tmp.cleanup()
 def mutate(self,fn):
  x=json.loads(self.index.read_text());fn(x);self.index.write_text(json.dumps(x))
 def test_exact_transport_bytes_and_derived_output(self):
  for name in ('catalog.json','reports.json'):shutil.copyfile(ROOT/'data'/name,self.root/'data'/name)
  shutil.copytree(ROOT/'data/report-parts',self.root/'data/report-parts')
  for policy in (ROOT/'data').glob('report-*-policy.json'):shutil.copyfile(policy,self.root/'data'/policy.name)
  x=json.loads(self.index.read_text());b=read_preview(self.root);self.assertEqual(len(b),x['bytes']);self.assertEqual(hashlib.sha256(b).hexdigest(),x['sha256'])
  expected=hydrate_reading_stages(b,self.root,'prototype-data')
  self.assertNotEqual(expected,b)
  self.assertEqual(write_preview(self.root,self.root/'dist'),hashlib.sha256(expected).hexdigest());self.assertEqual((self.root/'dist'/ROUTE).read_bytes(),expected)
  self.assertEqual(read_preview(self.root),b)
  self.assertEqual(len(x['parts']),5);self.assertTrue(all(p['bytes']<=48000 for p in x['parts']))
 def test_part_tamper_and_reorder_fail(self):
  p=self.root/'data/atlas-preview-parts/part-001.txt';p.write_bytes(p.read_bytes()+b' ')
  with self.assertRaises(ValueError):read_preview(self.root)
  shutil.copyfile(ROOT/'data/atlas-preview-parts/part-001.txt',p);self.mutate(lambda x:x['parts'].reverse())
  with self.assertRaises(ValueError):read_preview(self.root)
 def test_route_and_unknown_fields_are_rejected(self):
  for fn in [lambda x:x.update(route='../index.html'),lambda x:x.update(private_note='x')]:
   self.index.write_bytes((ROOT/'data/atlas-preview-parts/manifest.json').read_bytes());self.mutate(fn)
   with self.assertRaises(ValueError):read_preview(self.root)
 def test_traversal_symlinks_and_duplicate_fields_fail(self):
  self.mutate(lambda x:x['parts'][0].update(path='../outside.txt'))
  with self.assertRaises(ValueError):read_preview(self.root)
  self.index.write_bytes((ROOT/'data/atlas-preview-parts/manifest.json').read_bytes());p=self.root/'data/atlas-preview-parts/part-001.txt';b=p.read_bytes();p.unlink();(self.root/'outside.txt').write_bytes(b);p.symlink_to(self.root/'outside.txt')
  with self.assertRaises(ValueError):read_preview(self.root)
  self.index.write_text('{"schema_version":1,"schema_version":1}')
  with self.assertRaises(ValueError):read_preview(self.root)
 def test_output_does_not_follow_symlink(self):
  out=self.root/'dist';out.mkdir();(out/'atlas-preview').symlink_to(self.root/'outside',target_is_directory=True)
  with self.assertRaises(ValueError):write_preview(self.root,out)
if __name__=='__main__':unittest.main()
