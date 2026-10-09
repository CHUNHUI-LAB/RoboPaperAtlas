import sys, unittest, tempfile, shutil, hashlib, gzip, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import navigation_product as product

class NavigationProductBuildTests(unittest.TestCase):
    def fixture(self):
        td=tempfile.TemporaryDirectory(dir=ROOT);self.addCleanup(td.cleanup);r=Path(td.name)
        shutil.copytree(ROOT/'data/navigation-product',r/'data/navigation-product')
        (r/'assets').mkdir()
        for name in product.ASSETS:shutil.copyfile(ROOT/'assets'/name,r/'assets'/name)
        return r
    def test_frozen_exact_science_bytes(self):
        raw,m=product.payloads(ROOT)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),product.MODEL_SHA256)
        self.assertEqual(len(m['papers']),87)
        self.assertEqual(len(m['template']['nodes']),59)
    def test_build_route_and_assets(self):
        r=self.fixture();dest=product.write_preview(r,r/'dist')
        page=(dest/'index.html').read_text()
        self.assertEqual({x.name for x in dest.iterdir()},product.PUBLIC_FILES)
        for name in product.ASSETS:self.assertIn('../../assets/'+name+'?v=',page)
        self.assertEqual(hashlib.sha256((dest/'product-data.json').read_bytes()).hexdigest(),product.MODEL_SHA256)
        self.assertEqual(page.count('data-tree-tab='),3)
        self.assertIn('原59节点模板',page)
    def test_missing_source_rejected(self):
        r=self.fixture();(r/'data/navigation-product/model.json.gz').unlink()
        with self.assertRaises(Exception):product.write_preview(r,r/'dist')
        self.assertFalse((r/'dist').exists())
    def test_corrupted_compressed_source_rejected(self):
        r=self.fixture();p=r/'data/navigation-product/model.json.gz';p.write_bytes(p.read_bytes()[:-5])
        with self.assertRaises(Exception):product.write_preview(r,r/'dist')
    def test_manifest_cannot_authorize_altered_science(self):
        r=self.fixture();p=r/'data/navigation-product/model.json.gz';p.write_bytes(gzip.compress(b'{}'));mp=p.with_name('manifest.json');m=json.loads(mp.read_text());m['compressedBytes']=p.stat().st_size;m['compressedSha256']=hashlib.sha256(p.read_bytes()).hexdigest();mp.write_text(json.dumps(m))
        with self.assertRaises(Exception):product.write_preview(r,r/'dist')
    def test_extra_input_rejected(self):
        r=self.fixture();(r/'data/navigation-product/notes.txt').write_text('private')
        with self.assertRaises(Exception):product.write_preview(r,r/'dist')
    def test_source_symlink_rejected(self):
        r=self.fixture();p=r/'data/navigation-product/model.json.gz';p.unlink();p.symlink_to(ROOT/'data/navigation-product/model.json.gz')
        with self.assertRaises(Exception):product.write_preview(r,r/'dist')
    def test_source_destination_rejected(self):
        with self.assertRaises(Exception):product.validate_preview(ROOT,ROOT/'data/navigation-product')
    def test_main_entry_and_preflight(self):
        self.assertIn('research/navigation/index.html',(ROOT/'scripts/map_page.py').read_text())
        for name in ('build.py','build_previews.py'):
            s=(ROOT/'scripts'/name).read_text();self.assertIn('validate_navigation_product(ROOT,',s)
            if name=='build.py':self.assertLess(s.index('validate_navigation_product(ROOT,'),s.index('shutil.rmtree(target)'))
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(Exception):product.exact_json('{"a":1,"a":2}')
