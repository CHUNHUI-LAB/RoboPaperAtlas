import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import assemble_frontier as a
class FrontierPartsTests(unittest.TestCase):
 def test_exact_original_bytes(self):self.assertEqual(a.read_parts(),(ROOT/'data/frontier.json').read_bytes())
 def test_small_independently_decodable_parts(self):
  manifest=json.loads((a.PARTS/'manifest.json').read_text())
  for part in manifest['parts']:
   data=(a.PARTS/part['path']).read_bytes();self.assertLessEqual(len(data),60000);data.decode('utf-8')
 def test_traversal_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   m=json.loads((a.PARTS/'manifest.json').read_text());m['parts'][0]['path']='../outside.txt';Path(tmp,'manifest.json').write_text(json.dumps(m))
   with self.assertRaises(ValueError):a.read_parts(Path(tmp))
 def test_tampered_part_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   m=json.loads((a.PARTS/'manifest.json').read_text());Path(tmp,'manifest.json').write_text(json.dumps(m));Path(tmp,m['parts'][0]['path']).write_text('tampered')
   with self.assertRaises(ValueError):a.read_parts(Path(tmp))
 def test_reordering_rejected(self):
  with tempfile.TemporaryDirectory() as tmp:
   m=json.loads((a.PARTS/'manifest.json').read_text());m['parts'].reverse();Path(tmp,'manifest.json').write_text(json.dumps(m))
   with self.assertRaises(ValueError):a.read_parts(Path(tmp))
if __name__=='__main__':unittest.main()
