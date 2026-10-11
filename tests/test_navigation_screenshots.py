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


def run_product_capture_script(owner, body, extra):
    """Production DOM contract only; this deliberately does not claim layout."""
    import tempfile
    root = Path(__file__).parents[1]
    with tempfile.TemporaryDirectory(prefix='.navigation-capture-test-', dir=root) as tmp:
        build = subprocess.run(['python3', '-c', "import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;p.write_preview(Path('.').resolve(),Path(sys.argv[1]))", tmp], cwd=root, capture_output=True, text=True)
        owner.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        script = r"""
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{JSDOM,ResourceLoader,VirtualConsole}=require('jsdom');
const input=JSON.parse(fs.readFileSync(0,'utf8')),output=path.join(input.temp,'research/navigation'),errors=[];
class Resources extends ResourceLoader{fetch(url){throw Error('Unexpected external resource '+url);}}
const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(fs.readFileSync(path.join(output,'index.html'),'utf8'),{url:'https://example.org/research/navigation/',runScripts:'dangerously',pretendToBeVisual:true,resources:new Resources(),virtualConsole:vc,beforeParse(w){w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;w.scrollTo=(x,y)=>Object.defineProperty(w,'scrollY',{value:y,configurable:true});w.HTMLElement.prototype.scrollIntoView=function(){};Object.defineProperty(w.crypto,'subtle',{value:crypto.webcrypto.subtle});w.fetch=url=>Promise.resolve({ok:true,arrayBuffer:async()=>fs.readFileSync(path.join(output,url))});}});
(async()=>{const w=dom.window,d=w.document,wait=ms=>new Promise(r=>setTimeout(r,ms));
async function ready(check){for(let i=0;i<250&&!check();i++)await wait(10);assert.ok(check());await new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)));}
await ready(()=>w.NavigationProductApp);const a=w.NavigationProductApp,m=w.NavigationProductModel,s=input.science,e=input.expected,snapshot=new w.Function(input.snapshot),states=[];
function label(id){return d.getElementById('np-node-'+id)?.querySelector(':scope > .np-node-row > .np-node-label');}
async function expose(id){const b=a.getBundle(),ids=[];for(let p=b.positions[id];p;p=b.positions[p.parentId])ids.unshift(p.id);for(const parent of ids.slice(0,-1)){const item=d.getElementById('np-node-'+parent);assert.ok(item,parent);if(item.getAttribute('aria-expanded')==='false'){item.querySelector(':scope > .np-node-row > .np-node-toggle').click();await wait(35);}}assert.ok(label(id));return label(id);}
async function scope(id){if(d.getElementById('np-reading-landing').hidden){d.querySelector('[data-tree-tab="g"]').click();await ready(()=>!d.getElementById('np-reading-landing').hidden);}const entry=d.querySelector('[data-task-open="'+id+'"]');if(entry)entry.click();else{const all=d.getElementById('np-all-scopes');if(!all.open)all.querySelector('summary').click();d.querySelector('[data-scope-open="'+id+'"]').click();}await ready(()=>a.getState().route.scope===id&&d.querySelector('[data-task-route-scope]')?.dataset.taskRouteState==='ready');}
async function inventory(id){for(const row of e.scopes[id].methods)await expose(row.position.id);}
async function select(id){const control=await expose(id);control.click();await ready(()=>a.getState().route.node===id&&a.getContent().ready(a.getBundle().positions[id].entityId));}
""" + body + r"""
assert.deepEqual(errors,[]);process.stdout.write(JSON.stringify(states));dom.window.close();})().catch(error=>{console.error(error);dom.window.close();process.exitCode=1;});
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'temp': tmp, 'snapshot': MODULE.TASK_ROUTE_SNAPSHOT_JS, **extra}), cwd=root, text=True, capture_output=True, timeout=120)
        owner.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)


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

    def test_active_scope_requires_one_original_forest_and_keyboard_scope(self):
        import copy
        for tree in ('l', 'c'):
            data = {'scope': 'task:goat', 'expectedScope': 'task:goat', 'home': False,
                    'activeTree': tree, 'selectedTree': tree, 'treeCount': 1, 'rovingCount': 1, 'inactiveItemCount': 0,
                    'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                    'panels': [{'tree': tree, 'scope': 'task:goat', 'roots': [tree], 'expectedRoots': [tree],
                        'headingVisible': True, 'heading': {'x': 20, 'y': 200, 'width': 350, 'height': 25},
                        'rect': {'x': 20, 'y': 190, 'width': 500, 'height': 500}, 'expectedChildren': True,
                        'children': [{'visible': True, 'opaque': True, 'rect': {'x': 30, 'y': 250, 'width': 350, 'height': 30}}]}]}
            MODULE.check_parallel_scope(data)
            mutations = [lambda x: x['panels'].pop(), lambda x: x['panels'].append(copy.deepcopy(x['panels'][0])),
                         lambda x: x['panels'][0].update(scope='task:category-objectnav'),
                         lambda x: x['panels'][0].update(roots=['wrong']), lambda x: x.update(treeCount=2),
                         lambda x: x.update(rovingCount=2), lambda x: x.update(inactiveItemCount=1),
                         lambda x: x.update(selectedTree='g'), lambda x: x['panels'][0].update(headingVisible=False),
                         lambda x: x['panels'][0]['children'][0].update(visible=False),
                         lambda x: x['panels'][0]['children'][0]['rect'].update(y=1500)]
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
        self.assertEqual(len(MODULE.SCENE_NAMES), 45)
        self.assertEqual(len(set(MODULE.SCENE_NAMES)), 45)

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
        task_key = '["task:category-objectnav",null,null,null,null,null]'
        task_view = dict(schema=1, lastRouteByTree={'l': route.copy(), 'c': {'node': 'other-tree'}},
                         focusTargetByTree={'l': route['node'], 'c': 'other-tree-focus'})
        preserved = dict(route=route.copy(), contexts={'context': {'graphScale': 1}, task_key: {'taskView': task_view},
                                                      'unrelated': {'focusTarget': 'keep'}},
                         revision=12, originTrail=[{'focusTarget': 'origin', 'taskView': copy.deepcopy(task_view)}])
        expanded = dict(g=['global'], l=['root', 'branch'], c=['challenge'], a=[])
        original = {
            'route': route, 'taskContextKey': task_key, 'position': dict(id='method-vlfm', scope='task:category-objectnav', tree='l', paper='vlfm', version='v1', entity='vlfm-recipe', kind='pipeline_recipe'),
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
        for state in (collapsed['preservedState'], collapsed['history']['model']):
            state['contexts'][task_key]['taskView']['focusTargetByTree']['l'] = 'np-reader-toggle'
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
        for state in (reopened['preservedState'], reopened['history']['model']):
            state['contexts'][task_key]['taskView']['focusTargetByTree']['l'] = 'np-detail-scroll'
        return original, collapsed, reopened

    def test_reader_toggle_real_2b8_artifact_only_migrates_current_neutral_focus(self):
        # Exact failed Chrome transition from head 2b8c7e70dff29f26bcf7907920d20f6d55c6eb0f.
        # Original receipt SHA256: 67d0bf3f7e53900e1b778ef91d8cec316d0c6326c66d0576704f6373ab10ee4a
        # Preserve the complete raw states, measured geometry and five DOM identities.
        import base64, copy, gzip
        recorded = json.loads(gzip.decompress(base64.b64decode(
            'H4sIAAAAAAACA+19aXMbN7b2X2Hp1uRLJLsBNDZN5YMdZzKu8ZKyM5pb9zrlQmOR+YYiebko8Uzlv784QC9oii1RsiQyCSplRSK7'
            'sRyc85wFBzj/OZotxufjqZocnf7nSM8mEzVfWnN0euTUZGmPjuGz9cX0ezU/OkXs+Mj+OldTA0/850gdnf7vT/4J/7+j+Wx5qk9L'
            'hmWFyoKWhSSFNFxzWlZH/qHz+OykeXZyyktVGYe0FLIg2GIjsBXY9xi/FqZSTlpnSico10hiakrUfu1cgaVwTiFeldppVxSyMkc/'
            '/XZ85GZ6vfQzmM5PpjNjT659wY9soeaf3ms1sX6Gx0efxsvVbPE5kmO6sr+u/mH9X0f/++FopZY/n2q1suf+gZNZ9f+sXk3V5Yej'
            '4+l6Mok/PhxdTtyF/+jD0XK2Xmh7emFXn2bmZDKeWnVuT+uv4eGffO92ulp8jj2UBmlCdXniSIVOSsboiSyYPkFK+vkbgyVl/o2J'
            'nZ6vPh2d0uL46MLPb5IMdQm/+5Eu9WxuT9Vk0htb/8dP8KyxKzWevNcLv/LPP/+4sLZe2CKsaxEWrgjrVvzWrX7v0YYH6lUOC3R+'
            'yrBhhulKCuN4UWhjOMO2Xr/zU6sMwYJaKRUVVhFLBNZF+3Xpl0s6V6EKGV0aWspKuO5txQk3qpAWOcIKhSyWjuKjmsFaJvhRLc7t'
            'KrICLN5JoPbJwDpe5YVGNl6r+du5nR6dBqHwn1/axeXY/nLm/wUiTDwJPcWXvaf07GKuFuPlbNr7GBhheTZejivoZbVY+8+ms9XG'
            'yws7UavxbNr/dBkW6sfZPC7H0k780DeWIywwLEj8xS/JTSsyic/6Ble+mZ2ZoXv4lXWrHV74ZTw1s1/iK/GTRqiUXYzV5ORyvFz7'
            '/8UVOVlatdCfHpODaxTTmPKqMFZYTErMGWNKIr4dxQrGDOeOlA4hYoWUZcVKcXSVBa99/ArnecbxTGUjW73zwvK5YZWGMd7WPNhN'
            'JADBrMdEs/UqfFXZqf7UssZEjS+aPwBB/OhgLf0oQApOjwBlp/HzG0Y9V3O7aJqaL2armVcXzd8BhKDtG1bYt7OyF3M/Ldu8GoZz'
            '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'
            'j58+PtH3KfS/1beAvbOX4/qAiifM+Dww+4kunWKuoIKWlFpMvOEEWe7xYqsfFx4BvEh6kq/1zyBt+UKwfCHYXi8Eux/kvY7ZdgGB'
            '9vq8YRQ434ICDyVH939s+35P5g52dtixvsM/uzoc+PuiE6q7t/bggb+9r8F+7fU/DC9nxvsSxtuX6vh9Xwlx3aH+fCVEvhLi93gl'
            'xG0RMV8JkQ2J+zMkDoIdskBlgcoGUr4zKxtI2UDKd2b96Q2ke7sZ608Wa8ki9SczkX4CZd3sAUpxfwx/wNftNQQ4a59O9j7X46fh'
            'vuOwPRpLLHXf/rCYmbVencFsV+ML+zbs7HlCcokYx4wRissn5fHRehpMoFDxyje2XoDgfFqt5qdPnyLMnxT+P+RZuuD86cLGIhpP'
            'u36e/pf//Rv0VSDGN0CKv5BnV4nxFUz9m8lXQPhvPNn9QxP/bzvpvwqE/wZI8FVNp28ilfwrfTr5D8JjQINvAnmDWH/2rOGnsfCW'
            '3nh6HpZyaiehetQnOz7/5L/0RAAUNVBqChEhj49+9b94tvJ0xAgw2Q9zHLLq/Ft2uhqvgMKx++XpfDy3MIaTmjnG5mZ++tljNjxV'
            'v/pxYbX/9Sqj7cBYt2ekOSze4tKa9ysVxSbX1Mpb6LmmVq6plWtq5ZpauaZWrqmVa2rlmlq5plauqZVrauWaWrmmVq6plWtq5Zpa'
            'uaZWrqmV8wNyfkDOD8j5AbmmVq6plWtq5ZpauaZWrqmVa2rlmlq5plauqZVrauWaWrmmVq6plWtq5ZpauaZWrqmVa2rlmlq5plau'
            'qZVrauWaWrmmVq6plWtq5ZpauaZWrqmVa2rlmlq5plauqZVrauWaWrmmVq6plWtq5ZpauaZWrqmVa2rlmlq5plauqZVrauWaWrmm'
            'Vq6plWtq5Zpa+UKwfCFYrqmVa2rlmlq5plYuhZFramXGyyUjck2tfCVEvhIilwDKJSNyTa1cUysLVDaQ8p1Z2UDKBlK+MysbSLmm'
            'Vq6plUUq19S6z5paUDkKxukNx/HS9weln6rJTP/su7mxFpSbzH75draeepuKHh99qotQAVGV/vl8ASUmvG2HKT2u/4FdORnP51CE'
            'q7Yc3Gy6ej/+N5haCP5a2PZFQY5RIY8RLvx7s7n6v7XtLC+9SotclewJpm2Zq5LTJ0hwGkpdeQZ8IhB8GwpeUYAI+yuYge++e/bi'
            '5ZvvRy++e/+PD2uGy+LDWvr1+7AWWOAPa16EMzrr6RJsQdP0fZnuRvrWPo2NSUyhOZB76c2HBl8RK8L6z9yupIn9JJRhG5Qh+Jji'
            'Y0ZupEta/IuWPKEKlSlVyttR5ezV316PPqyLouL+f4xW/lumDf2wpkhQeN4K/6Q1xH/ORYkLTE4QHs0Xdr4YT1ejp6OX3757NvKf'
            'l38dqcV/jy9H62nN1taMnOf4ExjPaDlV8+Wn2SrpjWPl+2EOflYSfjpb+d4Q475nVvj+ReX8J4IUJDxZflg7h9TbIF1v1CX8WcAA'
            'NfePUYzhdWatb1wUHJp1GqYLHcHW+od1aS2Fn0UFP4mCLuCTdOrCuyUwGEqhNVEOESMMJrRTGP+W94j8txLajMRmHHqkiPvnhdcD'
            '8KQL41QovGWhL+0/Z6aEz0np4BNloS/n26Ql9p9wigW0A+03Y9CxNfZhTYrCL6ZwkoRn6Lvvn5+8CB+jmZldxN/6ZPFeHg/01+mw'
            'Z1qvvQ+pPz91C8+xY7sYXaj51/1XOeYyLtfzVy9/OMGjSzVZ26d6NnVjLzzawjswkMoPh1eUNTwnlRHh2VHTekM+JnTRkKC3eCUQ'
            'iOIwYsIwXJI+6pAPqAyMIryzuhxfrKMHdzo6++5dIKIJZCI/wP3qNatAb5wjFyZg389nq9PnL0bPfngJtNf+BSmFJ4aQGoaNtO+e'
            'O+Z/ls56ElKrWFi9sLYlrCoXYZWKOLWG1ixwqmepopnr8ql35z3PQmpDYC1YLFyaPrNFiWCU+7d5WUBnxAIDxPaIArnUgS0Dm0Xm'
            'ZFiEAQGrUGKAVQhiDeNxDSyXMqqnJdC4YrFNAT0CteK3tKLQAsfhcwJo4UzVsBkTRASxkn3J5bgUDUdFxvavuobTPJOjpl8/Kg4E'
            'BQqkQuffUuFnAeumeJT0ZjH8TxlEFSim4BnP/MAjBdEwWlKE8diG2xi2suMzYQIVbeXgPWw6sd42FjQKT6kNumNYD8al6RAsrk6k'
            'FTWWQVswcm5t/AnU9sZTFMxASQlSoQNNKtXQJ44mpaGQNoCMLJpP0m+pBsrU+BkgLrYvC1Sk6N5vp5a2+JZgIAu4gjkFni2dAbpQ'
            'Ktu15gCMnBfVtjGkLaft+DGoFrI8D1DZHxFTGHiBc9eAd29EFcCkF0aAtAJQP8L2EDdFeUtBtOa+rbwJ2i7VeF+uzYb5ueYKxIEr'
            'rAH6CISaMZWujMChG55P+aGvpHTgPsSb5/tPwmzTdWk5GxCgEqTpKwJZT2EhqwKcib7yoswABa0s+0jlaQoWBKsAPTAgTORzhmEt'
            '0ydTOvj1C2MGae2hR1mU7RgSpIozYpyhvoJjBKjn+/Ut4AIBtQtkGtmOtI2I0UPX1nJ42icTY8CSjFoADuM2oS1MPiVco2W3C/CX'
            'CSQ8yaws+kZPTzgjUVL2IkCgCErR7tkiwOnzEsZQBjXjZ1FEvfkFdkM3vKfZiNiLEREMAeoAPIbgsQbDBHIAclFE1fF0vl5Fobnl'
            '2gMRADLt0nuWNR2hmftcfOjDWB08/UayH4wJ4HX7q9Xrbi5fzg3wpfM2ADiKfWvmYU1LHHjDNl0ysqlA4zPeHCJ99dXhQqzz3MxP'
            'cmr7Pk3qx/SdRo6aZ6Kip5xy0LaKv3z511H921nz29nLk+fd7y/9bxhJ3hoGFEzjmmsqDsad93oj896rCk+MhWgW92Qo0QLevEat'
            '5CVKK65N1B3Rfa29OwPeWkqt1BuEWYrGwrmdjXo/dnEKDN7WFe3wWoWVxgaCpUqwbS0ZvumWpqqMGwyM6BBN+3m49uJ7VAOTcoHA'
            'nlbBBgqzT8methoZzdtYJjBX1TcDok8inCv6FklcMRCv+7UmMyJnRM6IfCtETp0AON4fV72L7VUhxgZUAZc08nffsWeVgfadIF7m'
            'Wo9qq5zNF7OL+arxaRgWqo0LUF40C5tyFC2F3sZXHs0A7WXwXTA4CR6tQJ6oK6Mk1SJXBF9CmMbJBXjvhCza+X8iGP/Tq4g/NB/f'
            'Eikj/tVbBL2gCDZNnymFtptMYZgnYZjbbKRohUkaolrBhY/QedxC58nzBpbrv1+kfwOg9v/eF6imJGJEu4ZtMzBmYMzAmIHxTwuM'
            '3EEwWzi54cNHQtWbZiysZxvwfkVen705Hb2yvml1Pp6ej15BdpL/OT1fK//Laziuvhy52WJ0Nl6uvXsT05dGbxIvJzvghwUi8MfT'
            'mLvTurKjpb1Q/je9HMGr6+XIjCE7Y3QZl7V2BjdlVK8XajVbfOyOw1sz9h+M1eRjyFlKvvk4m04+N/KzL5crLGy9b8fB/YqxKGrj'
            'InZ7QpLaMAopvp39azmaTUc/PHv/4z/ffXc6eq6WIa9oOVJTM3oOGVkXavFzFINGNE5eLMaXdjr6H7uYnbyHlJCYz9GXjN8Fv+jJ'
            'bGmXqyTs4ZcOx/S0k0kDBRFIl3q2gEa66NsGx8QUsI8xN8iaj6vPc/+zSU3X45X/q6oJ/NHT96PXVtXEXvhHlvPZdGlbBD7bFxOl'
            'K5V67HGfTfKwV4HCLlzQrTHVgdoyKqFgspmQxiAgiuOwbLRnL5CEmWwiJHUKRFSBFUQ24lZp3JGK2qVGoEK767V/uxEfkLh0EEJl'
            'Bebb0jAYgchM6WQVojS22e7vtLx/pkS6wc00LFvrlWS/bmj8XmEDTSRBzdhSVU15yDVirA0cx77uYPzusLn6hdrmwXu4Qf8QSM/w'
            'XC+v4Emr40XIufLkDHwC+7TpVnK6e7yJJFE6MEH4SUEwp0E4RiAcf+2EKIvBPsQgzj0NBMLiNX5Cz7jHMmyochTDh1fM9NT6F9Lg'
            'LkCeBof7Rj23JrGZGZHQqRVuY3gO7GdOy5q3apsihnl7qxS28TkRvMvlAHatA942zECXuAuId0Fy/IQ+Hy1Xdr6MQ/w36N8mNGBD'
            'Algp+zmTUS54VQbdKjZizmkWomTws+tsyHVR69UnsIogP/sjHMiaf1qoZdgLADigUlcbAd6QVMFjLlJCiatZLZ47VSPE3kCwDRgA'
            'lNTbKVG46mxLAXFi78UFwjnVCEi9emkaXJitZLRo8Io6AQkljIapBy6XIshMBUo3Tj06PU+ex42Cv43Pn5CIfWXf7YEntu8zwCyR'
            'aEjvDS5wLJlhkMtSibDvH3YiLeC6x5C66zso/10BbEi/R09Zpgl7Bm/w1YAfnW55UqdbMItgIzkrGvjZImPxGQas4BnCbvQepSqQ'
            'MLZZ87MipNEhwsCeSPSCao49CE3xByLodgRON3mSsEv1t7dnqXAnm5C/hFR4b3mq4HPb6yE0JnanEJ3GPNNZ9ZEkUMHGrL2QDxug'
            'AbbOmlGmaxC32qixdgjwNq361OtbfDRjdT6dLb13GX2vs1evGxxqUkM3lbBX+DoqqESvDKpYtLHx6qXWNMtc56cHJuNSJ0hfymay'
            '26AsBa6HxpuQkIgJ69uwdewpyZbrlDfcHHdyOdOqWk/U4nPtXH4PG8w9BzMHT+49Atu3IZMEgys220aUMVpZTTKrhdeVvnKWo/Nn'
            '6ry2kPvGPDM3fM10yZPDIRFzomSn7FPnJsSN5WC1Rmu2C/X9/TV5cfL27O2bjRMaIhCTFYPi3oR9Lqz+pKbjJXjnE3upAgKlm/Tp'
            '2MBia62YkBdbW8JEuua8WZ8wqdVcB1efRePixb7iRyE3Oc5km4tZ0zacKIinFFLxje9B3j/wZFiVsok69U4CGUiOiOFmIPf3dup1'
            'wWQE+SMN7seTEzHRNmWgOl0D82BtkmIjtSvGuRIdGZ/xemVz5ZLTSDUjJnPvAshfdEqp6w48iDaVPWmh9kkS5K+ncGXYMcE8qnkP'
            'ELrNkXCiaye4lxRL1zio9RZDko2Snk/yYyibgyN1bvSVJPy0zRSAtpMrzeEJ1EpcyHShrqPcS6iplbQRE+Aiu6Tu77Vt1PW5rrSV'
            'vJ/S77q2voAF0py+3m5t4vX7D3YazLvZ7CIZBMPENZStmyBBz3JzA23+DvVUU5qENWRVyCuKh462YvL1rb5Sr2dvmibTeTf6MiTU'
            'RzPlmmZevGgbqTk4jE4qjppjDpuvPDt7+77Pb9FsTlVVSvBU2uD9s1fduAfyMdO8TmFMsK6Fq1ktfd9FqxJQa6itzeG/++7su3cv'
            'vwtUDwxigoIIB3ZIwVvfpO/R9zLC3799+yaRljaQ0mO5a4j+5sXfEzvENgItKhPMTBEw1eGrL76GYhVd314pqSYyUi91QvfNl79/'
            '++zHdtTh6fpYUTwOlAairhn7s7UZz76vNUdoKqr3aLHd9GLAq6tvS+5IQ+YUtqL1FkH4esmPGqq0lWogPeWb7vk3z16/bfuOkTlZ'
            'q42gXSUwgxBmI594o79vZ68TDggIHz2MmwWuPZCUsLh3hWhsART5Doeul96b65+wXtZ//AfOUdvpxjHoojsGTeoT0OzKufCJdatw'
            'T8aF+vVV8nu4QtqbVl92vjoO8O/1m/473nz2r2RkK+jLTyjcZFG99M6fb+0E/fZnubKgvnsn3F+yGKswmzXMxvvkq3pZf4XVCJT1'
            'NsQTDEun4zUEaIdbC8bmZlJMVGUnV4/rE3yMS3KMCb/+JgO6cV6/RMdMHoub7zHA6Anv7jFggtZM5GeMCh6mTCWLU67P6+8oMIvZ'
            'L3efz93vH+jdy8DLZD68no7gvel4NwQjnJr2IwJTRENnGnYBi5s5t+FUGMh4NbF3v8Wi3LL2/JizHda+I5TkHaE8sQOIYNxf9CQM'
            '0NKqcfQBW3cgzGp2fh7nCtLloWgZr/+Pl8id1JB6DHeDqGqSzLe5Nq4Tz81bMG5z38XNRNyZ4Qh5UkiSyJDEUXpQpCITT0pvcvY5'
            'ztudrHESe9EhUexERQVlA57/88cf3745+q1hpm16iHoUaAYmYJIwMhmXV/CbNFBZbtFAvSYxSfAibXdD9xQg0T3dE0azakolwAx+'
            'UNMvkIJ7ubFE4BT/xNW7SnYRgwgoqCj+8nWb+hZS+6LrI4MXKlEwuSgBQ8jWjnrrHjWHi8ONHzEQkHgwtccbTwPHHa72HMm2ez+6'
            'rLj+Gd8YCtzkv40Txsnpsdop5KI9SdYLHV65WuH6U2XRG492W7xWIm4UNLt1cJw8/u5/bshJu6XYttyOJz2OjfqxgBiM8tRDzbrU'
            '2wWY4419k/TIeXBywFK8GE/scjWbtkG1QcKGU0N1jH4HIvfub+iTaGNS6beUaNUemWm2t7besFGH16+9+yJuG8YQdhq1q+PFyXHz'
            '/sFd3AZWulNSzbGWJkwfztSHHXhvfG+kfGy/76fP/PVR+BC/7p55NV55L3+1XtgRwMe1Qe+tR+2/+JKeK4YDunNjPUH5utco7rfS'
            '21prD06Ovh5BqARuOIiOdaRoiG3CV+l5/m67OT1WTvoOEqPabZkhvo8Tnajf1S3tryF5ub8o8a53P93uLGx/Vcs/biI46iNRejvP'
            'rsfgrkjAULwu2aT6OqRvKdyGmdvsUHSVta90AFGhLpQaL3PgNN6GA3jXxCxC0DoRwW5d8A69xIPZnMS7lLop1dEoHS7LCLGU7rhm'
            'v79I9PpCjVbKejPc0mugt+HF2cyv1Gyc5of0LYbmtq+uww5I8LWdCMdChgoJwdG4wa/CVUTUbQOBDXKBwPWbDLbWZbsNn+6x1qNM'
            'ttKFCEsVVVNUialtcnUfNijVevFIt2/XuzooUXSxfYpKipAHFELay5d6ij/YZOmNF0MmQnfdUgc2kFaQvp3AEDassUeiWHLGTZNR'
            'A6y5i9cANvaAl4S8ge1dc0oe5lbA3XyG2sbOej3r9azXs17Pej3r9UfU6ztoUCi5MJ8teqrNE6BVbagsi6DWiqDVupvP6z2E5mP/'
            'uXKreAuynk0mHp3SyKb/aH0x/V7No8rtQp8PXIdyoJzF8fV7F221ixjJjfc7n9SB3iu1LT6Nl6vZ4nMTAfbo/A8LeydNreyrwfJe'
            '6ewPYa/If/Thmm2d+o2f4o3Si8+xh9IgTTwfnjhSoZOSMXoiC6ZPkJJ+rsZgSaEu8cROz8PeWFGX8k2GuoTf/UjbiqSPWdY71+/N'
            '9XvvWIBeWTjOeRIPgtYrcrK0aqH3UZheY8qrwlhhMSkxZ4wpifh2xCoYM5w7UjqEiBVSlhUrxWCFnYHHD7z27eCody9dcM0KP1IR'
            '3IFJ3LEW6XBrD12L9IAWY79F7FrwgCSikLfaV8RLCALgIuhitfh1fOmdeYSfIFTy8pK0OvhhMMRoKiiuCsdKzBBxThOPum0JMI6Z'
            '1dSrN1JxYZHV0vKkQhgzWmNtS6ILbGQhsDfKcbEdgWTBnSkY4spbvXArm//njcWhIqgDTd8CgXYqBjXcTSIL+9Y6WxnncXTMAH/c'
            'ZoVbq7iQ3l5W2hCv0TV2VgpvEw2qoMHWDloFDdNgd9RrlvuRFM7AkO+ocIZbe2iFszfSH5B6mUOO6p6gQlHihGAlq6jwjiAtikpq'
            'tx0qSkkcLhWjkiJblIRWlbGdh2xoIYxmgnns8f61JERWzg1CxWBrBw0VwzS4Hb+2a/5IeDEw7jvixXBrD40X+6X/YYDGvUaJdoaV'
            'L6te+7gRuXsyNwelabhM4S48cQtu+G33ZX8cfZGLE+fixLk48UEXJ76yDZGrp/5+j+jsvVRxq31mF7PpHhQOc1wV2CBtBDVWVlgb'
            'pMrtKkNYzoyUSmi/gI4b7qQoO5WBtOOcuarSVmrkECswpXZQJwy2dtAOyjANdhdJWOpH8ksGhntHv2S4tYf2S/ZC9sNwR4zZBy5o'
            'pZijtsBICosQRx4h9IApqbAtkLaFIX5paMmkKQkyLS5ILF3pDKfYWVMQZYU2FR3EhcHWDhoXhmmwM4P6hX4kVBgY7B1RYbi1h0aF'
            'PRD9MDDhfKZWG0GJ+qMPR/N1NRnrWCIIPjxFyjuMgllKjHngnTOhXGUr5ypHmBdz/9NbrqzbGtMl835kQUoulRakrEo3FLywTGOj'
            'JCsJJtYRqyxV3tUd2hojWjFSFYXyBr8pGEOIEqfvf2ts+wwOamtsC3N4+fmkFlO7XCY7qpgV8klIkrhE++WLgcX7HfHFcDcHzBeP'
            'Y0kMrP1tFrexJJStjK64xJz4RjkiJWWsC0rB7opwVmmlESEEI65UUQ4aGoOdHbShMUyinXUeMMIjWRoDo72jpTHc2kNbGvug+mGY'
            'Gp/gtqv9BMM51brwXkdVMOx/rypBhabbkYNRJynmReWYoRhz5/+ZokMOLlhBkMKlg8YMYbIknYtSOiwL5px1lhOtMS6cJHoQOQY7'
            'O2jkGCbRzjzcMMMjocfAiO+IHsOtPTR67Ivyh4EgYzggsx8EsdijRqWxpkxU2iHpxV7h7QiCSCEoBJa8lVEU3qpHFSlZl37BKsSx'
            'daxSjnmYsIRw1SEIM1xYbKkpCmaK0jtbHqz4IIIMdnbQCDJMop35uGGGR0KQgRHfEUGGW3toBNkX5Q8EQerbSPeIJKqoeEE0LUlZ'
            'ehNBKCzJ0LkCLLiyGhcUFUYqKT3+iEq2UEGkJoQqpAuBCGOCKcqTPC+GqXZlKQT2HgyySpSotMN5XoOdHTSSDJNod37eYIpHQpSB'
            'kd8RUYZbe2hE2fcKHAiyXE72sbtiNTKaImsYFxxLrl3h3MAZAepKqoyiQlInECq1LQspWrjAFSZ+IVHFNLLI2zicWDIMF4OtHTRc'
            'DNNgd2b1K/1IEDEw2jtCxHBrDw0R+6D6YcDCRO0nGwPbklbePJDaWlphwWSFq4FAOHeFdlR5O0E6wxXDleHSdf6K8sDCjMWVxaq0'
            'iDlOPL4P4cJgaweNC8M02JlDw1I/EjAMDPeOwDDc2kMDw17IfhjIcAE3tu8FGyqDDVPWltZWHK5BYQaTAWxQ3CmFKm6I9itUOFEx'
            'KaouGiq9sVcSVUrm1846RXBFh0+dDbZ22BkZgzTYmUnrxX6srIztA75rVsZgaw+elbEfwh8GPkw9ru3j3IAr/BPSyzI1HFkgv2Rq'
            'ABwIq7QsCZHcOYk9pBheVUnmv/cfXKEokVRrxjxWVAXp7AqivC1BfCMcaeSIoN5/qYaxY6izw8aOQRLtzMLACI8FHNtHe1fgGGzt'
            'wYFjD1Q/ENQw+7grxXk7QGkqCS1LrJG34QqOB3K/SyuJQZUzTJPCUMRKb32w4dOn2x8/9NOnQ6O+BQOax7oTZWCwdz1yOtjagx85'
            'fXyi71Pof6tv/npn4QK4cEBl2lbkPNGlU8wVVNCSUouJN5wgyz1eZvXjwiOAF0lP8rX+2a7yJWD5ErA9XwJ2P8h7HbPtAgLtlXnD'
            'KHC+BQUeSo7u/6j2/Z7GHezssGN9h39edTjw90WnUndv7cEDf3tfg/3a638YXs6M9yWMty/V8fu+BuK6g/z5Goh8DcTv6xqIuyFi'
            'vhIiGxL3Z0gcBDtkgcoClQ2kfE9WNpCygXQVz4ev8st4/oc0kO7tZqw/Wawli9SfzET6CZR1swcoxf0x/AFft9cQ4Kx9Otn7XI+f'
            'hjuOw/ZoLKvUffvDYmbWenUGs12NL+zbsLPnCcklYhwzRigun5RQZiuYQKGilW9svQDB+bRazU+fPkWYPyn8f8izdMH504WNhTOe'
            'dv08/S//+zfoq0CMb4AUfyHPrhLjK5j6N5OvgPDfeLL7hyb+33bSfxUI/w2Q4KuaTt9EKvlX+nTyH4THgAbfBPIGsf7sWcNPA+6d'
            'HE/Pw1JO7WQ5VGkeESGvVpn3wxyHrDr/lp2uxiugcOx+eTofzy2M4aRmjrG5mZ9+Hk/DU/WrHxdW+1+vMtoOjHV7RprD4i0urXm/'
            'UlFsch2tvIWe62jlOlq5jlauo5XraOU6WrmOVq6jleto5TpauY5WrqOV62jlOlq5jlauo5XraOU6Wjk/IOcH5PyAXEcr19HKdbRy'
            'Ha1cRyvX0cp1tHIdrVxHK9fRynW0ch2tXEcr19HKdbRyHa1cRyvX0cp1tHIdrVxHK9fRynW0ch2tXEcr19HKdbRyHa1cRyvX0cp1'
            'tHIdrVxHK9fRynW0ch2tXEcr19HKdbRyHa1cRyvX0cp1tHIdrVxHK9fRynW0ch2tXEcr19HKdbRyHa1cRytfApYvAct1tHIdrVxH'
            'K9fRyuUvch2tzHi5TESuo5WvgcjXQOSyP9mQyHW0ch2tLFDZQMr3ZGUDKRtIuehPNpByHa1cRyuLVK6j9aV1tOLtisFwHC99f6Gg'
            '1mwKM76x/JObzH75draeepOKHh99qutOAU2V/vl8AVUlvGmHKT2u/4FZORnP51B3qzYc3Gy6ej/+N1haCP5a2PZFQY5RIY8RLvx7'
            's7n6v7VNNvz0Ki1sVbRlrYpQ06oIJa2C/2h/BZPv3XfPXrx88/3oxXfv//FhzXBZfFhLv1Yf1gIL/GHNi3AeZz1dgt1nGgvvstl5'
            'DP365j6NjQG7J349B9IuvanQYCliRVjrmbs7HdgGHQg+pviYkUeiwtmrv70efVgXRcX9/xit/LdMG/phTZGg8LwV/klriP+cixIX'
            'mJwgPJov7Hwxnq5GT0cvv333bOQ/L/86Uov/Hl+O1tOaZa0ZOc/NJzCe0XKq5stPs1XSG8fK98Mc/Kwk/HS28r0hxn3PrPD9i8r5'
            'TwQpSHiy/LB2Dqm3QXLeqEv4s4ABau4foxjD68xa37goODTrNEwXOoJt8w/r0loKP4sKfhIFXcAn6dSFdzlgMJRCa6IcIkYYTGin'
            'MP4t7+34byW0GYnNOPRIEffPC4/x8KQL41QovGWhL+0/Z6aEz0np4BNloS/n26Ql9p9wigW0A+03Y9CxNfZhTYrCL6ZwkoRn6Lvv'
            'n5+8CB+jmZldxN/6ZPEeHA/01+mwZ1qvvX+oPz91C8+gY7sYXaj51/1XOeYyLtfzVy9/OMGjSzVZ26d6NnVjLyvawjswkMoPh1eU'
            'NTwnlRHh2VHTekM+JnTRkKC3eCUQiOIwYsIwXHo+6lANqAyMIrwjuhxfrKN3djo6++5dIKIJZCI/wH3pNatAb5wjFyZg389nq9Pn'
            'L0bPfngJtNf+BSmFJ4aQGoaNtO+eO+Z/ls56ElKrWFi9sLYlrCoXYZWKOLWG1ixwqmepopnr8ql31T3PQtpCYC1YLFyaPrNFiWCU'
            '+7d5WUBnxAIDxPaIArnUgS0Dm0XmZFiEAQGrUGKAVQhiDeNxDSyXMqqnJdC4YrFNAT0CteK3tKLQAsfhcwJo4UzVsBkTRASxkn3J'
            '5bgUDUdFxvavuobTPJOjpl8/Kg4EBQqkQuffUuFnAeumeJT0ZjH8TxlEFSim4BnP/MAjBdEwWlKE8diG2xi2suMzYQIVbeXgPWw6'
            'sd42FjQKT6kNumNYD8al6RAsrk6kFTWWQVswcm5t/AnU9oZRFMxASQlSoQNNKtXQJ44mpaGQNoCMLJpP0m+pBsrU+BkgLrYvC1Sk'
            '6N5vp5a2+JZgIAu4gjkFni2dAbpQKtu15gCMnBfVtjGkLaft+DGoFrI8D1DZHxFTGHiBc9eAd29EFcCkF0aAtAJQP8L2EDdFeUtB'
            'tOa+rbwJ2i7VeF+uzYb5ueYKxIErrAH6CISaMZWujMChG55P+aGvpHTgPsSb5/tPwmzTdWk5GxCgEqTpKwJZT2EhqwKcib7yoswA'
            'Ba0s+0jlaQoWBKsAPTAgTORzhmEt0ydTOvj1C2MGae2hR1mU7RgSpIozYpyhvoJjBKjn+/Ut4AIBtQtkGtmOtI2I0UPX1nJ42icT'
            'Y8CSjFoADuM2oS1MPiVco2W3C/CXCSQ8yaws+kZPTzgjUVL2IkCgCErR7tkiwOnzEsZQBjXjZ1FEvfkFdkM3vKfZiNiLEREMAeoA'
            'PIbgsQbDBHIAclFE1fF0vl5Fobnl2gMRADLt0ruNNR2hmftcfOjDWB28+EayH4wJ4HX7q9Xrbi5fzg3wpfM2ADiGfWvmYU1LHHjD'
            'Nl0ysqlA4zPeHCJ99dXhQqzb3MxPcmr7Pk3qx/SdRo6aZ6Kip5xy0LaKv3z511H921nz29nLk+fd7y/9bxhJ3hoGFEzjmmsqDsad'
            '4FGlyHtV4YmxEM3ingwlWsCb16iVvERpxbWJuiO6r7V3Z8BbS6mVeoMwS9FYOLezUe/HLk6Bwdu6oh1eq7DS2ECwVAm2rSXDN93S'
            'VJVxg4ERHaJpPw/XXnyPamBSLhDY0yrYQGH2KdnTViOjeRvLBOaq+mZA9EmEc0XfIokrBuJ1v9ZkRuSMyBmRb4XIqRMAR/fjqnex'
            'vSrE2IAq4JJG/u479qwy0L4TxMtc61FtlbP5YnYxXzU+DcNCtXEByotmYVOOoqXQ2/jKoxmgvQy+CwYnwaMVyBN1ZZSkWuSK4EsI'
            '0zi5AO+dkEU7/08E4396FfGH5uNbImXEv3qLoBcUwabpM6XQdpMpDPMkDHObjRStMElDVCu48BE6j1voPHnewHL994v0bwDU/t/7'
            'AtWURIxo17BtBsYMjBkYMzD+aYGROwhmCyc3fPhIqHrTjIX1bAPer8jrszeno1fWN63Ox9Pz0SvIPPI/p+dr5X95DUfRlyM3W4zO'
            'xsu1d29iatLoTeLlZAf8sEAE/nga83JaV3a0tBfK/6aXI3h1vRyZMeRijC7jstbO4KaM6vVCrWaLj91Rd2vG/oOxmnwM+UjJNx9n'
            '08nnRn725XKFha337Ti4XzEWRW1cxG5PSFIbRiHFt7N/LUez6eiHZ+9//Oe7705Hz9UyJA0tR2pqRs8h2+pCLX6OYtCIxsmLxfjS'
            'Tkf/Yxezk/eQEhLzOfqS8bvgFz2ZLe1ylYQ9/NLhmHp2MmmgIALpUs8W0EgXfdvgmJje9TGmAlnzcfV57n82aed6vPJ/VTWBP3r6'
            'fvTaqprYC//Icj6bLm2LwGf7YqJ0pVKPPe6zSR72KlDYhQu6NaY6UFtGJRRMNhPSGAREcRyWjfbsBZIwk02EpE6BiCqwgshG3CqN'
            'O1JRu9QIVGh3vfZvN+IDEpcOQqiswHxbGgYjEJkpnaxClMY22/2dlvfPlEg3uJmGZWu9kuzXDY3fK2ygiSSoGVuqqikPuUaMtYHj'
            '2NcdjN8dNle/UNs8eA836B8C6Rme6+UVPGl1vAg5V56cgU9gnzbdSk53jzeRJEoHJgg/KQjmNAjHCITjr50QZTHYhxjEuaeBQFi8'
            'xk/oGfdYhg1VjmL48IqZnlr/QhrcBcjT4HDfqOfWJDYzIxI6tcJtDM+B/cxpWfNWbVPEMG9vlcI2PieCd7kcwK51wNuGGegSdwHx'
            'LkiOn9Dno+XKzpdxiP8G/duEBmxIACtlP2cyygWvyqBbxUbMOc1ClAx+dp0NuS5qvfoEVhHkXn+Ew1bzTwu1DHsBAAdU6mojwBuS'
            'KnjMRUoocTWrxXOnaoTYGwi2AQOAkno7JQpXnW0pIE7svbhAOKcaAalXL02DC7OVjBYNXlEnIKGE0TD1wOVSBJmpQOnGqUen58nz'
            'uFHwt/H5ExKxr+y7PfDE9n0GmCUSDem9wQWOJTMMclkqEfb9w06kBVz3GFJ3fQflvyuADen36CnLNGHP4A2+GvCj0y1P6nQLZhFs'
            'JGdFAz9bZCw+w4AVPEPYjd6jVAUSxjZrflaENDpEGNgTiV5QzbEHoSn+QATdjsDpJk8Sdqn+9vYsFe5kE/KXkPjuLU8VfG57PYTG'
            'xO4UotOYZzqrPpIEKtiYtRfyYQM0wNZZM8p0DeJWGzXWDgHeplWfen2Lj2aszqezpfcuo+919up1g0NNauimEvYKX0cFleiVQRWL'
            'NjZevdSaZpnr/PTAZFzqBOlL2Ux2G5SlwPXQeBMSEjFhfRu2jj0l2XKd8oZb4U4uZ1pV64lafK6dy+9hg7nnYObgyb1HYPs2ZJJg'
            'cMVm24gyRiurSWa18LrSV85ydP5MndcWct+YZ+aGr5kueXI4JGJOlOyUferchLixHKzWaM12ob6/vyYvTt6evX2zcUJDBGKyYlDc'
            'm7DPhdWf1HS8BO98Yi9VQKB0kz4dG1hsrRUT8mJrS5hI15wl6xMmtZrr4OqzaFy82Ff8KOQmx5lsczFr2oYTBfGUQiq+8T3I+wee'
            'DKtSNlGn3kkgA8kRMdwM5P7eTr0umIwgf6TB/XhyIibapgxUp2tgHqxNUmykdsU4V6Ij4zNer2yuXHIaqWbEZO5dAPmLTil13YEH'
            '0aayJy3UPkmC/PUUrgw7JphHNe8BQrc5Ek507QT3kmLpGge13mJIslHS80l+DGVzcKTOjb6ShJ+2mQLQdnKlOTyBWokLmS7UdZR7'
            'CfWykjZiAlxkl9T9vbaNuvbWlbaS91P6XdfWF7BAmtPX261NvH7/wU6DeTebXSSDYJi4hrJ1EyToWW5uoM3foVZqSpOwhqwKeUXx'
            '0NFWTL6+1Vfq9exN02Q670ZfhoT6aKZc08yLF20jNQeH0UnFUXPMYfOVZ2dv3/f5LZrNqapKCZ5KG7x/9qob90A+ZprXKYwJ1rVw'
            'Naul77toVQJqDbW1Ofx335199+7ld4HqgUFMUBDhwA4peOub9D36Xkb4+7dv3yTS0gZSeix3DdHfvPh7YofYRqBFZYKZKQKmOnz1'
            'xddQiKLr2ysl1URG6qVO6L758vdvn/3Yjjo8XR8riseB0kDUNWN/tjbj2fe15ghNRfUeLbabXgx4dfVtyR1pyJzCVrTeIghfL/lR'
            'Q5W2Ug2kp3zTPf/m2eu3bd8xMidrtRG0qwRmEMJs5BNv9Pft7HXCAQHho4dxs8C1B5ISFveuEI0tgCLf5ZD10rtz/SPVy/qP/8DB'
            'aTvd8dTzxLr4/YX69VXye7wS+jbnp2P/f++eix/8q3161dwyvVLVS+/V+bdP0G9/lnsG6gtzwqUji7EKs1nDbLyzvaqXy1OEikBQ'
            'bxw8wfQ3+DZcHoB2uGtgbG4mxURVdnL13D3Bx7gkx5jw68/d041z9yU6ZvJYpLcPNNc+9dkGoyectqyDcCkD96CCh+lSyeJ060P4'
            'N0kB/Bk455e7z2WHOwS2z4XBWLu5eIMvzIXXUxG8NxXvV2CEU1t9RGB6aOiQwg7z3oFjGw6FgYxXE3v3uxbKLWvOjznbYc0TIjEU'
            'iOSJDETCGPcXO/HpWzo1XjsA5Q5EWc3Oz+M8QaI89CzjPf3xtreTGh6P4RIPVU2SuTb3u/nHwydH3RUW9RMDt1V4SuCSA7fdjoI7'
            'cxohTwpJUsEhZZQbFOnIxJPSW5B9fkuPuG2/vyJ48ST6y7tQVsGd/8//+eOPb98c/dYw1zY9Qz0adGMFiYDByrjmgt+kb0qQq00i'
            '9NsUW9rsax4pyw3dE0fSqR8//B/U1D7o9SMD0MFxOpcaBCPkY1TeTiYisqCi+MvXbVJbSNqLTo0M/qVEwZiiBEwcW7vgrePTHBsO'
            'd3lEFz/xTWpfNp7zjXtX7QmRbTd6dPlufWaLQb5e3FEUbuPscHIurHb3uGjPiPWCglcuTbj+vFj0s6NFFi+MiFsAzT4cHBSPv/uf'
            'G1eotJuFbcvteNKD1qjv5ccwk6ceatal3gjAHG/siKSHyYP7AjbgxXhil6vZtA2XDRI2nAeqo+87ELl3M0OfRBuTSr+lRKv2MEyz'
            'cbX17ow6cH7trRZxQzAGp9N4XB0JTg6S94/k4jZk0p1/ag6sNAH4cFo+7K17s3ojmWMQCRPmrw+5h8h098yr8cr776v1wo4AOq4N'
            'Z289RP/F1+9csSDQnRvrCcrXvUZxv5Xepll7JHL09QiCIHB3QXSZI0VD1BK+Sk/qdxvJ6YFx0nd9GNVuywzxfZzVRP2ubmmIDcnL'
            '/cV/d73V6XanXPurWv5xU7xRH4nSe3d2PeB2RQKGInHJ9tPXITFL4TaA3OZ9oqusfaUDiPd0QdJ4TQOn8Z4bwLsmGhHC0YkIduuC'
            'd+glHrnmJN6S1E2pjjPpcA1GiJJ0BzH7/UWi11dltFLWm+GWXgO9DS/OZn6lZuM086NvMTT3eHUddkCCr+1EOBZyT0gIe8atexUu'
            'GaJuGwhskAsErt9ksLUu2w32dPe0HmWySS5EWKqomqJKTG2TqzusQanWi0e6HbnepUCJoovtU1RShDygENJeq9RT/MEmSw39IROh'
            'u0ipAxtIGEjfTmAIG9bYI1EsOeOmyZUB1tzFXQD7euB+P+8xeUsZ057HFJu5D/v6Zl+htq+zTs86Pev0rNOzTs86/RF1+g7aE4ok'
            'zGeLnlrzBOjUWllu7rzEu8rrDYTmY/+5mV28NM22wf/+52iqLpJdlGX4K/baftduUwx8DxH3oa/iNckD38ZNi/63P/32/wE8sMKv'
            'oF4CAA=='
        )))
        original, collapsed = recorded['original'], recorded['after']
        key = '["task:category-objectnav",null,null,null,null,null]'
        self.assertNotEqual(original['preservedState'], collapsed['preservedState'])
        self.assertEqual(original['preservedState']['contexts'][key]['taskView']['focusTargetByTree']['l'],
                         'pos:l:ff0298ffa17b4cfcf009bd')
        self.assertEqual(collapsed['preservedState']['contexts'][key]['taskView']['focusTargetByTree']['l'],
                         'np-reader-toggle')
        # The newly recorded field is M.taskContextKey(route); no artifact measurement changes.
        for snapshot in (original, collapsed):
            snapshot['taskContextKey'] = key
        untouched = copy.deepcopy(recorded)
        MODULE.check_reader_dom_identity(recorded['domIdentity'])
        MODULE.check_reader_toggle_transition(original, collapsed, original, True)
        self.assertEqual(recorded, untouched, 'validation must not erase raw diagnostic state')

    def test_reader_toggle_rejects_wrong_neutral_focus_and_every_unrelated_state_change(self):
        import copy
        original, collapsed, reopened = self.snapshots()
        key = original['taskContextKey']
        def both(snapshot, mutate):
            for state in (snapshot['preservedState'], snapshot['history']['model']):
                mutate(state)
        mutations = [
            lambda x: both(x, lambda s: s['contexts'][key]['taskView']['focusTargetByTree'].__setitem__('l', 'wrong')),
            lambda x: both(x, lambda s: s['contexts'][key]['taskView']['focusTargetByTree'].pop('l')),
            lambda x: both(x, lambda s: s['contexts'][key]['taskView']['focusTargetByTree'].__setitem__('c', 'stolen')),
            lambda x: both(x, lambda s: s['contexts'][key]['taskView']['lastRouteByTree']['l'].__setitem__('node', 'wrong')),
            lambda x: both(x, lambda s: s['contexts'][key]['taskView']['lastRouteByTree']['c'].__setitem__('node', 'wrong')),
            lambda x: both(x, lambda s: s['originTrail'][0]['taskView']['focusTargetByTree'].__setitem__('l', 'np-reader-toggle')),
            lambda x: both(x, lambda s: s['originTrail'][0].__setitem__('focusTarget', 'changed')),
            lambda x: both(x, lambda s: s['contexts']['unrelated'].__setitem__('focusTarget', 'changed')),
            lambda x: both(x, lambda s: s['contexts']['context'].__setitem__('graphScale', .9)),
            lambda x: x['history']['model']['contexts'][key]['taskView']['focusTargetByTree'].__setitem__('l', 'stale'),
            lambda x: x.__setitem__('taskContextKey', 'context'),
            lambda x: x.__setitem__('focus', 'wrong-focus'),
        ]
        for collapsed_phase, before, after in ((True, original, collapsed), (False, collapsed, reopened)):
            for index, mutate in enumerate(mutations):
                bad = copy.deepcopy(after); mutate(bad)
                with self.subTest(collapsed=collapsed_phase, mutation=index), self.assertRaises(RuntimeError):
                    MODULE.check_reader_toggle_transition(before, bad, original, collapsed_phase)
        # A correct after-pointer cannot excuse an incorrect initial/before pointer.
        for collapsed_phase, before, after in ((True, original, collapsed), (False, collapsed, reopened)):
            bad_before = copy.deepcopy(before)
            both(bad_before, lambda s: s['contexts'][key]['taskView']['focusTargetByTree'].__setitem__('l', 'wrong'))
            with self.subTest(before_phase=collapsed_phase), self.assertRaises(RuntimeError):
                MODULE.check_reader_toggle_transition(bad_before, after, original, collapsed_phase)
        bad_original = copy.deepcopy(original)
        both(bad_original, lambda s: s['contexts'][key]['taskView']['focusTargetByTree'].__setitem__('l', 'wrong'))
        with self.assertRaises(RuntimeError):
            MODULE.check_reader_toggle_transition(collapsed, reopened, bad_original, False)

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
        reopened = self.snapshots()[2]
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
 w.NavigationProductModel={KEY:'nav',getBucket:()=>bucket,contextKey:()=>key,taskContextKey:()=>JSON.stringify([route.scope,null,null,null,null,null])};
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
 assert.equal(initial.taskContextKey,JSON.stringify([route.scope,null,null,null,null,null]));assert.equal(initial.position.version,'v1');assert.equal(initial.reader.flowCount,5);assert.equal(initial.history.unrelated.external.keep,4);
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


class TaskRouteScreenshotChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        cls.science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        cls.expected = MODULE.task_route_expected(cls.science)

    def scope_snapshot(self, scope='task:category-objectnav'):
        import copy
        expected = self.expected['scopes'][scope]
        return {'ready': 'ready', 'home': False, 'readerHidden': False, 'scale': 1,
                'viewport': {'width': 1440, 'height': 900},
                'route': {'scope': scope, 'tree': 'l', 'node': expected['roots'][0], 'paper': None, 'version': None},
                'panelScope': scope, 'groups': list(expected['groups']),
                'activeTree': 'l', 'treeCount': 1, 'forestCount': 1, 'rovingCount': 1, 'inactiveItemCount': 0,
                'readerLists': 0, 'canvasState': 'ready', 'selectedRelation': None, 'expanded': {'l': ['root'], 'c': []},
                'relationEntries': [dict(row, selected='false') for row in expected['relations']], 'relationOverview': {},
                'methods': [dict(copy.deepcopy(row), ready=True) for row in expected['methods']],
                'readerScroll': {'top': 490, 'left': 0}, 'treeScroll': {'top': 0, 'left': 0},
                'window': {'x': 0, 'y': 120}, 'focus': 'exact-endpoint', 'activatedControl': 'exact-endpoint'}

    def test_task_route_original_source_expectations_keep_scope_variants_and_condition_fields(self):
        e, s = self.expected, self.science
        self.assertEqual(e['poni']['id'], 'pos:l:98bc421b8bfd17d6699922')
        self.assertEqual(e['relation']['detail']['claimIds'], ['method-edge:89'])
        self.assertEqual(e['claim']['versionId'], 'publication:poni:e83f98bb7132')
        self.assertEqual([p['label'] for p in e['portable']], ['TAP-RL', 'TAP-LLM'])
        self.assertEqual(len({p['id'] for p in e['portable']}), 2)
        self.assertEqual(len({p['entityId'] for p in e['portable']}), 2)
        self.assertEqual(s['entities'][e['image'][1]['entityId']]['detail']['pipeline']['input'], '预给遍历录制、当前与goal RGB')
        self.assertEqual(s['entities'][e['image'][2]['entityId']]['detail']['pipeline']['input'], '目标环境已收集轨迹、当前/goal RGB')
        parent = s['positions'][e['image'][0]['parentId']]['entityId']
        self.assertIn('scene-specific适应条件可见，不标成未知房屋零样本', s['entities'][parent]['detail']['evidence'])

    def test_task_route_scope_rejects_missing_stale_unready_or_merged_original_positions(self):
        import copy
        valid = self.scope_snapshot()
        expected = self.expected['scopes']['task:category-objectnav']
        MODULE.check_task_route_scope(valid, 'task:category-objectnav', expected)
        mutations = [lambda x: x.update(home=True), lambda x: x.update(scale=.9),
                     lambda x: x.update(readerHidden=True), lambda x: x.update(panelScope='task:imagenav'),
                     lambda x: x['route'].update(node='different-root'), lambda x: x['route'].update(paper='poni'),
                     lambda x: x['methods'].pop(), lambda x: x['methods'][0].update(ready=False),
                     lambda x: x['methods'][0]['position'].update(entity='other'),
                     lambda x: x['methods'][0].update(control='merged-control'),
                     lambda x: x['methods'][0].update(association='condition'), lambda x: x['groups'].reverse()]
        for mutate in mutations:
            bad = copy.deepcopy(valid)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_scope(bad, 'task:category-objectnav', expected)

    def test_task_route_proof_rejects_hidden_text_fragments_clipping_sticky_overlay_and_small_type(self):
        import copy
        area = {'x': 900, 'y': 200, 'width': 500, 'height': 600}
        rect = {'x': 930, 'y': 300, 'width': 350, 'height': 40}
        good = {'visible': True, 'opaque': True, 'unscaled': True, 'clipped': False, 'fontSize': 15,
                'foreground': [20, 30, 40], 'background': [255, 255, 255], 'rect': rect,
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900}, 'readerContent': area,
                'clipAreas': [dict(area)], 'renderedText': '原条件', 'fragments': [dict(rect, visible=True)]}
        good['textRuns'] = [{'text': '原条件', 'fontSize': 15, 'opaque': True, 'unscaled': True,
                             'foreground': [20, 30, 40], 'background': [255, 255, 255],
                             'fragments': [dict(rect, visible=True)], 'clipAreas': [dict(area)]}]
        MODULE.check_task_route_proof(good, '原条件')
        mutations = [lambda x: x.update(visible=False), lambda x: x.update(opaque=False),
                     lambda x: x.update(unscaled=False), lambda x: x.update(clipped=True),
                     lambda x: x.update(fontSize=14.99), lambda x: x.update(foreground=[180, 180, 180]),
                     lambda x: x.update(renderedText='同任务零样本'), lambda x: x.update(fragments=[]),
                     lambda x: x['fragments'][0].update(visible=False),
                     lambda x: x['fragments'][0].update(y=190),
                     lambda x: x['readerContent'].update(y=350),
                     lambda x: x['clipAreas'][0].update(height=90), lambda x: x['rect'].update(x=1300),
                     lambda x: x['textRuns'][0].update(fontSize=10), lambda x: x['textRuns'][0].update(foreground=[]),
                     lambda x: x['textRuns'][0].update(fragments=[]), lambda x: x['textRuns'][0]['clipAreas'][0].update(height=90)]
        for mutate in mutations:
            bad = copy.deepcopy(good)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_proof(bad, '原条件')

    def test_task_route_relation_rejects_wrong_claim_source_namespace_version_and_closed_evidence(self):
        import copy
        e, c = self.expected, self.expected['claim']
        row = {'id': e['relation']['id'], 'type': e['relation']['relationType'], 'renderAsTree': 'false',
               'scope': 'current-scope', 'open': True, 'from': e['relation']['from'], 'to': e['relation']['to'],
               'claims': [{'id': c['id'], 'version': c['versionId'], 'relation': 'same-version',
                           'statement': c['statement'], 'sources': [{'url': r['url'], 'status': e['claimSourceStatus']} for r in c['sourceRefs']]}],
               'targets': [{'position': e['poni']['id'], 'control': 'exact-endpoint'}]}
        MODULE.check_task_route_relation({'changes': [row]}, e)
        mutations = [lambda x: x.update(id='tasks:relation:90'), lambda x: x.update(open=False),
                     lambda x: x.update(renderAsTree='true'), lambda x: x.update(scope='outside-scope'),
                     lambda x: x.update({'from': 'wrong-endpoint'}), lambda x: x.update(to='wrong-endpoint'),
                     lambda x: x['claims'][0].update(id='method-edge:90'),
                     lambda x: x['claims'][0].update(version='arxiv:2201.10029v1'),
                     lambda x: x['claims'][0].update(statement='Other statement'),
                     lambda x: x['claims'][0].update(sources=['https://example.org/']),
                     lambda x: x['claims'][0]['sources'][0].update(status='stale source version'),
                     lambda x: x['targets'][0].update(position='same-paper-wrong-position')]
        for mutate in mutations:
            bad = copy.deepcopy(row)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_relation({'changes': [bad]}, e)

    def test_task_route_return_requires_exact_original_route_scroll_and_active_control(self):
        import copy
        before = self.scope_snapshot()
        MODULE.check_task_route_return(before, copy.deepcopy(before), 'exact-endpoint')
        mutations = [lambda x: x['route'].update(scope='scope:all'), lambda x: x['route'].update(version='another'),
                     lambda x: x.update(focus='other-method-on-same-paper'), lambda x: x.update(panelScope='task:imagenav'),
                     lambda x: x['readerScroll'].update(top=489), lambda x: x['treeScroll'].update(left=1),
                     lambda x: x['window'].update(y=0), lambda x: x.update(scale=.9)]
        for mutate in mutations:
            bad = copy.deepcopy(before)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_return(before, bad, 'exact-endpoint')

    def test_task_route_method_rejects_same_paper_wrong_variant_version_or_pipeline(self):
        import copy
        p = self.expected['poni']
        e = self.science['entities'][p['entityId']]
        data = {'ready': 'ready', 'home': False, 'readerHidden': False, 'scale': 1,
                'route': {k: p[v] for k, v in {'node': 'id', 'scope': 'scopeId', 'tree': 'tree', 'paper': 'paperId', 'version': 'versionId'}.items()},
                'position': {'entity': p['entityId']}, 'mechanism': {'entity': p['entityId'], 'ready': True,
                'flow': [e['detail']['pipeline'][k] for k in ('input', 'representation', 'decision', 'execution', 'feedback')]}}
        MODULE.check_task_route_method(data, p, e)
        mutations = [lambda x: x['route'].update(node='another-position'), lambda x: x['route'].update(version='another-version'),
                     lambda x: x['mechanism'].update(entity='other-same-paper-variant'),
                     lambda x: x['mechanism'].update(ready=False), lambda x: x['mechanism']['flow'].reverse()]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_method(bad, p, e)

    def test_task_route_javascript_compiles_actual_scripts_and_uses_real_inputs(self):
        import ast
        import inspect
        source = inspect.getsource(MODULE.task_route_checks)
        tree = ast.parse(source)
        scripts = [MODULE.TASK_ROUTE_PROOF_JS, MODULE.TASK_ROUTE_SNAPSHOT_JS, MODULE.TASK_ROUTE_RETURN_WAIT_JS]
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'js' and node.args and isinstance(node.args[0], ast.Constant):
                scripts.append(node.args[0].value)
        result = subprocess.run(['node', '-e', "for(const s of JSON.parse(require('fs').readFileSync(0,'utf8')))new Function(s);"], input=json.dumps(scripts), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('.navigate(', source)
        self.assertNotIn('.dispatch(', source)
        self.assertNotIn('history.replaceState', source)
        self.assertNotIn('style.', source)
        self.assertNotIn('.click()', source)
        self.assertNotIn('.focus(', source)
        self.assertIn('driver.click(', source)
        self.assertIn("'type': 'wheel'", source)
        self.assertIn("'sceneLimit': 22", source)
        self.assertIn('transition_record(', source)
        self.assertIn('expose_source_position(', source)

    def test_task_route_real_js_measures_nested_hidden_transparent_small_and_clipped_text(self):
        script = r"""
