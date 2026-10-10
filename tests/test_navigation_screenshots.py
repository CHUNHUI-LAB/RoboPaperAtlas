"""Transport-only checks; actual Chrome pixels are produced in the PR job."""
import importlib.util
import io
import json
from pathlib import Path
import unittest
import struct
import subprocess
import zlib
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('navigation_screenshots', Path(__file__).parents[1] / 'scripts/navigation_screenshots.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ScreenshotChecks(unittest.TestCase):
    def test_parallel_root_selector_preserves_tree_level_and_excludes_nested_groups(self):
        driver = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
const selector=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<section id="panel"><h3>Tree</h3><ul role="tree"><li role="treeitem" data-position="root"><ul role="group"><li role="treeitem" data-position="child"></li></ul></li></ul><div><ul role="tree"><li role="treeitem" data-position="unrelated"></li></ul></div></section>');
try {
 const p=dom.window.document.getElementById('panel');
 assert.deepEqual([...p.querySelectorAll(selector)].map(n=>n.dataset.position),['root']);
 assert.deepEqual([...p.querySelectorAll(':scope > [role=group] > [role=treeitem]')],[], 'old selector loses real tree roots');
 p.querySelector(':scope > [role=tree]').setAttribute('role','group');
 assert.deepEqual([...p.querySelectorAll(selector)],[], 'nested-group semantics must not substitute for a forest root');
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', driver], input=json.dumps(MODULE.PARALLEL_ROOT_SELECTOR),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_dom_status_selector_ignores_nested_new_tab_label(self):
        driver = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
const script=JSON.parse(require('fs').readFileSync(0,'utf8'));
function run(markup,check){const d=new JSDOM(markup,{runScripts:'outside-only'});try{const pick=new d.window.Function(script);check(d.window.document,(kind,id='source-1')=>pick.call(d.window,'relation-1',{kind,id}));}finally{d.window.close();}}
const start='<article data-task-relation="relation-1"><strong>Relation</strong><p><a data-task-relation-source="source-1" href="https://example.org/v1">Original source<span class="sr-only">（新标签页）</span></a>';
run(start+'<span id="actual-status"> · 未固定全文快照</span></p></article>',(d,pick)=>{
 assert.equal(pick('status'),d.getElementById('actual-status'));
 assert.equal(pick('status').textContent,' · 未固定全文快照');
 assert.equal(pick('source'),d.querySelector('a'));
 assert.notEqual(pick('status'),d.querySelector('.sr-only'));
 assert.throws(()=>pick('status','unknown'),/Exact source anchor missing/);
});
run(start+'</p></article>',(d,pick)=>assert.throws(()=>pick('status'),/Exact source status sibling missing/));
run(start+'<em>wrong sibling</em><span> · 未固定全文快照</span></p></article>',(d,pick)=>{assert.equal(d.querySelector('a').nextElementSibling.tagName,'EM');assert.throws(()=>pick('status'),/Exact source status sibling missing/);});
"""
        result = subprocess.run(['node', '-e', driver], input=json.dumps(MODULE.RELATION_EVIDENCE_ELEMENT_JS),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_graphical_default_rejects_fake_hidden_or_wrong_source_graph(self):
        import copy
        box = {'text':'question','rect':{'x':20,'y':20,'width':180,'height':25}, 'opaque':True,'unscaled':True,'visible':True,'clipped':False,'fontSize':15,'foreground':[26,52,64],'background':[255,255,255]}
        ids = ['p'+str(i) for i in range(39)]
        edges = [['p0',x] for x in ids[1:]]
        relations = [['r'+str(i),'a','b','typed'] for i in range(7)]
        data = {'mapVisible':True,'viewport':{'x':0,'y':0,'width':1440,'height':900},'map':{'x':0,'y':0,'width':1440,'height':900},
                'directoryTitle':copy.deepcopy(box),'tasks':[{'scope':'s'+str(i),'expectedScope':'s'+str(i),'position':'p'+str(i),'expectedPosition':'p'+str(i)} for i in range(22)],'expectedIds':ids,'expectedEdges':edges,'expectedChallengeLabels':{'e'+str(i):'question' for i in range(13)},'expectedRelations':relations,
                'nodes':[dict(copy.deepcopy(box),id=x) for x in ids],
                'edges':[{'parent':a,'child':b,'visible':True,'length':25,'endpointsMatch':True,'inBounds':True,'uncovered':True,'foreground':[50,90,100],'background':[255,255,255]} for a,b in edges],
                'challenges':[{'entity':'e'+str(i),'expectedEntity':'e'+str(i),'position':'p'+str(i),'challengeOpen':'p'+str(i),'label':copy.deepcopy(box),'title':'Original question','expectedTitle':'Original question','aria':'Original question; open'} for i in range(13)],
                'relations':[{'id':i,'from':a,'to':b,'type':t,'visible':True,'length':25,'endpointsMatch':True,'inBounds':True,'uncovered':True,'foreground':[50,90,100],'background':[255,255,255],'ownHits':[{'x':10,'y':10}]} for i,a,b,t in relations]}
        MODULE.check_graphical_map(data)
        mutations = [lambda x:x.__setitem__('mapVisible',False),lambda x:x['nodes'].pop(),
                     lambda x:x['nodes'][0].__setitem__('id','invented'),lambda x:x['nodes'][0].__setitem__('opaque',False),
                     lambda x:x['nodes'][0].__setitem__('unscaled',False),lambda x:x['nodes'][0]['rect'].__setitem__('y',950),
                     lambda x:x['edges'][0].__setitem__('parent','invented'),lambda x:x['edges'][0].__setitem__('visible',False),
                     lambda x:x['edges'][0].__setitem__('length',0),lambda x:x['edges'][0].__setitem__('length',float('nan')),
                     lambda x:x['edges'][0].__setitem__('foreground',[240,240,240]),lambda x:x['edges'][0].__setitem__('inBounds',False),
                     lambda x:x['tasks'][0].__setitem__('position','wrong'),lambda x:x['challenges'][0].__setitem__('challengeOpen','wrong'),
                     lambda x:x['directoryTitle'].__setitem__('clipped',True),lambda x:x['edges'][0].__setitem__('endpointsMatch',False),
                     lambda x:x['challenges'].pop(),lambda x:x['challenges'][0]['label'].__setitem__('text','Different question'),
                     lambda x:x['challenges'][0].__setitem__('title','Short substitute'),lambda x:x['challenges'][0]['label'].__setitem__('visible',False),
                     lambda x:x['challenges'][0]['label'].__setitem__('clipped',True),lambda x:x['challenges'][0]['label'].__setitem__('fontSize',9),
                     lambda x:x['relations'][0].__setitem__('type','inheritance'),lambda x:x['relations'][0].__setitem__('to','wrong'),
                     lambda x:x['relations'][0].__setitem__('visible',False)]
        for mutate in mutations:
            bad=copy.deepcopy(data);mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_graphical_map(bad)

    def test_relation_selection_cannot_pass_with_stale_article_or_wrong_sources(self):
        import copy
        expected={'id':'r','from':'a','to':'b','relationType':'composition','locators':[{'locator':'Section 3'}],
                  'sourceRefs':[{'sourceId':'s','url':'https://example.org/v1','versionId':'v1','versionStatus':'fixed'}]}
        data={'id':'r','from':'a','to':'b','type':'composition','open':True,'focus':'np-map-relation-evidence-r',
              'route':{'scope':'scope:all'},'beforeRoute':{'scope':'scope:all'},'text':'Section 3',
              'sources':[{'id':'s','url':'https://example.org/v1','version':'v1','status':'fixed'}],
              'visibleProofs':[{'visible':True,'opaque':True,'unscaled':True,'fontSize':15,'clipped':False,'foreground':[20,30,40],'background':[255,255,255],'rect':{'x':20,'y':20,'width':300,'height':40},'viewport':{'x':0,'y':0,'width':1440,'height':900}} for _ in range(4)]}
        MODULE.check_relation_evidence(data,expected)
        mutations=[lambda x:x.__setitem__('id','other'),lambda x:x.__setitem__('type','inheritance'),lambda x:x.__setitem__('from','wrong'),
                   lambda x:x.__setitem__('open',False),lambda x:x.__setitem__('focus','BODY'),lambda x:x['route'].__setitem__('scope','task:goat'),
                   lambda x:x['sources'].clear(),lambda x:x['sources'][0].__setitem__('url','https://example.org/v2'),
                   lambda x:x['sources'][0].__setitem__('version','v2'),lambda x:x['sources'][0].__setitem__('status','snapshot'),
                   lambda x:x.__setitem__('text','No locator'),lambda x:x['visibleProofs'][0].__setitem__('visible',False),
                   lambda x:x['visibleProofs'][0]['rect'].__setitem__('y',1000),lambda x:x['visibleProofs'].pop(),lambda x:x['visibleProofs'][0].__setitem__('unscaled',False),lambda x:x['visibleProofs'][0].__setitem__('fontSize',10),lambda x:x['visibleProofs'][0].update({'text':'固定全文','expectedText':'未固定全文快照'})]
        for mutate in mutations:
            bad=copy.deepcopy(data);mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_relation_evidence(bad,expected)

    def test_default_overview_cannot_pass_with_hidden_tree_or_missing_contract(self):
        import copy
        box = {'text': 'heading', 'visible': True, 'opaque': True, 'unscaled': True, 'foreground': [26, 52, 64], 'background': [255, 255, 255], 'clipped': False, 'fontSize': 15,
               'rect': {'x': 30, 'y': 30, 'width': 200, 'height': 22}}
        entries = [{'id': sid, 'name': dict(box, text=name), 'contract': dict(box, text=contract)}
                   for sid, name, contract in MODULE.TASK_INDEX]
        data = {'home': True, 'panelsHidden': True, 'route': {'paper': None, 'version': None},
                'windowScroll': 0, 'landingScroll': 0, 'scale': 1, 'entries': entries,
                'headings': [copy.deepcopy(box) for _ in range(3)],
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                'landing': {'x': 20, 'y': 20, 'width': 1400, 'height': 860}}
        MODULE.check_reading_home(data)
        mutations = [lambda x: x.__setitem__('home', False),
                     lambda x: x.__setitem__('landingScroll', 200),
                     lambda x: x.__setitem__('scale', .6),
                     lambda x: x['entries'].pop(),
                     lambda x: x['entries'][0]['contract'].__setitem__('text', 'wrong'),
                     lambda x: x['entries'][-1]['contract']['rect'].__setitem__('y', 950),
                     lambda x: x['entries'][0]['name'].__setitem__('visible', False),
                     lambda x: x['entries'][0]['contract'].__setitem__('fontSize', 10),
                     lambda x: x['entries'][0]['contract'].__setitem__('opaque', False),
                     lambda x: x['entries'][0]['contract'].__setitem__('unscaled', False),
                     lambda x: x['entries'][0]['contract'].__setitem__('foreground', [255,255,255])]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_reading_home(bad)

    def test_parallel_scope_requires_both_original_forests(self):
        import copy
        data = {'scope': 'task:goat', 'expectedScope': 'task:goat', 'home': False,
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                'panels': [{'tree': t, 'scope': 'task:goat', 'roots': [t], 'expectedRoots': [t],
                            'headingVisible': True, 'heading': {'x': 20, 'y': 200, 'width': 350, 'height': 25},
                            'rect': {'x': 20, 'y': 190, 'width': 500, 'height': 500}, 'expectedChildren': True, 'children': [{'visible': True, 'opaque': True, 'rect': {'x': 30, 'y': 250, 'width': 350, 'height': 30}}]} for t in ['l', 'c']]}
        MODULE.check_parallel_scope(data)
        mutations = [lambda x: x['panels'].pop(),
                     lambda x: x['panels'][1].__setitem__('scope', 'task:category-objectnav'),
                     lambda x: x['panels'][1].__setitem__('roots', ['wrong']),
                     lambda x: x['panels'][1]['children'][0].__setitem__('visible', False),
                     lambda x: x['panels'][1].__setitem__('headingVisible', False),
                     lambda x: x['panels'][1]['children'][0]['rect'].__setitem__('y', 1500)]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_parallel_scope(bad)

    def test_context_paths_reject_mixed_ancestry_and_unreadable_links(self):
        import copy
        data = {'route': {'tree': 'c', 'node': 'pos:c:6dcc2ce43c02d908266f20'},
                'expectedIds': ['root-c', 'insight'], 'localIds': ['root-c', 'insight'],
                'localTrees': ['c', 'c'], 'globalIds': ['goal', 'scope'],
                'expectedGlobalIds': ['goal', 'scope'], 'globalSeparators': 0,
                'labels': ['全局入口', '挑战–思路树 · 当前路径'],
                'rows': [{'x': 20, 'y': 100, 'width': 900, 'height': 30}, {'x': 20, 'y': 134, 'width': 900, 'height': 30}],
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                'buttons': [{'uncovered': True, 'clipped': False, 'row': {'x': 20, 'y': 134, 'width': 900, 'height': 30}, 'rect': {'x': 90, 'y': 135, 'width': 200, 'height': 25}}]}
        MODULE.check_context_path(data)
        mutations = [lambda x: x['localIds'].insert(0, 'literature'),
                     lambda x: x['localTrees'].__setitem__(0, 'g'),
                     lambda x: x.__setitem__('globalSeparators', 1),
                     lambda x: x['rows'][1].__setitem__('y', 100),
                     lambda x: x['buttons'][0].__setitem__('uncovered', False),
                     lambda x: x['buttons'][0].__setitem__('clipped', True),
                     lambda x: x['rows'][1].__setitem__('y', 950),
                     lambda x: x['buttons'][0]['row'].__setitem__('width', 10)]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_context_path(bad)

    def test_cropped_root_and_low_contrast_are_rejected(self):
        viewport = {'x': 0, 'y': 0, 'width': 1440, 'height': 900}
        self.assertTrue(MODULE.rect_inside({'x': 10, 'y': 200, 'width': 350, 'height': 60}, viewport))
        self.assertFalse(MODULE.rect_inside({'x': 1200, 'y': 200, 'width': 350, 'height': 60}, viewport))
        self.assertFalse(MODULE.rect_inside({'x': 10, 'y': 870, 'width': 350, 'height': 60}, viewport))
        self.assertLess(MODULE.contrast_ratio([255, 255, 255], [234, 245, 240]), 4.5)
        self.assertGreater(MODULE.contrast_ratio([26, 52, 64], [234, 245, 240]), 4.5)

    def test_blank_png_rejected_and_nonblank_pixels_detected(self):
        def png(rows, width):
            def chunk(kind, data):
                return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
            return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, len(rows), 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(b''.join(b'\0' + row for row in rows))) + chunk(b'IEND', b'')
        self.assertFalse(MODULE.png_has_visible_variation(png([bytes([255] * 90)] * 30, 30)))
        row = bytes(v for x in range(90) for v in ((x * 7) % 256, (x * 11) % 256, (x * 17) % 256))
        self.assertTrue(MODULE.png_has_visible_variation(png([row] * 90, 90)))

    def test_required_viewports(self):
        self.assertEqual(MODULE.VIEWPORTS, [(1440, 900), (1920, 1080)])

    def test_webdriver_envelope_and_loopback(self):
        driver = MODULE.Driver(12345)
        driver.session = 'test-session'
        with patch.object(MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"value":{"ok":true}}')) as opened:
            self.assertEqual(driver.js('return arguments[0]', 'value'), {'ok': True})
        request = opened.call_args.args[0]
        self.assertEqual(request.full_url, 'http://127.0.0.1:12345/session/test-session/execute/sync')
        self.assertEqual(json.loads(request.data), {'script': 'return arguments[0]', 'args': ['value']})
        self.assertEqual(opened.call_args.kwargs['timeout'], 50)

    def test_webdriver_errors_are_not_accepted(self):
        driver = MODULE.Driver(12345)
        with patch.object(MODULE.urllib.request, 'urlopen', return_value=io.BytesIO(b'{"value":{"error":"session not created","message":"launch failed"}}')):
            with self.assertRaisesRegex(RuntimeError, 'launch failed'):
                driver.request('POST', '/session', {})

    def test_wait_is_bounded_and_keeps_failures(self):
        with patch.object(MODULE.time, 'monotonic', side_effect=[0, 0, 2]), patch.object(MODULE.time, 'sleep'):
            with self.assertRaises(TimeoutError):
                MODULE.wait_for(lambda: False, timeout=1)
        with self.assertRaisesRegex(ValueError, 'failed'):
            MODULE.wait_for(lambda: (_ for _ in ()).throw(ValueError('failed')))


class ReaderToggleChecks(unittest.TestCase):
    @staticmethod
    def snapshots():
        import copy
        def rect(x, y, width, height):
            return dict(x=x, y=y, width=width, height=height)
        def proof(r, text='readable'):
            return dict(rect=r, text=text, visible=True, opaque=True, unscaled=True, clipped=False,
                        fontSize=15, foreground=[26, 52, 64], background=[255, 255, 255])
        route = dict(scope='task:category-objectnav', tree='l', node='method-vlfm', paper='vlfm', version='v1', mode='tree')
        preserved = dict(route=route.copy(), contexts={'context': {'graphScale': 1}}, revision=12)
        expanded = dict(g=['global'], l=['root', 'branch'], c=['challenge'], a=[])
        original = {
            'route': route, 'position': dict(id='method-vlfm', scope='task:category-objectnav', tree='l', paper='vlfm', version='v1', entity='vlfm-recipe', kind='pipeline_recipe'),
            'graphScale': 1, 'expanded': expanded, 'preservedState': preserved,
            'history': dict(length=17, url='http://127.0.0.1/#method-vlfm', modelKey='navigation', contextKey='context', entryKey='stable-entry', timeOrigin=1000, model=copy.deepcopy(preserved), unrelated={'otherApp': {'key': 'keep'}}),
            'viewport': rect(0, 0, 1440, 900), 'window': dict(x=0, y=0), 'layout': 'reading', 'collapsed': 'false', 'focus': 'np-node-method-vlfm',
            'panels': rect(20, 140, 1400, 720), 'columnGap': 16,
            'treePane': proof(rect(20, 140, 836.8, 700)), 'treeProof': proof(rect(21, 205, 834.8, 580)),
            'tree': dict(rect=rect(21, 205, 834.8, 580), client=rect(22, 206, 833, 578), left=0, top=200, scrollWidth=833, scrollHeight=978, maxLeft=0, maxTop=400),
            'title': proof(rect(34, 155, 700, 32), 'VLFM · 层级来路'),
            'selected': dict(count=1, id='method-vlfm', tree='l', entity='vlfm-recipe', aria='true', scope='task:category-objectnav',
                             row=proof(rect(40, 360, 780, 65)), label=proof(rect(60, 370, 710, 30), 'VLFM'), content=dict(x=18, y=354)),
            'toggle': dict(tag='BUTTON', hidden=False, disabled=False, controls='np-detail-scroll', expanded='true', proof=proof(rect(150, 90, 150, 32), '收起阅读栏')),
            'reader': dict(hidden=False, display='block', tabIndex=-1, proof=proof(rect(872.8, 140, 547.2, 720)),
                           scroll=dict(rect=rect(872.8, 140, 547.2, 720), client=rect(873.8, 141, 545, 718), top=160, left=0, maxTop=1000, maxLeft=0, scrollHeight=1718, scrollWidth=545),
                           heading=proof(rect(900, 142, 490, 40), 'READING DESK 所选节点'), entity='vlfm-recipe', flowCount=5, savedScroll=160, persistedScroll=160)}
        collapsed = copy.deepcopy(original)
        collapsed.update(collapsed='true', focus='np-reader-toggle')
        collapsed['treePane']['rect']['width'] = 1400
        collapsed['treeProof']['rect']['width'] = collapsed['tree']['rect']['width'] = 1398
        collapsed['tree']['client']['width'] = collapsed['tree']['scrollWidth'] = 1396
        collapsed['tree']['scrollHeight'] = 878
        collapsed['tree']['maxTop'] = 300
        collapsed['selected']['row']['rect']['width'] = 1340
        collapsed['toggle']['expanded'] = 'false'
        collapsed['toggle']['proof']['text'] = '展开所选节点正文'
        collapsed['reader'].update(hidden=True, display='none')
        collapsed['reader']['proof'].update(rect=rect(0, 0, 0, 0), visible=False, opaque=False)
        reopened = copy.deepcopy(original)
        reopened['focus'] = 'np-detail-scroll'
        return original, collapsed, reopened

    def test_reader_toggle_rejects_identity_history_and_preserved_state_changes(self):
        import copy
        original, collapsed, _ = self.snapshots()
        MODULE.check_reader_toggle_snapshot(original, False)
        MODULE.check_reader_toggle_transition(original, collapsed, original, True)
        mutations = [
            lambda x: x['route'].__setitem__('version', 'wrong'),
            lambda x: x['position'].__setitem__('paper', 'poni'),
            lambda x: x['selected'].__setitem__('scope', 'task:goat'),
            lambda x: x['selected'].__setitem__('entity', 'other'),
            lambda x: x['selected'].__setitem__('count', 2),
            lambda x: x['selected'].__setitem__('aria', 'false'),
            lambda x: x.__setitem__('graphScale', .9),
            lambda x: x['expanded']['c'].append('new'),
            lambda x: x['history'].__setitem__('length', 18),
            lambda x: x['history'].__setitem__('url', 'http://127.0.0.1/#other'),
            lambda x: x['history'].__setitem__('entryKey', 'other'),
            lambda x: x['history'].__setitem__('timeOrigin', 2000),
            lambda x: x['history']['unrelated']['otherApp'].__setitem__('key', 'lost'),
            lambda x: x['history']['model'].__setitem__('revision', 13),
            lambda x: x['preservedState'].__setitem__('revision', 13),
            lambda x: x['window'].__setitem__('y', 50),
            lambda x: x['reader'].__setitem__('entity', 'other'),
            lambda x: x['reader'].__setitem__('flowCount', 0),
        ]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(collapsed); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError):
                MODULE.check_reader_toggle_transition(original, bad, original, True)

    def test_reader_toggle_rejects_hidden_occluded_clipped_and_unrecovered_geometry(self):
        import copy
        original, collapsed, _ = self.snapshots()
        mutations = [
            lambda x: x['title'].__setitem__('opaque', False),
            lambda x: x['title'].__setitem__('visible', False),
            lambda x: x['title'].__setitem__('clipped', True),
            lambda x: x['title'].__setitem__('fontSize', 10),
            lambda x: x['title'].__setitem__('foreground', [240, 240, 240]),
            lambda x: x['title']['rect'].__setitem__('y', 1000),
            lambda x: x['treeProof'].__setitem__('visible', False),
            lambda x: x['treePane']['rect'].__setitem__('width', 1380),
            lambda x: x['tree']['client'].__setitem__('height', 50),
            lambda x: x['selected']['row'].__setitem__('visible', False),
            lambda x: x['selected']['label'].__setitem__('unscaled', False),
            lambda x: x['selected']['label'].__setitem__('clipped', True),
            lambda x: x['selected']['row']['rect'].__setitem__('y', 790),
            lambda x: x['selected']['label']['rect'].__setitem__('x', 1420),
            lambda x: x['toggle'].__setitem__('tag', 'DIV'),
            lambda x: x['toggle'].__setitem__('disabled', True),
            lambda x: x['toggle'].__setitem__('controls', 'wrong-reader'),
            lambda x: x['toggle'].__setitem__('expanded', 'true'),
            lambda x: x['toggle']['proof'].__setitem__('visible', False),
            lambda x: x['reader'].__setitem__('display', 'block'),
            lambda x: x['reader']['proof']['rect'].__setitem__('width', 550),
            lambda x: x['tree'].__setitem__('maxTop', float('nan')),
            lambda x: x['tree'].__setitem__('scrollHeight', 1),
        ]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(collapsed); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError):
                MODULE.check_reader_toggle_transition(original, bad, original, True)

    def test_reader_toggle_anchor_uses_only_legal_clamping_and_one_pixel_rounding(self):
        import copy
        original, collapsed, _ = self.snapshots()
        def move(snapshot, row_y, scroll_top):
            old_y = snapshot['selected']['row']['rect']['y']
            snapshot['selected']['row']['rect']['y'] = row_y
            snapshot['selected']['label']['rect']['y'] += row_y - old_y
            snapshot['tree']['top'] = scroll_top
            snapshot['selected']['content']['y'] = row_y - snapshot['tree']['client']['y'] + scroll_top
        # Reflow needs a negative scroll offset: the legitimate zero endpoint shifts
        # the row up by 20 px. No fixed 20 px tolerance is granted elsewhere.
        start_clamp = copy.deepcopy(collapsed)
        move(start_clamp, 340, 0)
        MODULE.check_reader_toggle_transition(original, start_clamp, original, True)
        # Reflow would need maxTop+20: allow only the measured maximum endpoint.
        end_clamp = copy.deepcopy(collapsed)
        move(end_clamp, 380, end_clamp['tree']['maxTop'])
        MODULE.check_reader_toggle_transition(original, end_clamp, original, True)
        for y, top in [(362, 200), (340, 1.1), (380, 298.9), (360, 301)]:
            bad = copy.deepcopy(collapsed); move(bad, y, top)
            with self.subTest(y=y, scroll=top), self.assertRaises(RuntimeError):
                MODULE.check_reader_toggle_transition(original, bad, original, True)
        rounding = copy.deepcopy(collapsed); move(rounding, 360.5, 200)
        MODULE.check_reader_toggle_transition(original, rounding, original, True)
        # Reopen anchors against the current collapsed row, even if the first
        # transition legitimately clamped; it does not promise an impossible
        # round trip to the pre-collapse pixel.
        reopened = copy.deepcopy(original); reopened['focus'] = 'np-detail-scroll'
        move(reopened, 340, 220)
        MODULE.check_reader_toggle_transition(start_clamp, reopened, original, False)
        wrong = copy.deepcopy(reopened); move(wrong, 360, 200)
        with self.assertRaises(RuntimeError):
            MODULE.check_reader_toggle_transition(start_clamp, wrong, original, False)

    def test_reader_reopen_requires_focus_exact_scroll_and_visible_reader_boundary(self):
        import copy
        original, collapsed, reopened = self.snapshots()
        MODULE.check_reader_toggle_transition(collapsed, reopened, original, False)
        mutations = [
            lambda x: x.__setitem__('focus', 'np-reader-toggle'),
            lambda x: x['reader']['scroll'].__setitem__('top', 159.5),
            lambda x: x['reader'].__setitem__('savedScroll', 0),
            lambda x: x['reader'].__setitem__('persistedScroll', 159.5),
            lambda x: x['reader'].__setitem__('hidden', True),
            lambda x: x['reader'].__setitem__('tabIndex', 0),
            lambda x: x['reader']['proof'].__setitem__('opaque', False),
            lambda x: x['reader']['proof'].__setitem__('visible', False),
            lambda x: x['reader']['proof']['rect'].__setitem__('x', 850),
            lambda x: x['reader']['proof']['rect'].__setitem__('height', 100),
            lambda x: x['reader']['heading'].__setitem__('visible', False),
            lambda x: x['reader']['heading']['rect'].__setitem__('y', 100),
            lambda x: x['toggle'].__setitem__('expanded', 'false'),
        ]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(reopened); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError):
                MODULE.check_reader_toggle_transition(collapsed, bad, original, False)
        oversized = copy.deepcopy(reopened)
        oversized['reader']['proof']['rect'].update(x=700, width=720)
        oversized['treePane']['rect']['width'] = 664
        with self.assertRaises(RuntimeError):
            MODULE.check_reader_toggle_snapshot(oversized, False)
        collapsed['focus'] = 'np-detail-scroll'
        with self.assertRaises(RuntimeError):
            MODULE.check_reader_toggle_transition(original, collapsed, original, True)

    def test_reader_toggle_real_js_snapshot_measures_hidden_ancestors_overlays_and_exact_row(self):
        driver = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
const {script,elementsScript,identityScript}=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM(`<!doctype html><style>*{opacity:1;visibility:visible;transform:none;zoom:1;color:rgb(26,52,64);background-color:rgb(255,255,255);font-size:15px;}</style>
<main id="navigation-product" data-reading-layout="reading" data-reader-collapsed="false">
<button id="np-reader-toggle" aria-controls="np-detail-scroll" aria-expanded="true">收起阅读栏</button>
<div class="np-panels" style="column-gap:16px"><section class="np-tree-pane"><h2 id="np-tree-heading">Branch</h2><div id="np-tree-scroll"><div id="np-tree"><section data-parallel-tree="l" data-scope-id="task:category-objectnav"><ul><li id="np-node-method" data-position="method" data-tree="l" data-entity="recipe" aria-selected="true"><div class="np-node-row"><button class="np-node-label">VLFM</button></div><ul><li><div class="np-node-row" id="decoy">Other row</div></li></ul></li></ul></section></div></div></section>
<aside id="np-detail-scroll" tabindex="-1"><div class="np-reader-heading">READING DESK</div><div class="np-method-mechanism" data-mechanism-entity="recipe"><dl class="np-method-flow">${'<dd>flow</dd>'.repeat(5)}</dl></div></aside></div></main>`,{url:'http://localhost/',runScripts:'outside-only'});
try {
 const w=dom.window,d=w.document,route={scope:'task:category-objectnav',tree:'l',node:'method',paper:'vlfm',version:'v1'},key='context';
 const bucket={graphScale:1,expandedByTree:{l:['root'],c:['ci']},selectedByTree:{l:'method'},focusTarget:'old',windowScroll:0,treeScrollByTree:{l:200,c:33},treeScrollLeftByTree:{l:0,c:4},detailScrollByTree:{l:160,c:44}};
 const state={route,contexts:{[key]:bucket,untouched:{value:3}},revision:12,originTrail:[{keep:'origin'}]};
 w.NavigationProductApp={getState:()=>state,getBundle:()=>({positions:{method:{id:'method',scopeId:route.scope,tree:'l',paperId:'vlfm',versionId:'v1',entityId:'recipe',kind:'pipeline_recipe'}}})};
 w.NavigationProductModel={KEY:'nav',getBucket:()=>bucket,contextKey:()=>key};
 w.history.replaceState({nav:JSON.parse(JSON.stringify(state)),external:{keep:4}},'');
 const rects=new Map();
 function setRect(e,x,y,width,height){const r={x,y,width,height,left:x,top:y,right:x+width,bottom:y+height};rects.set(e,r);e.getBoundingClientRect=()=>r;for(const [k,v] of Object.entries({clientLeft:0,clientTop:0,clientWidth:width,clientHeight:height,scrollWidth:width,scrollHeight:height}))Object.defineProperty(e,k,{configurable:true,value:v});}
 for(const e of d.querySelectorAll('*'))setRect(e,0,0,0,0);
 const toggle=d.getElementById('np-reader-toggle'),tree=d.getElementById('np-tree-scroll'),row=d.querySelector('#np-node-method > .np-node-row'),label=row.querySelector('button'),reader=d.getElementById('np-detail-scroll');
 setRect(toggle,20,20,150,32);setRect(tree,10,100,800,600);setRect(row,30,300,750,65);setRect(label,50,310,700,30);setRect(d.getElementById('decoy'),30,500,750,65);setRect(reader,830,100,550,700);
 tree.scrollTop=200;reader.scrollTop=160;Object.defineProperty(tree,'scrollHeight',{configurable:true,value:1000});
 let overlay=false;
 d.elementFromPoint=(x,y)=>{if(overlay&&x>=20&&x<=170&&y>=20&&y<=52)return d.body;return [...rects.entries()].reverse().find(([e,r])=>r.width&&r.height&&x>=r.x&&x<r.right&&y>=r.y&&y<r.bottom)?.[0]||d.body;};
 const snapshot=new w.Function(script),initial=snapshot(),elements=new w.Function(elementsScript)(),identity=new w.Function(identityScript);
 assert.equal(identity(elements).every(x=>x.same),true);
 assert.equal(initial.toggle.proof.visible,true);assert.equal(initial.selected.row.text,'VLFM');assert.equal(initial.selected.row.rect.y,300);assert.deepEqual(JSON.parse(JSON.stringify(initial.selected.content)),{x:20,y:400});
 assert.equal(initial.position.version,'v1');assert.equal(initial.reader.flowCount,5);assert.equal(initial.history.unrelated.external.keep,4);
 assert.equal(initial.preservedState.contexts[key].focusTarget,undefined);assert.equal(initial.preservedState.contexts[key].treeScrollByTree.l,undefined);assert.equal(initial.preservedState.contexts[key].treeScrollByTree.c,33);assert.equal(initial.preservedState.contexts[key].detailScrollByTree.c,44);assert.equal(initial.preservedState.contexts.untouched.value,3);assert.equal(initial.preservedState.originTrail[0].keep,'origin');
 assert.equal(bucket.focusTarget,'old','snapshot must not mutate the real model');assert.equal(w.history.state.nav.contexts[key].focusTarget,'old');
 overlay=true;assert.equal(snapshot().toggle.proof.visible,false,'an unrelated overlay must fail hit testing');overlay=false;
 d.getElementById('navigation-product').style.display='none';assert.equal(snapshot().toggle.proof.opaque,false,'hidden ancestor cannot pass');d.getElementById('navigation-product').style.display='';
 toggle.setAttribute('aria-controls','wrong');assert.equal(snapshot().toggle.controls,'wrong');
 reader.hidden=true;reader.style.display='none';setRect(reader,0,0,0,0);const hidden=snapshot();assert.equal(hidden.reader.hidden,true);assert.equal(hidden.reader.display,'none');assert.equal(hidden.reader.proof.opaque,false);
 const clone=row.cloneNode(true);row.replaceWith(clone);assert.equal(identity(elements).find(x=>x.name==='row').same,false,'same markup and source identity cannot substitute for the original row');
 clone.remove();assert.equal(snapshot().selected.row,null,'a nested descendant is not the selected row');
} finally {dom.window.close();}
"""
        result = subprocess.run(['node', '-e', driver], input=json.dumps({'script': MODULE.READER_TOGGLE_SNAPSHOT_JS, 'elementsScript': MODULE.READER_DOM_ELEMENTS_JS, 'identityScript': MODULE.READER_DOM_IDENTITY_JS}),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_reader_toggle_saves_diagnostics_before_failure_and_uses_real_controls(self):
        import copy
        original, collapsed, reopened = self.snapshots()
        class Driver:
            def __init__(self, snapshots):
                self.snapshots = iter(snapshots); self.clicks = []; self.scripts = []
            def settle(self): pass
            def js(self, script, *args):
                self.scripts.append(script)
                if script == MODULE.READER_DOM_ELEMENTS_JS: return ['original-elements']
                if script == MODULE.READER_DOM_IDENTITY_JS:
                    return [dict(name=name, same=True) for name in ('tree', 'selected', 'row', 'reader', 'method')]
                return copy.deepcopy(next(self.snapshots))
            def selector(self, selector): return {'selector': selector}
            def click(self, element): self.clicks.append(element['selector'])
        report, saved, captures = {}, [], []
        driver = Driver([original, original, collapsed, reopened])
        MODULE.reader_toggle_checks(driver, report, lambda: saved.append(copy.deepcopy(report)),
                                    lambda *args, **kwargs: captures.append((args, kwargs)), '1440x900')
        self.assertEqual(driver.clicks, [MODULE.READER_TOGGLE_SELECTOR] * 2)
        self.assertTrue(all(s in (MODULE.READER_TOGGLE_SNAPSHOT_JS, MODULE.READER_DOM_ELEMENTS_JS, MODULE.READER_DOM_IDENTITY_JS) for s in driver.scripts))
        self.assertEqual(captures, [(('1440x900-11b-reader-collapsed',), {'require_tree': True}),
                                    (('1440x900-11c-reader-reopened',), {'require_tree': False})])
        self.assertEqual(saved[-1]['readerToggleChecks'][0]['phases'][1]['after'], reopened)
        bad = copy.deepcopy(collapsed); bad['focus'] = 'BODY'
        report, saved, captures = {}, [], []
        with self.assertRaisesRegex(RuntimeError, 'focus'):
            MODULE.reader_toggle_checks(Driver([original, original, bad]), report,
                                        lambda: saved.append(copy.deepcopy(report)),
                                        lambda *args, **kwargs: captures.append(args), '1440x900')
        self.assertEqual(saved[-1]['readerToggleChecks'][0]['phases'][0]['before'], original)
        self.assertEqual(saved[-1]['readerToggleChecks'][0]['phases'][0]['after'], bad)
        self.assertEqual(captures, [])

    def test_reader_toggle_dom_replacement_and_stale_reference_fail_closed(self):
        import copy
        original, collapsed, _ = self.snapshots()
        identities = [dict(name=name, same=True) for name in ('tree', 'selected', 'row', 'reader', 'method')]
        MODULE.check_reader_dom_identity(identities)
        for index in range(5):
            bad = copy.deepcopy(identities); bad[index]['same'] = False
            with self.subTest(replaced=bad[index]['name']), self.assertRaises(RuntimeError):
                MODULE.check_reader_dom_identity(bad)
        class Driver:
            def __init__(self): self.snapshots = iter([original, original, collapsed])
            def settle(self): pass
            def js(self, script, *args):
                if script == MODULE.READER_DOM_ELEMENTS_JS: return ['original-elements']
                if script == MODULE.READER_DOM_IDENTITY_JS: raise RuntimeError('stale element reference')
                return copy.deepcopy(next(self.snapshots))
            def selector(self, selector): return {'selector': selector}
            def click(self, element): pass
        report, saved = {}, []
        with self.assertRaisesRegex(RuntimeError, 'stale element reference'):
            MODULE.reader_toggle_checks(Driver(), report, lambda: saved.append(copy.deepcopy(report)), lambda *a, **k: None, '1440x900')
        phase = saved[-1]['readerToggleChecks'][0]['phases'][0]
        self.assertEqual(phase['after'], collapsed)
        self.assertEqual(phase['domIdentityError'], 'stale element reference')

    def test_reader_toggle_real_wheel_setup_and_failure_diagnostic(self):
        import copy
        original, collapsed, reopened = self.snapshots()
        initial = copy.deepcopy(original); initial['reader']['scroll']['top'] = 0
        class Driver:
            def __init__(self, fail=False):
                self.snapshots = iter([initial, original, original, collapsed, reopened]); self.calls = []; self.fail = fail
            def settle(self): pass
            def js(self, script, *args):
                if script == MODULE.READER_DOM_ELEMENTS_JS: return ['original-elements']
                if script == MODULE.READER_DOM_IDENTITY_JS:
                    return [dict(name=name, same=True) for name in ('tree', 'selected', 'row', 'reader', 'method')]
                return copy.deepcopy(next(self.snapshots)) if script == MODULE.READER_TOGGLE_SNAPSHOT_JS else True
            def selector(self, selector): return {'selector': selector}
            def click(self, element): pass
            def call(self, *args):
                self.calls.append(args)
                if self.fail: raise RuntimeError('wheel rejected')
        report, driver = {}, Driver()
        MODULE.reader_toggle_checks(driver, report, lambda: None, lambda *a, **k: None, '1440x900')
        method, path, payload = driver.calls[0]
        self.assertEqual((method, path), ('POST', '/actions'))
        action = payload['actions'][0]['actions'][0]
        self.assertEqual((action['type'], action['origin'], action['deltaY']), ('scroll', {'selector': '#np-detail-scroll'}, 160))
        self.assertIn('afterWheel', report['readerToggleChecks'][0])
        report, saved = {}, []
        with self.assertRaisesRegex(RuntimeError, 'wheel rejected'):
            MODULE.reader_toggle_checks(Driver(True), report, lambda: saved.append(copy.deepcopy(report)), lambda *a, **k: None, '1440x900')
        self.assertEqual(saved[-1]['readerToggleChecks'][0]['afterWheel'], original)


if __name__ == '__main__':
    unittest.main()
