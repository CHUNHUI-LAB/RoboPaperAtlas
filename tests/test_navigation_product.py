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
        self.assertEqual(len(m['papers']),89)
        self.assertEqual(len(m['template']['nodes']),59)
    def test_build_route_and_assets(self):
        r=self.fixture();dest=product.write_preview(r,r/'dist')
        page=(dest/'index.html').read_text()
        self.assertEqual({x.name for x in dest.iterdir()},product.PUBLIC_FILES)
        for name in product.ASSETS:self.assertIn('../../assets/'+name+'?v=',page)
        self.assertEqual(hashlib.sha256((dest/'product-data.json').read_bytes()).hexdigest(),product.MODEL_SHA256)
        from html.parser import HTMLParser
        class Tabs(HTMLParser):
            values=[]
            def handle_starttag(self,tag,attrs):
                a=dict(attrs)
                if tag=='button' and a.get('role')=='tab':self.values.append(a.get('data-tree-tab'))
        tabs=Tabs();tabs.feed(page)
        self.assertEqual(tabs.values,['g','l','c'])
        self.assertIn('data-tree-tab="a"',page)
        self.assertIn('打开这篇论文的版本证据解析',page)
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


class NavigationEvidenceHistoryTests(unittest.TestCase):
    def setUp(self):
        self.previous_compressed=(ROOT/'tests/fixtures/navigation-product-20261008.json.gz').read_bytes()
        self.previous_raw=gzip.decompress(self.previous_compressed)
        self.previous=json.loads(self.previous_raw)
        self.current_raw=gzip.decompress((ROOT/'tests/fixtures/navigation-product-pr52-1229.json.gz').read_bytes())
        self.current=json.loads(self.current_raw)
    def test_explicit_historical_and_current_frozen_versions(self):
        self.assertEqual(hashlib.sha256(self.previous_compressed).hexdigest(),'75c02de2cb5e1a33db611598ed7c2b2253b14ea05e3edcb54862ab21cc290763')
        self.assertEqual(hashlib.sha256(self.previous_raw).hexdigest(),'a3d5b3cc579222c079701a84440bc2ee09621a682ff4603774fdfa2c41db7a7c')
        self.assertEqual(hashlib.sha256(self.current_raw).hexdigest(),'1229372f697316dc5c0627995fce7de18496160d85f4a1acb4ffc2a6faf1d708')
        self.assertEqual((len(self.previous['papers']),len(self.previous['claims']),len(self.previous['positions'])),(87,413,1557))
        self.assertEqual((len(self.current['papers']),len(self.current['claims']),len(self.current['positions'])),(89,436,1641))
    def test_every_historical_claim_and_position_identity_survives(self):
        for key,value in self.previous['claims'].items():self.assertEqual(self.current['claims'][key],value)
        for table in ('papers','entities','positions','relations'):
            self.assertTrue(set(self.previous[table])<=set(self.current[table]))
        for key,old in self.previous['positions'].items():
            for field in ('entityId','tree','scopeId','paperId','versionId','parentId','association'):
                self.assertEqual(self.current['positions'][key].get(field),old.get(field),(key,field))
        for old in self.previous['versions']:
            self.assertIn(self.current['versionAliases'].get(old,old),self.current['versions'])
        for name in ('template','analyses'):self.assertEqual(self.previous[name],self.current[name])
        changed={k for k in self.previous['coverage'] if self.previous['coverage'][k]!=self.current['coverage'][k]}
        self.assertEqual(changed,{'task:language-objectnav','setting:portable-objectnav','task:multistage-language-navigation'})
    def test_historical_input_cannot_impersonate_current_freeze(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as td:
            r=Path(td);shutil.copytree(ROOT/'data/navigation-product',r/'data/navigation-product');(r/'assets').mkdir()
            for name in product.ASSETS:shutil.copyfile(ROOT/'assets'/name,r/'assets'/name)
            p=r/'data/navigation-product/model.json.gz';p.write_bytes(self.previous_compressed)
            mp=p.with_name('manifest.json');manifest=json.loads(mp.read_text());manifest.update(sha256=hashlib.sha256(self.previous_raw).hexdigest(),bytes=len(self.previous_raw),compressedSha256=hashlib.sha256(self.previous_compressed).hexdigest(),compressedBytes=len(self.previous_compressed),expected={'papers':87,'claims':413,'positions':1557});mp.write_text(json.dumps(manifest))
            with self.assertRaises(Exception):product.write_preview(r,r/'dist')
            self.assertFalse((r/'dist').exists())