const {JSDOM}=require('jsdom'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM(`<!doctype html><style>*{opacity:1;visibility:visible;transform:none;zoom:1;color:rgb(20,30,40);background-color:rgb(255,255,255);font-size:15px}a,span{display:inline}</style><aside id="np-detail-scroll"><div class="np-reader-heading">Reader</div><p id="proof">精确<span id="nested">限定</span></p><p><a id="source" href="https://example.org/">§3.4–3.6 ↗<span class="np-sr">（新标签页）</span></a></p></aside><div id="overlay"></div>`,{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,nested=d.getElementById('nested'),root=d.getElementById('proof'),source=d.getElementById('source'),reader=d.getElementById('np-detail-scroll');
Object.defineProperty(w,'innerWidth',{value:1440});Object.defineProperty(w,'innerHeight',{value:900});
// JSDOM omits Chrome's computed zoom property; geometry remains an explicit
// fixture, while opacity/color/font/overflow come from the real CSS cascade.
const style=w.getComputedStyle.bind(w);w.getComputedStyle=e=>new Proxy(style(e),{get:(target,key)=>key==='zoom'?(target.zoom||'1'):Reflect.get(target,key)});
function r(x,y,width,height){return {x,y,width,height,left:x,top:y,right:x+width,bottom:y+height};}
for(const n of d.querySelectorAll('*')){n.getBoundingClientRect=()=>n===reader?r(850,100,550,700):n.className==='np-reader-heading'?r(850,100,550,50):r(900,250,300,24);for(const [k,v]of Object.entries({clientLeft:0,clientTop:0,clientWidth:550,clientHeight:700,scrollWidth:550,scrollHeight:700}))Object.defineProperty(n,k,{value:v,configurable:true});}
w.Range.prototype.getClientRects=function(){const p=this.startContainer.parentElement;if(w.getComputedStyle(p).fontSize==='0px')return [];return [r(900,250,200,20)];};
let overlay=false,anchor=false;d.elementFromPoint=()=>overlay?d.getElementById('overlay'):anchor?source:nested.style.display==='none'?root:nested;
const snapshot=new w.Function(input.script),spec={selector:'#proof',text:'精确限定'},results=[snapshot(spec)];
for(const style of ['font-size:10px','color:rgba(20,30,40,0)','font-size:0px','display:none','opacity:0','transform:scale(.5)']){nested.setAttribute('style',style);results.push(snapshot(spec));nested.removeAttribute('style');}
nested.style.overflowX='hidden';Object.defineProperty(nested,'clientWidth',{value:30,configurable:true});results.push(snapshot(spec));nested.removeAttribute('style');Object.defineProperty(nested,'clientWidth',{value:550,configurable:true});
overlay=true;results.push(snapshot(spec));overlay=false;anchor=true;results.push(snapshot({selector:'#source'}));
const assert=require('node:assert/strict'),duplicate=root.cloneNode(true);reader.appendChild(duplicate);assert.throws(()=>snapshot(spec),/duplicated/);duplicate.remove();d.body.appendChild(root);assert.throws(()=>snapshot(spec),/outside its measured region/);reader.appendChild(root);
process.stdout.write(JSON.stringify(results));}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_ROUTE_PROOF_JS}), text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        results = json.loads(result.stdout)
        MODULE.check_task_route_proof(results[0], '精确限定')
        for snapshot in results[1:-1]:
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_proof(snapshot, '精确限定')
        MODULE.check_task_route_proof(results[-1], '§3.4–3.6 ↗')

    def test_task_route_portable_claims_cannot_be_swapped_or_omitted(self):
        import copy
        rl, llm = self.expected['portable']
        def selected(p):
            return {'ready': 'ready', 'home': False, 'readerHidden': False, 'scale': 1,
                    'route': {k: p[v] for k, v in {'node': 'id', 'scope': 'scopeId', 'tree': 'tree', 'paper': 'paperId', 'version': 'versionId'}.items()},
                    'position': {'entity': p['entityId']}, 'mechanism': {'entity': p['entityId'], 'ready': True, 'flow': [],
                    'claims': [{'id': c['id'], 'statement': c['statement']} for c in MODULE.task_route_claims(self.science, p)]}}
        valid = selected(rl)
        MODULE.check_task_route_method(valid, rl, self.science['entities'][rl['entityId']], MODULE.task_route_claims(self.science, rl))
        for claims in ([], selected(llm)['mechanism']['claims'], [dict(valid['mechanism']['claims'][0], statement='Shared generic method')]):
            bad = copy.deepcopy(valid)
            bad['mechanism']['claims'] = claims
            with self.assertRaises(RuntimeError):
                MODULE.check_task_route_method(bad, rl, self.science['entities'][rl['entityId']], MODULE.task_route_claims(self.science, rl))
        bad = copy.deepcopy(valid)
        bad['mechanism']['flow'] = ['invented representation alongside correct claims']
        with self.assertRaises(RuntimeError):
            MODULE.check_task_route_method(bad, rl, self.science['entities'][rl['entityId']], MODULE.task_route_claims(self.science, rl))

    def test_task_route_production_dom_exact_selectors_and_actual_controls(self):
        body = r"""
await scope('task:category-objectnav');await inventory('task:category-objectnav');states.push(snapshot());
const stable=JSON.stringify({state:a.getState(),history:w.history.state});snapshot();assert.equal(JSON.stringify({state:a.getState(),history:w.history.state}),stable,'read-only snapshot');
assert.equal(d.querySelectorAll('#np-tree [data-parallel-tree]').length,1);assert.equal(d.querySelectorAll('#np-tree [role=tree]').length,1);assert.equal(d.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]').length,1);assert.equal(d.querySelectorAll('#np-detail-scroll [data-route-method],[data-route-group]').length,0);
const disclosure=d.getElementById('np-task-route-relations');assert.ok(disclosure);assert.equal(disclosure.open,false);disclosure.querySelector('summary').click();assert.equal(disclosure.open,true);
const choice=d.querySelector('[data-task-change="methods:relation:90"]');assert.ok(choice);const routeBefore=JSON.stringify(a.getState().route),historyBefore=w.history.length;choice.click();await ready(()=>d.querySelector('[data-selected-task-relation="methods:relation:90"]'));assert.equal(JSON.stringify(a.getState().route),routeBefore);assert.equal(w.history.length,historyBefore+1);
const relation=d.querySelector('[data-selected-task-relation="methods:relation:90"]');assert.equal(relation.dataset.fromEntity,e.relation.from);assert.equal(relation.dataset.toEntity,e.relation.to);assert.equal(relation.dataset.renderAsTree,'false');
const claim=relation.querySelector('[data-task-change-claim="method-edge:89"]');assert.equal(claim.querySelector('.np-change-claim').textContent,e.claim.statement);assert.ok([...claim.querySelectorAll(':scope > p')].some(n=>n.textContent==='原文定位：'+e.claim.locator.join('；')));const anchor=claim.querySelector('.np-source a');assert.equal(anchor.href,e.claim.sourceRefs[0].url);assert.equal(anchor.nextElementSibling.textContent,' · '+s.versions[e.claim.versionId].label);
const endpoint=relation.querySelector('[data-change-target="'+e.poni.id+'"]');endpoint.focus();d.getElementById('np-detail-scroll').scrollTop=333;const before=snapshot();endpoint.click();await ready(()=>a.getState().route.node===e.poni.id&&a.getContent().ready(e.poni.entityId));states.push(snapshot());d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===before.route.node&&d.querySelector('[data-selected-task-relation]'));assert.equal(d.activeElement.id,before.focus);assert.equal(d.getElementById('np-detail-scroll').scrollTop,333);states.push(snapshot());
const wire=Object.fromEntries(Object.keys(before.route).sort().map(k=>[k,before.route[k]]));assert.equal(new w.Function(input.returnWait)(wire,before.focus),true);
await scope('task:imagenav');await inventory('task:imagenav');states.push(snapshot());for(const p of e.image){const item=d.getElementById('np-node-'+p.id);assert.equal(item.querySelector(':scope > [data-route-association]').dataset.routeAssociation,'condition');await select(p.id);const flow=d.querySelector('[data-mechanism-entity="'+p.entityId+'"]');assert.equal(flow.querySelector('.np-reading-association').textContent,'条件关联，不能按同一任务或同一评测协议理解。');assert.deepEqual([...flow.querySelectorAll('.np-method-flow dd')].map(n=>n.textContent),['input','representation','decision','execution','feedback'].map(k=>s.entities[p.entityId].detail.pipeline[k]));d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.scopes['task:imagenav'].roots[0]);}
await scope('setting:portable-objectnav');await inventory('setting:portable-objectnav');states.push(snapshot());for(const p of e.portable){await select(p.id);assert.equal(d.querySelector('[data-mechanism-entity="'+p.entityId+'"] > h3').textContent,s.entities[p.entityId].label+' · 方法内部结构');states.push(snapshot());d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.scopes['setting:portable-objectnav'].roots[0]);}
"""
        states = run_product_capture_script(self, body, {'expected': self.expected, 'science': self.science, 'returnWait': MODULE.TASK_ROUTE_RETURN_WAIT_JS})
        for index, scope in ((0, 'task:category-objectnav'), (2, 'task:category-objectnav'), (3, 'task:imagenav'), (4, 'setting:portable-objectnav')):
            states[index]['viewport'] = {'width': 1440, 'height': 900}  # Contract fixture, not actual browser geometry.
            MODULE.check_task_route_scope(states[index], scope, self.expected['scopes'][scope])
        MODULE.check_task_route_relation(states[2], self.expected)
        for index, p in ((1, self.expected['poni']), (5, self.expected['portable'][0]), (6, self.expected['portable'][1])):
            MODULE.check_task_route_method(states[index], p, self.science['entities'][p['entityId']], MODULE.task_route_claims(self.science, p))

    def test_task_route_actual_transition_functions_save_failed_click_and_wait_diagnostics(self):
        import copy
        for kind in ('select-exact-method', 'explicit-return-method-origin', 'cold-selected-relation', 'restore-literature'):
            for where in ('click', 'wait', 'after', 'save'):
                before, saved, reads = self.scope_snapshot(), [], []
                failure = RuntimeError('original action failure') if where == 'click' else TimeoutError('original wait failure')
                class Driver:
                    changed = False
                    def settle(self): pass
                    def js(self, script):
                        if script == MODULE.TASK_ROUTE_SNAPSHOT_JS:
                            reads.append('after' if self.changed else 'before')
                            if self.changed and where == 'after': raise RuntimeError('diagnostic failed')
                            return dict(copy.deepcopy(before), focus='changed' if self.changed else before['focus'])
                        reads.append('origin')
                        return {'route': before['route'], 'bucket': {'focusTarget': 'changed'}}
                driver, record = Driver(), {}
                def action():
                    driver.changed = True
                    if where == 'click': raise failure
                def wait(_): raise failure
                def save():
                    saved.append(copy.deepcopy(record))
                    if driver.changed and where == 'save': raise RuntimeError('diagnostic save failed')
                with patch.object(MODULE, 'wait_for', side_effect=wait):
                    with self.assertRaises(type(failure)) as caught:
                        MODULE.transition_record(driver, record, save, kind, action, lambda: False)
                self.assertIs(caught.exception, failure)
                self.assertEqual(saved[0]['transitions'][0]['before'], before)
                self.assertIn('after', reads)
                self.assertIn('origin', reads)
                self.assertEqual(record['transitions'][0]['origin']['bucket']['focusTarget'], 'changed')
                if where == 'after': self.assertEqual(record['transitions'][0]['afterError'], 'diagnostic failed')
                if where == 'save': self.assertEqual(record['transitions'][0]['saveError'], 'diagnostic save failed')

    def test_task_route_return_predicate_keeps_all_own_fields_types_focus_and_content_ready(self):
        script = r"""
const assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const route={nav:'1',tree:'l',node:'root',scope:'task:category-objectnav',bench:null,protocol:null,paper:null,version:null,claim:null,mode:'tree',template:null};
const panel={dataset:{taskRouteState:'ready'}},positions={root:{entityId:'r'}};
let current=route,hasPanel=true,focus='exact-control',pending=null;
globalThis.NavigationProductApp={getState:()=>({route:current}),getBundle:()=>({positions}),getContent:()=>({ready:entity=>entity!==pending})};
globalThis.document={querySelector:s=>s==='[data-task-route-scope]'?(hasPanel?panel:null):null,get activeElement(){return {id:focus}}};
const predicate=new Function(input.script),wire=Object.fromEntries(Object.keys(route).sort().map(k=>[k,route[k]]));
assert.notEqual(JSON.stringify(route),JSON.stringify(wire));assert.equal(predicate(wire,'exact-control'),true);
// Every own field matters, including fields whose original value is null.
for(const key of Object.keys(route)){const wrong={...wire,[key]:route[key]===null?'changed':null};assert.equal(predicate(wrong,'exact-control'),false,key+' changed');const missing={...wire};delete missing[key];assert.equal(predicate(missing,'exact-control'),false,key+' missing');current={...route};delete current[key];assert.equal(predicate(wire,'exact-control'),false,key+' missing from runtime');current=route;}
assert.equal(predicate({...wire,nav:1},'exact-control'),false,'string/number identity');
assert.equal(predicate({...wire,extra:null},'exact-control'),false,'extra null field');current={...route,extra:null};assert.equal(predicate(wire,'exact-control'),false,'extra runtime field');current=route;
for(const value of [null,undefined,[],1,'route'])assert.equal(predicate(value,'exact-control'),false,'non-object route');
const inherited=Object.create(wire);assert.equal(predicate(inherited,'exact-control'),false,'inherited fields cannot replace own fields');
focus='wrong';assert.equal(predicate(wire,'exact-control'),false);focus='exact-control';hasPanel=false;assert.ok(!predicate(wire,'exact-control'));hasPanel=true;
for(const entity of ['r']){pending=entity;assert.equal(predicate(wire,'exact-control'),false,entity+' content still pending');}pending=null;assert.equal(predicate(wire,'exact-control'),true);
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_ROUTE_RETURN_WAIT_JS}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_task_route_scroll_diagnostics_read_actual_fields_without_actions_or_state_changes(self):
        import ast
        import inspect
        task = ast.parse(inspect.getsource(MODULE.task_route_checks)).body[0]
        snapshot = next(node for node in task.body if isinstance(node, ast.FunctionDef) and node.name == 'snapshot')
        expected = ast.parse('def snapshot():\n    return driver.js(TASK_ROUTE_SNAPSHOT_JS)\n').body[0]
        self.assertEqual(ast.dump(snapshot, include_attributes=False), ast.dump(expected, include_attributes=False), 'diagnostics stay in the original single snapshot call')
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM(`<!doctype html><style>#np-detail-scroll{overflow-anchor:none;overflow-y:auto;font-size:15px;line-height:24px}.np-reader-heading{position:sticky}</style><main id="navigation-product" data-reading-layout="browse"><aside id="np-detail-scroll"><div class="np-reader-heading">Reader</div><section data-task-route-scope="task:category-objectnav"><h2>已有路线与方法</h2><p id="intro">原记录</p><details data-task-change="methods:relation:90" open><summary id="relation-summary">SemExp → PONI</summary><article><p id="claim">原句第一行与第二行</p></article><nav><button id="endpoint" data-change-target="poni-position">PONI</button></nav></details></section></aside></main>`,{url:'https://example.org/',runScripts:'outside-only'});
try{const w=dom.window,d=w.document,reader=d.getElementById('np-detail-scroll'),panel=d.querySelector('[data-task-route-scope]'),button=d.getElementById('endpoint');
// Explicit geometry fixtures test collection only; they are not evidence of
// Chrome layout, legal clamping, or the cause of the production 29px movement.
let top=2635,total=3700;const rect=(x,y,width,height)=>({x,y,width,height,left:x,top:y,right:x+width,bottom:y+height});
for(const node of d.querySelectorAll('*')){node.getBoundingClientRect=()=>node===reader?rect(900,100,720,1000):node.className==='np-reader-heading'?rect(900,100,720,40):rect(920,620,650,60);for(const [key,value] of Object.entries({clientTop:0,clientLeft:0,clientHeight:60,clientWidth:650,offsetHeight:62,offsetWidth:652,scrollHeight:60,scrollWidth:650,scrollTop:0,scrollLeft:0}))Object.defineProperty(node,key,{configurable:true,get:()=>value,set:()=>{throw Error('Unexpected diagnostic DOM write '+key);}});}
Object.defineProperties(reader,{scrollTop:{get:()=>top},scrollHeight:{get:()=>total},clientHeight:{get:()=>1000},offsetHeight:{get:()=>1002},clientWidth:{get:()=>720}});
w.Range.prototype.getClientRects=function(){return [rect(920,620,300,20),rect(920,644,250,20)];};
const faces=[{family:'Noto Sans CJK SC',status:'loaded',style:'normal',weight:'400',display:'swap'}];faces.status='loaded';Object.defineProperty(d,'fonts',{value:faces});
const bucket={focusTarget:'endpoint',windowScroll:88,detailScrollByTree:{l:2635},treeScrollByTree:{l:0},treeScrollLeftByTree:{l:0},selectedByTree:{l:'root'},expandedByTree:{l:['root']}};
const state={route:{scope:'task:category-objectnav',tree:'l'},revision:9,contexts:{context:bucket},originTrail:[{route:{scope:'scope:all',tree:'g'},bucket:{detailScrollByTree:{g:0,l:17}}}]},persisted=JSON.parse(JSON.stringify(state));persisted.contexts.context.detailScrollByTree.l=2631;w.history.replaceState({nav:persisted},'');
const model={KEY:'nav',contextKey:()=> 'context',getBucket:value=>value.contexts.context},api={};button.focus();
const read=new w.Function('"use strict";'+input.script+'return taskRouteDiagnostic(...arguments);'),savedState=JSON.stringify(state),savedHistory=JSON.stringify(w.history.state),before=read(api,model,state,reader,panel);
assert.equal(before.reader.scrollTop,2635);assert.equal(before.reader.scrollHeight,3700);assert.equal(before.reader.clientHeight,1000);assert.equal(before.reader.offsetHeight,1002);assert.equal(before.reader.maxTop,2700);assert.equal(before.reader.style.overflowAnchor,'none');assert.equal(before.availableContent.y,140);assert.equal(before.availableContent.bottom,1100);
assert.equal(before.runtime.bucket.detailScrollByTree.l,2635);assert.equal(before.persisted.bucket.detailScrollByTree.l,2631);assert.equal(before.runtime.originTrail[0].bucket.detailScrollByTree.l,17,'remaining trail is reported without substituting the popped activation origin');
assert.equal(before.activeElement.id,'endpoint');assert.equal(before.runtimeFocusTarget.element.id,'endpoint');assert.equal(before.targetControls[0].position,'poni-position');assert.equal(before.targetControls[0].ancestorDisclosures[0].open,true);assert.equal(before.disclosures[0].relation,'methods:relation:90');assert.equal(before.disclosures[0].open,true);assert.ok(before.directReaderChildren.length);assert.ok(before.overviewBlocks.length);
const text=before.textBlocks.find(x=>x.geometry.id==='claim');assert.equal(text.textFragmentCount,2);assert.equal(text.textHeight,44);assert.equal(before.fonts.status,'loaded');assert.equal(before.fonts.faces[0].family,'Noto Sans CJK SC');assert.equal(before.restoring.available,false);
top=2606;total=3606;d.querySelector('details').open=false;const after=read(api,model,state,reader,panel);assert.equal(after.reader.scrollTop,2606);assert.equal(after.reader.maxTop,2606);assert.equal(after.runtime.bucket.detailScrollByTree.l,2635);assert.equal(after.persisted.bucket.detailScrollByTree.l,2631);assert.equal(after.disclosures[0].open,false);assert.equal(after.targetControls[0].ancestorDisclosures[0].open,false);
assert.equal(JSON.stringify(state),savedState);assert.equal(JSON.stringify(w.history.state),savedHistory);assert.equal(d.activeElement,button);assert.equal(reader.scrollTop,2606);
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_ROUTE_DIAGNOSTIC_JS}), cwd=Path(__file__).parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class TaskDensityScreenshotChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        cls.science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        cls.cases = MODULE.task_density_expected(cls.science)

    def snapshot(self, case):
        import copy
        expected = case['expected']
        return {'ready': 'ready', 'home': False, 'readerHidden': False, 'scale': 1,
                'viewport': {'width': 1440, 'height': 900},
                'route': {'scope': case['scope'], 'tree': 'l', 'node': expected['roots'][0], 'paper': None, 'version': None},
                'panelScope': case['scope'], 'groups': list(expected['groups']),
                'activeTree': 'l', 'treeCount': 1, 'forestCount': 1, 'rovingCount': 1, 'inactiveItemCount': 0,
                'readerLists': 0, 'canvasState': 'ready', 'selectedRelation': None,
                'methods': [dict(copy.deepcopy(row), ready=True) for row in expected['methods']],
                'readerScroll': {'top': 0, 'left': 0}, 'treeScroll': {'top': 0, 'left': 0},
                'window': {'x': 0, 'y': 88}, 'focus': 'natural-entry-focus', 'changes': [], 'relationEntries': [dict(row, selected='false') for row in expected['relations']],
                'relationDisclosure': {'open': False, 'tag': 'DETAILS', 'id': 'np-task-route-relations', 'summary': 'np-task-route-relations-summary', 'current': str(sum(r['scope'] == 'current-scope' for r in expected['relations'])), 'outside': str(sum(r['scope'] == 'outside-scope' for r in expected['relations'])), 'beforeTree': True, 'insideTree': False},
                'density': {'state': 'ready', 'selectedReady': True, 'internalScroll': [{'id': 'np-detail-scroll', 'top': 0, 'left': 0}],
                            'roots': expected['roots'], 'gap': 'original gap' if case.get('empty') else None}}

    def test_density_source_contract_has_four_bounded_cases_and_no_invented_pipeline(self):
        self.assertEqual([c['scope'] for c in self.cases], ['task:category-objectnav', 'task:imagenav', 'setting:portable-objectnav', 'task:aerial-visual-object-search'])
        expected = MODULE.task_route_expected(self.science)
        for case in self.cases:
            self.assertTrue(all(p['region'] == 'canvas' for p in case['proofs']))
            self.assertFalse(any(p['text'].startswith(('表示：', '决策：')) for p in case['proofs']))
        image_text = [p['text'] for p in self.cases[1]['proofs']]
        for gid in expected['scopes']['task:imagenav']['groups'][:2]:
            self.assertIn(self.science['positions'][gid]['label'], image_text)
        portable = expected['portable']
        self.assertEqual(len({p['id'] for p in portable}), 2)
        self.assertEqual(len({p['entityId'] for p in portable}), 2)
        self.assertNotEqual(MODULE.task_route_claims(self.science, portable[0]), MODULE.task_route_claims(self.science, portable[1]))
        self.assertTrue(self.cases[3]['empty'])
        self.assertEqual(self.cases[3]['expected']['methods'], [])

    def test_density_rejects_scrolled_partial_wrong_relation_version_variants_and_false_empty_inventory(self):
        import copy
        for case in self.cases:
            valid = self.snapshot(case)
            MODULE.check_task_density_snapshot(valid, case)
            mutations = [lambda d: d['readerScroll'].update(top=1), lambda d: d['readerScroll'].update(left=1),
                         lambda d: d['treeScroll'].update(top=1), lambda d: d['density']['internalScroll'][0].update(top=1),
                         lambda d: d['density'].update(state='partial'), lambda d: d['density'].update(selectedReady=False),
                         lambda d: d.update(scale=.9), lambda d: d['route'].update(scope='scope:all'),
                         lambda d: d.update(treeCount=2), lambda d: d.update(forestCount=2),
                         lambda d: d.update(rovingCount=2), lambda d: d.update(inactiveItemCount=1),
                         lambda d: d.update(readerLists=1), lambda d: d.update(selectedRelation='methods:relation:90'),
                         lambda d: d['density'].update(roots=['wrong-root']), lambda d: d['relationDisclosure'].update(open=True),
                         lambda d: d['relationDisclosure'].update(beforeTree=False), lambda d: d['relationDisclosure'].update(insideTree=True),
                         lambda d: d['relationDisclosure'].update(current='999'), lambda d: d['relationDisclosure'].update(tag='DIV')]
            if valid['methods']:
                mutations += [lambda d: d['methods'][0].update(version='other-version'),
                              lambda d: d['methods'][0]['position'].update(entity='merged-variant'),
                              lambda d: d['methods'][0].update(association='unconditional'),
                              lambda d: d['methods'].append(copy.deepcopy(d['methods'][0]))]
            if case.get('empty'):
                mutations += [lambda d: d['relationEntries'].append({'id': 'invented'}),
                              lambda d: d['changes'].append({'id': 'invented'}), lambda d: d['density'].update(gap=None)]
            for mutate in mutations:
                bad = copy.deepcopy(valid)
                mutate(bad)
                with self.assertRaises(RuntimeError): MODULE.check_task_density_snapshot(bad, case)

    def test_density_actual_orchestration_uses_only_natural_entry_clicks_and_saves_scroll_failures(self):
        import copy
        import inspect
        source = inspect.getsource(MODULE.task_density_checks)
        for forbidden in ('scrollIntoView', '.focus(', 'driver.cdp(', 'reveal(', 'scrollTop=', 'navigate(', "'/actions'"):
            self.assertNotIn(forbidden, source)
        owner = self
        transition_error = TimeoutError('actual transition timed out')

        class Driver:
            def __init__(self, failure=None):
                self.index = -1
                self.current = None
                self.failure = failure
                self.reads = 0
                self.proof_reads = 0
                self.calls = []
            def call(self, method, path, payload):
                owner.assertEqual((method, path), ('POST', '/url'))
                self.calls.append(('url', payload['url']))
                self.index += 1
                self.current = owner.cases[self.index]
                self.reads = 0
                self.proof_reads = 0
            def click(self, element):
                self.calls.append(('click', element['selector']))
            def selector(self, selector):
                return {'selector': selector}
            def settle(self):
                self.calls.append(('settle',))
            def js(self, script, *args):
                if script == MODULE.TASK_DENSITY_SNAPSHOT_JS:
                    self.reads += 1
                    if self.failure == 'wait-and-snapshot' or (self.failure == 'capture-and-snapshot' and self.reads == 2):
                        raise RuntimeError('diagnostic snapshot failed')
                    data = owner.snapshot(self.current)
                    if self.failure == 'scroll':
                        data['readerScroll']['top'] = 42
                    if self.failure == 'late-window' and self.reads == 2:
                        data['window']['y'] = 100
                    return data
                if script == MODULE.TASK_DENSITY_PROOFS_JS:
                    self.proof_reads += 1
                    return [{'spec': spec, 'actual': self.proof(spec)} for spec in args[0]]
                if script.startswith('return !!window.NavigationProductApp'):
                    return True
                if script.startswith('var a=NavigationProductApp,r=a.getState().route'):
                    return self.failure not in ('wait-timeout', 'wait-and-snapshot', 'wait-and-save')
                raise AssertionError('Unexpected script ' + script)
            def proof(self, spec):
                rect = {'x': 920, 'y': 300, 'width': 200, 'height': 30}
                area = {'x': 900, 'y': 200, 'width': 500, 'height': 650}
                if self.failure == 'late-geometry' and self.proof_reads == 2:
                    rect['y'] += 1
                fragment = dict(rect, visible=self.failure != 'hidden' and not (self.failure == 'late-hidden' and self.proof_reads == 2))
                return {'visible': True, 'opaque': True, 'unscaled': True, 'clipped': False, 'fontSize': 15,
                        'foreground': [10, 20, 30], 'background': [255, 255, 255], 'rect': rect,
                        'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900}, 'readerContent': area, 'clipAreas': [],
                        'renderedText': spec['text'], 'fragments': [fragment],
                        'textRuns': [{'fontSize': 15, 'opaque': True, 'unscaled': True, 'foreground': [10, 20, 30],
                                      'background': [255, 255, 255], 'fragments': [fragment], 'clipAreas': []}]}

        report, captured, saved = {}, [], []
        driver = Driver()
        with patch.object(MODULE, 'wait_for', side_effect=lambda check: self.assertTrue(check())):
            MODULE.task_density_checks(driver, report, lambda: saved.append(copy.deepcopy(report)), lambda name, **kwargs: captured.append(name), '1440x900', 'http://localhost/research/navigation/', self.science)
        self.assertEqual(len(captured), 4)
        self.assertEqual(len([c for c in driver.calls if c[0] == 'click']), 5)
        self.assertEqual(report['taskDensityChecks'][0]['documentTopClaimed'], False)
        for scene in report['taskDensityChecks'][0]['scenes']:
            self.assertEqual(scene['naturalEntryWindow']['y'], 88)
            self.assertEqual(scene['status'], 'captured_for_human_review')
            kinds = [a['kind'] for a in scene['actions']]
            self.assertEqual(kinds.count('click-task-entry'), 1)
            self.assertTrue(all(k.startswith(('read-', 'capture-')) for k in kinds[kinds.index('read-natural-entry'):]))
        def bounded_wait(check):
            if not check():
                raise transition_error

        for failure in ('scroll', 'hidden', 'late-window', 'late-hidden', 'late-geometry', 'wait-timeout', 'wait-and-snapshot', 'capture-and-snapshot', 'wait-and-save', 'capture-and-save'):
            report, saved = {}, []
            def capture(*args, **kwargs):
                if failure in ('capture-and-snapshot', 'capture-and-save'):
                    raise transition_error
            def save():
                saved.append(copy.deepcopy(report))
                scene = report['taskDensityChecks'][0]['scenes'][0] if report['taskDensityChecks'][0]['scenes'] else {}
                if (failure == 'wait-and-save' and 'initial' in scene) or (failure == 'capture-and-save' and 'afterCapture' in scene):
                    raise RuntimeError('diagnostic save failed')
            with patch.object(MODULE, 'wait_for', side_effect=bounded_wait):
                with self.assertRaises((RuntimeError, TimeoutError)) as caught:
                    MODULE.task_density_checks(Driver(failure), report, save, capture, '1440x900', 'http://localhost/research/navigation/', self.science)
            self.assertTrue(saved)
            scene = saved[-1]['taskDensityChecks'][0]['scenes'][0]
            if failure in ('wait-and-snapshot', 'capture-and-snapshot'):
                self.assertIs(caught.exception, transition_error)
                self.assertIn('initialSnapshotError' if failure == 'wait-and-snapshot' else 'afterCaptureSnapshotError', scene)
            elif failure in ('wait-and-save', 'capture-and-save'):
                self.assertIs(caught.exception, transition_error)
                self.assertIn('initialSaveError' if failure == 'wait-and-save' else 'afterCaptureSaveError', report['taskDensityChecks'][0]['scenes'][0])
            else:
                self.assertIn('initial', scene)

    def test_density_actual_javascript_syntax(self):
        import ast
        import inspect
        scripts = [MODULE.TASK_DENSITY_SNAPSHOT_JS, MODULE.TASK_DENSITY_PROOFS_JS]
        for node in ast.walk(ast.parse(inspect.getsource(MODULE.task_density_checks))):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'js' and node.args and isinstance(node.args[0], ast.Constant):
                scripts.append(node.args[0].value)
        result = subprocess.run(['node', '-e', "for(const s of JSON.parse(require('fs').readFileSync(0,'utf8')))new Function(s);"], input=json.dumps(scripts), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_density_production_roots_keep_source_fields_reachable_without_disclosure(self):
        body = r"""
