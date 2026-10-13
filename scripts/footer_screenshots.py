"""Add bounded desktop shared-footer evidence to the existing PR Chrome session.

No browser/package install, deployment, source mutation or synthetic click is used.
Real navigation targets are checked; screenshots still require human review.
"""
import base64
import hashlib
import time

LINKS = (
    ('https://chunhui-lab.github.io/GradCompass/', 'GradCompass 申请导航 ↗'),
    ('https://chunhui-lab.github.io/IELTSOrbit/', 'IELTSOrbit 雅思学习 ↗'),
)
ROUTES = (('home', 'index.html'), ('about', 'about/index.html'))
GITHUB = 'https://github.com/CHUNHUI-LAB/RoboPaperAtlas'
ELEMENT = 'element-6066-11e4-a52e-4f735466cecf'
SNAPSHOT_JS = r"""
const footer=document.querySelector('footer.site-footer');
function rect(r){return {x:r.x,y:r.y,width:r.width,height:r.height};}
function visible(e){for(let n=e;n;n=n.parentElement){const s=getComputedStyle(n);if(s.display==='none'||s.visibility!=='visible'||Number(s.opacity)!==1)return false;}return true;}
function proof(e){const s=getComputedStyle(e),r=e.getBoundingClientRect(),range=document.createRange();range.selectNodeContents(e);
 const fragments=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0).map(r=>({...rect(r),uncovered:[[.5,.5],[.1,.5],[.9,.5]].every(([x,y])=>{const hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!hit&&(hit===e||e.contains(hit));})}));
 return {href:e.href,rawHref:e.getAttribute('href'),text:e.innerText.replace(/\s+/g,' ').trim(),target:e.target,rel:e.rel.split(/\s+/).filter(Boolean).sort(),tabIndex:e.tabIndex,
  visible:visible(e),rect:rect(r),fragments,fontSize:parseFloat(s.fontSize),focus:document.activeElement===e,focusVisible:e.matches(':focus-visible'),outlineWidth:parseFloat(s.outlineWidth),outlineStyle:s.outlineStyle,boxShadow:s.boxShadow};}
return {url:location.href,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},fonts:document.fonts.status,
 footerCount:document.querySelectorAll('footer.site-footer').length,footer:footer?{visible:visible(footer),rect:rect(footer.getBoundingClientRect())}:null,
 links:footer?[...footer.querySelectorAll('a')].map(proof):[],scroll:{x:scrollX,y:scrollY},historyLength:history.length};
"""

TARGET_SNAPSHOT_JS = r"""
return {url:location.href,readyState:document.readyState,title:document.title,
 brand:document.querySelector('header .brand')?.textContent.trim() || '',
 main:!!document.querySelector('main'),
 error:!!document.querySelector('#main-frame-error, #errorPageContainer, body.neterror'),
 openerIsNull:window.opener===null};
"""


def wait_footer_stable(driver, wait_for, clock=time.monotonic):
    state = {'position': None, 'since': None, 'samples': 0}
    def ready():
        data = driver.js(SNAPSHOT_JS)
        state['samples'] += 1
        visible = (data.get('footer') and data['footer']['visible'] and
                   inside(data['footer']['rect'], data['viewport']))
        if not visible or data['scroll'] != state['position']:
            state['position'] = data['scroll']
            state['since'] = clock() if visible else None
            return False
        if state['since'] is None:
            state['since'] = clock()
        return data if clock() - state['since'] >= .3 else False
    return wait_for(ready, 10)


def wait_target_ready(driver, url, step, wait_for):
    identity = url.rstrip('/').rsplit('/', 1)[-1]
    def ready():
        data = driver.js(TARGET_SNAPSHOT_JS)
        step['destination'] = data
        return (data['url'] == url and data['readyState'] in ('interactive', 'complete') and
                identity in data['title'] and identity in data['brand'] and data['main'] and
                not data['error'] and data['openerIsNull'])
    wait_for(ready, 30)
    check_opened_target(url, step['destination']['url'])
    return step['destination']['url']


