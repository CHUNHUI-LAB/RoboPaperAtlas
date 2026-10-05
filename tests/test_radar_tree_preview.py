import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from radar_tree_preview import FILES, MANIFEST, ROUTE, SOURCE, payloads, write_preview

class RadarTreePreviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        shutil.copytree(ROOT / SOURCE, self.root / SOURCE)
        (self.root / 'scripts').mkdir()
        shutil.copyfile(ROOT / MANIFEST, self.root / MANIFEST)
    def test_exact_reviewed_bytes_and_repeat_build(self):
        before = payloads(self.root)
        for _ in range(2):
            write_preview(self.root, self.root / 'dist')
            out = self.root / 'dist' / ROUTE
            self.assertEqual({p.relative_to(out).as_posix() for p in out.rglob('*') if p.is_file()}, FILES)
            self.assertEqual({n:(out/n).read_bytes() for n in FILES}, before)
    def test_missing_source(self):
        (self.root/SOURCE/'index.html').unlink()
        with self.assertRaises(ValueError): payloads(self.root)
    def test_extra_source(self):
        (self.root/SOURCE/'private.json').write_text('{}')
        with self.assertRaises(ValueError): payloads(self.root)
    def test_changed_bytes(self):
        (self.root/SOURCE/'graph.js').write_text('changed')
        with self.assertRaises(ValueError): payloads(self.root)
    def test_manifest_cannot_expand_allowlist(self):
        p=self.root/MANIFEST;m=json.loads(p.read_text());m['files']['private.json']='0'*64;p.write_text(json.dumps(m))
        with self.assertRaises(ValueError): payloads(self.root)
    def test_source_symlink(self):
        p=self.root/SOURCE/'index.html';p.unlink();p.symlink_to(ROOT/SOURCE/'index.html')
        with self.assertRaises(ValueError): payloads(self.root)
    def test_output_symlink(self):
        (self.root/'dist').symlink_to(self.root/SOURCE,target_is_directory=True)
        with self.assertRaises(ValueError): write_preview(self.root,self.root/'dist')
    def test_source_overlap(self):
        for target in (self.root,self.root/'previews',self.root/SOURCE,self.root/SOURCE/'nested'):
            with self.assertRaises(ValueError): write_preview(self.root,target)
    def test_outside_target(self):
        with self.assertRaises(ValueError): write_preview(self.root,self.root.parent/'escape')
    def test_unexpected_output(self):
        dest=self.root/'dist'/ROUTE;dest.mkdir(parents=True);(dest/'private.json').write_text('{}')
        with self.assertRaises(ValueError): write_preview(self.root,self.root/'dist')
    def test_output_fifo_rejected_without_open(self):
        write_preview(self.root,self.root/'dist')
        p=self.root/'dist'/ROUTE/'index.html';p.unlink();os.mkfifo(p)
        with self.assertRaises(ValueError): write_preview(self.root,self.root/'dist')
    def test_output_hardlink_does_not_modify_original(self):
        write_preview(self.root,self.root/'dist')
        original=self.root/'keep.txt';original.write_text('keep')
        p=self.root/'dist'/ROUTE/'index.html';p.unlink();os.link(original,p)
        write_preview(self.root,self.root/'dist')
        self.assertEqual(original.read_text(),'keep')
    def test_acceptance_not_promoted(self):
        p=self.root/MANIFEST;m=json.loads(p.read_text());m['status']='approved';p.write_text(json.dumps(m))
        with self.assertRaises(ValueError): payloads(self.root)
    def test_actual_builder_rejects_source_before_deleting(self):
        before=payloads(ROOT)
        run=subprocess.run([sys.executable,str(ROOT/'scripts/build.py'),'--output',SOURCE],capture_output=True,text=True)
        self.assertNotEqual(run.returncode,0)
        self.assertIn('overlap',run.stderr)
        self.assertEqual(payloads(ROOT),before)
    def test_c_model_and_dom_contract(self):
        subprocess.run(['node',str(ROOT/'tests/test_radar_tree_c.cjs')],check=True,capture_output=True,text=True,timeout=30)
    def test_normal_builder_and_ci_wrapper_retain_route(self):
        self.assertIn('write_radar_tree_preview(ROOT, target)',(ROOT/'scripts/build.py').read_text())
        self.assertIn("ROOT / 'scripts/build.py'",(ROOT/'scripts/build_previews.py').read_text())

if __name__ == '__main__': unittest.main()