const natural=new w.Function(input.naturalSnapshot);
for(const c of input.cases){await scope(c.scope);const canvas=d.getElementById('np-tree-scroll');for(const spec of c.proofs){const found=[...d.querySelectorAll(spec.selector)].filter(n=>n.textContent===spec.text);assert.equal(found.length,1,spec.selector+' '+spec.text);assert.ok(canvas.contains(found[0]));for(let p=found[0];p&&p!==canvas;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)assert.ok(p.querySelector(':scope > summary').contains(found[0]),'natural field is behind a closed disclosure');}states.push(natural());}
"""
        states = run_product_capture_script(self, body, {'science': self.science, 'expected': MODULE.task_route_expected(self.science), 'naturalSnapshot': MODULE.TASK_DENSITY_SNAPSHOT_JS, 'cases': self.cases})
        for data, case in zip(states, self.cases):
            data['viewport'] = {'width': 1440, 'height': 900}  # JSDOM is not physical viewport evidence.
            MODULE.check_task_density_snapshot(data, case)


class ExplorationCaptureChecks(unittest.TestCase):
    def restore_fixture(self):
        import copy
        route = dict(nav='1', scope='task:category-objectnav', tree='l', node='poni', paper='poni', version='v1', bench=None, protocol=None, template=None, claim=None, mode='tree')
        key = json.dumps([route[k] for k in ('scope', 'bench', 'protocol', 'paper', 'version', 'template')], separators=(',', ':'))
        neutral = json.dumps([route[k] for k in ('scope', 'bench', 'protocol')] + [None, None, None], separators=(',', ':'))
        view = {'schema': 1, 'lastRouteByTree': {'l': route, 'c': None}, 'focusTargetByTree': {'l': 'poni', 'c': None}}
        runtime = {'route': route, 'contexts': {key: {'expandedByTree': {'l': ['root', 'group']}}, neutral: {'taskView': view}}}
        return {'route': route, 'selectedRelation': None, 'expanded': {'l': ['root', 'group']}, 'relationOverview': {}, 'relationView': {}, 'scale': 1,
                'treeScroll': {'top': 320, 'left': 0}, 'readerScroll': {'top': 65, 'left': 0}, 'window': {'x': 0, 'y': 80},
                'focus': 'np-node-poni', 'taskView': view, 'treeCount': 1, 'forestCount': 1, 'rovingCount': 1,
                'inactiveItemCount': 0, 'runtime': runtime, 'persisted': copy.deepcopy(runtime)}

    def test_restore_rejects_zero_scroll_stale_neutral_pointer_and_exact_bucket(self):
        import copy
        before = self.restore_fixture()
        MODULE.check_exploration_restore(before, copy.deepcopy(before), nonzero=True)
        mutations = [lambda x: x['treeScroll'].update(top=0), lambda x: x.update(focus='np-node-other'),
                     lambda x: x['taskView']['lastRouteByTree']['l'].update(version='other'),
                     lambda x: x['taskView']['focusTargetByTree'].update(l='other'),
                     lambda x: x.update(treeCount=2), lambda x: x.update(rovingCount=2),
                     lambda x: x.update(inactiveItemCount=1), lambda x: x['relationOverview'].update(l={'open': True}),
                     lambda x: x['persisted']['contexts'].clear(), lambda x: x.update(scale=.9),
                     lambda x: x['relationView'].update(l={'id': 'wrong'}),
                     lambda x: x['taskView']['lastRouteByTree'].update(c={'node': 'unexpected'})]
        for mutate in mutations:
            bad = copy.deepcopy(before)
            mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_exploration_restore(before, bad, nonzero=True)
        zero = copy.deepcopy(before)
        zero['treeScroll']['top'] = 0
        with self.assertRaisesRegex(RuntimeError, 'nonzero'): MODULE.check_exploration_restore(zero, copy.deepcopy(zero), nonzero=True)
        inactive_before = copy.deepcopy(before)
        inactive_before['taskView']['lastRouteByTree']['c'] = {'tree': 'c', 'node': 'visited-in-the-meantime'}
        inactive_before['taskView']['focusTargetByTree']['c'] = 'visited-focus'
        restored = copy.deepcopy(before)
        restored['taskView']['lastRouteByTree']['c'] = copy.deepcopy(inactive_before['taskView']['lastRouteByTree']['c'])
        restored['taskView']['focusTargetByTree']['c'] = 'visited-focus'
        restored['persisted'] = copy.deepcopy(restored['runtime'])
        MODULE.check_exploration_restore(before, restored, inactive_before=inactive_before)
        restored['taskView']['focusTargetByTree']['c'] = 'overwritten-inactive-focus'
        restored['persisted'] = copy.deepcopy(restored['runtime'])
        with self.assertRaisesRegex(RuntimeError, 'inactive tree'):
            MODULE.check_exploration_restore(before, restored, inactive_before=inactive_before)

    def test_selected_scene_compares_one_proof_batch_before_and_after_capture(self):
        import ast
        import copy
        import inspect
        function = ast.parse(inspect.getsource(MODULE.task_route_checks)).body[0]
        scene = next(node for node in function.body if isinstance(node, ast.FunctionDef) and node.name == 'scene')
        code = compile(ast.Module(body=[scene], type_ignores=[]), '<actual-selected-scene>', 'exec')
        for changed in (False, True):
            record, saved = {'scenes': []}, []
            class Driver:
                captured = False
                calls = 0
                def js(self, script, specs):
                    self.calls += 1
                    self_outer.assertEqual(script, MODULE.TASK_DENSITY_PROOFS_JS)
                    return [{'spec': spec, 'actual': {'renderedText': 'changed' if changed and self.captured else spec['text']}} for spec in specs]
            self_outer = self
            driver = Driver()
            def capture(*args, **kwargs): driver.captured = True
            env = dict(driver=driver, record=record, prefix='1440x900', snapshot=lambda: {'route': 'unchanged'},
                       save=lambda: saved.append(copy.deepcopy(record)), TASK_DENSITY_PROOFS_JS=MODULE.TASK_DENSITY_PROOFS_JS,
                       check_task_route_proof=lambda *args: None, capture=capture)
            exec(code, env)
            specs = [{'selector': '#source', 'text': 'original'}]
            if changed:
                with self.assertRaisesRegex(RuntimeError, 'geometry changed'):
                    env['scene']('-selected', specs, scroll=False)
                self.assertIn('afterProofs', saved[-1]['scenes'][0])
            else:
                env['scene']('-selected', specs, scroll=False)
            self.assertEqual(driver.calls, 2)

    def test_new_orchestration_javascript_compiles_and_uses_actual_controls(self):
        import ast
        import inspect
        scripts = []
        for function in (MODULE.exploration_state_checks, MODULE.expose_source_position, MODULE.reveal_control, MODULE.task_route_checks, MODULE.cold_relation_refresh, MODULE.cold_relation_refresh_comparison):
            source = inspect.getsource(function)
            for forbidden in ('.navigate(', 'history.replaceState(', 'history.pushState(', '.dispatchEvent(', '.style.'):
                self.assertNotIn(forbidden, source)
            for node in ast.walk(ast.parse(source)):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == 'js' and node.args and isinstance(node.args[0], ast.Constant):
                    scripts.append(node.args[0].value)
        result = subprocess.run(['node', '-e', "for(const source of JSON.parse(require('fs').readFileSync(0,'utf8')))new Function(source);"], input=json.dumps(scripts), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        source = inspect.getsource(MODULE.task_route_checks)
        self.assertLess(source.index('open-method-relationship-disclosure'), source.index('select-methods-relation-90'))
        self.assertIn('cold_relation_refresh_comparison(driver, record, save,', source)
        self.assertIn('cold_relation_refresh(driver, record, save,', inspect.getsource(MODULE.cold_relation_refresh_comparison))
        for event in ('pin-exact-method-claim', 'browser-back-to-claim', 'browser-forward-to-relation', 'cold-selected-relation', 'relation-to-task', 'task-to-global'):
            self.assertIn(event, inspect.getsource(MODULE.cold_relation_refresh) if event == 'cold-selected-relation' else source)

    def test_packet_hold_accepts_only_existing_pinned_loopback_content(self):
        import hashlib
        import tempfile
        from types import SimpleNamespace
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory)
            raw = b'{"public":"reviewed fixture"}'
            digest = hashlib.sha256(raw).hexdigest()
            path = '/research/navigation/content/' + digest + '.json'
            packet = dist / path.lstrip('/')
            packet.parent.mkdir(parents=True)
            packet.write_bytes(raw)
            server = SimpleNamespace(server_address=('127.0.0.1', 9000))
            with MODULE.PacketHold(server, path, dist, digest) as hold:
                self.assertIs(server.packet_hold, hold)
                self.assertFalse(hold.released.is_set())
                with self.assertRaises(RuntimeError):
                    with MODULE.PacketHold(server, path, dist, digest): pass
            self.assertIsNone(server.packet_hold)
            self.assertTrue(hold.released.is_set())
            for bad_path in ('https://example.org/content.json', '/research/navigation/../secret.json', '/research/navigation/content/not-a-sha.json'):
                with self.assertRaises(RuntimeError): MODULE.PacketHold(server, bad_path, dist, digest)
            with self.assertRaises(RuntimeError): MODULE.PacketHold(SimpleNamespace(server_address=('0.0.0.0', 9000)), path, dist, digest)
            packet.write_bytes(b'changed')
            with self.assertRaises(RuntimeError): MODULE.PacketHold(server, path, dist, digest)

    def test_production_switches_keep_distinct_contexts_and_analysis_identity(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        expected = MODULE.task_route_expected(science)
        body = r"""