def inside(r, area):
    return (r['width'] > 0 and r['height'] > 0 and r['x'] >= area['x'] - 1 and
            r['y'] >= area['y'] - 1 and r['x'] + r['width'] <= area['x'] + area['width'] + 1 and
            r['y'] + r['height'] <= area['y'] + area['height'] + 1)


def check_snapshot(data, origin, route, width, height, focused=None):
    if (data['url'] != origin + '/' + route or data['viewport'] != dict(x=0, y=0, width=width, height=height) or
            data['fonts'] != 'loaded' or data['footerCount'] != 1 or not data.get('footer') or
            not data['footer']['visible'] or not inside(data['footer']['rect'], data['viewport'])):
        raise RuntimeError('Shared footer is missing, hidden, clipped, or on the wrong desktop page')
    expected_local = ['index.html', 'reading/index.html', 'about/index.html']
    hrefs = [a['href'] for a in data['links']]
    expected = [origin + '/' + p for p in expected_local] + [GITHUB] + [url for url, _ in LINKS]
    if hrefs != expected:
        raise RuntimeError('Footer changed existing navigation, omitted a root link, or duplicated/reordered links')
    for url, label in LINKS:
        a = next(a for a in data['links'] if a['href'] == url)
        if (a['rawHref'] != url or a['text'] != label or a['target'] != '_blank' or
                a['rel'] != ['noopener', 'noreferrer'] or a['tabIndex'] != 0 or
                not a['visible'] or a['fontSize'] < 12 or not inside(a['rect'], data['viewport']) or
                not inside(a['rect'], data['footer']['rect']) or not a['fragments'] or
                any(not f['uncovered'] or not inside(f, data['viewport']) or not inside(f, a['rect']) for f in a['fragments'])):
            raise RuntimeError('Related-site footer link is unsafe, unreadable, clipped, covered or not keyboard reachable')
        if focused == url and (not a['focus'] or not a['focusVisible'] or
                not ((a['outlineWidth'] >= 1 and a['outlineStyle'] not in ('none', 'hidden')) or a['boxShadow'] != 'none')):
            raise RuntimeError('Native keyboard focus lacks a visible indicator on the expected footer link')


def check_opener(before, after):
    for key in ('url', 'scroll', 'historyLength'):
        if before[key] != after[key]:
            raise RuntimeError('Cross-site activation changed the local opener: ' + key)


def check_opened_target(url, actual):
    if url not in dict(LINKS) or actual != url:
        raise RuntimeError('Native footer activation opened an unexpected destination')


def key(driver, value, shift=False, settle=True):
    actions = ([{'type': 'keyDown', 'value': '\ue008'}] if shift else [])
    actions += [{'type': 'keyDown', 'value': value}, {'type': 'keyUp', 'value': value}]
    if shift:
        actions.append({'type': 'keyUp', 'value': '\ue008'})
    driver.call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'footer-keyboard', 'actions': actions}]})
    driver.call('DELETE', '/actions')
    if settle:
        driver.settle()


def activate(driver, url, method, record, save, wait_for):
    check_opened_target(url, url)
    before = driver.js(SNAPSHOT_JS)
    original = driver.call('GET', '/window')
    handles = set(driver.call('GET', '/window/handles'))
    step = {'method': method, 'expectedUrl': url, 'before': before, 'status': 'starting'}
    record['activations'].append(step)
    save()
    opened = set()
    try:
        if method == 'Enter':
            if driver.js('return document.activeElement.href') != url:
                raise RuntimeError('Enter target is not the focused footer anchor')
            key(driver, '\ue007', settle=False)
        elif method == 'pointer':
            driver.click(driver.selector('footer.site-footer a[href="' + url + '"]'))
        else:
            raise RuntimeError('Unsupported footer activation method')
        wait_for(lambda: len(set(driver.call('GET', '/window/handles')) - handles) == 1, 15)
        opened = set(driver.call('GET', '/window/handles')) - handles
        driver.call('POST', '/window', {'handle': next(iter(opened))})
        actual = wait_target_ready(driver, url, step, wait_for)
        step['actualUrl'] = actual
        check_opened_target(url, actual)
        step['status'] = 'opened_exact_production_root'
    finally:
        # Close only new tabs created by this one test activation.
        opened |= set(driver.call('GET', '/window/handles')) - handles
        for handle in opened:
            driver.call('POST', '/window', {'handle': handle})
            driver.call('DELETE', '/window')
        driver.call('POST', '/window', {'handle': original})
        driver.settle()
        step['after'] = driver.js(SNAPSHOT_JS)
        save()
    check_opener(before, step['after'])
    step['status'] = 'verified_exact_root_and_unchanged_opener'
    save()


