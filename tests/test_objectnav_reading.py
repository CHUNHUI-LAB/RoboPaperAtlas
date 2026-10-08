import copy
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import objectnav_reading_preview as reader
ROOT=Path(__file__).resolve().parents[1]
class Tags(HTMLParser):
    def __init__(self,text):
        super().__init__();self.ids=[];self.links=[];self.template_ids=[];self.feed(text)
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a)
        if 'data-template-id' in a:self.template_ids.append(a['data-template-id'])
def assigned(path):
    s=path.read_text();return json.loads(s[s.index('=')+1:].strip().rstrip(';'))
class ObjectNavReaderTests(unittest.TestCase):
    def setUp(self):
        self.payload,self.data=reader.payloads(ROOT)
        self.text=reader.render(self.data,self.payload)
    def test_exact_59_template_and_22_answers(self):
        legacy=ROOT/'previews/radar-c2-analysis/data'
        self.assertEqual(self.data['template'],assigned(legacy/'reference-complete.js')['analysis'])
        self.assertEqual(self.data['poni'],assigned(legacy/'scoped-analysis.js')['poni'])
        tags=Tags(self.text)
        self.assertEqual(len(tags.template_ids),59)
        self.assertEqual(set(tags.template_ids),{n['source_id'] for n in self.data['template']})
        self.assertEqual(self.text.count('已核部分 · '),22)
        self.assertEqual(self.text.count('未填写。保留原模板位置'),36) # + unfilled root = 37
        self.assertIn('原模板根节点未填写',self.text)
    def test_all_hash_links_exist_and_unique(self):
        tags=Tags(self.text)
        self.assertEqual(len(tags.ids),len(set(tags.ids)))
        for link in tags.links:
            if link['href'].startswith('#'):self.assertIn(link['href'][1:],tags.ids)
            if link['href'].startswith('https://'):
                self.assertEqual(link['target'],'_blank')
                self.assertIn('noopener',link['rel'])
    def test_scope_and_no_remote_data_or_state(self):
        for phrase in ['不是所有 ObjectNav','不是三阶段精读全部完成','22 / 59','37 个','固定 arXiv:2312.03275v1','1 m / 500 步','不能据此宣称完整 evaluator 等价','Interaction-free 不等于无需训练','仿真 PointNav','不能把评分当作校准目标存在概率']:
            self.assertIn(phrase,self.text)
        for banned in ['localStorage','sessionStorage','fetch(','innerHTML','pushState','replaceState','document.write']:
            self.assertNotIn(banned,self.payload['reader.js'].decode())
        self.assertNotIn('/workspace/',self.text)
        self.assertNotIn('content.json',self.text)
        self.assertIn('style.css?v=',self.text)
    def test_reader_dom_fixture_in_ci(self):
        subprocess.run(['node',str(ROOT/'tests/test_objectnav_reading.cjs')],check=True,capture_output=True,text=True,timeout=20)
    def test_narrow_and_keyboard_contract(self):
        css=self.payload['style.css'].decode()
        for value in ['max-width:600px','grid-template-columns:1fr','focus-visible','overflow-wrap:anywhere','minmax(0,1fr)','font-size:17px']:
            self.assertIn(value,css)
        self.assertIn('跳到正文',self.text)
        self.assertIn('tabindex="-1"',self.text)
    def sandbox(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup);root=Path(temp.name)
        shutil.copytree(ROOT/reader.SOURCE,root/reader.SOURCE)
        (root/'scripts').mkdir();shutil.copyfile(ROOT/reader.MANIFEST,root/reader.MANIFEST)
        return root
    def test_output_allowlist_repeated_build_and_no_data_publish(self):
        root=self.sandbox();dest=reader.write_preview(root,root/'dist')
        before={p.name:p.read_bytes() for p in dest.iterdir()}
        self.assertEqual(set(before),{'index.html','style.css','reader.js'})
        reader.write_preview(root,root/'dist');self.assertEqual(before,{p.name:p.read_bytes() for p in dest.iterdir()})
        (dest/'extra.txt').write_text('unexpected')
        with self.assertRaises(ValueError):reader.write_preview(root,root/'dist')
    def test_nonregular_output_rejected_before_any_write(self):
        root=self.sandbox();dest=reader.write_preview(root,root/'dist')
        (dest/'index.html').write_text('last good');(dest/'reader.js').unlink();(dest/'reader.js').mkdir()
        with self.assertRaises(ValueError):reader.write_preview(root,root/'dist')
        self.assertEqual((dest/'index.html').read_text(),'last good')
    def test_missing_extra_tampered_and_resealed_science_fail_closed(self):
        for kind in ['missing','extra','tamper','reseal','symlink']:
            with self.subTest(kind=kind):
                root=self.sandbox();content=root/reader.SOURCE/'content.json'
                if kind=='missing':content.unlink()
                elif kind=='extra':(content.parent/'extra.txt').write_text('x')
                elif kind=='symlink':content.unlink();content.symlink_to(ROOT/reader.SOURCE/'content.json')
                else:
                    content.write_text(content.read_text().replace('500','501'))
                    if kind=='reseal':
                        mp=root/reader.MANIFEST;m=json.loads(mp.read_text());m['files']['content.json']=hashlib.sha256(content.read_bytes()).hexdigest();mp.write_text(json.dumps(m))
                with self.assertRaises(ValueError):reader.write_preview(root,root/'dist')
                self.assertFalse((root/'dist'/reader.ROUTE).exists())
    def test_build_preflight_keeps_existing_output_on_bad_source(self):
        import build_previews as build
        root=self.sandbox();target=root/'dist';target.mkdir();sentinel=target/'last-good.txt';sentinel.write_text('keep')
        (root/reader.SOURCE/'content.json').unlink()
        with patch.object(build,'ROOT',root),patch.object(build,'validate_source'),patch.object(build,'validate_submit_source'),patch.object(build,'validate_c2_preview'),patch.object(sys,'argv',['build.py']),self.assertRaises(ValueError):
            build.main()
        self.assertEqual(sentinel.read_text(),'keep')
    def test_original_notes_visible(self):
        for n in self.data['template']:
            for key in ('note','interpretation_note','structural_note'):
                if n.get(key):self.assertIn(reader.esc(n[key]).replace('\n','<br>'),self.text)
        self.assertIn('不是隐瞒真实限制的指令',self.text)
    def test_forbidden_target_and_symlink_output(self):
        root=self.sandbox()
        for target in [root,root/'previews/nested',root/'scripts/other',root.parent/'escape']:
            with self.subTest(target=target),self.assertRaises(ValueError):reader.write_preview(root,target)
        (root/'dist').symlink_to(ROOT/'dist-exemplar',target_is_directory=True)
        with self.assertRaises(ValueError):reader.write_preview(root,root/'dist')
if __name__=='__main__':unittest.main()
