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


def separate_disclosure_save_sites(case, tree):
    """Prove only the additive audit's exact checkpoints before testing old counts."""
    import ast
    helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'disclosure_bounds_checks')
    def count(node):
        return len([n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save'])
    nested = {n.name: count(n) for n in helper.body if isinstance(n, ast.FunctionDef)}
    case.assertEqual(nested, {'snapshot': 0, 'action': 3, 'key': 0, 'wheel_to': 0, 'proof': 1})
    case.assertEqual(count(helper), 9)
    case.assertEqual(count(helper) - sum(nested.values()), 5)
    tree.body.remove(helper)


def chrome_text_fixture(text, font, area, foreground, background):
    import copy
    fragment = dict(area, visible=True)
    return dict(text=text, renderedText=text, rect=copy.deepcopy(area), visible=True, opaque=True, unscaled=True, clipped=False,
                fontSize=font, foreground=foreground, background=background, clipAreas=[], fragments=[fragment],
                textRuns=[dict(text=text, fontSize=font, foreground=foreground, background=background, opaque=True, unscaled=True,
                               clipAreas=[], fragments=[copy.deepcopy(fragment)])])


def desktop_chrome_fixture(width=1440, height=900, top=132, bottom_padding=16, route=None, home=False):
    """Independent synthetic DOM frames, not an assertion of browser pixels."""
    import copy
    def frame(selector, x, y, w, h, **values):
        area = dict(x=x, y=y, width=w, height=h)
        return dict(selector=selector, count=1, rect=area, clientRect=copy.deepcopy(area),
                    position='relative', display='block', opaque=True, unscaled=True, top=0, left=0,
                    marginTop=0, marginBottom=0, marginLeft=0, marginRight=0, paddingTop=0, paddingBottom=0, paddingLeft=0, paddingRight=0, rowGap=0) | values
    result = dict(layoutWidth=width, rootClientWidth=width, rootRect=dict(x=0, y=0, width=width, height=height), rootGutter='stable', topology=True,
                body=frame('body', 0, 0, width, height),
                header=frame('.site-header', 0, 0, width, 32),
                app=frame('#navigation-product', 0, 32, width, height - 32, paddingLeft=16, paddingRight=16, paddingBottom=bottom_padding),
                start=frame('#navigation-product > .np-global-start', 16, 32, width - 32, 24),
                workspace=frame('#np-workspace', 16, 56, width - 32, height - 56 - bottom_padding),
                identity=frame('#np-selection-context', 16, 56, width - 32, 20),
                bar=frame('#np-workspace > .np-workspace-bar', 16, 76, width - 32, top - 76))
    route = route if route is not None else dict(tree='l')
    texts = [('当前任务', '原始阅读范围'), ('当前路线', '原始路线'), ('当前论文', '尚未选择'), ('来源版本', '尚未选择')]
    result['identitySource'] = dict(route=route, scopeId='original-scope', routePositionId=None, atRoot=home, fields=texts)
    if route.get('tree') == 'g' and route.get('node'):
        import sys
        with patch.object(sys, 'path', [str(Path(__file__).parents[1] / 'scripts'), *sys.path]):
            from navigation_research_map import build_research_map
            graph = build_research_map(S0FooterCaptureChecks.source())
        path = []; position = graph['positions'][route['node']]
        while position:
            path.insert(0, {key: position.get(key) for key in ('id', 'parentId', 'entityId', 'tree', 'scopeId')})
            position = graph['positions'].get(position.get('parentId'))
        result['identitySource'].update(tabSourceSha256=graph['sourceModelSha256'], tabPath=path)

    result['identityFields'] = [dict(tag='DIV', className='np-context-field', children=['DT', 'DD'],
        label=chrome_text_fixture(label, 11, dict(x=20+i*330, y=58, width=100, height=14), [98,107,103], [250,250,248]),
        value=chrome_text_fixture(value, 13, dict(x=125+i*330, y=58, width=150, height=17), [23,26,25], [250,250,248])) for i,(label,value) in enumerate(texts)]
    result['controls'] = []
    for i,(selector,tag,identity,tree,text,font) in enumerate(MODULE.WORKSPACE_CONTROL_SPECS):
        hidden = selector=='#np-overview-toggle' and not home
        fg, bg = [23,26,25], [255,255,255]
        if tree: fg,bg=([49,92,75],[255,255,255]) if tree==route['tree'] else ([107,122,130],[237,241,236])
        elif selector=='#np-overview-toggle': fg,bg=[49,92,75],[250,250,248]
        elif selector=='#np-reading-tools > summary': bg=[250,250,248]
        proof=chrome_text_fixture(text or ('原全局树图' if home else '回到差异概览'),font,dict(x=20+i*160,y=78,width=155,height=18),fg,bg)
        proof.update(opaque=not hidden,visible=not hidden)
        result['controls'].append(dict(selector=selector,count=1,tag=tag,id=identity,tree=tree,hidden=hidden,disabled=False,hover=False,
                                       selected=str(tree==route['tree']).lower() if tree else None,proof=proof))
    return result


def run_product_capture_script(owner, body, extra):
    """Production desktop DOM contract (1440px default); does not claim layout.

    Explicit viewport fixtures override this. Compact pane behavior is exercised
    by test_navigation_workspace.cjs rather than hidden desktop controls.
    """
    import tempfile
    root = Path(__file__).parents[1]
    with tempfile.TemporaryDirectory(prefix='.navigation-capture-test-', dir=root) as tmp:
        build = subprocess.run(['python3', '-c', "import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;p.write_preview(Path('.').resolve(),Path(sys.argv[1]))", tmp], cwd=root, capture_output=True, text=True)
        owner.assertEqual(build.returncode, 0, build.stdout + build.stderr)
        script = r"""
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto'),assert=require('node:assert/strict'),{JSDOM,ResourceLoader,VirtualConsole}=require('jsdom');
const input=JSON.parse(fs.readFileSync(0,'utf8')),output=path.join(input.temp,'research/navigation'),errors=[];
class Resources extends ResourceLoader{fetch(url){const parsed=new URL(url),name=path.basename(parsed.pathname),allowed=new Set(['site.css','catalog-navigation.js','presentation.js','interface.js','chrome.js']);assert.equal(parsed.origin,'https://example.org');assert.equal(parsed.pathname,'/assets/'+name);if(!allowed.has(name))throw Error('Unexpected external navigation dependency '+url);return Promise.resolve(fs.readFileSync(path.join(process.cwd(),'assets',name)));}}
const vc=new VirtualConsole();vc.on('jsdomError',e=>errors.push(e.message));
const dom=new JSDOM(fs.readFileSync(path.join(output,'index.html'),'utf8'),{url:'https://example.org/research/navigation/',runScripts:'dangerously',pretendToBeVisual:true,resources:new Resources(),virtualConsole:vc,beforeParse(w){w.innerWidth=1440;w.innerHeight=900;w.matchMedia=query=>({media:query,get matches(){const limit=query.match(/\((min|max)-width:\s*(\d+)px\)/);return limit?(limit[1]==='min'?w.innerWidth>=+limit[2]:w.innerWidth<=+limit[2]):false;},addListener(){},removeListener(){},addEventListener(){},removeEventListener(){}});if(input.viewport){Object.defineProperty(w,'innerWidth',{value:input.viewport.width,configurable:true});Object.defineProperty(w,'innerHeight',{value:input.viewport.height,configurable:true});}w.TextEncoder=TextEncoder;w.TextDecoder=TextDecoder;w.scrollTo=(x,y)=>Object.defineProperty(w,'scrollY',{value:y,configurable:true});w.HTMLElement.prototype.scrollIntoView=function(){};Object.defineProperty(w.crypto,'subtle',{value:crypto.webcrypto.subtle});w.fetch=url=>Promise.resolve({ok:true,arrayBuffer:async()=>fs.readFileSync(path.join(output,url))});}});
(async()=>{const w=dom.window,d=w.document,wait=ms=>new Promise(r=>setTimeout(r,ms));
async function ready(check){for(let i=0;i<250&&!check();i++)await wait(10);assert.ok(check(),JSON.stringify({errors,loadState:d.getElementById('navigation-product')?.dataset.loadState,message:d.getElementById('np-loading')?.textContent}));await new Promise(r=>w.requestAnimationFrame(()=>w.requestAnimationFrame(r)));}
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
    def capture_bounds_fixture(self, mutation=''):
        """Execute the exact capture snapshot in JSDOM; rectangles are test fixtures."""
        import ast
        source = ast.parse((Path(__file__).parents[1] / 'scripts/navigation_screenshots.py').read_text())
        main = next(n for n in source.body if isinstance(n, ast.FunctionDef) and n.name == 'main')
        capture = next(n for n in main.body if isinstance(n, ast.FunctionDef) and n.name == 'capture')
        snapshot = next(n for n in capture.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'data' for t in n.targets)).value
        self.assertEqual(snapshot.func.attr, 'js')
        self.assertEqual(snapshot.args[1].id, 'CAPTURE_BOUNDS_SELECTOR')
        gates = [n for n in ast.walk(capture) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'check_capture_visible_regions']
        self.assertEqual(len(gates), 1)
        self.assertEqual([a.id for a in gates[0].args], ['data', 'require_tree', 'require_home'])
        driver = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict');
const input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<main id="np-workspace"><div id="np-tree-scroll"><ul id="np-tree"><li data-position="actual-tree-position"><div class="np-node-row">Actual tree label</div></li></ul></div><aside class="np-reading-pane"><header id="np-reader-heading"><h2>Fixed identity</h2></header><div id="np-detail-scroll"><div id="np-reader-summary">Actual reader summary</div><div class="np-detail-scroll">Nested evidence</div></div></aside></main>',{runScripts:'outside-only'});
try {
 const w=dom.window,d=w.document;
 Object.defineProperty(w,'innerWidth',{value:1440});Object.defineProperty(w,'innerHeight',{value:900});Object.defineProperty(w,'devicePixelRatio',{value:1});
 Object.defineProperty(d,'fonts',{value:{status:'loaded'}});
 w.HTMLElement.prototype.getBoundingClientRect=function(){return this.id==='np-detail-scroll'?{x:801,y:319.296875,width:622,height:563.703125}:{x:800,y:132,width:624,height:752};};
 const reader=d.getElementById('np-detail-scroll'),wrapper=reader.parentElement;
 assert.ok(wrapper.matches('.np-reading-pane'));assert.equal(wrapper.id,'');assert.notEqual(reader,wrapper);
 if(input.mutation==='missing-id')reader.removeAttribute('id');
 if(input.mutation==='detached-reader')reader.remove();
 if(input.mutation==='renamed-id')reader.id='np-reader-body';
 const snapshot=new w.Function(input.snapshot);
 const current=snapshot.call(w,input.selector),legacy=snapshot.call(w,input.selector.replace(',#np-detail-scroll',''));
 assert.ok(current.bounds.some(r=>r.id===''),'wrapper diagnostics are still collected');
 assert.ok(!legacy.bounds.some(r=>r.id==='np-detail-scroll'),'legacy wrapper selector omits the moved inner reader');
 process.stdout.write(JSON.stringify({current,legacy}));
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', driver], input=json.dumps({'selector': MODULE.CAPTURE_BOUNDS_SELECTOR, 'snapshot': snapshot.args[0].value, 'mutation': mutation}), text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return json.loads(result.stdout)

    def test_capture_bounds_collects_real_inner_reader_and_preserves_wrapper_diagnostics(self):
        data = self.capture_bounds_fixture()
        readers = [r for r in data['current']['bounds'] if r['id'] == 'np-detail-scroll']
        self.assertEqual(len(readers), 1)
        self.assertEqual({k: readers[0][k] for k in ('x', 'y', 'width', 'height')}, {'x': 801, 'y': 319.296875, 'width': 622, 'height': 563.703125})
        MODULE.check_capture_visible_regions(data['current'], require_tree=False)
        with self.assertRaisesRegex(RuntimeError, 'Reader is not visible'):
            MODULE.check_capture_visible_regions(data['legacy'], require_tree=False)

    def test_capture_bounds_visible_wrapper_cannot_replace_missing_or_detached_reader(self):
        for mutation in ('missing-id', 'detached-reader', 'renamed-id'):
            with self.subTest(mutation=mutation):
                data = self.capture_bounds_fixture(mutation)['current']
                self.assertTrue(any(r['id'] == '' and r['width'] > 0 and r['height'] > 0 for r in data['bounds']))
                self.assertFalse(any(r['id'] == 'np-detail-scroll' for r in data['bounds']))
                with self.assertRaisesRegex(RuntimeError, 'Reader is not visible'):
                    MODULE.check_capture_visible_regions(data, require_tree=False)

    def test_capture_bounds_preserves_reader_geometry_and_tree_identity_negatives(self):
        import copy
        box = {'id': 'np-detail-scroll', 'x': 801, 'y': 319, 'width': 622, 'height': 564}
        wrapper = {'id': '', 'x': 800, 'y': 132, 'width': 624, 'height': 752}
        data = {'viewport': {'width': 1440, 'height': 900}, 'bounds': [wrapper, box]}
        MODULE.check_capture_visible_regions(data, require_tree=False)
        for mutation in ({'width': 0}, {'height': 0}, {'x': 1440}, {'y': 900}, {'x': -622}, {'y': -564}, {'id': ''}):
            broken = copy.deepcopy(data); broken['bounds'][1].update(mutation)
            with self.subTest(mutation=mutation), self.assertRaisesRegex(RuntimeError, 'Reader is not visible'):
                MODULE.check_capture_visible_regions(broken, require_tree=False)
        with self.assertRaisesRegex(RuntimeError, 'No actual tree node visible'):
            MODULE.check_capture_visible_regions(data)
        tree = dict(box, id='', position='actual-tree-position')
        data['bounds'].append(tree)
        MODULE.check_capture_visible_regions(data)
        tree['height'] = 0
        with self.assertRaisesRegex(RuntimeError, 'No actual tree node visible'):
            MODULE.check_capture_visible_regions(data)
        # Home never depended on the hidden tree/reader bounds; its own map gates remain.
        MODULE.check_capture_visible_regions({'viewport': data['viewport'], 'bounds': []}, require_home=True)

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
        data = {'relationsVisible':'false','selectedRelation':None,'relationControls':[r[0] for r in relations],'mapVisible':True,'viewport':{'x':0,'y':0,'width':1440,'height':900},'map':{'x':0,'y':0,'width':1440,'height':900},
                'directoryTitle':copy.deepcopy(box),'tasks':[{'scope':'s'+str(i),'expectedScope':'s'+str(i),'position':'p'+str(i),'expectedPosition':'p'+str(i)} for i in range(22)],'expectedIds':ids,'expectedEdges':edges,'expectedChallengeLabels':{'e'+str(i):'question' for i in range(13)},'expectedRelations':relations,
                'nodes':[dict(copy.deepcopy(box),id=x) for x in ids],
                'edges':[{'parent':a,'child':b,'visible':True,'length':25,'endpointsMatch':True,'inBounds':True,'uncovered':True,'foreground':[50,90,100],'background':[255,255,255]} for a,b in edges],
                'challenges':[{'entity':'e'+str(i),'expectedEntity':'e'+str(i),'position':'p'+str(i),'challengeOpen':'p'+str(i),'label':copy.deepcopy(box),'title':'Original question','expectedTitle':'Original question','aria':'Original question; open'} for i in range(13)],
                'relations':[{'id':i,'from':a,'to':b,'type':t,'visible':False,'length':25,'endpointsMatch':True,'inBounds':True,'uncovered':True,'foreground':[50,90,100],'background':[255,255,255],'ownHits':[{'x':10,'y':10}]} for i,a,b,t in relations]}
        MODULE.check_graphical_map(data)
        all_lines = copy.deepcopy(data); all_lines['relationsVisible'] = 'true'
        for edge in all_lines['relations']: edge['visible'] = True
        MODULE.check_graphical_map(all_lines)
        single = copy.deepcopy(data); single['selectedRelation'] = single['relations'][2]['id']; single['relations'][2]['visible'] = True
        MODULE.check_graphical_map(single)
        for value in (all_lines, single):
            bad = copy.deepcopy(value); next(e for e in bad['relations'] if e['visible'])['visible'] = False
            with self.assertRaises(RuntimeError): MODULE.check_graphical_map(bad)
            for mutation in (dict(ownHits=[]), dict(uncovered=False), dict(inBounds=False), dict(endpointsMatch=False),
                             dict(length=0), dict(length=float('nan')), dict(foreground=[250,250,250]),
                             dict(type='invented'), dict(to='wrong-target')):
                bad = copy.deepcopy(value); next(e for e in bad['relations'] if e['visible']).update(mutation)
                with self.assertRaises(RuntimeError): MODULE.check_graphical_map(bad)
        mutations = [lambda x:x['relationControls'].pop(),lambda x:x.update(selectedRelation='invented'),lambda x:x.__setitem__('mapVisible',False),lambda x:x['nodes'].pop(),
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
                     lambda x:x['relations'][0].__setitem__('visible',True)]
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
        # Full text-run and actual panel-client geometry supplement the old box gate.
        for kind, proof in zip(('heading', 'locator', 'source', 'status'), data['visibleProofs']):
            proof.update(S0FooterCaptureChecks.proof('原文来源 · s' if kind == 'source' else ' · fixed' if kind == 'status' else 'Section 3', proof['rect']))
            proof.update(kind=kind, sourceRecord=data['sources'][0].copy() if kind in ('source', 'status') else None)
            if kind == 'source':
                proof.update(elementTag='A', accessibilitySuffix=dict(tag='SPAN', className='np-sr', text='（新标签页）'), accessibleText=proof['text'] + '（新标签页）')
            proof.update(panelId='np-overview-relation-panel', panelContains=True, relationId='r',
                         panelClientRect=dict(x=10, y=10, width=400, height=500))
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
            panel = data['panels'][0]
            panel.update(headingSelector='#np-tree-heading', headingTree=tree, headingInPane=True,
                         headingProof=MethodReadingCaptureChecks.proof('文献树' if tree == 'l' else '挑战–思路树', 20, 200, 350, 25),
                         expectedRootRecords=[dict(id=tree, entity='source-root', tree=tree, scope=data['scope'], label='Original task root')],
                         rootRecords=[dict(id=tree, entity='source-root', tree=tree, scope=data['scope'], proof=MethodReadingCaptureChecks.proof('Original task root', 30, 225, 350, 25))])
            MODULE.check_parallel_scope(data)
            mutations = [lambda x: x['panels'].pop(), lambda x: x['panels'].append(copy.deepcopy(x['panels'][0])),
                         lambda x: x['panels'][0].update(scope='task:category-objectnav'),
                         lambda x: x['panels'][0].update(roots=['wrong']), lambda x: x.update(treeCount=2),
                         lambda x: x.update(rovingCount=2), lambda x: x.update(inactiveItemCount=1),
                         lambda x: x.update(selectedTree='g'), lambda x: x['panels'][0].update(headingVisible=False),
                         lambda x: x['panels'][0].update(headingSelector='h3'), lambda x: x['panels'][0].update(headingTree='g'),
                         lambda x: x['panels'][0].update(headingInPane=False), lambda x: x['panels'][0]['headingProof'].update(fontSize=14),
                         lambda x: x['panels'][0]['headingProof'].update(renderedText='wrong tree'),
                         lambda x: x['panels'][0]['rootRecords'][0].update(entity='same-label-wrong-root'),
                         lambda x: x['panels'][0]['rootRecords'][0]['proof'].update(renderedText='different scope'),
                         lambda x: x['panels'][0]['rootRecords'][0]['proof'].update(visible=False),
                         lambda x: x['panels'][0]['rootRecords'][0]['proof'].update(clipped=True),
                         lambda x: x['panels'][0]['rootRecords'][0]['proof'].update(foreground=[230,230,230]),
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
                'labels': ['领域', '挑战–思路树'],
                'rows': [{'x': 20, 'y': 100, 'width': 300, 'height': 30}, {'x': 340, 'y': 100, 'width': 900, 'height': 30}],
                'viewport': {'x': 0, 'y': 0, 'width': 1440, 'height': 900},
                'buttons': [{'uncovered': True, 'clipped': False, 'row': {'x': 340, 'y': 100, 'width': 900, 'height': 30}, 'rect': {'x': 360, 'y': 101, 'width': 200, 'height': 25}}]}
        MODULE.check_context_path(data)
        mutations = [lambda x: x['localIds'].insert(0, 'literature'),
                     lambda x: x['localTrees'].__setitem__(0, 'g'),
                     lambda x: x.__setitem__('globalSeparators', 1),
                     lambda x: x['rows'][1].__setitem__('y', 134),
                     lambda x: x['buttons'][0].__setitem__('uncovered', False),
                     lambda x: x['buttons'][0].__setitem__('clipped', True),
                     lambda x: x['rows'][1].__setitem__('y', 950),
                     lambda x: x['buttons'][0]['row'].__setitem__('width', 10)]
        for mutate in mutations:
            bad = copy.deepcopy(data)
            mutate(bad)
            with self.assertRaises(RuntimeError):
                MODULE.check_context_path(bad)

    def test_desktop_context_disclosure_rejects_wrong_ancestry_labels_and_covered_text(self):
        import copy
        def rect(x, y, w, h): return dict(x=x, y=y, width=w, height=h)
        def proof(text, area):
            return dict(text=text, rect=area, visible=True, opaque=True, unscaled=True, clipped=False,
                        fontSize=15, foreground=[20, 30, 40], background=[255, 255, 255], fragments=[dict(area, visible=True)])
        def button(id, text, area):
            return dict(id=id, text=text, title=text, aria=text, proof=proof(text, area))
        viewport = rect(0, 0, 1440, 900)
        entry, summary, popover = rect(20, 50, 290, 30), rect(320, 51, 240, 28), rect(320, 90, 820, 140)
        data = dict(route=dict(tree='c', node='pos:c:6dcc2ce43c02d908266f20'),
                    expectedIds=['root-c', 'insight'], localIds=['root-c', 'insight'], localTrees=['c', 'c'],
                    expectedGlobalIds=['goal', 'scope'], globalIds=['goal', 'scope'], globalSeparators=0,
                    labels=['领域', '挑战–思路树'], viewport=viewport,
                    desktopDisclosure=dict(tag='DETAILS', open=True, summary=proof('挑战–思路树 · 原树路径', summary),
                      compactRows=[entry, summary], popover=popover, localLabel=proof('挑战–思路树', rect(334, 104, 120, 24)),
                      expectedLocalLabels=['完整原始任务', '完整原始问题'],
                      globalButtons=[button('goal', '领域', rect(22, 52, 45, 26)), button('scope', 'AudioGoal', rect(72, 52, 230, 26))],
                      localButtons=[button('root-c', '完整原始任务', rect(460, 104, 400, 28)), button('insight', '完整原始问题', rect(334, 145, 700, 48))]))
        MODULE.check_context_path(data)
        changes = [lambda d: d['localIds'].__setitem__(0, 'wrong'), lambda d: d['localTrees'].__setitem__(0, 'l'),
                   lambda d: d['desktopDisclosure']['localButtons'].reverse(),
                   lambda d: d['desktopDisclosure']['localButtons'][0].update(id='wrong'),
                   lambda d: d['desktopDisclosure']['localButtons'][0].update(text='简称'),
                   lambda d: d['desktopDisclosure']['localButtons'][0].update(aria='different'),
                   lambda d: d['desktopDisclosure']['localButtons'][0]['proof'].update(visible=False),
                   lambda d: d['desktopDisclosure']['localButtons'][1]['proof']['fragments'][0].update(visible=False),
                   lambda d: d['desktopDisclosure']['localButtons'][1]['proof'].update(clipped=True),
                   lambda d: d['desktopDisclosure']['localButtons'][1]['proof']['fragments'][0].update(width=1500),
                   lambda d: d['desktopDisclosure']['summary'].update(visible=False),
                   lambda d: d['desktopDisclosure']['globalButtons'][0]['proof'].update(visible=False),
                   lambda d: d['desktopDisclosure']['popover'].update(y=880),
                   lambda d: d['desktopDisclosure']['compactRows'][1].update(y=90)]
        for change in changes:
            bad = copy.deepcopy(data); change(bad)
            with self.assertRaises(RuntimeError): MODULE.check_context_path(bad)
        closed = copy.deepcopy(data); closed['desktopDisclosure']['open'] = False
        for item in closed['desktopDisclosure']['localButtons']:
            item['proof'].update(visible=False, fragments=[])
        MODULE.check_context_path(closed)
        closed['desktopDisclosure']['localButtons'][0]['proof']['fragments'] = [dict(rect(334, 104, 100, 28), visible=True)]
        with self.assertRaises(RuntimeError): MODULE.check_context_path(closed)

    def test_context_disclosure_transition_preserves_route_scroll_and_origin(self):
        import copy
        before = dict(open=False, route=dict(scope='audio', tree='c', node='source', paper='paper', version='version'),
                      originTrail=[dict(route=dict(scope='all'), bucket=dict(treeScrollByTree=dict(g=71)))], historyLength=3,
                      window=dict(x=0, y=0), treeScroll=dict(top=137, left=4), readerScroll=dict(top=211, left=0))
        opened = copy.deepcopy(before); opened['open'] = True
        MODULE.check_context_ancestry_transition(before, opened, True)
        closed = copy.deepcopy(opened); closed['open'] = False
        MODULE.check_context_ancestry_transition(opened, closed, False)
        MODULE.check_context_ancestry_transition(closed, opened, True)
        for change in (lambda d: d.update(open=False), lambda d: d['route'].update(node='wrong'),
                       lambda d: d['originTrail'].clear(), lambda d: d.update(historyLength=4),
                       lambda d: d['treeScroll'].update(top=0), lambda d: d['readerScroll'].update(top=0),
                       lambda d: d['window'].update(y=1)):
            bad = copy.deepcopy(opened); change(bad)
            with self.assertRaises(RuntimeError): MODULE.check_context_ancestry_transition(before, bad, True)

    def test_production_context_disclosure_uses_real_summary_and_full_source_path(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
const pid='pos:c:6dcc2ce43c02d908266f20',p=s.positions[pid];
a.navigate(m.routeForPosition(a.getBundle(),{scope:p.scopeId},pid),{cross:true,initialTree:true});await ready(()=>a.getState().route.node===pid&&a.getContent().ready(p.entityId));
const tree=d.getElementById('np-tree-scroll'),reader=d.getElementById('np-detail-scroll');tree.scrollTop=137;tree.scrollLeft=4;reader.scrollTop=211;
const stateRead=new w.Function(input.contextState),pathRead=new w.Function(input.contextPath),statesBefore=JSON.parse(JSON.stringify(stateRead()));
d.elementFromPoint=()=>null;w.Range.prototype.getClientRects=()=>[];
let detail=d.querySelector('#np-global-context .np-ancestry-disclosure');assert.equal(detail.open,false);
const first=pathRead();assert.deepEqual(first.localIds,first.expectedIds);assert.deepEqual(first.desktopDisclosure.localButtons.map(b=>b.text),first.expectedIds.map(id=>s.entities[s.positions[id].entityId].label));
assert.equal(first.desktopDisclosure.summary.text,'挑战–思路树 · 原树路径');
for(const open of [true,false,true,false]){d.querySelector(input.contextSummary).click();assert.equal(detail.open,open);const now=JSON.parse(JSON.stringify(stateRead()));for(const key of ['route','originTrail','historyLength','window','treeScroll','readerScroll'])assert.deepEqual(now[key],statesBefore[key],key);states.push(now);}
await scope('task:imagenav');const group=s.positions[e.image.find(p=>p.paperId==='zhu').parentId];await select(group.id);
detail=d.querySelector('#np-global-context .np-ancestry-disclosure');assert.equal(detail.open,false);d.querySelector(input.contextSummary).click();assert.equal(detail.open,true);
const root=e.scopes['task:imagenav'].roots[0],target=d.querySelector('[data-path-kind="local-ancestry"] [data-context-position="'+root+'"]');assert.ok(target);assert.equal(target.closest('details:not([open])'),null);target.click();await ready(()=>a.getState().route.node===root);assert.equal(a.getState().route.node,root);
"""
        result = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science),
            'contextState': MODULE.CONTEXT_ANCESTRY_STATE_JS, 'contextPath': MODULE.CONTEXT_PATH_SNAPSHOT_JS,
            'contextSummary': MODULE.CONTEXT_ANCESTRY_SUMMARY_SELECTOR})
        self.assertEqual([item['open'] for item in result], [True, False, True, False])

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
        self.assertEqual(len(MODULE.SCENE_NAMES), 53)
        self.assertEqual(len(set(MODULE.SCENE_NAMES)), 53)

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


class RelationPathSamplingChecks(unittest.TestCase):
    """Execute the production probe with deterministic SVG geometry/hit stacks.

    These are counterexamples to the sampler, not substituted Chrome evidence.
    Real browser captures remain the PR job's responsibility.
    """

    def probe(self, **case):
        driver = r"""
const {JSDOM}=require('jsdom'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<div id="map"><svg><path id="edge" data-map-relation="tasks:relation:90" data-from-entity="from" data-to-entity="to"></path></svg></div>');
const d=dom.window.document,m=d.getElementById('map'),svg=m.querySelector('svg'),e=d.getElementById('edge'),c=input.case;
const identity={a:1,b:0,c:0,d:1,e:0,f:0},matrix=c.matrix||identity;matrix.inverse=()=>{const det=matrix.a*matrix.d-matrix.b*matrix.c;return {a:matrix.d/det,b:-matrix.b/det,c:-matrix.c/det,d:matrix.a/det,e:(matrix.c*matrix.f-matrix.d*matrix.e)/det,f:(matrix.b*matrix.e-matrix.a*matrix.f)/det};};
global.DOMPoint=class{constructor(x,y){this.x=x;this.y=y;}matrixTransform(a){return {x:this.x*a.a+this.y*a.c+a.e,y:this.x*a.b+this.y*a.d+a.f};}};
global.innerWidth=1440;global.innerHeight=900;global.document=d;
global.rect=n=>n.area||{x:0,y:0,width:1440,height:900};
global.color=()=>({rgb:[60,131,125],alpha:1});global.bg=()=>[255,255,255];
const style={opacity:'1',strokeOpacity:'1',visibility:'visible',display:'block',stroke:'rgb(60, 131, 125)',strokeWidth:'2',strokeDasharray:'5px, 4px',strokeDashoffset:String(c.offset||0),strokeLinecap:'butt',strokeLinejoin:'miter',vectorEffect:'non-scaling-stroke'};
global.getComputedStyle=n=>Object.assign({},style,n.customStyle||{});
function configure(path,points,styleChanges={}){
  if(c.float32Geometry)points=points.map(p=>p.map(Math.fround));
  path.points=points;path.customStyle=styleChanges;path.setAttribute('d','M '+points.map(p=>p.join(' ')).join(' L '));path.getScreenCTM=()=>matrix;
  path.parts=points.slice(1).map((p,i)=>({a:points[i],b:p,len:Math.hypot(p[0]-points[i][0],p[1]-points[i][1])}));
  path.getTotalLength=()=>{const len=path.parts.reduce((sum,p)=>sum+p.len,0);return c.float32Geometry?Math.fround(len):len;};
  path.getPointAtLength=arc=>{let pos=c.float32Geometry?Math.fround(arc):arc;for(const p of path.parts){if(pos<=p.len){const q={x:p.a[0]+(p.b[0]-p.a[0])*pos/p.len,y:p.a[1]+(p.b[1]-p.a[1])*pos/p.len};return c.float32Geometry?{x:Math.fround(q.x),y:Math.fround(q.y)}:q;}pos-=p.len;}const p=points.at(-1);return {x:p[0],y:p[1]};};
  path.nearest=(x,y)=>{let arc=0,best={distance:Infinity};for(const p of path.parts){const dx=p.b[0]-p.a[0],dy=p.b[1]-p.a[1],t=Math.max(0,Math.min(1,((x-p.a[0])*dx+(y-p.a[1])*dy)/(p.len*p.len))),distance=Math.hypot(x-p.a[0]-t*dx,y-p.a[1]-t*dy);if(distance<best.distance)best={distance,arc:arc+t*p.len};arc+=p.len;}return best;};
  path.isPointInStroke=q=>{
    if(c.float32Geometry)q={x:Math.fround(q.x),y:Math.fround(q.y)};
    const s=getComputedStyle(path),dash=s.strokeDasharray==='none'?null:s.strokeDasharray.split(/[ ,]+/).map(parseFloat),period=dash&&dash.reduce((a,b)=>a+b,0),painted=arc=>!dash||((arc+(c.offset||0))%period+period)%period<dash[0];
    // Unlike nearest-arc approximation, a real stroked corner is the union of
    // painted segments. These cases use butt caps and the inner miter side.
    if(c.strokeUnion){let arc=0;for(const p of path.parts){const dx=p.b[0]-p.a[0],dy=p.b[1]-p.a[1],t=((q.x-p.a[0])*dx+(q.y-p.a[1])*dy)/(p.len*p.len),distance=Math.abs((q.x-p.a[0])*dy-(q.y-p.a[1])*dx)/p.len;if(t>=0&&t<=1&&distance<=parseFloat(s.strokeWidth)/2&&painted(arc+t*p.len))return true;arc+=p.len;}return false;}
    const p=path.nearest(q.x,q.y);return p.distance<=parseFloat(s.strokeWidth)/2+1e-8&&painted(p.arc);
  };
}
configure(e,c.points||[[30,100],[568.421875,100]],c.style||{});
if(c.rawPath!==undefined)e.setAttribute('d',c.rawPath);
if(c.pathLength!==undefined)e.setAttribute('pathLength',String(c.pathLength));
const extras=[];for(const spec of c.crossingPaths||[]){const p=d.createElementNS('http://www.w3.org/2000/svg','path');if(spec.foreign)p.id='foreign-path';else if(spec.parent){p.dataset.mapParent='parent';p.dataset.mapChild='child';}else{p.dataset.mapRelation=spec.id||'tasks:relation:91';p.dataset.fromEntity='other-from';p.dataset.toEntity='other-to';}svg.append(p);configure(p,spec.points,{strokeDasharray:'none',strokeWidth:spec.width||'2'});extras.push(p);}
const cards=[];for(const spec of c.cards||[]){const n=d.createElement('button');n.dataset.mapPosition=spec.id||'card';if(spec.task)n.dataset.taskOpen=spec.task;n.area=spec.rect;if(spec.hidden)n.customStyle={visibility:'hidden'};m.append(n);cards.push(n);}
let calls=0,arcs=[];const original=e.getPointAtLength;e.getPointAtLength=arc=>{arcs.push(arc);return original(arc);};
d.elementsFromPoint=(x,y)=>{
  if(c.float32HitTest){x=Math.fround(x);y=Math.fround(y);}
  const q={x:(x-matrix.e)/matrix.a,y:(y-matrix.f)/matrix.d},stack=[];
  if(!c.pointerlessCards)for(const n of cards){const r=n.area;if(!n.customStyle&&x>=r.x&&x<=r.x+r.width&&y>=r.y&&y<=r.y+r.height)stack.push(n);}
  for(const p of extras)if(p.isPointInStroke(q))stack.push(p);
  if(!c.missing&&!c.gapsOnly&&getComputedStyle(e).visibility==='visible'&&getComputedStyle(e).display!=='none'&&e.isPointInStroke(q))stack.push(e);
  stack.push(c.gapSurface==='map'?m:svg,m);return stack;
};
d.elementFromPoint=(x,y)=>{calls++;return d.elementsFromPoint(x,y)[0];};
const result=new Function('e','m',input.helper+'\n'+input.edge+'\nreturn edge(e);')(e,m);
console.log(JSON.stringify({result,calls,arcs}));dom.window.close();
"""
        edge = next(line.strip() for line in Path(MODULE.__file__).read_text().splitlines() if line.strip().startswith('function edge(e)'))
        helper = MODULE.RELATION_PATH_SAMPLES_JS
        if case.pop('legacyCoordinates', False):
            current = 'var z={x:Math.fround(rawScreen.x),y:Math.fround(rawScreen.y)},localProbe=point(inverse,z.x,z.y)'
            self.assertIn(current, helper)
            helper = helper.replace(current, 'var z=rawScreen,localProbe=q', 1)
        run = subprocess.run(['node', '-e', driver], cwd=Path(__file__).parents[1],
                             input=json.dumps(dict(helper=helper, edge=edge, case=case)),
                             text=True, capture_output=True, timeout=30)
        self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
        return json.loads(run.stdout)

    def assert_complete_sampling(self, record):
        edge = record['result']; proof = edge['sampling']; count = proof['count']
        self.assertTrue(proof['valid'])
        self.assertEqual(record['calls'], count)
        self.assertEqual(sum(proof['counts'].values()), count)
        self.assertLessEqual(proof['maxScreenStep'], .5)
        # The endpoint bounds probes precede every evenly spaced interior probe.
        self.assertEqual(record['arcs'][:2], [0, edge['length']])
        self.assertEqual(len(record['arcs']), count + 2)
        for i, arc in enumerate(record['arcs'][2:]):
            self.assertAlmostEqual(arc, edge['length'] * (i + .5) / count)
        self.assertAlmostEqual(proof['firstArc'], record['arcs'][2])
        self.assertAlmostEqual(proof['lastArc'], record['arcs'][-1])
        self.assertLessEqual(len(edge['ownHits']), proof['diagnosticLimit'])
        self.assertLessEqual(len(edge['blockedHits']), proof['diagnosticLimit'])
        self.assertLessEqual(len(edge['crossings']), proof['diagnosticLimit'])

    def test_real_r90_r93_float32_corner_uses_one_coordinate_for_both_queries(self):
        # Actual 88ec3e6 receipt points. Local SVG values and the screen hit-test
        # each use float32; the map translation is exact and is not rounded away.
        for points, length, raw_y in [
            ([[277.828125, 366], [277.828125, 379.3333333333333], [687.25, 379.3333333333333], [687.25, 269], [697.25, 269]], 543.0885620117188, 561.2239685058594),
            ([[317.90625, 442], [317.90625, 455.3333333333333], [695.25, 455.3333333333333], [695.25, 355.5], [697.25, 355.5]], 492.51043701171875, 637.2239685058594),
        ]:
            case = dict(points=points, matrix=dict(a=1, b=0, c=0, d=1, e=41, f=181.890625),
                        float32Geometry=True, float32HitTest=True, strokeUnion=True, gapSurface='map')
            old = self.probe(**case, legacyCoordinates=True)['result']
            self.assertEqual(old['length'], length)
            self.assertFalse(old['uncovered'])
            self.assertEqual(old['sampling']['counts']['blocked'], 1)
            blocked = old['blockedHits'][0]
            self.assertTrue(blocked['painted'])
            self.assertEqual(blocked['hit']['id'], 'map')
            self.assertEqual(blocked['y'], raw_y)
            self.assertTrue(5 < blocked['arc'] % 9 < 9)
            record = self.probe(**case)
            self.assert_complete_sampling(record)
            new = record['result']
            self.assertTrue(new['uncovered'])
            self.assertEqual(new['sampling']['counts']['blocked'], 0)
            self.assertEqual(new['sampling']['coordinates'], 'float32-screen-roundtrip')
            self.assertEqual(new['sampling']['roundtripDifferenceCount'], 1)
            delta = new['roundtripDifferences'][0]
            self.assertTrue(delta['rawPainted'])
            self.assertFalse(delta['painted'])
            self.assertEqual(delta['localProbe']['y']-delta['rawLocal']['y'], 2**-15)
            self.assertEqual(delta['rawScreen']['y'], raw_y)
            # A screen background at an actually painted point is still failure.
            missing = self.probe(**case, missing=True)['result']
            self.assertFalse(missing['uncovered'])
            self.assertGreater(missing['sampling']['counts']['blocked'], 0)
            self.assertFalse(missing['ownHits'])

    def test_original_r90_arc_length_alias_is_reproducible_without_chrome(self):
        # 0f497e receipt: all 19 old probes occupy the 4px gap in a 5px/4px
        # dash cycle. This unobscured fixture isolates aliasing from card overlap.
        length = 538.421875
        old_phases = [length * i / 20 % 9 for i in range(1, 20)]
        self.assertTrue(all(5 <= value < 9 for value in old_phases))
        self.assertAlmostEqual(old_phases[0], 8.92109375)
        self.assertAlmostEqual(old_phases[-1], 7.50078125)
        for surface in ('map', 'svg'):
            record = self.probe(gapSurface=surface)
            self.assert_complete_sampling(record)
            edge = record['result']
            self.assertTrue(edge['visible'] and edge['uncovered'] and edge['inBounds'])
            self.assertTrue(edge['ownHits'])
            self.assertGreater(edge['sampling']['counts']['gap'], 0)
            self.assertEqual(edge['sampling']['counts']['blocked'], 0)

    def test_original_r90_card_intersection_remains_a_failure_after_alias_fix(self):
        # Rebuilt from the same receipt's node rectangles and production route.
        points = [[318.828125, 547.890625], [318.828125, 558.890625],
                  [720.25, 558.890625], [720.25, 450.890625], [738.25, 450.890625]]
        cards = [dict(id='ivln', rect=dict(x=508.5, y=415.890625, width=213.75, height=56)),
                 dict(id='ndh', rect=dict(x=508.5, y=491.890625, width=213.75, height=56))]
        record = self.probe(points=points, cards=cards)
        self.assert_complete_sampling(record)
        edge = record['result']
        self.assertEqual(edge['length'], 538.421875)
        self.assertTrue(edge['ownHits'])
        self.assertFalse(edge['uncovered'])
        self.assertEqual({row['position'] for row in edge['cardIntersections']}, {'ivln', 'ndh'})
        self.assertGreater(edge['sampling']['counts']['blocked'], 0)
        # Pointer-events:none or another SVG stroke cannot conceal a real card.
        concealed = self.probe(points=points, cards=cards, pointerlessCards=True)['result']
        self.assertFalse(concealed['uncovered'])
        self.assertEqual(concealed['sampling']['counts']['blocked'], 0)

    def test_tiny_between_probe_card_is_rejected_by_complete_segment_geometry(self):
        edge = self.probe(cards=[dict(rect=dict(x=31.001, y=99, width=.04, height=2))])['result']
        self.assertFalse(edge['uncovered'])
        self.assertTrue(edge['cardIntersections'])

    def test_original_r93_along_card_top_borders_is_independently_rejected(self):
        points = [[358.90625, 623.890625], [358.90625, 643.890625],
                  [708.25, 643.890625], [708.25, 537.390625], [738.25, 537.390625]]
        cards = [dict(id='hieranav', rect=dict(x=278.75, y=643.890625, width=213.75, height=56)),
                 dict(id='soon', rect=dict(x=508.5, y=643.890625, width=213.75, height=56))]
        for pointerless in (False, True):
            edge = self.probe(points=points, cards=cards, pointerlessCards=pointerless)['result']
            self.assertEqual(edge['length'], 505.84375)
            self.assertFalse(edge['uncovered'])
            self.assertEqual({row['position'] for row in edge['cardIntersections']}, {'hieranav', 'soon'})

    def test_missing_hidden_empty_and_gap_only_paths_cannot_provide_visible_evidence(self):
        for change in (dict(missing=True), dict(gapsOnly=True), dict(style=dict(strokeDasharray='0px, 4px')), dict(rawPath=''), dict(rawPath='M 30 100 C 40 100 500 100 568 100')):
            with self.subTest(change=change):
                edge = self.probe(**change)['result']
                self.assertFalse(edge['uncovered'])
                self.assertFalse(edge['ownHits'])
        for style in (dict(visibility='hidden'), dict(display='none'), dict(opacity='0'), dict(strokeOpacity='0'), dict(strokeWidth='0')):
            with self.subTest(style=style):
                self.assertFalse(self.probe(style=style)['result']['visible'])

    def test_only_geometric_registered_transverse_crossings_are_permitted(self):
        for parent in (False, True):
            for x, painted in ((100, False), (104, True)):
                # At x=100 all covered samples lie in the gap; x=104 lies
                # completely inside a painted dash. Both are real crossings.
                record = self.probe(crossingPaths=[dict(points=[[x, 80], [x, 120]], parent=parent)])
                self.assert_complete_sampling(record)
                self.assertTrue(record['result']['uncovered'])
                self.assertGreater(record['result']['sampling']['counts']['crossing'], 0)
                self.assertTrue(all(row['sine'] == 1 for row in record['result']['crossings']))
                self.assertTrue(all(row['painted'] is painted for row in record['result']['crossings']))
        for spec in (dict(points=[[101, 80], [101, 120]], foreign=True),
                     dict(points=[[100, 100], [120, 100]]),
                     dict(points=[[100, 99.9], [120, 100.1]])):
            with self.subTest(spec=spec):
                edge = self.probe(crossingPaths=[spec])['result']
                self.assertFalse(edge['uncovered'])
                self.assertGreater(edge['sampling']['counts']['blocked'], 0)
        edge = self.probe(crossingPaths=[dict(points=[[101, 80], [101, 120]])],
                          cards=[dict(rect=dict(x=100, y=99, width=2, height=2))])['result']
        self.assertFalse(edge['uncovered'])

    def test_sampling_covers_small_dashes_short_paths_and_scaled_paths(self):
        for change in (dict(points=[[30, 100], [46, 100]]),
                       dict(points=[[30, 100], [46, 100]], style=dict(strokeDasharray='.2px, .1px')),
                       dict(matrix=dict(a=2, b=0, c=0, d=2, e=0, f=0))):
            with self.subTest(change=change):
                record = self.probe(**change)
                self.assert_complete_sampling(record)
                self.assertTrue(record['result']['uncovered'])
                self.assertTrue(record['result']['ownHits'])
        # Oversized sample budgets fail rather than silently coarsening the scan.
        self.assertFalse(self.probe(style=dict(strokeDasharray='.0001px, .0001px'))['result']['uncovered'])

    def test_exact_endpoints_can_touch_their_own_cards_but_not_cross_their_interior(self):
        cards = [dict(task='from', rect=dict(x=10, y=90, width=20, height=20)),
                 dict(task='to', rect=dict(x=46, y=90, width=20, height=20))]
        edge = self.probe(points=[[30, 100], [46, 100]], cards=cards)['result']
        self.assertTrue(edge['uncovered'])
        self.assertFalse(edge['cardIntersections'])
        edge = self.probe(points=[[29.5, 100], [46, 100]], cards=cards)['result']
        self.assertFalse(edge['uncovered'])


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
            'viewport': rect(0, 0, 1440, 900), 'window': dict(x=0, y=0), 'layout': 'reading', 'methodReading': 'true', 'collapsed': 'false', 'focus': 'np-node-method-vlfm',
            'panels': rect(16, 132, 1408, 752), 'columnGap': 16,
            'treePane': proof(rect(16, 132, 400, 752)), 'treeProof': proof(rect(17, 205, 398, 580)),
            'tree': dict(rect=rect(17, 205, 398, 580), client=rect(18, 206, 396, 578), left=0, top=200, scrollWidth=396, scrollHeight=978, maxLeft=0, maxTop=400),
            'title': proof(rect(34, 155, 364, 32), '当前位置与来路'),
            'selected': dict(count=1, id='method-vlfm', tree='l', entity='vlfm-recipe', aria='true', scope='task:category-objectnav',
                             row=proof(rect(40, 360, 356, 65)), label=proof(rect(60, 370, 320, 30), 'VLFM'), content=dict(x=22, y=354)),
            'toggle': dict(tag='BUTTON', hidden=False, disabled=False, controls='np-detail-scroll', expanded='true', proof=proof(rect(150, 90, 150, 32), '收起阅读栏')),
            'reader': dict(hidden=False, display='block', tabIndex=-1, proof=proof(rect(432, 132, 992, 752)),
                           scroll=dict(rect=rect(433, 228, 990, 655), client=rect(434, 229, 988, 653), top=160, left=0, maxTop=1000, maxLeft=0, scrollHeight=1718, scrollWidth=545),
                           heading=proof(rect(433, 133, 990, 95), 'VLFM · v1'), entity='vlfm-recipe', flowCount=5, savedScroll=160, persistedScroll=160)}
        collapsed = copy.deepcopy(original)
        collapsed.update(collapsed='true', focus='np-reader-toggle')
        for state in (collapsed['preservedState'], collapsed['history']['model']):
            state['contexts'][task_key]['taskView']['focusTargetByTree']['l'] = 'np-reader-toggle'
        collapsed['treePane']['rect']['width'] = 1408
        collapsed['treeProof']['rect']['width'] = collapsed['tree']['rect']['width'] = 1406
        collapsed['tree']['client']['width'] = collapsed['tree']['scrollWidth'] = 1404
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
            '6md0fOSnufTTrVn0t925Pv4yuWkSwMh+gI0oJ4vWta9v09pELVfvgPDb3/8jLQY0+8leePKjfYLH2oxn5zM12VDEXv9ODS6CLlaL'
            'X8eXp0gi/AShkpeXpNXBD4MhRlNBcVU4VmKGiHOaeNStFZg+5ZhZTb16IxUXFlktLZfd18xojbUtiS6wkYXAjDlcbEcgWXBnCoa4'
            'sopVzlr/r6QDCDTY9C0Q6Hr5u7GbRBb2rXW2Ms7j6JgB/rjNCreWciG9Da20IV6ja+ysFN4mGlRBg60dtAoapsHuqNcs9yMpnIEh'
            '31HhDLf20Apnb6Q/IPUyn42nqz1BhaLECcFKVlHhHUFaFJXUbjtUlJI4XCpGJUW2KAmtKmM7r9nQQhjNBPPY431uSYisnBuEisHW'
            'DhoqhmlwO35t1/yR8GJg3HfEi+HWHhov9kv/wwCNe40S7QwrOwLKQUTp7sncHJSmga535IlbcMNvuy/74+iLgeVtfAtBNaPCcWtE'
            'qaWmhCCRuB5I09LQihNRIMq9pjAWW3Mn5nCOFK5Qqqr8j8KUgqtSq5t4Z0gZ7RrAvYsy0g+kjK5bjJ3BcGukcgAQ9TZAfDhVO8wA'
            'DzK7u6jbm9ZhC3QMzGpHRXxTh7tA1HYV/ftnxvsxMAaRoJ5GUK5HD8V312jsozubH0iW92yAzC5m0z0oH+a4KrBB2ghqrKywNkiV'
            '29WHsJwZKZXQfgEdN9xJUXbqA2nHOXNVpa3UyCFWYErtoH4YbO2gnZVhGuwukrDUj+SjDAz3jj7KcGsP7aPsheyH4ZoYsw9c0Eox'
            'R22BkRQWIY48QugBs1JhWyBtC0P80tCSSVMSZFpckFi60hlOsbOmIMoKbSo6iAuDrR00LgzTYGcG9Qv9SKgwMNg7osJwaw+NCnsg'
            '+mFgwvlMrTYCFPVHH47m62oy1kEAwnOnSHnnUTBLiTEPvIsmlKts5VzlCPNi7n96y5V122S6ZN6nLEjJpdKClFXphgIZlmlslGQl'
            'wcQ6YpWlyru9Q9tkRCtGqqJQ3vg3BWMIUeL0/W+TbZ/BQW2TbWEOLz+f1GJql8tkdxWzQj4JCROXaL98MbB4vyO+GO7mgPnicSyJ'
            'gbW/zeI2loSyldEVl5gT3yhHpKSMdQEq2GkRziqtNCKEYMSVKspBQ2Ows4M2NIZJtLPOA0Z4JEtjYLR3tDSGW3toS2MfVD8MU+PT'
            '2C7UfgLjnGpdeK+jKhj2v1eVoELT7cjBqJMU86JyzFCMufP/TNEhBxesIEjh0kFjhjBZks5FKR2WBXPOOsuJ1hgXThI9iByDnR00'
            'cgyTaGcebpjhkdBjYMR3RI/h1h4aPfZF+cNAkPGFOrf7QRCLPWpUGmvKRKUdkl7sFd6OIIgUgkJgyVsZReGtelSRknWpGKxCHFvH'
            'KuWYhwlLCFcdgjDDhcWWmqJgpii9s+XBig8iyGBnB40gwyTamY8bZngkBBkY8R0RZLi1h0aQfVH+QBBkulypqbZ7RBJVVLwgmpak'
            'LL2JIBSWZOiMARZcWY0LigojlZQef0QlW6ggUhNCFdKFQIQxwRTlSc4Xw1S7shQCew8GWSVKVNrhnK/Bzg4aSYZJtDs/bzDFIyHK'
            'wMjviCjDrT00oux7BQ4EWS4n+9hdsRoZTZE1jAuOJdeucG7gvAB1JVVGUSGpEwiV2paFFC1c4AoTv5CoYhpZ5G0cTiwZhovB1g4a'
            'LoZpsDuz+pV+JIgYGO0dIWK4tYeGiH1Q/TBgYaL2k42BbUkrbx5IbS2tsGCywtVAIJy7QjuqvJ0gneGK4cpw6Tp/RXlgYcbiymJV'
            'WsQcJx7fh3BhsLWDxoVhGuzMoWGpHwkYBoZ7R2AYbu2hgWEvZD8MZLhYT4DJ94ANlcGGKWtLaysuSmKYwWQAGxR3SqGKG6L9ChVO'
            'VEyKqouGSm/slUSVkvm1s04RXNHhE2iDrR12RsYgDXZm0nqxHysrY/uA75qVMdjag2dl7Ifwh4EPU49r+zhD4Ar/hPSyTA1HFsgv'
            'mRoAB8IqLUtCJHdOYg8phldVcgrA+w+uUJRIqjVjHiuqgnR2BVHeliC+EY40ckRQ779Uw9gx1NlhY8cgiXZmYWCExwKO7aO9K3AM'
            'tvbgwLEHqh8Iaph93JvivB2gNJWEliXWyNtwBccDud+llcSgyhmmSWEoYqW3PtjwSdTtjx/6SdShUd+CAc1j3Y8yMNi7Hj8dbO3B'
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
        old = MODULE._reader_toggle_preserved(original, original['route']['node'])
        new = MODULE._reader_toggle_preserved(collapsed, 'np-reader-toggle')
        self.assertEqual(old, new, 'historical failure was only the neutral focus projection')
        with self.assertRaises(RuntimeError):
            MODULE.check_reader_toggle_snapshot(original, False)
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
<main id="navigation-product" data-reading-layout="reading" data-method-reading="true" data-reader-collapsed="false">
<button id="np-reader-toggle" aria-controls="np-detail-scroll" aria-expanded="true">收起阅读栏</button>
<div class="np-panels" style="column-gap:16px"><section class="np-tree-pane"><h2 id="np-tree-heading">Branch</h2><div id="np-tree-scroll"><div id="np-tree"><section data-parallel-tree="l" data-scope-id="task:category-objectnav"><ul><li id="np-node-method" data-position="method" data-tree="l" data-entity="recipe" aria-selected="true"><div class="np-node-row"><button class="np-node-label">VLFM</button></div><ul><li><div class="np-node-row" id="decoy">Other row</div></li></ul></li></ul></section></div></div></section>
<aside class="np-reading-pane"><div id="np-reader-heading" class="np-reader-heading">VLFM v1</div><div id="np-detail-scroll" tabindex="-1"><div class="np-method-mechanism" data-mechanism-entity="recipe"><dl class="np-method-flow">${'<dd>flow</dd>'.repeat(5)}</dl></div></div></aside></div></main>`,{url:'http://localhost/',runScripts:'outside-only'});
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
 setRect(toggle,20,20,150,32);setRect(tree,10,100,800,600);setRect(row,30,300,750,65);setRect(label,50,310,700,30);setRect(d.getElementById('decoy'),30,500,750,65);setRect(reader,830,200,550,600);setRect(d.querySelector('.np-reading-pane'),830,100,550,700);
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
 reader.hidden=true;reader.style.display='none';d.querySelector('.np-reading-pane').hidden=true;d.querySelector('.np-reading-pane').style.display='none';setRect(reader,0,0,0,0);setRect(d.querySelector('.np-reading-pane'),0,0,0,0);const hidden=snapshot();assert.equal(hidden.reader.hidden,true);assert.equal(hidden.reader.display,'none');assert.equal(hidden.reader.proof.opaque,false);
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
                'window': {'x': 0, 'y': 0}, 'focus': 'exact-endpoint', 'activatedControl': 'exact-endpoint'}

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
                     lambda x: x['window'].update(y=88), lambda x: x.update(scale=.9)]
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

    def test_portable_fixed_identity_and_section_proofs_reject_wrong_or_hidden_text(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8')),specs=input.specs,i=specs[0].methodIdentity;
const dom=new JSDOM('<style>*{opacity:1;visibility:visible;transform:none;zoom:1;color:rgb(20,30,40);background-color:rgb(255,255,255);font-size:15px}.np-reader-identity-duplicate{display:none}</style><aside class="np-reading-pane"><header id="np-reader-heading"><div id="np-reader-object-title"><h2></h2></div><div id="np-reader-object-meta"></div></header><div id="np-detail-scroll"><section data-mechanism-entity="'+i.entity+'"><h3><span class="np-method-identity-prefix np-reader-identity-duplicate"></span>方法内部结构</h3><article data-method-claim="'+input.claim+'"><p></p></article></section></div></aside><div id="overlay"></div>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,host=d.getElementById('np-reader-object-title'),title=host.querySelector('h2'),meta=d.getElementById('np-reader-object-meta'),heading=d.querySelector('[data-mechanism-entity] > h3'),prefix=heading.firstElementChild,claim=d.querySelector('[data-method-claim] > p'),reader=d.getElementById('np-detail-scroll'),header=d.getElementById('np-reader-heading');
for(const key of ['position','entity','paper','version'])host.dataset['object'+key[0].toUpperCase()+key.slice(1)]=i[key];title.textContent=i.title;meta.textContent=specs[3].text;prefix.textContent=i.title+' · ';prefix.dataset.readerDuplicatePosition=i.position;claim.textContent=specs[1].text;
w.NavigationProductApp={getState:()=>({route:{node:i.position,paper:i.paper,version:i.version}})};
Object.defineProperty(w,'innerWidth',{value:1440});Object.defineProperty(w,'innerHeight',{value:900});
const style=w.getComputedStyle.bind(w);w.getComputedStyle=e=>new Proxy(style(e),{get:(target,key)=>key==='zoom'?(target.zoom||'1'):Reflect.get(target,key)});
function r(y,h=24){return{x:820,y,width:560,height:h,left:820,top:y,right:1380,bottom:y+h};}
for(const n of d.querySelectorAll('*')){n.getBoundingClientRect=()=>n===reader?r(220,600):n===header?r(132,88):n===title?r(144):n===meta?r(176):n===heading?r(240):r(290);for(const[k,v]of Object.entries({clientLeft:0,clientTop:0,clientWidth:560,clientHeight:n===reader?600:n===header?88:24,scrollWidth:560,scrollHeight:n===reader?600:n===header?88:24}))Object.defineProperty(n,k,{value:v,configurable:true});}
w.Range.prototype.getClientRects=function(){const parent=this.startContainer.parentElement;return w.getComputedStyle(parent).display==='none'?[]:[parent.getBoundingClientRect()];};
let covered=false;d.elementFromPoint=(x,y)=>covered?d.getElementById('overlay'):y<170?title:y<210?meta:y<270?heading:claim;
const proof=new w.Function(input.proof),results={valid:specs.map(s=>proof(s)),legacy:proof({selector:specs[0].selector,text:specs[0].text})};
// A wrong visible title or exact source/version attribute cannot represent the hidden prefix.
for(const key of ['position','entity','paper','version']){const attr='object'+key[0].toUpperCase()+key.slice(1),old=host.dataset[attr];host.dataset[attr]='wrong';assert.throws(()=>proof(specs[0]),/exact fixed source identity/);assert.throws(()=>proof(specs[2]),/missing/);host.dataset[attr]=old;}
title.textContent='wrong title';assert.throws(()=>proof(specs[0]),/exact fixed source identity/);assert.throws(()=>proof(specs[2]),/missing/);title.textContent=i.title;
meta.textContent='wrong version';assert.throws(()=>proof(specs[3]),/missing/);meta.textContent=specs[3].text;
const oldRoute=w.NavigationProductApp;w.NavigationProductApp={getState:()=>({route:{node:i.position,paper:i.paper,version:'wrong-version'}})};assert.throws(()=>proof(specs[0]),/exact fixed source identity/);w.NavigationProductApp=oldRoute;
prefix.dataset.readerDuplicatePosition='wrong-position';assert.throws(()=>proof(specs[0]),/exact fixed source identity/);prefix.dataset.readerDuplicatePosition=i.position;
prefix.style.display='inline';assert.throws(()=>proof(specs[0]),/exact fixed source identity/);prefix.removeAttribute('style');
const hidden=d.createElement('span');hidden.style.display='none';hidden.textContent='scientific qualifier';heading.appendChild(hidden);assert.throws(()=>proof({...specs[0],text:heading.textContent}),/exact fixed source identity/);hidden.remove();
covered=true;results.covered=specs.map(s=>proof(s));covered=false;
title.style.opacity='0';results.hiddenTitle=proof(specs[2]);title.removeAttribute('style');heading.style.opacity='0';results.hiddenSection=proof(specs[0]);heading.removeAttribute('style');
process.stdout.write(JSON.stringify(results));}finally{dom.window.close();}
"""
        for position in self.expected['portable']:
            claim = MODULE.task_route_claims(self.science, position)[0]
            specs = MODULE.portable_method_proof_specs(self.science, position, claim)
            self.assertEqual(len(specs), 4)
            self.assertEqual(specs[2]['text'], self.science['entities'][position['entityId']]['label'])
            self.assertIn(self.science['versions'][position['versionId']]['label'], specs[3]['text'])
            result = subprocess.run(['node', '-e', script], input=json.dumps({'specs': specs, 'claim': claim['id'], 'proof': MODULE.TASK_ROUTE_PROOF_JS}), text=True, capture_output=True, cwd=Path(__file__).parents[1])
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            actual = json.loads(result.stdout)
            for spec, proof in zip(specs, actual['valid']):
                MODULE.check_task_route_proof(proof, spec.get('renderedText', spec.get('text')))
            for proof in actual['covered'] + [actual['hiddenTitle'], actual['hiddenSection'], actual['legacy']]:
                with self.assertRaises(RuntimeError):
                    MODULE.check_task_route_proof(proof)

    def test_portable_capture_specs_match_actual_source_dom_for_both_variants(self):
        specs = [MODULE.portable_method_proof_specs(self.science, p, MODULE.task_route_claims(self.science, p)[0]) for p in self.expected['portable']]
        body = r"""
await scope('setting:portable-objectnav');await inventory('setting:portable-objectnav');
for(let index=0;index<e.portable.length;index++){const p=e.portable[index];await select(p.id);for(const spec of input.specs[index]){const nodes=[...d.querySelectorAll(spec.selector)].filter(n=>spec.text===undefined||n.textContent===spec.text);assert.equal(nodes.length,1,JSON.stringify(spec));}const h=d.querySelector('[data-mechanism-entity="'+p.entityId+'"] > h3');assert.equal(h.lastChild.nodeType,w.Node.TEXT_NODE);assert.equal(h.lastChild.textContent,'方法内部结构');assert.equal(h.firstElementChild.dataset.readerDuplicatePosition,p.id);states.push(snapshot());d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.scopes['setting:portable-objectnav'].roots[0]);}
"""
        states = run_product_capture_script(self, body, {'science': self.science, 'expected': self.expected, 'specs': specs})
        self.assertEqual(len(states), 2)
        for state, position in zip(states, self.expected['portable']):
            MODULE.check_task_route_method(state, position, self.science['entities'][position['entityId']], MODULE.task_route_claims(self.science, position))

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
const dom=new JSDOM(`<!doctype html><style>#np-detail-scroll{overflow-anchor:none;overflow-y:auto;font-size:15px;line-height:24px}.np-reader-heading{position:sticky}</style><main id="navigation-product" data-reading-layout="browse"><aside id="np-detail-scroll"><div id="np-reader-heading" class="np-reader-heading">Reader</div><section data-task-route-scope="task:category-objectnav"><h2>已有路线与方法</h2><p id="intro">原记录</p><details data-task-change="methods:relation:90" open><summary id="relation-summary">SemExp → PONI</summary><article><p id="claim">原句第一行与第二行</p></article><nav><button id="endpoint" data-change-target="poni-position">PONI</button></nav></details></section></aside></main>`,{url:'https://example.org/',runScripts:'outside-only'});
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
                'window': {'x': 0, 'y': 0}, 'focus': 'natural-entry-focus', 'changes': [], 'relationEntries': [dict(row, selected='false') for row in expected['relations']],
                'relationDisclosure': {'open': False, 'tag': 'DETAILS', 'id': 'np-task-route-relations', 'summary': 'np-task-route-relations-summary', 'current': str(sum(r['scope'] == 'current-scope' for r in expected['relations'])), 'outside': str(sum(r['scope'] == 'outside-scope' for r in expected['relations'])), 'beforeTree': True, 'insideTree': False, 'insideTreeScroll': False, 'toolbar': True},
                'density': {'state': 'ready', 'selectedReady': True, 'internalScroll': [{'id': 'np-detail-scroll', 'top': 0, 'left': 0}],
                            'roots': expected['roots'], 'gap': 'original gap' if case.get('empty') else None}}

    def test_density_source_contract_has_four_bounded_cases_and_no_invented_pipeline(self):
        self.assertEqual([c['scope'] for c in self.cases], ['task:category-objectnav', 'task:imagenav', 'setting:portable-objectnav', 'task:aerial-visual-object-search'])
        expected = MODULE.task_route_expected(self.science)
        for case in self.cases:
            self.assertEqual(case['proofs'][0]['region'], 'toolbar')
            self.assertTrue(all(p['region'] == 'canvas' for p in case['proofs'][1:]))
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
                         lambda d: d['relationDisclosure'].update(insideTreeScroll=True), lambda d: d['relationDisclosure'].update(insideTree=True),
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
        self.assertEqual(report['taskDensityChecks'][0]['documentTopClaimed'], True)
        for scene in report['taskDensityChecks'][0]['scenes']:
            self.assertEqual(scene['naturalEntryWindow']['y'], 0)
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
for(const c of input.cases){await scope(c.scope);const canvas=d.getElementById('np-tree-scroll');for(const spec of c.proofs){const found=[...d.querySelectorAll(spec.selector)].filter(n=>n.textContent===spec.text);assert.equal(found.length,1,spec.selector+' '+spec.text);const region=spec.region==='toolbar'?d.querySelector('.np-workspace-bar'):canvas;assert.ok(region.contains(found[0]));assert.equal(canvas.contains(d.getElementById('np-task-route-canvas')),false);for(let p=found[0];p&&p!==region;p=p.parentElement)if(p.tagName==='DETAILS'&&!p.open)assert.ok(p.querySelector(':scope > summary').contains(found[0]),'natural field is behind a closed disclosure');}states.push(natural());}
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
                'treeScroll': {'top': 320, 'left': 0}, 'readerScroll': {'top': 65, 'left': 0}, 'window': {'x': 0, 'y': 0},
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
        for function in (MODULE.exploration_state_checks, MODULE.desktop_hierarchy_checks, MODULE.expose_source_position, MODULE.reveal_control, MODULE.task_route_checks, MODULE.cold_relation_refresh, MODULE.cold_relation_refresh_comparison):
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
assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisState,'imported');assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisVersion,e.poni.versionId);assert.equal(d.querySelector('[data-analysis-state=imported] > p').textContent,'本版本部分解析：22/59 原节点已填 · 0 个实例答案');assert.equal(d.getElementById('np-open-analysis-template').textContent,'通用原59节点模板（未填答参考）');
d.querySelector('[data-tree-tab="c"]').click();await ready(()=>a.getState().route.tree==='c');const ci='pos:c:6a8a9d2f7b1f3ab3a8ada5';await select(ci);const cRoute=a.getState().route;
d.querySelector('[data-tree-tab="l"]').click();await ready(()=>a.getState().route.node===e.poni.id);assert.deepEqual(JSON.parse(JSON.stringify(a.getState().route)),JSON.parse(JSON.stringify(lRoute)));assert.equal(d.querySelectorAll('#np-tree [data-parallel-tree]').length,1);assert.equal(d.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]').length,1);assert.equal(d.querySelector('#np-tree').dataset.activeTaskTree,'l');
d.querySelector('[data-tree-tab="c"]').click();await ready(()=>a.getState().route.node===ci);assert.deepEqual(JSON.parse(JSON.stringify(a.getState().route)),JSON.parse(JSON.stringify(cRoute)));assert.equal(m.taskView(a.getState()).lastRouteByTree.l.node,e.poni.id);assert.equal(m.taskView(a.getState()).lastRouteByTree.c.node,ci);
d.querySelector('[data-tree-tab="l"]').click();await ready(()=>a.getState().route.node===e.poni.id);d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a');const first=m.descendants(a.getBundle(),s.analyses.poni[e.poni.versionId].roots).find(id=>s.positions[id].kind==='analysis_answer');assert.equal(a.getState().route.node,first);assert.notEqual(first,s.analyses.poni[e.poni.versionId].roots[0]);assert.equal(a.getState().route.template,null);states.push(snapshot());
d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.poni.id);const vlfm=Object.values(s.positions).find(p=>p.scopeId==='task:category-objectnav'&&p.tree==='l'&&p.paperId==='vlfm'&&p.kind==='pipeline_recipe');const scopeRoot=s.forests['task:category-objectnav'].l[0];label(scopeRoot).click();await ready(()=>a.getState().route.node===scopeRoot);await select(vlfm.id);assert.equal(d.querySelector('[data-analysis-state]').dataset.analysisState,'not-imported');d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a');assert.equal(a.getState().route.node,null);assert.equal(a.getState().route.template,null);assert.ok(d.querySelector('#np-tree .np-empty').textContent.includes('尚未导入原59节点解析'));d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===vlfm.id);d.getElementById('np-open-analysis-template').click();await ready(()=>a.getState().route.template==='1');assert.equal(a.getState().route.paper,vlfm.paperId);assert.equal(a.getState().route.version,vlfm.versionId);const templateRoot=s.template.roots[0];label(templateRoot).click();await ready(()=>a.getState().route.node===templateRoot);assert.equal(d.querySelector('#np-detail-content .np-detail-body > .np-boundary').textContent,'参考模式：原59节点模板，当前论文/版本未填答；0答案，不计入解析覆盖。');assert.ok([...d.querySelectorAll('#np-detail-content .np-detail-block > p')].some(n=>n.textContent==='这是通用模板问题，当前论文版本未填答；不表示原论文没有讨论，也不借用其他论文的答案。'));states.push(snapshot());
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



class ReturnClickDiagnosticChecks(unittest.TestCase):
    def test_http_error_preserves_exception_and_exports_only_bounded_recognized_fields(self):
        class Body(io.BytesIO):
            def __init__(self, value): super().__init__(value); self.reads = []
            def read(self, size=-1): self.reads.append(size); return super().read(size)
        body = Body(json.dumps({'value': {'error': 'element click intercepted', 'message':
            'element click intercepted: Element <button id="np-task-route-return" value="PRIVATE_HTML_TOKEN">SECRET_TEXT</button> is not clickable at point (701, 154). Other element would receive the click: <div data-token="PRIVATE_TOKEN">. https://site/?token=PRIVATE_URL_TOKEN Bearer PRIVATE_BEARER_TOKEN',
            'stacktrace': 'PRIVATE_STACK', 'token': 'PRIVATE_JSON_TOKEN'}, 'extra': 'PRIVATE_EXTRA'}).encode())
        original = MODULE.urllib.error.HTTPError('http://127.0.0.1/session/PRIVATE_SESSION', 400, 'Bad Request', {'Set-Cookie': 'PRIVATE_COOKIE'}, body)
        driver = MODULE.Driver(1)
        with patch.object(MODULE.urllib.request, 'urlopen', side_effect=original):
            with self.assertRaises(MODULE.urllib.error.HTTPError) as caught:
                driver.request('POST', '/session/PRIVATE_SESSION/element/PRIVATE_ELEMENT/click', {'private': 'PRIVATE_REQUEST'})
        self.assertIs(caught.exception, original)
        self.assertEqual(str(caught.exception), 'HTTP Error 400: Bad Request')
        diagnostic = original.navigation_webdriver_diagnostic
        self.assertEqual(body.reads, [MODULE.WEBDRIVER_HTTP_BODY_LIMIT + 1])
        self.assertEqual(diagnostic['error'], 'element click intercepted')
        self.assertIn('not clickable at point (701, 154)', diagnostic['message'])
        self.assertIn('other element would receive the click', diagnostic['message'])
        self.assertEqual(diagnostic['command'], '/session/:session/element/:element/click')
        self.assertNotIn('PRIVATE', json.dumps(diagnostic)); self.assertNotIn('SECRET_TEXT', json.dumps(diagnostic))
        self.assertNotIn('<', diagnostic['message']); self.assertNotIn('headers', diagnostic)

    def test_http_error_non_json_oversize_shape_and_diagnostic_failures_fail_closed(self):
        cases = [b'<html>PRIVATE_NON_JSON</html>', b'x' * (MODULE.WEBDRIVER_HTTP_BODY_LIMIT + 1),
                 b'{}', b'[]', b'{"value":null}', b'{"value":{"error":[]}}',
                 b'{"value":{"error":17}}', b'{"value":{"error":"PRIVATE_UNKNOWN"}}',
                 b'{"value":{"error":"unknown error","message":"PRIVATE_UNKNOWN_MESSAGE"}}',
                 b'{"value":{"error":"unknown error","message":[]}}']
        for raw in cases:
            original = MODULE.urllib.error.HTTPError('http://localhost/private', 400, 'Bad Request', {}, io.BytesIO(raw))
            with self.subTest(raw_type=raw[:20]), patch.object(MODULE.urllib.request, 'urlopen', side_effect=original):
                with self.assertRaises(MODULE.urllib.error.HTTPError) as caught:
                    MODULE.Driver(1).request('POST', '/PRIVATE_UNRECOGNIZED?token=PRIVATE_TOKEN')
                self.assertIs(caught.exception, original)
                diagnostic = original.navigation_webdriver_diagnostic
                self.assertEqual(diagnostic['httpStatus'], 400)
                self.assertNotIn('PRIVATE', json.dumps(diagnostic)); self.assertNotIn('body', diagnostic)
                self.assertEqual(diagnostic['truncated'], len(raw) > MODULE.WEBDRIVER_HTTP_BODY_LIMIT)
                if diagnostic['truncated']: self.assertNotIn('error', diagnostic); self.assertNotIn('message', diagnostic)
        class BrokenBody:
            def read(self, size): raise ValueError('PRIVATE_READ_ERROR')
            def close(self): pass
        for failure in ('read', 'decoder'):
            original = MODULE.urllib.error.HTTPError('http://localhost/', 400, 'Bad Request', {}, BrokenBody() if failure == 'read' else io.BytesIO(b'{}'))
            with patch.object(MODULE.urllib.request, 'urlopen', side_effect=original):
                with patch.object(MODULE, 'webdriver_http_diagnostic', side_effect=ValueError('PRIVATE_DECODER_ERROR')) if failure == 'decoder' else patch.object(MODULE.json, 'loads', wraps=MODULE.json.loads):
                    with self.assertRaises(MODULE.urllib.error.HTTPError) as caught: MODULE.Driver(1).request('POST', '/session')
            self.assertIs(caught.exception, original)
            self.assertNotIn('PRIVATE', json.dumps(getattr(original, 'navigation_webdriver_diagnostic', {})))

    def test_current_action_http_error_survives_different_error_during_after_snapshot(self):
        import copy
        errors = [MODULE.urllib.error.HTTPError('http://localhost/', 400, 'Bad Request', {}, io.BytesIO(json.dumps({'value': {'error': code, 'message': code}}).encode()))
                  for code in ('element click intercepted', 'javascript error')]
        native = MODULE.Driver(1)
        class Driver:
            def __init__(self): self.calls = 0
            def js(self, script, *args):
                if script == MODULE.TASK_ROUTE_RETURN_SNAPSHOT_JS:
                    self.calls += 1
                    if self.calls == 1: return {'returnClickDiagnostic': {'before': True}}
                    return native.request('POST', '/session/opaque/execute/sync')
                return {'origin': 'diagnostic'}
            def settle(self): pass
        record, saved = {}, []
        with patch.object(MODULE.urllib.request, 'urlopen', side_effect=errors):
            with self.assertRaises(MODULE.urllib.error.HTTPError) as caught:
                MODULE.transition_record(Driver(), record, lambda: saved.append(copy.deepcopy(record)), 'relation-to-task',
                                         lambda: native.request('POST', '/session/opaque/element/opaque/click'))
        self.assertIs(caught.exception, errors[0])
        phase = saved[-1]['transitions'][0]
        self.assertEqual(phase['webdriverError']['error'], 'element click intercepted')
        self.assertEqual(errors[1].navigation_webdriver_diagnostic['error'], 'javascript error')
        self.assertEqual(errors[0].navigation_webdriver_diagnostic['error'], 'element click intercepted')
        self.assertIn('afterError', phase)
        self.assertEqual(phase['before']['returnClickDiagnostic'], {'before': True})

    def test_return_button_geometry_reports_sticky_hit_without_actions_or_text(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<style>*{display:block;opacity:1;visibility:visible} .np-reader-heading{position:sticky}</style><main id="navigation-product"><div id="np-tree-scroll"></div><aside id="np-detail-scroll"><div id="np-reader-heading" class="np-reader-heading">PRIVATE_HEADER_TEXT</div><section><button id="np-task-route-return" class="np-return" value="PRIVATE_VALUE">PRIVATE_BUTTON_TEXT</button></section></aside></main>',{url:'https://example.org/',runScripts:'outside-only'});
try{const w=dom.window,d=w.document,reader=d.getElementById('np-detail-scroll'),button=d.getElementById('np-task-route-return'),header=d.querySelector('.np-reader-heading');
const rect=(x,y,width,height)=>({x,y,width,height,left:x,top:y,right:x+width,bottom:y+height});let headerHeight=45;
for(const e of d.querySelectorAll('*')){e.getBoundingClientRect=()=>e===button?rect(620,145,300,38):e===header?rect(600,126,808,headerHeight):rect(600,126,808,672);e.getClientRects=()=>[e.getBoundingClientRect()];
for(const [key,value] of Object.entries({clientLeft:0,clientTop:0,clientWidth:808,clientHeight:672,scrollTop:53,scrollLeft:0,scrollHeight:1000}))Object.defineProperty(e,key,{get:()=>value,set:()=>{throw Error('diagnostic write '+key);}});
for(const name of ['click','focus','scrollIntoView'])e[name]=()=>{throw Error('diagnostic action '+name);};}
Object.defineProperties(w,{innerWidth:{value:1440},innerHeight:{value:900},scrollX:{value:0},scrollY:{value:0}});
d.elementFromPoint=(x,y)=>y<126+headerHeight?header:button;d.elementsFromPoint=(x,y)=>[d.elementFromPoint(x,y),reader];
const run=new w.Function(input.script+';return relationReturnClickDiagnostic();'),beforeHTML=d.documentElement.outerHTML,beforeHistory=JSON.stringify(w.history.state),covered=run();
assert.equal(covered.count,1);assert.equal(covered.button.computedVisible,true);assert.equal(covered.points.length,5);assert.equal(covered.points[0].hitsTarget,false);assert.equal(covered.points[0].top.className,'np-reader-heading');assert.equal(covered.points[0].inEffectiveReader,false);
assert.equal(covered.points[3].hitsTarget,true);assert.equal(covered.points[3].inEffectiveReader,true);assert.equal(covered.effectiveReader.y,171);assert.equal(covered.scroll.reader.top,53);
assert.ok(!JSON.stringify(covered).includes('PRIVATE'));assert.equal(d.documentElement.outerHTML,beforeHTML);assert.equal(JSON.stringify(w.history.state),beforeHistory);
headerHeight=20;const clear=run();assert.equal(clear.points[0].hitsTarget,true);assert.equal(clear.points[0].inEffectiveReader,true);
d.getElementById('navigation-product').style.opacity='0';assert.equal(run().button.computedVisible,false);d.getElementById('navigation-product').style.opacity='1';button.disabled=true;assert.equal(run().button.disabled,true);
button.remove();const missing=run();assert.equal(missing.count,0);assert.equal(missing.button,null);assert.deepEqual(JSON.parse(JSON.stringify(missing.points)),[]);
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_ROUTE_DIAGNOSTIC_JS}),
                                cwd=Path(__file__).parents[1], text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_relation_to_task_retains_native_click_wait_and_one_before_after_snapshot(self):
        import ast, inspect
        source = inspect.getsource(MODULE.task_route_checks)
        function = ast.parse(source).body[0]
        calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'transition_record'
                 and len(n.args) > 3 and isinstance(n.args[3], ast.Constant) and n.args[3].value == 'relation-to-task']
        self.assertEqual(len(calls), 1)
        self.assertEqual(ast.unparse(calls[0].args[4]), "lambda: driver.click(driver.selector('#np-task-route-return'))")
        self.assertIn('TASK_OVERVIEW_RETURN_WAIT_JS', ast.unparse(calls[0].args[5]))
        self.assertTrue(MODULE.TASK_OVERVIEW_RETURN_WAIT_JS.endswith(MODULE.TASK_ROUTE_RETURN_WAIT_JS))
        self.assertEqual(MODULE.TASK_ROUTE_RETURN_SNAPSHOT_JS,
                         MODULE.TASK_ROUTE_SNAPSHOT_JS.replace('return {route:s.route,', 'return {returnClickDiagnostic:relationReturnClickDiagnostic(),route:s.route,', 1))
        self.assertNotIn('returnClickDiagnostic:relationReturnClickDiagnostic()', MODULE.TASK_ROUTE_SNAPSHOT_JS)
        class Driver:
            def __init__(self): self.scripts = []; self.actions = 0
            def js(self, script, *args): self.scripts.append(script); return {}
            def settle(self): pass
        driver = Driver()
        MODULE.transition_record(driver, {}, lambda: None, 'relation-to-task', lambda: setattr(driver, 'actions', driver.actions + 1), lambda: True)
        self.assertEqual(driver.actions, 1)
        self.assertEqual(driver.scripts.count(MODULE.TASK_ROUTE_RETURN_SNAPSHOT_JS), 2)
        self.assertNotIn(MODULE.TASK_ROUTE_SNAPSHOT_JS, driver.scripts)



class TaskOverviewReturnChecks(unittest.TestCase):
    @staticmethod
    def snapshots():
        import copy
        route = dict(nav='1', scope='task:category-objectnav', tree='l', node='pos:l:74abdf1c989032e2d82e82',
                     paper=None, version=None, bench=None, protocol=None, template=None, claim=None, mode='tree')
        key = json.dumps([route[k] for k in ('scope', 'bench', 'protocol', 'paper', 'version', 'template')], separators=(',', ':'))
        focus = 'np-task-change-target-task:category-objectnav-methods:relation:90-pos:l:98bc421b8bfd17d6699922'
        view = {'schema': 1, 'lastRouteByTree': {'l': route, 'c': {'tree': 'c', 'node': 'prior-challenge'}},
                'focusTargetByTree': {'l': focus, 'c': 'prior-challenge-focus'}}
        overview = {'l': {'route': route, 'open': True}, 'c': {'route': {'tree': 'c'}, 'open': True}}
        relation = {'l': {'id': 'methods:relation:90', 'route': route}, 'c': None}
        bucket = {'focusTarget': focus, 'taskView': view, 'relationOverviewByTree': overview, 'relationViewByTree': relation,
                  'expandedByTree': {'l': [route['node'], 'prior-group'], 'c': ['prior-challenge']},
                  'treeScrollByTree': {'l': 120, 'c': 83}, 'treeScrollLeftByTree': {'l': 17, 'c': 3},
                  'detailScrollByTree': {'l': 70, 'c': 61}, 'graphScale': 1, 'windowScroll': 88}
        runtime = {'route': route, 'revision': 5, 'contexts': {key: bucket, 'other': {'focusTarget': 'retained'}},
                   'originTrail': [{'route': {'scope': 'scope:all'}, 'bucket': {'focusTarget': 'origin'}}]}
        before = {'route': route, 'position': {'id': route['node'], 'entity': route['scope'], 'kind': 'task'},
                  'selectedRelation': 'methods:relation:90', 'expanded': bucket['expandedByTree'], 'selected': [route['node']],
                  'relationOverview': overview, 'relationView': relation, 'scale': 1, 'treeScroll': {'top': 120, 'left': 17},
                  'readerScroll': {'top': 70, 'left': 0}, 'window': {'x': 0, 'y': 0}, 'focus': focus,
                  'relationDisclosure': {'id': 'np-task-route-relations', 'summary': 'np-task-route-relations-summary', 'open': True,
                                         'beforeTree': True, 'insideTree': False, 'insideTreeScroll': False, 'toolbar': True, 'tag': 'DETAILS', 'current': '5', 'outside': '2'},
                  'readerHidden': False, 'readerLists': 0, 'taskView': view, 'treeCount': 1, 'forestCount': 1,
                  'rovingCount': 1, 'inactiveItemCount': 0, 'runtime': runtime, 'persisted': copy.deepcopy(runtime),
                  'historyEntryKey': 'native-relation-fixture', 'historyLength': 50}
        after = copy.deepcopy(before)
        after.update(focus='np-task-route-relations-summary', selectedRelation=None, historyEntryKey='native-task-fixture')
        after['treeScroll'] = {'top': 0, 'left': 0}; after['readerScroll']['top'] = 0
        after['relationDisclosure']['open'] = False
        after['relationOverview']['l']['open'] = False; after['relationView']['l'] = None
        after['taskView']['focusTargetByTree']['l'] = after['focus']
        after['runtime']['revision'] = 6
        after['runtime']['contexts'][key].update(focusTarget=after['focus'])
        after['runtime']['contexts'][key]['treeScrollByTree']['l'] = 0
        after['runtime']['contexts'][key]['treeScrollLeftByTree']['l'] = 0
        after['runtime']['contexts'][key]['detailScrollByTree']['l'] = 0
        after['persisted'] = copy.deepcopy(after['runtime'])
        back = copy.deepcopy(before); back['focus'] = 'np-task-route-return'
        back['taskView']['focusTargetByTree']['l'] = back['focus']
        back['runtime']['contexts'][key]['focusTarget'] = back['focus']
        back['persisted'] = copy.deepcopy(back['runtime'])
        return before, after, back, copy.deepcopy(after)

    def test_explicit_return_allows_only_collapsed_current_presentation_and_new_entry(self):
        import copy
        before, after, _, _ = self.snapshots()
        MODULE.check_task_overview_return(before, after)
        mutations = [lambda x: x['relationDisclosure'].update(open=True), lambda x: x.update(focus='np-task-change-task:category-objectnav-methods:relation:90'),
                     lambda x: x.update(selectedRelation='methods:relation:90'), lambda x: x['treeScroll'].update(top=1),
                     lambda x: x['treeScroll'].update(left=1), lambda x: x['readerScroll'].update(top=70),
                     lambda x: x['window'].update(y=88), lambda x: x.update(scale=.9), lambda x: x.update(readerHidden=True),
                     lambda x: x.update(readerLists=1), lambda x: x['expanded']['l'].clear(),
                     lambda x: x['relationOverview']['c'].update(open=False), lambda x: x['relationView'].update(c={'id': 'wrong'}),
                     lambda x: x['taskView']['focusTargetByTree'].update(c='stolen'),
                     lambda x: x['taskView']['focusTargetByTree'].update(l='wrong-current-copy'),
                     lambda x: x['taskView']['lastRouteByTree'].update(c={'tree': 'c', 'node': 'changed'}),
                     lambda x: x.update(historyEntryKey=before['historyEntryKey']), lambda x: x.update(historyLength=True)]
        for name in ('runtime', 'persisted'):
            mutations += [lambda x, n=name: x[n].update(revision=True), lambda x, n=name: x[n].update(revision=7),
                          lambda x, n=name: x[n]['contexts']['other'].update(focusTarget='changed'),
                          lambda x, n=name: x[n]['originTrail'][0]['bucket'].update(focusTarget='changed')]
            active_key = next(k for k in before[name]['contexts'] if k != 'other')
            for scroll_field in ('treeScrollByTree', 'treeScrollLeftByTree', 'detailScrollByTree'):
                mutations.append(lambda x, n=name, k=active_key, f=scroll_field: x[n]['contexts'][k][f].update(c=999))
        for field in before['route']:
            mutations.append(lambda x, f=field: x['route'].__setitem__(f, 'changed'))
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(after); mutate(bad)
            with self.subTest(mutation=index), self.assertRaises(RuntimeError): MODULE.check_task_overview_return(before, bad)
        # The actual ae264 failure returned with open=true and focus on this entry.
        # These are recorded values, not a successful image or native traversal fixture.
        old = copy.deepcopy(after); old['relationDisclosure']['open'] = True
        old['focus'] = 'np-task-change-task:category-objectnav-methods:relation:90'
        with self.assertRaisesRegex(RuntimeError, 'collapsed'): MODULE.check_task_overview_return(before, old)

    def test_overview_return_real_back_forward_contract_and_failure_diagnostics(self):
        import copy
        before, collapsed, back, forward = self.snapshots()
        class Driver:
            def __init__(self): self.state = copy.deepcopy(collapsed); self.actions = []; self.waits = []
            def settle(self): pass
            def call(self, method, path, body):
                self.actions.append((method, path, body)); self.state = copy.deepcopy(back if path == '/back' else forward)
            def js(self, script, *args):
                if script == MODULE.TASK_ROUTE_SNAPSHOT_JS: return copy.deepcopy(self.state)
                if script == MODULE.TASK_RELATION_HISTORY_WAIT_JS: self.waits.append(args); return True
                return {}
        driver, record, saved = Driver(), {}, []
        MODULE.task_overview_history_checks(driver, record, lambda: saved.append(copy.deepcopy(record)), before, collapsed)
        self.assertEqual(driver.actions, [('POST', '/back', {}), ('POST', '/forward', {})])
        self.assertEqual(driver.waits[0], (before['route'], 'np-task-route-return', before))
        self.assertEqual(driver.waits[1], (collapsed['route'], 'np-task-route-relations-summary', collapsed))
        for index in range(2):
            self.assertIn('before', saved[-1]['transitions'][index]); self.assertIn('after', saved[-1]['transitions'][index])
        for mutation in ('open', 'focus', 'scroll', 'neutral', 'other', 'origin', 'revision'):
            original = copy.deepcopy(back)
            if mutation == 'open': back['relationDisclosure']['open'] = False
            elif mutation == 'focus': back['focus'] = 'np-task-route-relations-summary'
            elif mutation == 'scroll': back['readerScroll']['top'] = 0
            elif mutation == 'neutral': back['taskView']['focusTargetByTree']['l'] = 'wrong'
            elif mutation == 'other': back['runtime']['contexts']['other']['focusTarget'] = 'wrong'
            elif mutation == 'origin': back['runtime']['originTrail'] = []
            else: back['runtime']['revision'] = 6
            with self.subTest(back_mutation=mutation), self.assertRaises(RuntimeError):
                MODULE.task_overview_history_checks(Driver(), {}, lambda: None, before, collapsed)
            back.clear(); back.update(original)
        for mutate in (lambda x: x['relationDisclosure'].update(open=True),
                       lambda x: x.update(focus='np-task-route-return'),
                       lambda x: x['treeScroll'].update(top=120),
                       lambda x: x['runtime']['contexts']['other'].update(focusTarget='changed')):
            original = copy.deepcopy(forward); mutate(forward)
            with self.assertRaises(RuntimeError):
                MODULE.task_overview_history_checks(Driver(), {}, lambda: None, before, collapsed)
            forward.clear(); forward.update(original)
        failure = TimeoutError('original traversal failure'); record = {}; saved = []
        with patch.object(MODULE, 'wait_for', side_effect=failure), self.assertRaises(TimeoutError) as caught:
            MODULE.task_overview_history_checks(Driver(), record, lambda: saved.append(copy.deepcopy(record)), before, collapsed)
        self.assertIs(caught.exception, failure); self.assertIn('after', saved[-1]['transitions'][0])

    def test_overview_ready_and_scene_keep_original_scientific_wait_native_click_and_visible_tree(self):
        import ast, inspect
        source = inspect.getsource(MODULE.task_route_checks); function = ast.parse(source).body[0]
        calls = [n for n in ast.walk(function) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        action = next(n for n in calls if n.func.id == 'transition_record' and len(n.args) > 3 and isinstance(n.args[3], ast.Constant) and n.args[3].value == 'relation-to-task')
        self.assertEqual(ast.unparse(action.args[4]), "lambda: driver.click(driver.selector('#np-task-route-return'))")
        self.assertIn('TASK_OVERVIEW_RETURN_WAIT_JS', ast.unparse(action.args[5]))
        scene = next(n for n in calls if n.func.id == 'scene' and isinstance(n.args[0], ast.Constant) and n.args[0].value == '-26-return-objectnav-task')
        self.assertEqual(len(scene.args[1].elts), 2); self.assertIn('tree_label_selector', ast.unparse(scene.args[1]))
        self.assertIn("science['positions']", ast.unparse(scene.args[1])); self.assertEqual(ast.literal_eval(scene.keywords[0].value), False)
        self.assertIn("require_tree=specs[0].get('region') == 'canvas'", source)
        self.assertTrue(MODULE.TASK_OVERVIEW_RETURN_WAIT_JS.endswith(MODULE.TASK_ROUTE_RETURN_WAIT_JS))
        script = r"""
const assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
let open=false,selected=false,focus='np-task-route-relations-summary',ready=true,state='ready';const route=input.route;
global.NavigationProductApp={getState:()=>({route}),getContent:()=>({ready:()=>ready}),getBundle:()=>({positions:{[route.node]:{entityId:'task:category-objectnav'}}})};
global.document={activeElement:{get id(){return focus;}},getElementById:()=>({get open(){return open;}}),querySelector:q=>q==='[data-task-route-scope]'?{dataset:{taskRouteState:state}}:q==='[data-selected-task-relation]'&&selected?{}:null};
const run=new Function(input.script);assert.equal(!!run(route,focus),true);
open=true;assert.equal(run(route,focus),false);open=false;selected=true;assert.equal(run(route,focus),false);selected=false;
focus='wrong';assert.equal(!!run(route,'np-task-route-relations-summary'),false);focus='np-task-route-relations-summary';ready=false;assert.equal(!!run(route,focus),false);ready=true;
for(const key of Object.keys(route)){const wrong={...route,[key]:'wrong'};assert.equal(!!run(wrong,focus),false);}
state='loading';assert.equal(!!run(route,focus),false);
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.TASK_OVERVIEW_RETURN_WAIT_JS, 'route': self.snapshots()[0]['route']}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_production_explicit_return_and_history_restore_distinct_overview_presentations(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
await scope('task:category-objectnav');const overview=d.getElementById('np-task-route-relations');overview.querySelector('summary').click();await ready(()=>overview.open);
let relationButton=d.querySelector('[data-task-change="methods:relation:90"]');relationButton.focus();relationButton.click();await ready(()=>d.querySelector('[data-selected-task-relation="methods:relation:90"]')&&d.querySelector('[data-relation-state]')?.dataset.relationState==='ready');
const before=snapshot(),button=d.getElementById('np-task-route-return');button.focus();button.click();await ready(()=>new w.Function(input.returnWait)(before.route,'np-task-route-relations-summary'));
const collapsed=snapshot();states.push(before,collapsed);assert.equal(d.getElementById('np-task-route-relations').open,false);assert.equal(label(before.route.node).textContent,s.positions[before.route.node].label);
w.history.back();await ready(()=>d.querySelector('[data-selected-task-relation="methods:relation:90"]')&&d.activeElement.id==='np-task-route-return');states.push(snapshot());
w.history.forward();await ready(()=>new w.Function(input.returnWait)(before.route,'np-task-route-relations-summary'));states.push(snapshot());
"""
        before, collapsed, back, forward = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science), 'returnWait': MODULE.TASK_OVERVIEW_RETURN_WAIT_JS})
        # JSDOM exercises actual product push/back/forward state, not native Navigation API keys or layout.
        self.assertIsNone(before['historyEntryKey']); self.assertIsNone(collapsed['historyEntryKey'])
        self.assertFalse(before['relationDisclosure']['open']); self.assertFalse(collapsed['relationDisclosure']['open'])
        self.assertEqual(back['selectedRelation'], 'methods:relation:90'); self.assertEqual(back['focus'], 'np-task-route-return')
        self.assertFalse(back['relationDisclosure']['open']); self.assertFalse(forward['relationDisclosure']['open'])
        for original, restored in ((before, back), (collapsed, forward)):
            MODULE.check_exploration_restore(original, restored, focus=restored['focus'])
        # Unit keys only let the same strict state validator inspect these real DOM/model snapshots.
        before['historyEntryKey'] = 'unit-before'; collapsed['historyEntryKey'] = 'unit-collapsed'
        MODULE.check_task_overview_return(before, collapsed)


class DefaultOverviewMaterializationChecks(unittest.TestCase):
    @staticmethod
    def real_fixture():
        import base64, gzip, hashlib
        # b988 receipt SHA256 6dd0739e2d7d095192da3d0fc7653b2872f4deffbb1dc0cf3750c8df0be0b1f5.
        # Unmodified projection of select transition 26 before/origin and return 27 after;
        # source forest roots come from the pinned raw export. No invented browser measurement.
        raw = gzip.decompress(base64.b64decode('H4sIAAAAAAACA+1WzW4TMRB+F58TaTfJbn5uoHKIVIHURFyqKvLas4lVZ73yetNGVS5woJx4gHLgzAG4IlW8TSi3vgJj726TQkIAcaBVL4m9nhnPfDPfeM4IjQ1o0jsjcJrShAO3a0p6h0c1wvCPpCrrsR40WBRFrMGCsBOx2O+G3RZtEBQaF7KykpU9v+l1At6OuxQiz4tbkR81WyGplcc8jPx2A+IwonEYQxuazTblN8chb3egAQH3vJB7LQianaDTJkeLGokVyzPSI0laTxSHeqHAOhxQtuV1oOt5QaPpQcA61h5NQA6YSgF1DM2Oe2JKx5DQWXGZMEIlLvTECDPfICQQjV1BHYuEl6ruztTCmeRS1ki25W6jwX6WuJyBzpwXVgND1EA56AHTSkrrmoTYkJ6HOirFfychqXV8T2RMqizXYOUiiJWGoTNsdA6YvFxrDAzv8atIEDfrSl2r3EC9MpTZ4yQTvFSPqcxQH11PVpvcWIHSWJZPp1TPt1usVxLoN8UCIXtPho/6+wOy5v8zDH0m4MRFaX9uXegMFoElbFIByiQV02ozVc4hB2aNWGQL75Li+65aXE9UqpVRTMmdiYNpit5DJbc1kYvFnQ/BmqASz3xcgQRmgB+UuVtX3larfogmTpAcyqX41J1gzfh+YNEpCvZON55fJOah8dyJxvPA0h0sVVqMhSvVKGfHYOyKg6FCFgYfz4vUOeZ6jrieY6bniGnLpqL3LdH/luRDqsc2TLJjthhrmk4GN9CnVFMpS9IfIJXmFRt+rLoVDPfy0atq8Fa2yziqxbhayF0eL2rOm+flmLCWoZV99rO1LVlDa5Jm5sCivFn/ziJvbUxgilj7i3XC7+CnY/9Keh9bw28wumgXVUexneIetNGHOvvTOnNZVwbnokMslixTTJTPDuFCYxdAdTYRkvd5tmrff9mfS5AKU7jjkJqJK8pihurzfzJFSRqBzW/fGnlKZ9eX58u3n65efF5efFm+fHN18eHru1fLj5ffzt9fX74m9oHkFm+vRN66UWJP7RC02lfvwHDuUuBSMbJDl0jGI5R0M4v7ujGUzFDjRlAnwkcimaGS0vMRzHA+ShhsHO+q+xdHi++6ovGW6w8AAA=='))
        assert hashlib.sha256(raw).hexdigest() == 'ab1e3f12fe5f05b45c8e34f538500b256105139c95dafe16db34ec853b234d98'
        data = json.loads(raw)
        # The clicked label has no ID; the existing selector records its real treeitem ID.
        data['before']['activatedControl'] = 'np-node-' + data['origin']['bucket']['focusTarget']
        # Raw receipt bytes remain pinned above. Only the explicitly superseded
        # outer-scroll/placement display fields are projected to the new shell.
        data['legacyDisplay'] = {phase: {'window': data[phase]['window'].copy(), 'disclosure': data[phase]['relationDisclosure'].copy()} for phase in ('before', 'after')}
        for phase in ('before', 'after'):
            data[phase]['window'] = {'x': 0, 'y': 0}
            data[phase]['relationDisclosure'].update(insideTreeScroll=False, toolbar=True)
        return data

    def test_real_b988_closed_origin_materialization_preserves_original_evidence(self):
        import copy
        f = self.real_fixture(); before = f['before']; original = copy.deepcopy(before)
        self.assertEqual(before['relationOverview'], {})
        self.assertEqual(before['relationDisclosure'], f['after']['relationDisclosure'])
        self.assertEqual(before['treeScroll'], {'left': 0, 'top': 16})
        with self.assertRaisesRegex(RuntimeError, 'relationOverview'):
            MODULE.check_task_route_return(before, f['after'], before['activatedControl'])
        expected = MODULE.task_route_origin_overview(before, f['origin'], f['roots'])
        self.assertEqual(expected, {'l': {'route': before['route'], 'open': False}})
        self.assertEqual(before, original)
        proof = copy.deepcopy(before)
        proof['expectedOverviewMaterialization'] = {'overview': expected, 'sourceRoots': f['roots']}
        proof['actualOrigin'] = f['origin']
        MODULE.check_task_route_return(proof, f['after'], before['activatedControl'])
        self.assertEqual(proof['relationOverview'], {})
        self.assertEqual(f['after']['relationOverview'], f['origin']['bucket']['relationOverviewByTree'])

    def test_materialization_rejects_wrong_route_open_existing_null_or_inactive_changes(self):
        import copy
        base = self.real_fixture()
        mutations = [lambda f: f['before']['relationOverview'].update(l=None),
                     lambda f: f['before']['relationOverview'].update(l={'route': f['before']['route'], 'open': True}),
                     lambda f: f['before']['relationDisclosure'].update(open=True),
                     lambda f: f['before']['relationDisclosure'].update(open=0),
                     lambda f: f['before']['relationDisclosure'].update(tag='DIV'),
                     lambda f: f['before']['relationDisclosure'].update(insideTree=True),
                     lambda f: f['before'].update(selectedRelation='methods:relation:90'),
                     lambda f: f['before']['position'].update(id='other-root'),
                     lambda f: f['before']['position'].update(kind='pipeline_recipe'),
                     lambda f: f.update(roots=[]),
                     lambda f: f['origin']['bucket']['relationOverviewByTree']['l'].update(open=True),
                     lambda f: f['origin']['bucket']['relationOverviewByTree']['l'].update(open=0),
                     lambda f: f['origin']['bucket']['relationOverviewByTree'].update(c={'route': {}, 'open': False}),
                     lambda f: f['before']['relationOverview'].update(c={'route': {'tree': 'c'}, 'open': True})]
        for field in base['before']['route']:
            mutations.append(lambda f, k=field: f['origin']['bucket']['relationOverviewByTree']['l']['route'].__setitem__(k, 'wrong'))
            mutations.append(lambda f, k=field: f['origin']['route'].__setitem__(k, 'wrong'))
        for index, mutate in enumerate(mutations):
            f = copy.deepcopy(base); mutate(f)
            with self.subTest(mutation=index), self.assertRaises(RuntimeError):
                MODULE.task_route_origin_overview(f['before'], f['origin'], f['roots'])
        f = copy.deepcopy(base)
        inactive = {'route': {'scope': 'task:imagenav', 'tree': 'c', 'node': 'saved'}, 'open': True}
        f['before']['relationOverview']['c'] = copy.deepcopy(inactive)
        f['origin']['bucket']['relationOverviewByTree']['c'] = copy.deepcopy(inactive)
        expected = MODULE.task_route_origin_overview(f['before'], f['origin'], f['roots'])
        self.assertEqual(expected['c'], inactive)
        for field in ('route', 'open'):
            bad = copy.deepcopy(f); del bad['origin']['bucket']['relationOverviewByTree']['c'][field]
            with self.assertRaises(RuntimeError): MODULE.task_route_origin_overview(bad['before'], bad['origin'], bad['roots'])
        # An existing map has no default exception: exact fields are retained, including extension fields.
        f['before']['relationOverview'] = copy.deepcopy(f['origin']['bucket']['relationOverviewByTree'])
        f['before']['relationOverview']['l']['existingField'] = 'retained'
        f['origin']['bucket']['relationOverviewByTree']['l']['existingField'] = 'retained'
        self.assertEqual(MODULE.task_route_origin_overview(f['before'], f['origin'], f['roots']), f['before']['relationOverview'])
        del f['origin']['bucket']['relationOverviewByTree']['l']['existingField']
        with self.assertRaises(RuntimeError): MODULE.task_route_origin_overview(f['before'], f['origin'], f['roots'])

    def test_return_rechecks_proven_origin_and_retains_all_old_strict_fields(self):
        import copy
        f = self.real_fixture(); before = f['before']; control = before['activatedControl']
        before['expectedOverviewMaterialization'] = {'overview': MODULE.task_route_origin_overview(before, f['origin'], f['roots']), 'sourceRoots': f['roots']}
        before['actualOrigin'] = f['origin']
        for field in ('route', 'panelScope', 'scale', 'readerScroll', 'treeScroll', 'window', 'selectedRelation', 'expanded', 'relationOverview', 'focus'):
            bad = copy.deepcopy(f['after']); bad[field] = 'wrong-relation' if field == 'selectedRelation' else None
            with self.subTest(field=field), self.assertRaises(RuntimeError): MODULE.check_task_route_return(before, bad, control)
        bad = copy.deepcopy(f['after']); bad['relationDisclosure']['open'] = True
        with self.assertRaises(RuntimeError): MODULE.check_task_route_return(before, bad, control)
        for mutate in (lambda b: b['expectedOverviewMaterialization']['overview']['l'].update(open=True),
                       lambda b: b['actualOrigin']['bucket']['relationOverviewByTree']['l'].update(open=True),
                       lambda b: b['expectedOverviewMaterialization'].update(sourceRoots=[])):
            bad = copy.deepcopy(before); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_task_route_return(bad, f['after'], control)

    def test_raw_portable_setting_root_is_exact_and_nonroot_setting_is_rejected(self):
        import copy, gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        sid = 'setting:portable-objectnav'
        roots = [science['positions'][pid] for pid in science['forests'][sid]['l']]
        self.assertEqual(len(roots), 1); root = roots[0]
        self.assertEqual(root['kind'], 'setting'); self.assertIsNone(root['parentId'])
        # Real immutable raw root identity in a unit disclosure fixture, not a new browser screenshot.
        f = self.real_fixture(); before = f['before']
        before['route'].update(scope=sid, node=root['id']); before['panelScope'] = sid
        before['position'] = {key: root[value] for key, value in
            {'id': 'id', 'entity': 'entityId', 'scope': 'scopeId', 'tree': 'tree', 'paper': 'paperId', 'version': 'versionId', 'kind': 'kind'}.items()}
        origin = {'route': copy.deepcopy(before['route']), 'bucket': {'relationOverviewByTree': {
            'l': {'route': copy.deepcopy(before['route']), 'open': False}}}}
        expected = MODULE.task_route_origin_overview(before, origin, roots)
        self.assertEqual(expected, origin['bucket']['relationOverviewByTree'])
        for field in ('entity', 'kind'):
            bad = copy.deepcopy(before); bad['position'][field] = 'wrong'
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                MODULE.task_route_origin_overview(bad, origin, roots)
        child = science['positions'][root['childIds'][0]]
        bad = copy.deepcopy(before); bad['route']['node'] = child['id']
        bad['position'].update(id=child['id'], entity=child['entityId'], kind='setting')
        bad_origin = copy.deepcopy(origin); bad_origin['route'] = copy.deepcopy(bad['route'])
        bad_origin['bucket']['relationOverviewByTree']['l']['route'] = copy.deepcopy(bad['route'])
        with self.assertRaises(RuntimeError): MODULE.task_route_origin_overview(bad, bad_origin, roots)
        forged_root = copy.deepcopy(child); forged_root['kind'] = 'setting'
        with self.assertRaises(RuntimeError): MODULE.task_route_origin_overview(bad, bad_origin, [forged_root])

    def test_select_records_unmodified_origin_and_proposal_before_rejecting_bad_materialization(self):
        import ast, copy, inspect
        source = inspect.getsource(MODULE.task_route_checks); function = ast.parse(source).body[0]
        select = next(n for n in function.body if isinstance(n, ast.FunctionDef) and n.name == 'select_method')
        returned = next(n for n in function.body if isinstance(n, ast.FunctionDef) and n.name == 'return_method')
        # Only post-click proof is new: native action and original exact ready/wait/scroll path remain.
        self.assertIn('lambda: driver.click(element)', ast.unparse(select))
        self.assertIn('a.getContent().ready(p.entityId)', ast.unparse(select))
        self.assertIn("lambda: driver.click(driver.selector('.np-return-previous'))", ast.unparse(returned))
        self.assertIn('TASK_ROUTE_RETURN_WAIT_JS', ast.unparse(returned))
        for bad_origin in (False, True):
            f = self.real_fixture(); before = f['before']; original = copy.deepcopy(before)
            if bad_origin: f['origin']['bucket']['relationOverviewByTree']['l']['open'] = True
            phase, saved = {'origin': f['origin'], 'before': copy.deepcopy(before)}, []
            paint_calls = []; test = self
            class Driver:
                def call(self, method, path, data):
                    test.assertEqual((method, path), ('POST', '/execute/async'))
                    test.assertEqual(data, dict(script=MODULE.DESKTOP_CHROME_PAINT_SETTLE_JS, args=[2000]))
                    paint_calls.append(data)
                    return dict(status='settled', scopeSelector=MODULE.DESKTOP_CHROME_PAINT_SELECTOR,
                                timeoutMs=2000, elapsedMs=32, before={'colors': []}, after={'colors': []})
                def js(self, script, element=None):
                    if script == MODULE.DESKTOP_SHELL_SNAPSHOT_JS: return {'geometry': 'original-source-layout'}
                    return before['activatedControl'] if "[role=treeitem]" in script else f['origin']['bucket']['focusTarget']
            env = dict(driver=Driver(), snapshot=lambda: before, reveal_control=lambda *args: 'element',
                       expose_source_position=lambda *args: 'element', record={}, save=lambda: saved.append(copy.deepcopy(phase)),
                       transition_record=lambda *args: phase, json=json, MODULE=MODULE, report={}, prefix='1440x900',
                       desktop_chrome_snapshot=MODULE.desktop_chrome_snapshot,
                       DESKTOP_SHELL_SNAPSHOT_JS=MODULE.DESKTOP_SHELL_SNAPSHOT_JS,
                       task_route_origin_overview=MODULE.task_route_origin_overview,
                       science={'forests': {before['route']['scope']: {'l': [p['id'] for p in f['roots']]}},
                                'positions': {p['id']: p for p in f['roots']}})
            exec(compile(ast.Module(body=[select], type_ignores=[]), '<actual-select-method>', 'exec'), env)
            if bad_origin:
                with self.assertRaises(RuntimeError): env['select_method']({'id': 'target'})
                self.assertFalse(saved[-1]['overviewMaterialization']['validated'])
            else:
                result = env['select_method']({'id': 'target'})
                self.assertTrue(saved[-1]['overviewMaterialization']['validated'])
                MODULE.check_task_route_return(result, f['after'], result['activatedControl'])
            self.assertEqual(len(paint_calls), 1)
            self.assertEqual(env['report']['desktopChromePaintSettles'][0]['scope'], 'desktop-workspace-toolbar')
            self.assertEqual(env['report']['desktopChromePaintSettles'][0]['phase'], '1440x900-method-origin')
            self.assertEqual(phase['before'], original)
            self.assertEqual(before['relationOverview'], {})
            self.assertEqual(saved[-1]['desktopShellBefore'], {'geometry': 'original-source-layout'})
            evidence = next(item['overviewMaterialization'] for item in saved if 'overviewMaterialization' in item)
            self.assertEqual(evidence['beforeOverview'], {})
            self.assertEqual(evidence['expectedOverview'], {'l': {'route': original['route'], 'open': False}})
            self.assertEqual(evidence['actualOriginOverview'], f['origin']['bucket']['relationOverviewByTree'])


class DelayedRequestFixtureChecks(unittest.TestCase):
    def test_cache_control_restores_default_on_every_failure_and_preserves_original(self):
        import copy
        for failure in (None, 'enable', 'refresh', 'wait', 'disable', 'refresh-disable', 'entry-save', 'exit-save', 'hold-diagnostic'):
            calls, saved, record = [], [], {}
            primary = RuntimeError('original failure'); cleanup = RuntimeError('cleanup failure')
            class Driver:
                def cdp(self, command, params):
                    calls.append((command, params))
                    if params['cacheDisabled'] and failure == 'enable': raise primary
                    if not params['cacheDisabled'] and failure in ('disable', 'refresh-disable'): raise cleanup
            class Hold:
                def diagnostic(self):
                    if failure == 'hold-diagnostic': raise cleanup
                    return {'seen': True, 'events': [{'event': 'armed', 'elapsedMs': 0}]}
            def save():
                saved.append(copy.deepcopy(record))
                if failure == 'entry-save' and not record['cacheControl']['restoreAttempted']: raise primary
                if failure == 'exit-save' and record['cacheControl']['restoreAttempted']: raise cleanup
            def run():
                with MODULE.DelayedRequestCacheControl(Driver(), record, save, Hold()):
                    calls.append(('refresh', {}))
                    if failure in ('refresh', 'wait', 'refresh-disable'): raise primary
            with self.subTest(failure=failure):
                if failure:
                    with self.assertRaises(RuntimeError) as caught: run()
                    self.assertIs(caught.exception, primary if failure in ('enable', 'refresh', 'wait', 'refresh-disable', 'entry-save') else cleanup)
                else: run()
            self.assertEqual(calls[0], ('Network.setCacheDisabled', {'cacheDisabled': True}))
            self.assertEqual(calls[-1], ('Network.setCacheDisabled', {'cacheDisabled': False}))
            if failure in ('enable', 'entry-save'): self.assertNotIn(('refresh', {}), calls)
            state = record['cacheControl']; self.assertTrue(state['disableAttempted']); self.assertTrue(state['restoreAttempted'])
            self.assertEqual(state['restoreAcknowledged'], failure not in ('disable', 'refresh-disable'))
            self.assertTrue(saved)

    def test_real_loopback_hold_records_exact_get_and_conditional304_before_release(self):
        import concurrent.futures, functools, hashlib, http.server, tempfile, threading, urllib.request, urllib.error
        with tempfile.TemporaryDirectory() as directory:
            dist = Path(directory); raw = b'{"public":"pinned request fixture"}'; digest = hashlib.sha256(raw).hexdigest()
            path = '/research/navigation/content/' + digest + '.json'; packet = dist / path.lstrip('/')
            packet.parent.mkdir(parents=True); packet.write_bytes(raw)
            server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(MODULE.QuietHandler, directory=str(dist)))
            thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
            def get(requested, headers=None):
                try: response = urllib.request.urlopen(urllib.request.Request('http://127.0.0.1:' + str(server.server_port) + requested, headers=headers or {}), timeout=2)
                except urllib.error.HTTPError as exc: response = exc
                with response: return response.status, response.headers.get('Last-Modified'), response.read()
            try:
                status, modified, body = get(path); self.assertEqual((status, body), (200, raw))
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    for requested, headers, wanted in ((path, {}, 200), (path + '?not-recorded=private', {}, 200), (path, {'If-Modified-Since': modified}, 304)):
                        with MODULE.PacketHold(server, path, dist, digest) as hold:
                            task = pool.submit(get, requested, headers)
                            self.assertTrue(hold.seen.wait(1)); self.assertFalse(task.done())
                            hold.note('planned-release'); hold.released.set(); self.assertEqual(task.result(timeout=2)[0], wanted)
                            MODULE.wait_for(lambda: any(e['event'] == 'request-finished' for e in hold.diagnostic()['events']), timeout=1)
                        diagnostic = hold.diagnostic(); events = diagnostic['events']; names = [row['event'] for row in events]
                        self.assertLess(names.index('armed'), names.index('seen')); self.assertLess(names.index('seen'), names.index('held'))
                        self.assertLess(names.index('planned-release'), names.index('response')); self.assertIn('release-observed', names)
                        self.assertIn('request-finished', names); self.assertEqual(next(e['status'] for e in events if e['event'] == 'response'), wanted)
                        self.assertEqual(diagnostic['requestCount'], 1)
                        self.assertTrue(all(e['request'] == 1 for e in events if e['event'] in ('seen', 'held', 'release-observed', 'response', 'request-finished')))
                        self.assertEqual([e['elapsedMs'] for e in events], sorted(e['elapsedMs'] for e in events))
                        self.assertFalse(diagnostic['expired']); self.assertEqual(diagnostic['path'], path)
                        self.assertNotIn('private', json.dumps(diagnostic)); self.assertNotIn('headers', json.dumps(diagnostic))
                with MODULE.PacketHold(server, path, dist, digest) as hold:
                    for _ in range(40): hold.note('unit-event')
                    self.assertEqual(len(hold.diagnostic()['events']), 32); self.assertTrue(hold.diagnostic()['truncated'])
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=2)

    def test_target_resource_diagnostic_is_read_only_bounded_and_omits_other_urls(self):
        script = r"""
const assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8')),sha='a'.repeat(64),origin='http://127.0.0.1:1000';
global.window=global;global.location={href:origin+'/research/navigation/#PRIVATE_HASH',origin};global.document={readyState:'complete'};
const target={name:origin+'/research/navigation/content/'+sha+'.json?PRIVATE_QUERY',initiatorType:'fetch',startTime:3,duration:12,transferSize:0,encodedBodySize:16084,decodedBodySize:16084,responseStatus:200,deliveryType:'cache',workerStart:0,PRIVATE_FIELD:'PRIVATE_DATA'};
const entries=Array.from({length:10},()=>({...target}));entries.push({...target,name:'https://outside.test/'+sha+'.json?PRIVATE_OTHER'});entries.push({...target,name:origin+'/other/PRIVATE_ROUTE'});
global.performance={timeOrigin:1000,now:()=>17,getEntriesByType:k=>k==='navigation'?[{type:'reload'}]:entries,clearResourceTimings:()=>{throw Error('must not clear');}};
global.NavigationProductApp={getBundle:()=>({delivery:{packets:{poni:{sha256:sha}}}}),getContent:()=>({ready:()=>true,status:()=> 'ready',diagnostics:()=>({phase:'ready',elapsedMs:7,receivedBytes:16084,expectedBytes:16084,attempt:1,PRIVATE_FIELD:'PRIVATE_DATA'})})};
const result=new Function(input.script)(sha,'poni');assert.equal(result.resources.length,8);assert.equal(result.resourceEntryCount,10);assert.equal(result.resourceEntriesTruncated,true);assert.equal(result.ownerPacketMatches,true);assert.equal(result.resources[0].deliveryType,'cache');assert.equal(result.resources[0].transferSize,0);assert.equal(result.navigationType,'reload');
assert.ok(!JSON.stringify(result).includes('PRIVATE'));assert.ok(!JSON.stringify(result).includes('http'));assert.throws(()=>new Function(input.script)('wrong','poni'),/identity/);
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.DELAYED_PACKET_DIAGNOSTIC_JS}), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_delay_keeps_original_bounds_actions_and_separate_normal_cache_cold_checks(self):
        import ast, inspect
        source = inspect.getsource(MODULE.task_route_checks)
        self.assertIn("for interrupt in ('none', 'wheel', 'scope'):", source)
        self.assertIn("as hold, DelayedRequestCacheControl(driver, delayed, save, hold):", source)
        self.assertIn("driver.call('POST', '/refresh', {})", source)
        self.assertIn("wait_for(lambda: hold.seen.is_set(), timeout=5)", source)
        self.assertIn("dataset.relationState==='loading'\"), timeout=5)", source)
        self.assertIn("if hold.expired:", source); self.assertIn("check_exploration_restore(delayed['before'], delayed['after'])", source)
        self.assertIn("for key in ('route', 'treeScroll', 'readerScroll', 'window', 'focus', 'taskView'):", source)
        self.assertIn('hold.released.wait(8)', inspect.getsource(MODULE.QuietHandler.do_GET))
        for name in ('cold_relation_refresh', 'cold_relation_refresh_comparison'):
            self.assertNotIn('CacheControl', inspect.getsource(getattr(MODULE, name)))
            self.assertNotIn('setCacheDisabled', inspect.getsource(getattr(MODULE, name)))
        stages = ('refresh-start', 'refresh-return', 'seen-confirmed', 'loading-confirmed', 'planned-release')
        for stage in stages: self.assertIn("hold.note('" + stage + "')", source)
        tree = ast.parse(source)
        contexts = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'DelayedRequestCacheControl']
        self.assertEqual(len(contexts), 1)



class DesktopHierarchyContractChecks(unittest.TestCase):
    @staticmethod
    def shell(tree='l', width=1440, layout_width=None):
        import copy
        height = 900 if width == 1440 else 1080
        def rect(x, y, w, h): return dict(x=x, y=y, width=w, height=h)
        def proof(r, text): return dict(rect=r, text=text, visible=True, opaque=True, unscaled=True, clipped=False,
                                       fontSize=15, foreground=[20, 30, 40], background=[255, 255, 255])
        gap = 24 if tree == 'a' else 16
        layout_width = layout_width or width
        route = {'tree': tree}
        tw = (400 if width == 1440 else 448) if tree == 'a' else (layout_width - 32 - gap) * 1.1 / 2.1
        pane = rect(16 + tw + gap, 132, layout_width - 32 - tw - gap, height - 148)
        return {'chrome': desktop_chrome_fixture(layout_width, height, route=route), 'stationaryAncestors': [{'selector': selector, 'top': 0, 'left': 0} for selector in MODULE.STATIONARY_SHELL_SELECTORS],
                'ready': 'ready', 'route': route, 'methodReading': 'false', 'readingLayout': 'browse', 'position': None, 'window': {'x': 0, 'y': 0},
                'viewport': rect(0, 0, width, height), 'home': False, 'collapsed': False,
                'panels': rect(16, 132, layout_width - 32, height - 148), 'treePane': rect(16, 132, tw, height - 148),
                'tree': rect(17, 176, tw - 2, height - 217), 'pane': pane,
                'reader': rect(pane['x'] + 1, 228, pane['width'] - 2, height - 245),
                'heading': proof(rect(pane['x'] + 1, 133, pane['width'] - 2, 95), 'Object · version'),
                'title': proof(rect(pane['x'] + 12, 144, pane['width'] - 24, 32), 'Object'),
                'meta': proof(rect(pane['x'] + 12, 185, pane['width'] - 24, 22), 'Exact version'),
                'headingInsideScroll': False, 'pickerInsideTree': False, 'pickerInToolbar': True,
                'permanentScrollIds': ['np-tree-scroll', 'np-detail-scroll'],
                'offsets': {'tree': {'top': 0, 'left': 0}, 'reader': {'top': 0, 'left': 0}},
                'rootRows': [], 'routeRows': [], 'relation': None, 'visibleTaskDefinitions': 0,
                'titleRelation': None, 'returnControlCount': 0, 'returnControl': None, 'treeFooter': None}

    def test_chrome_budget_measures_new_top_gutter_and_original_pane_ratios(self):
        import copy
        for width in (1440, 1920):
            for tree in ('l', 'c', 'a'):
                data = self.shell(tree, width, layout_width=width - 15)
                # Engines may report the root client box with or without the
                # reserved stable gutter. The body still measures actual width.
                data['chrome']['rootClientWidth'] = width
                # The source panes move below an independently measured larger toolbar.
                data['chrome']['bar']['rect']['height'] += 57
                data['chrome']['bar']['clientRect']['height'] += 57
                for key in ('panels', 'treePane', 'tree', 'pane', 'reader'):
                    data[key]['y'] += 57; data[key]['height'] -= 57
                for key in ('heading', 'title', 'meta'): data[key]['rect']['y'] += 57
                MODULE.check_desktop_shell(data)
                self.assertEqual(data['panels']['y'], 189)
                for mutate in (lambda d: d.pop('chrome'), lambda d: d['chrome'].update(topology=False),
                               lambda d: d['chrome']['header']['rect'].update(height=100),
                               lambda d: d['chrome']['app']['rect'].update(height=100),
                               lambda d: d['chrome']['bar']['rect'].update(height=800),
                               lambda d: d['chrome']['identity'].update(opaque=False),
                               lambda d: d['chrome']['start'].update(unscaled=False),
                               lambda d: d['chrome']['workspace'].update(top=1),
                               lambda d: d['chrome']['body'].update(marginLeft=15),
                               lambda d: d['chrome']['body']['rect'].update(width=width),
                               lambda d: d['panels'].update(width=width - 32)):
                    bad = copy.deepcopy(data); mutate(bad)
                    with self.subTest(width=width, tree=tree), self.assertRaises(RuntimeError): MODULE.check_desktop_shell(bad)

    def test_fixed_desktop_shell_rejects_outer_scroll_hidden_version_third_scroll_and_old_columns(self):
        import copy
        for width in (1440, 1920):
            for tree in ('l', 'c', 'a'):
                good = self.shell(tree, width)
                MODULE.check_desktop_shell(good)
                mutations = [lambda d: d['window'].update(y=88), lambda d: d['window'].update(x=1),
                             lambda d: d['panels'].update(y=180), lambda d: d['panels'].update(height=200),
                             lambda d: d.update(pickerInsideTree=True), lambda d: d.update(pickerInToolbar=False),
                             lambda d: d.update(headingInsideScroll=True),
                             lambda d: d['permanentScrollIds'].append('nested-detail-scroll'),
                             lambda d: d['meta'].update(visible=False), lambda d: d['meta'].update(clipped=True),
                             lambda d: d['meta'].update(fontSize=14), lambda d: d['meta'].update(text=''),
                             lambda d: d['meta'].update(foreground=[250, 250, 250]),
                             lambda d: d['title'].update(unscaled=False), lambda d: d['title']['rect'].update(y=-20),
                             lambda d: d['treePane'].update(width=1100), lambda d: d['pane'].update(width=720)]
                for index, mutate in enumerate(mutations):
                    bad = copy.deepcopy(good); mutate(bad)
                    with self.subTest(width=width, tree=tree, mutation=index), self.assertRaises(RuntimeError):
                        MODULE.check_desktop_shell(bad)

    def test_original_identity_and_workspace_text_cannot_hide_behind_correct_frames(self):
        import copy
        good = self.shell()
        MODULE.check_desktop_shell(good)
        field = lambda d: d['chrome']['identityFields'][0]['value']
        control = lambda d: d['chrome']['controls'][0]
        mutations = [lambda d: d['chrome'].pop('identitySource'), lambda d: d['chrome']['identityFields'].pop(),
                     lambda d: d['chrome']['identityFields'][0].update(children=['DD', 'DT']),
                     lambda d: field(d).update(opaque=False), lambda d: field(d).update(clipped=True),
                     lambda d: field(d).update(fontSize=12), lambda d: field(d).update(text='shortened'),
                     lambda d: field(d)['textRuns'][0].update(unscaled=False),
                     lambda d: field(d)['fragments'][-1].update(visible=False),
                     lambda d: field(d)['textRuns'][0]['fragments'][-1].update(y=500),
                     lambda d: field(d).update(foreground=[]),
                     lambda d: d['chrome']['controls'].pop(), lambda d: control(d).update(count=2),
                     lambda d: control(d).update(tag='SPAN'), lambda d: control(d).update(tree='other'),
                     lambda d: control(d).update(hidden=True), lambda d: control(d).update(disabled=True),
                     lambda d: control(d).update(selected='true'), lambda d: control(d)['proof'].update(clipped=True),
                     lambda d: control(d)['proof'].update(visible=False),
                     lambda d: control(d)['proof']['textRuns'][0]['fragments'][-1].update(visible=False)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(index=index), self.assertRaises(RuntimeError): MODULE.check_desktop_shell(bad)
        # Preserve the existing lower-contrast unselected tab and approved hover
        # styles; do not turn this geometry repair into a new color redesign.
        self.assertLess(MODULE.contrast_ratio(control(good)['proof']['foreground'], control(good)['proof']['background']), 4.5)
        for index, foreground, background in ((0,[107,122,130],[255,255,255]),(4,[49,92,75],[250,250,248]),
                                               (6,[49,92,75],[255,255,255]),(7,[23,26,25],[240,244,239])):
            hovered=copy.deepcopy(good); row=hovered['chrome']['controls'][index];row['hover']=True
            for proof in [row['proof'], *row['proof']['textRuns']]: proof.update(foreground=foreground,background=background)
            MODULE.check_desktop_shell(hovered)
        transitioning=copy.deepcopy(good);proof=transitioning['chrome']['controls'][0]['proof']
        for row in [proof,*proof['textRuns']]: row.update(foreground=[82,110,105],background=[246,248,245])
        MODULE.check_desktop_shell(transitioning)

    def test_stationary_ancestor_offsets_cannot_hide_behind_window_zero_or_correct_panel_bounds(self):
        import copy
        for width in (1440,1920):
            good=self.shell(width=width);MODULE.check_desktop_shell(good)
            for selector in MODULE.STATIONARY_SHELL_SELECTORS:
                for axis in ('top','left'):
                    for value in (117,1,-1,float('nan'),True):
                        bad=copy.deepcopy(good);next(r for r in bad['stationaryAncestors'] if r['selector']==selector)[axis]=value
                        self.assertEqual(bad['window'],{'x':0,'y':0});self.assertEqual(bad['panels']['y'],132)
                        with self.subTest(width=width,selector=selector,axis=axis,value=value),self.assertRaisesRegex(RuntimeError,'hidden scroll offset'):
                            MODULE.check_desktop_shell(bad)
            for rows in (None,[],good['stationaryAncestors'][:-1],list(reversed(good['stationaryAncestors'])),good['stationaryAncestors']*2):
                bad=copy.deepcopy(good);bad['stationaryAncestors']=rows
                with self.assertRaises(RuntimeError):MODULE.check_desktop_shell(bad)
            shifted=copy.deepcopy(good);shifted['panels']['y']=15
            with self.assertRaisesRegex(RuntimeError,'viewport-filling'):MODULE.check_desktop_shell(shifted)

    def test_stationary_ancestor_snapshot_records_actual_hidden_offsets_without_mutating_them(self):
        script=r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<!doctype html><main id="navigation-product"><section id="np-workspace"><div class="np-panels"><section class="np-tree-pane"><div id="np-tree-scroll"></div></section><aside class="np-reading-pane"><div id="np-detail-scroll"></div></aside></div></section></main>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document;d.body.style.overflow='hidden';d.body.scrollTop=117;d.body.scrollLeft=9;d.getElementById('np-detail-scroll').scrollTop=1169;const snap=new w.Function(input.script+';return stationaryShellAncestors();'),rows=snap();assert.equal(w.scrollY,0);assert.equal(rows.find(r=>r.selector==='body').top,117);assert.equal(rows.find(r=>r.selector==='body').left,9);assert.equal(d.body.scrollTop,117);assert.equal(d.getElementById('np-detail-scroll').scrollTop,1169);assert.ok(!rows.some(r=>r.id==='np-tree-scroll'||r.id==='np-detail-scroll'));process.stdout.write(JSON.stringify(rows));}finally{dom.window.close();}
"""
        result=subprocess.run(['node','-e',script],input=json.dumps({'script':MODULE.STATIONARY_SHELL_ANCESTORS_JS}),cwd=Path(__file__).parents[1],text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        rows=json.loads(result.stdout)
        with self.assertRaisesRegex(RuntimeError,'hidden scroll offset'):MODULE.check_stationary_shell_ancestors(rows)
        self.assertIn('stationaryAncestors:stationaryShellAncestors()',MODULE.DESKTOP_SHELL_SNAPSHOT_JS)
        self.assertIn('stationaryAncestors:stationaryShellAncestors()',MODULE.TASK_ROUTE_DIAGNOSTIC_JS)
        for forbidden in ('scrollTop=', 'scrollTop =', 'scrollLeft=', '.scrollTo(', '.scrollIntoView(', '.focus('):
            self.assertNotIn(forbidden,MODULE.STATIONARY_SHELL_ANCESTORS_JS)
        self.assertEqual(len(MODULE.SCENE_NAMES)*len(MODULE.VIEWPORTS),106)

    def test_selector_overlay_cannot_displace_root_or_hide_either_original_relation_endpoint(self):
        import copy
        before = self.shell()
        row = before['title'].copy()
        ids = ['root', 'original-route', 'semexp', 'poni']
        for i, pid in enumerate(ids):
            proof = copy.deepcopy(row)
            proof['rect'] = {'x': 40, 'y': 190 + i * 75, 'width': 680, 'height': 55}
            before['routeRows'].append({'id': pid, 'proof': proof})
        before['rootRows'] = copy.deepcopy(before['routeRows'][:1])
        opened, selected = copy.deepcopy(before), copy.deepcopy(before)
        opened['pickerDisclosure'] = {'open': True, 'position': 'absolute', 'rect': {'x': 800, 'y': 96, 'width': 360, 'height': 288}}
        selected['relation'] = 'methods:relation:90'
        MODULE.check_relation_canvas_stability(before, opened, selected, ids)
        for field, value in (('x', 700), ('height', 324), ('width', 600)):
            bad = copy.deepcopy(opened); bad['pickerDisclosure']['rect'][field] = value
            with self.assertRaises(RuntimeError): MODULE.check_relation_canvas_stability(before, bad, selected, ids)
        for mutate in (lambda d: d['tree'].update(y=500), lambda d: d['rootRows'][0]['proof']['rect'].update(y=600),
                       lambda d: d['offsets']['tree'].update(top=1), lambda d: d['routeRows'].pop(),
                       lambda d: d['routeRows'][-1]['proof'].update(visible=False),
                       lambda d: d['routeRows'][-1]['proof']['rect'].update(y=510),
                       lambda d: d.update(relation='methods:relation:88'), lambda d: d.update(visibleTaskDefinitions=1)):
            bad = copy.deepcopy(selected); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_relation_canvas_stability(before, opened, bad, ids)

    def test_first_analysis_answer_uses_original_preorder_every_version_and_keeps_root_separate(self):
        import copy, gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        for paper, versions in science['analyses'].items():
            for version, entry in versions.items():
                answer = MODULE.first_analysis_answer(science, entry)
                self.assertEqual(answer['kind'], 'analysis_answer')
                self.assertEqual((answer['paperId'], answer['versionId']), (paper, version))
                self.assertNotIn(answer['id'], entry['roots'])
        entry = science['analyses']['poni']['publication:poni:e83f98bb7132']
        answer = MODULE.first_analysis_answer(science, entry)
        self.assertEqual(answer['id'], 'pos:a:a0e29c6be7f62075654f7f')
        data = self.shell('a')
        data['route'].update(node=answer['id'], paper=answer['paperId'], version=answer['versionId'], template=None)
        data['fixedIdentity'] = {'position': answer['id'], 'paper': answer['paperId'], 'version': answer['versionId']}
        data['meta']['text'] = 'Exact version · 本版本部分解析：22/59 原节点已填 · 0 个实例答案'
        data['position'] = {k: answer[v] for k, v in {'id': 'id', 'kind': 'kind', 'paper': 'paperId', 'version': 'versionId', 'parent': 'parentId'}.items()}
        data['answer'] = copy.deepcopy(data['title']); data['answer']['rect'].update(x=460, y=250, width=800, height=80)
        MODULE.check_analysis_first_answer(data, answer, entry, 'Object', 'Exact version')
        for mutate in (lambda d: d['route'].update(node=entry['roots'][0]), lambda d: d['route'].update(template='1'),
                       lambda d: d['route'].update(version='other'), lambda d: d['position'].update(kind='analysis_structure'),
                       lambda d: d['fixedIdentity'].update(version='other'), lambda d: d['meta'].update(text='Exact version'),
                       lambda d: d['answer'].update(visible=False), lambda d: d['answer'].update(text='invented answer'), lambda d: d['answer']['rect'].update(y=330),
                       lambda d: d['offsets']['reader'].update(top=1)):
            bad = copy.deepcopy(data); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_analysis_first_answer(bad, answer, entry, 'Object', 'Exact version')

    def test_ready_outer_scroll_migration_retains_exact_offsets_and_unrelated_buckets(self):
        import copy
        before = ExplorationCaptureChecks().restore_fixture()
        before['window']['y'] = 150
        before['runtime']['contexts']['unrelated'] = {'windowScroll': 88, 'treeScrollByTree': {'c': 333}, 'focusTarget': 'retain'}
        before['persisted'] = copy.deepcopy(before['runtime'])
        after = copy.deepcopy(before); after['window']['y'] = 0
        MODULE.check_exploration_restore(before, after, nonzero=True)
        for mutate in (lambda d: d['window'].update(y=150), lambda d: d['treeScroll'].update(top=0),
                       lambda d: d['treeScroll'].update(left=1), lambda d: d['readerScroll'].update(top=64),
                       lambda d: d['runtime']['contexts'].pop('unrelated'),
                       lambda d: d['runtime']['contexts']['unrelated'].update(windowScroll=0)):
            bad = copy.deepcopy(after); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_exploration_restore(before, bad, nonzero=True)

    def test_production_fixed_selectors_and_first_answer_keep_version_root_and_sources(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
await scope('task:category-objectnav');
// DOM identity only; JSDOM has no native Range rectangles or browser pixels.
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};const shellSnapshot=new w.Function(input.shellSnapshot);assert.equal(shellSnapshot().headingInsideScroll,false);
const tree=d.getElementById('np-tree-scroll'),reader=d.getElementById('np-detail-scroll'),picker=d.getElementById('np-task-route-canvas'),heading=d.getElementById('np-reader-heading');
assert.equal(tree.contains(picker),false);assert.ok(picker.closest('.np-workspace-bar'));assert.equal(reader.contains(heading),false);assert.ok(heading.closest('.np-reading-pane'));
d.getElementById('np-task-route-relations-summary').click();d.querySelector('[data-task-change="methods:relation:90"]').click();await ready(()=>d.querySelector('[data-selected-task-relation]')&&d.querySelector('[data-relation-state]')?.dataset.relationState==='ready');
assert.equal(d.getElementById('np-task-route-relations').open,false);assert.equal(d.getElementById('np-task-relation-title').closest('#np-reader-heading'),heading);assert.equal(d.getElementById('np-reader-object-title').textContent,'SemExp → PONI · 复用组件并替换策略');assert.ok(d.getElementById('np-reader-object-meta').textContent.includes(s.versions[e.poni.versionId].label));
d.querySelector('[data-change-target="'+e.poni.id+'"]').click();await ready(()=>a.getState().route.node===e.poni.id&&a.getContent().ready(e.poni.entityId));
const entry=d.getElementById('np-reader-analysis-entry');assert.equal(reader.contains(entry),false);assert.ok(entry.contains(d.getElementById('np-open-version-analysis')));assert.equal(entry.querySelector('.np-analysis-reference').open,false);
d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a'&&a.getContent().ready(a.getBundle().positions[a.getState().route.node].entityId));
const analysis=s.analyses.poni[e.poni.versionId],answer=m.descendants(a.getBundle(),analysis.roots).map(id=>s.positions[id]).find(p=>p.kind==='analysis_answer');assert.equal(a.getState().route.node,answer.id);assert.equal(d.querySelector('.np-analysis-answer > p').textContent,s.entities[answer.entityId].detail.answer.answer);assert.equal(d.getElementById('np-reader-object-title').dataset.objectVersion,answer.versionId);assert.equal(d.querySelector('[data-analysis-root]'),null);states.push(snapshot());
d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===e.poni.id);d.getElementById('np-open-analysis-structure').click();await ready(()=>a.getState().route.node===analysis.roots[0]&&d.querySelector('[data-analysis-root]'));const root=s.positions[analysis.roots[0]];assert.notEqual(root.kind,'analysis_answer');assert.deepEqual([...d.querySelectorAll('[data-analysis-chapter]')].map(el=>el.dataset.analysisChapter),root.childIds);assert.equal(m.descendants(a.getBundle(),analysis.roots).length,analysis.originalNodeCount+analysis.instanceCount);states.push(snapshot());
"""
        states = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science), 'shellSnapshot': MODULE.DESKTOP_SHELL_SNAPSHOT_JS})
        self.assertNotEqual(states[0]['route']['node'], states[1]['route']['node'])
        self.assertEqual(states[0]['route']['version'], states[1]['route']['version'])

    def test_new_state_capture_mapping_keeps_original_90_scenes_and_historical_diagnostics(self):
        import inspect
        original_migrations = {
            'shared_chrome_budget', 'relation_picker', 'reader_identity', 'context_path',
            'outer_scroll', 's0_footer', 's0_adaptive_spacing', 'overview_relations',
            'analysis_entry', 'active_forest_heading', 'method_geometry', 'method_ancestry',
            'method_introduction', 'source_scroll_fixtures', 'method_analysis_controls',
        }
        self.assertEqual(len(original_migrations), 15)
        self.assertEqual(set(MODULE.DISPLAY_CONTRACT_MIGRATIONS),
                         original_migrations | {'workspace_branch_tabs'})
        self.assertIn('shared_chrome_budget', MODULE.DISPLAY_CONTRACT_MIGRATIONS)
        self.assertIn('s0_footer', MODULE.DISPLAY_CONTRACT_MIGRATIONS)
        self.assertEqual(len(MODULE.SCENE_NAMES), 53)
        for name in ('-31-s0-reading-hierarchy', '-32-s1-relation-90', '-33-s2-first-answer', '-30-analysis-root-coverage'):
            self.assertIn(name, MODULE.SCENE_NAMES)
        source = inspect.getsource(MODULE.main)
        self.assertIn('desktop_hierarchy_checks(', source)
        self.assertIn('displayContractMigrations', source)
        for script in (MODULE.TASK_ROUTE_DIAGNOSTIC_JS, MODULE.COLD_RESTORE_SNAPSHOT_JS, MODULE.READER_TOGGLE_SNAPSHOT_JS):
            self.assertNotIn('window.scrollTo(', script)
        result = subprocess.run(['node', '-e', "new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));"],
                                input=json.dumps(MODULE.DESKTOP_SHELL_SNAPSHOT_JS), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)


def method_candidate_scope_fixture(ids, roving, indexes=None):
    """Synthetic focus metadata for receipt/transport tests, not browser evidence."""
    root=dict(token='fixture-workspace',id='np-workspace',tag='SECTION',hidden=False,inert=False,display='block',visibility='visible')
    items=[dict(token='fixture-'+pid,id='np-node-'+pid,tag='LI',sourcePosition=pid,tabIndex='native-tree-roving',disabled=False,hidden=False,layout=True) for pid in ids]
    items += [dict(token='fixture-control-'+str(i),id='control-'+str(i),tag='BUTTON',sourcePosition=None,tabIndex=0,disabled=False,hidden=False,layout=True) for i in range(6)]
    return dict(same=True,root=root,items=items,treeTabIndexes=[dict(position=pid,tabIndex=indexes[pid] if indexes else 0 if pid==roving else -1) for pid in ids])


def method_candidate_inventory_fixture(state):
    scope=state['scopeCandidates'];indexes={r['position']:r['tabIndex'] for r in scope['treeTabIndexes']};eligible=[]
    for item in scope['items']:
        row=dict(item);row['tabIndex']=indexes[row['sourcePosition']] if row['sourcePosition'] else row['tabIndex']
        if row['tabIndex']>=0 and not row['disabled'] and row['layout']:eligible.append(dict(row,inWorkspace=True))
    return dict(scopeRoot=scope['root']['token'],candidateCount=len(scope['items']),eligibleCount=len(eligible),eligible=eligible)


def attach_method_child_fixture(data, expected):
    """Independent synthetic staged evidence; never a claim about Chrome pixels."""
    import copy
    p=expected['position']; selected=p['id']; key='method-fixture'; history_key='navigation-fixture'
    names={'methods:pipeline-tap-llm':'-28-portable-llm','methods:pipeline-zhu':'-27-imagenav-zhu','methods:pipeline-poni':'-23-poni-method'}
    data['captureName']='1440x900'+names.get(p['entityId'],'-03-method-reader' if p['tree']=='g' else '-11-active-method-reader')
    bucket=dict(focusTarget=selected,expandedByTree=copy.deepcopy(data['expanded']),selectedByTree={p['tree']:selected},
                treeScrollByTree={p['tree']:0},treeScrollLeftByTree={p['tree']:0},detailScrollByTree={p['tree']:0},windowScroll=0)
    runtime=dict(route=copy.deepcopy(data['route']),originTrail=[],revision=7,contexts={key:bucket})
    before=dict(route=copy.deepcopy(data['route']),runtime=runtime,history={history_key:copy.deepcopy(runtime)},historyKey=history_key,
                contextKey=key,historyLength=15,viewport=dict(data['viewport'],dpr=1),window=dict(x=0,y=0),
                tree=dict(top=0,left=0,maxTop=145,maxLeft=0,client=copy.deepcopy(data['tree'])),
                reader=dict(top=0,left=0,maxTop=200,maxLeft=0,client=copy.deepcopy(data['reader'])),
                active=dict(id='np-node-'+selected,tag='LI',position=selected,tabIndex=0,original=True),
                roving=[selected],domSame=True,hoverSame=True,originalFocus=dict(id='np-node-'+selected,tag='LI',tabIndex=0),tabBound=8,
                scopeCandidates=method_candidate_scope_fixture([r['id'] for r in data['rows']],selected))
    children=[r['id'] for r in data['rows'] if r['id'] in expected['children']]
    audit=dict(binding=MODULE.method_child_binding(data['captureName'],data,expected),status='verified_native_children',cleanedUp=True,
               before=before,after=copy.deepcopy(before),baselineMode='coherent',required=children,proofs=[],actions=[],keys=[])
    audit['tabCandidatesBefore']=method_candidate_inventory_fixture(before);audit['tabCandidatesAfter']=method_candidate_inventory_fixture(audit['after'])
    audit['settles']=[dict(ok=True,elapsed=180,quietMs=160)]
    audit['afterSnapshot']=copy.deepcopy({k:v for k,v in data.items() if k not in ('captureName','childReadability')})
    current=copy.deepcopy(before)
    def key_action(pid, key_name):
        nonlocal current
        state=copy.deepcopy(current);state['active']=dict(id='np-node-'+pid,tag='LI',position=pid,tabIndex=0,original=pid==selected);state['roving']=[pid]
        state['runtime']['contexts'][key]['focusTarget']=pid
        for row in state['scopeCandidates']['treeTabIndexes']:row['tabIndex']=0 if row['position']==pid else -1
        trace=MethodKeyTraceChecks.fixture(selected,expected['chain'][0],pid,key_name,top=0)
        for frame in [trace['before'],trace['after'],*(e['snapshot'] for e in trace['events'])]:
            frame['route']=copy.deepcopy(data['route']);frame['tree']['rect']=copy.deepcopy(data['tree']);frame['tree']['clientRect']=copy.deepcopy(data['tree'])
        trace['before']['active']=current['active']['id'];trace['after']['active']='np-node-'+pid
        for event in trace['events']:event['eventTarget']=current['active']['id']
        index=len(audit['actions'])
        audit['keys'].append(dict(input='\ue011' if key_name=='Home' else '\ue015',target=pid,trace=copy.deepcopy(trace),actionIndex=index))
        audit['actions'].append(dict(kind='tree-key',before=copy.deepcopy(current),after=copy.deepcopy(state),tabCandidatesBefore=method_candidate_inventory_fixture(current),tabCandidatesAfter=method_candidate_inventory_fixture(state),events=dict(overflow=0,events=[dict(type='keydown',key=key_name,trusted=True,target=current['active']['id'])])))
        current=state
        return state,trace
    for pid in children:
        state,trace=key_action(pid,'ArrowDown')
        audit['proofs'].append(dict(id=pid,row=copy.deepcopy(next(r for r in data['rows'] if r['id']==pid)),state=copy.deepcopy(state),keyTrace=trace))
    if children:
        key_action(expected['chain'][0],'Home')
        for pid in expected['chain'][1:]:key_action(pid,'ArrowDown')
    data['childReadability']=audit
    return audit


class MethodReadingCaptureChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        cls.science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        spec = importlib.util.spec_from_file_location('method_capture_source_map', Path(__file__).parents[1] / 'scripts/navigation_research_map.py')
        module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
        cls.source_positions = dict(cls.science['positions'])
        cls.source_positions.update(module.build_research_map(cls.science)['positions'])
        cls.cases = {
            'global': cls.source_positions['pos:g:b3c94b96a7de2feaa05e57'],
            'local': cls.source_positions['pos:l:ff0298ffa17b4cfcf009bd'],
            'rich': MODULE.task_route_expected(cls.science)['portable'][1],
            'condition': MODULE.task_route_expected(cls.science)['image'][0],
            'imported': MODULE.task_route_expected(cls.science)['poni'],
        }

    @staticmethod
    def proof(text, x=450, y=145, width=650, height=24):
        r = dict(x=x, y=y, width=width, height=height)
        area = dict(x=0, y=0, width=1440, height=900)
        fragment = dict(r, visible=True)
        return dict(text=text, renderedText=text, rect=r, visible=True, opaque=True, unscaled=True, clipped=False,
                    fontSize=15, foreground=[20, 30, 40], background=[255, 255, 255], viewport=area,
                    readerContent=area, clipAreas=[], fragments=[fragment],
                    textRuns=[dict(text=text, opaque=True, unscaled=True, fontSize=15, foreground=[20, 30, 40],
                                   background=[255, 255, 255], fragments=[fragment], clipAreas=[])])

    def receipt(self, case='global'):
        p = self.cases[case]
        expected = MODULE.method_reading_expected(self.science, p, self.source_positions)
        rows = []
        for index, pid in enumerate(expected['chain'] + expected['children']):
            source = self.source_positions[pid]
            label = source.get('sourceLabel') or source['label']
            rows.append(dict(id=pid, parent=source.get('parentId'), domParent=source.get('parentId'), entity=source['entityId'],
                             tree=p['tree'], level=index + 1 if pid in expected['chain'] else len(expected['chain']) + 1,
                             ancestor=pid in expected['chain'][:-1], selected=pid == p['id'], tabIndex=0 if pid == p['id'] else -1,
                             label=label, sourceLabel=label, role=source['kind'], roleProof=self.proof(source['kind'], 30, 218 + index * 50, 360, 20), proof=self.proof(label, 30, 190 + index * 50, 360, 28)))
        title = rows[len(expected['chain']) - 1]['label']
        meta = expected['version']['label'] + (' · 未固定快照' if expected['version'].get('versionStatus') == 'snapshot_not_version_pinned' else '')
        data = dict(route={k: p[v] for k, v in (('node', 'id'), ('tree', 'tree'), ('scope', 'scopeId'), ('paper', 'paperId'), ('version', 'versionId'))},
                    expanded={p['tree']: expected['chain'].copy()}, methodReading='true', readingLayout='reading', selectedRelation=None,
                    fixedIdentity=dict(position=p['id'], entity=p['entityId'], paper=p['paperId'], version=p['versionId']),
                    title=self.proof(title), meta=self.proof(meta, y=179),
                    treeHeading=self.proof('当前位置与来路', 30, 144, 360), tree=dict(x=17, y=176, width=398, height=683),
                    viewport=dict(x=0, y=0, width=1440, height=900), reader=dict(x=433, y=261, width=990, height=622),
                    pane=dict(x=432, y=132, width=992, height=752),
                    heading=self.proof('fixed source identity', 433, 133, 990, 128), rows=rows,
                    siblings=[], introductions=[dict(text='Original interface introduction', rendering=dict(display='none', rendered=False))],
                    mechanism=dict(entity=p['entityId'], ready=True, rect=dict(x=465, y=280, width=880, height=900),
                                   fields=[dict(text=snippet, rendering=dict(rendered=True), proof=self.proof(snippet, y=280)) for snippet in expected['snippets']]),
                    analysisControls=[self.proof('Original analysis status', y=215, width=500)])
        if expected['siblings']:
            data['siblings'] = [dict(tag='DETAILS', parent=p['parentId'], open=False, summary=self.proof('Real parent alternatives', 30, 700, 360),
                                    controls=[dict(tag='BUTTON', id=pid, treeRole=False, sourceLabel=expected['siblingLabels'][pid], text=expected['siblingLabels'][pid], meta='Original role · '+expected['siblingVersions'].get(pid, ''), disabled=False) for pid in expected['siblings']])]
        for row in rows:
            if row['id'] in expected['childDisplay']:
                display=expected['childDisplay'][row['id']]
                row['label']=display['label'];row['role']=display['role']
                row['proof']['text']=display['label'];row['roleProof']['text']=display['role']
        attach_method_child_fixture(data, expected)
        return data, expected

    def test_source_projection_keeps_exact_global_local_and_original_condition_identity(self):
        global_, local = self.cases['global'], self.cases['local']
        self.assertNotEqual(global_['id'], local['id'])
        self.assertEqual(global_['versionId'], local['versionId'])
        self.assertEqual(self.cases['condition']['association'], 'condition')
        for case in self.cases:
            data, expected = self.receipt(case)
            MODULE.check_method_reading(data, expected, self.source_positions, compact=True)
            self.assertEqual(expected['chain'][-1], data['route']['node'])
            self.assertTrue(all(self.source_positions[pid]['tree'] == data['route']['tree'] for pid in expected['chain']))
        data, expected = self.receipt('rich')
        self.assertTrue(any('v5内容不能覆盖v1' in text for text in expected['snippets']))
        self.assertTrue(any('预先提供MP3D拓扑' in text for text in expected['snippets']))

    def test_method_receipt_rejects_fake_ancestor_sibling_same_paper_and_wrong_version(self):
        import copy
        data, expected = self.receipt('rich')
        mutations = [lambda d: d.update(methodReading='false'), lambda d: d.update(readingLayout='new-science-route'),
                     lambda d: d.update(selectedRelation='methods:relation:90'), lambda d: d['route'].update(tree='g'),
                     lambda d: d['route'].update(node=self.cases['local']['id']), lambda d: d['route'].update(version='old-version'),
                     lambda d: d['fixedIdentity'].update(entity='same-paper-other-method'), lambda d: d['rows'].pop(0),
                     lambda d: d['rows'][1].update(parent='invented'), lambda d: d['rows'][1].update(domParent='invented'),
                     lambda d: d['rows'][1].update(level=1), lambda d: d['rows'][0].update(ancestor=False),
                     lambda d: d['rows'][0].update(tabIndex=0), lambda d: d['rows'][-1].update(selected=True),
                     lambda d: d['rows'][0].update(sourceLabel='truncated'), lambda d: d['rows'][0].update(role=''),
                     lambda d: d['siblings'][0].update(parent='same-paper-wrong-parent'), lambda d: d['siblings'][0].update(tag='DIV'),
                     lambda d: d['siblings'][0]['controls'][0].update(id='invented'), lambda d: d['siblings'][0]['controls'][0].update(treeRole=True),
                     lambda d: d['siblings'][0]['controls'][0].update(sourceLabel='shortened'), lambda d: d['siblings'][0]['controls'][0].update(meta='wrong version'),
                     lambda d: d['title'].update(text='Another method'), lambda d: d['meta'].update(text='Short version'),
                     lambda d: d['mechanism'].update(entity='same-paper-other-entity'), lambda d: d['mechanism'].update(ready=False),
                     lambda d: d['mechanism']['fields'].clear(), lambda d: d.update(analysisControls=[]),
                     lambda d: d['introductions'][0]['rendering'].update(display='block', rendered=True)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(data); mutate(bad)
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                MODULE.check_method_reading(bad, expected, self.source_positions)
        data, expected = self.receipt('global')
        self.assertFalse(expected['siblings'])
        data['siblings'] = [dict(tag='DETAILS', parent=expected['position']['parentId'], controls=[])]
        with self.assertRaises(RuntimeError): MODULE.check_method_reading(data, expected, self.source_positions)

    def test_method_visual_receipt_rejects_low_contrast_small_type_hidden_boundaries_and_old_header(self):
        import copy
        data, expected = self.receipt()
        mutations = [lambda d: d['heading']['rect'].update(height=129), lambda d: d['reader'].update(y=262),
                     lambda d: d.pop('pane'), lambda d: (d['heading']['rect'].update(y=143), d['reader'].update(y=271)),
                     lambda d: d['mechanism']['rect'].update(width=478), lambda d: d['mechanism']['rect'].update(width=1200),
                     lambda d: d['rows'][0]['proof'].update(visible=False), lambda d: d['rows'][0]['proof'].update(fontSize=14.99), lambda d: d['rows'][0]['roleProof'].update(fontSize=14),
                     lambda d: d['title']['textRuns'][0].update(fontSize=10), lambda d: d['title'].update(fragments=[]),
                     lambda d: d['meta']['textRuns'][0]['fragments'][0].update(visible=False),
                     lambda d: d['meta'].update(foreground=[200, 200, 200]), lambda d: d['meta'].update(clipped=True),
                     lambda d: d['mechanism']['fields'][0]['rendering'].update(rendered=False),
                     lambda d: d['mechanism']['fields'][0]['proof'].update(clipped=True),
                     lambda d: d['mechanism']['fields'][0]['proof'].update(fontSize=14),
                     lambda d: d['mechanism']['fields'][0]['proof'].update(foreground=[240, 240, 240]),
                     lambda d: d['analysisControls'][0].update(visible=False)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(data); mutate(bad)
            with self.subTest(index=index), self.assertRaises(RuntimeError):
                MODULE.check_method_reading(bad, expected, self.source_positions, compact=True)
        # No hard clipping target is imposed on another genuinely long source identity.
        data['heading']['rect']['height'] = 140
        attach_method_child_fixture(data, expected)
        MODULE.check_method_reading(data, expected, self.source_positions, compact=False)

    def test_method_geometry_is_separate_from_task_relation_analysis_and_collapse(self):
        import copy
        for width in (1440, 1920):
            for tree in ('g', 'l'):
                p = self.cases['global' if tree == 'g' else 'local']
                data = DesktopHierarchyContractChecks.shell(tree, width)
                data.update(methodReading='true', readingLayout='reading', position=dict(id=p['id'], kind=p['kind'], paper=p['paperId'], version=p['versionId']))
                data['route'].update(node=p['id'], paper=p['paperId'], version=p['versionId'])
                if tree == 'g':
                    data['route']['scope'] = p['scopeId']
                    data['chrome'] = desktop_chrome_fixture(width, data['viewport']['height'], route=data['route'])
                    for tab in data['chrome']['controls']:
                        if tab['tree']: tab['selected'] = str(tab['tree'] == 'l').lower()
                old_width = data['treePane']['width']; width_delta = old_width - (400 if width == 1440 else 448)
                data['treePane']['width'] -= width_delta; data['tree']['width'] -= width_delta
                for key in ('pane', 'reader'):
                    data[key]['x'] -= width_delta; data[key]['width'] += width_delta
                for key in ('heading', 'title', 'meta'):
                    data[key]['rect']['x'] -= width_delta; data[key]['rect']['width'] += width_delta
                HeaderFooterCaptureChecks.add_method_footer(data)
                MODULE.check_desktop_shell(data)
                self.assertEqual(data['pane']['width'], 992 if width == 1440 else 1424)
                for mutate in (lambda d: d.update(methodReading='false'), lambda d: d.update(readingLayout='method'),
                               lambda d: d.update(relation='methods:relation:90'), lambda d: d['route'].update(version='stale'),
                               lambda d: d['position'].update(kind='challenge'), lambda d: d['route'].update(tree='c')):
                    bad = copy.deepcopy(data); mutate(bad)
                    with self.assertRaises(RuntimeError): MODULE.check_desktop_shell(bad)
                data['collapsed'] = True; data['treePane']['width'] = width - 32; data['tree']['width'] = width - 34
                data['permanentScrollIds'] = ['np-tree-scroll']
                MODULE.check_desktop_shell(data)
            # Existing relation, C and A geometry remains independent and strict.
            for tree in ('l', 'c', 'a'):
                data = DesktopHierarchyContractChecks.shell(tree, width)
                MODULE.check_desktop_shell(data)
                data['methodReading'] = 'true'
                with self.assertRaises(RuntimeError): MODULE.check_desktop_shell(data)

    def test_method_capture_reuses_all_98_scenes_and_is_read_only(self):
        import inspect
        self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)
        for suffix in ('-03-method-reader', '-03b-reader-visible', '-11-active-method-reader', '-23-poni-method', '-27-imagenav-zhu', '-28-portable-llm'):
            self.assertIn(suffix, MODULE.SCENE_NAMES)
        source = inspect.getsource(MODULE.main)
        self.assertIn("data['methodReading'] = driver.js(METHOD_READING_SNAPSHOT_JS)", source)
        self.assertIn('check_method_reading(', source)
        for operation in ('.click(', '.focus(', 'scrollIntoView(', 'scrollTo(', '.navigate(', '.replaceState(', '.pushState('):
            self.assertNotIn(operation, MODULE.METHOD_READING_SNAPSHOT_JS)
        result = subprocess.run(['node', '-e', "new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));"],
                                input=json.dumps(MODULE.METHOD_READING_SNAPSHOT_JS), text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_native_keyboard_receipt_preserves_route_scroll_origin_and_expansion(self):
        import copy
        before = dict(route=dict(tree='g', node='real-method', scope='scope:all', paper='p', version='v', claim=None),
                      originTrail=[dict(route=dict(tree='l', node='original'), bucket=dict(expandedByTree=dict(l=['original'])))],
                      historyLength=5, expanded=dict(g=['root', 'parent', 'real-method'], l=['keep']), window=dict(x=0, y=0),
                      treeScroll=dict(top=37, left=0), readerScroll=dict(top=211, left=0), focus='np-node-real-method', roving=['real-method'],
                      methodReading='true', siblings=[])
        after = copy.deepcopy(before); after.update(focus='np-node-parent', roving=['parent'])
        MODULE.check_method_navigation_transition(before, after, 'parent', exact_tree_scroll=True)
        for mutate in (lambda d: d['route'].update(node='same-paper-other-position'), lambda d: d['originTrail'].clear(),
                       lambda d: d['expanded']['l'].append('new'), lambda d: d['readerScroll'].update(top=0),
                       lambda d: d['treeScroll'].update(top=0), lambda d: d.update(historyLength=6),
                       lambda d: d.update(focus='np-node-other'), lambda d: d.update(roving=['parent', 'root']),
                       lambda d: d.update(methodReading='false')):
            bad = copy.deepcopy(after); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_method_navigation_transition(before, bad, 'parent', exact_tree_scroll=True)

    def test_method_return_requires_exact_previous_geometry_and_effective_offsets(self):
        import copy
        before = DesktopHierarchyContractChecks.shell()
        before['route'].update(node='original-task-root', scope='task:category-objectnav')
        before['relation'] = 'methods:relation:90'
        HeaderFooterCaptureChecks.add_return_control(before)
        before['offsets'] = dict(tree=dict(top=90, left=17), reader=dict(top=211, left=0))
        MODULE.check_method_layout_return(before, copy.deepcopy(before))
        for mutate in (lambda d: d['offsets']['tree'].update(top=0), lambda d: d['offsets']['tree'].update(left=0),
                       lambda d: d['offsets']['reader'].update(top=0), lambda d: d.update(relation=None),
                       lambda d: d['route'].update(node='same-paper-other-position'), lambda d: d['treePane'].update(width=400),
                       lambda d: d.update(methodReading='true')):
            bad = copy.deepcopy(before); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_method_layout_return(before, bad)

    def test_production_method_source_projection_and_native_controls_keep_real_global_local_identity(self):
        body = r"""
// Production DOM and event tests only. JSDOM has no layout; browser geometry is separately gated.
w.Range.prototype.getClientRects=function(){return [];};d.elementFromPoint=()=>d.body;
const receipt=new w.Function(input.methodSnapshot),navState=new w.Function(input.navigationSnapshot);
const stable=()=>{const x=navState();delete x.focus;delete x.roving;return JSON.stringify(x);};
async function inspect(p){
  await ready(()=>a.getState().route.node===p.id&&a.getContent().ready(p.entityId));
  const value=receipt(),chain=[];for(let q=a.getBundle().positions[p.id];q;q=a.getBundle().positions[q.parentId])chain.unshift(q.id);
  const ids=[],expanded=new Set(m.getBucket(a.getState()).expandedByTree[p.tree]),path=new Set(chain);function visit(id){ids.push(id);if(expanded.has(id)){let children=a.getBundle().positions[id].childIds;if(children.some(cid=>path.has(cid)))children=children.filter(cid=>path.has(cid));children.forEach(visit);}}visit(chain[0]);assert.equal(JSON.stringify(value.rows.map(r=>r.id)),JSON.stringify(ids));assert.equal(value.methodReading,'true');
  assert.equal(value.readingLayout,'reading');assert.equal(value.fixedIdentity.entity,p.entityId);assert.equal(value.fixedIdentity.version,p.versionId);
  const before=stable();let current=d.getElementById('np-node-'+p.id);current.focus();
  current.dispatchEvent(new w.KeyboardEvent('keydown',{key:'Home',bubbles:true}));assert.equal(d.activeElement.dataset.position,ids[0]);
  for(const id of ids.slice(1)){d.activeElement.dispatchEvent(new w.KeyboardEvent('keydown',{key:'ArrowDown',bubbles:true}));assert.equal(d.activeElement.dataset.position,id);}
  assert.equal(stable(),before,'keyboard presentation cannot mutate the route, origin, expansion or offsets');
  const disclosure=d.querySelector('#np-tree details[data-method-siblings]');
  if(disclosure){const summary=disclosure.querySelector(':scope > summary'),route=JSON.stringify(a.getState().route),expanded=JSON.stringify(m.getBucket(a.getState()).expandedByTree),origin=JSON.stringify(a.getState().originTrail);summary.click();assert.equal(disclosure.open,true);assert.equal(disclosure.closest('[role=treeitem]'),null);assert.equal(disclosure.querySelector('[role=treeitem],[role=group]'),null);summary.click();assert.equal(disclosure.open,false);assert.equal(JSON.stringify(a.getState().route),route);assert.equal(JSON.stringify(m.getBucket(a.getState()).expandedByTree),expanded);assert.equal(JSON.stringify(a.getState().originTrail),origin);}
  states.push(value);
}
// Explicit real g controls, never an inferred ObjectNav/L substitute.
d.getElementById('np-overview-toggle').click();await ready(()=>d.getElementById('np-reading-landing').hidden);
const global=input.cases.global;await select(global.id);await inspect(global);
d.querySelector('[data-tree-tab="g"]').click();await ready(()=>a.getState().route.node===a.getBundle().researchMap.roots[0]);d.getElementById('np-overview-toggle').click();await ready(()=>!d.getElementById('np-reading-landing').hidden);
for(const name of ['local','rich','condition','imported']){const p=input.cases[name];await scope(p.scopeId);await select(p.id);await inspect(p);}
"""
        states = run_product_capture_script(self, body, {'science': self.science, 'expected': MODULE.task_route_expected(self.science),
            'cases': self.cases, 'methodSnapshot': MODULE.METHOD_READING_SNAPSHOT_JS,
            'navigationSnapshot': MODULE.METHOD_NAVIGATION_STATE_JS, 'viewport': dict(width=1440, height=900)})
        self.assertEqual(len(states), 5)
        for case, data in zip(('global', 'local', 'rich', 'condition', 'imported'), states):
            expected = MODULE.method_reading_expected(self.science, self.cases[case], self.source_positions)
            MODULE.check_method_reading(data, expected, self.source_positions, visual=False)

    def test_method_projection_respects_original_collapsed_children_and_expanded_grandchildren(self):
        import copy
        data, expected = self.receipt('global')
        data['expanded']['g'].remove(expected['position']['id'])
        data['rows'] = data['rows'][:len(expected['chain'])]
        attach_method_child_fixture(data, expected)
        MODULE.check_method_reading(data, expected, self.source_positions)
        wrong = copy.deepcopy(data); wrong['rows'].append(self.receipt('global')[0]['rows'][-1])
        with self.assertRaises(RuntimeError): MODULE.check_method_reading(wrong, expected, self.source_positions)
        p = next(p for p in self.source_positions.values() if p['tree'] == 'l' and p['kind'] == 'pipeline_recipe'
                 and any(self.source_positions[c]['childIds'] for c in p['childIds']))
        expected = MODULE.method_reading_expected(self.science, p, self.source_positions)
        closed = MODULE.method_visible_source_ids(expected, self.source_positions, expected['chain'])
        self.assertEqual(closed, expected['chain'] + p['childIds'])
        child = next(cid for cid in p['childIds'] if self.source_positions[cid]['childIds'])
        opened = MODULE.method_visible_source_ids(expected, self.source_positions, expected['chain'] + [child])
        self.assertEqual(opened, closed[:closed.index(child) + 1] + self.source_positions[child]['childIds'] + closed[closed.index(child) + 1:])
        self.assertTrue(all(pid in self.source_positions for pid in opened))
        self.assertEqual(expected['siblings'], [pid for pid in self.source_positions[p['parentId']]['childIds'] if pid != p['id']])

    def test_parallel_scope_snapshot_uses_actual_fixed_heading_and_original_root_source(self):
        import inspect
        body = r"""
w.Range.prototype.getClientRects=function(){return [];};d.elementFromPoint=()=>d.body;const parallel=new w.Function(input.parallelSnapshot);
for(const sid of ['task:audiogoal','task:goat']){await scope(sid);for(const tree of ['l','c']){
 if(a.getState().route.tree!==tree){d.querySelector('[data-tree-tab="'+tree+'"]').click();await ready(()=>a.getState().route.tree===tree&&a.getContent().ready(a.getBundle().positions[a.getState().route.node].entityId));}
 const roots=s.forests[sid],records={};for(const t of ['l','c'])records[t]=roots[t].map(id=>({id,entity:s.positions[id].entityId,tree:t,scope:sid,label:s.entities[s.positions[id].entityId].label}));
 const result=parallel(sid,input.rootSelector,roots,Object.fromEntries(['l','c'].map(t=>[t,roots[t].some(id=>s.positions[id].childIds.length>0)])),records);
 assert.equal(result.panels.length,1);const panel=result.panels[0];assert.equal(panel.headingSelector,'#np-tree-heading');assert.equal(panel.headingTree,tree);assert.equal(panel.headingInPane,true);assert.equal(panel.headingProof.text,tree==='l'?'文献树':'挑战–思路树');assert.ok(panel.legacyHeading);assert.equal(panel.rootRecords.length,records[tree].length);
 panel.rootRecords.forEach((root,i)=>{assert.equal(root.id,records[tree][i].id);assert.equal(root.entity,records[tree][i].entity);assert.equal(root.proof.text,records[tree][i].label);});states.push(result);
}}
"""
        states = run_product_capture_script(self, body, {'science': self.science, 'expected': MODULE.task_route_expected(self.science),
            'parallelSnapshot': MODULE.PARALLEL_SCOPE_SNAPSHOT_JS, 'rootSelector': MODULE.PARALLEL_ROOT_SELECTOR,
            'viewport': dict(width=1440, height=900)})
        self.assertEqual([(x['scope'], x['activeTree']) for x in states], [('task:audiogoal', 'l'), ('task:audiogoal', 'c'), ('task:goat', 'l'), ('task:goat', 'c')])
        source = inspect.getsource(MODULE.main)
        self.assertIn('PARALLEL_SCOPE_SNAPSHOT_JS', source)
        self.assertNotIn("h=e.querySelector('h3')", source)


    def test_actual_63341ad_parallel_heading_failure_stays_historical_and_strict(self):
        # Unmodified failed Chrome receipt fragment, head 63341ad8342ff438da52669a2bcd30b86cb6b1c5.
        # Full receipt SHA256: 7f1ba9abfa86887282fdd5e350491b8eea3fe31491b5a62761592af32f2f858a
        import copy
        historical = json.loads(r"""{"activeTree": "l", "expectedScope": "task:audiogoal", "home": false, "inactiveItemCount": 0, "panels": [{"children": [{"background": [248, 251, 250], "clipped": false, "fontSize": 16, "foreground": [32, 52, 63], "opaque": true, "rect": {"height": 42, "width": 718, "x": 53, "y": 240}, "text": "−层级 2AV-Nav 音视听觉目标策略1路线", "unscaled": true, "visible": true}, {"background": [248, 251, 250], "clipped": false, "fontSize": 16, "foreground": [32, 52, 63], "opaque": true, "rect": {"height": 42, "width": 694, "x": 77, "y": 317}, "text": "·层级 3AV-Nav 音视听觉目标策略具体方法", "unscaled": true, "visible": true}], "expectedChildren": true, "expectedRoots": ["pos:l:907fd0617aea6bfeebfe45"], "heading": {"height": 0, "width": 0, "x": 0, "y": 0}, "headingVisible": false, "rect": {"height": 238.25, "width": 742, "x": 29, "y": 184}, "roots": ["pos:l:907fd0617aea6bfeebfe45"], "scope": "task:audiogoal", "tree": "l"}], "rovingCount": 1, "scope": "task:audiogoal", "selectedTree": "l", "treeCount": 1, "viewport": {"height": 900, "width": 1440, "x": 0, "y": 0}}""")
        unchanged = copy.deepcopy(historical)
        self.assertEqual(historical['panels'][0]['heading'], dict(x=0, y=0, width=0, height=0))
        self.assertFalse(historical['panels'][0]['headingVisible'])
        with self.assertRaisesRegex(RuntimeError, 'heading is not visible'):
            MODULE.check_parallel_scope(historical)
        self.assertEqual(historical, unchanged)
        self.assertIn('active_forest_heading', MODULE.DISPLAY_CONTRACT_MIGRATIONS)


class OriginalChallengeCaptureChecks(unittest.TestCase):
    @staticmethod
    def fixture():
        def rect(x, y, width, height): return dict(x=x, y=y, width=width, height=height)
        viewport = rect(0, 0, 1440, 900)
        def proof(text, y=260, region=None):
            box = rect(870, y, 500, 24)
            fragment = dict(box, visible=True)
            return dict(text=text, renderedText=text, rect=box, visible=True, opaque=True, unscaled=True,
                        fontSize=15, clipped=False, foreground=[20, 30, 40], background=[255, 255, 255],
                        viewport=viewport, readerContent=region or rect(850, 230, 574, 650), clipAreas=[],
                        fragments=[fragment], textRuns=[dict(fontSize=15, opaque=True, unscaled=True,
                        foreground=[20, 30, 40], background=[255, 255, 255], clipAreas=[], fragments=[fragment])])
        position = dict(id='original-position', entityId='original-challenge', tree='g', scopeId='scope:all', paperId='paper', versionId='version')
        original = dict(id=position['entityId'], label='完整的原始研究问题？', detail=dict(plain_language_question='完整的原始研究问题？',
                        condition_scope=dict(condition='原适用条件', tasks=['ObjectNav', 'zero-shot ObjectNav'], remaining_limit='原剩余限制')))
        header = rect(850, 132, 574, 96)
        title = proof(original['label'], 144, header)
        role = proof(' · 研究问题', 185, header)
        def duplicate(tag, field=None):
            return dict(tag=tag, marked=True, position=position['id'], owner=position['id'],
                        directChild=True, field=field, text=original['label'],
                        rendering=dict(rendered=False, display='none',
                                       blockedBy=dict(reason='display-none', tag=tag, id=None)))
        heading_duplicate = duplicate('H3')
        question_duplicate = duplicate('SECTION', 'plain_language_question')
        data = dict(route=dict(node=position['id'], tree='g', scope='scope:all', paper='paper', version='version'),
                    summaryCount=1, summaryPosition=position['id'], titleCount=1, title=title,
                    titleIdentity=dict(position=position['id'], entity=position['entityId'], paper='paper', version='version'),
                    identityHeadingCount=1, identityHeading=heading_duplicate, questionDuplicate=question_duplicate,
                    markedDuplicates=[heading_duplicate, question_duplicate],
                    roleCount=1, questionRole=role, questionCount=1, questionText=original['label'], question=None,
                    scopeCount=1, scopeEntity=original['id'], scope=proof('完整范围', 260),
                    scopeParagraphs=[proof('适用条件：原适用条件', 270), proof('任务范围：ObjectNav；zero-shot ObjectNav', 305), proof('仍未解决：原剩余限制', 340)],
                    viewport=viewport)
        return data, position, original

    def test_fixed_title_requires_exact_identity_original_label_and_all_existing_visibility_gates(self):
        import copy
        data, position, original = self.fixture()
        MODULE.check_original_challenge_reading(data, position, original)
        mutations = [lambda d: d.update(titleCount=0), lambda d: d.update(titleCount=2), lambda d: d.update(title=None),
                     lambda d: d.update(summaryPosition='other-position'), lambda d: d.update(summaryCount=2),
                     lambda d: d.update(scopeCount=0), lambda d: d.update(scopeEntity='other-challenge'),
                     lambda d: d['title'].update(renderedText='简称'), lambda d: d['title'].update(visible=False),
                     lambda d: d['title'].update(opaque=False), lambda d: d['title'].update(unscaled=False),
                     lambda d: d['title'].update(clipped=True), lambda d: d['title'].update(fontSize=14),
                     lambda d: d['title'].update(foreground=[250, 250, 250]), lambda d: d['title']['rect'].update(y=950),
                     lambda d: d['title']['textRuns'][0].update(opaque=False), lambda d: d['title']['fragments'][0].update(visible=False),
                     lambda d: d.update(roleCount=0), lambda d: d['questionRole'].update(renderedText=' · 来源'),
                     lambda d: d['questionRole'].update(visible=False), lambda d: d.update(questionText='删除了原字段')]
        for field in ('position', 'entity', 'paper', 'version'):
            mutations.append(lambda d, f=field: d['titleIdentity'].__setitem__(f, 'different'))
        for field in ('node', 'tree', 'scope', 'paper', 'version'):
            mutations.append(lambda d, f=field: d['route'].__setitem__(f, 'different'))
            mutations.append(lambda d, f=field: d['route'].pop(f))
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(data); mutate(bad)
            bad['text'] = original['label']  # Hidden/other section text must never substitute for the fixed title.
            with self.subTest(mutation=index), self.assertRaises(RuntimeError):
                MODULE.check_original_challenge_reading(bad, position, original)

    def test_approved_duplicates_must_be_actually_hidden_and_exactly_owned(self):
        import copy
        data, position, original = self.fixture()
        mutations = [lambda d: d.update(identityHeadingCount=0), lambda d: d.update(identityHeadingCount=2),
                     lambda d: d['identityHeading'].update(text='其他生成标题'),
                     lambda d: d['markedDuplicates'].pop(),
                     lambda d: d['markedDuplicates'].append(dict(d['questionDuplicate'], field='evidence'))]
        for key in ('identityHeading', 'questionDuplicate'):
            mutations += [lambda d, k=key: d[k]['rendering'].update(rendered=True, display='block', blockedBy=None),
                          lambda d, k=key: d[k]['rendering'].update(blockedBy=dict(reason='empty-bounds')),
                          lambda d, k=key: d[k]['rendering'].update(display='block', visibility='hidden',
                              rect=dict(x=870, y=270, width=500, height=24), blockedBy=dict(reason='visibility')),
                          lambda d, k=key: d[k]['rendering'].update(display='block', opacity='0',
                              rect=dict(x=870, y=270, width=500, height=24), blockedBy=dict(reason='opacity-zero')),
                          lambda d, k=key: d[k].update(marked=False),
                          lambda d, k=key: d[k].update(position='other-position'),
                          lambda d, k=key: d[k].update(owner='other-summary'),
                          lambda d, k=key: d[k].update(directChild=False)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(data); mutate(bad)
            with self.subTest(mutation=index), self.assertRaises(RuntimeError):
                MODULE.check_original_challenge_reading(bad, position, original)

    def test_each_original_scope_field_must_remain_in_an_actually_visible_paragraph(self):
        import copy
        data, position, original = self.fixture()
        mutations = [lambda d: d['scopeParagraphs'].pop(), lambda d: d['scope'].update(visible=False)]
        for index in range(3):
            mutations += [lambda d, i=index: d['scopeParagraphs'][i].update(renderedText='被替换的字段'),
                          lambda d, i=index: d['scopeParagraphs'][i].update(visible=False),
                          lambda d, i=index: d['scopeParagraphs'][i].update(fontSize=14),
                          lambda d, i=index: d['scopeParagraphs'][i].update(unscaled=False),
                          lambda d, i=index: d['scopeParagraphs'][i].update(clipped=True),
                          lambda d, i=index: d['scopeParagraphs'][i]['rect'].update(y=950),
                          lambda d, i=index: d['scopeParagraphs'][i]['textRuns'][0].update(opaque=False)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(data); mutate(bad)
            bad['text'] = '原适用条件 ObjectNav zero-shot ObjectNav 原剩余限制'
            with self.subTest(mutation=index), self.assertRaises(RuntimeError):
                MODULE.check_original_challenge_reading(bad, position, original)

    def test_different_question_including_whitespace_cannot_be_represented_by_fixed_title(self):
        import copy
        for question in ('不同的原始问题？', ' 完整的原始研究问题？'):
            data, position, original = self.fixture()
            original['detail']['plain_language_question'] = question
            data.update(questionText=question, roleCount=0, questionRole=None)
            data['markedDuplicates'] = [data['identityHeading']]
            data['questionDuplicate'].update(marked=False, field=None)
            data['questionDuplicate']['rendering'].update(rendered=True, display='block', blockedBy=None)
            data['question'] = copy.deepcopy(data['scopeParagraphs'][0]); data['question'].update(text=question, renderedText=question)
            MODULE.check_original_challenge_reading(data, position, original)
            for mutate in (lambda d: d.update(question=None), lambda d: d.update(roleCount=1), lambda d: d['question'].update(visible=False)):
                bad = copy.deepcopy(data); mutate(bad)
                with self.assertRaises(RuntimeError): MODULE.check_original_challenge_reading(bad, position, original)

    def test_production_original_challenge_binds_fixed_selector_role_and_retained_raw_field(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
const p=Object.values(a.getBundle().researchMap.positions).find(p=>p.entityId==='legacy:ci_search_unknown_target');
d.querySelector('[data-challenge-open="'+p.id+'"]').click();await ready(()=>a.getState().route.node===p.id&&a.getContent().ready(p.entityId)&&d.querySelector('[data-reading-node="'+p.id+'"]'));
const original=s.entities[p.entityId],header=d.getElementById('np-reader-object-title'),titles=d.querySelectorAll(input.titleSelector),roles=d.querySelectorAll(input.roleSelector),summary=d.querySelector('#np-reader-summary [data-reading-node="'+p.id+'"]');
assert.equal(titles.length,1);assert.equal(titles[0].textContent,original.label);assert.deepEqual([header.dataset.objectPosition,header.dataset.objectEntity,header.dataset.objectPaper,header.dataset.objectVersion],[p.id,p.entityId,p.paperId||'',p.versionId||'']);
assert.equal(roles.length,1);assert.equal(roles[0].textContent,' · 研究问题');const raw=summary.querySelector('[data-reader-duplicate-field="plain_language_question"] > p');assert.ok(raw);assert.equal(raw.textContent,original.detail.plain_language_question);assert.equal(summary.querySelector('[data-challenge-scope]').dataset.challengeScope,original.id);states.push(snapshot());
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};
states[0].workspaceChrome=(new w.Function(input.chromeSnapshot))();
assert.equal(a.getState().route.tree,'g');assert.deepEqual(JSON.parse(JSON.stringify(states[0].workspaceChrome.controls.filter(row=>row.tree&&row.selected==='true').map(row=>row.tree))),['c']);
"""
        states = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science),
                                            'titleSelector': MODULE.ORIGINAL_CHALLENGE_TITLE_SELECTOR,
                                            'roleSelector': MODULE.ORIGINAL_CHALLENGE_ROLE_SELECTOR,
                                            'chromeSnapshot': MODULE.VISUAL_GEOMETRY + MODULE.FIXED_TEXT_PROOF_JS + MODULE.DESKTOP_CHROME_GEOMETRY_JS + ';return desktopChromeGeometry();'})
        self.assertEqual(states[0]['position']['entity'], 'legacy:ci_search_unknown_target')
        self.assertEqual(MODULE.workspace_selected_tree(states[0]['route'], states[0]['workspaceChrome']['identitySource']), 'c')

    def test_snapshot_uses_only_exact_fixed_h2_and_measures_actual_text_fragments(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM(`<!doctype html><style>*{opacity:1;visibility:visible;transform:none;zoom:1;color:rgb(20,30,40);background-color:rgb(255,255,255);font-size:15px}span{display:inline}</style>
<div id="np-reader-heading"><div id="np-reader-object-title" data-object-position="p" data-object-entity="e" data-object-paper="paper" data-object-version="v"><h2><span id="actual-title">完整原问题？</span></h2></div><p id="np-reader-object-meta"><span class="np-reader-field-role" data-reader-field-role="plain_language_question"> · 研究问题</span></p></div>
<div id="np-detail-scroll"><div id="np-reader-summary"><section data-reading-node="p"><h3 id="summary-decoy" class="np-reader-identity-duplicate" data-reader-duplicate-position="p" style="display:none">完整原问题？</h3><aside data-challenge-scope="e"><p>条件</p><p>任务</p><p>限制</p></aside><section class="np-detail-block np-reader-identity-duplicate" data-reader-duplicate-position="p" data-reader-duplicate-field="plain_language_question" style="display:none"><h3>研究问题</h3><p>完整原问题？</p></section></section></div></div>`,{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,rect=(x,y,width,height)=>({x,y,width,height,left:x,top:y,right:x+width,bottom:y+height});
w.NavigationProductApp={getState:()=>({route:{node:'p',tree:'g',scope:'scope:all',paper:'paper',version:'v'}})};
Object.defineProperties(w,{innerWidth:{value:1440},innerHeight:{value:900}});const style=w.getComputedStyle.bind(w);w.getComputedStyle=e=>new Proxy(style(e),{get:(t,k)=>k==='zoom'?(t.zoom||'1'):Reflect.get(t,k)});
for(const e of d.querySelectorAll('*')){e.getBoundingClientRect=()=>e.id==='np-reader-heading'?rect(850,132,574,96):e.id==='np-detail-scroll'?rect(850,230,574,650):e.closest('#np-reader-heading')?rect(870,e.closest('#np-reader-object-meta')?185:144,500,24):rect(870,270,500,24);for(const [k,v] of Object.entries({clientLeft:0,clientTop:0,clientWidth:e.id==='np-reader-heading'||e.id==='np-detail-scroll'?574:500,clientHeight:e.id==='np-reader-heading'?96:e.id==='np-detail-scroll'?650:24,scrollWidth:500,scrollHeight:24}))Object.defineProperty(e,k,{value:v,configurable:true});}
w.Range.prototype.getClientRects=function(){return [this.startContainer.parentElement.getBoundingClientRect()];};
d.elementFromPoint=(x,y)=>y<175?d.getElementById('actual-title'):y<228?d.querySelector('.np-reader-field-role'):d.querySelector('[data-challenge-scope] > p');
const snap=new w.Function(input.script),position={id:'p',entityId:'e'},run=()=>snap(position,'完整原问题？',input.title,input.role),good=run();
assert.equal(good.title.tag,'H2');assert.equal(good.title.renderedText,'完整原问题？');assert.equal(good.titleIdentity.entity,'e');assert.equal(good.questionRole.renderedText,' · 研究问题');assert.equal(good.questionCount,1);assert.equal(good.question,null);assert.equal(good.scopeParagraphs.length,3);assert.equal(good.title.textRuns[0].opaque,true);
assert.equal(good.identityHeading.rendering.rendered,false);assert.equal(good.identityHeading.rendering.blockedBy.reason,'display-none');assert.equal(good.questionDuplicate.rendering.rendered,false);assert.deepEqual(JSON.parse(JSON.stringify(good.markedDuplicates.map(e=>[e.tag,e.field,e.owner,e.directChild]))),[['H3',null,'p',true],['SECTION','plain_language_question','p',true]]);
for(const e of [d.getElementById('summary-decoy'),d.querySelector('[data-reader-duplicate-field]')]){e.style.display='block';const shown=run(),record=e.tagName==='H3'?shown.identityHeading:shown.questionDuplicate;assert.equal(record.rendering.rendered,true);e.style.display='none';}
const answer=d.createElement('section');answer.className='np-analysis-answer np-reader-identity-duplicate';answer.textContent='A原回答';d.getElementById('np-detail-scroll').appendChild(answer);assert.equal(run().markedDuplicates.length,2,'A answers outside the exact summary are never deduplication evidence');
d.getElementById('actual-title').style.display='none';const hidden=run();assert.equal(hidden.title.textRuns[0].opaque,false);d.getElementById('actual-title').style.display='';
const header=d.getElementById('np-reader-object-title'),duplicate=header.querySelector('h2').cloneNode(true);header.appendChild(duplicate);assert.equal(run().titleCount,2);assert.equal(run().title,null);duplicate.remove();header.querySelector('h2').remove();assert.equal(run().titleCount,0);assert.equal(run().title,null);assert.equal(d.getElementById('summary-decoy').textContent,'完整原问题？');
}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.ORIGINAL_CHALLENGE_SNAPSHOT_JS,
                                'title': MODULE.ORIGINAL_CHALLENGE_TITLE_SELECTOR, 'role': MODULE.ORIGINAL_CHALLENGE_ROLE_SELECTOR}),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class HeaderFooterCaptureChecks(unittest.TestCase):
    @staticmethod
    def add_return_control(data):
        import copy
        title = data['title']['rect']
        data['titleRelation'] = data['relation']
        button = copy.deepcopy(data['title'])
        button['text'] = '返回路线概览'
        button['rect'] = dict(x=title['x'] + title['width'] - 130, y=title['y'], width=130, height=28)
        title['width'] -= 142
        data['returnControlCount'] = 1
        data['returnControl'] = dict(tag='BUTTON', disabled=False, inHeading=True, insideScroll=False, proof=button)

    @staticmethod
    def add_method_footer(data):
        import copy
        pane = data['treePane']; bottom = pane['y'] + pane['height'] - 1
        footer_rect = dict(x=pane['x'] + 1, y=bottom - 46, width=pane['width'] - 2, height=46)
        data['tree']['height'] = footer_rect['y'] - data['tree']['y']
        data['routeRows'] = [dict(id='original-row-' + str(i)) for i in range(6)]
        texts = ['6 个来路与分枝节点 · 2 个直接子节点', '选择节点深入 · ＋展开 · 拖动空白平移']
        base = copy.deepcopy(data['title'])
        base.update(rect=footer_rect, text=''.join(texts), fontSize=12, foreground=[87, 111, 120])
        labels = []
        for i, text in enumerate(texts):
            proof = copy.deepcopy(base)
            proof.update(text=text, renderedText=text, rect=dict(x=pane['x'] + 15 + i * 186, y=bottom - 41, width=174, height=36), clipAreas=[])
            fragments = [dict(x=proof['rect']['x'], y=bottom - 41 + j * 18, width=170 if j == 0 else 100, height=14, visible=True) for j in range(2)]
            proof.update(fragments=fragments, textRuns=[dict(text=text, opaque=True, unscaled=True, fontSize=12, foreground=[87, 111, 120], background=[255, 255, 255], clipAreas=[], fragments=copy.deepcopy(fragments))])
            labels.append(dict(tag='SPAN', id='np-canvas-count' if i == 0 else '', proof=proof))
        data['treeFooter'] = dict(count=1, proof=base, inPane=True, insideTree=False, sourcePosition=data['route']['node'], sourceChildCount=2, labels=labels)

    @classmethod
    def method_shell(cls, width=1440):
        data = DesktopHierarchyContractChecks.shell('l', width)
        data.update(methodReading='true', readingLayout='reading', position=dict(id='exact-method', kind='pipeline_recipe', paper='paper', version='version'))
        data['route'].update(node='exact-method', paper='paper', version='version')
        delta = data['treePane']['width'] - (400 if width == 1440 else 448)
        data['treePane']['width'] -= delta; data['tree']['width'] -= delta
        for key in ('pane', 'reader'):
            data[key]['x'] -= delta; data[key]['width'] += delta
        for key in ('heading', 'title', 'meta'):
            data[key]['rect']['x'] -= delta; data[key]['rect']['width'] += delta
        cls.add_method_footer(data)
        return data

    @classmethod
    def relation_shell(cls, width=1440):
        data = DesktopHierarchyContractChecks.shell('l', width)
        data['relation'] = 'methods:relation:90'
        data['title']['text'] = 'SemExp → PONI · 复用组件并替换策略'
        data['meta']['text'] = '当前范围关系 · CVPR 2022 accepted proceedings'
        cls.add_return_control(data)
        return data

    def test_relation_return_requires_disjoint_real_boxes_and_original_title_hit_gate(self):
        import copy
        for width in (1440, 1920):
            good = self.relation_shell(width)
            MODULE.check_desktop_shell(good)
            # A wrapping title may take another line; no fixed title-height exemption.
            wrapped = copy.deepcopy(good)
            wrapped['title']['rect']['height'] = 40
            MODULE.check_desktop_shell(wrapped)
            mutations = [lambda d: d['title']['rect'].update(width=d['meta']['rect']['width']),
                         lambda d: d['title'].update(visible=False), lambda d: d['title'].update(clipped=True),
                         lambda d: d['title'].update(opaque=False), lambda d: d['meta'].update(visible=False),
                         lambda d: d['returnControl']['proof'].update(visible=False), lambda d: d['returnControl']['proof'].update(clipped=True),
                         lambda d: d['returnControl']['proof']['rect'].update(y=d['meta']['rect']['y']),
                         lambda d: d['returnControl']['proof']['rect'].update(x=d['heading']['rect']['x'] + d['heading']['rect']['width']),
                         lambda d: d['returnControl'].update(inHeading=False), lambda d: d['returnControl'].update(insideScroll=True),
                         lambda d: d['returnControl'].update(disabled=True), lambda d: d['returnControl'].update(tag='SPAN'),
                         lambda d: d['returnControl']['proof'].update(text='返回'), lambda d: d.update(returnControlCount=2),
                         lambda d: d.update(returnControlCount=0, returnControl=None)]
            for index, mutate in enumerate(mutations):
                bad = copy.deepcopy(good); mutate(bad)
                with self.subTest(width=width, mutation=index), self.assertRaises(RuntimeError):
                    MODULE.check_desktop_shell(bad)

    def test_fixed_relation_title_and_source_version_cannot_be_replaced_by_other_readable_text(self):
        import copy, gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        expected = MODULE.task_route_expected(science)
        good = self.relation_shell()
        MODULE.check_desktop_relation_heading(good, expected)
        for mutate in (lambda d: d['title'].update(text='PONI'), lambda d: d['meta'].update(text='当前范围关系 · arXiv v1'),
                       lambda d: d.update(titleRelation='methods:relation:88'), lambda d: d.update(relation='methods:relation:88'),
                       lambda d: d['title'].update(visible=False)):
            bad = copy.deepcopy(good); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_desktop_relation_heading(bad, expected)

    def test_method_footer_preserves_complete_wrapped_labels_and_no_return_method_heading(self):
        import copy
        for width in (1440, 1920):
            good = self.method_shell(width)
            heading = copy.deepcopy({k: good[k] for k in ('heading', 'title', 'meta')})
            MODULE.check_desktop_shell(good)
            self.assertEqual(good['returnControlCount'], 0)
            self.assertIsNone(good['returnControl'])
            self.assertEqual({k: good[k] for k in heading}, heading)
            self.assertEqual(len(good['treeFooter']['labels'][0]['proof']['fragments']), 2)
            self.assertEqual(good['treeFooter']['labels'][0]['proof']['fontSize'], 12)
            # Ordinary task/C/A footer sizing is not constrained by the method-only gate.
            for tree in ('l', 'c', 'a'):
                ordinary = DesktopHierarchyContractChecks.shell(tree, width)
                ordinary['treeFooter'] = {'proof': {'rect': {'height': 24}}}
                MODULE.check_desktop_shell(ordinary)

    def test_method_footer_rejects_hidden_clipped_offpane_overlapping_or_shortened_text(self):
        import copy
        for width in (1440, 1920):
            good = self.method_shell(width)
            def label(d): return d['treeFooter']['labels'][1]['proof']
            mutations = [lambda d: d['treeFooter']['proof'].update(clipped=True),
                         lambda d: d['treeFooter']['proof'].update(visible=False),
                         lambda d: d['treeFooter']['proof']['rect'].update(height=24),
                         lambda d: d['treeFooter']['proof']['rect'].update(y=d['tree']['y'] + d['tree']['height'] - 8),
                         lambda d: d['treeFooter']['proof']['rect'].update(y=d['treePane']['y'] + d['treePane']['height'] - 8),
                         lambda d: d['tree'].update(height=d['tree']['height'] + 8),
                         lambda d: d['treeFooter'].update(insideTree=True), lambda d: d['treeFooter'].update(inPane=False),
                         lambda d: d['treeFooter'].update(count=2), lambda d: d.update(treeFooter=None),
                         lambda d: label(d).update(text='选择节点深入'), lambda d: label(d).update(renderedText='选择节点深入'),
                         lambda d: label(d).update(visible=False), lambda d: label(d).update(clipped=True),
                         lambda d: label(d).update(fontSize=11), lambda d: label(d).update(foreground=[200, 200, 200]),
                         lambda d: label(d)['textRuns'][0].update(opaque=False), lambda d: label(d)['textRuns'][0].update(unscaled=False),
                         lambda d: label(d)['textRuns'][0].update(fragments=[]), lambda d: label(d)['textRuns'][0].update(text='选择节点深入'),
                         lambda d: label(d)['fragments'][1].update(visible=False),
                         lambda d: label(d)['fragments'][1].update(x=label(d)['rect']['x'] - 5),
                         lambda d: label(d)['fragments'][1].update(y=d['treePane']['y'] + d['treePane']['height'] + 3),
                         lambda d: label(d)['textRuns'][0]['fragments'][1].update(y=d['viewport']['height'] + 1),
                         lambda d: label(d)['textRuns'][0].update(clipAreas=[dict(x=0, y=0, width=width, height=800)]),
                         lambda d: label(d)['rect'].update(x=d['treeFooter']['labels'][0]['proof']['rect']['x']),
                         lambda d: d['treeFooter']['labels'].pop(), lambda d: d['treeFooter'].update(sourcePosition='other-method'),
                         lambda d: d['treeFooter'].update(sourceChildCount=1), lambda d: d['routeRows'].pop(),
                         lambda d: d['permanentScrollIds'].append('footer-scroll')]
            for index, mutate in enumerate(mutations):
                bad = copy.deepcopy(good); mutate(bad)
                with self.subTest(width=width, mutation=index), self.assertRaises(RuntimeError):
                    MODULE.check_desktop_shell(bad)

    def test_production_snapshot_measures_real_return_and_method_footer_without_changing_route(self):
        import gzip
        science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        body = r"""
// DOM identity and text only; JSDOM is not browser layout evidence.
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};
const shell=new w.Function(input.shellSnapshot);
await scope('task:category-objectnav');const ordinary=shell();assert.equal(ordinary.returnControlCount,0);assert.equal(ordinary.returnControl,null);assert.equal(ordinary.treeFooter,null);
d.getElementById('np-task-route-relations-summary').click();d.querySelector('[data-task-change="methods:relation:90"]').click();await ready(()=>d.querySelector('[data-selected-task-relation]')&&d.querySelector('[data-relation-state]')?.dataset.relationState==='ready');
const before=JSON.stringify(a.getState()),relation=shell();assert.equal(JSON.stringify(a.getState()),before);assert.equal(relation.returnControlCount,1);assert.equal(relation.returnControl.tag,'BUTTON');assert.equal(relation.returnControl.inHeading,true);assert.equal(relation.returnControl.insideScroll,false);assert.equal(relation.titleRelation,'methods:relation:90');assert.equal(relation.treeFooter,null);states.push(relation);
d.querySelector('[data-change-target="'+e.poni.id+'"]').click();await ready(()=>a.getState().route.node===e.poni.id&&a.getContent().ready(e.poni.entityId));
const methodState=JSON.stringify(a.getState()),method=shell(),footer=method.treeFooter;assert.equal(JSON.stringify(a.getState()),methodState);assert.equal(method.returnControlCount,0);assert.equal(method.returnControl,null);assert.equal(footer.count,1);assert.equal(footer.inPane,true);assert.equal(footer.insideTree,false);assert.equal(footer.sourcePosition,e.poni.id);assert.equal(footer.sourceChildCount,e.poni.childIds.length);
assert.deepEqual(JSON.parse(JSON.stringify(footer.labels.map(x=>[x.tag,x.id]))),[['SPAN','np-canvas-count'],['SPAN','']]);assert.equal(footer.labels[0].proof.renderedText,method.routeRows.length+' 个来路与分枝节点 · '+e.poni.childIds.length+' 个直接子节点');assert.equal(footer.labels[1].proof.renderedText,'选择节点深入 · ＋展开 · 拖动空白平移');states.push(method);
const footerLabel=d.querySelector('.np-canvas-footer > span:last-child'),hidden=d.createElement('span');hidden.style.display='none';hidden.textContent='不能用隐藏文字冒充可见标签';footerLabel.appendChild(hidden);const hiddenProof=shell().treeFooter.labels[1].proof;assert.equal(hiddenProof.textRuns.at(-1).text,hidden.textContent);assert.equal(hiddenProof.textRuns.at(-1).opaque,false);hidden.remove();
"""
        states = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science), 'shellSnapshot': MODULE.DESKTOP_SHELL_SNAPSHOT_JS, 'viewport': {'width': 1440, 'height': 900}})
        self.assertEqual(states[0]['returnControl']['proof']['text'], '返回路线概览')
        self.assertEqual(states[1]['treeFooter']['labels'][1]['proof']['text'], '选择节点深入 · ＋展开 · 拖动空白平移')

    def test_fixed_text_snapshot_uses_every_wrapped_run_hit_and_clipping_ancestor(self):
        import copy
        good = self.method_shell()
        label = good['treeFooter']['labels'][0]['proof']
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<style>*{opacity:1;visibility:visible;transform:none;zoom:1;color:rgb(87,111,120);background-color:rgb(255,255,255);font-size:12px}span,b{display:inline}</style><section id="pane"><div id="footer" style="overflow-x:hidden;overflow-y:hidden"><span id="label">6 个来路与分枝节点 · <b>2 个直接子节点</b></span></div></section><div id="cover"></div>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,span=d.getElementById('label'),nested=span.querySelector('b'),footer=d.getElementById('footer'),pane=d.getElementById('pane'),proof=input.proof;
const style=w.getComputedStyle.bind(w);w.getComputedStyle=e=>new Proxy(style(e),{get:(t,k)=>k==='zoom'?(t.zoom||'1'):Reflect.get(t,k)});
const fragments=proof.fragments,boxes=new Map([[pane,input.pane],[footer,input.footer],[span,proof.rect],[nested,fragments[1]]]);let clipHeight=input.footer.height,cover=false;
for(const el of d.querySelectorAll('*')){el.getBoundingClientRect=()=>boxes.get(el)||input.viewport;for(const [key,value] of Object.entries({clientTop:0,clientLeft:0}))Object.defineProperty(el,key,{value});for(const key of ['clientWidth','scrollWidth'])Object.defineProperty(el,key,{get:()=>el.getBoundingClientRect().width});for(const key of ['clientHeight','scrollHeight'])Object.defineProperty(el,key,{get:()=>el===footer&&key==='clientHeight'?clipHeight:el.getBoundingClientRect().height});}
w.Range.prototype.getClientRects=function(){return [this.startContainer.parentElement===nested?fragments[1]:fragments[0]];};
d.elementFromPoint=(x,y)=>cover&&y>=fragments[1].y?d.getElementById('cover'):y>=fragments[1].y?nested:span;
const read=new w.Function(input.script+';return fixedTextProof(arguments[0]);'),normal=read(span);
assert.equal(normal.renderedText,proof.text);assert.equal(normal.textRuns.length,2);assert.equal(normal.fragments.length,2);assert.equal(normal.visible,true);assert.equal(normal.textRuns[1].fragments[0].visible,true);assert.equal(normal.clipAreas.length,1);
nested.style.display='none';const hidden=read(span);assert.equal(hidden.textRuns[1].opaque,false);nested.style.display='';
cover=true;const covered=read(span);assert.equal(covered.textRuns[1].fragments[0].visible,false);cover=false;
clipHeight=24;const clipped=read(span);assert.equal(clipped.clipAreas[0].height,24);assert.equal(clipped.textRuns[1].clipAreas[0].height,24);
process.stdout.write(JSON.stringify([normal,hidden,covered,clipped]));}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.VISUAL_GEOMETRY + MODULE.FIXED_TEXT_PROOF_JS,
                                'proof': label, 'pane': good['treePane'], 'footer': good['treeFooter']['proof']['rect'], 'viewport': good['viewport']}),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        normal, *broken = json.loads(result.stdout)
        good['treeFooter']['labels'][0]['proof'] = normal
        MODULE.check_method_footer(good)
        for index, proof in enumerate(broken):
            bad = copy.deepcopy(good); bad['treeFooter']['labels'][0]['proof'] = proof
            with self.subTest(index=index), self.assertRaises(RuntimeError): MODULE.check_method_footer(bad)

    def test_snapshot_extension_preserves_five_point_title_proof_and_exact_scene_plan(self):
        import inspect
        self.assertEqual(len(MODULE.SCENE_NAMES), 53)
        self.assertEqual(MODULE.VIEWPORTS, [(1440, 900), (1920, 1080)])
        self.assertIn('heading:proof(header),title:proof(title),meta:proof(meta)', MODULE.DESKTOP_SHELL_SNAPSHOT_JS)
        self.assertIn("[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]]", MODULE.VISUAL_GEOMETRY)
        self.assertIn("check_desktop_relation_heading(record['relation'], expected)", inspect.getsource(MODULE.desktop_hierarchy_checks))
        self.assertIn("check_desktop_relation_heading(record['relationScrolled'], expected)", inspect.getsource(MODULE.desktop_hierarchy_checks))
        self.assertIn("check_method_footer(data)", inspect.getsource(MODULE.check_desktop_shell))
        self.assertIn("...(footer?[footer,...footer.querySelectorAll('*')]:[])", MODULE.DESKTOP_SHELL_SNAPSHOT_JS)


class MethodKeyTraceChecks(unittest.TestCase):
    """Reconstructed 0→145→12 receipt offsets; the next Chrome run owns actual geometry."""

    @staticmethod
    def fixture(source='method', root='root', target='root', key='Home', top=145):
        import copy
        def row(identity, y):
            return dict(id='np-node-'+identity,position=identity,rect=dict(x=28,y=y,width=360,height=84),itemMarginTop=4,rowScrollMarginBlockStart='0px')
        frame=dict(route=dict(tree='g',node=source),methodReading='true',window=dict(x=0,y=0),active='np-node-child',
                   tree=dict(id='np-tree-scroll',connected=True,top=top,left=0,scrollHeight=601,scrollWidth=398,
                             rect=dict(x=17,y=382,width=398,height=456),clientRect=dict(x=17,y=382,width=398,height=456),paddingTop=8,scrollPaddingBlockStart='12px'),
                   root=row(root,382+12-top),target=row(target,382+12-top))
        events=[dict(phase=phase,key=key,code=key,isTrusted=True,defaultPrevented=phase=='bubble',eventTarget='np-node-child',snapshot=copy.deepcopy(frame)) for phase in ('capture','bubble')]
        return dict(scope='method-tree-key',source=source,root=root,target=target,key=key,eventLimit=2,before=frame,events=events,overflow=0,after=copy.deepcopy(frame),cleanedUp=True)

    def probe(self, **case):
        script=r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case;let top=145,throwRect=false;
const rows={};for(const id of ['root','method','child']){const row={getBoundingClientRect:()=>({x:28,y:382+(id==='root'?12:id==='method'?375:540)-top,width:360,height:id==='root'?84:60})};rows[id]={id:'np-node-'+id,dataset:{position:id},firstElementChild:row};}
const listeners=[];const tree={id:'np-tree-scroll',isConnected:true,scrollLeft:0,scrollHeight:601,scrollWidth:398,clientLeft:0,clientTop:0,clientWidth:398,clientHeight:456,
 get scrollTop(){return top;},getBoundingClientRect(){if(throwRect)throw Error('snapshot failed');return {x:17,y:382,width:398,height:456};},
 addEventListener:(type,fn,capture)=>listeners.push({type,fn,capture}),removeEventListener:(type,fn,capture)=>{const i=listeners.findIndex(x=>x.type===type&&x.fn===fn&&x.capture===capture);if(i>=0)listeners.splice(i,1);}};
global.window=global;global.scrollX=0;global.scrollY=0;global.NavigationProductApp={getState:()=>({route:{tree:'g',node:'method'}})};
const app={dataset:{methodReading:'true'}};global.document={activeElement:rows.child,getElementById:id=>id==='np-tree-scroll'?tree:id==='navigation-product'?app:c.missing&&id==='np-node-root'?null:rows[id.replace('np-node-','')]};
global.getComputedStyle=e=>e===tree?{paddingTop:'8px',scrollPaddingBlockStart:(c.old?0:12)+'px'}:{marginTop:'4px',scrollMarginBlockStart:'0px'};
let start=null,result=null,error=null,probe=null;
try{start=new Function(input.start)('method','root','root','Home');probe=window.__npMethodKeyTrace;
 if(c.preScroll)top=111;
 const event={key:'Home',code:'Home',isTrusted:!c.untrusted,defaultPrevented:false,target:rows.child};
 for(const l of listeners.filter(x=>x.capture))l.fn(event);
 // Native nearest aligns the existing root offset against the scroll-padding
 // edge. 12=8px pane padding+4px first-li margin, inferred from exact CSS.
 const rootY=12-top,paddedTop=c.old?0:12;if(rootY<paddedTop)top=Math.max(0,top+rootY-paddedTop);
 event.defaultPrevented=true;document.activeElement=rows.root;
 for(const l of listeners.filter(x=>!x.capture))l.fn(event);
 if(c.extra)for(let n=0;n<10;n++)for(const l of listeners)l.fn(event);
 if(c.failSnapshot)throwRect=true;
 result=new Function(input.stop)();
}catch(e){error=String(e);if(window.__npMethodKeyTrace){try{result=new Function(input.stop)();}catch(_){} }}
process.stdout.write(JSON.stringify({start,result,error,listeners:listeners.length,installed:!!window.__npMethodKeyTrace,top,cleanedUp:probe?.state.cleanedUp}));
"""
        result=subprocess.run(['node','-e',script],input=json.dumps(dict(case=case,start=MODULE.METHOD_KEY_TRACE_START_JS,stop=MODULE.METHOD_KEY_TRACE_STOP_JS)),
                              text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr)
        return json.loads(result.stdout)

    def test_method_only_css_padding_matches_existing_8_plus_4_without_layout_changes(self):
        import re
        css=(Path(__file__).parents[1]/'assets/navigation-product.css').read_text()
        rules=re.findall(r'#navigation-product\[data-method-reading=true\] \.np-tree-scroll\s*\{([^}]*)\}',css)
        self.assertEqual(rules,['padding:8px 10px;scroll-padding-block-start:12px;'])
        self.assertEqual(css.count('scroll-padding-block-start:'),1)
        self.assertIn('#navigation-product[data-method-reading=true] .np-tree li {margin:4px 0;}',css)
        # Method-only rule is nested in the existing desktop1200px media block.
        index=css.index('#navigation-product[data-method-reading=true] .np-tree-scroll')
        self.assertGreater(css.rfind('@media (min-width:1200px)',0,index),css.rfind('@media (max-width:',0,index))

    def test_receipt_145_home12_old_red_and_scroll_padding12_zero_green(self):
        old,new=self.probe(old=True),self.probe()
        self.assertEqual((old['top'],new['top']),(12,0))
        for data in (old,new):
            self.assertIsNone(data['error']);self.assertFalse(data['installed']);self.assertEqual(data['listeners'],0)
            trace=data['result'];MODULE.check_method_key_trace(trace,'method','root','root','Home')
            self.assertEqual(trace['before']['tree']['top'],145)
            self.assertEqual(trace['events'][0]['snapshot']['tree']['top'],145)
            self.assertEqual(trace['events'][1]['snapshot']['tree']['top'],data['top'])
            self.assertEqual(trace['after']['root']['rect']['y'],382+12-data['top'])
        before=dict(route={},originTrail=[],historyLength=1,expanded={},window=dict(x=0,y=0),readerScroll=dict(top=0,left=0),methodReading='true',roving=['method'],treeScroll=dict(top=0,left=0))
        for top in (12,1,145):
            with self.assertRaises(RuntimeError): MODULE.check_method_navigation_transition(before,dict(before,treeScroll=dict(top=top,left=0)),exact_tree_scroll=True)
        MODULE.check_method_navigation_transition(before,dict(before),exact_tree_scroll=True)

    def test_pre_key_transport_scroll_is_distinct_from_product_handler_scroll(self):
        trace=self.probe(preScroll=True)['result']
        self.assertEqual([trace['before']['tree']['top'],trace['events'][0]['snapshot']['tree']['top'],trace['events'][1]['snapshot']['tree']['top'],trace['after']['tree']['top']],[145,111,0,0])
        for forbidden in ('.focus(','.scrollIntoView(','.scrollTo(','.preventDefault(','.click(','scrollTop=','scrollLeft=','replaceState','pushState'):
            self.assertNotIn(forbidden,MODULE.METHOD_KEY_TRACE_START_JS+MODULE.METHOD_KEY_TRACE_STOP_JS)

    def test_trace_bound_missing_scope_and_finally_cleanup_are_fail_closed(self):
        extra=self.probe(extra=True)
        self.assertEqual(len(extra['result']['events']),2);self.assertEqual(extra['result']['overflow'],3)
        with self.assertRaises(RuntimeError): MODULE.check_method_key_trace(extra['result'],'method','root','root','Home')
        for case in (dict(failSnapshot=True),dict(missing=True)):
            data=self.probe(**case);self.assertTrue(data['error']);self.assertFalse(data['installed']);self.assertEqual(data['listeners'],0)
        self.assertTrue(self.probe(failSnapshot=True)['cleanedUp'])
        with self.assertRaises(RuntimeError): MODULE.check_method_key_trace(self.probe(untrusted=True)['result'],'method','root','root','Home')

    def test_trace_does_not_excuse_wrong_context_missing_phases_or_invalid_geometry(self):
        import copy
        good=self.fixture();MODULE.check_method_key_trace(good,'method','root','root','Home')
        mutations=[lambda d:d.update(cleanedUp=False),lambda d:d.update(eventLimit=3),lambda d:d.update(after=None),lambda d:d['events'].pop(),
                   lambda d:d['events'][0].update(phase='bubble'),lambda d:d['events'][1].update(defaultPrevented=False),
                   lambda d:d['events'][0].update(key='End'),lambda d:d['after']['route'].update(node='other'),
                   lambda d:d['after']['tree'].update(connected=False),lambda d:d['after']['root'].update(position='other'),
                   lambda d:d['after']['target']['rect'].update(height=0),lambda d:d['after']['tree']['clientRect'].update(y=float('nan'))]
        for mutate in mutations:
            bad=copy.deepcopy(good);mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_method_key_trace(bad,'method','root','root','Home')

    def test_actual_thirteen_key_orchestration_keeps_exact_gate_and_cleans_failed_input(self):
        import copy
        path=['root','literature','tasks','objectnav','route','method','child'];chain=path[:-1];test=self
        before=dict(route=dict(tree='g',node='method'),originTrail=[],historyLength=15,expanded=dict(g=chain),window=dict(x=0,y=0),
                    readerScroll=dict(top=0,left=0),treeScroll=dict(top=0,left=0),methodReading='true',focus='np-node-method',roving=['method'],siblings=[])
        class Driver:
            def __init__(self, old=False, fail=False):self.state=copy.deepcopy(before);self.old=old;self.fail=fail;self.live=False;self.keys=[];self.cleanups=0
            def js(self, script,*args):
                if script==MODULE.METHOD_NAVIGATION_STATE_JS:return copy.deepcopy(self.state)
                if script==MODULE.METHOD_KEY_TRACE_START_JS:
                    test.assertFalse(self.live);self.live=True;self.source,self.root,self.target,self.key=args
                    return test.fixture(*args)
                if script==MODULE.METHOD_KEY_TRACE_STOP_JS:
                    test.assertTrue(self.live);self.live=False;self.cleanups+=1;return test.fixture(self.source,self.root,self.target,self.key)
                raise AssertionError('unexpected script')
            def selector(self,selector):return {MODULE.ELEMENT:'focused-node'}
            def call(self,method,url,data):
                self.keys.append(data['text'])
                if self.fail:raise RuntimeError('native input failed')
                if self.target=='child':self.state['treeScroll']['top']=145
                elif self.target=='root' and self.state['treeScroll']['top']>0:self.state['treeScroll']['top']=12 if self.old else 0
                self.state.update(focus='np-node-'+self.target,roving=[self.target])
            def settle(self):pass
        for old,fail in ((False,False),(True,False),(False,True)):
            driver=Driver(old,fail);report={};saved=[]
            with patch.object(MODULE,'method_visible_source_ids',return_value=path):
                if old or fail:
                    with self.assertRaisesRegex(RuntimeError,'exact tree scroll' if old else 'native input failed'):
                        MODULE.method_navigation_checks(driver,report,lambda:saved.append(copy.deepcopy(report)),'1440x900',dict(position=dict(id='method',tree='g'),chain=chain),{})
                else:MODULE.method_navigation_checks(driver,report,lambda:saved.append(copy.deepcopy(report)),'1440x900',dict(position=dict(id='method',tree='g'),chain=chain),{})
            expected_keys=['\ue011']+['\ue015']*6+['\ue011']+['\ue015']*5
            self.assertEqual(driver.keys,expected_keys[:1] if fail else expected_keys)
            self.assertEqual(driver.cleanups,len(driver.keys));self.assertFalse(driver.live)
            self.assertTrue(saved[-1]['methodNavigationChecks'][0]['steps'][-1]['trace']['cleanedUp'])
            if not old and not fail:self.assertEqual(report['methodNavigationChecks'][0]['status'],'verified_native_keyboard')


class ScrollRegionVisibilityChecks(unittest.TestCase):
    def test_closed_details_body_is_excluded_but_summary_and_open_offscreen_scroll_remain(self):
        script = r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<style>*{opacity:1}.scroll{overflow-x:auto;overflow-y:auto}</style><div id="ancestor"><details id="disclosure"><summary id="first-summary" class="scroll"><span id="summary-child" class="scroll">Summary</span></summary><summary id="second-summary" class="scroll">Hidden second summary</summary><div id="np-peer-strip" class="np-peer-strip scroll">Body</div></details></div>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,ancestor=d.getElementById('ancestor'),details=d.getElementById('disclosure'),candidate=d.getElementById('np-peer-strip');let y=200;
for(const e of d.querySelectorAll('*'))e.getBoundingClientRect=()=>({x:20,y,width:300,height:120});
d.elementFromPoint=()=>{throw Error('Occlusion is not a scroll-container exemption');};
const read=new w.Function(input.script+';return scrollRegionCandidate(arguments[0]);'),closed=read(candidate);
assert.equal(closed.rendered,false);assert.deepEqual(JSON.parse(JSON.stringify(closed.blockedBy)),{reason:'closed-details',tag:'DETAILS',id:'disclosure'});assert.equal(closed.rect.height,120,'positive stale bounds must not defeat closed-details semantics');
assert.equal(read(d.getElementById('first-summary')).rendered,true);assert.equal(read(d.getElementById('summary-child')).rendered,true);assert.equal(read(d.getElementById('second-summary')).rendered,false);
details.open=true;assert.equal(read(candidate).rendered,true);y=5000;assert.equal(read(candidate).rendered,true,'open content below the viewport still supplies a third persistent scroll region');ancestor.style.overflow='hidden';assert.equal(read(candidate).rendered,true,'ancestor clipping is not an exemption');
const records=[closed,read(candidate)];
const nested=d.createElement('details'),nestedSummary=d.createElement('summary');nested.id='nested-disclosure';nestedSummary.textContent='Nested summary';nested.appendChild(nestedSummary);details.appendChild(nested);nested.appendChild(candidate);assert.equal(read(candidate).rendered,false);assert.equal(read(candidate).blockedBy.id,'nested-disclosure');nested.open=true;assert.equal(read(candidate).rendered,true);details.open=false;assert.equal(read(candidate).rendered,false);assert.equal(read(candidate).blockedBy.id,'disclosure');details.open=true;details.appendChild(candidate);nested.remove();
for(const [property,value,reason] of [['display','none','display-none'],['opacity','0','opacity-zero']]){ancestor.style[property]=value;const hidden=read(candidate);assert.equal(hidden.rendered,false);assert.equal(hidden.blockedBy.reason,reason);ancestor.style[property]='';}
ancestor.hidden=true;assert.equal(read(candidate).rendered,false);ancestor.hidden=false;
for(const value of ['hidden','collapse']){candidate.style.visibility=value;assert.equal(read(candidate).rendered,false);}candidate.style.visibility='visible';ancestor.style.visibility='hidden';assert.equal(read(candidate).rendered,true,'a visible child may override inherited visibility');ancestor.style.visibility='';
candidate.getBoundingClientRect=()=>({x:20,y,width:0,height:0});assert.equal(read(candidate).rendered,false);
process.stdout.write(JSON.stringify(records));}finally{dom.window.close();}
"""
        result = subprocess.run(['node', '-e', script], input=json.dumps({'script': MODULE.VISUAL_GEOMETRY + MODULE.SCROLL_REGION_VISIBILITY_JS}),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1])
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        closed, opened_offscreen = json.loads(result.stdout)
        data = DesktopHierarchyContractChecks.shell()
        data['permanentScrollIds'] += [closed['id']] if closed['rendered'] else []
        MODULE.check_desktop_shell(data)
        data['permanentScrollIds'] += [opened_offscreen['id']] if opened_offscreen['rendered'] else []
        with self.assertRaisesRegex(RuntimeError, 'exactly the tree and reader'):
            MODULE.check_desktop_shell(data)

    def test_actual_snapshot_keeps_generic_candidate_diagnostics_and_strict_two_region_gate(self):
        source = MODULE.DESKTOP_SHELL_SNAPSHOT_JS
        self.assertIn('scrollRegionCandidates:scrollCandidates', source)
        self.assertIn('scrollCandidates.filter(candidate=>candidate.rendered)', source)
        for forbidden in ('np-peer-strip', 'innerWidth', 'innerHeight', 'elementFromPoint', 'IntersectionObserver'):
            self.assertNotIn(forbidden, MODULE.SCROLL_REGION_VISIBILITY_JS)
        self.assertIn("['np-tree-scroll', 'np-detail-scroll']", __import__('inspect').getsource(MODULE.check_desktop_shell))


class SourceBoundScrollFixtureChecks(unittest.TestCase):
    def state(self, top=0, maximum=300):
        import copy
        metrics = {'id': 'np-detail-scroll', 'top': top, 'left': 0, 'scrollHeight': 600 + maximum, 'clientHeight': 600, 'maxTop': maximum}
        return {'route': {'scope': 'task:category-objectnav', 'tree': 'l', 'node': 'source-poni', 'paper': 'poni', 'version': 'original-version'},
                'position': {'id': 'source-poni', 'paper': 'poni', 'version': 'original-version'}, 'relation': None,
                'window': {'x': 0, 'y': 0}, 'historyIdentity': {'url':'exact-route','length':3,'entryKey':'entry','revision':2,'originTrail':[]},
                'treeState': {'positions':[{'id':'source-poni','selected':'true'}],'expanded':{'l':['root']}}, 'focusPosition':'source-poni', 'reader': metrics,
                'tree': dict(copy.deepcopy(metrics), id='np-tree-scroll', top=0), 'branches': []}

    def test_positive_wheel_requires_actual_overflow_headroom_delta_and_exact_source(self):
        import copy
        before, after = self.state(), self.state(top=180)
        MODULE.check_native_wheel_progress(before, after, 'reader')
        for mutate in (lambda b, a: b['reader'].update(scrollHeight=600, maxTop=0),
                       lambda b, a: b['reader'].update(top=300),
                       lambda b, a: a['reader'].update(top=0),
                       lambda b, a: a['route'].update(version='wrong-version'),
                       lambda b, a: a['position'].update(id='wrong-source'),
                       lambda b, a: a.update(relation='other-relation'),
                       lambda b, a: a['tree'].update(top=20),
                       lambda b, a: a['historyIdentity'].update(revision=3),
                       lambda b, a: a['historyIdentity']['originTrail'].append({'route':'wrong'}),
                       lambda b, a: a['treeState']['expanded']['l'].append('wrong'),
                       lambda b, a: a['window'].update(y=10),
                       lambda b, a: b['reader'].update(maxTop=float('nan')),
                       lambda b, a: b['reader'].update(clientHeight=0),
                       lambda b, a: b['reader'].update(scrollHeight=600)):
            b, a = copy.deepcopy(before), copy.deepcopy(after); mutate(b, a)
            with self.subTest(before=b, after=a), self.assertRaises(RuntimeError):
                MODULE.check_native_wheel_progress(b, a, 'reader')

    def test_short_relation_input_is_explicitly_not_a_positive_scroll(self):
        import copy
        def shell(maximum, top):
            d = self.state(top=top, maximum=maximum)
            return {**{k:d[k] for k in ('route','position','relation','window')},
                    'fixedIdentity': d['position'], 'title': {'text':'full source title','rect':{'x':20}},
                    'meta': {'text':'full source version','rect':{'x':20}},
                    'offsets': {'tree':{'top':0,'left':0},'reader':{'top':top,'left':0}},
                    'scrollMetrics': {'reader':d['reader']}}
        short = shell(0, 0)
        MODULE.check_fixed_reader_scroll(short, copy.deepcopy(short), positive=False)
        with self.assertRaises(RuntimeError): MODULE.check_fixed_reader_scroll(short, short, positive=True)
        before, after = shell(300, 0), shell(300, 180)
        MODULE.check_fixed_reader_scroll(before, after, positive=True)
        with self.assertRaises(RuntimeError): MODULE.check_fixed_reader_scroll(before, before, positive=False)
        for key, value in (('title', {'text':'shortened title'}), ('meta', {'text':'wrong version'}),
                           ('fixedIdentity', {'position':'wrong'}), ('offsets', {'tree':{'top':1},'reader':{'top':180}})):
            bad = copy.deepcopy(after); bad[key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError): MODULE.check_fixed_reader_scroll(before, bad, positive=True)

    def test_native_original_disclosure_preparation_records_metrics_and_rejects_no_overflow(self):
        import copy
        owner = self
        class Driver:
            def __init__(self, grows=True, wrong=False): self.open=False; self.calls=[]; self.grows=grows; self.wrong=wrong
            def js(self, script, *args):
                if script == MODULE.SCROLL_FIXTURE_SNAPSHOT_JS:
                    state = owner.state(maximum=300 if self.open and self.grows else 0)
                    if self.open and self.wrong: state['route']['version']='wrong'
                    return state
                if 'Ambiguous original content disclosure' in script:
                    return {'selector':'#np-evidence-panel > summary','text':'原文证据'} if not self.open else None
                return {'element':'original-summary'}
            def click(self, element): self.calls.append(element); self.open=True
            def settle(self): pass
        for grows, wrong, success in ((True,False,True),(False,False,False),(True,True,False)):
            record, driver = {}, Driver(grows,wrong)
            if success:
                actual = MODULE.prepare_scroll_fixture(driver, record, lambda:None, 'reader')
                self.assertEqual(actual['reader']['maxTop'],300)
                self.assertEqual(record['scrollPreparations'][0]['steps'][0]['nativeDisclosure']['text'],'原文证据')
            else:
                with self.assertRaises(RuntimeError): MODULE.prepare_scroll_fixture(driver, record, lambda:None, 'reader')
            self.assertEqual(len(driver.calls),1)
            self.assertEqual(record['scrollPreparations'][0]['initial']['reader']['maxTop'],0)

    def test_native_selected_focus_restores_before_wheel_without_rebuilding_or_reselecting(self):
        import copy, inspect
        owner = self
        class Driver:
            def __init__(self, stuck=False, wrong=False, rebuilt=False): self.n=0; self.calls=[]; self.stuck=stuck; self.wrong=wrong; self.rebuilt=rebuilt
            def js(self, script, *args):
                if script == MODULE.SCROLL_FIXTURE_SNAPSHOT_JS:
                    state=owner.state()
                    if self.n and self.wrong: state['route']['node']='other'
                    return state
                if script == MODULE.READER_DOM_ELEMENTS_JS: return ['original']
                if script == MODULE.READER_DOM_IDENTITY_JS:
                    return [dict(name=name,same=not self.rebuilt) for name in ('tree','selected','row','reader','method')]
                if script == MODULE.SELECTED_TREE_FOCUS_JS:
                    return {'target':'np-node-source-poni','active':'np-node-source-poni' if self.n and not self.stuck else 'source-summary','valid':True,'bound':2}
                raise AssertionError(script)
            def call(self,*args): self.calls.append(args);self.n+=1
            def settle(self): pass
        driver,record=Driver(),{}
        MODULE.restore_selected_tree_focus(driver,record,lambda:None)
        self.assertEqual(len(driver.calls),1)
        actions=driver.calls[0][2]['actions'][0]['actions']
        self.assertEqual([a['value'] for a in actions],['\ue008','\ue004','\ue004','\ue008'])
        self.assertEqual(record['nativeSelectedFocus']['focusPath'][-1]['active'],'np-node-source-poni')
        for args in ((True,False,False),(False,True,False),(False,False,True)):
            with self.subTest(args=args),self.assertRaises(RuntimeError):MODULE.restore_selected_tree_focus(Driver(*args),{},lambda:None)
        code=inspect.getsource(MODULE.reader_toggle_checks)
        self.assertLess(code.index('restore_selected_tree_focus('),code.index("'deltaY': 160"))
        helper=inspect.getsource(MODULE.restore_selected_tree_focus)
        for forbidden in ('.click(','.focus(','.navigate(','.scrollTop =','dispatchEvent'):
            self.assertNotIn(forbidden,helper)

    def test_native_action_failure_retains_after_metrics_and_original_error(self):
        owner=self
        class Driver:
            def __init__(self, diagnostic_fails=False):self.n=0;self.diagnostic_fails=diagnostic_fails
            def js(self,*args):
                self.n+=1
                if self.n>1 and self.diagnostic_fails:raise RuntimeError('diagnostic failed')
                return owner.state(top=0 if self.n==1 else 20)
            def settle(self):raise AssertionError('failed action must not settle')
        def reject():raise RuntimeError('native input rejected')
        for fail in (False,True):
            record={}
            with self.subTest(diagnostic_fails=fail),self.assertRaisesRegex(RuntimeError,'native input rejected'):
                MODULE.measured_fixture_action(Driver(fail),record,lambda:None,{'kind':'wheel'},reject)
            item=record['nativeScrollActions'][0]
            self.assertEqual(item['actionError'],'native input rejected')
            if fail:self.assertEqual(item['diagnosticError'],'diagnostic failed')
            else:self.assertEqual(item['after']['reader']['top'],20)

    def test_original_retention_child_rejects_wrong_parent_kind_version_and_ambiguity(self):
        import copy, gzip
        science=json.loads(gzip.decompress((Path(__file__).parents[1]/'data/navigation-product/model.json.gz').read_bytes()))
        pipeline=MODULE.task_route_expected(science)['poni']
        child=MODULE.literature_scroll_position(science,pipeline)
        self.assertEqual(child['id'],'pos:l:fda854f4cc082325e119d5')
        self.assertEqual(child['parentId'],pipeline['id'])
        for field,value in (('parentId','wrong'),('kind','pipeline_recipe'),('versionId','wrong'),('paperId','wrong'),('tree','c'),('scopeId','wrong')):
            bad=copy.deepcopy(science);bad['positions'][child['id']][field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError): MODULE.literature_scroll_position(bad,pipeline)
        bad=copy.deepcopy(pipeline);bad['childIds'].append(child['id'])
        with self.assertRaises(RuntimeError): MODULE.literature_scroll_position(science,bad)

    def test_source_native_child_ancestor_analysis_and_legacy_claim_routes(self):
        import gzip
        science=json.loads(gzip.decompress((Path(__file__).parents[1]/'data/navigation-product/model.json.gz').read_bytes()))
        expected=MODULE.task_route_expected(science)
        child=MODULE.literature_scroll_position(science,expected['poni'])
        body=r"""
await scope(e.poni.scopeId);await select(input.child.id);const saved=JSON.parse(JSON.stringify(a.getState().route));
assert.equal(d.getElementById('navigation-product').dataset.methodReading,'false');assert.equal(d.querySelector('#np-reader-analysis-entry [data-analysis-state]'),null);
const measurement=new w.Function(input.measurement);let measured=measurement();assert.equal(measured.position.id,input.child.id);assert.equal(measured.reader.clientHeight,0);assert.equal(measured.reader.maxTop,0);assert.ok(measured.branches.every(row=>row.children.length&&row.scope===saved.scope&&row.tree==='l'));
d.querySelector('[data-tree-tab="c"]').click();await ready(()=>a.getState().route.tree==='c');await select('pos:c:6a8a9d2f7b1f3ab3a8ada5');
d.querySelector('[data-tree-tab="l"]').click();await ready(()=>a.getState().route.node===input.child.id);assert.deepEqual(JSON.parse(JSON.stringify(a.getState().route)),saved);
await select(e.poni.id);const pipeline=JSON.parse(JSON.stringify(a.getState().route));assert.equal(pipeline.version,saved.version);assert.equal(d.querySelector('#np-reader-analysis-entry [data-analysis-state]').dataset.analysisState,'imported');
const claim=input.claim.id;assert.equal(m.validateRoute(a.getBundle(),{...pipeline,claim}).claim,claim);assert.throws(()=>m.validateRoute(a.getBundle(),{...saved,claim}),error=>error.code==='claim_mismatch');
d.getElementById('np-evidence-panel').querySelector(':scope > summary').click();await wait(35);assert.equal(d.getElementById('np-evidence-panel').open,true);
d.querySelector('#np-detail-content .np-evidence > summary').click();await wait(35);assert.ok(d.querySelector('[data-claim-id="'+claim+'"]'));assert.equal(a.getState().route.node,pipeline.node);assert.equal(a.getState().route.version,pipeline.version);
d.getElementById('np-open-version-analysis').click();await ready(()=>a.getState().route.tree==='a'&&a.getContent().ready(a.getBundle().positions[a.getState().route.node].entityId));assert.equal(s.positions[a.getState().route.node].kind,'analysis_answer');assert.equal(a.getState().route.version,pipeline.version);
d.querySelector('.np-return-previous').click();await ready(()=>a.getState().route.node===pipeline.node);await select(e.scopes[e.poni.scopeId].roots[0]);await select('pos:l:ff0298ffa17b4cfcf009bd');assert.equal(a.getState().route.version,'source:method-lineage:vlfm');states.push(snapshot());
"""
        states=run_product_capture_script(self,body,{'science':science,'expected':expected,'child':child,'claim':MODULE.task_route_claims(science,expected['poni'])[0],'measurement':MODULE.SCROLL_FIXTURE_SNAPSHOT_JS})
        self.assertEqual(states[0]['route']['paper'],'vlfm')

    def end_state(self, row_y=994.5, row_height=42):
        state=self.state(maximum=42)
        state['tree'].update(clientHeight=863,scrollHeight=905,maxTop=42)
        state['treeEndTarget']={'position':'source-poni','scope':state['route']['scope'],'tree':state['route']['tree'],
            'isFirstNodeRow':True,'row':{'x':53,'y':row_y,'width':996,'height':row_height},
            'viewport':{'x':17,'y':176,'width':1054,'height':863}}
        return state

    def test_end_readiness_rejects_padding_only_overflow_wrong_target_and_oversized_noop(self):
        import copy
        padding=self.end_state();MODULE.check_scroll_metrics(padding['tree'],headroom=True)
        self.assertFalse(MODULE.end_target_below_viewport(padding),'42px of annotation/padding overflow does not move the visible row')
        self.assertFalse(MODULE.end_target_below_viewport(self.end_state(row_y=997,row_height=42)),'a row ending exactly at the viewport edge is visible')
        self.assertTrue(MODULE.end_target_below_viewport(self.end_state(row_y=1050)))
        self.assertTrue(MODULE.end_target_below_viewport(self.end_state(row_y=1010)))
        for y,h in ((100,1000),(176,900)):
            self.assertFalse(MODULE.end_target_below_viewport(self.end_state(row_y=y,row_height=h)),'nearest is a no-op for a row spanning both viewport edges')
        for mutate in (lambda d:d.update(treeEndTarget=None),lambda d:d['treeEndTarget'].update(position='wrong-last'),
                       lambda d:d['treeEndTarget'].update(scope='wrong-scope'),lambda d:d['treeEndTarget'].update(tree='c'),
                       lambda d:d['treeEndTarget'].update(isFirstNodeRow=False),lambda d:d['tree'].update(top=1),
                       lambda d:d['treeEndTarget']['row'].update(height=0),lambda d:d['treeEndTarget']['viewport'].update(height=float('nan'))):
            bad=copy.deepcopy(padding);mutate(bad)
            with self.assertRaises(RuntimeError):MODULE.end_target_below_viewport(bad)

    def test_end_preparation_expands_real_branches_past_padding_overflow_but_wheel_does_not(self):
        import copy,inspect
        owner=self
        class Driver:
            def __init__(self,exhausted=False):self.clicks=0;self.exhausted=exhausted;self.native=[]
            def js(self,script,*args):
                if script==MODULE.SCROLL_FIXTURE_SNAPSHOT_JS:
                    state=owner.end_state(row_y=1050 if self.clicks else 994.5)
                    if self.clicks:state['tree'].update(scrollHeight=1000,maxTop=137)
                    state['branches']=[] if self.exhausted or self.clicks else [{'id':'original-branch','scope':state['route']['scope'],'tree':'l','children':['original-child'],'control':'np-node-original-branch','label':'Original source branch'}]
                    return state
                if 'Exact visible control absent' in script:self.native.append(args[0]);return {'original':'branch-toggle'}
                if 'scrollIntoView' in script:return None
                raise AssertionError(script)
            def click(self,element):self.clicks+=1
            def settle(self):pass
        record,driver={},Driver();actual=MODULE.prepare_scroll_fixture(driver,record,lambda:None,'tree',require_end_target=True)
        self.assertEqual(driver.clicks,1);self.assertEqual(record['scrollPreparations'][0]['scenario'],'native_original_end_row_below_viewport')
        self.assertEqual(driver.native,[{'selector':'[id="np-node-original-branch"] > .np-node-row > .np-node-toggle'}])
        self.assertTrue(MODULE.end_target_below_viewport(actual));self.assertEqual(actual['tree']['top'],0)
        wheel=Driver();MODULE.prepare_scroll_fixture(wheel,{},lambda:None,'tree');self.assertEqual(wheel.clicks,0,'wheel can use real padding overflow')
        with self.assertRaisesRegex(RuntimeError,'already visible'):MODULE.prepare_scroll_fixture(Driver(exhausted=True),{},lambda:None,'tree',require_end_target=True)
        code=inspect.getsource(MODULE.exploration_state_checks)
        self.assertIn("prepare_scroll_fixture(driver, record, save, 'tree', require_end_target=True)",code)
        self.assertIn("check_native_wheel_progress(before, after, 'tree')",code)
        self.assertIn("after['focusPosition'] != before['treeState']['positions'][-1]['id']",code)
        self.assertGreaterEqual(code.count('nonzero=True'),4)

    def test_end_preparation_natively_resets_and_remeasures_after_each_branch_reveal(self):
        owner=self
        class Driver:
            def __init__(self,stuck=False):self.phase=0;self.top=30;self.stuck=stuck;self.wheels=[]
            def js(self,script,*args):
                if script==MODULE.SCROLL_FIXTURE_SNAPSHOT_JS:
                    state=owner.end_state(row_y=(1050 if self.phase else 994.5)-self.top)
                    state['tree']['top']=self.top
                    if self.phase:state['tree'].update(scrollHeight=1000,maxTop=137)
                    state['branches']=[] if self.phase else [{'id':'original-branch','scope':state['route']['scope'],'tree':'l','children':['original-child'],'control':'np-node-original-branch','label':'Original branch'}]
                    return state
                if 'Exact visible control absent' in script:return {'original':'branch-toggle'}
                if 'scrollIntoView' in script:return None
                raise AssertionError(script)
            def selector(self,selector):return {'selector':selector}
            def click(self,element):self.phase=1;self.top=80
            def call(self,method,path,payload):
                self.wheels.append(payload['actions'][0]['actions'][0])
                if not self.stuck:self.top=0
            def settle(self):pass
        driver,record=Driver(),{}
        ready=MODULE.prepare_scroll_fixture(driver,record,lambda:None,'tree',require_end_target=True)
        self.assertEqual([action['deltaY'] for action in driver.wheels],[-905,-1000])
        self.assertTrue(all(action['type']=='scroll' and action['origin']=={'selector':'#np-tree-scroll'} for action in driver.wheels))
        preparation=record['scrollPreparations'][0]
        self.assertEqual([row['tree']['top'] for row in preparation['endStartResets']],[0,0])
        self.assertEqual(preparation['steps'][0]['after']['tree']['top'],80)
        self.assertEqual(ready['treeEndTarget']['row']['y'],1050)
        self.assertEqual(ready['tree']['top'],0);self.assertTrue(MODULE.end_target_below_viewport(ready))
        failed={}
        with self.assertRaisesRegex(RuntimeError,'at zero scroll'):
            MODULE.prepare_scroll_fixture(Driver(stuck=True),failed,lambda:None,'tree',require_end_target=True)
        self.assertEqual(failed['nativeScrollActions'][0]['after']['tree']['top'],30)

    def test_end_snapshot_measures_original_first_row_not_overflowing_item(self):
        script=r"""
const {JSDOM}=require('jsdom'),assert=require('node:assert/strict'),input=JSON.parse(require('fs').readFileSync(0,'utf8'));
const dom=new JSDOM('<!doctype html><div id="np-tree-scroll"><div id="np-tree"><section data-parallel-tree="c"><ul role="tree"><li role="treeitem" data-position="last"><div class="np-node-row">Exact last source row</div><span>Original annotation below row</span></li></ul></section></div></div>',{runScripts:'outside-only'});
try{const w=dom.window,d=w.document,tree=d.getElementById('np-tree-scroll'),item=d.querySelector('[role=treeitem]'),row=item.firstElementChild;
 w.NavigationProductApp={getBundle:()=>({positions:{last:{id:'last',tree:'c',scopeId:'original-scope'}}}),getState:()=>({route:{tree:'c',scope:'original-scope'}})};
 tree.getBoundingClientRect=()=>({x:16,y:175,width:1056,height:865});for(const [key,value] of Object.entries({clientLeft:1,clientTop:1,clientWidth:1054,clientHeight:863,scrollHeight:905}))Object.defineProperty(tree,key,{value});
 item.getBoundingClientRect=()=>({x:53,y:994.5,width:996,height:70});row.getBoundingClientRect=()=>({x:53,y:994.5,width:996,height:42});
 const snap=new w.Function(input.script+';return actualTreeEndTarget();'),out=snap();assert.equal(out.position,'last');assert.equal(out.row.height,42);assert.equal(out.viewport.y+out.viewport.height,1039);assert.ok(out.row.y+out.row.height<1039);assert.ok(item.getBoundingClientRect().y+item.getBoundingClientRect().height>1039);assert.equal(tree.scrollTop,0);
 row.className='not-the-source-row';assert.equal(snap().isFirstNodeRow,false);process.stdout.write(JSON.stringify(out));
}finally{dom.window.close();}
"""
        result=subprocess.run(['node','-e',script],input=json.dumps({'script':MODULE.END_TARGET_SNAPSHOT_JS}),cwd=Path(__file__).parents[1],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        target=json.loads(result.stdout);self.assertEqual(target['tree'],'c');self.assertEqual(target['scope'],'original-scope')
        for forbidden in ('scrollTop=', 'scrollTop =', '.scrollTo(', '.scrollIntoView(', '.focus(', '.click('):self.assertNotIn(forbidden,MODULE.END_TARGET_SNAPSHOT_JS)
        self.assertEqual(len(MODULE.SCENE_NAMES)*len(MODULE.VIEWPORTS),106)

    def test_all_shortened_fixture_sites_keep_native_positive_gates_and_98_scenes(self):
        import inspect
        desktop=inspect.getsource(MODULE.desktop_hierarchy_checks)
        self.assertIn("record['relationScrollScenario']",desktop)
        self.assertIn("check_native_wheel_progress(prepared, record['methodWheelMetrics'], 'reader')",desktop)
        self.assertIn("check_fixed_reader_scroll(record['methodBeforeWheel'], record['methodScrolled'], positive=True)",desktop)
        self.assertLess(desktop.index("entry_box['y']"),desktop.index('prepared = prepare_scroll_fixture'))
        exploration=inspect.getsource(MODULE.exploration_state_checks)
        self.assertIn("routes = [literature['route'], pipeline['route']",exploration)
        self.assertIn("claim_route = dict(pipeline['route']",exploration)
        self.assertIn("lambda: ready_node(literature['route']['node'])",exploration)
        self.assertIn("select(expected['scopes'][expected['poni']['scopeId']]['roots'][0])",exploration)
        self.assertIn('nonzero=True',exploration)
        delayed=inspect.getsource(MODULE.task_route_checks)
        self.assertIn("check_scroll_metrics(delayed['pendingScrollMetrics']['tree'], headroom=True)",delayed)
        self.assertIn("check_native_wheel_progress(delayed['pendingScrollMetrics'], delayed['newerScrollMetrics'], 'tree')",delayed)
        for fn in (MODULE.prepare_scroll_fixture,MODULE.desktop_hierarchy_checks,MODULE.exploration_state_checks):
            code=inspect.getsource(fn)
            for forbidden in ('style.', 'scrollTop=', 'scrollTop =', '.navigate(', 'dispatchEvent(', 'replaceState(', 'pushState('):
                self.assertNotIn(forbidden,code)
        self.assertEqual(len(MODULE.SCENE_NAMES)*len(MODULE.VIEWPORTS),106)


class WorkspaceSourceTabChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import sys
        with patch.object(sys, 'path', [str(Path(__file__).parents[1] / 'scripts'), *sys.path]):
            from navigation_research_map import build_research_map
            cls.graph = build_research_map(S0FooterCaptureChecks.source())
        cls.contract = MODULE.workspace_tab_source_contract(cls.graph)
        cls.root = cls.graph['roots'][0]
        cls.challenge = 'pos:g:ef16259815fbbfb1f944b9'
        cls.literature = next(p['id'] for p in cls.graph['positions'].values() if p['entityId'] == 'legacy:nav:l')

    def shell(self, node, selected):
        data = DesktopHierarchyContractChecks.shell()
        data['route'] = dict(tree='g', node=node, scope='scope:all', paper=None, version=None)
        data['chrome'] = desktop_chrome_fixture(route=data['route'])
        if node == self.root:
            data['chrome']['identitySource']['atRoot'] = True
            toggle = next(row for row in data['chrome']['controls'] if row['id'] == 'np-overview-toggle')
            toggle['hidden'] = False
            toggle['proof'].update(opaque=True, visible=True)
        for row in data['chrome']['controls']:
            if row['tree']: row['selected'] = str(row['tree'] == selected).lower()
        return data

    def test_frozen_global_paths_determine_one_branch_without_changing_source_tree(self):
        self.assertEqual(self.contract[self.root]['tab'], 'g')
        self.assertEqual(self.contract[self.literature]['tab'], 'l')
        self.assertEqual(self.contract[self.challenge], dict(tab='c', path=[
            dict(id='pos:g:62d6d6cb98df700cdd762e', parentId=None, entityId='legacy:nav:goal', tree='g', scopeId='scope:all'),
            dict(id='pos:g:4ff09ffb1b1dc4d549b8fe', parentId='pos:g:62d6d6cb98df700cdd762e', entityId='legacy:nav:c', tree='g', scopeId='scope:all'),
            dict(id=self.challenge, parentId='pos:g:4ff09ffb1b1dc4d549b8fe', entityId='legacy:ci_search_unknown_target', tree='g', scopeId='scope:all')]))
        descendant = next(identity for identity, value in self.contract.items() if value['tab'] == 'l' and len(value['path']) > 3)
        self.assertEqual(MODULE.workspace_selected_tree(dict(tree='g', scope='scope:all', node=descendant),
                         dict(tabSourceSha256=MODULE.WORKSPACE_TAB_SCIENCE_SHA256, tabPath=self.contract[descendant]['path'])), 'l')
        for tree in ('l', 'c', 'a'):
            MODULE.check_desktop_chrome(DesktopHierarchyContractChecks.shell(tree))
            self.assertEqual(MODULE.workspace_selected_tree(dict(tree=tree), {}), tree)

    def test_exact_challenge_chrome_rejects_old_g_expectation_and_wrong_or_multiple_tabs(self):
        import copy
        for node, selected in ((self.root, 'g'), (self.literature, 'l'), (self.challenge, 'c')):
            good = self.shell(node, selected)
            MODULE.check_desktop_chrome(good)
            self.assertEqual(good['route']['tree'], 'g')
            for wrong in ('g', 'l', 'c', 'a', None):
                if wrong == selected: continue
                bad = copy.deepcopy(good)
                for row in bad['chrome']['controls']:
                    if row['tree']: row['selected'] = str(row['tree'] == wrong).lower()
                with self.assertRaisesRegex(RuntimeError, 'selected source tree'): MODULE.check_desktop_chrome(bad)
            bad = copy.deepcopy(good)
            next(row for row in bad['chrome']['controls'] if row['tree'] and row['tree'] != selected)['selected'] = 'true'
            with self.assertRaisesRegex(RuntimeError, 'selected source tree'): MODULE.check_desktop_chrome(bad)

    def test_runtime_path_must_match_exact_source_even_when_selected_tab_looks_correct(self):
        import copy
        good = self.shell(self.challenge, 'c')
        mutations = [lambda s: s.pop('tabPath'), lambda s: s.update(tabPath=[]), lambda s: s.update(tabPath=None),
                     lambda s: s.update(tabSourceSha256='wrong'), lambda s: s['tabPath'].pop(0),
                     lambda s: s['tabPath'][1].update(entityId='legacy:nav:l'),
                     lambda s: s['tabPath'][-1].update(parentId='wrong'),
                     lambda s: s['tabPath'][0].update(id='another-root'),
                     lambda s: s['tabPath'][-1].update(scopeId='other'), lambda s: s['tabPath'][-1].update(tree='c'),
                     lambda s: s['tabPath'].append(copy.deepcopy(s['tabPath'][-1]))]
        for mutate in mutations:
            bad = copy.deepcopy(good); mutate(bad['chrome']['identitySource'])
            with self.assertRaisesRegex(RuntimeError, 'source path'): MODULE.check_desktop_chrome(bad)
        for route in (dict(tree='g', node='unknown', scope='scope:all'), dict(tree='g', node=self.challenge, scope='other'), dict(tree='unknown')):
            with self.assertRaises(RuntimeError): MODULE.workspace_selected_tree(route, good['chrome']['identitySource'])

    def test_source_builder_rejects_broken_cycle_wrong_root_and_ambiguous_branch(self):
        import copy
        for mutate in (lambda g: g.update(sourceModelSha256='wrong'), lambda g: g.update(roots=[self.challenge]),
                       lambda g: g['roots'].append(self.root),
                       lambda g: g['positions'][self.challenge].update(parentId='missing'),
                       lambda g: (g['positions'][self.challenge].update(parentId=self.challenge), g['positions'][self.challenge]['childIds'].append(self.challenge)),
                       lambda g: g['positions'][self.challenge].update(entityId='legacy:nav:l'),
                       lambda g: g['positions'][self.challenge].update(tree='c'),
                       lambda g: g['positions'][self.challenge].update(scopeId='wrong')):
            graph = copy.deepcopy(self.graph); mutate(graph)
            with self.assertRaises(RuntimeError): MODULE.workspace_tab_source_contract(graph)

    def test_source_cache_is_bound_to_model_path_and_reviewed_content_hash(self):
        import tempfile, gzip
        raw = gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            valid = Path(directory) / 'reviewed.gz'; valid.write_bytes(gzip.compress(raw))
            other = Path(directory) / 'other.gz'; other.write_bytes(gzip.compress(b'{}'))
            self.assertEqual(MODULE.load_workspace_tab_sources(str(valid), MODULE.WORKSPACE_TAB_SCIENCE_SHA256)[self.challenge]['tab'], 'c')
            for path, digest in ((str(valid), 'another-version'), (str(other), MODULE.WORKSPACE_TAB_SCIENCE_SHA256)):
                with self.assertRaisesRegex(RuntimeError, 'reviewed scientific source'): MODULE.load_workspace_tab_sources(path, digest)

    def test_browser_snapshot_records_raw_parent_path_and_rejects_cycles_without_ui_oracle(self):
        import copy
        script = r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),b={positions:input.positions,researchMap:{roots:input.roots},delivery:{sourceModelSha256:input.sha},scopes:[{id:'scope:all',label:'All'}],entities:{},papers:{},versions:{}};
global.window={NavigationProductApp:{getBundle:()=>b,getState:()=>({route:input.route})}};
global.document={querySelector:()=>null,querySelectorAll:()=>[],getElementById:()=>null,body:{clientWidth:1425},documentElement:{clientWidth:1425,getBoundingClientRect:()=>({x:0,y:0,width:1440,height:900})}};
global.getComputedStyle=()=>({scrollbarGutter:'stable'});
process.stdout.write(JSON.stringify(new Function(input.script+';return desktopChromeGeometry().identitySource;')()));
"""
        for mutation in ('normal', 'missing-parent', 'cycle'):
            positions = copy.deepcopy(self.graph['positions'])
            if mutation == 'missing-parent': positions[self.challenge]['parentId'] = 'missing'
            if mutation == 'cycle': positions[self.challenge]['parentId'] = self.challenge
            payload = dict(script=MODULE.VISUAL_GEOMETRY + MODULE.DESKTOP_CHROME_GEOMETRY_JS,
                           positions=positions, roots=self.graph['roots'], sha=MODULE.WORKSPACE_TAB_SCIENCE_SHA256,
                           route=dict(tree='g', node=self.challenge, scope='scope:all'))
            result = subprocess.run(['node', '-e', script], input=json.dumps(payload), text=True, capture_output=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            source = json.loads(result.stdout)
            if mutation == 'normal':
                self.assertEqual(source['tabPath'], self.contract[self.challenge]['path'])
                self.assertEqual(MODULE.workspace_selected_tree(payload['route'], source), 'c')
            else:
                self.assertIsNone(source['tabPath'])
                with self.assertRaises(RuntimeError): MODULE.workspace_selected_tree(payload['route'], source)
        self.assertIn('workspace_branch_tabs', MODULE.DISPLAY_CONTRACT_MIGRATIONS)
        self.assertNotIn('activeTree', MODULE.DESKTOP_CHROME_GEOMETRY_JS)


class RelationSelectorRevealChecks(unittest.TestCase):
    """Replay R91's measured scroll geometry without claiming browser pixels."""

    def probe(self, **case):
        fixture = r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case,relation='tasks:relation:91';
let top=0,left=0,calls=[];
const client={x:965,y:181.890625,width:403,height:322},rowHeight=36.25;
const buttonTop=c.buttonTop===undefined?338.640625:c.buttonTop,buttonHeight=c.buttonHeight||rowHeight;
const summary={getBoundingClientRect:()=>({x:977,y:191.890625-top,width:379,height:28})};
const menu={id:'np-task-relations',open:true,clientLeft:1,clientTop:1,clientWidth:403,clientHeight:322,scrollHeight:620,scrollWidth:403,
 get scrollTop(){return top;},get scrollLeft(){return left;},matches:()=>true,contains:e=>e===button,
 querySelector:s=>summary,getBoundingClientRect:()=>({x:964,y:180.890625,width:420,height:324})};
const button={id:'np-relation-select-'+relation,tagName:'BUTTON',dataset:{relationSelect:relation},closest:()=>menu,matches:()=>true,
 getBoundingClientRect:()=>({x:977-left,y:buttonTop-top,width:379,height:buttonHeight}),
 scrollIntoView:options=>{calls.push(options);if(c.noScroll)return;
  const r=button.getBoundingClientRect(),bottom=client.y+client.height;
  let delta=0;
  if(options.block==='center')delta=r.y+r.height/2-(client.y+client.height/2);
  else if(options.block==='nearest'){
   if(r.y<client.y&&r.y+r.height>bottom)delta=0;
   else if(r.y<client.y)delta=r.y-client.y;
   else if(r.y+r.height>bottom)delta=r.y+r.height-bottom;
  }else throw Error('Unknown native scroll option');
  top=Math.max(0,Math.min(menu.scrollHeight-menu.clientHeight,Math.round(top+delta)));
 }};
global.document={querySelectorAll:()=>[menu]};global.innerWidth=1440;global.innerHeight=900;global.scrollX=0;global.scrollY=0;
const data=new Function(input.script)(button,relation);
process.stdout.write(JSON.stringify({data,calls}));
"""
        script = MODULE.RELATION_SELECTOR_REVEAL_JS
        if case.pop('legacy_center', False):
            script = script.replace("e.scrollIntoView({block:'nearest',inline:'nearest'})", "e.scrollIntoView({block:'center'})")
        result = subprocess.run(['node', '-e', fixture], input=json.dumps(dict(script=script, case=case)),
                                text=True, capture_output=True, cwd=Path(__file__).parents[1], timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_exact_r91_geometry_rejects_old_fourteen_pixel_scroll_and_accepts_nearest(self):
        old = self.probe(legacy_center=True)['data']; new = self.probe()['data']
        self.assertEqual(old['before']['buttonRect'], dict(x=977, y=338.640625, width=379, height=36.25))
        self.assertEqual(old['after']['scrollTop'], 14)
        self.assertEqual(old['after']['summaryRect']['y'], 177.890625)
        self.assertAlmostEqual(old['after']['summaryRect']['y'] + .1 * 28, 180.690625)
        self.assertLess(180.690625, old['after']['clientRect']['y'])
        with self.assertRaisesRegex(RuntimeError, 'unnecessarily scrolled'):
            MODULE.check_relation_selector_reveal(old, 'tasks:relation:91')
        MODULE.check_relation_selector_reveal(new, 'tasks:relation:91')
        self.assertEqual(new['before'], new['after'])
        # Replay the original failing text predicate too; the summary's top hit
        # lies outside the client, independently of its still-visible text centre.
        for data, passes in ((old, False), (new, True)):
            frame = data['after']; area = frame['summaryRect']
            proof = S0FooterCaptureChecks.proof('7条有据对照与组合', area)
            proof['clipAreas'] = [frame['clientRect']]
            proof['visible'] = area['y'] + .1 * area['height'] >= frame['clientRect']['y']
            fragment = dict(x=992.890625, y=area['y'] + 3, width=130.453125, height=18, visible=True)
            proof['fragments'] = [fragment]; proof['textRuns'][0]['fragments'] = [fragment.copy()]
            if passes: MODULE.check_s0_text(proof, proof['text'], frame['viewport'])
            else:
                with self.assertRaises(RuntimeError): MODULE.check_s0_text(proof, proof['text'], frame['viewport'])

    def test_all_seven_existing_fitting_rows_remain_unscrolled(self):
        for i in range(7):
            result = self.probe(buttonTop=229.890625 + i * 36.25)
            MODULE.check_relation_selector_reveal(result['data'], 'tasks:relation:91')
            self.assertEqual(result['calls'], [dict(block='nearest', inline='nearest')])
            self.assertEqual(result['data']['before'], result['data']['after'])

    def test_target_that_needs_scrolling_is_revealed_and_noop_is_rejected(self):
        data = self.probe(buttonTop=540)['data']
        MODULE.check_relation_selector_reveal(data, 'tasks:relation:91')
        self.assertGreater(data['after']['scrollTop'], data['before']['scrollTop'])
        self.assertTrue(MODULE.rect_inside(data['after']['buttonRect'], data['after']['clientRect']))
        bad = self.probe(buttonTop=540, noScroll=True)['data']
        with self.assertRaisesRegex(RuntimeError, 'clipped or outside'):
            MODULE.check_relation_selector_reveal(bad, 'tasks:relation:91')

    def test_oversized_target_cannot_pass_as_revealed(self):
        data = self.probe(buttonTop=175, buttonHeight=360)['data']
        with self.assertRaisesRegex(RuntimeError, 'clipped or outside'):
            MODULE.check_relation_selector_reveal(data, 'tasks:relation:91')

    def test_missing_wrong_target_page_scroll_and_geometry_changes_fail(self):
        import copy
        good = self.probe()['data']
        for mutate in (lambda d: d.update(relation='wrong'), lambda d: d.update(requested=dict(block='center')),
                       lambda d: d['after'].update(buttonRelation='wrong'), lambda d: d['after'].update(buttonTag='DIV'),
                       lambda d: d['after'].update(menuCount=2), lambda d: d['after'].update(open=False),
                       lambda d: d['after'].update(topology=False), lambda d: d['after']['window'].update(y=1),
                       lambda d: d['after']['clientRect'].update(height=323), lambda d: d['after'].update(scrollLeft=1),
                       lambda d: d['after']['summaryRect'].update(y=180)):
            bad = copy.deepcopy(good); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_relation_selector_reveal(bad, 'tasks:relation:91')

    def test_reveal_receipt_is_saved_before_rejecting_unnecessary_scroll(self):
        import copy, inspect, ast
        test = self
        class Driver:
            def __init__(self, data): self.data = data
            def js(self, script, control, relation):
                test.assertEqual(script, MODULE.RELATION_SELECTOR_REVEAL_JS)
                test.assertEqual((control, relation), ('native-button', 'tasks:relation:91'))
                return self.data
        for legacy in (False, True):
            data = self.probe(legacy_center=legacy)['data']; report = {}; saved = []
            save = lambda: saved.append(copy.deepcopy(report))
            if legacy:
                with self.assertRaises(RuntimeError):
                    MODULE.reveal_relation_selector(Driver(data), 'native-button', 'tasks:relation:91', report, save)
            else: MODULE.reveal_relation_selector(Driver(data), 'native-button', 'tasks:relation:91', report, save)
            self.assertEqual(saved, [report])
            self.assertEqual(report['relationSelectorRevealChecks'], [data])
        main = inspect.getsource(MODULE.main)
        self.assertEqual(main.count("reveal_relation_selector(driver, control, expected['id'], report, save)"), 1)
        self.assertIn("before_selection = s0_footer_check('before-selection-' + expected['id'])", main)
        tree = ast.parse(inspect.getsource(MODULE))
        helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'reveal_relation_selector')
        saves = [n for n in ast.walk(helper) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']
        self.assertEqual(len(saves), 1)


class S0ToolbarPaintSettleChecks(unittest.TestCase):
    """Synthetic animation clocks test the protocol, not Chrome render evidence."""

    def probe(self, **case):
        fixture = r"""
const {JSDOM}=require('jsdom'),input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case;
const dom=new JSDOM('<div id="np-reading-landing"><div class="np-overview-map-toolbar"><button id="np-map-relations-toggle">显示全部关系</button></div></div><div id="np-workspace"><div class="np-workspace-bar"><div class="np-tabs"><button data-tree-tab="g" aria-selected="false">全景</button><button data-tree-tab="l" aria-selected="true">文献发展</button></div></div></div>');
global.document=dom.window.document;
const toolbar=document.querySelector(c.workspace?'.np-workspace-bar':'.np-overview-map-toolbar'),button=c.workspace?document.querySelector('[data-tree-tab=g]'):document.getElementById('np-map-relations-toggle'),other=c.workspace?document.querySelector('[data-tree-tab=l]'):null;
const outside=document.querySelector(c.workspace?'.np-overview-map-toolbar':'.np-workspace-bar');outside.getAnimations=()=>{throw Error('Unrelated toolbar was inspected');};
let now=0,nextId=1,queue=[],answer=null,callbacks=0,inspections=0;
global.performance={now:()=>now};
global.setTimeout=(fn,delay)=>{const id=nextId++;queue.push({id,at:now+delay,fn});return id;};
global.clearTimeout=id=>{queue=queue.filter(t=>t.id!==id);};
global.requestAnimationFrame=fn=>c.frozenFrames?nextId++:setTimeout(fn,16);
global.cancelAnimationFrame=clearTimeout;
class Transition{
 constructor(start,end,property='background-color',cancel=false){this.start=start;this.end=end;this.transitionProperty=property;this.cancelled=cancel;this.effect={target:button,getComputedTiming:()=>({duration:c.infinite?Infinity:c.invalidTiming?NaN:end-start,endTime:c.infinite?Infinity:end-start})};}
 get playState(){return c.paused?'paused':now<this.end||c.stuck||c.pending?'running':this.cancelled?'idle':'finished';}
 get pending(){return !!c.pending;}
 get currentTime(){return c.pending?null:Math.min(now-this.start,this.end-this.start);}
 get playbackRate(){return c.reverse?-1:1;}
 finish(){throw Error('Must not force animation completion');}
 cancel(){throw Error('Must not cancel an animation');}
}
global.CSSTransition=Transition;
let transitions=c.none?[]:c.replacement?[new Transition(0,48,'background-color',true),new Transition(48,208,'background-color')]:[new Transition(0,160,c.property||'background-color')];
if(c.workspace&&!c.none&&!c.replacement){for(const target of [button,other]){const a=new Transition(0,160,'color');a.effect.target=target;transitions.push(a);}const a=new Transition(0,160);a.effect.target=other;transitions.push(a);}
// A forever-running CSS animation is not a colour CSSTransition, and must not
// make this local wait depend on unrelated animation elsewhere in the app.
const unrelated={transitionProperty:'background-color',playState:'running',pending:false,effect:{target:button,getComputedTiming:()=>({duration:Infinity,endTime:Infinity})}};
toolbar.getAnimations=opts=>{if(!opts.subtree)throw Error('Toolbar descendants were not inspected');inspections++;
 if(c.churn)transitions.push(new Transition(now,now+1));
 return [...transitions.filter(a=>a.start<=now&&(now<a.end||c.stuck||c.pending||c.paused||c.infinite||c.invalidTiming||c.reverse)),...(c.unrelated?[unrelated]:[])];};
global.getComputedStyle=e=>{
 if(c.workspace){const running=!c.none&&now<(c.replacement?208:160),isTab=e===button||e===other;
  const bg=isTab&&(c.alpha||running)?'rgba(255, 255, 255, 0.4)':e===other?'rgb(255, 255, 255)':e===button?'rgba(0, 0, 0, 0)':'rgb(237, 241, 236)';
  const fg=e===button?(running?'rgb(105, 121, 128)':'rgb(107, 122, 130)'):(running?'rgb(51, 93, 77)':'rgb(49, 92, 75)');
  return {color:fg,backgroundColor:bg,borderTopColor:'rgb(49, 92, 75)',borderRightColor:'rgb(49, 92, 75)',borderBottomColor:'rgb(49, 92, 75)',borderLeftColor:'rgb(49, 92, 75)'};
 }
 const end=c.replacement?208:160,alpha=e===button&&(c.alpha||(!c.none&&now<end))?'rgba(240, 244, 239, 0.6)':e===button?'rgba(0, 0, 0, 0)':'rgb(255, 255, 255)';
 return {color:c.lowContrast?'rgb(220, 220, 220)':'rgb(49, 92, 75)',backgroundColor:alpha,borderTopColor:'rgb(136, 161, 142)',borderRightColor:'rgb(136, 161, 142)',borderBottomColor:'rgb(136, 161, 142)',borderLeftColor:'rgb(136, 161, 142)'};
};
if(c.missing)toolbar.remove();
if(c.unsupported)global.CSSTransition=undefined;
if(c.disappear)setTimeout(()=>toolbar.remove(),48);
if(c.replaceRoot)setTimeout(()=>{const replacement=toolbar.cloneNode(true);replacement.getAnimations=toolbar.getAnimations;toolbar.before(replacement);toolbar.className='detached-from-selector';},48);
const backgrounds=()=>new Function(input.visual+'\nreturn arguments[0].map(e=>bg(e));')([button,...(other?[other]:[])]);
const beforeBackgrounds=backgrounds();
new Function(input.script)(2000,value=>{answer=value;callbacks++;});
let steps=0;while(queue.length&&steps++<1000){queue.sort((a,b)=>a.at-b.at||a.id-b.id);const item=queue.shift();now=item.at;item.fn();}
if(!answer||steps>=1000)throw Error('Unbounded paint settlement');
const background=new Function(input.visual+'\nreturn bg(document.getElementById("np-map-relations-toggle"));')();
const foreground=new Function(input.visual+'\nreturn color(getComputedStyle(document.body).color).rgb;')();
process.stdout.write(JSON.stringify({answer,callbacks,inspections,background,foreground,steps,beforeBackgrounds,afterBackgrounds:backgrounds()}));
"""
        result = subprocess.run(['node', '-e', fixture], input=json.dumps(dict(
            case=case, script=MODULE.DESKTOP_CHROME_PAINT_SETTLE_JS if case.get('workspace') else MODULE.S0_TOOLBAR_PAINT_SETTLE_JS, visual=MODULE.VISUAL_GEOMETRY)),
            text=True, capture_output=True, cwd=Path(__file__).parents[1], timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_finite_colour_transition_finishes_naturally_and_keeps_rgba_evidence(self):
        data = self.probe(); result = data['answer']
        self.assertEqual(result['status'], 'settled')
        self.assertEqual(result['elapsedMs'], 176)
        self.assertEqual(data['callbacks'], 1)
        self.assertEqual(data['background'], [255, 255, 255])
        self.assertEqual(result['before']['colors'][1]['backgroundColor'], 'rgba(240, 244, 239, 0.6)')
        self.assertEqual(result['after']['colors'][1]['backgroundColor'], 'rgba(0, 0, 0, 0)')
        animation = result['before']['transitions'][0]
        self.assertEqual(animation['property'], 'background-color')
        self.assertEqual(animation['playState'], 'running')
        self.assertFalse(animation['pending'])
        self.assertEqual((animation['duration'], animation['endTime']), (160, 160))
        self.assertEqual(result['after']['transitions'], [])
        self.assertEqual(len(result['observedTransitions']), 1)

    def test_cancellation_and_replacement_transition_are_reenumerated(self):
        result = self.probe(replacement=True)['answer']
        self.assertEqual(result['status'], 'settled')
        self.assertEqual(result['elapsedMs'], 224)
        self.assertEqual(len(result['observedTransitions']), 2)
        self.assertEqual(result['observedTransitions'][1]['firstSeenMs'], 48)
        self.assertEqual(result['after']['transitions'], [])

    def test_longhand_border_colours_and_text_colour_are_waited(self):
        for prop in ('color', 'border-color', 'border-top-color', 'border-right-color', 'border-bottom-color', 'border-left-color'):
            with self.subTest(prop=prop):
                result = self.probe(property=prop)['answer']
                self.assertEqual(result['status'], 'settled')
                self.assertEqual(result['elapsedMs'], 176)
                self.assertEqual(result['observedTransitions'][0]['first']['property'], prop)

    def test_unrelated_animation_and_transform_do_not_extend_local_wait(self):
        for case in (dict(none=True, unrelated=True), dict(property='transform', unrelated=True)):
            result = self.probe(**case)['answer']
            self.assertEqual(result['status'], 'settled')
            self.assertEqual(result['elapsedMs'], 32)
            self.assertEqual(result['observedTransitions'], [])

    def test_stuck_pending_and_frozen_frame_paths_timeout_once(self):
        for case in (dict(stuck=True), dict(pending=True), dict(frozenFrames=True)):
            with self.subTest(case=case):
                data = self.probe(**case); result = data['answer']
                self.assertEqual(result['status'], 'timeout')
                self.assertEqual(result['elapsedMs'], 2000)
                self.assertEqual(data['callbacks'], 1)
                self.assertTrue(result['before']['transitions'])
                self.assertTrue(result['after'])

    def test_nonending_timing_missing_api_and_removed_toolbar_fail_closed(self):
        for case in (dict(infinite=True), dict(invalidTiming=True), dict(paused=True), dict(reverse=True),
                     dict(unsupported=True), dict(missing=True), dict(disappear=True)):
            with self.subTest(case=case):
                data = self.probe(**case)
                self.assertEqual(data['answer']['status'], 'error')
                self.assertEqual(data['callbacks'], 1)
                self.assertLess(data['answer']['elapsedMs'], 2000)

    def test_transition_churn_has_a_diagnostic_bound_and_cannot_pass(self):
        result = self.probe(churn=True)['answer']
        self.assertEqual(result['status'], 'error')
        self.assertIn('churn', result['reason'])
        self.assertEqual(len(result['observedTransitions']), 64)

    def test_stable_alpha_or_low_contrast_still_fails_original_readability_gate(self):
        import copy
        for case in (dict(none=True, alpha=True), dict(alpha=True), dict(none=True, lowContrast=True), dict(lowContrast=True)):
            with self.subTest(case=case):
                result = self.probe(**case)
                self.assertEqual(result['answer']['status'], 'settled')
                data = S0FooterCaptureChecks.fixture()
                proof = next(row['proof'] for row in data['toolbar']['controls'] if row['id'] == 'np-map-relations-toggle')
                for run in [proof, *proof['textRuns']]:
                    run['background'] = copy.deepcopy(result['background'])
                    run['foreground'] = copy.deepcopy(result['foreground'])
                with self.assertRaises(RuntimeError): MODULE.check_s0_footer(data)

    def test_successful_settle_does_not_excuse_hidden_clipped_or_covered_controls(self):
        self.assertEqual(self.probe(none=True)['answer']['status'], 'settled')
        for mutate in (lambda p: p.update(visible=False), lambda p: p.update(opaque=False),
                       lambda p: p.update(clipped=True), lambda p: p['fragments'][0].update(visible=False)):
            data = S0FooterCaptureChecks.fixture()
            proof = next(row['proof'] for row in data['toolbar']['controls'] if row['id'] == 'np-map-relations-toggle')
            mutate(proof)
            with self.assertRaises(RuntimeError): MODULE.check_s0_footer(data)

    def test_receipt_is_saved_before_any_timeout_or_error_is_raised(self):
        import copy
        good = self.probe()['answer']
        test = self
        class Driver:
            def __init__(self, result): self.result = result
            def call(self, method, path, data):
                test.assertEqual((method, path), ('POST', '/execute/async'))
                test.assertEqual(data, dict(script=MODULE.S0_TOOLBAR_PAINT_SETTLE_JS, args=[2000]))
                return self.result
        for data in (good, None, dict(good, status='timeout'), dict(good, status='error'),
                     dict(good, elapsedMs=2000), dict(good, elapsedMs=float('nan')),
                     dict(good, timeoutMs=4000), dict(good, before=None), dict(good, after=None)):
            report = {}; saved = []
            save = lambda: saved.append(copy.deepcopy(report))
            if data is good:
                self.assertEqual(MODULE.settle_s0_toolbar_paint(Driver(data), report, save, 'before-selection'), good)
            else:
                with self.assertRaises(RuntimeError): MODULE.settle_s0_toolbar_paint(Driver(data), report, save, 'before-selection')
            self.assertEqual(len(saved), 1)
            self.assertEqual(saved[0]['s0ToolbarPaintSettles'][0]['phase'], 'before-selection')
            self.assertIs(report['s0ToolbarPaintSettles'][0]['settle'], data)
        source = (Path(__file__).parents[1] / 'scripts/navigation_screenshots.py').read_text()
        import ast
        tree = ast.parse(source)
        separate_disclosure_save_sites(self, tree)
        paint_helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settle_s0_toolbar_paint')
        def save_calls(node):
            return [n for n in ast.walk(node) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']
        self.assertEqual(len(save_calls(paint_helper)), 1)
        tree.body.remove(paint_helper)
        native_paint_helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settle_version_title_paint')
        self.assertEqual(len(save_calls(native_paint_helper)), 1)
        tree.body.remove(native_paint_helper)
        selector_helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'reveal_relation_selector')
        self.assertEqual(len(save_calls(selector_helper)), 1)
        tree.body.remove(selector_helper)
        chrome_helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'desktop_chrome_snapshot')
        self.assertEqual(len(save_calls(chrome_helper)), 1)
        tree.body.remove(chrome_helper)
        child_helper = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'method_child_readability_checks')
        self.assertEqual(len(save_calls(child_helper)), 1)
        tree.body.remove(child_helper)
        self.assertEqual(len(save_calls(tree)), 99)  # Every original save checkpoint remains.
        self.assertIn('def s0_footer_check(phase):\n        settle_s0_toolbar_paint(driver, report, save, phase)\n        data = desktop_chrome_snapshot(driver, report, save, phase, S0_FOOTER_SNAPSHOT_JS, footer_expected)', source)


class DesktopChromePaintSettleChecks(unittest.TestCase):
    """Actual receipt geometry/colours with synthetic animation clocks, not Chrome pixels."""

    def probe(self, **case):
        return S0ToolbarPaintSettleChecks.probe(self, workspace=True, **case)

    def test_g_to_l_tabs_keep_actual_failure_colours_and_settle_to_css_endpoints(self):
        data = self.probe(); result = data['answer']
        self.assertEqual(result['scopeSelector'], '#np-workspace > .np-workspace-bar')
        self.assertEqual((result['status'], result['elapsedMs'], data['callbacks']), ('settled', 176, 1))
        self.assertEqual(data['beforeBackgrounds'], [[], []])
        self.assertEqual(data['afterBackgrounds'], [[237, 241, 236], [255, 255, 255]])
        tabs = {row['treeTab']: row for row in result['before']['colors'] if row['treeTab']}
        # Foregrounds and selection are exact 9082001 receipt values; the 0.4
        # alpha is synthetic because that old receipt did not retain raw RGBA.
        self.assertEqual((tabs['g']['color'], tabs['g']['selected']), ('rgb(105, 121, 128)', 'false'))
        self.assertEqual((tabs['l']['color'], tabs['l']['selected']), ('rgb(51, 93, 77)', 'true'))
        self.assertEqual(len(result['observedTransitions']), 4)
        self.assertEqual(result['after']['transitions'], [])
        areas = [dict(x=0, y=0, width=1440, height=900)]
        for i, (text, x, width, fg) in enumerate((('全景', 30, 30.015625, [105,121,128]),
                                                ('文献发展', 84.015625, 60.015625, [51,93,77]))):
            proof = chrome_text_fixture(text, 15, dict(x=x, y=250.015625, width=width, height=18), fg, data['beforeBackgrounds'][i])
            with self.assertRaises(RuntimeError): MODULE.check_chrome_text(proof, text, 15, *areas)
            for row in [proof, *proof['textRuns']]: row['background'] = data['afterBackgrounds'][i]
            MODULE.check_chrome_text(proof, text, 15, *areas)

    def test_scoped_wait_retains_replacement_timeout_and_nonending_failures(self):
        self.assertEqual(self.probe(replacement=True)['answer']['elapsedMs'], 224)
        for case in (dict(stuck=True), dict(pending=True), dict(frozenFrames=True)):
            with self.subTest(case=case):
                result = self.probe(**case)
                self.assertEqual((result['answer']['status'], result['answer']['elapsedMs'], result['callbacks']), ('timeout', 2000, 1))
        for case in (dict(paused=True), dict(infinite=True), dict(invalidTiming=True), dict(reverse=True),
                     dict(missing=True), dict(disappear=True), dict(replaceRoot=True), dict(unsupported=True), dict(churn=True)):
            with self.subTest(case=case):
                result = self.probe(**case)
                self.assertEqual(result['answer']['status'], 'error')
                self.assertEqual(result['callbacks'], 1)
                self.assertLessEqual(len(result['answer']['observedTransitions']), 64)

    def test_stable_alpha_hidden_clipped_and_covered_text_still_fail_original_gate(self):
        data = self.probe(none=True, alpha=True)
        self.assertEqual(data['answer']['status'], 'settled')
        area = dict(x=0, y=0, width=1440, height=900)
        proof = chrome_text_fixture('全景', 15, dict(x=30,y=250.015625,width=30.015625,height=18), [107,122,130], data['afterBackgrounds'][0])
        with self.assertRaises(RuntimeError): MODULE.check_chrome_text(proof, '全景', 15, area)
        import copy
        for mutate in (lambda p:p.update(visible=False), lambda p:p.update(opaque=False), lambda p:p.update(clipped=True),
                       lambda p:p.update(fontSize=14), lambda p:p['fragments'][0].update(visible=False),
                       lambda p:p['textRuns'][0]['fragments'][0].update(y=899)):
            bad = copy.deepcopy(proof)
            for row in [bad,*bad['textRuns']]: row['background']=[237,241,236]
            mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_chrome_text(bad, '全景', 15, area)

    def test_wrapper_saves_scope_then_takes_snapshot_only_after_bounded_success(self):
        import copy
        good = self.probe()['answer']; test = self
        class Driver:
            def __init__(self, result): self.result=result; self.events=[]
            def call(self, method, path, data):
                self.events.append('settle')
                test.assertEqual((method,path), ('POST','/execute/async'))
                test.assertEqual(data,dict(script=MODULE.DESKTOP_CHROME_PAINT_SETTLE_JS,args=[2000]))
                return self.result
            def js(self, script, *args):
                self.events.append('snapshot')
                return {'exactScript':script, 'args':args}
        for snapshot, args in ((MODULE.DESKTOP_SHELL_SNAPSHOT_JS,()),(MODULE.S0_FOOTER_SNAPSHOT_JS,({'source':'exact'},))):
            for result in (good,None,dict(good,status='timeout'),dict(good,status='error'),dict(good,elapsedMs=2000),
                           dict(good,elapsedMs=float('nan')),dict(good,timeoutMs=4000),dict(good,before=None),dict(good,after=None),
                           dict(good,scopeSelector=MODULE.S0_TOOLBAR_PAINT_SELECTOR)):
                driver=Driver(result);report={};saved=[]
                def save(): saved.append(copy.deepcopy(report));driver.events.append('save')
                if result is good:
                    value=MODULE.desktop_chrome_snapshot(driver,report,save,'1440x900-02-task-expanded',snapshot,*args)
                    self.assertEqual(value,{'exactScript':snapshot,'args':args})
                    self.assertEqual(driver.events,['settle','save','snapshot'])
                else:
                    with self.assertRaises(RuntimeError): MODULE.desktop_chrome_snapshot(driver,report,save,'bad',snapshot,*args)
                    self.assertEqual(driver.events,['settle','save'])
                self.assertEqual(len(saved),1)
                record=saved[0]['desktopChromePaintSettles'][0]
                self.assertEqual(record['scope'],'desktop-workspace-toolbar')
                self.assertNotIn('s0ToolbarPaintSettles',report)
        driver=Driver(good)
        with self.assertRaises(RuntimeError): MODULE.desktop_chrome_snapshot(driver,{},lambda:None,'unsupported','return true;')
        self.assertEqual(driver.events,[])

    def test_all_six_chrome_snapshot_entries_use_one_scoped_wrapper_without_mutating_driver_settle(self):
        import ast,inspect
        tree=ast.parse((Path(__file__).parents[1]/'scripts/navigation_screenshots.py').read_text())
        snapshots={'DESKTOP_SHELL_SNAPSHOT_JS','S0_FOOTER_SNAPSHOT_JS'}
        calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call)]
        wrapped=[n for n in calls if isinstance(n.func,ast.Name) and n.func.id=='desktop_chrome_snapshot']
        self.assertEqual(len(wrapped),6)
        self.assertEqual([sum(isinstance(n.args[4],ast.Name) and n.args[4].id==name for n in wrapped) for name in sorted(snapshots)],[4,2])
        raw=[n for n in calls if isinstance(n.func,ast.Attribute) and n.func.attr=='js' and n.args and isinstance(n.args[0],ast.Name) and n.args[0].id in snapshots]
        self.assertEqual(raw,[])
        self.assertEqual(MODULE.S0_TOOLBAR_PAINT_SETTLE_JS.split('\n',1)[1],MODULE.SCOPED_TOOLBAR_PAINT_SETTLE_JS)
        self.assertEqual(MODULE.DESKTOP_CHROME_PAINT_SETTLE_JS.split('\n',1)[1],MODULE.SCOPED_TOOLBAR_PAINT_SETTLE_JS)
        self.assertIn('document.fonts.ready.then(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>done(true))))',inspect.getsource(MODULE.Driver.settle))
        self.assertNotIn('paint',inspect.getsource(MODULE.Driver.settle))


class S0FooterCaptureChecks(unittest.TestCase):
    @staticmethod
    def source():
        import gzip
        return json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))

    @staticmethod
    def expected(science=None):
        import sys
        with patch.object(sys, 'path', [str(Path(__file__).parents[1] / 'scripts'), *sys.path]):
            return MODULE.s0_footer_expected(science or S0FooterCaptureChecks.source())

    @staticmethod
    def proof(text, area):
        import copy
        fragment = dict(area, visible=True)
        return dict(text=text, renderedText=text, rect=copy.deepcopy(area), visible=True, opaque=True, unscaled=True,
                    fontSize=15, clipped=False, foreground=[32, 52, 63], background=[255, 255, 255],
                    clipAreas=[], fragments=[fragment], textRuns=[dict(text=text, opaque=True, unscaled=True,
                    fontSize=15, foreground=[32, 52, 63], background=[255, 255, 255], clipAreas=[], fragments=[copy.deepcopy(fragment)])])

    @classmethod
    def fixture(cls, width=1440, selected=None):
        import copy
        height = 900 if width == 1440 else 1080
        def rect(x, y, w, h): return dict(x=x, y=y, width=w, height=h)
        def frame(identity, area, parent='', **kwargs):
            return dict(id=identity, tag='DIV', className='', parent=parent, rect=area, clientRect=copy.deepcopy(area),
                        position='static', display='block', flexDirection='row', flexGrow='0', flexShrink='1', flexBasis='auto',
                        rowGap=0, marginTop=0, marginBottom=0, paddingTop=0, paddingBottom=0, borderTop=0, borderBottom=0,
                        minHeight='0px', maxHeight='none', overflowX='visible', overflowY='visible',
                        top=0, left=0, scrollHeight=area['height'], clientHeight=area['height'], scrollWidth=area['width'], clientWidth=area['width'],
                        maxTop=0, inline=dict(top='', left='', width='', height='')) | kwargs
        expected = cls.expected(); viewport = rect(0, 0, width, height)
        map_box = rect(41, 149, width - 82, height - 241.5)
        footer_rect = rect(41, height - 80.5, width - 82, 47.5)
        # Preserve the compact map fixture while budgeting a real preceding toolbar.
        bottom_padding = 4 if height <= 950 else 16
        landing = frame('np-reading-landing', rect(16, 100, width - 32, height - 100 - bottom_padding), paddingTop=17,
                        paddingBottom=33 - bottom_padding, display='flex', flexDirection='column')
        toolbar = frame('', rect(41, 117, width - 82, 32), 'np-reading-landing',
                        className='np-overview-map-toolbar', flexShrink='0', count=1, beforeMap=True, first=True,
                        controls=[dict(id=identity, tag=tag, proof=cls.proof(label or '显示全部关系', rect(41 + i * 190, 117, 180, 24)))
                                  for i, (identity, tag, label) in enumerate(MODULE.S0_TOOLBAR_LABELS)])
        footer = frame('np-overview-footer', footer_rect, 'np-reading-landing', className='np-overview-footer',
                       display='flex', flexDirection='column', flexShrink='0', rowGap=4, marginTop=12,
                       afterMap=True, insideMap=False, children=[dict(id='', className='np-map-legend'), dict(id='', className='np-overview-coverage np-map-coverage')])
        legend = frame('', rect(41, footer_rect['y'], width - 82, 21.75), 'np-overview-footer', inFooter=True, labels=[])
        coverage = frame('', rect(41, footer_rect['y'] + 25.75, width - 82, 21.75), 'np-overview-footer', inFooter=True)
        texts = expected['legend'] + [expected['readouts'][selected] if selected else expected['defaultReadout']]
        x = 41
        for i, text in enumerate(texts):
            label_rect = rect(x, footer_rect['y'], [190, 210, 720][i], 21.75); x += [190, 210, 720][i] + 18
            legend['labels'].append(dict(id='np-map-relation-readout' if i == 2 else '', className=['np-map-parent-key', 'np-map-relation-key', ''][i], proof=cls.proof(text, label_rect)))
        coverage['proof'] = cls.proof(expected['coverage'], coverage['rect'])
        footer['proof'] = cls.proof(''.join(texts) + expected['coverage'], footer_rect)
        # A genuinely wrapped original run is included; final fragments are gated.
        footer['proof']['fragments'] = [dict(legend['rect'], visible=True), dict(coverage['rect'], visible=True)]
        footer['proof']['textRuns'][0]['fragments'] = copy.deepcopy(footer['proof']['fragments'])
        cw = min(520, max(408, 408 + (map_box['width'] - 1360) * 112 / 480))
        lw = map_box['width'] - cw - 24; cx = map_box['x'] + lw + 24; tw = (lw - 8 - 48) / 4
        layout_notes = []
        for key in ('0', '1', '2', '3', 'editorial', 'process'):
            editorial = key == 'editorial'; hidden = key == 'process'
            x = max(5, lw / 2 - 130) if editorial else 10 if hidden else 8 + int(key) * (tw + 16)
            note = cls.proof('Reviewed editorial note', rect(map_box['x'] + x, map_box['y'] + (104 if editorial else 124), 260 if editorial else tw, 20.25))
            note.update(visible=False, opaque=not hidden)  # Original notes use pointer-events:none.
            layout_notes.append(dict(key=key, hidden=hidden, proof=note))
        task_places = {scope: (column, rank) for rank, group in enumerate(MODULE.S0_TASK_ROWS) for column, scope in enumerate(group)}
        task_labels = {scope: (name, contract) for scope, name, contract in MODULE.TASK_INDEX}
        # Actual map client height is integer-rounded while its rect is fractional.
        map_frame = frame('np-overview-map', map_box, 'np-reading-landing', position='relative', flexGrow='1')
        map_frame.update(clientHeight=round(map_box['height'] + .01), scrollHeight=round(map_box['height'] + .01))
        map_frame['clientRect']['height'] = map_frame['clientHeight']
        extra = max(0, map_frame['clientHeight'] - (108 + 12 * (37 + 5) + 37) - 12)
        task_extra, c_extra = min(24, extra / 5), min(7, extra / 12)
        nodes = []; task_by_id = {row['id']: row['scope'] for row in expected['tasks']}
        challenge_index = 0
        for i, node in enumerate(expected['nodes']):
            if node['id'] in task_by_id:
                scope = task_by_id[node['id']]; column, rank = task_places[scope]
                area = rect(49 + column * (tw + 16), 307 + rank * (76 + task_extra), tw, 56)
                name, contract = task_labels[scope]
                labels = dict(name=cls.proof(name, rect(area['x'] + 10, area['y'] + 26, tw - 20, 21)),
                              contract=cls.proof(contract, rect(area['x'] + 10, area['y'] + 4, tw - 20, 20.8)))
                labels['contract']['fontSize'] = 16
            elif node['id'] == expected['challenge']:
                area = rect(cx, 209, cw, 37.390625)
                labels = dict(title=cls.proof('C', rect(cx + 12, 216, cw - 24, 23.390625)))
                labels['title']['fontSize'] = 18
            elif i >= 4:
                area = rect(cx, 257 + challenge_index * (42 + c_extra), cw, 37); challenge_index += 1
                labels = dict(challenge=cls.proof(MODULE.CHALLENGE_LABELS[node['entity']], rect(cx + 8, area['y'] + 7, cw - 35, 21.75)))
            elif node['id'] == expected['root']:
                area = rect(map_box['x'] + (map_box['width'] - 540) / 2, 149, 540, 42.390625)
                labels = dict(title=cls.proof('General goal', rect(area['x'] + 12, 156, 170, 26)),
                              subtitle=cls.proof('Original goal', rect(area['x'] + 198, 160, 300, 21.75)))
                labels['title']['fontSize'] = 20
            elif node['id'] == expected['literature']:
                area = rect(41, 209, lw, 37.390625)
                labels = dict(title=cls.proof('L', rect(53, 216, lw - 24, 23.390625)))
                labels['title']['fontSize'] = 18
            else:
                area = rect(49, 253, 130, 26.5)
                labels = dict(title=cls.proof('任务入口', area))
            replaced = selected is not None and node['id'] in expected['challengeIds']
            node_proof = cls.proof(node['entity'], area)
            node_proof.update(opaque=not replaced, visible=not replaced)
            for label in labels.values(): label.update(opaque=not replaced, visible=not replaced)
            nodes.append(dict(node, scope=task_by_id.get(node['id']), visibility='hidden' if replaced else 'visible', display='block', opacity='1', proof=node_proof, labels=labels))
        panel = frame('np-overview-relation-panel', rect(cx, 257, cw, map_box['height'] - 120), 'np-overview-map',
                      position='absolute', overflowX='auto', overflowY='auto', count=1, hidden=selected is None,
                      articles=[selected] if selected else [])
        panel['clientRect'] = rect(cx + 1, 258, cw - 17, panel['rect']['height'] - 2)
        panel.update(clientWidth=panel['clientRect']['width'], scrollWidth=panel['clientRect']['width'], clientHeight=panel['clientRect']['height'])
        panel.update(scrollHeight=panel['clientHeight'] + (211 if selected else 0), maxTop=211 if selected else 0)
        route = dict(scope='scope:all', tree='g', node=expected['root'], paper=None, version=None)
        view = dict(selectedRelation=selected, relationScrollTop=0, scrollTop=0, relationsOpen=False, linesVisible=False)
        return dict(chrome=desktop_chrome_fixture(width, height, top=100, bottom_padding=bottom_padding, route=route, home=True), expected=expected, viewport=viewport, ready='ready', home=True, scale=1, window=dict(x=0, y=0),
                    route=route, historyRoute=copy.deepcopy(route), focus='np-map-relation-evidence-' + selected if selected else 'BODY',
                    selectedRelation=selected, relationsVisible='false', selectorOpen=False, runtimeOverview=copy.deepcopy(view), historyOverview=copy.deepcopy(view),
                    landing=landing, map=map_frame, toolbar=toolbar, footerCount=1, legendCount=1, coverageCount=1,
                    footer=footer, legend=legend, coverage=coverage, nodes=nodes, layoutNotes=layout_notes, panel=panel, scrollRegionCandidates=[],
                    scrollIds=['np-overview-relation-panel'] if selected else [])

    def test_source_bound_complete_footer_and_original_nodes_fit_both_desktops(self):
        for width in (1440, 1920):
            for selected in (None, 'tasks:relation:88', 'tasks:relation:90', 'tasks:relation:94'):
                data = self.fixture(width, selected)
                MODULE.check_s0_footer(data)
                self.assertEqual([row['id'] for row in data['nodes']], [row['id'] for row in data['expected']['nodes']])
                self.assertIn('选段覆盖，不代表全文精读或领域穷尽。', data['coverage']['proof']['renderedText'])
                self.assertEqual(len(data['footer']['proof']['fragments']), 2)
        source = self.source(); original = self.expected(source)
        scope = next(row for row in source['scopes'] if row['id'] == 'task:pointnav')
        scope['coverage']['direct']['methodCount'] = 5
        changed = self.expected(source)
        self.assertNotEqual(original['coverage'], changed['coverage'])
        self.assertEqual(original['nodes'], changed['nodes'])

    def test_chrome_and_toolbar_budget_cannot_hide_excess_height_nodes_or_footer_overlap(self):
        import copy
        good = self.fixture()
        MODULE.check_s0_footer(good)
        for mutate in (lambda d: d['chrome']['header']['rect'].update(height=200),
                       lambda d: d['chrome']['bar']['rect'].update(height=200),
                       lambda d: d.pop('toolbar'), lambda d: d['toolbar'].update(count=2),
                       lambda d: d['toolbar'].update(first=False), lambda d: d['toolbar'].update(beforeMap=False),
                       lambda d: d['toolbar'].update(position='absolute'), lambda d: d['toolbar'].update(flexShrink='1'),
                       lambda d: d['toolbar']['controls'].pop(), lambda d: d['toolbar']['controls'][0]['proof'].update(visible=False),
                       lambda d: d['toolbar']['controls'][0]['proof'].update(fontSize=14),
                       lambda d: d['toolbar']['controls'][0]['proof'].update(fontSize=16.1),
                       lambda d: d['toolbar']['controls'][0]['proof'].update(clipped=True),
                       lambda d: d['toolbar']['rect'].update(height=200),
                       lambda d: d['nodes'].pop(), lambda d: d['nodes'][4]['labels'].pop('contract'),
                       lambda d: d['footer']['rect'].update(y=d['map']['rect']['y'] + d['map']['rect']['height'] - 1)):
            bad = copy.deepcopy(good); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)
        # Budget accounting alone must not license reducing the source map: a
        # genuinely taller toolbar takes height from the map, never from cards.
        bad = copy.deepcopy(good); extra = 40
        bad['toolbar']['rect']['height'] += extra
        bad['toolbar']['clientRect']['height'] += extra
        for key in ('rect', 'clientRect'):
            bad['map'][key]['y'] += extra; bad['map'][key]['height'] -= extra
        for key in ('clientHeight', 'scrollHeight'): bad['map'][key] -= extra
        with self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_both_desktops_can_have_only_compact_source_height_after_current_chrome(self):
        import copy
        def translate(value, delta):
            if isinstance(value, dict):
                if all(key in value for key in ('x', 'y', 'width', 'height')): value['y'] += delta
                for child in value.values(): translate(child, delta)
            elif isinstance(value, list):
                for child in value: translate(child, delta)
        for width in (1440, 1920):
            data = self.fixture(width)
            old = MODULE.check_s0_adaptive_spacing(data)
            # A synthetic tight budget at either viewport: the exact original
            #649px compact graph fits with fractional CSS pixel rounding. This
            # is not a claim that a1080px screen has the old838px map available.
            delta = data['map']['rect']['height'] - 649.5
            for key in ('rect', 'clientRect'): data['chrome']['bar'][key]['height'] += delta
            for key in ('rect', 'clientRect'):
                data['landing'][key]['y'] += delta; data['landing'][key]['height'] -= delta
                data['map'][key]['y'] += delta; data['map'][key]['height'] -= delta
            for region in ('landing', 'map'):
                for key in ('clientHeight', 'scrollHeight'): data[region][key] -= delta
            translate(data['toolbar'], delta)
            ranks = {scope: rank for rank, group in enumerate(MODULE.S0_TASK_ROWS) for scope in group}
            challenges = data['expected']['challengeIds']
            for row in data['nodes']:
                spread = ranks[row['scope']] * old['taskExtra'] if row['scope'] else (
                    challenges.index(row['id']) * old['challengeExtra'] if row['id'] in challenges else 0)
                translate(row, delta - spread)
            translate(data['layoutNotes'], delta)
            translate(data['panel'], delta)
            for key in ('rect', 'clientRect'): data['panel'][key]['height'] -= delta
            for key in ('clientHeight', 'scrollHeight'): data['panel'][key] -= delta
            MODULE.check_s0_footer(data)
            self.assertEqual(MODULE.check_s0_adaptive_spacing(data)['availableExtra'], 0)
            # All accounting still balances when more chrome consumes space,
            # but the unchanged source graph must then fail containment.
            bad = copy.deepcopy(data)
            for key in ('rect', 'clientRect'): bad['chrome']['bar'][key]['height'] += 20
            for key in ('rect', 'clientRect'):
                bad['landing'][key]['y'] += 20; bad['landing'][key]['height'] -= 20
                bad['map'][key]['y'] += 20; bad['map'][key]['height'] -= 20
            for region in ('landing', 'map'):
                for key in ('clientHeight', 'scrollHeight'): bad[region][key] -= 20
            for key in ('toolbar', 'nodes', 'layoutNotes'): translate(bad[key], 20)
            with self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_adaptive_spacing_uses_actual_client_height_and_preserves_compact_map_gap(self):
        for width, task_extra, c_extra in ((1440, 0, 0), (1920, 24, 7)):
            for selected in (None, *self.expected()['readouts']):
                for mode in ('false', 'true'):
                    data = self.fixture(width, selected); data['relationsVisible'] = mode
                    if mode == 'true':
                        proof = data['toolbar']['controls'][-1]['proof']
                        proof['text'] = proof['renderedText'] = proof['textRuns'][0]['text'] = '仅显示所选关系'
                    result = MODULE.check_s0_adaptive_spacing(data)
                    MODULE.check_s0_footer(data)
                    self.assertEqual(result, dict(compactBottom=649, availableExtra=0 if width == 1440 else 178,
                        taskRowCount=6, challengeCount=13, taskExtra=task_extra, challengeExtra=c_extra))
                    last = data['nodes'][-1]['proof']['rect']; map_rect = data['map']['rect']
                    self.assertAlmostEqual(last['y'] + last['height'] - map_rect['y'], 649 if width == 1440 else 733)
                    self.assertAlmostEqual(map_rect['y'] + map_rect['height'] - last['y'] - last['height'], 9.5 if width == 1440 else 105.5)
                    tasks = [n['proof']['rect'] for n in data['nodes'] if n['scope']]
                    self.assertAlmostEqual(max(r['y'] + r['height'] for r in tasks) - map_rect['y'], 594 if width == 1440 else 714)
                    self.assertTrue(all(data['footer']['rect']['y'] - r['y'] - r['height'] >= 12 for r in tasks + [last]))

    def test_adaptive_spacing_rejects_stale_large_layout_compact_drift_and_invented_metadata(self):
        import copy
        small = self.fixture(); large = self.fixture(1920)
        # Copy final y from the compact layout while retaining genuine large-map x/width.
        stale = copy.deepcopy(large)
        for old, new in zip(small['nodes'], stale['nodes']): new['proof']['rect']['y'] = old['proof']['rect']['y']
        stale['adaptiveSpacing'] = dict(compactBottom=649, taskExtra=24, challengeExtra=7, passed=True)
        with self.assertRaisesRegex(RuntimeError, 'bounded measured'): MODULE.check_s0_adaptive_spacing(stale)
        for width, good in ((1440, small), (1920, large)):
            for identity in (good['expected']['root'], good['expected']['literature'], good['expected']['directory'],
                             good['expected']['tasks'][0]['id'], good['expected']['challengeIds'][0], good['expected']['challengeIds'][-1]):
                for delta in (-1, 1, 120):
                    bad = copy.deepcopy(good); next(n for n in bad['nodes'] if n['id'] == identity)['proof']['rect']['y'] += delta
                    with self.subTest(width=width, identity=identity, delta=delta), self.assertRaises(RuntimeError):
                        MODULE.check_s0_adaptive_spacing(bad)

    def test_adaptive_spacing_reconstructs_task_start_from_measured_notes(self):
        import copy
        data = self.fixture(1920)
        for note in data['layoutNotes'][:4]: note['proof']['rect']['height'] += 30
        with self.assertRaisesRegex(RuntimeError, 'bounded measured'): MODULE.check_s0_adaptive_spacing(data)
        # New notes bottom is 174.25, so bus is 179.25 and task start is 187.25.
        for node in data['nodes']:
            if node['scope']:
                node['proof']['rect']['y'] += 29.25
                for label in node['labels'].values(): label['rect']['y'] += 29.25
        result = MODULE.check_s0_adaptive_spacing(data)
        self.assertEqual(result['compactBottom'], 649)
        self.assertEqual((result['taskExtra'], result['challengeExtra']), (24, 7))
        smaller = copy.deepcopy(data); smaller['map']['clientHeight'] = 659
        smaller['map']['clientRect']['height'] = 659; smaller['map']['rect']['height'] = 658.5
        with self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(smaller)

    def test_adaptive_spacing_rejects_wrong_rows_order_count_x_sizes_fonts_overlap_and_footer(self):
        import copy
        good = self.fixture(1920)
        task = lambda d: next(n for n in d['nodes'] if n['scope'] == 'task:pointnav')
        c = lambda d: next(n for n in d['nodes'] if n['id'] == d['expected']['challengeIds'][0])
        mutations = [lambda d: d['nodes'].pop(), lambda d: d['nodes'].append(copy.deepcopy(d['nodes'][0])),
                     lambda d: d['nodes'].__setitem__(slice(-2, None), list(reversed(d['nodes'][-2:]))),
                     lambda d: task(d).update(scope='task:invented'),
                     lambda d: task(d)['proof']['rect'].update(y=407),
                     lambda d: task(d)['proof']['rect'].update(x=50),
                     lambda d: c(d)['proof']['rect'].update(x=c(d)['proof']['rect']['x'] - 1),
                     lambda d: task(d)['proof']['rect'].update(width=task(d)['proof']['rect']['width'] + 1),
                     lambda d: task(d)['proof']['rect'].update(height=55),
                     lambda d: task(d)['proof']['rect'].update(height=57),
                     lambda d: c(d)['proof']['rect'].update(height=38),
                     lambda d: c(d)['proof']['rect'].update(height=36),
                     lambda d: task(d)['labels']['contract'].update(fontSize=15),
                     lambda d: task(d)['labels']['name'].update(fontSize=14),
                     lambda d: c(d)['labels']['challenge'].update(fontSize=14),
                     lambda d: c(d)['labels']['challenge'].update(visible=False),
                     lambda d: task(d)['labels']['name'].update(clipped=True),
                     lambda d: task(d)['labels'].pop('name'),
                     lambda d: task(d)['proof']['rect'].update(y=c(d)['proof']['rect']['y'], x=c(d)['proof']['rect']['x']),
                     lambda d: d['footer']['rect'].update(y=d['nodes'][-1]['proof']['rect']['y'] + 40),
                     lambda d: d['layoutNotes'].pop(), lambda d: d['layoutNotes'][0]['proof']['rect'].update(y=274),
                     lambda d: d['layoutNotes'][0]['proof'].update(fontSize=14),
                     lambda d: d['map'].update(clientHeight=0), lambda d: d['map'].update(clientWidth=0),
                     lambda d: d['map'].update(clientHeight=840), lambda d: d['map']['clientRect'].update(height=838.5)]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=index), self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)

    def test_adaptive_spacing_gate_is_independent_and_wired_to_original_capture_saves(self):
        import inspect, ast
        self.assertEqual(MODULE.S0_TASK_ROWS[0], ('task:pointnav', 'task:ddn', 'task:vln', 'task:multion'))
        self.assertEqual(MODULE.S0_TASK_ROWS[-1], ('task:aerial-visual-object-search', 'task:person-finding-following', 'task:namo'))
        self.assertEqual(sorted(scope for group in MODULE.S0_TASK_ROWS for scope in group), sorted(row[0] for row in MODULE.TASK_INDEX))
        gate = inspect.getsource(MODULE.check_s0_adaptive_spacing)
        for evidence in ("map_box['clientHeight']", "map_box['clientWidth']", "data.get('layoutNotes'", 'S0_TASK_ROWS', "expected['challengeIds']", "row['proof']['rect']['height']"):
            self.assertIn(evidence, gate)
        self.assertNotIn('OVERVIEW_TASK_PLACEMENT', gate)
        self.assertNotIn("data['adaptiveSpacing']", gate)
        self.assertIn("len(expected['nodes'])", gate)
        self.assertNotIn('!= 39', gate)
        self.assertNotIn('!= 13', gate)
        self.assertIn('check_s0_adaptive_spacing(data)', inspect.getsource(MODULE.check_s0_footer))
        main = inspect.getsource(MODULE.main)
        self.assertIn("graph['s0AdaptiveSpacing'] = desktop_chrome_snapshot(driver, report, save, 'reading-home-' + relation_mode, S0_FOOTER_SNAPSHOT_JS, footer_expected)", main)
        self.assertIn("check_s0_footer(graph['s0AdaptiveSpacing'])", main)
        self.assertIn("reading_home(relation_mode='all')", main)
        tree = ast.parse(inspect.getsource(MODULE))
        separate_disclosure_save_sites(self, tree)
        native_paint = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settle_version_title_paint')
        self.assertEqual(len([n for n in ast.walk(native_paint) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']), 1)
        tree.body.remove(native_paint)
        saves = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']
        self.assertEqual(len(saves), 103)  # 99 original + S0 paint + selector reveal + desktop paint + child audit saves.
        self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)
        self.assertIn('s0_adaptive_spacing', MODULE.DISPLAY_CONTRACT_MIGRATIONS)

    def test_footer_rejects_legacy_absolute_map_child_missing_duplicate_and_extra_scroll(self):
        import copy
        good = self.fixture()
        mutations = [lambda d: d.update(footer=None), lambda d: d.update(footerCount=0), lambda d: d.update(footerCount=2),
                     lambda d: d.update(legendCount=2), lambda d: d.update(coverageCount=0),
                     lambda d: d['footer'].update(parent='np-overview-map', insideMap=True),
                     lambda d: d['footer'].update(afterMap=False), lambda d: d['legend'].update(inFooter=False),
                     lambda d: d['coverage'].update(inFooter=False), lambda d: d['footer']['children'].pop(),
                     lambda d: d['footer'].update(position='absolute'), lambda d: d['legend'].update(position='absolute'),
                     lambda d: d['coverage'].update(position='fixed'), lambda d: d['legend']['inline'].update(top='666px'),
                     lambda d: d['footer'].update(flexShrink='1'), lambda d: d['footer'].update(flexGrow='1'),
                     lambda d: d['footer'].update(flexBasis='48px'), lambda d: d['footer'].update(maxHeight='48px'),
                     lambda d: d['footer'].update(rowGap=0), lambda d: d['coverage'].update(overflowY='auto'),
                     lambda d: d['footer'].update(overflowX='hidden'), lambda d: d['footer'].update(top=1),
                     lambda d: d['landing'].update(top=1), lambda d: d['map'].update(left=1), lambda d: d['map'].update(flexGrow='0'),
                     lambda d: d['map'].update(minHeight='704px'), lambda d: d['map'].update(parent='wrong'),
                     lambda d: d['map'].update(scrollHeight=d['map']['clientHeight'] + 9),
                     lambda d: d['scrollIds'].append('third-scroll'), lambda d: d['landing']['rect'].update(height=550),
                     lambda d: d['window'].update(y=1), lambda d: d.update(scale=.8)]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_complete_text_rejects_shortening_bad_alpha_font_contrast_scale_and_final_fragment(self):
        import copy
        good = self.fixture(selected='tasks:relation:88')
        for target in ('coverage', 'footer', 'readout'):
            def proof(data): return data['legend']['labels'][2]['proof'] if target == 'readout' else data[target]['proof']
            mutations = [lambda p: p.update(text='简称'), lambda p: p.update(renderedText='简称'),
                         lambda p: p.update(visible=False), lambda p: p.update(opaque=False), lambda p: p.update(unscaled=False),
                         lambda p: p.update(fontSize=14), lambda p: p.update(foreground=[]), lambda p: p.update(foreground=[220, 220, 220]),
                         lambda p: p.update(clipped=True), lambda p: p.update(textRuns=[]), lambda p: p.update(fragments=[]),
                         lambda p: p['textRuns'][0].update(text='少字'), lambda p: p['textRuns'][0].update(opaque=False),
                         lambda p: p['textRuns'][0].update(unscaled=False), lambda p: p['textRuns'][0].update(fontSize=14),
                         lambda p: p['textRuns'][0].update(foreground=[]), lambda p: p['textRuns'][0].update(background=[]),
                         lambda p: p['textRuns'][0].update(foreground=[200, 200, 200]),
                         lambda p: p['fragments'][-1].update(visible=False), lambda p: p['fragments'][-1].update(y=901),
                         lambda p: p['textRuns'][0]['fragments'][-1].update(visible=False),
                         lambda p: p['textRuns'][0]['fragments'][-1].update(x=-10),
                         lambda p: p['textRuns'][0].update(clipAreas=[dict(x=0, y=0, width=1440, height=820)])]
            for i, mutate in enumerate(mutations):
                bad = copy.deepcopy(good); mutate(proof(bad))
                with self.subTest(target=target, mutation=i), self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_panel_footer_map_nodes_and_source_identity_are_independently_bounded(self):
        import copy
        good = self.fixture(selected='tasks:relation:90')
        mutations = [lambda d: d['panel'].update(parent='np-reading-landing'), lambda d: d['panel'].update(count=2),
                     lambda d: d['panel'].update(hidden=True), lambda d: d['panel'].update(articles=['tasks:relation:88']),
                     lambda d: d['panel'].update(overflowY='hidden'), lambda d: d['panel'].update(overflowY='scroll'),
                     lambda d: d['panel']['rect'].update(height=d['map']['rect']['height']),
                     lambda d: d['panel']['rect'].update(x=41), lambda d: d['panel']['rect'].update(y=300),
                     lambda d: d['panel']['clientRect'].update(width=900), lambda d: d['panel'].update(left=1),
                     lambda d: d['panel'].update(top=500), lambda d: d['scrollIds'].append('nested-source-scroll'),
                     lambda d: d['map']['rect'].update(height=d['map']['rect']['height'] + 20),
                     lambda d: d['footer']['rect'].update(y=d['footer']['rect']['y'] - 12),
                     lambda d: d['nodes'][-1]['proof']['rect'].update(y=d['footer']['rect']['y']),
                     lambda d: d['nodes'][4]['proof']['rect'].update(x=d['panel']['rect']['x']),
                     lambda d: d['nodes'][0].update(id='wrong'), lambda d: d['nodes'][1].update(parent='wrong'),
                     lambda d: d['nodes'][4].update(scope='wrong'), lambda d: d['nodes'][0].update(entity='wrong'),
                     lambda d: d['nodes'][0]['proof'].update(unscaled=False), lambda d: d['nodes'].pop(),
                     lambda d: d['route'].update(version='borrowed-version'), lambda d: d['historyRoute'].update(node='wrong'),
                     lambda d: d.update(selectedRelation='wrong-source')]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_only_exact_source_challenges_are_temporarily_hidden_and_close_restores_all(self):
        import copy
        opened = self.fixture(selected='tasks:relation:90'); closed = self.fixture()
        MODULE.check_s0_stability(opened, closed)
        self.assertEqual([r['id'] for r in opened['nodes'] if r['visibility'] == 'hidden'], opened['expected']['challengeIds'])
        self.assertTrue(all(r['proof']['opaque'] for r in closed['nodes']))
        for index in (0, 1, 2, 4):
            bad = copy.deepcopy(opened); bad['nodes'][index].update(visibility='hidden'); bad['nodes'][index]['proof'].update(opaque=False, visible=False)
            with self.subTest(non_challenge=index), self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)
        for initial in (opened, closed):
            bad = copy.deepcopy(initial); node = next(r for r in bad['nodes'] if r['id'] == bad['expected']['challengeIds'][0])
            node.update(visibility='visible' if initial is opened else 'hidden'); node['proof'].update(opaque=initial is opened, visible=initial is opened)
            with self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)
        for update in (dict(display='none'), dict(opacity='0')):
            bad = copy.deepcopy(opened); bad['nodes'][-1].update(update)
            with self.assertRaises(RuntimeError): MODULE.check_s0_footer(bad)

    def test_native_scroll_stability_requires_positive_actual_movement_and_exact_saved_offsets(self):
        import copy
        before = self.fixture(selected='tasks:relation:90'); after = copy.deepcopy(before)
        after['panel']['top'] = 137
        for key in ('runtimeOverview', 'historyOverview'): after[key]['relationScrollTop'] = 137
        MODULE.check_s0_wheel(before, after, 137)
        MODULE.check_s0_stability(after, copy.deepcopy(after), restore=True)
        mutations = [lambda d: d['nodes'][4]['proof']['rect'].update(y=d['nodes'][4]['proof']['rect']['y'] + 2),
                     lambda d: d['footer']['rect'].update(y=d['footer']['rect']['y'] + 2),
                     lambda d: d['landing'].update(left=1), lambda d: d['window'].update(y=1),
                     lambda d: d['panel'].update(top=0), lambda d: d['panel'].update(maxTop=0),
                     lambda d: d['historyOverview'].update(relationScrollTop=136),
                     lambda d: d['runtimeOverview'].update(relationScrollTop=0),
                     lambda d: d['historyOverview'].update(selectedRelation='tasks:relation:88'), lambda d: d.update(focus='BODY')]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(after); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError): MODULE.check_s0_wheel(before, bad, 137)
        for delta in (0, -137):
            with self.assertRaises(RuntimeError): MODULE.check_s0_wheel(before, after, delta)
        zero = copy.deepcopy(before); zero['panel'].update(maxTop=0, scrollHeight=zero['panel']['clientHeight'])
        with self.assertRaisesRegex(RuntimeError, 'real source overflow'): MODULE.check_s0_wheel(zero, zero, 137)
        restored = copy.deepcopy(after); restored['panel']['top'] = 138
        for key in ('runtimeOverview', 'historyOverview'): restored[key]['relationScrollTop'] = 138
        with self.assertRaisesRegex(RuntimeError, 'exact effective'): MODULE.check_s0_stability(after, restored, restore=True)
        for key in ('focus', 'selectorOpen', 'relationsVisible'):
            bad = copy.deepcopy(after); bad[key] = {'focus': 'BODY', 'selectorOpen': True, 'relationsVisible': 'true'}[key]
            with self.assertRaises(RuntimeError): MODULE.check_s0_stability(after, bad, restore=True)

    def test_relationship_text_must_fit_real_panel_client_region_not_only_viewport(self):
        import copy
        area = dict(x=1000, y=280, width=370, height=30)
        proof = self.proof('Section 3', area)
        proof.update(panelId='np-overview-relation-panel', panelContains=True, relationId='r',
                     panelClientRect=dict(x=992, y=258, width=391, height=536), viewport=dict(x=0, y=0, width=1440, height=900))
        expected = dict(id='r', relationType='composition', **{'from': 'a', 'to': 'b'}, locators=[dict(locator='Section 3')], sourceRefs=[dict(sourceId='s', url='https://example.org/v1', versionId='v1', versionStatus='fixed', descriptor='完整来源版本描述')])
        data = dict(id='r', type='composition', **{'from': 'a', 'to': 'b'}, open=True, focus='np-map-relation-evidence-r', route={}, beforeRoute={}, text='Section 3',
                    sources=[dict(id='s', url='https://example.org/v1', version='v1', status='fixed')], visibleProofs=[copy.deepcopy(proof) for _ in range(4)])
        for kind, proof in zip(('heading', 'locator', 'source', 'status'), data['visibleProofs']):
            proof.update(self.proof('原文来源 · 完整来源版本描述' if kind == 'source' else ' · fixed' if kind == 'status' else 'Section 3', proof['rect']))
            proof.update(kind=kind, sourceRecord=data['sources'][0].copy() if kind in ('source', 'status') else None)
            if kind == 'source':
                proof.update(elementTag='A', accessibilitySuffix=dict(tag='SPAN', className='np-sr', text='（新标签页）'), accessibleText=proof['text'] + '（新标签页）')
        MODULE.check_relation_evidence(data, expected)
        for label in ('原文来源 · 完整来源', '原文来源 · 另一版本描述'):
            bad = copy.deepcopy(data); proof = bad['visibleProofs'][2]
            proof.update(self.proof(label, proof['rect']), accessibleText=label + '（新标签页）')
            proof.pop('expectedText', None)
            with self.assertRaisesRegex(RuntimeError, 'another source'): MODULE.check_relation_evidence(bad, expected)
        for mutate in (lambda p: p.pop('accessibilitySuffix'), lambda p: p.update(elementTag='SPAN'), lambda p: p.update(accessibleText=p['text']),
                       lambda p: p['accessibilitySuffix'].update(text='隐藏科学条件'), lambda p: p['accessibilitySuffix'].update(className='np-hidden')):
            bad = copy.deepcopy(data); mutate(bad['visibleProofs'][2])
            with self.assertRaisesRegex(RuntimeError, 'screen-reader suffix'): MODULE.check_relation_evidence(bad, expected)
        bad = copy.deepcopy(data); bad['visibleProofs'][0]['accessibilitySuffix'] = dict(tag='SPAN', className='np-sr', text='（新标签页）')
        with self.assertRaisesRegex(RuntimeError, 'Only an exact source anchor'): MODULE.check_relation_evidence(bad, expected)
        for key, value in (('id', 'wrong-source'), ('version', 'v2'), ('url', 'https://example.org/v2'), ('status', 'snapshot')):
            bad = copy.deepcopy(data); bad['visibleProofs'][2]['sourceRecord'][key] = value
            with self.assertRaisesRegex(RuntimeError, 'another source'): MODULE.check_relation_evidence(bad, expected)
        for mutate in (lambda p: p.update(panelContains=False), lambda p: p.update(panelId='other'), lambda p: p.update(relationId='other'),
                       lambda p: p['panelClientRect'].update(height=25), lambda p: p['fragments'][-1].update(y=795),
                       lambda p: p['textRuns'][0]['fragments'][-1].update(y=795), lambda p: p.update(renderedText='hidden'),
                       lambda p: p['textRuns'][0].update(opaque=False)):
            bad = copy.deepcopy(data); mutate(bad['visibleProofs'][0])
            with self.assertRaises(RuntimeError): MODULE.check_relation_evidence(bad, expected)

    def test_source_fragment_snapshot_excludes_only_exact_original_accessibility_suffix(self):
        science = self.source()
        body = r"""
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};
d.querySelector('[data-relation-select="tasks:relation:90"]').click();await wait(20);
const source=d.querySelector('[data-task-relation="tasks:relation:90"] [data-task-relation-source]'),sourceProof=new w.Function(input.sourceProof),actual=sourceProof(source);
assert.equal(actual.accessibilitySuffix.text,'（新标签页）');assert.equal(actual.accessibleText,actual.renderedText+'（新标签页）');assert.equal(actual.text,actual.renderedText);assert.ok(!actual.textRuns.some(run=>run.text==='（新标签页）'));assert.equal(actual.sourceRecord.id,source.dataset.taskRelationSource);states.push(actual);
const suffix=source.lastChild;suffix.remove();assert.throws(()=>sourceProof(source),/suffix/);source.appendChild(suffix);suffix.textContent='隐藏科学条件';assert.throws(()=>sourceProof(source),/suffix/);suffix.textContent='（新标签页）';source.appendChild(suffix.cloneNode(true));assert.throws(()=>sourceProof(source),/suffix/);source.lastChild.remove();
const hidden=d.createElement('span');hidden.style.display='none';hidden.textContent='不得跳过科学限定';source.insertBefore(hidden,suffix);const bad=sourceProof(source);assert.equal(bad.textRuns.at(-1).text,hidden.textContent);assert.equal(bad.textRuns.at(-1).opaque,false);
"""
        states = run_product_capture_script(self, body, dict(science=science, expected=MODULE.task_route_expected(science),
            sourceProof=MODULE.RELATION_EVIDENCE_PROOF_JS, viewport=dict(width=1440, height=900)))
        self.assertEqual(states[0]['accessibilitySuffix'], dict(tag='SPAN', className='np-sr', text='（新标签页）'))
        self.assertNotIn('ignoredTextParent', MODULE.S0_FOOTER_SNAPSHOT_JS.split('var a=NavigationProductApp', 1)[-1])

    def test_production_snapshot_has_exact_footer_identity_source_text_and_no_state_mutation(self):
        science = self.source(); expected = self.expected(science)
        body = r"""
// DOM identity only; no synthetic rectangle is claimed as browser evidence.
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};
const footerSnapshot=new w.Function(input.footerSnapshot),state=JSON.stringify(a.getState()),initial=footerSnapshot(input.footerExpected);
assert.equal(JSON.stringify(a.getState()),state);assert.equal(initial.footerCount,1);assert.equal(initial.footer.id,'np-overview-footer');assert.equal(initial.footer.parent,'np-reading-landing');assert.equal(initial.footer.afterMap,true);assert.equal(initial.footer.insideMap,false);assert.equal(initial.legend.inFooter,true);assert.equal(initial.coverage.inFooter,true);
assert.equal(initial.coverage.proof.renderedText,input.footerExpected.coverage);assert.equal(initial.legend.labels[2].proof.renderedText,input.footerExpected.defaultReadout);
assert.equal(initial.chrome.identityFields.length,4);assert.equal(initial.chrome.identitySource.scopeId,a.getState().route.scope);assert.deepEqual(initial.chrome.identitySource.route,a.getState().route);
assert.deepEqual(JSON.parse(JSON.stringify(initial.chrome.identityFields.map(f=>[f.label.renderedText,f.value.renderedText]))),JSON.parse(JSON.stringify(initial.chrome.identitySource.fields)));
assert.deepEqual(JSON.parse(JSON.stringify(initial.chrome.controls.map(c=>[c.count,c.tag,c.tree]))),[[1,'BUTTON','g'],[1,'BUTTON','l'],[1,'BUTTON','c'],[1,'BUTTON','a'],[1,'SUMMARY',null],[1,'BUTTON',null],[1,'SUMMARY',null],[1,'BUTTON',null]]);
const identityValue=d.querySelector('#np-selection-context dd');identityValue.style.visibility='hidden';assert.equal(footerSnapshot(input.footerExpected).chrome.identityFields[0].value.opaque,false);identityValue.style.visibility='';
const originalTab=d.querySelector('.np-workspace-bar .np-tabs > [data-tree-tab="g"]'),duplicateTab=originalTab.cloneNode(true);originalTab.parentElement.appendChild(duplicateTab);assert.equal(footerSnapshot(input.footerExpected).chrome.controls[0].count,2);duplicateTab.remove();
assert.deepEqual(JSON.parse(JSON.stringify(initial.nodes.map(({id,parent,entity})=>({id,parent,entity})))),input.footerExpected.nodes);states.push(initial);
d.querySelector('[data-relation-select="tasks:relation:90"]').click();await wait(35);const selectedState=JSON.stringify(a.getState()),selected=footerSnapshot(input.footerExpected);assert.equal(JSON.stringify(a.getState()),selectedState);assert.equal(selected.legend.labels[2].proof.renderedText,input.footerExpected.readouts['tasks:relation:90']);assert.equal(selected.panel.parent,'np-overview-map');assert.deepEqual(JSON.parse(JSON.stringify(selected.panel.articles)),['tasks:relation:90']);states.push(selected);
for(const id of Object.keys(input.footerExpected.readouts)){d.querySelector('[data-relation-select="'+id+'"]').click();await wait(10);assert.equal(footerSnapshot(input.footerExpected).legend.labels[2].proof.renderedText,input.footerExpected.readouts[id]);}
const span=d.createElement('span');span.style.opacity='0';span.textContent='隐藏尾注';d.querySelector('.np-map-coverage').appendChild(span);assert.equal(footerSnapshot(input.footerExpected).coverage.proof.textRuns.at(-1).opaque,false);span.remove();
"""
        states = run_product_capture_script(self, body, {'science': science, 'expected': MODULE.task_route_expected(science),
            'footerSnapshot': MODULE.S0_FOOTER_SNAPSHOT_JS, 'footerExpected': expected, 'viewport': dict(width=1440, height=900)})
        self.assertEqual(states[0]['footer']['children'], [dict(id='', className='np-map-legend'), dict(id='', className='np-overview-coverage np-map-coverage')])
        self.assertEqual(states[1]['selectedRelation'], 'tasks:relation:90')

    def test_designated_s0_scenes_cannot_omit_footer_but_glossary_keeps_original_overlay_contract(self):
        import copy, inspect
        s0 = self.fixture(); shell = DesktopHierarchyContractChecks.shell()
        shell.update(chrome=s0['chrome'], route=s0['route'], home=True, position=None, landing=s0['landing']['rect'], landingOffsets=dict(top=0, left=0), s0Footer=s0)
        for viewport in MODULE.VIEWPORTS:
            for suffix in MODULE.S0_FOOTER_SCENES:
                self.assertTrue(MODULE.s0_footer_required(str(viewport[0]) + 'x' + str(viewport[1]) + suffix))
                MODULE.check_desktop_shell(shell, require_s0_footer=True)
                omitted = copy.deepcopy(shell); omitted.pop('s0Footer')
                with self.assertRaisesRegex(RuntimeError, 'omitted'): MODULE.check_desktop_shell(omitted, require_s0_footer=True)
                bad = copy.deepcopy(shell); bad['s0Footer']['coverage']['proof']['visible'] = False
                with self.assertRaises(RuntimeError): MODULE.check_desktop_shell(bad, require_s0_footer=True)
        self.assertFalse(MODULE.s0_footer_required('1440x900-12-directory-return'))
        glossary = copy.deepcopy(shell); glossary.pop('s0Footer')
        MODULE.check_desktop_shell(glossary)
        for mutate in (lambda d: d['window'].update(y=1), lambda d: d['landing'].update(height=500), lambda d: d['landingOffsets'].update(top=1)):
            bad = copy.deepcopy(glossary); mutate(bad)
            with self.assertRaises(RuntimeError): MODULE.check_desktop_shell(bad)
        code = inspect.getsource(MODULE.main)
        self.assertIn("capture(prefix + '-12-directory-return', require_home=True)", code)
        self.assertIn('require_s0_footer=requires_s0_footer', code)
        self.assertEqual(sum(MODULE.s0_footer_required('1440x900' + name) for name in MODULE.SCENE_NAMES), 5)

    def test_snapshot_javascript_syntax_and_existing_scene_wiring_remain_strict(self):
        import inspect
        syntax = subprocess.run(['node', '-e', "new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));"],
                                input=json.dumps(MODULE.S0_FOOTER_SNAPSHOT_JS), text=True, capture_output=True)
        self.assertEqual(syntax.returncode, 0, syntax.stdout + syntax.stderr)
        source = inspect.getsource(MODULE.main)
        self.assertIn("report.setdefault('s0FooterChecks', [])", source)
        self.assertIn("data['desktopShell']['s0Footer'] = s0_footer_check(name)", source)
        self.assertIn("check_s0_stability(footer_before_reload, footer_after_reload, restore=True)", source)
        self.assertIn("check_s0_stability(footer_before_endpoint, footer_after_back, restore=True)", source)
        self.assertIn("check_s0_wheel(wheel_before, wheel_record['after'], delta)", source)
        self.assertIn("closed['focus'] != 'np-relation-select-' + expected['id']", source)
        self.assertIn("'type': 'wheel', 'id': 's0-source-scroll'", source)
        self.assertIn("check_s0_footer(data['s0Footer'])", inspect.getsource(MODULE.check_desktop_shell))
        self.assertIn('RELATION_EVIDENCE_PROOF_JS', source)
        self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)
        for required in ('-00-default-reading-overview', '-31-s0-reading-hierarchy', '-13-relation-88', '-13-relation-90', '-13-relation-94'):
            self.assertIn(required, MODULE.SCENE_NAMES)
        snapshot = MODULE.S0_FOOTER_SNAPSHOT_JS
        for forbidden in ('scrollTop=', 'scrollTop =', 'replaceState(', 'pushState(', '.navigate(', 'dispatchEvent('):
            self.assertNotIn(forbidden, snapshot)
        self.assertNotRegex(snapshot, r'\.style\.[A-Za-z]+\s*=')


class AnalysisAnswerRowsCaptureChecks(unittest.TestCase):
    @classmethod
    def source_expected(cls):
        science = S0FooterCaptureChecks.source()
        entry = next(iter(science['analyses']['poni'].values()))
        return science, entry, MODULE.analysis_answer_rows_expected(science, entry['roots'][0])

    @classmethod
    def frame(cls, top=0):
        import copy
        _, _, expected = cls.source_expected()
        client = dict(x=450, y=270, width=950, height=500)
        route = dict(nav='1', scope='task:category-objectnav', tree='a', node=expected['root'], paper=expected['paper'],
                     version=expected['version'], bench=None, protocol=None, template=None, claim=None, mode='tree')
        data = dict(ready='ready', route=route, historyRoute=copy.deepcopy(route), window=dict(x=0, y=0),
                    viewport=dict(x=0, y=0, width=1440, height=900),
                    stationaryAncestors=[dict(selector=selector, top=0, left=0) for selector in MODULE.STATIONARY_SHELL_SELECTORS],
                    reader=dict(top=top, left=0, scrollHeight=1260, clientHeight=500, maxTop=760), readerClient=client, readerRect=client.copy(),
                    tree=dict(top=0, left=0, scrollHeight=600, clientHeight=500, maxTop=100), expanded=dict(a=[expected['root']]),
                    runtimeReader=top, historyReader=top, focus=dict(id='np-node-' + expected['root'], answer=None),
                    fixedIdentity=dict(position=expected['root'], paper=expected['paper'], version=expected['version']),
                    answerBodyCount=0, coverageCount=1, root=expected['root'], chapters=expected['chapters'].copy(), rows=[])
        for i, source in enumerate(expected['rows']):
            area = dict(x=460, y=client['y'] + 100 + i * 50 - top, width=920, height=44)
            proof = S0FooterCaptureChecks.proof(source['label'], area)
            visible = MODULE.rect_inside(area, client)
            proof['visible'] = visible
            proof['fragments'][0]['visible'] = visible
            proof['textRuns'][0]['fragments'][0]['visible'] = visible
            data['rows'].append({key: source[key] for key in ('id', 'parent', 'entity', 'chapter', 'paper', 'version', 'scope')} |
                dict(tag='BUTTON', type='button', disabled=False, hidden=False, role=None, tabIndex=0,
                     itemTag='LI', itemChildren=1, listTag='UL', listClass='np-analysis-answer-index', listRole=None,
                     itemRect=area.copy(), contentRect=dict(x=10, y=100 + i * 50, width=920, height=44), proof=proof))
        return data, expected

    @classmethod
    def scan(cls):
        frames = [cls.frame(top)[0] for top in (0, 250, 500, 750, 760)]
        expected = cls.frame()[1]
        visible = []
        for source in expected['rows']:
            index = next(i for i, frame in enumerate(frames) if MODULE.analysis_answer_visible(
                next(row for row in frame['rows'] if row['id'] == source['id']), frame, source['label']))
            visible.append(dict(id=source['id'], frame=index, label=source['label']))
        return dict(frames=frames, visibleRows=visible, bottom=frames[-1], positiveWheelCount=len(frames) - 1), expected

    @classmethod
    def keyboard(cls, index=0):
        import copy
        before, expected = cls.frame(500)
        target = expected['keyboardTargets'][index]
        source = next(row for row in expected['rows'] if row['id'] == target)
        before['focus'] = dict(id='', answer=target)
        route = MODULE.analysis_answer_route(before['route'], source)
        selected = copy.deepcopy(before)
        selected.update(route=copy.deepcopy(route), historyRoute=copy.deepcopy(route), answerBodyCount=1, coverageCount=0,
                        fixedIdentity=dict(position=target, paper=source['paper'], version=source['version']))
        after = copy.deepcopy(before); after['focus'] = dict(id='np-node-' + expected['root'], answer=None)
        key = 'Enter' if index == 0 else ' '
        return dict(target=target, key=key, before=before, selected=selected, after=after, expectedRoute=route,
                    events=[dict(type=kind, key=key, trusted=True, target=target) for kind in ('keydown', 'keyup')]), expected

    def test_source_preorder_keeps_all_answers_full_labels_and_same_named_distinct_destinations(self):
        science, entry, expected = self.source_expected()
        self.assertEqual(len(expected['rows']), entry['answeredOriginalCount'])
        self.assertEqual(len({row['id'] for row in expected['rows']}), entry['answeredOriginalCount'])
        self.assertEqual(expected['keyboardSelection'], 'same-label-distinct-original-IDs')
        left, right = [next(row for row in expected['rows'] if row['id'] == target) for target in expected['keyboardTargets']]
        self.assertNotEqual(left['id'], right['id']); self.assertEqual(left['label'], right['label'])
        self.assertEqual(left['label'], '具体怎么做的')
        self.assertTrue(all(not science['positions'][row['id']]['isPaperSpecificInstantiation'] for row in expected['rows']))
        for source in expected['rows']:
            science['entities'][source['entity']]['label'] = source['id']
        distinct = MODULE.analysis_answer_rows_expected(science, expected['root'])
        self.assertEqual(distinct['keyboardSelection'], 'two-distinct-original-IDs-no-repeated-source-label')
        self.assertEqual(distinct['keyboardTargets'], [distinct['rows'][0]['id'], distinct['rows'][-1]['id']])

    def test_actual_positive_scan_proves_every_complete_original_row_through_content_bottom(self):
        record, expected = self.scan()
        MODULE.check_analysis_answer_scan(record, expected)
        self.assertEqual(record['bottom']['reader']['top'], record['bottom']['reader']['maxTop'])
        self.assertEqual([row['id'] for row in record['visibleRows']], [row['id'] for row in expected['rows']])
        self.assertGreater(record['visibleRows'][-1]['frame'], 0)
        self.assertFalse(MODULE.analysis_answer_visible(record['frames'][0]['rows'][-1], record['frames'][0], expected['rows'][-1]['label']))

    def test_answer_rows_reject_missing_reordered_merged_inline_clipped_and_wrong_version(self):
        import copy
        good, expected = self.frame()
        mutations = [lambda d: d['rows'].pop(), lambda d: d['rows'].reverse(),
                     lambda d: d['rows'][1].update(id=d['rows'][0]['id']),
                     lambda d: d['rows'][1]['proof'].update(text=d['rows'][0]['proof']['text'] + d['rows'][1]['proof']['text']),
                     lambda d: d['rows'][1]['contentRect'].update(y=d['rows'][0]['contentRect']['y']),
                     lambda d: d['rows'][1]['contentRect'].update(y=d['rows'][0]['contentRect']['y'] + 43),
                     lambda d: d['rows'][0]['proof'].update(clipped=True), lambda d: d['rows'][0]['proof'].update(renderedText='简称'),
                     lambda d: d['rows'][0].update(itemTag='SPAN'), lambda d: d['rows'][0].update(itemChildren=2),
                     lambda d: d['rows'][0].update(tag='A'), lambda d: d['rows'][0].update(role='treeitem'),
                     lambda d: d['rows'][0].update(disabled=True), lambda d: d['rows'][0].update(tabIndex=-1),
                     lambda d: d['rows'][0].update(version='other-version'), lambda d: d['rows'][0].update(paper='other-paper'),
                     lambda d: d['rows'][0].update(parent='wrong-parent'), lambda d: d['rows'][0].update(chapter='wrong-chapter'),
                     lambda d: d['chapters'].reverse(), lambda d: d['route'].update(version='wrong'),
                     lambda d: d['historyRoute'].pop('claim'), lambda d: d.update(coverageCount=2),
                     lambda d: d['rows'][0]['itemRect'].update(width=100), lambda d: d['readerClient'].update(x=1440)]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError): MODULE.check_analysis_answer_rows(bad, expected)

    def test_scan_rejects_zero_actual_scroll_missing_bottom_covered_clipped_and_offreader_fragments(self):
        import copy
        good, expected = self.scan()
        mutations = [lambda d: d.update(positiveWheelCount=0), lambda d: d['frames'].__setitem__(1, copy.deepcopy(d['frames'][0])),
                     lambda d: d.update(bottom=d['frames'][0]), lambda d: d['visibleRows'].pop(),
                     lambda d: d['visibleRows'].reverse(), lambda d: d['frames'][-1]['reader'].update(top=759),
                     lambda d: d['frames'][1]['tree'].update(top=5), lambda d: d['frames'][1]['rows'][4]['contentRect'].update(x=15)]
        for i, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=i), self.assertRaises(RuntimeError): MODULE.check_analysis_answer_scan(bad, expected)
        for property, value in (('visible', False), ('fontSize', 14), ('foreground', []), ('background', []), ('unscaled', False)):
            bad = copy.deepcopy(good)
            for frame in bad['frames']: frame['rows'][-1]['proof'][property] = value
            with self.subTest(property=property), self.assertRaises(RuntimeError): MODULE.check_analysis_answer_scan(bad, expected)
        for target in ('fragment', 'run-fragment', 'reader'):
            bad = copy.deepcopy(good)
            for frame in bad['frames']:
                proof = frame['rows'][-1]['proof']
                if target == 'fragment': proof['fragments'][-1]['y'] = 880
                elif target == 'run-fragment': proof['textRuns'][0]['fragments'][-1]['y'] = 880
                else: frame['readerClient']['height'] = 100
            with self.subTest(target=target), self.assertRaises(RuntimeError): MODULE.check_analysis_answer_scan(bad, expected)

    def test_two_native_keys_require_exact_full_route_version_and_back_effective_offset(self):
        import copy
        for index in (0, 1):
            good, expected = self.keyboard(index)
            MODULE.check_analysis_answer_keyboard(good, expected, index)
            mutations = [lambda d: d.update(key='Escape'), lambda d: d.update(target=expected['keyboardTargets'][1 - index]),
                         lambda d: d['events'][0].update(trusted=False), lambda d: d['events'][0].update(target='wrong'),
                         lambda d: d['events'][0].update(key='Escape'), lambda d: d['events'].pop(),
                         lambda d: d['before']['reader'].update(top=0),
                         lambda d: d['selected']['route'].pop('protocol'), lambda d: d['selected']['route'].update(nav=True),
                         lambda d: d['selected']['route'].update(version='other-version'), lambda d: d['selected']['route'].update(claim='borrowed-claim'),
                         lambda d: d['selected']['historyRoute'].update(node='other'), lambda d: d['selected']['fixedIdentity'].update(position='other'),
                         lambda d: d['selected'].update(answerBodyCount=0), lambda d: d['after']['reader'].update(top=499),
                         lambda d: d['after'].update(runtimeReader=0), lambda d: d['after'].update(historyReader=0),
                         lambda d: d['after']['route'].update(node='other'), lambda d: d['before']['focus'].update(answer=None)]
            for i, mutate in enumerate(mutations):
                bad = copy.deepcopy(good); mutate(bad)
                with self.subTest(key=index, mutation=i), self.assertRaises(RuntimeError): MODULE.check_analysis_answer_keyboard(bad, expected, index)

    def test_production_answer_snapshot_records_order_and_complete_multiline_source_labels(self):
        science, entry, expected = self.source_expected()
        body = r"""
d.elementFromPoint=()=>d.body;w.Range.prototype.getClientRects=function(){return [];};
await scope('task:category-objectnav');await select(e.poni.id);d.getElementById('np-open-analysis-structure').click();await ready(()=>a.getState().route.node===input.answers.root&&a.getContent().ready(a.getBundle().positions[input.answers.root].entityId));
const snap=new w.Function(input.answerSnapshot),before=JSON.stringify(a.getState()),actual=snap();assert.equal(JSON.stringify(a.getState()),before);assert.equal(actual.root,input.answers.root);assert.equal(actual.coverageCount,1);assert.equal(actual.answerBodyCount,0);
assert.deepEqual(JSON.parse(JSON.stringify(actual.chapters)),input.answers.chapters);
assert.deepEqual(JSON.parse(JSON.stringify(actual.rows.map(row=>row.id))),input.answers.rows.map(row=>row.id));
for(let i=0;i<actual.rows.length;i++){assert.equal(actual.rows[i].proof.text,input.answers.rows[i].label);assert.equal(actual.rows[i].proof.renderedText,input.answers.rows[i].label);assert.equal(actual.rows[i].itemTag,'LI');assert.equal(actual.rows[i].tag,'BUTTON');assert.equal(actual.rows[i].itemChildren,1);assert.equal(actual.rows[i].version,input.answers.version);}
states.push(actual);
"""
        states = run_product_capture_script(self, body, dict(science=science, expected=MODULE.task_route_expected(science),
            answers=expected, answerSnapshot=MODULE.ANALYSIS_ANSWER_ROWS_SNAPSHOT_JS, viewport=dict(width=1440, height=900)))
        self.assertEqual(len(states[0]['rows']), entry['answeredOriginalCount'])
        self.assertTrue(any('\n' in row['proof']['text'] for row in states[0]['rows']))

    def test_answer_scripts_compile_and_existing_root_scene_uses_native_scan_keys_back_without_injection(self):
        import inspect
        for script in (MODULE.ANALYSIS_ANSWER_ROWS_SNAPSHOT_JS, MODULE.ANALYSIS_EXACT_ROUTE_READY_JS):
            result = subprocess.run(['node', '-e', "new Function(JSON.parse(require('fs').readFileSync(0,'utf8')));"], input=json.dumps(script), text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        code = inspect.getsource(MODULE.analysis_answer_rows_checks)
        for required in ('native_scroll(', "'type': 'keyDown'", "'type': 'keyUp'", "'/back'", "'keydown'", "'keyup'", 'e.isTrusted',
                         'check_native_wheel_progress(', "audit['bottom'] = current", 'check_analysis_answer_keyboard(', "scroll_to(initial['reader']['top'])"):
            self.assertIn(required, code)
        for forbidden in ('scrollTop=', 'scrollTop =', '.style.', '.navigate(', 'dispatchEvent(', 'replaceState(', 'pushState(', 'scrollIntoView('):
            self.assertNotIn(forbidden, code)
        flow = inspect.getsource(MODULE.exploration_state_checks)
        self.assertLess(flow.index('analysis_answer_rows_checks('), flow.index("capture(prefix + '-30-analysis-root-coverage')"))
        self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)


class AtomicReceiptPersistenceChecks(unittest.TestCase):
    """The same checkpoints retain all JSON evidence and survive failed writes."""

    @staticmethod
    def report():
        return {'head': 'fixture-head', 'complete': False, 'nullable': None, 'count': 0,
                'route': {'nav': '1', 'scope': 'scope:all', 'bench': None, 'protocol': None,
                          'tree': 'a', 'node': 'fixture:answer', 'paper': 'fixture:paper',
                          'version': 'fixture:version', 'claim': None, 'mode': 'read', 'template': None},
                'proofs': [{'text': '完整来源 · 研究问题\n第二行🙂', 'rect': {'x': 0.125, 'y': -2.5, 'width': 840, 'height': 36},
                            'visible': True, 'missing': None, 'fragments': [], 'events': ['keydown', 'keyup']}],
                'sameLabelDistinctIds': ['fixture:first', 'fixture:second'], 'empty': {}, 'offsets': [0, 12.75, 900]}

    def assert_only_receipt(self, directory, expected):
        self.assertEqual([path.name for path in directory.iterdir()], ['receipt.json'])
        self.assertEqual(json.loads((directory / 'receipt.json').read_text(encoding='utf-8')), expected)

    @staticmethod
    def failed_writer(real_factory):
        from contextlib import contextmanager
        from types import SimpleNamespace
        @contextmanager
        def factory(*args, **kwargs):
            with real_factory(*args, **kwargs) as stream:
                def write(payload):
                    stream.write(payload[:len(payload) // 2])
                    stream.flush()
                    raise OSError('injected partial temporary write')
                yield SimpleNamespace(name=stream.name, write=write)
        return factory

    def test_compact_unicode_roundtrip_keeps_every_field_type_order_and_checkpoint(self):
        import copy
        import tempfile
        report = self.report(); pristine = copy.deepcopy(report)
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'
            MODULE.write_receipt(target, report)
            raw = target.read_bytes()
            self.assertEqual(raw, (json.dumps(report, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8'))
            self.assertLess(len(raw), len((json.dumps(report, ensure_ascii=False, indent=2) + '\n').encode('utf-8')))
            self.assertEqual(list(json.loads(raw)), list(report))
            self.assertEqual(json.loads(raw), pristine)
            self.assertEqual(report, pristine)
            self.assert_only_receipt(Path(directory), pristine)

    def test_same_directory_atomic_replace_observes_complete_closed_temp_and_prior_target(self):
        import tempfile
        prior = {'previous': '完整检查点'}; report = self.report(); real_replace = MODULE.os.replace
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; target.write_text(json.dumps(prior), encoding='utf-8')
            original = target.read_bytes(); replacements = []
            def replace(source, destination):
                source = Path(source); destination = Path(destination)
                self.assertEqual(source.parent, target.parent)
                self.assertNotEqual(source, target)
                self.assertEqual(destination, target)
                self.assertTrue(source.name.startswith('.receipt.json.'))
                self.assertTrue(source.name.endswith('.tmp'))
                self.assertEqual(target.read_bytes(), original)
                self.assertEqual(json.loads(source.read_text(encoding='utf-8')), report)
                replacements.append((source, destination))
                real_replace(source, destination)
            with patch.object(MODULE.os, 'replace', side_effect=replace):
                MODULE.write_receipt(target, report)
            self.assertEqual(len(replacements), 1)
            self.assert_only_receipt(Path(directory), report)
            self.assertFalse(replacements[0][0].exists())

    def test_partial_temporary_write_failure_preserves_previous_receipt_and_cleans_temp(self):
        import tempfile
        real_factory = MODULE.tempfile.NamedTemporaryFile
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; prior = {'checkpoint': 'previous'}
            target.write_text(json.dumps(prior), encoding='utf-8'); original = target.read_bytes()
            with patch.object(MODULE.tempfile, 'NamedTemporaryFile', side_effect=self.failed_writer(real_factory)):
                with self.assertRaisesRegex(OSError, 'partial temporary write'):
                    MODULE.write_receipt(target, self.report())
            self.assertEqual(target.read_bytes(), original)
            self.assert_only_receipt(Path(directory), prior)

    def test_temporary_close_failure_never_replaces_prior_receipt_and_cleans_temp(self):
        from contextlib import contextmanager
        import tempfile
        real_factory = MODULE.tempfile.NamedTemporaryFile
        @contextmanager
        def failed_close(*args, **kwargs):
            with real_factory(*args, **kwargs) as stream:
                yield stream
            raise OSError('injected temporary close failure')
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; prior = {'checkpoint': 'previous'}
            target.write_text(json.dumps(prior), encoding='utf-8'); original = target.read_bytes()
            with patch.object(MODULE.tempfile, 'NamedTemporaryFile', side_effect=failed_close):
                with patch.object(MODULE.os, 'replace') as replace:
                    with self.assertRaisesRegex(OSError, 'temporary close failure'):
                        MODULE.write_receipt(target, self.report())
            replace.assert_not_called()
            self.assertEqual(target.read_bytes(), original)
            self.assert_only_receipt(Path(directory), prior)

    def test_replace_failure_preserves_previous_receipt_and_cleans_complete_temp(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; prior = {'checkpoint': 'previous'}
            target.write_text(json.dumps(prior), encoding='utf-8'); original = target.read_bytes()
            with patch.object(MODULE.os, 'replace', side_effect=OSError('injected replace failure')) as replace:
                with self.assertRaisesRegex(OSError, 'replace failure'):
                    MODULE.write_receipt(target, self.report())
            self.assertEqual(replace.call_count, 1)
            self.assertEqual(target.read_bytes(), original)
            self.assert_only_receipt(Path(directory), prior)

    def test_serialization_failure_never_creates_temp_or_changes_prior_receipt(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; prior = {'checkpoint': 'previous'}
            target.write_text(json.dumps(prior), encoding='utf-8'); original = target.read_bytes()
            report = self.report(); report['notJSON'] = {1, 2}
            with patch.object(MODULE.tempfile, 'NamedTemporaryFile') as create:
                with self.assertRaises(TypeError):
                    MODULE.write_receipt(target, report)
            create.assert_not_called()
            self.assertEqual(target.read_bytes(), original)
            self.assert_only_receipt(Path(directory), prior)

    def test_temporary_creation_failure_leaves_previous_receipt_untouched(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'; prior = {'checkpoint': 'previous'}
            target.write_text(json.dumps(prior), encoding='utf-8'); original = target.read_bytes()
            with patch.object(MODULE.tempfile, 'NamedTemporaryFile', side_effect=OSError('injected create failure')):
                with self.assertRaisesRegex(OSError, 'create failure'):
                    MODULE.write_receipt(target, self.report())
            self.assertEqual(target.read_bytes(), original)
            self.assert_only_receipt(Path(directory), prior)

    def test_failed_initial_write_cannot_publish_a_partial_first_receipt(self):
        import tempfile
        real_factory = MODULE.tempfile.NamedTemporaryFile
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'receipt.json'
            with patch.object(MODULE.tempfile, 'NamedTemporaryFile', side_effect=self.failed_writer(real_factory)):
                with self.assertRaises(OSError):
                    MODULE.write_receipt(target, self.report())
            self.assertFalse(target.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_original_save_wrapper_writes_each_call_immediately_with_all_96_call_sites(self):
        import ast
        import tempfile
        source = Path(MODULE.__file__).read_text(encoding='utf-8'); tree = ast.parse(source)
        separate_disclosure_save_sites(self, tree)
        native_paint = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settle_version_title_paint')
        self.assertEqual(len([n for n in ast.walk(native_paint) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']), 1)
        tree.body.remove(native_paint)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'save']
        self.assertEqual(len(calls), 103)  # 99 original + S0 paint + selector reveal + desktop paint + child audit saves.
        saves = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef) and node.name == 'save']
        self.assertEqual(len(saves), 1)
        self.assertEqual(ast.dump(saves[0].body[0].value.func), "Name(id='write_receipt', ctx=Load())")
        self.assertEqual(len(saves[0].body), 1)
        compiled = compile(ast.fix_missing_locations(ast.Module(body=[saves[0]], type_ignores=[])), '<original-save>', 'exec')
        with tempfile.TemporaryDirectory() as directory:
            report = self.report(); namespace = {'out': Path(directory), 'report': report}
            with patch.object(MODULE, 'write_receipt', wraps=MODULE.write_receipt) as writer:
                namespace['write_receipt'] = writer
                exec(compiled, namespace)
                for count in range(3):
                    report['count'] = count; report['complete'] = count == 2
                    namespace['save']()
                    self.assertEqual(writer.call_count, count + 1)
                    self.assert_only_receipt(Path(directory), report)
            self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)


class S0SelectorOcclusionChecks(unittest.TestCase):
    @staticmethod
    def fixture(width=1440, selected=None):
        data = S0FooterCaptureChecks.fixture(width, selected)
        row = next(row for row in data['nodes'] if row['id'] == data['expected']['challenge'])
        label = row['labels']['title']; r = label['rect']
        # The native popup covers only the right half: some probes still hit label.
        popup_rect = dict(x=r['x'] + r['width'] / 2, y=120, width=data['viewport']['width'] - r['x'] - r['width'] / 2 - 16, height=330)
        popup = S0FooterCaptureChecks.proof('Existing native selector', popup_rect)
        popup['clipped'] = True  # The existing popup itself may scroll.
        data.update(selectorOpen=True, relationSelector=dict(id='np-task-relations', tag='DETAILS', open=True, inToolbar=True, count=1, proof=popup))
        label['visible'] = False
        label['hitProbes'] = []
        for fx, fy in ((.5, .5), (.1, .1), (.9, .1), (.1, .9), (.9, .9)):
            x, y = r['x'] + r['width'] * fx, r['y'] + r['height'] * fy
            covered = x >= popup_rect['x']
            label['hitProbes'].append(dict(x=x, y=y, label=not covered, selector=covered,
                ancestorIds=['np-relation-select-tasks:relation:88', 'np-task-relations', 'navigation-product'] if covered else ['navigation-product'],
                hitId='np-relation-select-tasks:relation:88' if covered else '', hitTag='BUTTON' if covered else 'H3'))
        return data, label

    def test_exact_open_native_popup_may_occlude_samples_without_claiming_label_exposure(self):
        for width in (1440, 1920):
            for selected in (None, *S0FooterCaptureChecks.expected()['readouts']):
                data, label = self.fixture(width, selected)
                self.assertFalse(label['visible'])
                self.assertTrue(MODULE.s0_label_exposed(label, data))
                MODULE.check_s0_footer(data)
                # This is still an actual covered label, not mutated exposure data.
                self.assertFalse(label['visible'])
                self.assertTrue(data['relationSelector']['proof']['clipped'])

    def test_closed_state_missing_popup_wrong_identity_and_foreign_cover_fail(self):
        import copy
        good, _ = self.fixture()
        def label(data): return next(row for row in data['nodes'] if row['id'] == data['expected']['challenge'])['labels']['title']
        mutations = [lambda d: d.update(selectorOpen=False), lambda d: d.pop('relationSelector'),
            lambda d: d['relationSelector'].update(open=False), lambda d: d['relationSelector'].update(id='foreign-overlay'),
            lambda d: d['relationSelector'].update(tag='DIV'), lambda d: d['relationSelector'].update(count=2),
            lambda d: d['relationSelector'].update(inToolbar=False),
            lambda d: d['relationSelector']['proof'].update(visible=False), lambda d: d['relationSelector']['proof'].update(opaque=False),
            lambda d: d['relationSelector']['proof'].update(unscaled=False),
            lambda d: d['relationSelector']['proof']['rect'].update(x=-1),
            lambda d: d['relationSelector']['proof']['rect'].update(y=500),
            lambda d: label(d)['hitProbes'][0].update(selector=False, ancestorIds=['foreign-cover']),
            lambda d: label(d)['hitProbes'][0].update(ancestorIds=['np-task-relations-wrong']),
            lambda d: label(d)['hitProbes'][0].update(label=True),
            lambda d: label(d)['hitProbes'][0].update(x=label(d)['hitProbes'][0]['x'] + 1),
            lambda d: label(d)['hitProbes'][0].update(y=0),
            lambda d: label(d)['hitProbes'][0].update(selector='true'),
            lambda d: label(d)['hitProbes'].pop(), lambda d: label(d).pop('hitProbes')]
        for index, mutate in enumerate(mutations):
            bad = copy.deepcopy(good); mutate(bad)
            with self.subTest(mutation=index), self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)
        MODULE.check_s0_footer(good)

    def test_popup_exception_never_relaxes_text_style_identity_clipping_or_geometry(self):
        import copy
        good, _ = self.fixture()
        def label(data): return next(row for row in data['nodes'] if row['id'] == data['expected']['challenge'])['labels']['title']
        for change in (dict(opaque=False), dict(unscaled=False), dict(clipped=True), dict(fontSize=14), dict(foreground=[180, 180, 180]), dict(background=[])):
            bad = copy.deepcopy(good); label(bad).update(change)
            with self.subTest(change=change), self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)
        bad = copy.deepcopy(good); label(bad)['rect']['x'] -= 50
        with self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)
        bad = copy.deepcopy(good); bad['nodes'][0]['id'] = 'invented-source'
        with self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)
        # A different label covered by an unrelated element is still a failure.
        bad = copy.deepcopy(good); bad['nodes'][0]['labels']['title']['visible'] = False
        with self.assertRaises(RuntimeError): MODULE.check_s0_adaptive_spacing(bad)

    def test_same_view_stability_and_close_focus_contracts_still_include_open_picker(self):
        import copy
        before, _ = self.fixture(); after, _ = self.fixture(selected='tasks:relation:88')
        after.update(selectorOpen=False)
        after['relationSelector']['open'] = False
        title = next(row for row in after['nodes'] if row['id'] == after['expected']['challenge'])['labels']['title']; title['visible'] = True
        MODULE.check_s0_stability(before, after)
        for field in ('x', 'y'):
            bad = copy.deepcopy(after); bad['map']['rect'][field] += 1
            with self.subTest(field=field), self.assertRaises(RuntimeError): MODULE.check_s0_stability(before, bad)
        closed, label = self.fixture(); closed.update(selectorOpen=False); closed['relationSelector']['open'] = False
        with self.assertRaises(RuntimeError): MODULE.check_s0_footer(closed)
        label['visible'] = True
        MODULE.check_s0_footer(closed)

    def test_capture_records_actual_hit_ancestry_and_keeps_all_original_native_checkpoints(self):
        import inspect, ast
        js = MODULE.S0_FOOTER_SNAPSHOT_JS
        for text in ('document.elementFromPoint(x,y)', 'e.contains(hit)', 'selector.contains(hit)', 'ancestorIds:ids', "selector.tagName", "selector.open", "querySelectorAll('#np-task-relations').length", 'proof:box(selector)', 'proof.hitProbes=', "selector.matches('#np-reading-landing>.np-overview-map-toolbar>#np-task-relations')"):
            self.assertIn(text, js)
        main = inspect.getsource(MODULE.main)
        for text in ("s0_footer_check('before-selection-'", "s0_footer_check('closed-'", "check_s0_stability(before_selection, selected_footer)", "closed['focus'] != 'np-relation-select-'", 'check_s0_stability(footer_before_reload, footer_after_reload, restore=True)'):
            self.assertIn(text, main)
        tree = ast.parse(inspect.getsource(MODULE))
        separate_disclosure_save_sites(self, tree)
        native_paint = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'settle_version_title_paint')
        self.assertEqual(len([n for n in ast.walk(native_paint) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']), 1)
        tree.body.remove(native_paint)
        saves = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id == 'save']
        self.assertEqual(len(saves), 103)  # 99 original + S0 paint + selector reveal + desktop paint + child audit saves.
        self.assertEqual(len(MODULE.SCENE_NAMES) * len(MODULE.VIEWPORTS), 106)


if __name__ == '__main__':
    unittest.main()


class VersionTitleCaptureChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import gzip
        import sys
        paths = patch.object(sys, 'path', [str(Path(__file__).parents[1] / 'scripts'), *sys.path])
        paths.start(); cls.addClassCleanup(paths.stop)
        cls.science = json.loads(gzip.decompress((Path(__file__).parents[1] / 'data/navigation-product/model.json.gz').read_bytes()))
        cls.expected = MODULE.version_title_expected(cls.science)

    @classmethod
    def fixture(cls, index=0, width=1440, height=900):
        import copy
        expected = copy.deepcopy(cls.expected[index])
        area = dict(x=0, y=0, width=width, height=height)
        rect = dict(x=160, y=350, width=1000, height=72)
        fragment = dict(x=160, y=350, width=800, height=24, visible=True)
        run = dict(text=expected['title'], opaque=True, unscaled=True, fontSize=16,
                   foreground=[24,49,61], background=[251,252,249], clipAreas=[], fragments=[fragment.copy()])
        proof = dict(text=expected['title']+'具体方法', renderedText=expected['title'], rect=rect,
                     visible=True, opaque=True, unscaled=True, fontSize=16, foreground=[24,49,61],
                     background=[251,252,249], clipped=False, fragments=[fragment.copy()], textRuns=[run],
                     clipAreas=[], viewport=area, readerContent=dict(x=120,y=0,width=1200,height=height),
                     textOverflow='clip', lineClamp='none')
        nav = dict(branchPath='/research/navigation/branches/'+expected['branch'], branchTitle=expected['title'],
                   enhancedHref=expected['enhancedHref'], route=copy.deepcopy(expected['route']), ready=True,
                   sourcePosition=expected['sourcePosition'], entity=expected['entity'], label=expected['title'],
                   sourceScope=expected['sourceScope'], sourceLabel=expected['sourceLabel'], console=[], networkFailures=[])
        data = dict(screenKind='native_version_title', position=expected['position'], ancestors=expected['ancestors'].copy(),
                    ancestorOpen=[True]*len(expected['ancestors']), focusedSummary=True, title=proof,
                    linkCount=1, branchHref=expected['branch'], pagePath='/research/navigation/branches/index.html',
                    readyState='complete', scriptCount=4, appPresent=False, sourceBinding=copy.deepcopy(expected),
                    scripts=[dict(src='../../../assets/'+name,defer=True,inline='') for name in ('catalog-navigation.js','presentation.js','interface.js','chrome.js')],
                    nativeActions=[dict(position=pid,beforeOpen=False,afterOpen=True,clicked=True) for pid in expected['ancestors']],
                    fonts='loaded', viewport=dict(width=width,height=height,dpr=1), bodyWidth=width, windowScroll=400,
                    pngDimensions=[width,height],pixelVariation=True,screenshotSha256='a'*64,
                    renderedFonts=[dict(familyName='Noto Sans',glyphCount=80)],console=[],networkFailures=[],enhancedNavigation=nav)
        return data, expected

    def test_exact_four_version_titles_and_original_98_scenes_are_preserved(self):
        self.assertEqual([x['position'] for x in self.expected], [
            'pos:g:18a33fba17e8e92ee1ed5d','pos:g:751e83079cd6d4ffeaf58a',
            'pos:g:e45df86dddd9cb1b67463c','pos:g:31c6cd8857132fbe346c39'])
        self.assertEqual(len(MODULE.SCENE_NAMES[:-4])*len(MODULE.VIEWPORTS),98)
        self.assertEqual(MODULE.SCENE_NAMES[-4:],tuple(row['suffix'] for row in self.expected))
        self.assertEqual(len(MODULE.SCENE_NAMES)*len(MODULE.VIEWPORTS),106)
        self.assertEqual(len(set(MODULE.SCENE_NAMES)),53)
        for i in range(4):
            for width,height in MODULE.VIEWPORTS:
                data,expected=self.fixture(i,width,height);MODULE.check_version_title_capture(data,expected)
        before=json.dumps(self.science,sort_keys=True);MODULE.version_title_expected(self.science)
        self.assertEqual(json.dumps(self.science,sort_keys=True),before)

    def test_version_title_source_inventory_rejects_wrong_or_duplicate_occurrences(self):
        import copy
        for mutation in ('title','paper','version','duplicate'):
            rows=list(MODULE.VERSION_TITLE_CASES)
            if mutation=='duplicate':rows[-1]=rows[0]
            else:
                first=list(rows[0]);first[{'title':4,'paper':2,'version':3}[mutation]]='wrong';rows[0]=tuple(first)
            with self.subTest(mutation=mutation),patch.object(MODULE,'VERSION_TITLE_CASES',tuple(rows)),self.assertRaises(RuntimeError):
                MODULE.version_title_expected(self.science)

    def test_version_title_gate_rejects_identity_ancestry_selection_and_link_errors(self):
        import copy
        mutations=[lambda d:d.update(position='wrong'),lambda d:d['ancestors'].reverse(),
                   lambda d:d['ancestorOpen'].__setitem__(0,False),lambda d:d.update(focusedSummary=False),
                   lambda d:d.update(linkCount=2),lambda d:d.update(linkCount=0),lambda d:d.update(branchHref='wrong.html'),
                   lambda d:d.update(pagePath='/research/navigation/index.html'),lambda d:d.update(scriptCount=1),
                   lambda d:d['scripts'][0].update(src='../../../assets/navigation-product.js'),
                   lambda d:d['scripts'][0].update(inline='window.NavigationProductApp={}'),
                   lambda d:d['scripts'][0].update(defer=False),
                   lambda d:d.update(appPresent=True),lambda d:d['sourceBinding'].update(version='wrong'),
                   lambda d:d['sourceBinding'].update(paper='wrong'),lambda d:d['nativeActions'].pop(),
                   lambda d:d['nativeActions'][-1].update(clicked=False),lambda d:d['nativeActions'][0].update(position='wrong')]
        for i,mutate in enumerate(mutations):
            data,expected=self.fixture();mutate(data)
            with self.subTest(mutation=i),self.assertRaises(RuntimeError):MODULE.check_version_title_capture(data,expected)

    def test_version_title_gate_rejects_truncation_occlusion_scaling_and_fake_bounds(self):
        mutations=[lambda d:d['title'].update(renderedText=d['title']['renderedText'][:-1]),
                   lambda d:d['title'].update(clipped=True),lambda d:d['title'].update(visible=False),
                   lambda d:d['title'].update(opaque=False),lambda d:d['title'].update(unscaled=False),
                   lambda d:d['title'].update(fontSize=15),lambda d:d['title']['textRuns'][0].update(fontSize=15),
                   lambda d:d['title'].update(textOverflow='ellipsis'),lambda d:d['title'].update(lineClamp='2'),
                   lambda d:d['title']['fragments'][0].update(visible=False),
                   lambda d:d['title']['textRuns'][0]['fragments'][0].update(visible=False),
                   lambda d:d['title']['fragments'][0].update(y=899),lambda d:d['title'].update(textRuns=[]),
                   lambda d:d['title'].update(fragments=[]),lambda d:d['title']['viewport'].update(width=2000),
                   lambda d:d['title']['readerContent'].update(width=2000),lambda d:d.update(bodyWidth=1442),
                   lambda d:d['title']['textRuns'][0].update(foreground=[230,230,230]),
                   lambda d:d['title']['textRuns'][0]['clipAreas'].append(dict(x=0,y=0,width=20,height=20))]
        for i,mutate in enumerate(mutations):
            data,expected=self.fixture();mutate(data)
            with self.subTest(mutation=i),self.assertRaises(RuntimeError):MODULE.check_version_title_capture(data,expected)

    def test_version_title_gate_requires_actual_media_fonts_and_resource_health(self):
        mutations=[lambda d:d.update(pngDimensions=[900,1440]),lambda d:d.update(pixelVariation=False),
                   lambda d:d.update(screenshotSha256='wrong'),lambda d:d.update(renderedFonts=[]),
                   lambda d:d['renderedFonts'][0].update(glyphCount=0),lambda d:d.update(fonts='loading'),
                   lambda d:d['viewport'].update(dpr=2),lambda d:d.update(console=[dict(level='SEVERE')]),
                   lambda d:d.update(networkFailures=[dict(status=404)]),lambda d:d.update(readyState='loading')]
        for i,mutate in enumerate(mutations):
            data,expected=self.fixture();mutate(data)
            with self.subTest(mutation=i),self.assertRaises(RuntimeError):MODULE.check_version_title_capture(data,expected)

    def test_version_title_navigation_must_retain_exact_actual_source(self):
        mutations=[lambda n:n.update(branchPath='wrong'),lambda n:n.update(branchTitle='old title'),
                   lambda n:n.update(enhancedHref='wrong'),lambda n:n['route'].update(paper='cow'),
                   lambda n:n['route'].update(version='source:legacy:langmap26:0'),lambda n:n['route'].update(node='wrong'),
                   lambda n:n.update(ready=False),lambda n:n.update(sourcePosition='wrong'),lambda n:n.update(entity='wrong'),
                   lambda n:n.update(label='old title'),lambda n:n.update(sourceScope='wrong'),lambda n:n.update(sourceLabel='changed'),
                   lambda n:n.update(console=[dict(level='SEVERE')]),lambda n:n.update(networkFailures=[dict(status=404)])]
        data,expected=self.fixture();del data['enhancedNavigation']
        MODULE.check_version_title_capture(data,expected,require_navigation=False)
        with self.assertRaises(RuntimeError):MODULE.check_version_title_capture(data,expected)
        for i,mutate in enumerate(mutations):
            data,expected=self.fixture();mutate(data['enhancedNavigation'])
            with self.subTest(mutation=i),self.assertRaises(RuntimeError):MODULE.check_version_title_capture(data,expected)

    def test_version_title_flow_uses_native_controls_and_preserves_original_capture(self):
        import inspect,ast
        source=inspect.getsource(MODULE.version_title_checks)
        self.assertIn('driver.click(driver.selector(selector + \' > summary\'))',source)
        self.assertIn('driver.click(driver.selector(link_selector))',source)
        self.assertIn('driver.click(control)',source)
        self.assertIn('scrollIntoView',source)
        for forbidden in ('.navigate(','.open =','.open=','.textContent=','.textContent =','innerHTML','style.'):
            self.assertNotIn(forbidden,source)
        tree=ast.parse(Path(MODULE.__file__).read_text());main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
        calls=[n for n in ast.walk(main) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='version_title_checks']
        self.assertEqual(len(calls),1)
        self.assertEqual([n.id for n in calls[0].args],['driver','report','save','prefix','base','science','out'])
        result=subprocess.run(['node','-e','new Function(JSON.parse(require("fs").readFileSync(0,"utf8")));'],input=json.dumps(MODULE.VERSION_TITLE_SNAPSHOT_JS),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_snapshot_and_native_links_use_real_generated_full_titles(self):
        import tempfile
        root=Path(__file__).parents[1]
        with tempfile.TemporaryDirectory(prefix='.version-title-native-',dir=root) as tmp:
            result=subprocess.run(['python3','-c',"import sys;from pathlib import Path;sys.path.insert(0,'scripts');import navigation_product as p;p.write_preview(Path('.').resolve(),Path(sys.argv[1]))",tmp],cwd=root,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            script=r"""
const fs=require('fs'),path=require('path'),assert=require('node:assert/strict'),{JSDOM}=require('jsdom'),input=JSON.parse(fs.readFileSync(0,'utf8'));
const folder=path.join(input.root,'research/navigation/branches'),dom=new JSDOM(fs.readFileSync(path.join(folder,'index.html'),'utf8'),{url:'https://example.org/research/navigation/branches/index.html',runScripts:'outside-only'}),w=dom.window,d=w.document,states=[];
try{
Object.defineProperty(d,'readyState',{value:'complete'});Object.defineProperty(d,'fonts',{value:{status:'loaded'}});
Object.defineProperty(w,'innerWidth',{value:1440});Object.defineProperty(w,'innerHeight',{value:900});Object.defineProperty(w,'devicePixelRatio',{value:1});Object.defineProperty(d.body,'scrollWidth',{value:1440});
// JSDOM verifies the actual native markup/selectors and text, not Chrome layout.
w.getComputedStyle=()=>({display:'block',visibility:'visible',opacity:'1',transform:'none',zoom:'1',fontSize:'16px',color:'rgb(24,49,61)',backgroundColor:'rgb(251,252,249)',overflowX:'visible',overflowY:'visible',textOverflow:'clip',webkitLineClamp:'none'});
w.HTMLElement.prototype.getBoundingClientRect=function(){return this.tagName==='MAIN'?{x:120,y:0,width:1200,height:900}:{x:160,y:350,width:1000,height:72};};
w.Range.prototype.getClientRects=function(){return [{x:160,y:350,width:800,height:24}];};
const snapshot=new w.Function(input.snapshot);
for(const expected of input.cases){
 const actions=[];
 for(const pid of expected.ancestors){const n=d.querySelector('[data-native-position="'+pid+'"]'),before=n.open;if(!before)n.querySelector(':scope > summary').click();assert.equal(n.open,true);actions.push({position:pid,beforeOpen:before,afterOpen:n.open,clicked:!before});}
 const n=d.querySelector('[data-native-position="'+expected.position+'"]'),summary=n.querySelector(':scope > summary');summary.focus();d.elementFromPoint=()=>summary;
 const data=snapshot(expected);assert.equal(data.title.renderedText,expected.title);assert.equal(data.title.textRuns.length,1);assert.ok(summary.querySelector('.native-depth'),'original badge still present but is not substituted for title');
 assert.equal(data.branchHref,expected.branch);const branch=new JSDOM(fs.readFileSync(path.join(folder,data.branchHref),'utf8'),{url:'https://example.org/research/navigation/branches/'+data.branchHref});
 try{assert.equal(branch.window.document.querySelector('main > h1').textContent,expected.title);const link=[...branch.window.document.querySelectorAll('main > p > a')].filter(a=>a.getAttribute('href')===expected.enhancedHref);assert.equal(link.length,1);const route=Object.fromEntries(new URL(link[0].href).hash.slice(1).split('&').map(s=>s.split('=').map(decodeURIComponent)));for(const key of ['node','paper','version','scope','tree'])assert.equal(route[key],expected.route[key]);}finally{branch.window.close();}
 data.nativeActions=actions;states.push(data);
}
const expected=input.cases[0],target=d.querySelector('[data-native-position="'+expected.position+'"]');target.after(target.cloneNode(true));assert.throws(()=>snapshot(expected),/missing or duplicated/);
process.stdout.write(JSON.stringify(states));
}finally{dom.window.close();}
"""
            result=subprocess.run(['node','-e',script],cwd=root,input=json.dumps({'root':tmp,'cases':self.expected,'snapshot':MODULE.VERSION_TITLE_SNAPSHOT_JS}),text=True,capture_output=True,timeout=60)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            states=json.loads(result.stdout);self.assertEqual(len(states),4)
            for actual,expected in zip(states,self.expected):
                good,_=self.fixture();actual.update(sourceBinding=expected,renderedFonts=good['renderedFonts'],pngDimensions=[1440,900],pixelVariation=True,screenshotSha256='a'*64,console=[],networkFailures=[])
                MODULE.check_version_title_capture(actual,expected,require_navigation=False)


class MethodChildReadabilityChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        MethodReadingCaptureChecks.setUpClass()

    def fixture(self, case='global'):
        return MethodReadingCaptureChecks().receipt(case)

    def test_actual_failure_requires_child_native_proof_and_preserves_first_screen_ancestry(self):
        import copy
        data,expected=self.fixture();child=data['rows'][-1]
        data['tree']=dict(x=17,y=382.390625,width=398,height=455.609375)
        # Reproduce the real below-viewport child, without altering the independent
        # source text or the separately revealed proof frame.
        for key,y,h in (('proof',859.890625,93),('roleProof',957.890625,21)):
            child[key]['rect'].update(y=y,height=h);child[key]['visible']=False
        # Synthetic fixture ancestor geometry is shifted into the real current pane.
        for index,row in enumerate(data['rows'][:-1]):
            row['proof']['rect'].update(y=394+index*65,height=28)
            row['roleProof']['rect'].update(y=422+index*65,height=20)
        audit=data['childReadability'];audit['binding']=MODULE.method_child_binding(data['captureName'],data,expected)
        for state in [audit['before'],audit['after'],audit['proofs'][0]['state'],*[a[k] for a in audit['actions'] for k in ('before','after')]]:
            state['tree']['client']=copy.deepcopy(data['tree'])
        item=audit['proofs'][0];item['state']['tree']['top']=145
        audit['actions'][0]['after']['tree']['top']=145;audit['actions'][1]['before']['tree']['top']=145
        for key,y,h in (('proof',714.890625,93),('roleProof',812.890625,21)):
            item['row'][key]['rect'].update(y=y,height=h)
        for trace in [k['trace'] for k in audit['keys']]:
            for frame in [trace['before'],trace['after'],*(e['snapshot'] for e in trace['events'])]:
                frame['tree']['clientRect']=copy.deepcopy(data['tree']);frame['tree']['rect']=copy.deepcopy(data['tree'])
        for trace in (item['keyTrace'],audit['keys'][0]['trace']):
            for frame in [trace['before'],trace['after'],*(e['snapshot'] for e in trace['events'])]:
                frame['tree']['clientRect']=copy.deepcopy(data['tree']);frame['tree']['rect']=copy.deepcopy(data['tree']);frame['tree']['top']=145
        audit['afterSnapshot']=copy.deepcopy({k:v for k,v in data.items() if k not in ('captureName','childReadability')})
        MODULE.check_method_reading(data,expected,MethodReadingCaptureChecks.source_positions,compact=True)
        old=copy.deepcopy(data)
        self.assertFalse(MODULE._reader_proof(old['rows'][-1]['proof'],old['tree'],old['viewport'],font_size=15),'old all-at-once requirement stays red at actual CI coordinates')
        bad=copy.deepcopy(data);bad.pop('childReadability')
        with self.assertRaisesRegex(RuntimeError,'lacks its complete'):MODULE.check_method_reading(bad,expected,MethodReadingCaptureChecks.source_positions)
        for key in ('proof','roleProof'):
            bad=copy.deepcopy(data);bad['rows'][0][key]['visible']=False
            with self.assertRaises(RuntimeError):MODULE.check_method_reading(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_receipt_replay_requires_final_snapshot_quiet_windows_and_exact_key_action_bridge(self):
        import copy
        data,expected=self.fixture()
        for mutate in (lambda a:a.pop('afterSnapshot'),lambda a:a.update(afterSnapshot={}),lambda a:a.pop('settles'),
                       lambda a:a['settles'][0].update(ok=False),lambda a:a['settles'][0].update(quietMs=159),lambda a:a['settles'][0].update(elapsed=2001),
                       lambda a:a['actions'][0].update(kind='anything'),lambda a:a['actions'][0]['events'].update(events=[]),
                       lambda a:a['keys'][0].update(actionIndex=1),lambda a:a['actions'][0]['events']['events'][0].update(key='Home'),
                       lambda a:a['actions'][0]['events']['events'][0].update(target='other-node'),lambda a:a['actions'][0]['events']['events'][0].update(trusted=False),
                       lambda a:a['before']['active'].update(original=False),lambda a:a['before'].update(hoverSame=False)):
            bad=copy.deepcopy(data);mutate(bad['childReadability'])
            with self.subTest(mutation=mutate),self.assertRaises(RuntimeError):MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_all_thirteen_scene_sources_bind_technical_and_portable_environment_children(self):
        science=MethodReadingCaptureChecks.science;positions=MethodReadingCaptureChecks.source_positions
        routes=MODULE.task_route_expected(science)
        sources=[MethodReadingCaptureChecks.cases['global'],MethodReadingCaptureChecks.cases['local'],routes['poni'],*routes['image'],*routes['portable']]
        self.assertEqual(len(sources),8)
        for source in sources:
            expected=MODULE.method_reading_expected(science,source,positions)
            self.assertEqual(set(expected['childDisplay']),set(source['childIds']))
            for pid,display in expected['childDisplay'].items():
                child=positions[pid];self.assertIn(child['kind'],('technical_improvement','environment'))
                self.assertEqual(display['label'],science['entities'][child['entityId']]['label'])
                role='有来源的阅读条目' if child['kind']=='environment' else '技术改进'+(' · 条件关联' if child.get('association')=='condition' else '')
                self.assertEqual(display['role'],role)
        self.assertTrue(all(positions[p['childIds'][0]]['kind']=='environment' for p in routes['portable']))

    def test_source_claim_viewport_scene_and_expansion_cannot_reuse_an_audit(self):
        import copy
        data,expected=self.fixture('imported')
        for mutate in (lambda d:d['route'].update(claim='different-original-claim'),lambda d:d.update(captureName='1920x1080-24-poni-claim'),
                       lambda d:d['viewport'].update(width=1920),lambda d:d['expanded']['l'].pop(),
                       lambda d:d['childReadability']['binding'].update(scienceSha256='0'*64),
                       lambda d:d['childReadability']['binding']['identity'].update(version='wrong'),
                       lambda d:d['childReadability'].update(required=[]),lambda d:d['childReadability']['proofs'].clear(),
                       lambda d:d['childReadability']['proofs'].append(copy.deepcopy(d['childReadability']['proofs'][0]))):
            bad=copy.deepcopy(data);mutate(bad)
            with self.subTest(mutation=mutate),self.assertRaises(RuntimeError):MODULE.check_method_reading(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_children_keep_full_text_role_contrast_font_hit_and_clip_gates(self):
        import copy
        data,expected=self.fixture()
        for key in ('proof','roleProof'):
            for mutate in (lambda p:p.update(text='short'),lambda p:p.update(visible=False),lambda p:p.update(opaque=False),
                           lambda p:p.update(unscaled=False),lambda p:p.update(clipped=True),lambda p:p.update(fontSize=14.99),
                           lambda p:p.update(foreground=[240,240,240]),lambda p:p.update(background=[]),lambda p:p['rect'].update(y=899)):
                bad=copy.deepcopy(data);mutate(bad['childReadability']['proofs'][0]['row'][key])
                with self.subTest(key=key,mutation=mutate),self.assertRaises(RuntimeError):MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)
        for mutate in (lambda p:p['keyTrace']['events'][0].update(isTrusted=False),lambda p:p['state']['active'].update(position='other'),
                       lambda p:p['state'].update(roving=['other']),lambda p:p['keyTrace']['after']['tree'].update(top=12),
                       lambda p:p['row'].update(parent='different-source')):
            bad=copy.deepcopy(data);mutate(bad['childReadability']['proofs'][0])
            with self.assertRaises(RuntimeError):MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_matching_initial_and_revealed_shortened_text_cannot_replace_source_expectation(self):
        import copy
        data,expected=self.fixture()
        for field,proof in (('label','proof'),('role','roleProof')):
            bad=copy.deepcopy(data)
            for row in (bad['rows'][-1],bad['childReadability']['proofs'][0]['row']):
                row[field]='truncated';row[proof]['text']='truncated'
            with self.assertRaisesRegex(RuntimeError,'independent scientific source'):
                MODULE.check_method_reading(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_exact_return_rejects_runtime_history_focus_scroll_dom_and_hover_drift(self):
        import copy
        data,expected=self.fixture();base=data['childReadability']['after'];key=base['contextKey'];hk=base['historyKey']
        for mutate in (lambda a:a['tree'].update(top=12),lambda a:a['reader'].update(top=160),lambda a:a['window'].update(y=1),
                       lambda a:a.update(domSame=False),lambda a:a.update(hoverSame=False),lambda a:a['active'].update(original=False),
                       lambda a:a.update(roving=[expected['children'][0]]),lambda a:a['runtime']['contexts'][key].update(focusTarget='other'),
                       lambda a:a['history'][hk]['contexts'][key].update(focusTarget='other'),lambda a:a['runtime']['contexts'][key]['expandedByTree']['g'].pop(),
                       lambda a:a['runtime']['route'].update(claim='other')):
            bad=copy.deepcopy(data);mutate(bad['childReadability']['after'])
            with self.subTest(mutation=mutate),self.assertRaises(RuntimeError):MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_explicit_empty_closed_child_audit_is_required_and_visible_child_need_not_scroll(self):
        data,expected=self.fixture()
        MODULE.check_method_child_audit(data,expected,MethodReadingCaptureChecks.source_positions)
        self.assertEqual(data['childReadability']['proofs'][0]['state']['tree']['top'],0,'already-visible child can have genuine0→0 keyboard geometry')
        data['expanded']['g'].remove(expected['position']['id']);data['rows']=data['rows'][:-1]
        audit=attach_method_child_fixture(data,expected)
        self.assertEqual(audit['required'],[]);self.assertEqual(audit['proofs'],[])
        MODULE.check_method_reading(data,expected,MethodReadingCaptureChecks.source_positions)
        data.pop('childReadability')
        with self.assertRaises(RuntimeError):MODULE.check_method_reading(data,expected,MethodReadingCaptureChecks.source_positions)

    def test_stable_focus_only_difference_is_preserved_but_other_model_drift_is_not_accepted(self):
        import copy
        data,expected=self.fixture();before=data['childReadability']['before'];key=before['contextKey'];hk=before['historyKey']
        before['history'][hk]['contexts'][key]['focusTarget']=expected['chain'][0]
        self.assertEqual(MODULE.method_child_baseline_mode(before),'stable-keyboard-focus-only')
        bad=copy.deepcopy(before);bad['history'][hk]['contexts'][key]['treeScrollByTree']['g']=12
        with self.assertRaises(RuntimeError):MODULE.method_child_baseline_mode(bad)
        bad=copy.deepcopy(before);bad['active']['position']='external'
        with self.assertRaises(RuntimeError):MODULE.method_child_baseline_mode(bad)

    def test_only_13_original_method_scenes_share_gateway_and_all_106_pngs_remain(self):
        import ast,inspect
        wanted={'-03-method-reader','-03b-reader-visible','-11-active-method-reader','-11c-reader-reopened','-23-poni-method','-24-poni-claim',
                '-27-imagenav-zhu','-27-imagenav-sptm','-27-imagenav-ving','-28-portable-rl','-28-portable-llm','-30-analysis-imported-entry','-30-analysis-not-imported'}
        self.assertEqual(set(MODULE.METHOD_CHILD_SCENES),wanted);self.assertEqual(len(MODULE.METHOD_CHILD_SCENES),13)
        self.assertTrue(wanted<=set(MODULE.SCENE_NAMES));self.assertEqual(len(MODULE.SCENE_NAMES)*len(MODULE.VIEWPORTS),106)
        tree=ast.parse(inspect.getsource(MODULE.main));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='method_child_readability_checks']
        self.assertEqual(len(calls),1)
        source=inspect.getsource(MODULE.main)
        self.assertIn("if data['desktopShell'].get('methodReading') == 'true' and not data['desktopShell']['collapsed']:",source)
        self.assertIn("compact=name.endswith(('-03-method-reader', '-03b-reader-visible', '-11-active-method-reader', '-11c-reader-reopened'))",source)
        self.assertIn('check_method_child_audit(data, expected, source_positions)',inspect.getsource(MODULE.check_method_reading))

    def test_observer_scripts_are_syntactically_valid_and_never_set_focus_scroll_or_state(self):
        js=[getattr(MODULE,n) for n in dir(MODULE) if n.startswith('METHOD_CHILD_') and n.endswith('_JS')]
        self.assertEqual({n for n in dir(MODULE) if n.startswith('METHOD_CHILD_') and n.endswith('_JS')},
                         {'METHOD_CHILD_PROBE_START_JS','METHOD_CHILD_STATE_JS','METHOD_CHILD_ACTION_JS','METHOD_CHILD_IDLE_JS','METHOD_CHILD_READER_POINT_JS','METHOD_CHILD_HOVER_POINT_JS','METHOD_CHILD_PROBE_STOP_JS'})
        for script in js:
            for operation in ('.focus(','.scrollIntoView(','.scrollTo(','.navigate(','.replaceState(','.pushState(','.scrollTop=', '.scrollLeft=', '.tabIndex='):
                self.assertNotIn(operation,script)
        result=subprocess.run(['node','-e',"for(const s of JSON.parse(require('fs').readFileSync(0,'utf8')))new Function(s);"],input=json.dumps(js),text=True,capture_output=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_reader_pointer_requires_exact_self_hit_integer_client_padding_and_not_overlay(self):
        code=r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case;
const reader={id:'np-detail-scroll',isConnected:true,tabIndex:-1,clientLeft:1,clientTop:1,clientWidth:970,clientHeight:430,getBoundingClientRect:()=>({x:433.25,y:446.6875,width:992,height:436.3125})};
global.window=global;window.__npMethodChildProbe={active:c.wrong?{}:reader};global.innerWidth=1440;global.innerHeight=900;
const probes=[];global.document={getElementById:()=>reader,elementFromPoint:(x,y)=>{probes.push([x,y]);return c.overlay?{}:c.descendant?{parentElement:reader}:reader;}};
let value,error;try{value=new Function(input.script)();}catch(e){error=String(e);}process.stdout.write(JSON.stringify({value,error,probes}));
"""
        def probe(**case):
            result=subprocess.run(['node','-e',code],input=json.dumps(dict(case=case,script=MODULE.METHOD_CHILD_READER_POINT_JS)),text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)
        good=probe();p=good['value']['point'];self.assertIsInstance(p['x'],int);self.assertIsInstance(p['y'],int)
        self.assertGreater(p['x'],434.25);self.assertLess(p['x'],444.25);self.assertLess(p['x'],1404.25)
        self.assertEqual(good['value']['candidateCount'],9)
        for case in ('overlay','descendant'):
            self.assertIsNone(probe(**{case:True})['value']['point'])
        self.assertIn('original reader',probe(wrong=True)['error'])


# Native-input transport/state-machine regressions. This is a deterministic fake
# WebDriver, NOT Chrome, trusted-browser-event evidence, layout or paint proof.
class _MethodChildNativeDriver:
    """Interpret requested native actions; JS calls may only inspect/observe.

    The model implements the product's important independent state channels:
    DOM object focus, roving tabindex, runtime focus, persisted history/taskView,
    independent pane offsets, hover and a 120 ms debounced scroll save.
    """
    def __init__(self, fixture, expected, positions, *, original='tree', divergent=False,
                 child_visible=False, reader_top=0, tree_top=0, tab_scroll=False, fault=None):
        import copy
        self.copy = copy.deepcopy
        self.base = copy.deepcopy(fixture)
        self.base.pop('captureName', None); self.base.pop('childReadability', None)
        self.expected, self.positions, self.fault = expected, positions, fault
        self.route = dict(nav='1', bench=None, protocol=None, claim=None, mode='tree', template=None,
                          **self.base['route'])
        self.base['route'] = copy.deepcopy(self.route)
        self.tree_name = self.route['tree']; self.selected = self.route['node']
        self.path = MODULE.method_visible_source_ids(expected, positions, self.base['expanded'][self.tree_name])
        self.root, self.child = self.path[0], expected['children'][0]
        self.child_visible, self.tab_scroll = child_visible, tab_scroll
        self.tree = dict(top=tree_top, left=0, maxTop=300, maxLeft=0,
                         client=dict(x=17, y=382.391, width=398, height=456))
        self.reader = dict(top=reader_top, left=0, maxTop=800, maxLeft=0,
                           client=dict(x=433, y=261, width=990, height=622))
        self.initial_reader_top = reader_top
        self.base['tree'] = copy.deepcopy(self.tree['client'])
        self.nodes = {pid: dict(id='np-node-'+pid, tag='LI', position=pid, tabIndex=-1) for pid in self.path}
        self.nodes[self.selected]['tabIndex'] = 0
        self.reader_node = dict(id='np-detail-scroll', tag='DIV', position=None, tabIndex=-1)
        self.tree_node = dict(id='np-tree-scroll', tag='DIV', position=None, tabIndex=0)
        self.header_button = dict(id='np-reader-heading-button', tag='BUTTON', position=None, tabIndex=0)
        self.content_button = dict(id='np-reader-content-button', tag='BUTTON', position=None, tabIndex=0)
        self.toggle_button = dict(id='np-reader-toggle', tag='BUTTON', position=None, tabIndex=0)
        self.active = self.reader_node if original == 'reader' else self.content_button if original == 'reader-control' else self.nodes[self.selected]
        self.original_active = self.active
        self.roving = self.selected
        self.original_focus = {k: self.active[k] for k in ('id', 'tag', 'tabIndex')}
        self.dom_refs = [object() for _ in range(4 + len(self.path))]
        self.original_dom_refs = self.dom_refs.copy()
        self.original_hover = object(); self.hover = self.original_hover
        self.pointer = None; self.shift = False
        self.history_key = 'navigationProduct'; self.context_key = 'exact-method-context'; self.neutral_key = 'task-neutral-context'
        initial_focus = self.active['position'] or self.active['id']
        bucket = dict(expandedByTree=copy.deepcopy(self.base['expanded']), selectedByTree={self.tree_name:self.selected},
                      treeScrollByTree={self.tree_name:tree_top}, treeScrollLeftByTree={self.tree_name:0},
                      detailScrollByTree={self.tree_name:reader_top}, windowScroll=0, focusTarget=initial_focus,
                      graphScale=1, untouched=dict(nested=['preserve', 17]))
        self.runtime = dict(schemaVersion='navigation-ui/1', modelRevision='fixture-source-revision',
                            route=copy.deepcopy(self.route), revision=7,
                            originTrail=[dict(route=dict(node='existing-origin'), bucket=dict(focusTarget='original-origin-focus'))],
                            contexts={self.context_key:bucket, 'other-context':dict(untouched=['keep', 23])})
        if self.tree_name in ('l','c'):
            self.runtime['contexts'][self.neutral_key] = dict(taskView=dict(schema=1,
                lastRouteByTree={self.tree_name:copy.deepcopy(self.route)}, focusTargetByTree={self.tree_name:initial_focus}))
        self.history = {self.history_key:copy.deepcopy(self.runtime), 'externalOwner':dict(nested=['do not replace', 42])}
        if divergent:
            if original != 'tree': raise AssertionError('Supported divergent fixture starts at its roving treeitem')
            self.history[self.history_key]['contexts'][self.context_key]['focusTarget'] = self.root
            if self.tree_name in ('l','c'):
                for s in (self.runtime,self.history[self.history_key]):
                    s['contexts'][self.neutral_key]['taskView']['focusTargetByTree'][self.tree_name] = self.root
        self.now = 0; self.pending_save = None; self.probe = False; self.trace = None
        self.events = []; self.overflow = 0; self.calls = []; self.keys = []
        self.cleanup_calls = 0; self.trace_cleanup_calls = 0; self.save_count = 0; self.saved_focuses = []
        self.child_seen = False; self.return_home_count = 0; self.no_scroll_stage = False
        self.wheel_count = 0; self.fault_triggered = False
        self.initial_state = self.snapshot_state()
        self.initial_snapshot = self.snapshot_reading()

    def _event(self, kind, *, key=None, target=None, trusted=True):
        if not self.probe: return
        target = target or self.active
        row = dict(type=kind, key=key, trusted=trusted, target=target['id'],
                   originalTarget=target is self.original_active, readerTarget=target is self.reader_node)
        if len(self.events) < 24: self.events.append(row)
        else: self.overflow = min(25, self.overflow + 1)

    def _focus(self, node):
        if self.active is not node:
            self.active = node; self._event('focusin', target=node)

    def _scroll(self, region, *, top=None, left=None):
        area = self.tree if region == 'tree' else self.reader
        old = (area['top'],area['left'])
        if top is not None: area['top'] = max(0,min(area['maxTop'],top))
        if left is not None: area['left'] = max(0,min(area['maxLeft'],left))
        if old != (area['top'],area['left']):
            self._event('scroll',target=self.tree_node if region=='tree' else self.reader_node)
            self.pending_save = self.now + 120

    def _save_current(self):
        # Production capture clones runtime and reads DOM focus, never roving alone.
        self.runtime = self.copy(self.runtime)
        bucket = self.runtime['contexts'][self.context_key]
        bucket.update(focusTarget=self.active['position'] or self.active['id'], windowScroll=0)
        bucket['treeScrollByTree'][self.tree_name] = self.tree['top']
        bucket['treeScrollLeftByTree'][self.tree_name] = self.tree['left']
        bucket['detailScrollByTree'][self.tree_name] = self.reader['top']
        if self.tree_name in ('l','c'):
            task = self.runtime['contexts'][self.neutral_key]['taskView']
            task['lastRouteByTree'][self.tree_name] = self.copy(self.route)
            task['focusTargetByTree'][self.tree_name] = bucket['focusTarget']
        self.history[self.history_key] = self.copy(self.runtime)
        self.pending_save = None; self.save_count += 1; self.saved_focuses.append(bucket['focusTarget'])

    def _idle(self):
        self.now += 200
        if self.pending_save is not None and self.pending_save <= self.now: self._save_current()
        return dict(ok=True, elapsed=200, quietMs=160)

    def _row_rect(self, pid):
        if pid == self.child:
            y = 690 if self.child_visible else 855.891
            height = 127.5
        else:
            y = self.tree['client']['y'] + 12 + self.path.index(pid)*58
            height = 49
        return dict(x=25,y=y-self.tree['top'],width=375,height=height)

    def _native_nearest(self, pid):
        import math
        row = self._row_rect(pid); client = self.tree['client']
        top = self.tree['top']
        top_edge=client['y']+(12 if pid==self.root else 0)
        if row['y'] < top_edge: top -= math.ceil(round(top_edge-row['y'],6))
        elif row['y']+row['height'] > client['y']+client['height']:
            top += math.ceil(round(row['y']+row['height']-client['y']-client['height'],6))
        self._scroll('tree',top=top)

    def _trace_frame(self):
        if not self.trace: raise AssertionError('No active keyboard trace')
        def row(pid):
            return dict(id='np-node-'+pid,position=pid,rect=self._row_rect(pid),itemMarginTop=0,rowScrollMarginBlockStart='auto')
        return dict(route=self.copy(self.route),methodReading='true',window=dict(x=0,y=0),active=self.active['id'],
                    tree=dict(id='np-tree-scroll',connected=True,top=self.tree['top'],left=self.tree['left'],
                              scrollHeight=756,scrollWidth=398,rect=self.copy(self.tree['client']),clientRect=self.copy(self.tree['client']),
                              paddingTop=0,scrollPaddingBlockStart='auto'),
                    root=row(self.trace['root']),target=row(self.trace['target']))

    def _key(self, value):
        key = {'\ue011':'Home','\ue015':'ArrowDown','\ue004':'Tab','\ue008':'Shift'}.get(value,value)
        if key=='Shift': self.shift=True; return
        trusted = not (self.fault=='untrusted-child' and key=='ArrowDown' and self.active['position']==self.path[self.path.index(self.child)-1])
        self._event('keydown',key=key,trusted=trusted)
        self.keys.append((key,self.active['id']))
        if key=='Tab':
            ring = [self.tree_node,self.nodes[self.roving],self.header_button,self.content_button,self.toggle_button]
            # tabindex=-1 reader is outside the sequential ring; its DOM position
            # is between fixed header controls and reader content controls.
            if self.active is self.reader_node: target = self.header_button if self.shift else self.content_button
            else:
                index=next((i for i,n in enumerate(ring) if n is self.active),1)
                target=ring[(index+(-1 if self.shift else 1))%len(ring)]
            self._focus(target)
            if self.tab_scroll and target is self.header_button: self._scroll('reader',top=0)
            return
        if key not in ('Home','ArrowDown'): raise AssertionError('Unsupported native key '+key)
        if self.active['position'] is None: return
        source=self.active['id']; at=self.path.index(self.active['position'])
        # Detect the persistence-preserving phase from actual restored history,
        # not from an incidental count of Home requests.
        if (self.child_seen and self.history==self.initial_state['history'] and self.pending_save is None and
                self.active['position']==self.initial_state['history'][self.history_key]['contexts'][self.context_key]['focusTarget']):
            self.no_scroll_stage=True
        target=self.root if key=='Home' else self.path[min(len(self.path)-1,at+1)]
        if self.fault=='action-error' and target==self.child:
            self.fault_triggered=True; raise RuntimeError('injected native action transport failure')
        if self.trace:
            self.trace['events'].append(dict(phase='capture',key=key,code=key,isTrusted=trusted,defaultPrevented=False,
                                              eventTarget=source,snapshot=self._trace_frame()))
        for node in self.nodes.values(): node['tabIndex']=-1
        self.nodes[target]['tabIndex']=0; self.roving=target; self._focus(self.nodes[target]); self._native_nearest(target)
        self.runtime['contexts'][self.context_key]['focusTarget']=target
        if target==self.child: self.child_seen=True
        if self.fault=='delayed-save' and self.no_scroll_stage and key=='ArrowDown' and not self.fault_triggered:
            # Fault injection: a delayed pre-existing save leaks into the
            # history-preserving phase. No DOM scroll is invented for the key.
            self.pending_save=self.now+120; self.fault_triggered=True
        if self.fault=='dom-replaced' and target==self.child: self.dom_refs[-1]=object()
        if self.trace:
            self.trace['events'].append(dict(phase='bubble',key=key,code=key,isTrusted=trusted,defaultPrevented=True,
                                              eventTarget=source,snapshot=self._trace_frame()))

    def _wheel(self, action):
        self.wheel_count += 1
        x,y=action['x'],action['y']
        region=next((name for name,area in [('tree',self.tree),('reader',self.reader)]
                     if area['client']['x']<=x<area['client']['x']+area['client']['width'] and
                     area['client']['y']<=y<area['client']['y']+area['client']['height']),None)
        if region is None: raise AssertionError('Native wheel origin misses both existing panes')
        if action['origin']!='viewport' or action['duration']!=80: raise AssertionError('Unexpected native wheel transport')
        if self.fault=='wheel-noop': self.fault_triggered=True; return
        area=self.tree if region=='tree' else self.reader
        dx,dy=action['deltaX'],action['deltaY']
        if self.fault=='wheel-inexact':
            dx=dx/2;dy=dy/2;self.fault_triggered=True
        self._scroll(region,top=area['top']+dy,left=area['left']+dx)

    def _pointer(self, action):
        kind=action['type']
        if kind=='pointerMove':
            self.pointer=(action['x'],action['y'])
            self.hover = self.original_hover if self.pointer==(100,200) else self.reader_node
        elif kind=='pointerDown':
            if self.pointer!=(435,500): raise AssertionError('Pointer down was not aimed at verified reader self-hit')
            self._event('pointerdown',target=self.reader_node)
            if self.fault!='pointer-no-focus': self._focus(self.reader_node)
            else: self.fault_triggered=True
        elif kind=='pointerUp':
            self._event('pointerup',target=self.reader_node);self._event('click',target=self.reader_node)
        else: raise AssertionError('Unexpected pointer action '+kind)

    def call(self, method, endpoint, payload):
        self.calls.append(('call',method,endpoint,self.copy(payload)))
        if method!='POST': raise AssertionError('Unexpected non-POST transport')
        if endpoint=='/execute/async':
            if payload!={'script':MODULE.METHOD_CHILD_IDLE_JS,'args':[]}: raise AssertionError('Non-observational asynchronous JavaScript')
            return self._idle()
        if endpoint!='/actions': raise AssertionError('Only native actions and read-only idle may run')
        for source in payload['actions']:
            for action in source['actions']:
                if source['type']=='key':
                    if action['type']=='keyDown': self._key(action['value'])
                    elif action['type']=='keyUp':
                        if action['value']=='\ue008': self.shift=False
                    else: raise AssertionError('Unexpected key action')
                elif source['type']=='wheel': self._wheel(action)
                elif source['type']=='pointer': self._pointer(action)
                else: raise AssertionError('Unexpected action source')
        return None

    def snapshot_state(self):
        active={**self.active,'original':self.active is self.original_active}
        return dict(route=self.copy(self.route),runtime=self.copy(self.runtime),history=self.copy(self.history),
                    historyKey=self.history_key,contextKey=self.context_key,historyLength=15,
                    viewport=dict(self.base['viewport'],dpr=1),window=dict(x=0,y=0),tree=self.copy(self.tree),reader=self.copy(self.reader),
                    active=active,roving=[self.roving],hoverSame=self.hover is self.original_hover,
                    domSame=len(self.dom_refs)==len(self.original_dom_refs) and all(a is b for a,b in zip(self.dom_refs,self.original_dom_refs)),
                    originalFocus=self.copy(self.original_focus),tabBound=8,
                    scopeCandidates=method_candidate_scope_fixture(self.path,self.roving,{pid:self.nodes[pid]['tabIndex'] for pid in self.path}))

    def snapshot_reading(self):
        snapshot=self.copy(self.base)
        for row in snapshot['rows']:
            pid=row['id'];row['tabIndex']=self.nodes[pid]['tabIndex']
            if pid==self.child:
                label_y=694 if self.child_visible else 859.891
                role_y=792 if self.child_visible else 957.891
                label_height=93;role_height=21
            else:
                label_y=self.tree['client']['y']+8+self.path.index(pid)*58
                role_y=label_y+29;label_height=28;role_height=20
            row['proof']=MethodReadingCaptureChecks.proof(row['label'],30,label_y-self.tree['top'],360,label_height)
            row['roleProof']=MethodReadingCaptureChecks.proof(row['role'],30,role_y-self.tree['top'],360,role_height)
            for field in ('proof','roleProof'):
                proof=row[field]
                visible=MODULE.rect_inside(proof['rect'],self.tree['client'],0)
                proof['visible']=visible;proof['clipped']=not visible
                proof['readerContent']=self.copy(self.tree['client'])
                proof['clipAreas']=[self.copy(self.tree['client'])]
                for fragment in proof['fragments']:fragment['visible']=visible
                for run in proof['textRuns']:
                    run['clipAreas']=[self.copy(self.tree['client'])]
                    for fragment in run['fragments']:fragment['visible']=visible
        # Reflect reader movement in source/geometry snapshots, so failing to
        # restore reader160 cannot pass only because source strings are stable.
        delta=self.initial_reader_top-self.reader['top']
        snapshot['mechanism']['rect']['y']+=delta
        for field in snapshot['mechanism']['fields']:
            field['proof']['rect']['y']+=delta
        return snapshot

    def js(self, script, *args):
        self.calls.append(('js',script,self.copy(args)))
        if script==MODULE.METHOD_CHILD_PROBE_START_JS:
            if self.probe: raise AssertionError('Probe installed twice')
            self.probe=True;return True
        if script==MODULE.METHOD_CHILD_STATE_JS:
            if not self.probe: raise AssertionError('State measurement requires its observation probe')
            return self.snapshot_state()
        if script==MODULE.METHOD_READING_SNAPSHOT_JS:return self.snapshot_reading()
        if script==MODULE.METHOD_CHILD_ACTION_JS:
            if args==('baseline',):
                self.original_active=self.active;self.original_hover=self.hover
                self.original_focus={k:self.active[k] for k in ('id','tag','tabIndex')}
                return True
            if args==('candidates',):return method_candidate_inventory_fixture(self.snapshot_state())
            if args==('reset',):self.events=[];self.overflow=0;return True
            if args==('read',):return dict(events=self.copy(self.events),overflow=self.overflow)
            raise AssertionError('Unexpected event-recorder command')
        if script==MODULE.METHOD_CHILD_READER_POINT_JS:
            if self.original_active is not self.reader_node: raise AssertionError('Reader pointer special-case used for another original focus')
            return dict(id='np-detail-scroll',client=self.copy(self.reader['client']),
                        point=None if self.fault=='pointer-missing' else dict(x=435,y=500),candidateCount=0 if self.fault=='pointer-missing' else 1)
        if script==MODULE.METHOD_CHILD_HOVER_POINT_JS:
            return dict(point=dict(x=100,y=200),id='original-hover-target',tag='BUTTON')
        if script==MODULE.METHOD_KEY_TRACE_START_JS:
            if self.trace is not None: raise AssertionError('Keyboard trace leaked from preceding action')
            source,root,target,key=args
            self.trace=dict(scope='method-tree-key',source=source,root=root,target=target,key=key,eventLimit=2,
                            events=[],overflow=0,after=None,cleanedUp=False)
            self.trace['before']=self._trace_frame();return self.copy(self.trace)
        if script==MODULE.METHOD_KEY_TRACE_STOP_JS:
            if self.trace is None: raise AssertionError('No keyboard trace to clean up')
            self.trace['after']=self._trace_frame();self.trace['cleanedUp']=True
            result=self.copy(self.trace);self.trace=None;self.trace_cleanup_calls+=1;return result
        if script==MODULE.METHOD_CHILD_PROBE_STOP_JS:
            self.cleanup_calls+=1;self.probe=False
            if self.fault=='cleanup-error': self.fault_triggered=True;raise RuntimeError('injected probe cleanup transport failure')
            return dict(cleanedUp=True)
        raise AssertionError('Unapproved JavaScript execution: helper must not focus, scroll, rewrite model/history or rebuild DOM')


class MethodChildNativeOrchestrationChecks(unittest.TestCase):
    """State-machine transport checks; actual Chrome remains the acceptance gate."""
    @classmethod
    def setUpClass(cls):
        MethodReadingCaptureChecks.setUpClass()

    def make(self, case='global', **options):
        fixture=MethodReadingCaptureChecks()
        data,expected=fixture.receipt(case)
        driver=_MethodChildNativeDriver(data,expected,fixture.source_positions,**options)
        data=driver.snapshot_reading()
        report={};saves=[]
        suffix='-11c-reader-reopened' if options.get('original')=='reader' else '-03-method-reader' if case=='global' else '-11-active-method-reader'
        name='1440x900'+suffix
        return driver,data,expected,fixture.source_positions,report,lambda:saves.append(len(driver.calls)),name,saves

    def run_helper(self, values):
        driver,data,expected,positions,report,save,name,_=values
        return MODULE.method_child_readability_checks(driver,report,save,name,data,expected,positions)

    def assert_exact_return(self, values, record):
        driver,data,expected,positions,report,save,name,saves=values
        self.assertEqual(record['status'],'verified_native_children')
        self.assertTrue(record['cleanedUp']);self.assertFalse(driver.probe);self.assertIsNone(driver.trace)
        self.assertEqual(driver.cleanup_calls,1);self.assertGreater(len(saves),0)
        self.assertEqual(driver.snapshot_state(),driver.initial_state)
        self.assertEqual(driver.snapshot_reading(),driver.initial_snapshot)
        self.assertIs(driver.active,driver.original_active)
        self.assertTrue(all(a is b for a,b in zip(driver.dom_refs,driver.original_dom_refs)))
        self.assertEqual(record['before'],record['after'])
        self.assertEqual(record['afterSnapshot'],driver.initial_snapshot)
        MODULE.check_method_child_audit(data,expected,positions)
        action_calls=[call for call in driver.calls if call[:3]==('call','POST','/actions')]
        self.assertGreater(len(action_calls),0)
        self.assertEqual(driver.history['externalOwner'],{'nested':['do not replace',42]})
        self.assertEqual(driver.runtime['contexts']['other-context'],{'untouched':['keep',23]})

    def test_coherent_global_child_full_label_and_role_require_actual_145_scroll(self):
        values=self.make();driver=values[0]
        before=next(r for r in driver.initial_snapshot['rows'] if r['id']==driver.child)
        self.assertEqual(before['proof']['rect']['y'],859.891)
        self.assertEqual(before['roleProof']['rect']['y']+before['roleProof']['rect']['height'],978.891)
        self.assertFalse(before['proof']['visible']);self.assertFalse(before['roleProof']['visible'])
        record=self.run_helper(values);self.assert_exact_return(values,record)
        proof=record['proofs'][0]
        self.assertEqual(proof['state']['tree']['top'],145)
        self.assertEqual(proof['keyTrace']['before']['tree']['top'],0)
        self.assertEqual(proof['keyTrace']['after']['tree']['top'],145)
        for field in ('proof','roleProof'):
            self.assertTrue(MODULE._reader_proof(proof['row'][field],driver.tree['client'],driver.base['viewport'],font_size=15))
        self.assertEqual(record['baselineMode'],'coherent')
        self.assertGreater(driver.wheel_count,0,'coherent original selected focus must be naturally persisted after Home saves root')

    def test_stable_original_history_root_runtime_method_survives_without_final_save(self):
        for case in ('global','local'):
            with self.subTest(case=case):
                values=self.make(case,divergent=True);driver=values[0]
                record=self.run_helper(values);self.assert_exact_return(values,record)
                self.assertEqual(record['baselineMode'],'stable-keyboard-focus-only')
                key=driver.context_key;hkey=driver.history_key
                self.assertEqual(driver.runtime['contexts'][key]['focusTarget'],driver.selected)
                self.assertEqual(driver.history[hkey]['contexts'][key]['focusTarget'],driver.root)
                self.assertEqual(record['persistedReturn']['runtime'],driver.initial_state['history'][hkey])
                self.assertEqual(driver.saved_focuses[-1],driver.root,'last native save must persist original history, never the runtime-only final focus')
                self.assertTrue(all(a['kind']=='tree-key' for a in record['actions'][-len(driver.expected['chain']):]),'history reconstruction must finish with only non-scrolling keys')
                if case=='local':
                    self.assertEqual(driver.runtime['contexts'][driver.neutral_key]['taskView']['focusTargetByTree']['l'],driver.root)

    def test_nonzero_original_tree_offset_and_reader_scroll_survive_focus_only_history_return(self):
        values=self.make(divergent=True,tree_top=4,reader_top=160);driver=values[0]
        record=self.run_helper(values);self.assert_exact_return(values,record)
        self.assertEqual(record['before']['tree']['top'],4);self.assertEqual(record['after']['tree']['top'],4)
        self.assertEqual(record['after']['reader']['top'],160)
        persisted=record['persistedReturn'];self.assertEqual(persisted['tree']['top'],4)
        # A needless Home here would move12px-padded root back to0 and fail.
        last_home=max(i for i,k in enumerate(record['keys']) if k['input']=='\ue011')
        self.assertTrue(all(k['input']=='\ue015' for k in record['keys'][last_home+1:]))

    def test_reader_reopened_minus_one_focus_reader160_and_tab_scroll_are_restored(self):
        values=self.make('local',original='reader',reader_top=160,tab_scroll=True);driver=values[0]
        record=self.run_helper(values);self.assert_exact_return(values,record)
        self.assertEqual(record['before']['originalFocus'],dict(id='np-detail-scroll',tag='DIV',tabIndex=-1))
        self.assertEqual(record['after']['reader']['top'],160)
        self.assertTrue(any(a['kind']=='reverse-tab' and a['after']['reader']['top']==0 for a in record['actions']))
        pointer=next(a for a in record['actions'] if a['kind']=='pointer-return-reader')
        self.assertEqual(pointer['after']['active']['id'],'np-detail-scroll')
        self.assertTrue(pointer['after']['active']['original'])
        for kind in ('pointerdown','pointerup','click','focusin'):
            self.assertTrue(any(e['type']==kind and e['readerTarget'] and e['trusted'] for e in pointer['events']['events']))
        self.assertTrue(any(a['kind']=='restore-original-hover' for a in record['actions']))
        self.assertTrue(any(a['kind']=='wheel-reader' for a in record['actions']))

    def test_reader_focus_alone_requires_effective_one_pixel_persistence_roundtrip(self):
        values=self.make('local',original='reader',reader_top=160,child_visible=True)
        driver=values[0];record=self.run_helper(values);self.assert_exact_return(values,record)
        pointer=next(a for a in record['actions'] if a['kind']=='pointer-return-reader')
        key=driver.context_key;hkey=driver.history_key
        self.assertEqual(pointer['after']['active']['id'],'np-detail-scroll')
        self.assertEqual(pointer['after']['runtime']['contexts'][key]['focusTarget'],driver.selected)
        self.assertEqual(pointer['after']['history'][hkey]['contexts'][key]['focusTarget'],'np-detail-scroll')
        wheels=[a for a in record['actions'] if a['kind']=='wheel-reader']
        self.assertEqual([(a['before']['reader']['top'],a['after']['reader']['top']) for a in wheels],[(160,161),(161,160)])
        self.assertEqual(driver.saved_focuses,['np-detail-scroll','np-detail-scroll'])

    def test_execution_transport_never_requests_javascript_focus_scroll_or_model_writes(self):
        import re
        values=self.make('local',original='reader',reader_top=160,tab_scroll=True)
        record=self.run_helper(values);self.assert_exact_return(values,record)
        for call in values[0].calls:
            if call[0]=='js':
                script=call[1]
            elif call[:3]==('call','POST','/execute/async'):
                script=call[3]['script']
            else:
                self.assertEqual(call[:3],('call','POST','/actions'))
                continue
            self.assertNotRegex(script,r'\.(?:focus|scrollIntoView|scrollTo|navigate|replaceState|pushState)\s*\(')
            self.assertNotRegex(script,r'\.(?:scrollTop|scrollLeft|tabIndex|focusTarget)\s*=(?!=)')
            self.assertNotRegex(script,r'history\.state\s*=(?!=)')

    def test_tab_reachable_reader_control_returns_without_activating_it(self):
        values=self.make('local',original='reader-control',reader_top=160,tab_scroll=True)
        record=self.run_helper(values);self.assert_exact_return(values,record)
        self.assertTrue(any(a['kind']=='tab' for a in record['actions']))
        self.assertFalse(any(a['kind']=='pointer-return-reader' for a in record['actions']))
        self.assertFalse(any(e['type']=='click' for a in record['actions'] for e in a['events']['events']))

    def test_already_visible_child_zero_scroll_still_requires_trusted_key_proof(self):
        values=self.make(child_visible=True);driver=values[0]
        record=self.run_helper(values);self.assert_exact_return(values,record)
        proof=record['proofs'][0]
        self.assertEqual(proof['keyTrace']['before']['tree']['top'],0)
        self.assertEqual(proof['keyTrace']['after']['tree']['top'],0)
        self.assertEqual([e['phase'] for e in proof['keyTrace']['events']],['capture','bubble'])
        self.assertTrue(all(e['isTrusted'] for e in proof['keyTrace']['events']))
        self.assertEqual(driver.wheel_count,0,'zero-scroll child proof does not invent a wheel requirement')

    def test_missing_self_hit_or_pointer_without_focus_fails_and_cleans_up(self):
        for fault,pattern in [('pointer-missing','safe self-hit'),('pointer-no-focus','exact-target focus')]:
            with self.subTest(fault=fault):
                values=self.make('local',original='reader',reader_top=160,tab_scroll=True,fault=fault)
                with self.assertRaisesRegex(RuntimeError,pattern): self.run_helper(values)
                self.assert_failure_cleanup(values)

    def test_ineffective_or_inexact_native_wheel_cannot_pass_restoration(self):
        for fault,pattern in [('wheel-noop','no effective progress'),('wheel-inexact','integer native wheel')]:
            with self.subTest(fault=fault):
                values=self.make(fault=fault)
                with self.assertRaisesRegex(RuntimeError,pattern): self.run_helper(values)
                self.assertTrue(values[0].fault_triggered);self.assert_failure_cleanup(values)

    def test_delayed_save_in_no_scroll_history_return_is_rejected(self):
        values=self.make(divergent=True,fault='delayed-save')
        with self.assertRaisesRegex(RuntimeError,'forbidden persistence or scroll change'): self.run_helper(values)
        self.assertTrue(values[0].fault_triggered);self.assert_failure_cleanup(values)
        self.assertNotEqual(values[0].history,values[0].initial_state['history'])

    def test_untrusted_already_visible_child_is_rejected(self):
        values=self.make(child_visible=True,fault='untrusted-child')
        with self.assertRaisesRegex(RuntimeError,'trusted'): self.run_helper(values)
        self.assert_failure_cleanup(values)

    def test_transport_action_failure_always_cleans_up_both_observers(self):
        values=self.make(fault='action-error')
        with self.assertRaisesRegex(RuntimeError,'native action transport failure'): self.run_helper(values)
        self.assertTrue(values[0].fault_triggered);self.assert_failure_cleanup(values)
        self.assertGreater(values[0].trace_cleanup_calls,0)

    def test_original_dom_replacement_fails_even_with_same_node_labels(self):
        values=self.make(fault='dom-replaced')
        with self.assertRaisesRegex(RuntimeError,'original DOM'): self.run_helper(values)
        self.assert_failure_cleanup(values)

    def test_cleanup_failure_never_attaches_a_successful_audit(self):
        values=self.make(fault='cleanup-error')
        with self.assertRaisesRegex(RuntimeError,'cleanup transport failure'): self.run_helper(values)
        driver,data,_,_,report,_,_,_=values
        self.assertEqual(driver.cleanup_calls,1);self.assertFalse(driver.probe);self.assertIsNone(driver.trace)
        self.assertNotIn('childReadability',data)
        self.assertNotEqual(report['methodChildReadabilityChecks'][0].get('cleanedUp'),True)

    def assert_failure_cleanup(self, values):
        driver,data,_,_,report,_,_,_=values
        self.assertFalse(driver.probe);self.assertIsNone(driver.trace);self.assertEqual(driver.cleanup_calls,1)
        self.assertTrue(report['methodChildReadabilityChecks'][0]['cleanedUp'])
        self.assertNotEqual(report['methodChildReadabilityChecks'][0]['status'],'verified_native_children')
        self.assertNotIn('childReadability',data)


class MethodChildObserverContractChecks(unittest.TestCase):
    def probe_dom(self, replacement=None, events=0, roving=False, rebind=False):
        code=r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),{JSDOM}=require('jsdom');
const dom=new JSDOM('<main id="navigation-product" data-method-reading="true"><section id="np-workspace"><div id="np-reader-object-title">method</div><div id="np-tree-scroll"><ul id="np-tree"><li id="np-node-method" role="treeitem" tabindex="0" data-position="method"><div class="np-node-row"><button class="np-node-label">method</button><span class="np-node-kind">具体方法</span></div></li><li id="np-node-child" role="treeitem" tabindex="-1" data-position="child"><div class="np-node-row"><button class="np-node-label">full scientific child</button><span class="np-node-kind">技术改进</span></div></li></ul></div><div id="np-detail-scroll" tabindex="-1"><section data-mechanism-entity="method">full original mechanism</section></div></section></main>',{runScripts:'outside-only'}),w=dom.window,d=w.document;
const s={route:{tree:'g',node:'method'},contexts:{k:{focusTarget:'method',expandedByTree:{g:['method']},selectedByTree:{g:'method'}}}},h={nav:s};
w.NavigationProductApp={getState:()=>JSON.parse(JSON.stringify(s))};w.NavigationProductModel={KEY:'nav',contextKey:()=> 'k'};w.history.replaceState(h,'');
for(const n of d.querySelectorAll('*')){n.getBoundingClientRect=()=>({x:17,y:382,width:398,height:456});for(const [k,v] of Object.entries({clientWidth:398,clientHeight:456,scrollWidth:398,scrollHeight:601}))Object.defineProperty(n,k,{value:v,configurable:true});}
const observed=new Set();const add=d.addEventListener.bind(d),remove=d.removeEventListener.bind(d);d.addEventListener=(t,f,c)=>{if(['keydown','pointerdown','pointerup','click','focusin','scroll'].includes(t))observed.add(f);return add(t,f,c);};d.removeEventListener=(t,f,c)=>{observed.delete(f);return remove(t,f,c);};
const method=d.getElementById('np-node-method'),child=d.getElementById('np-node-child');
if(input.roving&&!input.rebind)method.focus();
new w.Function(input.start)();
if(input.rebind)method.focus();
new w.Function(input.action)('baseline');const before=new w.Function(input.state)();
if(input.roving){method.tabIndex=-1;child.tabIndex=0;child.focus();s.contexts.k.focusTarget='child';}

if(input.replacement){const selectors={row:'[data-position="method"]>.np-node-row',label:'[data-position="child"] .np-node-label',role:'[data-position="child"] .np-node-kind',mechanism:'[data-mechanism-entity]'};const n=d.querySelector(selectors[input.replacement]);n.replaceWith(n.cloneNode(true));}
for(let i=0;i<input.events;i++)d.getElementById('np-tree-scroll').dispatchEvent(new w.Event('scroll',{bubbles:true}));
const after=new w.Function(input.state)();if(input.rebind)method.focus();const events=new w.Function(input.action)('read'),refs=w.__npMethodChildProbe.refs.length;const stop=new w.Function(input.stop)();
process.stdout.write(JSON.stringify({before,after,events,refs,stop,listeners:observed.size,installed:!!w.__npMethodChildProbe}));dom.window.close();
"""
        result=subprocess.run(['node','-e',code],input=json.dumps(dict(start=MODULE.METHOD_CHILD_PROBE_START_JS,state=MODULE.METHOD_CHILD_STATE_JS,
                              action=MODULE.METHOD_CHILD_ACTION_JS,stop=MODULE.METHOD_CHILD_PROBE_STOP_JS,replacement=replacement,events=events,roving=roving,rebind=rebind)),text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)

    def test_same_text_row_label_role_or_mechanism_clones_are_not_original_dom(self):
        good=self.probe_dom();self.assertTrue(good['before']['domSame']);self.assertTrue(good['after']['domSame']);self.assertEqual(good['refs'],13)
        for target in ('row','label','role','mechanism'):
            with self.subTest(target=target):
                data=self.probe_dom(target);self.assertTrue(data['before']['domSame']);self.assertFalse(data['after']['domSame'])
                self.assertEqual(data['listeners'],0);self.assertFalse(data['installed']);self.assertTrue(data['stop']['cleanedUp'])

    def test_original_focus_metadata_is_a_baseline_snapshot_while_roving_reads_real_dom(self):
        data=self.probe_dom(roving=True)
        self.assertEqual(data['before']['originalFocus'],dict(id='np-node-method',tag='LI',tabIndex=0))
        self.assertEqual(data['after']['originalFocus'],data['before']['originalFocus'])
        self.assertEqual(data['after']['active']['id'],'np-node-child');self.assertFalse(data['after']['active']['original'])
        self.assertEqual(data['after']['roving'],['child']);self.assertTrue(data['after']['domSame'])
        MODULE.check_method_child_state(data['before'],data['after'])
        with self.assertRaises(RuntimeError):MODULE.check_method_child_state(data['before'],data['after'],exact=True)

    def test_listener_rebinds_original_target_after_natural_baseline_focus_change(self):
        data=self.probe_dom(roving=True,rebind=True)
        events=[e for e in data['events']['events'] if e['type']=='focusin' and e['target']=='np-node-method']
        self.assertEqual(len(events),2);self.assertFalse(events[0]['originalTarget']);self.assertTrue(events[-1]['originalTarget'])
        self.assertEqual(data['after']['originalFocus']['tabIndex'],0)

    def test_observer_caps_events_and_preserves_untrusted_status_instead_of_fabricating_native_input(self):
        data=self.probe_dom(events=100)
        self.assertEqual(len(data['events']['events']),24);self.assertEqual(data['events']['overflow'],25)
        self.assertTrue(all(e['trusted'] is False for e in data['events']['events']))
        self.assertEqual(data['listeners'],0);self.assertFalse(data['installed'])

    def idle(self, **case):
        code=r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),c=input.case;let now=0,serial=0,queue=[],cancelled=new Set(),answer=null,calls=0,reads=0;
global.window=global;global.performance={now:()=>now};window.__npMethodChildProbe={lastScroll:0,lastFocus:0};
global.setTimeout=(fn,delay)=>{const id=++serial;queue.push({id,t:now+delay,fn});return id;};global.clearTimeout=id=>cancelled.add(id);
global.requestAnimationFrame=fn=>{if(c.hangFrames)return;++serial;queue.push({id:serial,t:now+(c.slowFrames?1100:16),fn});};
global.NavigationProductApp={getState:()=>({revision:c.churn?++reads:c.lateSave&&now>=100?1:0})};global.history={state:{value:1}};global.scrollX=0;global.scrollY=0;
global.document={activeElement:{id:'method',tagName:'LI'},getElementById:()=>({scrollTop:0,scrollLeft:0})};
new Function(input.script)(r=>{answer=r;calls++;});
for(let limit=0;queue.length&&limit<500;limit++){queue.sort((a,b)=>a.t-b.t||a.id-b.id);let e=queue.shift();if(cancelled.has(e.id))continue;now=e.t;e.fn();}
process.stdout.write(JSON.stringify({answer,calls,now,reads}));
"""
        result=subprocess.run(['node','-e',code],input=json.dumps(dict(case=case,script=MODULE.METHOD_CHILD_IDLE_JS)),text=True,capture_output=True,timeout=10)
        self.assertEqual(result.returncode,0,result.stderr);return json.loads(result.stdout)

    def test_quiet_wait_covers_late_save_and_two_frames_without_waiting_for_assertions(self):
        data=self.idle(lateSave=True);self.assertTrue(data['answer']['ok']);self.assertEqual(data['calls'],1)
        self.assertGreaterEqual(data['answer']['elapsed'],292);self.assertGreaterEqual(data['answer']['quietMs'],160);self.assertLessEqual(data['answer']['elapsed'],2000)

    def test_watchdog_rejects_churn_stalled_or_slow_frames_without_late_success(self):
        for case in ('churn','hangFrames','slowFrames'):
            with self.subTest(case=case):
                data=self.idle(**{case:True});self.assertFalse(data['answer']['ok']);self.assertEqual(data['calls'],1);self.assertEqual(data['answer']['elapsed'],2000)


class MethodChildCandidateReceiptChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        MethodReadingCaptureChecks.setUpClass()

    def fixture(self):
        import copy
        data,expected=MethodChildReadabilityChecks().fixture()
        audit=data['childReadability']
        # Match the observed 171 baseline / 175 later global search counts.
        outside=[dict(token='outside-'+str(i),id='outside-'+str(i),tag='BUTTON',sourcePosition=None,
                      tabIndex=0,disabled=False,hidden=False,layout=True,inWorkspace=False) for i in range(167)]
        snapshots=[audit['before'],audit['after'],*(a[k] for a in audit['actions'] for k in ('before','after')),*(p['state'] for p in audit['proofs'])]
        for state in snapshots:state['tabBound']=171
        inventories=[audit['tabCandidatesBefore'],audit['tabCandidatesAfter'],*(a[k] for a in audit['actions'] for k in ('tabCandidatesBefore','tabCandidatesAfter'))]
        for i,inventory in enumerate(inventories):
            additions=outside[:163] if i==0 else outside
            inventory['eligible']+=copy.deepcopy(additions)
            inventory['candidateCount']+=len(additions);inventory['eligibleCount']+=len(additions)
        self.assertEqual(audit['tabCandidatesBefore']['eligibleCount']+1,171)
        self.assertEqual(audit['actions'][0]['tabCandidatesBefore']['eligibleCount']+1,175)
        return data,expected

    def test_external_171_to_175_inventory_is_recorded_without_changing_baseline_budget(self):
        data,expected=self.fixture();audit=data['childReadability']
        MODULE.check_method_reading(data,expected,MethodReadingCaptureChecks.source_positions)
        self.assertEqual(audit['before'],audit['actions'][0]['before'])
        self.assertEqual(audit['before'],audit['after'])
        self.assertNotEqual(audit['tabCandidatesBefore'],audit['tabCandidatesAfter'])

    def test_dynamic_budget_or_actual_intervening_state_drift_remains_rejected(self):
        import copy
        data,expected=self.fixture()
        for mutation in ('budget','runtime','history','tree','reader','scope'):
            bad=copy.deepcopy(data);frame=bad['childReadability']['actions'][0]['before']
            if mutation=='budget':frame['tabBound']=175
            elif mutation=='runtime':frame['runtime']['revision']+=1
            elif mutation=='history':frame['historyLength']+=1
            elif mutation in ('tree','reader'):frame[mutation]['top']+=12
            else:frame['scopeCandidates']['items'][0]['hidden']=True
            with self.subTest(mutation=mutation),self.assertRaises(RuntimeError):
                MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_tab_wheel_and_pointer_cannot_borrow_the_traced_tree_roving_exception(self):
        import copy
        data,expected=self.fixture()
        for kind in ('tab','reverse-tab','wheel-tree','wheel-reader','pointer-move-reader','pointer-return-reader','restore-original-hover'):
            bad=copy.deepcopy(data);audit=bad['childReadability'];action=audit['actions'][0]
            action['kind']=kind
            audit['keys']=[row for row in audit['keys'] if row['actionIndex']!=0]
            with self.subTest(kind=kind),self.assertRaisesRegex(RuntimeError,'Non-tree-key method action changed'):
                MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

    def test_scope_candidates_cannot_be_omitted_or_mislabeled_as_external(self):
        import copy
        data,expected=self.fixture()
        for mutation in ('omit','external','invent-scope','count','duplicate','missing','budget','wrong-source-tree'):
            bad=copy.deepcopy(data);audit=bad['childReadability'];inventory=audit['actions'][0]['tabCandidatesBefore']
            if mutation=='omit':inventory['eligible'].pop(0);inventory['eligibleCount']-=1
            elif mutation=='external':inventory['eligible'][0]['inWorkspace']=False
            elif mutation=='invent-scope':inventory['eligible'][-1]['inWorkspace']=True
            elif mutation=='count':inventory['eligibleCount']-=1
            elif mutation=='duplicate':inventory['eligible'][-1]['token']=inventory['eligible'][0]['token']
            elif mutation=='missing':del audit['tabCandidatesAfter']
            elif mutation=='budget':audit['before']['tabBound']=256
            else:audit['before']['scopeCandidates']['treeTabIndexes'][0]['position']='forged-source'
            with self.subTest(mutation=mutation),self.assertRaises(RuntimeError):
                MODULE.check_method_child_audit(bad,expected,MethodReadingCaptureChecks.source_positions)

class MethodChildFrozenTabBudgetDOMChecks(unittest.TestCase):
    """Execute production START/STATE/ACTION/STOP against real JSDOM nodes.

    Geometry is explicitly stubbed because JSDOM has no layout. This tests actual
    selector membership, DOM references, order, properties and observer output;
    it is not native-keyboard, paint, hit-testing, or Chrome acceptance evidence.
    """
    @classmethod
    def setUpClass(cls):
        cls.cases = [
            'unchanged', 'external-four', 'external-four-clones', 'before-baseline-four', 'baseline-gap-four',
            'internal-four', 'internal-remove-four', 'internal-clone-four', 'internal-reorder-four',
            'add-hidden', 'add-negative', 'remove-hidden', 'clone-hidden', 'remove-negative', 'clone-negative',
            'disabled', 'hidden', 'display-none', 'visibility-hidden', 'ancestor-hidden', 'ancestor-display-none',
            'details-open', 'empty-details-open', 'href', 'role', 'type', 'name', 'aria-label', 'aria-controls',
            'raw-data-action', 'control-text', 'input-value', 'input-checked',
            'tab-control-negative', 'label-positive', 'reader-fake-tree-positive', 'legal-roving', 'roving-positive',
            'roving-negative-two', 'roving-two-zero', 'roving-no-zero', 'workspace-clone', 'workspace-hidden',
        ]
        code = r"""
const input=JSON.parse(require('fs').readFileSync(0,'utf8')),{JSDOM}=require('jsdom');
const clone=x=>JSON.parse(JSON.stringify(x));
const selector='a[href],button,input,select,textarea,summary,[tabindex]';
function runCase(name){
 const dom=new JSDOM(`<!doctype html><html><body>
 <main id="navigation-product" data-method-reading="true">
  <section id="np-workspace">
   <div id="np-reader-object-title">Original method title</div>
   <div id="np-tree-scroll" tabindex="0"><ul id="np-tree">
    <li id="np-node-method" role="treeitem" tabindex="0" data-position="method"><div class="np-node-row"><button id="method-label" class="np-node-label" tabindex="-1">method</button><span class="np-node-kind">具体方法</span></div></li>
    <li id="np-node-child" role="treeitem" tabindex="-1" data-position="child"><div class="np-node-row"><button id="child-label" class="np-node-label" tabindex="-1">full scientific child</button><span class="np-node-kind">技术改进</span></div></li>
   </ul></div>
   <div id="np-detail-scroll" tabindex="-1">
    <section data-mechanism-entity="method">Original scientific mechanism</section>
    <div id="ordinary-controls"><button id="scope-a" type="button">A</button><button id="scope-b" type="button">B</button><button id="scope-c" type="button">C</button><button id="scope-d" type="button">D</button></div>
    <a id="scope-link" href="/original">Original source</a>
    <input id="scope-input" name="original-name" aria-label="Original label" aria-controls="original-target">
    <select id="scope-select"><option>Original choice</option></select><textarea id="scope-textarea"></textarea>
    <button id="scope-hidden" hidden>Hidden original control</button>
    <button id="scope-negative" tabindex="-1">Non-tabstop original control</button>
    <button id="scope-disabled" disabled>Disabled original control</button>
    <div id="ancestor-wrapper"><button id="ancestor-control">Ancestor-sensitive control</button></div>
    <details id="scope-details"><summary id="scope-summary">Original closed disclosure</summary><button id="details-child">Closed disclosure child</button></details>
    <details id="empty-details"><summary id="empty-summary">Empty disclosure</summary><p>No interactive descendants</p></details>
    <button id="reader-fake-tree" role="treeitem" data-position="reader-decoy" tabindex="-1">Outside scientific tree</button>
   </div>
  </section>
 </main><footer id="external-controls"></footer></body></html>`,{runScripts:'outside-only',url:'https://example.org/navigation/'});
 const w=dom.window,d=w.document,workspace=d.getElementById('np-workspace'),method=d.getElementById('np-node-method'),child=d.getElementById('np-node-child');
 // Cache actual JSDOM computed styles within an immutable fixture phase.
 // Each deliberate mutation phase invalidates this cache before observation.
 const nativeStyle=w.getComputedStyle.bind(w);let styles=new WeakMap();
 w.getComputedStyle=n=>{if(!styles.has(n))styles.set(n,nativeStyle(n));return styles.get(n);};
 // A browser's layout is intentionally not asserted. Supply deterministic
 // geometry while deriving hidden/details/display eligibility from real DOM.
 w.HTMLElement.prototype.getBoundingClientRect=function(){return {x:17,y:382,width:398,height:456,left:17,right:415,top:382,bottom:838};};
 w.HTMLElement.prototype.getClientRects=function(){
  for(let n=this;n;n=n.parentElement){
   if(n.hidden||w.getComputedStyle(n).display==='none')return [];
   if(n.tagName==='DETAILS'&&!n.open){const summary=[...n.children].find(c=>c.tagName==='SUMMARY');if(this!==n&&this!==summary&&!summary?.contains(this))return [];}
  }
  return [this.getBoundingClientRect()];
 };
 for(const [key,value] of Object.entries({clientWidth:398,clientHeight:456,scrollWidth:398,scrollHeight:601}))Object.defineProperty(w.HTMLElement.prototype,key,{get(){return value;},configurable:true});
 const eligible=()=>[...d.querySelectorAll(selector)].filter(n=>n.tabIndex>=0&&!n.disabled&&n.getClientRects().length);
 const footer=d.getElementById('external-controls');
 for(let i=eligible().length;i<170;i++){const b=d.createElement('button');b.id='outside-base-'+i;b.textContent='Existing outside control '+i;footer.appendChild(b);}
 if(eligible().length!==170)throw Error('Fixture baseline must have exactly170 actual eligible DOM candidates');
 const s={route:{nav:'1',tree:'g',node:'method',scope:'scope:all',paper:'p',version:'v',claim:null,bench:null,protocol:null,mode:'tree',template:null},
  revision:3,originTrail:[],contexts:{k:{focusTarget:'method',expandedByTree:{g:['method']},selectedByTree:{g:'method'},treeScrollByTree:{g:0},treeScrollLeftByTree:{g:0},detailScrollByTree:{g:0},windowScroll:0}}};
 w.NavigationProductApp={getState:()=>clone(s)};w.NavigationProductModel={KEY:'nav',contextKey:()=> 'k'};w.history.replaceState({nav:clone(s),otherOwner:{keep:'unchanged'}},'');
 method.focus();
 const observed=new Map(),add=d.addEventListener.bind(d),remove=d.removeEventListener.bind(d),types=['keydown','pointerdown','pointerup','click','focusin','scroll'];
 d.addEventListener=(t,f,c)=>{if(types.includes(t)){if(!observed.has(t))observed.set(t,new Set());observed.get(t).add(f);}return add(t,f,c);};
 d.removeEventListener=(t,f,c)=>{observed.get(t)?.delete(f);return remove(t,f,c);};
 const start=new w.Function(input.start),state=new w.Function(input.state),action=new w.Function(input.action),stop=new w.Function(input.stop);
 const addFour=(parent,prefix)=>{for(let i=0;i<4;i++){const b=d.createElement('button');b.id=prefix+i;b.textContent='New control '+i;parent.appendChild(b);}};
 const replace=n=>n.replaceWith(n.cloneNode(true));
 const read=()=>({state:clone(state()),inventory:clone(action('candidates'))});
 let before,after,repeat,restored,startBudget,stopResult;
 try{
  start();startBudget=state().tabBound;
  if(name==='before-baseline-four')addFour(footer,'external-added-');
  action('baseline');
  if(name==='baseline-gap-four')addFour(footer,'baseline-gap-added-');
  before=read();action('reset');
  if(name==='external-four')addFour(footer,'external-added-');
  else if(name==='external-four-clones')[...footer.children].slice(0,4).forEach(replace);
  else if(name==='internal-four')addFour(workspace,'internal-added-');
  else if(name==='internal-remove-four')['a','b','c','d'].forEach(x=>d.getElementById('scope-'+x).remove());
  else if(name==='internal-clone-four')['a','b','c','d'].forEach(x=>replace(d.getElementById('scope-'+x)));
  else if(name==='internal-reorder-four'){const p=d.getElementById('ordinary-controls');for(const n of [...p.children].reverse())p.appendChild(n);}
  else if(name==='add-hidden'){const b=d.createElement('button');b.id='hidden-added';b.hidden=true;workspace.appendChild(b);}
  else if(name==='add-negative'){const b=d.createElement('button');b.id='negative-added';b.tabIndex=-1;workspace.appendChild(b);}
  else if(name==='remove-hidden')d.getElementById('scope-hidden').remove();
  else if(name==='clone-hidden')replace(d.getElementById('scope-hidden'));
  else if(name==='remove-negative')d.getElementById('scope-negative').remove();
  else if(name==='clone-negative')replace(d.getElementById('scope-negative'));
  else if(name==='disabled')d.getElementById('scope-a').disabled=true;
  else if(name==='hidden')d.getElementById('scope-a').hidden=true;
  else if(name==='display-none')d.getElementById('scope-a').style.display='none';
  else if(name==='visibility-hidden')d.getElementById('scope-a').style.visibility='hidden';
  else if(name==='ancestor-hidden')d.getElementById('ancestor-wrapper').hidden=true;
  else if(name==='ancestor-display-none')d.getElementById('ancestor-wrapper').style.display='none';
  else if(name==='details-open')d.getElementById('scope-details').open=true;
  else if(name==='empty-details-open')d.getElementById('empty-details').open=true;
  else if(name==='href')d.getElementById('scope-link').setAttribute('href','/changed');
  else if(name==='role')d.getElementById('scope-a').setAttribute('role','switch');
  else if(name==='type')d.getElementById('scope-a').setAttribute('type','submit');
  else if(name==='name')d.getElementById('scope-input').name='different-name';
  else if(name==='aria-label')d.getElementById('scope-input').setAttribute('aria-label','Changed label');
  else if(name==='aria-controls')d.getElementById('scope-input').setAttribute('aria-controls','different-target');
  else if(name==='raw-data-action')d.getElementById('scope-a').setAttribute('data-action','unexpected');
  else if(name==='control-text')d.getElementById('scope-a').textContent='Changed visible purpose';
  else if(name==='input-value')d.getElementById('scope-input').value='Changed live value';
  else if(name==='input-checked')d.getElementById('scope-input').checked=true;
  else if(name==='tab-control-negative')d.getElementById('scope-a').tabIndex=-1;
  else if(name==='label-positive')d.getElementById('method-label').tabIndex=0;
  else if(name==='reader-fake-tree-positive')d.getElementById('reader-fake-tree').tabIndex=0;
  else if(name==='legal-roving'){method.tabIndex=-1;child.tabIndex=0;child.focus();s.contexts.k.focusTarget='child';}
  else if(name==='roving-positive'){method.tabIndex=1;}
  else if(name==='roving-negative-two'){method.tabIndex=-2;child.tabIndex=0;child.focus();s.contexts.k.focusTarget='child';}
  else if(name==='roving-two-zero'){child.tabIndex=0;}
  else if(name==='roving-no-zero'){method.tabIndex=-1;}
  else if(name==='workspace-clone')replace(workspace);
  else if(name==='workspace-hidden')workspace.hidden=true;
  styles=new WeakMap();after=read();repeat=read();
  if(name==='legal-roving'){method.tabIndex=0;child.tabIndex=-1;method.focus();s.contexts.k.focusTarget='method';styles=new WeakMap();restored=read();}
 }finally{if(w.__npMethodChildProbe)stopResult=stop();}
 const result={name,startBudget,before,after,repeat,restored,stop:stopResult,
  listeners:[...observed.values()].reduce((n,x)=>n+x.size,0),installed:!!w.__npMethodChildProbe};
 dom.window.close();return result;
}
process.stdout.write(JSON.stringify(input.cases.map(runCase)));
"""
        result=subprocess.run(['node','-e',code],input=json.dumps(dict(cases=cls.cases,
            start=MODULE.METHOD_CHILD_PROBE_START_JS,state=MODULE.METHOD_CHILD_STATE_JS,
            action=MODULE.METHOD_CHILD_ACTION_JS,stop=MODULE.METHOD_CHILD_PROBE_STOP_JS)),
            text=True,capture_output=True,timeout=90,cwd=Path(MODULE.__file__).parents[1])
        if result.returncode:
            raise AssertionError('Actual production observer JS failed in JSDOM:\n'+result.stderr)
        cls.results={row['name']:row for row in json.loads(result.stdout)}

    def assert_inventory(self, frame):
        MODULE.check_method_child_candidates(frame['state'],frame['inventory'])
        items=frame['inventory']['eligible']
        self.assertEqual(len(items),frame['inventory']['eligibleCount'])
        self.assertEqual(len({row['token'] for row in items}),len(items))
        self.assertTrue(all(type(row['inWorkspace']) is bool for row in items))

    def assert_rejected(self, case):
        data=self.results[case]
        with self.assertRaises(RuntimeError):
            MODULE.check_method_child_state(data['before']['state'],data['after']['state'])
        self.assertEqual(data['before']['state']['tabBound'],171)
        self.assertEqual(data['after']['state']['tabBound'],171,'budget cannot be repurposed as a changing scope count')

    def test_external_171_to_175_changes_only_separate_diagnostic_not_actual_state_bridge(self):
        data=self.results['external-four'];before,after=data['before'],data['after']
        self.assertEqual(data['startBudget'],171)
        self.assertEqual(before['inventory']['eligibleCount'],170)
        self.assertEqual(after['inventory']['eligibleCount'],174)
        self.assertEqual(min(256,after['inventory']['eligibleCount']+1),175)
        self.assertEqual(before['state']['tabBound'],171);self.assertEqual(after['state']['tabBound'],171)
        self.assertEqual(before['state'],after['state'],'the full bridge remains exact; do not remove actual state fields')
        MODULE.check_method_child_state(before['state'],after['state'],exact=True)
        self.assert_inventory(before);self.assert_inventory(after)
        added=[row for row in after['inventory']['eligible'] if row['id'] and row['id'].startswith('external-added-')]
        self.assertEqual(len(added),4);self.assertTrue(all(row['inWorkspace'] is False for row in added))
        old={row['id']:row['token'] for row in before['inventory']['eligible']}
        for row in after['inventory']['eligible']:
            if row['id'] in old:self.assertEqual(row['token'],old[row['id']])
        self.assertEqual(after,data['repeat'],'stable tokens must survive repeated real STATE reads')

    def test_outside_same_id_clones_have_new_diagnostic_tokens_but_no_workspace_changes(self):
        data=self.results['external-four-clones'];before,after=data['before'],data['after']
        self.assertEqual(before['state'],after['state'])
        self.assert_inventory(before);self.assert_inventory(after)
        old={row['id']:row for row in before['inventory']['eligible']}
        changed=[row for row in after['inventory']['eligible'] if row['token']!=old[row['id']]['token']]
        self.assertEqual(len(changed),4)
        self.assertTrue(all(row['inWorkspace'] is False for row in changed))
        self.assertEqual(after,data['repeat'])

    def test_budget_is_frozen_at_settled_baseline_not_premature_probe_start(self):
        data=self.results['before-baseline-four']
        self.assertEqual(data['startBudget'],171)
        self.assertEqual(data['before']['state']['tabBound'],175)
        self.assertEqual(data['before']['inventory']['eligibleCount'],174)
        self.assertEqual(data['before'],data['after'])
        self.assert_inventory(data['before'])

    def test_first_baseline_state_freezes_budget_and_inventory_in_the_same_observation(self):
        data=self.results['baseline-gap-four']
        self.assertEqual(data['startBudget'],171)
        self.assertEqual(data['before']['inventory']['eligibleCount'],174)
        self.assertEqual(data['before']['state']['tabBound'],175)
        self.assertEqual(data['before'],data['after'])
        self.assert_inventory(data['before'])
        MODULE.check_method_child_state(data['before']['state'],data['after']['state'],exact=True)

    def test_same_four_new_controls_inside_scope_are_explicitly_internal_and_rejected(self):
        data=self.results['internal-four'];before,after=data['before'],data['after']
        self.assertEqual(after['inventory']['eligibleCount']-before['inventory']['eligibleCount'],4)
        new=[row for row in after['inventory']['eligible'] if row['id'] and row['id'].startswith('internal-added-')]
        self.assertEqual(len(new),4);self.assertTrue(all(row['inWorkspace'] is True for row in new))
        self.assertFalse(after['state']['scopeCandidates']['same'])
        self.assert_rejected('internal-four')
        self.assert_inventory(after)
        # A count increase of four is not itself evidence of external controls.
        import copy
        forged=copy.deepcopy(after['inventory'])
        for row in forged['eligible']:
            if row['id'] and row['id'].startswith('internal-added-'):row['inWorkspace']=False
        with self.assertRaises(RuntimeError):MODULE.check_method_child_candidates(after['state'],forged)

    def test_scope_order_and_original_candidate_objects_cannot_be_replaced_by_equal_html(self):
        for case in ('internal-remove-four','internal-clone-four','internal-reorder-four','workspace-clone'):
            with self.subTest(case=case):
                data=self.results[case];self.assert_rejected(case)
                self.assertFalse(data['after']['state']['scopeCandidates']['same'])
        clones=self.results['internal-clone-four']
        old={row['id']:row for row in clones['before']['state']['scopeCandidates']['items']}
        new={row['id']:row for row in clones['after']['state']['scopeCandidates']['items']}
        for identity in ('scope-a','scope-b','scope-c','scope-d'):
            self.assertNotEqual(old[identity]['token'],new[identity]['token'])
            self.assertEqual(old[identity]['id'],new[identity]['id'])
            self.assertEqual(old[identity]['tabIndex'],new[identity]['tabIndex'])

    def test_hidden_and_minus_one_candidates_are_bound_even_when_tab_count_does_not_change(self):
        baseline=self.results['unchanged']['before']
        source={row['id']:row for row in baseline['state']['scopeCandidates']['items']}
        for identity in ('scope-hidden','scope-negative','scope-disabled','details-child','child-label','np-detail-scroll'):
            self.assertIn(identity,source)
            self.assertNotIn(identity,[row['id'] for row in baseline['inventory']['eligible']])
        for case in ('add-hidden','add-negative','remove-hidden','clone-hidden','remove-negative','clone-negative'):
            with self.subTest(case=case):
                self.assert_rejected(case)
                data=self.results[case]
                self.assertEqual(data['before']['inventory']['eligibleCount'],data['after']['inventory']['eligibleCount'])

    def test_disabled_hidden_layout_ancestor_and_disclosure_changes_remain_hard_failures(self):
        for case in ('disabled','hidden','display-none','visibility-hidden','ancestor-hidden','ancestor-display-none',
                     'details-open','empty-details-open','workspace-hidden'):
            with self.subTest(case=case):self.assert_rejected(case)
        data=self.results['empty-details-open']
        self.assertEqual(data['before']['inventory']['eligibleCount'],data['after']['inventory']['eligibleCount'])
        self.assertTrue(data['after']['state']['scopeCandidates']['same'],'same node identities cannot hide changed details semantics')

    def test_non_tree_candidate_semantics_are_not_masked_by_roving_exception(self):
        for case in ('href','role','type','name','aria-label','aria-controls','raw-data-action','control-text','input-value','input-checked',
                     'tab-control-negative','label-positive','reader-fake-tree-positive'):
            with self.subTest(case=case):self.assert_rejected(case)
        baseline=self.results['unchanged']['before']['state']['scopeCandidates']['items']
        by_id={row['id']:row for row in baseline}
        self.assertIsNone(by_id['method-label']['sourcePosition'])
        self.assertIsNone(by_id['reader-fake-tree']['sourcePosition'])
        self.assertEqual(by_id['np-node-method']['sourcePosition'],'method')

    def test_only_real_treeitem_zero_minus_one_roving_is_allowed_and_exactly_returns(self):
        data=self.results['legal-roving'];before,after,restored=data['before'],data['after'],data['restored']
        MODULE.check_method_child_state(before['state'],after['state'])
        self.assertEqual(before['state']['scopeCandidates']['items'],after['state']['scopeCandidates']['items'])
        self.assertEqual(after['state']['scopeCandidates']['treeTabIndexes'],[dict(position='method',tabIndex=-1),dict(position='child',tabIndex=0)])
        self.assertEqual(after['state']['roving'],['child'])
        self.assertEqual(after['state']['active']['id'],'np-node-child')
        self.assertEqual(after['state']['originalFocus'],dict(id='np-node-method',tag='LI',tabIndex=0))
        self.assertEqual(before['state']['history'],after['state']['history'])
        self.assertEqual(before['state'],restored['state'])
        MODULE.check_method_child_state(before['state'],restored['state'],exact=True)
        for frame in (before,after,restored):self.assert_inventory(frame)
        for case in ('roving-positive','roving-negative-two','roving-two-zero','roving-no-zero'):
            with self.subTest(case=case):self.assert_rejected(case)

    def test_actual_observers_clean_up_every_fixture_including_invalid_scope_cases(self):
        for case,data in self.results.items():
            with self.subTest(case=case):
                self.assertTrue(data['stop']['cleanedUp'])
                self.assertEqual(data['listeners'],0)
                self.assertFalse(data['installed'])