await scope('task:category-objectnav');await select(e.poni.id);const lRoute=a.getState().route;
assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisState,'imported');assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisVersion,e.poni.versionId);assert.equal(d.querySelector('[data-analysis-state=imported] > p').textContent,'本版本已导入：22 个原模板节点已填，0 个实例节点已填。');assert.equal(d.getElementById('np-open-analysis-template').textContent,'通用原59节点模板（未填答参考）');
d.querySelector('[data-tree-tab="c"]').click();await ready(()=>a.getState().route.tree==='c');const ci='pos:c:6a8a9d2f7b1f3ab3a8ada5';await select(ci);const cRoute=a.getState().route;
d.querySelector('[data-tree-tab="l"]').click();await ready(()=>a.getState().route.node===e.poni.id);assert.deepEqual(JSON.parse(JSON.stringify(a.getState().route)),JSON.parse(JSON.stringify(lRoute)));assert.equal(d.querySelectorAll('#np-tree [data-parallel-tree]').length,1);assert.equal(d.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]').length,1);assert.equal(d.querySelector('#np-tree').dataset.activeTaskTree,'l');
d.querySelector('[data-tree-tab="c"]').click();await ready(()=>a.getState().route.node===ci);assert.deepEqual(JSON.parse(JSON.stringify(a.getState().route)),JSON.parse(JSON.stringify(cRoute)));assert.equal(m.taskView(a.getState()).lastRouteByTree.l.node,e.poni.id);assert.equal(m.taskView(a.getState()).lastRouteByTree.c.node,ci);
d.querySelector('[data-tree-tab="l"]').click();await ready(()=>a.getState().route.node===e.poni.id);d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a');assert.equal(a.getState().route.node,s.analyses.poni[e.poni.versionId].roots[0]);assert.equal(a.getState().route.template,null);states.push(snapshot());
d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.poni.id);const vlfm=Object.values(s.positions).find(p=>p.scopeId==='task:category-objectnav'&&p.tree==='l'&&p.paperId==='vlfm'&&p.kind==='pipeline_recipe');await select(vlfm.id);assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisState,'not-imported');d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a');assert.equal(a.getState().route.node,null);assert.equal(a.getState().route.template,null);assert.ok(d.querySelector('#np-tree .np-empty').textContent.includes('尚未导入原59节点解析'));d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===vlfm.id);d.getElementById('np-open-analysis-template').click();await ready(()=>a.getState().route.template==='1');assert.equal(a.getState().route.paper,vlfm.paperId);assert.equal(a.getState().route.version,vlfm.versionId);const templateRoot=s.template.roots[0];label(templateRoot).click();await ready(()=>a.getState().route.node===templateRoot);assert.equal(d.querySelector('#np-detail-content .np-detail-body > .np-boundary').textContent,'参考模式：原59节点模板，当前论文/版本未填答；0答案，不计入解析覆盖。');assert.ok([...d.querySelectorAll('#np-detail-content .np-detail-block > p')].some(n=>n.textContent==='这是通用模板问题，当前论文版本未填答；不表示原论文没有讨论，也不借用其他论文的答案。'));states.push(snapshot());
"""
        states = run_product_capture_script(self, body, {'science': science, 'expected': expected})
        self.assertEqual(states[0]['route']['tree'], 'a')
        self.assertEqual(states[1]['route']['template'], '1')


class RelationHistoryChecks(unittest.TestCase):
    @staticmethod
    def snapshots(length=50):
        import copy
        before = ExplorationCaptureChecks().restore_fixture()
        before.update(historyEntryKey='native-before', historyLength=length,
                      focus='np-task-route-relations-summary', relationDisclosure={'open': True, 'id': 'np-task-route-relations'})
        before['taskView']['focusTargetByTree']['l'] = before['focus']
        before['runtime'].update(revision=1, originTrail=[{'route': {'scope': 'scope:all'}, 'focus': 'saved-origin'}])
        before['persisted'] = copy.deepcopy(before['runtime'])
        selected = copy.deepcopy(before)
        selected.update(historyEntryKey='native-selected', selectedRelation='methods:relation:90', focus='np-task-relation-title')
        selected['runtime']['revision'] = 2
        selected['taskView']['focusTargetByTree']['l'] = selected['focus']
        selected['relationView'] = {'l': {'id': 'methods:relation:90', 'route': copy.deepcopy(selected['route'])}}
        selected['persisted'] = copy.deepcopy(selected['runtime'])
        back = copy.deepcopy(before)
        back['focus'] = 'np-task-change-' + before['route']['scope'] + '-methods:relation:90'
        back['taskView']['focusTargetByTree']['l'] = back['focus']
        back['persisted'] = copy.deepcopy(back['runtime'])
        return before, selected, back, copy.deepcopy(selected)

    def test_relation_history_capped_length_needs_distinct_native_entries_and_exact_revisions(self):
        import copy
        # Actual 50c receipt projection; raw SHA256: dabc2e4ff52e6b5ff4dde0b34f54956cae29ea42e09209aaf881f026ec707f7b
        recorded = json.loads('{"before":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"historyLength":50,"selectedRelation":null,"focus":"np-task-route-relations-summary","runtime":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"revision":1},"persisted":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"revision":1}},"after":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"historyLength":50,"selectedRelation":"methods:relation:90","focus":"np-task-relation-title","runtime":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"revision":2},"persisted":{"route":{"bench":null,"claim":null,"mode":"tree","nav":"1","node":"pos:l:74abdf1c989032e2d82e82","paper":null,"protocol":null,"scope":"task:category-objectnav","template":null,"tree":"l","version":null},"revision":2}}}')
        self.assertEqual(recorded['before']['route'], recorded['after']['route'])
        self.assertEqual(len(recorded['before']['route']), 11)
        self.assertEqual((recorded['before']['historyLength'], recorded['after']['historyLength']), (50, 50))
        # The failed artifact lacks native entry keys and traversal evidence; it alone cannot pass.
        with self.assertRaisesRegex(RuntimeError, 'native key'):
            MODULE.check_relation_history_entry(recorded['before'], recorded['after'])
        before, selected, _, _ = self.snapshots()
        # These 50c receipt values reproduce the obsolete length gate failure.
        # Native keys below are unit fixtures, not keys recovered from that failed run.
        self.assertEqual((before['historyLength'], selected['historyLength']), (50, 50))
        self.assertEqual((before['runtime']['revision'], selected['runtime']['revision']), (1, 2))
        self.assertNotEqual(selected['historyLength'], before['historyLength'] + 1)
        MODULE.check_relation_history_entry(before, selected)
        added = copy.deepcopy(selected); added['historyLength'] = 51
        MODULE.check_relation_history_entry(before, added)
        for field, value in [('historyEntryKey', None), ('historyEntryKey', ''),
                             ('historyEntryKey', before['historyEntryKey']), ('historyLength', 49),
                             ('historyLength', 52), ('historyLength', True), ('selectedRelation', 'tasks:relation:90'),
                             ('focus', 'wrong')]:
            bad = copy.deepcopy(selected); bad[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(RuntimeError):
                MODULE.check_relation_history_entry(before, bad)
        for target in ('runtime', 'persisted'):
            for value in (1, 3, True):
                bad = copy.deepcopy(selected); bad[target]['revision'] = value
                with self.subTest(target=target, revision=value), self.assertRaises(RuntimeError):
                    MODULE.check_relation_history_entry(before, bad)
        bad = copy.deepcopy(before); bad['historyEntryKey'] = None
        with self.assertRaises(RuntimeError): MODULE.check_relation_history_entry(bad, selected)
        for target in ('runtime', 'persisted'):
            bad = copy.deepcopy(before); bad[target]['revision'] = True
            with self.subTest(before_revision=target), self.assertRaises(RuntimeError):
                MODULE.check_relation_history_entry(bad, selected)
        # replaceState cannot pass merely by increasing the model revision at length 50.
        replaced = copy.deepcopy(selected); replaced['historyEntryKey'] = before['historyEntryKey']
        with self.assertRaisesRegex(RuntimeError, 'replaced'):
            MODULE.check_relation_history_entry(before, replaced)
        # A selected entry and its faithful Forward replay must not both carry
        # damage introduced by the initial click to unrelated state.
        mutations = [lambda x: x['taskView']['focusTargetByTree'].update(c='stolen'),
                     lambda x: x['taskView']['lastRouteByTree'].update(c={'node': 'wrong'}),
                     lambda x: x['runtime']['originTrail'][0].update(focus='changed'),
                     lambda x: x['persisted']['originTrail'][0].update(focus='changed')]
        for index, mutate in enumerate(mutations):
            bad_selected = copy.deepcopy(selected); mutate(bad_selected)
            bad_forward = copy.deepcopy(bad_selected)
            self.assertEqual(bad_selected, bad_forward)
            with self.subTest(initial_selection=index), self.assertRaises(RuntimeError):
                MODULE.check_relation_history_entry(before, bad_selected)

    def test_relation_history_roundtrip_keeps_full_routes_scopes_scroll_disclosure_and_origin(self):
        import copy
        before, selected, back, forward = self.snapshots()
        for expected, actual, focus in ((before, back, back['focus']), (selected, forward, selected['focus'])):
            MODULE.check_relation_history_restore(expected, actual, focus, 50)
            mutations = [lambda x: x.update(historyEntryKey='wrong'), lambda x: x.update(historyLength=49),
                         lambda x: x['runtime'].update(revision=17), lambda x: x['persisted'].update(revision=17),
                         lambda x: x['runtime'].update(revision=True), lambda x: x['persisted'].update(revision=True),
                         lambda x: x.update(selectedRelation='methods:relation:89'), lambda x: x.update(scale=.9),
                         lambda x: x['treeScroll'].update(top=0), lambda x: x['readerScroll'].update(top=0),
                         lambda x: x['relationDisclosure'].update(open=False),
                         lambda x: x['taskView']['focusTargetByTree'].update(c='stolen'),
                         lambda x: x['runtime']['originTrail'][0].update(focus='changed'),
                         lambda x: x['persisted']['originTrail'][0].update(focus='changed')]
            for field in expected['route']:
                mutations.append(lambda x, f=field: x['route'].__setitem__(f, 'changed'))
            for index, mutate in enumerate(mutations):
                bad = copy.deepcopy(actual); mutate(bad)
                with self.subTest(focus=focus, mutation=index), self.assertRaises(RuntimeError):
                    MODULE.check_relation_history_restore(expected, bad, focus, 50)
        summary_focus = copy.deepcopy(back); summary_focus['focus'] = before['focus']
        with self.assertRaises(RuntimeError):
            MODULE.check_relation_history_restore(before, summary_focus, back['focus'], 50)

    def test_relation_history_uses_real_back_forward_and_saves_failed_wait(self):
        import copy
        before, selected, back, forward = self.snapshots()
        class Driver:
            def __init__(self): self.state = copy.deepcopy(selected); self.actions = []; self.waits = []
            def settle(self): pass
            def call(self, method, path, body):
                self.actions.append((method, path, body))
                self.state = copy.deepcopy(back if path == '/back' else forward)
            def js(self, script, *args):
                if script == MODULE.TASK_ROUTE_SNAPSHOT_JS: return copy.deepcopy(self.state)
                if script == MODULE.TASK_RELATION_HISTORY_WAIT_JS:
                    self.waits.append(args); return True
                return {'diagnostic': 'origin'}
        driver, record, saved = Driver(), {}, []
        MODULE.relation_history_checks(driver, record, lambda: saved.append(copy.deepcopy(record)), before, selected)
        self.assertEqual(driver.actions, [('POST', '/back', {}), ('POST', '/forward', {})])
        self.assertEqual([x['kind'] for x in record['transitions']], ['browser-back-relation-selection', 'browser-forward-relation-selection'])
        self.assertEqual(driver.waits[0], (before['route'], back['focus'], before))
        self.assertEqual(driver.waits[1], (selected['route'], selected['focus'], selected))
        replaced = copy.deepcopy(selected); replaced['historyEntryKey'] = before['historyEntryKey']
        replacement_driver = Driver()
        with self.assertRaisesRegex(RuntimeError, 'replaced'):
            MODULE.relation_history_checks(replacement_driver, {}, lambda: None, before, replaced)
        self.assertEqual(replacement_driver.actions, [], 'replaceState fails before navigation')
        driver, record, saved = Driver(), {}, []
        failure = TimeoutError('wrong browser entry')
        with patch.object(MODULE, 'wait_for', side_effect=failure):
            with self.assertRaises(TimeoutError) as caught:
                MODULE.relation_history_checks(driver, record, lambda: saved.append(copy.deepcopy(record)), before, selected)
        self.assertIs(caught.exception, failure)
        self.assertEqual(saved[-1]['transitions'][0]['before'], selected)
        self.assertEqual(saved[-1]['transitions'][0]['after'], back)
        self.assertEqual(driver.actions, [('POST', '/back', {})])

    def test_relation_history_wait_checks_native_key_revision_relation_and_all_route_fields(self):
        script = r"""
const assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const route={nav:'1',tree:'l',node:'root',scope:'task:category-objectnav',bench:null,protocol:null,paper:null,version:null,claim:null,mode:'tree',template:null};
let state={route,revision:2},key='native-key',relation='methods:relation:90',focus='np-task-relation-title',ready='ready';
globalThis.window={get navigation(){return {currentEntry:{key}}}};
globalThis.NavigationProductApp={getState:()=>state,getBundle:()=>({positions:{root:{entityId:'r'}}}),getContent:()=>({ready:()=>true})};
globalThis.document={querySelector:s=>s==='[data-task-route-scope]'?{dataset:{taskRouteState:'ready'}}:s==='[data-selected-task-relation]'?(relation?{dataset:{selectedTaskRelation:relation}}:null):s==='[data-relation-state]'?{dataset:{relationState:ready}}:null,get activeElement(){return {id:focus}}};
const predicate=new Function(input.script),expected={route,runtime:{revision:2},historyEntryKey:key,selectedRelation:relation};
assert.equal(predicate({...route},focus,expected),true);
for(const wrong of [null,'','old-key']){key=wrong;assert.equal(predicate(route,focus,expected),false);}key=expected.historyEntryKey;
state.revision=1;assert.equal(predicate(route,focus,expected),false);state.revision=2;
relation=null;assert.equal(predicate(route,focus,expected),false);relation=expected.selectedRelation;
ready='loading';assert.equal(predicate(route,focus,expected),false);ready='ready';
for(const field of Object.keys(route)){assert.equal(predicate({...route,[field]:'changed'},focus,expected),false,field);const missing={...route};delete missing[field];assert.equal(predicate(missing,focus,expected),false,field+' missing');}
focus='wrong';assert.equal(predicate(route,'np-task-relation-title',expected),false);
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_RELATION_HISTORY_WAIT_JS}), capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_real_jsdom_push_and_replace_history_restore_different_predecessors(self):
        # Actual JSDOM history traversal is a state-control test. It has no native
        # Navigation API key support and is not evidence of Chrome geometry/keys.
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
(async()=>{for(const operation of ['pushState','replaceState']){const dom=new JSDOM('',{url:'https://example.org/task'}),w=dom.window;
try{const route={scope:'task:category-objectnav',tree:'l',node:'root',paper:null,version:null,claim:null,bench:null,protocol:null,template:null,mode:'tree',nav:'1'};
const before={route,revision:1,selectedRelation:null},selected={route,revision:2,selectedRelation:'methods:relation:90'};
w.history.replaceState({route:{scope:'scope:all'},revision:0},'');w.history.pushState(before,'');w.history[operation](selected,'');
async function traverse(direction){const done=new Promise((resolve,reject)=>{const timer=setTimeout(()=>reject(Error('history timeout')),1000);w.addEventListener('popstate',()=>{clearTimeout(timer);resolve(w.history.state)},{once:true});});w.history[direction]();return done;}
const back=await traverse('back');if(operation==='pushState')assert.deepEqual(back,before);else assert.notDeepEqual(back,before,'replaceState must not retain the overwritten task entry');
assert.deepEqual(await traverse('forward'),selected);
}finally{dom.window.close();}}})().catch(e=>{console.error(e);process.exitCode=1;});
"""
        result = subprocess.run(['node', '-e', script], cwd=Path(__file__).parents[1], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ColdGeometryDiagnosticChecks(unittest.TestCase):
    def test_probe_captures_real_generated_inline_controller_frames_without_source_url(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
assert.ok([...d.scripts].some(s=>s.textContent.includes('function selectTaskRelation(')), 'the actual generator embeds the controller inline');
assert.ok(![...d.scripts].some(s=>/sourceURL=.*navigation-product/.test(s.textContent)), 'do not add a fake sourceURL to production');
w.eval(input.probe);await scope('task:category-objectnav');await select(e.poni.id);
const report=new w.Function(input.stop)(),frames=report.events.filter(e=>e.kind==='tree-scrollTop-before').flatMap(e=>e.stack);
assert.ok(frames.some(s=>s.includes('/research/navigation/:')),JSON.stringify(frames));
assert.ok(frames.every(s=>!s.includes('https:')&&!s.includes('example.org')&&!s.includes('?')&&!s.includes('#')));
assert.equal(Object.values(report.cleanup).every(Boolean),true);states.push(report);
"""
        reports = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science),
                                                          'probe': MODULE.COLD_GEOMETRY_PROBE_JS, 'stop': MODULE.COLD_GEOMETRY_STOP_JS})
        self.assertTrue(reports[0]['capabilities']['scrollTop'])

    def test_cleanup_integrity_detects_dom_history_changes_without_exporting_live_state(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
for(const mode of ['dom-history','window-only']){const dom=new JSDOM('<main id="navigation-product"><div id="np-tree-scroll"></div><div id="np-detail-scroll"></div></main>',{url:'https://example.org/research/navigation/',runScripts:'outside-only'});
try{const w=dom.window,d=w.document;w.TextEncoder=TextEncoder;w.requestAnimationFrame=()=>1;w.cancelAnimationFrame=()=>{};
w.Element.prototype.scrollIntoView=function(){};w.history.replaceState({testOnlyPrivateMarker:'DO_NOT_EXPORT_LIVE_STATE'},'');
const originalDefine=w.Object.defineProperty,originalFocus=w.HTMLElement.prototype.focus;w.eval(input.probe);
w.Object.defineProperty=function(target,key,descriptor){const result=originalDefine.call(this,target,key,descriptor);if(key==='focus'&&descriptor.value===originalFocus){if(mode==='window-only')originalDefine.call(w.Object,w,'scrollY',{value:42,configurable:true});else{d.getElementById('navigation-product').appendChild(d.createElement('i'));w.history.replaceState({changed:true},'');}}return result;};
const report=new w.Function(input.stop)();assert.equal(report.cleanup.descriptors,true);assert.equal(report.cleanup.domUnchanged,mode==='window-only');assert.equal(report.cleanup.liveStateUnchanged,mode==='window-only');assert.equal(report.cleanup.scrollUnchanged,mode!=='window-only');
assert.ok(!JSON.stringify(report).includes('DO_NOT_EXPORT_LIVE_STATE'));assert.equal(w.__captureColdGeometryProbe,undefined);
}finally{dom.window.close();}}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'probe': MODULE.COLD_GEOMETRY_PROBE_JS, 'stop': MODULE.COLD_GEOMETRY_STOP_JS}),
                                cwd=Path(__file__).parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_uninstrumented_refresh_uses_original_baseline_and_cannot_hide_native_failure(self):
        import copy
        expected = ExplorationCaptureChecks().restore_fixture()
        cleanup_keys = ('descriptors', 'observer', 'listener', 'raf', 'container', 'integrityObserver',
                        'liveStateUnchanged', 'domUnchanged', 'focusUnchanged', 'scrollUnchanged')
        for failure in (None, 'observed-scroll', 'native-scroll', 'native-wait', 'native-wait-and-save', 'cleanup', 'probe-remains', 'remove'):
            events, saved, record = [], [], {}
            original = TimeoutError('original native wait failure')
            class Driver:
                def __init__(self): self.refreshes = 0; self.probe = False; self.state = copy.deepcopy(expected)
                def cdp(self, command, params):
                    events.append(command)
                    if command == 'Page.addScriptToEvaluateOnNewDocument': return {'identifier': 'only-one-probe'}
                    if failure == 'remove': raise RuntimeError('script removal failed')
                    return {}
                def call(self, method, path, body):
                    self.refreshes += 1; events.append(path)
                    if self.refreshes == 1: self.probe = True
                    self.state = copy.deepcopy(expected)
                    if (failure == 'observed-scroll' and self.refreshes == 1) or (failure == 'native-scroll' and self.refreshes == 2): self.state['treeScroll']['top'] += 5
                def settle(self): pass
                def js(self, script, *args):
                    if script == MODULE.COLD_GEOMETRY_STOP_JS:
                        self.probe = failure == 'probe-remains'; events.append('cleanup')
                        return {'cleanup': {k: not (failure == 'cleanup' and k == 'domUnchanged') for k in cleanup_keys}}
                    if script == MODULE.COLD_GEOMETRY_ABSENT_JS: return not self.probe
                    if script == MODULE.TASK_ROUTE_SNAPSHOT_JS: return copy.deepcopy(self.state)
                    return {'origin': 'diagnostic'}
            driver = Driver()
            ready = lambda: True
            def wait(predicate):
                self.assertIs(predicate, ready)
                if driver.refreshes == 2 and failure in ('native-wait', 'native-wait-and-save'): raise original
                return predicate()
            def save():
                saved.append(copy.deepcopy(record))
                if failure == 'native-wait-and-save' and len(record.get('transitions', [])) == 2 and 'after' in record['transitions'][-1]: raise RuntimeError('secondary save failure')
            with self.subTest(failure=failure), patch.object(MODULE, 'wait_for', side_effect=wait):
                if failure:
                    with self.assertRaises((RuntimeError, TimeoutError)) as caught:
                        MODULE.cold_relation_refresh_comparison(driver, record, save, expected, ready)
                    if failure in ('native-wait', 'native-wait-and-save'): self.assertIs(caught.exception, original)
                else:
                    result = MODULE.cold_relation_refresh_comparison(driver, record, save, expected, ready)
                    self.assertEqual(result['kind'], 'cold-selected-relation-uninstrumented')
                    self.assertEqual(result['after'], expected)
            self.assertEqual(events.count('Page.addScriptToEvaluateOnNewDocument'), 1)
            self.assertEqual(events.count('Page.removeScriptToEvaluateOnNewDocument'), 1)
            second_expected = failure in (None, 'native-scroll', 'native-wait', 'native-wait-and-save')
            self.assertEqual(driver.refreshes, 2 if second_expected else 1)
            if second_expected:
                self.assertLess(events.index('Page.removeScriptToEvaluateOnNewDocument'), len(events) - 1)
                self.assertEqual(saved[-1]['transitions'][-1]['kind'], 'cold-selected-relation-uninstrumented')
                self.assertIn('before', saved[-1]['transitions'][-1]); self.assertIn('after', saved[-1]['transitions'][-1])
                self.assertEqual(saved[-1]['coldGeometryDiagnostic']['nativeComparisonClearance'], {'currentProbeAbsent': True, 'futureScriptRemoved': True})

    def test_early_probe_preserves_native_calls_bounds_data_and_restores_current_document(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
(async()=>{for(const overflow of [false,true]){const dom=new JSDOM('<main id="navigation-product"><div id="np-tree-scroll"><div id="np-task-route-canvas"></div><div id="np-tree"><li id="node" aria-selected="true" data-position="root"></li></div></div><aside id="np-detail-scroll"><div id="np-reader-summary"></div></aside><button id="focus-target"></button><input value="DO_NOT_READ_PRIVATE_VALUE"></main><div id="outside"></div>',{url:'https://example.org/',runScripts:'outside-only'});
try{const w=dom.window,d=w.document;w.TextEncoder=TextEncoder;
let next=0,frames=new Map(),nativeCalls=[],tops=new WeakMap(),sentinel=new Error('native sentinel');
w.requestAnimationFrame=fn=>{frames.set(++next,fn);return next;};w.cancelAnimationFrame=id=>frames.delete(id);
const proto=w.Element.prototype,originalDescriptor=Object.getOwnPropertyDescriptor(proto,'scrollTop');
const getter=function(){return tops.get(this)||0;},setter=function(value){nativeCalls.push({kind:'set',target:this,value});if(value===-999)throw sentinel;tops.set(this,value);};
Object.defineProperty(proto,'scrollTop',{...originalDescriptor,get:getter,set:setter});
const focus=function(){nativeCalls.push({kind:'focus',target:this,args:[...arguments]});if(arguments[0]==='throw')throw sentinel;return 'focus-result';};
const into=function(){nativeCalls.push({kind:'into',target:this,args:[...arguments]});if(arguments[0]==='throw')throw sentinel;return 'into-result';};
Object.defineProperty(w.HTMLElement.prototype,'focus',{value:focus,writable:true,configurable:true});Object.defineProperty(proto,'scrollIntoView',{value:into,writable:true,configurable:true});
const originalFocus=Object.getOwnPropertyDescriptor(w.HTMLElement.prototype,'focus'),originalInto=Object.getOwnPropertyDescriptor(proto,'scrollIntoView'),tree=d.getElementById('np-tree-scroll'),button=d.getElementById('focus-target');
w.eval(input.probe);
assert.equal(Object.getOwnPropertyDescriptor(proto,'scrollTop').get,getter,'original getter remains untouched');
const options={get preventScroll(){throw Error('diagnostic must not inspect call options');}};
assert.equal(button.focus(options),'focus-result');assert.equal(nativeCalls.at(-1).args[0],options);assert.equal(nativeCalls.at(-1).target,button);
assert.equal(button.scrollIntoView(options),'into-result');assert.equal(nativeCalls.at(-1).args[0],options);
for(const action of [()=>button.focus('throw'),()=>button.scrollIntoView('throw'),()=>{tree.scrollTop=-999;}])assert.throws(action,e=>e===sentinel,'the original exception identity is preserved');
w.eval('document.getElementById("np-tree-scroll").scrollTop=534;\n//# sourceURL=https://example.org/assets/navigation-product.js');assert.equal(tree.scrollTop,534);
const relation=d.createElement('section');relation.dataset.selectedTaskRelation='methods:relation:90';d.getElementById('np-reader-summary').appendChild(relation);await Promise.resolve();
tree.dispatchEvent(new w.Event('scroll',{bubbles:false}));
if(frames.size){const [id,fn]=frames.entries().next().value;frames.delete(id);fn(123.5);}
if(overflow)for(let i=0;i<300;i++)tree.scrollTop=i;
const result=new w.Function(input.stop)();assert.equal(w.__captureColdGeometryProbe,undefined);assert.equal(frames.size,0);
assert.equal(Object.getOwnPropertyDescriptor(proto,'scrollTop').get,getter);assert.equal(Object.getOwnPropertyDescriptor(proto,'scrollTop').set,setter);
assert.deepEqual(Object.getOwnPropertyDescriptor(w.HTMLElement.prototype,'focus'),originalFocus);assert.deepEqual(Object.getOwnPropertyDescriptor(proto,'scrollIntoView'),originalInto);
assert.equal(Object.values(result.cleanup).every(Boolean),true);assert.equal(result.privateEpoch.available,false);
assert.ok(result.events.length<=result.limits.events);assert.ok(result.eventBytes<=result.limits.bytes);assert.equal(result.truncated,overflow);
assert.ok(result.events.some(e=>e.kind==='tree-scrollTop-before'&&e.value===534&&e.stack.some(s=>s.includes('/assets/navigation-product.js'))));
assert.ok(result.events.some(e=>e.kind==='tree-scrollTop-after'&&e.geometry.tree.top===534));
assert.ok(result.events.some(e=>e.kind==='ui-dom-observed'&&e.preMeaning.includes('not synchronous')));
assert.ok(result.events.some(e=>e.kind==='scroll-event'));assert.ok(result.events.some(e=>e.kind==='animation-frame'&&e.frameTime===123.5));
assert.ok(!JSON.stringify(result).includes('DO_NOT_READ_PRIVATE_VALUE'));assert.ok(result.limitations.some(x=>x.includes('force layout')));
const frozen=JSON.stringify(result);tree.scrollTop=10;button.focus();relation.remove();tree.dispatchEvent(new w.Event('scroll'));await Promise.resolve();assert.equal(JSON.stringify(result),frozen,'current-document hooks and observer are gone');
}finally{dom.window.close();}}})().catch(error=>{console.error(error);process.exitCode=1;});
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'probe': MODULE.COLD_GEOMETRY_PROBE_JS, 'stop': MODULE.COLD_GEOMETRY_STOP_JS}),
                                cwd=Path(__file__).parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_probe_geometry_failure_cannot_change_native_return_or_exception(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<main id="navigation-product"><div id="np-tree-scroll"></div><button id="button"></button></main>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document;w.TextEncoder=TextEncoder;w.requestAnimationFrame=()=>{throw Error('probe frame failure');};w.cancelAnimationFrame=()=>{};
const button=d.getElementById('button'),tree=d.getElementById('np-tree-scroll'),sentinel=new Error('native failure');let calls=0;
w.HTMLElement.prototype.focus=function(value){calls++;if(value==='throw')throw sentinel;return 37;};w.Element.prototype.scrollIntoView=function(){return 41;};
tree.getBoundingClientRect=()=>{throw Error('geometry unavailable');};w.eval(input.probe);
assert.equal(button.focus('value'),37);assert.throws(()=>button.focus('throw'),e=>e===sentinel);assert.equal(calls,2);
const report=new w.Function(input.stop)();assert.ok(report.errors.length);assert.equal(Object.values(report.cleanup).every(Boolean),true);assert.equal(w.__captureColdGeometryProbe,undefined);
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'probe': MODULE.COLD_GEOMETRY_PROBE_JS, 'stop': MODULE.COLD_GEOMETRY_STOP_JS}),
                                cwd=Path(__file__).parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_cold_refresh_keeps_original_action_wait_and_cleans_on_every_failure(self):
        import copy
        for failure in (None, 'refresh', 'wait', 'stop', 'remove', 'cleanup', 'save', 'refresh-and-stop'):
            events, saved, record = [], [], {}
            original = RuntimeError('original refresh failure')
            class Driver:
                def cdp(self, command, params):
                    events.append((command, params))
                    if command == 'Page.addScriptToEvaluateOnNewDocument': return {'identifier': 'probe-1'}
                    if failure == 'remove': raise RuntimeError('remove failed')
                    return {}
                def call(self, method, path, data):
                    events.append((method, path, data))
                    if failure in ('refresh', 'refresh-and-stop'): raise original
                def settle(self): events.append(('settle',))
                def js(self, script, *args):
                    if script == MODULE.COLD_GEOMETRY_STOP_JS:
                        events.append(('stop-current-document',))
                        if failure in ('stop', 'refresh-and-stop'): raise RuntimeError('stop failed')
                        return {'cleanup': {k: not (failure == 'cleanup' and k == 'descriptors') for k in ('descriptors', 'observer', 'listener', 'raf', 'container', 'integrityObserver', 'liveStateUnchanged', 'domUnchanged', 'focusUnchanged', 'scrollUnchanged')}}
                    if script == MODULE.TASK_ROUTE_SNAPSHOT_JS: return {'snapshot': 'before-or-after'}
                    return {'origin': 'retained'}
            ready = lambda: True
            def wait(predicate):
                self.assertIs(predicate, ready)
                if failure == 'wait': raise original
                self.assertTrue(predicate())
            def save():
                saved.append(copy.deepcopy(record))
                if failure == 'save' and 'observation' in record.get('coldGeometryDiagnostic', {}): raise RuntimeError('save failed')
            with self.subTest(failure=failure), patch.object(MODULE, 'wait_for', side_effect=wait):
                if failure:
                    with self.assertRaises(RuntimeError) as caught:
                        MODULE.cold_relation_refresh(Driver(), record, save, ready)
                    if failure in ('refresh', 'wait', 'refresh-and-stop'): self.assertIs(caught.exception, original)
                else:
                    phase = MODULE.cold_relation_refresh(Driver(), record, save, ready)
                    self.assertEqual(phase['kind'], 'cold-selected-relation')
            self.assertEqual(events[0][0], 'Page.addScriptToEvaluateOnNewDocument')
            self.assertEqual(sum(x[:2] == ('POST', '/refresh') for x in events), 1)
            self.assertLess(events.index(('stop-current-document',)), next(i for i, x in enumerate(events) if x[0] == 'Page.removeScriptToEvaluateOnNewDocument'))
            self.assertIn('after', saved[-1]['transitions'][0])
            self.assertTrue(saved[-1]['coldGeometryDiagnostic']['instrumented'])



if __name__ == '__main__':
    unittest.main()
