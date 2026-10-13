"""Footer capture contracts and negative controls; not real-browser acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('footer_screenshots', ROOT / 'scripts/footer_screenshots.py')
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)
ORIGIN = 'http://127.0.0.1:4186'


def fixture():
    box = dict(x=20, y=700, width=200, height=24)
    links = [dict(href=ORIGIN + '/' + p) for p in ('index.html', 'reading/index.html', 'about/index.html')]
    links.append(dict(href=M.GITHUB))
    for i, (url, label) in enumerate(M.LINKS):
        rect = dict(box, x=700 + i * 230)
        links.append(dict(href=url, rawHref=url, text=label, target='_blank', rel=['noopener', 'noreferrer'],
                          tabIndex=0, visible=True, rect=rect, fragments=[dict(rect, uncovered=True)],
                          fontSize=14, focus=i == 0, focusVisible=i == 0,
                          outlineWidth=2, outlineStyle='solid', boxShadow='none'))
    return dict(url=ORIGIN + '/index.html', viewport=dict(x=0, y=0, width=1440, height=900),
                fonts='loaded', footerCount=1, footer=dict(visible=True, rect=dict(x=0, y=650, width=1440, height=200)),
                links=links, scroll=dict(x=0, y=2000), historyLength=2)


def target_fixture(url):
    identity=url.rstrip('/').rsplit('/',1)[-1]
    return dict(url=url,readyState='complete',title=identity,brand=identity,main=True,error=False,openerIsNull=True)


def poll(check, timeout):
    for _ in range(20):
        result=check()
        if result:return result
    raise TimeoutError('mock bounded wait')


class FooterScreenshotChecks(unittest.TestCase):
    def test_exact_desktop_plan_and_safe_snapshot(self):
        self.assertEqual(M.ROUTES, (('home', 'index.html'), ('about', 'about/index.html')))
        M.check_snapshot(fixture(), ORIGIN, 'index.html', 1440, 900, M.LINKS[0][0])
        for width, height in ((1440, 900), (1920, 1080)):
            d = fixture(); d['viewport'].update(width=width, height=height)
            d['url'] = ORIGIN + '/about/index.html'
            M.check_snapshot(d, ORIGIN, 'about/index.html', width, height)

    def test_rejects_hidden_clipped_covered_missing_unsafe_or_unreadable_footer(self):
        mutations = [lambda d:d.update(url=ORIGIN + '/wrong'), lambda d:d.update(fonts='loading'),
                     lambda d:d.update(footerCount=2), lambda d:d['footer'].update(visible=False),
                     lambda d:d['footer']['rect'].update(y=850), lambda d:d['links'].pop(),
                     lambda d:d['links'].append(copy.deepcopy(d['links'][-1])),
                     lambda d:d['links'][1].update(href=ORIGIN + '/wrong.html'),
                     lambda d:d['links'][4].update(rawHref='//chunhui-lab.github.io/GradCompass/'),
                     lambda d:d['links'][4].update(text='GradCompass'),
                     lambda d:d['links'][4].update(target='_self'),
                     lambda d:d['links'][4].update(rel=['noopener']),
                     lambda d:d['links'][4].update(tabIndex=-1),
                     lambda d:d['links'][4].update(visible=False),
                     lambda d:d['links'][4].update(fontSize=8),
                     lambda d:d['links'][4]['rect'].update(x=1500),
                     lambda d:d['links'][4].update(fragments=[]),
                     lambda d:d['links'][4]['fragments'][0].update(uncovered=False),
                     lambda d:d['links'][4]['fragments'][0].update(width=300)]
        for index, mutate in enumerate(mutations):
            d=fixture();mutate(d)
            with self.subTest(index=index),self.assertRaises(RuntimeError):
                M.check_snapshot(d,ORIGIN,'index.html',1440,900)

    def test_native_focus_must_be_on_correct_anchor_and_visibly_indicated(self):
        for change in [dict(focus=False),dict(focusVisible=False),dict(outlineWidth=0,boxShadow='none'),dict(outlineStyle='none',boxShadow='none')]:
            d=fixture();d['links'][4].update(change)
            with self.subTest(change=change),self.assertRaises(RuntimeError):
                M.check_snapshot(d,ORIGIN,'index.html',1440,900,M.LINKS[0][0])

    def test_target_is_exact_root_not_repo_preview_or_other_site(self):
        for url,_ in M.LINKS:
            M.check_opened_target(url,url)
            for bad in [url+'index.html',url+'?source=test',url+'preview/',M.GITHUB,'https://example.org/']:
                with self.subTest(url=url,bad=bad),self.assertRaises(RuntimeError):M.check_opened_target(url,bad)
        with self.assertRaises(RuntimeError):M.check_opened_target(M.GITHUB,M.GITHUB)

    def test_opener_url_scroll_and_history_cannot_be_changed(self):
        d=fixture();M.check_opener(d,copy.deepcopy(d))
        for key,value in [('url',ORIGIN+'/about/'),('scroll',dict(x=0,y=0)),('historyLength',3)]:
            after=copy.deepcopy(d);after[key]=value
            with self.subTest(key=key),self.assertRaises(RuntimeError):M.check_opener(d,after)

    def test_keyboard_transport_uses_native_actions_and_releases_shift(self):
        class Driver:
            def __init__(self):self.calls=[]
            def call(self,*args):self.calls.append(args)
            def settle(self):pass
        d=Driver();M.key(d,'\ue004',shift=True)
        self.assertEqual(d.calls[0][0:2],('POST','/actions'))
        self.assertEqual(d.calls[0][2]['actions'][0]['actions'],[
            {'type':'keyDown','value':'\ue008'}, {'type':'keyDown','value':'\ue004'},
            {'type':'keyUp','value':'\ue004'}, {'type':'keyUp','value':'\ue008'}])
        self.assertEqual(d.calls[-1],('DELETE','/actions'))

    def test_real_snapshot_executes_on_generated_home_and_nested_footer(self):
        script=r'''
const fs=require('fs'),{JSDOM}=require('jsdom'),assert=require('assert');
const input=JSON.parse(fs.readFileSync(0,'utf8'));
for(const route of ['index.html','about/index.html']){
 const dom=new JSDOM(fs.readFileSync('dist/'+route,'utf8'),{url:input.origin+'/'+route,runScripts:'outside-only'}),w=dom.window,d=w.document;
 const style=d.createElement('style');style.textContent='*{opacity:1;visibility:visible}a{font-size:14px;outline:2px solid blue}';d.head.append(style);
 Object.defineProperty(d,'fonts',{value:{status:'loaded'}});Object.defineProperty(w,'innerWidth',{value:1440});Object.defineProperty(w,'innerHeight',{value:900});
 Object.defineProperty(w.HTMLElement.prototype,'innerText',{get(){return this.textContent}});
 const footer=d.querySelector('footer.site-footer'),links=[...footer.querySelectorAll('a')],box=e=>e===footer?{x:0,y:650,width:1440,height:200}:{x:20+links.indexOf(e)*230,y:700,width:210,height:24};
 footer.getBoundingClientRect=()=>box(footer);for(const a of links)a.getBoundingClientRect=()=>box(a);
 d.createRange=()=>({selectNodeContents(e){this.e=e},getClientRects(){return [box(this.e)]}});
 d.elementFromPoint=(x,y)=>links.find(a=>{const r=box(a);return x>=r.x&&x<=r.x+r.width&&y>=r.y&&y<=r.y+r.height})||footer;
 const result=new w.Function(input.snapshot)();assert.equal(result.links.length,6);assert.equal(result.links[4].text,'GradCompass 申请导航 ↗');assert.equal(result.links[5].text,'IELTSOrbit 雅思学习 ↗');
 process.stdout.write(JSON.stringify(result)+'\n');dom.window.close();
}
'''
        result=subprocess.run(['node','-e',script],input=json.dumps(dict(origin=ORIGIN,snapshot=M.SNAPSHOT_JS)),text=True,capture_output=True,cwd=ROOT)
        self.assertEqual(result.returncode,0,result.stderr)
        for route,line in zip(('index.html','about/index.html'),result.stdout.splitlines()):
            M.check_snapshot(json.loads(line),ORIGIN,route,1440,900)

    def test_capture_is_additive_to_existing_plan_and_workflow_security(self):
        source=(ROOT/'scripts/navigation_screenshots.py').read_text()
        self.assertIn('from footer_screenshots import capture_footer_checks',source)
        self.assertIn('capture_footer_checks(driver, report, save, out, dist,',source)
        self.assertIn("'scripts/footer_screenshots.py', 'tests/test_footer_screenshots.py'",source)
        workflow=(ROOT/'.github/workflows/navigation-screenshots.yml').read_text()
        self.assertIn('contents: read',workflow);self.assertIn('persist-credentials: false',workflow)
        self.assertIn('navigation-screenshots/*.png',workflow)
        module=(ROOT/'scripts/footer_screenshots.py').read_text()
        self.assertNotIn('.click()',module);self.assertNotIn('window.open(',module)
        self.assertNotIn('install',module.split('LINKS =',1)[1])


class BoundedWaitChecks(unittest.TestCase):
    def test_scroll_wait_requires_visible_footer_and_continuous_stability(self):
        snapshots=[]
        for y,visible in [(10,False),(10,False),(20,True),(30,True),(40,True),(40,True),(40,True),(40,True),(40,True)]:
            d=fixture();d['scroll']['y']=y;d['footer']['visible']=visible;snapshots.append(d)
        class Driver:
            def js(self,script):return snapshots.pop(0)
        ticks=iter(i*.11 for i in range(30))
        result=M.wait_footer_stable(Driver(),poll,clock=lambda:next(ticks))
        self.assertEqual(result['scroll']['y'],40)
        self.assertLessEqual(len(snapshots),1)

    def test_invisible_or_continuously_moving_footer_times_out(self):
        for visible in (False,True):
            class Driver:
                y=0
                def js(self,script):
                    self.y+=1;d=fixture();d['scroll']['y']=self.y;d['footer']['visible']=visible;return d
            with self.subTest(visible=visible),self.assertRaises(TimeoutError):
                M.wait_footer_stable(Driver(),poll)

    def test_target_waits_through_blank_loading_and_checks_identity(self):
        url=M.LINKS[0][0];good=target_fixture(url)
        pending=[dict(good,url='about:blank'),dict(good,readyState='loading'),good]
        class Driver:
            def js(self,script):return pending.pop(0)
        step={};self.assertEqual(M.wait_target_ready(Driver(),url,step,poll),url)
        self.assertEqual(pending,[])
        for change in [dict(url='about:blank'),dict(url=url+'preview/'),dict(error=True),dict(title='404'),dict(brand='Other'),dict(main=False),dict(openerIsNull=False)]:
            class BadDriver:
                def js(self,script):return dict(good,**change)
            with self.subTest(change=change),self.assertRaises(TimeoutError):
                M.wait_target_ready(BadDriver(),url,{},poll)


class ActivationChecks(unittest.TestCase):
    class Driver:
        def __init__(self,actual=None):self.current='local';self.handles={'local','unrelated'};self.closed=[];self.expected=M.LINKS[0][0];self.actual=actual or self.expected
        def js(self,script,*args):
            if script==M.TARGET_SNAPSHOT_JS:return target_fixture(self.actual)
            return self.expected if script=='return document.activeElement.href' else fixture()
        def selector(self,selector):return {M.ELEMENT:selector}
        def click(self,element):self.handles.add('new')
        def settle(self):pass
        def call(self,method,path,data=None):
            if path=='/window/handles':return sorted(self.handles)
            if path=='/window' and method=='GET':return self.current
            if path=='/window' and method=='POST':self.current=data['handle'];return
            if path=='/window' and method=='DELETE':self.closed.append(self.current);self.handles.remove(self.current);return
            if path=='/url':return self.actual
            if path=='/actions' and method=='POST':self.handles.add('new')

    def test_native_enter_and_pointer_check_new_target_and_preserve_other_tabs(self):
        for method in ('Enter','pointer'):
            d=self.Driver();record={'activations':[]}
            M.activate(d,d.expected,method,record,lambda:None,lambda f,t:self.assertTrue(f()))
            self.assertEqual(d.current,'local');self.assertEqual(d.handles,{'local','unrelated'});self.assertEqual(d.closed,['new'])
            self.assertEqual(record['activations'][0]['actualUrl'],d.expected)

    def test_full_capture_plan_keeps_four_images_and_sixteen_real_activation_requests(self):
        import base64
        import tempfile
        class Driver(self.Driver):
            def __init__(self):super().__init__();self.route='index.html';self.width=1440;self.height=900;self.focus=M.GITHUB
            def cdp(self,cmd,data):self.width=data['width'];self.height=data['height']
            def js(self,script,*args):
                if script==M.TARGET_SNAPSHOT_JS:return target_fixture(self.actual)
                if script=='return document.activeElement.href':return self.focus
                if script==M.SNAPSHOT_JS:
                    d=fixture();d['url']=ORIGIN+'/'+self.route;d['viewport'].update(width=self.width,height=self.height)
                    for a in d['links'][4:]:a.update(focus=a['href']==self.focus,focusVisible=a['href']==self.focus)
                    return d
                if 'focus({preventScroll:true})' in script:self.focus=M.GITHUB
            def click(self,element):
                selector=element[M.ELEMENT];self.expected=selector.split('href="')[1].split('"')[0];self.actual=self.expected;self.focus=self.expected;self.handles.add('new')
            def call(self,method,path,data=None):
                if path=='/url' and method=='POST':self.route=data['url'].removeprefix(ORIGIN+'/');return
                if path=='/screenshot':return base64.b64encode(b'\x89PNG\r\n\x1a\ntransport-fixture').decode()
                if path=='/actions' and method=='POST':
                    actions=data['actions'][0]['actions'];values=[a['value'] for a in actions if a['type']=='keyDown']
                    if '\ue007' in values:self.expected=self.focus;self.actual=self.expected;self.handles.add('new')
                    elif '\ue004' in values:
                        order=[M.GITHUB,*dict(M.LINKS)];self.focus=order[order.index(self.focus)+(-1 if '\ue008' in values else 1)]
                    return
                return super().call(method,path,data)
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);dist=root/'dist';out=root/'out';out.mkdir();(dist/'about').mkdir(parents=True);(dist/'assets').mkdir()
            for _,route in M.ROUTES:(dist/route).write_text('fixture')
            (dist/'assets/style.css').write_text('fixture')
            d=Driver();report={}
            with patch.object(M,'wait_footer_stable',side_effect=lambda driver,wait:driver.js(M.SNAPSHOT_JS)):
                M.capture_footer_checks(d,report,lambda:None,out,dist,ORIGIN,[(1440,900),(1920,1080)],poll,lambda image:True)
            self.assertEqual(len(list(out.glob('*.png'))),4)
            self.assertEqual(len(report['footerCaptures']),4)
            self.assertEqual(sum(len(r['activations']) for r in report['footerCaptures']),16)
            self.assertTrue(all(len(r['keyboard'])==3 and r['status']=='captured_for_human_review' for r in report['footerCaptures']))
            self.assertEqual(d.handles,{'local','unrelated'})
            self.assertEqual(set(report['footerServedSources']),{'index.html','about/index.html','assets/style.css'})

    def test_wrong_destination_still_closes_only_new_tab_and_restores_opener(self):
        d=self.Driver('https://example.org/wrong');record={'activations':[]}
        with self.assertRaises(TimeoutError):M.activate(d,d.expected,'pointer',record,lambda:None,poll)
        self.assertEqual(d.handles,{'local','unrelated'});self.assertEqual(d.current,'local')


if __name__=='__main__':unittest.main()