def capture_footer_checks(driver, report, save, out, dist, origin, viewports, wait_for, png_check):
    if tuple(viewports) != ((1440, 900), (1920, 1080)):
        raise RuntimeError('Footer evidence is limited to the existing two desktop viewports')
    report['footerCapturePlan'] = [f'{w}x{h}-footer-{name}' for w, h in viewports for name, _ in ROUTES]
    report['footerCaptures'] = []
    report['footerServedSources'] = {route: hashlib.sha256((dist / route).read_bytes()).hexdigest() for _, route in ROUTES}
    report['footerServedSources'].update({str(p.relative_to(dist)): hashlib.sha256(p.read_bytes()).hexdigest()
                                        for p in sorted((dist / 'assets').rglob('*')) if p.is_file()})
    save()
    for width, height in viewports:
        driver.cdp('Emulation.setDeviceMetricsOverride', {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': False})
        for name, route in ROUTES:
            record = {'name': f'{width}x{height}-footer-{name}', 'route': route, 'activations': [], 'keyboard': [], 'status': 'starting'}
            report['footerCaptures'].append(record)
            save()
            driver.call('POST', '/url', {'url': origin + '/' + route})
            driver.settle()
            driver.js("document.querySelector('footer.site-footer').scrollIntoView({block:'end'});")
            driver.settle()
            record['initial'] = wait_footer_stable(driver, wait_for)
            check_snapshot(record['initial'], origin, route, width, height)
            # Anchor the native Tab sequence at the unchanged predecessor only.
            driver.js("document.querySelector(arguments[0]).focus({preventScroll:true});", 'footer.site-footer a[href="' + GITHUB + '"]')
            for url, _ in LINKS:
                key(driver, '\ue004')
                snapshot = driver.js(SNAPSHOT_JS)
                record['keyboard'].append({'key': 'Tab', 'expected': url, 'snapshot': snapshot})
                save()
                check_snapshot(snapshot, origin, route, width, height, focused=url)
            key(driver, '\ue004', shift=True)
            snapshot = driver.js(SNAPSHOT_JS)
            record['keyboard'].append({'key': 'Shift+Tab', 'expected': LINKS[0][0], 'snapshot': snapshot})
            check_snapshot(snapshot, origin, route, width, height, focused=LINKS[0][0])
            image = base64.b64decode(driver.call('GET', '/screenshot'), validate=True)
            if not image.startswith(b'\x89PNG\r\n\x1a\n') or not png_check(image):
                raise RuntimeError('Footer screenshot is not a nonempty PNG')
            (out / (record['name'] + '.png')).write_bytes(image)
            record['screenshotSha256'] = hashlib.sha256(image).hexdigest()
            save()
            for index, (url, _) in enumerate(LINKS):
                if index:
                    key(driver, '\ue004')
                    check_snapshot(driver.js(SNAPSHOT_JS), origin, route, width, height, focused=url)
                activate(driver, url, 'Enter', record, save, wait_for)
            for url, _ in LINKS:
                activate(driver, url, 'pointer', record, save, wait_for)
            record['status'] = 'captured_for_human_review'
            save()
    if [r['name'] for r in report['footerCaptures']] != report['footerCapturePlan']:
        raise RuntimeError('Desktop footer screenshot plan is incomplete')
