"""Build the existing site once, then append two isolated allowlisted routes."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import build_previews as b

class BuildPreviewsTests(unittest.TestCase):
 def test_validates_then_builds_once_then_appends(self):
  order=[]
  with patch.object(b,'safe_target',side_effect=lambda root,target:order.append('target') or target),patch.object(b,'validate_source',side_effect=lambda root:order.append('source')),patch.object(b,'validate_submit_source',side_effect=lambda *a:order.append('submit-source')),patch.object(b.subprocess,'run',side_effect=lambda *a,**kw:order.append('build')) as run,patch.object(b,'write_preview',side_effect=lambda *a:order.append('preview')) as write,patch.object(b,'write_submit_preview',side_effect=lambda *a:order.append('submit')) as submit:
   b.main(['--output','dist-test'])
  self.assertEqual(order,['target','source','submit-source','build','preview','submit'])
  run.assert_called_once_with([sys.executable,str(b.ROOT/'scripts/build.py'),'--output','dist-test'],check=True)
  write.assert_called_once_with(b.ROOT,b.ROOT/'dist-test');submit.assert_called_once_with(b.ROOT,b.ROOT/'dist-test')
 def test_failed_base_build_does_not_append(self):
  with patch.object(b,'safe_target'),patch.object(b,'validate_source'),patch.object(b,'validate_submit_source'),patch.object(b.subprocess,'run',side_effect=subprocess.CalledProcessError(1,'build')),patch.object(b,'write_preview') as write,patch.object(b,'write_submit_preview') as submit:
   with self.assertRaises(subprocess.CalledProcessError):b.main([])
  write.assert_not_called();submit.assert_not_called()
 def test_invalid_source_blocks_base_build(self):
  with patch.object(b,'safe_target'),patch.object(b,'validate_source'),patch.object(b,'validate_submit_source',side_effect=ValueError('bad source')),patch.object(b.subprocess,'run') as run:
   with self.assertRaises(ValueError):b.main([])
  run.assert_not_called()

class SubmissionAllowlistTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name).resolve();self.source=self.root/'submit-preview';(self.source/'data').mkdir(parents=True)
  for name in b.SUBMIT_FILES:(self.source/name).write_text('public '+name)
  self.target=self.root/'dist';self.target.mkdir();(self.target/'index.html').write_text('unchanged main')
 def test_only_four_files_added_and_repeat_is_safe(self):
  for _ in range(2):b.write_submit_preview(self.root,self.target)
  self.assertEqual((self.target/'index.html').read_text(),'unchanged main')
  self.assertEqual({p.relative_to(self.target/'submit-preview').as_posix() for p in (self.target/'submit-preview').rglob('*') if p.is_file()},set(b.SUBMIT_FILES))
  for name in b.SUBMIT_FILES:self.assertEqual((self.source/name).read_bytes(),(self.target/'submit-preview'/name).read_bytes())
 def test_missing_file(self):
  (self.source/'app.js').unlink()
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
 def test_extra_file_and_directory(self):
  for name in ['private.txt','unexpected']:
   p=self.source/name;p.write_text('x') if '.' in name else p.mkdir()
   with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
   p.unlink() if p.is_file() else p.rmdir()
 def test_source_symlink(self):
  p=self.source/'app.js';p.unlink();p.symlink_to(self.target/'index.html')
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
 def test_source_directory_symlink(self):
  p=self.source/'data';(p/'venues.json').unlink();p.rmdir();other=self.root/'other';other.mkdir();(other/'venues.json').write_text('x');p.symlink_to(other,target_is_directory=True)
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
 def test_destination_symlink(self):
  (self.target/'submit-preview').symlink_to(self.source,target_is_directory=True)
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
 def test_extra_destination_file(self):
  b.write_submit_preview(self.root,self.target);(self.target/'submit-preview/private.txt').write_text('x')
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
 def test_escape_and_source_overlap(self):
  for target in [self.root,self.root.parent/'outside',self.root/'dist/../escape',self.source,self.source/'nested']:
   with self.subTest(target=target),self.assertRaises(ValueError):b.write_submit_preview(self.root,target)
 def test_regular_file_required(self):
  p=self.source/'app.js';p.unlink();p.mkdir()
  with self.assertRaises(ValueError):b.write_submit_preview(self.root,self.target)
if __name__=='__main__':unittest.main()
