"""PR-only visual evidence using the runner's existing Chrome and ChromeDriver.

No packages or browsers are downloaded. Browser security defaults are retained.
Screenshots are evidence for human review, not an automatic visual approval.
"""
from __future__ import annotations

import argparse
import base64
import functools
import hashlib
import http.server
import json
import os
from pathlib import Path
import shutil
import socket
import struct
import subprocess
import threading
import time
import urllib.request
import urllib.parse
import zlib

# User requested desktop-only, viewport-filling use on 2026-10-10.
# This does not request browser fullscreen privileges or send F11.
VIEWPORTS = [(1440, 900), (1920, 1080)]
ELEMENT = 'element-6066-11e4-a52e-4f735466cecf'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rect_inside(rect, area, tolerance=1):
    return (rect['width'] > 0 and rect['height'] > 0 and
            rect['x'] >= area['x'] - tolerance and rect['y'] >= area['y'] - tolerance and
            rect['x'] + rect['width'] <= area['x'] + area['width'] + tolerance and
            rect['y'] + rect['height'] <= area['y'] + area['height'] + tolerance)


def check_context_path(data):
    """Verify local ancestry independently from the separately labelled global navigation."""
    if data['route']['tree'] != 'c' or data['route']['node'] != 'pos:c:6dcc2ce43c02d908266f20':
        raise RuntimeError('Wrong AudioGoal challenge route')
    if data['localIds'] != data['expectedIds'] or any(t != 'c' for t in data['localTrees']):
        raise RuntimeError('Current challenge path differs from actual parent chain')
    if data['globalIds'] != data['expectedGlobalIds'] or data['globalSeparators'] != 0:
        raise RuntimeError('Global entry links imply a false ancestry chain')
    if data['labels'] != ['全局入口', '挑战–思路树 · 当前路径']:
        raise RuntimeError('Global entry and current path need distinct readable labels')
    if len(data['rows']) != 2 or data['rows'][0]['y'] + data['rows'][0]['height'] > data['rows'][1]['y'] + 1:
        raise RuntimeError('Context groups are not on separate lines')
    if not all(rect_inside(r, data['viewport']) for r in data['rows']):
        raise RuntimeError('Context rows are outside the screenshot')
    if not data['buttons'] or not all(x['uncovered'] and rect_inside(x['rect'], data['viewport']) and rect_inside(x['rect'], x['row']) and not x['clipped'] for x in data['buttons']):
        raise RuntimeError('Context link is clipped, covered or outside the screenshot')


def contrast_ratio(foreground, background):
    def luminance(rgb):
        channels = [v / 255 for v in rgb[:3]]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in channels]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    a, b = sorted((luminance(foreground), luminance(background)))
    return (b + .05) / (a + .05)


def png_has_visible_variation(image):
    """Reject single-color/near-empty Chrome RGB(A) screenshots without extra libraries."""
    width, height, depth, color = struct.unpack('>IIBB', image[16:26])
    if depth != 8 or color not in (2, 6) or image[28] != 0:
        raise RuntimeError('Unsupported screenshot PNG encoding')
    channels = 3 if color == 2 else 4
    compressed, offset = bytearray(), 8
    while offset < len(image):
        size = struct.unpack('>I', image[offset:offset + 4])[0]
        if image[offset + 4:offset + 8] == b'IDAT':
            compressed.extend(image[offset + 8:offset + 8 + size])
        offset += size + 12
    raw = zlib.decompress(compressed)
    stride = width * channels
    if len(raw) != height * (stride + 1):
        raise RuntimeError('Invalid screenshot pixel data')
    previous, colors, contrasts = bytearray(stride), set(), 0
    for y in range(height):
        start = y * (stride + 1)
        kind, row = raw[start], bytearray(raw[start + 1:start + 1 + stride])
        for x in range(stride):
            left = row[x - channels] if x >= channels else 0
            up = previous[x]
            upper_left = previous[x - channels] if x >= channels else 0
            if kind == 1:
                value = left
            elif kind == 2:
                value = up
            elif kind == 3:
                value = (left + up) // 2
            elif kind == 4:
                p = left + up - upper_left
                distances = [abs(p - left), abs(p - up), abs(p - upper_left)]
                value = [left, up, upper_left][distances.index(min(distances))]
            elif kind == 0:
                value = 0
            else:
                raise RuntimeError('Unknown PNG row filter')
            row[x] = (row[x] + value) % 256
        if y % 3 == 0:
            for x in range(0, stride, channels * 3):
                rgb = tuple(row[x:x + 3])
                colors.add(tuple(v // 16 for v in rgb))
                if max(rgb) - min(rgb) > 30 or max(rgb) < 180:
                    contrasts += 1
        previous = row
    return len(colors) >= 8 and contrasts >= 100


def command(*args):
    return subprocess.check_output(args, text=True).strip()


def wait_for(check, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(.1)
    raise TimeoutError('Browser condition did not become ready within bounded wait')


class Driver:
    def __init__(self, port):
        self.url = f'http://127.0.0.1:{port}'
        self.session = None

    def request(self, method, path, data=None):
        raw = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(self.url + path, data=raw, method=method,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=50) as response:
            value = json.load(response)['value']
        if isinstance(value, dict) and value.get('error'):
            raise RuntimeError(value['error'] + ': ' + value.get('message', ''))
        return value

    def call(self, method, path, data=None):
        return self.request(method, '/session/' + self.session + path, data)

    def js(self, script, *args):
        return self.call('POST', '/execute/sync', {'script': script, 'args': list(args)})

    def click(self, element):
        self.call('POST', '/element/' + element[ELEMENT] + '/click', {})

    def selector(self, selector):
        return self.call('POST', '/element', {'using': 'css selector', 'value': selector})

    def settle(self):
        self.call('POST', '/execute/async', {'script': 'var done=arguments[arguments.length-1];document.fonts.ready.then(()=>requestAnimationFrame(()=>requestAnimationFrame(()=>done(true))));', 'args': []})

    def cdp(self, cmd, params):
        return self.call('POST', '/goog/cdp/execute', {'cmd': cmd, 'params': params})


def free_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dist', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    if out.exists() and any(out.iterdir()):
        raise RuntimeError('Screenshot output directory must be fresh and empty')
    out.mkdir(parents=True, exist_ok=True)
    dist = args.dist.resolve()
    expected = os.environ.get('EXPECTED_HEAD', '')
    head = command('git', 'rev-parse', 'HEAD')
    if not expected or head != expected:
        raise RuntimeError('Exact pull-request head binding is required')
    report = {'head': head, 'eventSha': os.environ.get('GITHUB_SHA'), 'tree': command('git', 'rev-parse', 'HEAD^{tree}'),
              'htmlSha256': sha(dist / 'research/navigation/index.html'),
              'scienceSha256': sha(dist / 'research/navigation/product-data.json'),
              'visualAcceptance': 'pending_human_review', 'captures': [], 'status': 'starting',
              'reviewScope': 'user_requested_desktop_only_2026-10-10',
              'browserFullscreenRequested': False}
    report['frontendSources'] = {name: sha(name) for name in ('assets/navigation-product.js', 'assets/navigation-product.css', 'scripts/navigation_product.py')}
    report['servedFiles'] = {str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'research/navigation').rglob('*')) if p.is_file()}
    report['servedFiles'].update({str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'assets').glob('navigation-*.js'))})
    report['servedFiles']['assets/navigation-product.css'] = sha(dist / 'assets/navigation-product.css')
    driver = None
    process = None
    server = None
    logs = (out / 'chromedriver.log').open('w')

    def save():
        (out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    def capture(name, require_tree=True, require_overview=False, require_flow=False):
        driver.settle()
        data = driver.js('''return {viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
          loadState:document.querySelector('[data-load-state]')?.dataset.loadState,
          route:window.NavigationProductApp?.getState().route,
          fonts:document.fonts.status, ready:!!window.NavigationProductApp,
          fallbackHidden:document.getElementById('np-static-reading')?.hidden,
          bounds:[...document.querySelectorAll('#np-workspace,#np-tree-scroll,.np-reading-pane,#np-tree .np-node-row')].map(e=>{let r=e.getBoundingClientRect();return {id:e.id,position:e.closest('[data-position]')?.dataset.position,text:e.textContent.slice(0,180),x:r.x,y:r.y,width:r.width,height:r.height};}),
          nodeCount:document.querySelectorAll('#np-tree [role=treeitem]').length,
          focus:document.activeElement?.id, bodyWidth:document.body.scrollWidth};''')
        data['readingVisibility'] = driver.js('''function rect(e){if(!e)return null;let r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
          let a=NavigationProductApp,b=a.getBundle(),root=b.researchMap.roots[0];
          function color(value){let m=/^rgba?\\(([^)]+)\\)$/.exec(value);if(!m)return null;let v=m[1].split(',').map(Number);if(![3,4].includes(v.length)||v.some(n=>!Number.isFinite(n))||v.slice(0,3).some(n=>n<0||n>255))return null;return {rgb:v.slice(0,3),alpha:v.length===4?v[3]:1};}
          function foreground(e){let c=color(getComputedStyle(e).color);return c&&c.alpha===1?c.rgb:[];}
          function background(e){while(e){let c=color(getComputedStyle(e).backgroundColor);if(!c)return [];if(c.alpha===1)return c.rgb;if(c.alpha!==0)return [];e=e.parentElement;}return [255,255,255];}
          function opaqueVisible(e){while(e){let s=getComputedStyle(e);if(Number(s.opacity)!==1||s.visibility!=='visible'||s.display==='none')return false;e=e.parentElement;}return true;}
          let reader=document.getElementById('np-detail-scroll'),readerRect=rect(reader),heading=reader.querySelector('.np-reader-heading'),headingRect=rect(heading),contentTop=readerRect.y;
          if(heading&&['sticky','fixed'].includes(getComputedStyle(heading).position)&&headingRect.height>0)contentTop=Math.max(contentTop,headingRect.y+headingRect.height);
          let contentRect={x:readerRect.x,y:contentTop,width:readerRect.width,height:Math.max(0,readerRect.y+readerRect.height-contentTop)};
          function uncovered(e){let r=e.getBoundingClientRect();return [[.5,.5],[.05,.05],[.95,.05],[.05,.95],[.95,.95]].every(([fx,fy])=>{let hit=document.elementFromPoint(r.x+r.width*fx,r.y+r.height*fy);return hit&&(hit===e||e.contains(hit));});}
          return {canvas:rect(document.getElementById('np-tree-scroll')),reader:readerRect,readerContent:contentRect,readerHeading:headingRect,
            roots:[root,...b.positions[root].childIds].map(id=>{let row=document.getElementById('np-node-'+id)?.querySelector(':scope > .np-node-row'),label=row?.querySelector('.np-node-label');return {id,entity:b.positions[id].entityId,row:rect(row),label:rect(label),text:label?.textContent,opaqueVisible:label?opaqueVisible(label):false,clipped:label?label.scrollHeight>label.clientHeight+1||label.scrollWidth>label.clientWidth+1:true,foreground:label?foreground(label):[],background:label?background(label):[]};}),
            mechanism:rect(document.querySelector('.np-reading-pane .np-method-mechanism')),
            flow:[...document.querySelectorAll('.np-reading-pane .np-method-flow dd')].map(e=>({text:e.textContent,rect:rect(e),uncovered:uncovered(e)}))};''')
        image = base64.b64decode(driver.call('GET', '/screenshot'), validate=True)
        if not image.startswith(b'\x89PNG\r\n\x1a\n'):
            raise RuntimeError('Screenshot is not PNG')
        png_width, png_height = struct.unpack('>II', image[16:24])
        if [png_width, png_height] != [data['viewport']['width'] * data['viewport']['dpr'], data['viewport']['height'] * data['viewport']['dpr']]:
            raise RuntimeError('PNG dimensions do not match measured CSS viewport and DPR')
        (out / (name + '.png')).write_bytes(image)
        data.update(name=name, screenshotSha256=hashlib.sha256(image).hexdigest(), pixelVariation=png_has_visible_variation(image))
        selector = driver.js("var n=[...document.querySelectorAll('#np-tree .np-node-label')].find(e=>/[\\u3400-\\u9fff]/.test(e.textContent));return n?'[id='+JSON.stringify(n.closest('[id]').id)+'] > .np-node-row .np-node-label':null")
        if not selector:
            raise RuntimeError('No Chinese label available to verify actual rendered font')
        root_node = driver.cdp('DOM.getDocument', {'depth': 1})['root']['nodeId']
        label_node = driver.cdp('DOM.querySelector', {'nodeId': root_node, 'selector': selector})['nodeId']
        data['renderedFonts'] = driver.cdp('CSS.getPlatformFontsForNode', {'nodeId': label_node})['fonts']
        if not any(f.get('glyphCount', 0) > 0 for f in data['renderedFonts']):
            raise RuntimeError('Chinese label has no rendered font glyphs')
        data['console'] = driver.call('POST', '/log', {'type': 'browser'})
        data['networkFailures'] = []
        for entry in driver.call('POST', '/log', {'type': 'performance'}):
            message = json.loads(entry['message'])['message']
            if message['method'] == 'Network.loadingFailed':
                p = message['params']
                data['networkFailures'].append({'type': p.get('type'), 'error': p.get('errorText'), 'cancelled': p.get('canceled', False)})
            elif message['method'] == 'Network.responseReceived' and message['params']['response']['status'] >= 400:
                response = message['params']['response']
                data['networkFailures'].append({'status': response['status'], 'path': urllib.parse.urlsplit(response['url']).path})
        report['captures'].append(data)
        save()
        if not data['ready'] or data['loadState'] != 'ready' or not data['fallbackHidden'] or not data['nodeCount'] or data['fonts'] != 'loaded':
            raise RuntimeError('Blank, unready, or font-pending capture')
        if not data['pixelVariation']:
            raise RuntimeError('Screenshot has insufficient nonblank pixel variation')
        if any(e.get('level') == 'SEVERE' for e in data['console']):
            raise RuntimeError('Browser console contains severe errors')
        if data['networkFailures']:
            raise RuntimeError('Candidate resource request failed')
        visible = [r for r in data['bounds'] if r['width'] > 0 and r['height'] > 0 and r['x'] < data['viewport']['width'] and r['y'] < data['viewport']['height'] and r['x'] + r['width'] > 0 and r['y'] + r['height'] > 0]
        if require_tree and not any(r.get('position') for r in visible):
            raise RuntimeError('No actual tree node visible in captured viewport')
        if not require_tree and not any(r.get('id') == 'np-detail-scroll' for r in visible):
            raise RuntimeError('Reader is not visible in reader screenshot')
        viewport = {'x': 0, 'y': 0, 'width': data['viewport']['width'], 'height': data['viewport']['height']}
        if require_overview:
            roots = data['readingVisibility']['roots']
            if len(roots) != 3:
                raise RuntimeError('Overview must expose General goal and both original main branches')
            for node in roots:
                if not node['row'] or not rect_inside(node['row'], viewport) or not rect_inside(node['row'], data['readingVisibility']['canvas']):
                    raise RuntimeError('Overview root or main branch is outside the initial visible canvas: ' + node['id'])
                if node['clipped']:
                    raise RuntimeError('Overview main heading text is clipped: ' + node['id'])
                if not node['opaqueVisible'] or len(node['foreground']) != 3 or len(node['background']) != 3 or contrast_ratio(node['foreground'], node['background']) < 4.5:
                    raise RuntimeError('Overview main heading contrast is below 4.5:1: ' + node['id'])
        if require_flow:
            reader = data['readingVisibility']['readerContent']
            visible_flow = [item for item in data['readingVisibility']['flow'] if item['text'].strip() and item['uncovered'] and rect_inside(item['rect'], viewport) and rect_inside(item['rect'], reader)]
            if not visible_flow:
                raise RuntimeError('Method screenshot does not show any complete actual mechanism field inside the reader')

    try:
        binary = shutil.which('google-chrome') or shutil.which('google-chrome-stable')
        executable = shutil.which('chromedriver')
        if not executable and os.environ.get('CHROMEWEBDRIVER'):
            candidate = Path(os.environ['CHROMEWEBDRIVER']) / 'chromedriver'
            if candidate.is_file():
                executable = str(candidate)
        if not binary or not executable:
            raise RuntimeError('Preinstalled Chrome and ChromeDriver are required; no download fallback')
        report['chromeVersion'] = command(binary, '--version')
        report['driverVersion'] = command(executable, '--version')
        font_tool = shutil.which('fc-list')
        if not font_tool:
            raise RuntimeError('Cannot verify installed Chinese fonts')
        report['chineseFonts'] = sorted(set(command(font_tool, ':lang=zh', 'family').splitlines()))
        if not report['chineseFonts']:
            raise RuntimeError('No installed Chinese font; do not treat missing glyphs as visual success')
        font_version = command('dpkg-query', '-W', '-f=${Version}', 'fonts-noto-cjk')
        if font_version != '1:20230817+repack1-3':
            raise RuntimeError('Chinese font package version differs from pinned visual fixture')
        font_files = [Path(p) for p in command('dpkg-query', '-L', 'fonts-noto-cjk').splitlines()
                      if p.startswith('/usr/share/fonts/') and Path(p).is_file()]
        if not font_files:
            raise RuntimeError('Pinned package has no installed font files')
        report['fontPackage'] = {'name': 'fonts-noto-cjk', 'version': font_version,
            'packageSha256': '7d64b985f6fe128c99eae5610d5c047338e572bdcfb2bb09736be01b824a7f6c',
            'source': 'https://packages.ubuntu.com/noble/all/fonts-noto-cjk/download',
            'license': 'SIL Open Font License 1.1',
            'copyrightSha256': sha('/usr/share/doc/fonts-noto-cjk/copyright'),
            'files': {str(p): sha(p) for p in sorted(font_files)}}
        server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(dist)))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        port = free_port()
        process = subprocess.Popen([executable, f'--port={port}', '--allowed-ips=127.0.0.1'], stdout=logs, stderr=subprocess.STDOUT)
        driver = Driver(port)
        def available():
            if process.poll() is not None:
                raise RuntimeError('ChromeDriver exited before startup')
            try:
                return driver.request('GET', '/status').get('ready')
            except (OSError, ValueError):
                return False
        wait_for(available, 15)
        session = driver.request('POST', '/session', {'capabilities': {'alwaysMatch': {
            'browserName': 'chrome', 'goog:chromeOptions': {'binary': binary, 'args': ['--headless=new']},
            'goog:loggingPrefs': {'browser': 'ALL', 'performance': 'ALL'}}}})
        driver.session = session['sessionId']
        driver.cdp('DOM.enable', {})
        driver.cdp('CSS.enable', {})
        driver.call('POST', '/timeouts', {'script': 45000, 'pageLoad': 60000, 'implicit': 0})
        base = f'http://127.0.0.1:{server.server_port}/research/navigation/'
        for width, height in VIEWPORTS:
            driver.call('POST', '/url', {'url': 'about:blank'})
            # Runner-owned DevTools emulation avoids Chrome's minimum outer window width.
            driver.cdp('Emulation.setDeviceMetricsOverride', {'width': width, 'height': height, 'deviceScaleFactor': 1, 'mobile': False})
            if driver.js('return [innerWidth,innerHeight]') != [width, height]:
                raise RuntimeError('Requested CSS viewport could not be established')
            driver.call('POST', '/url', {'url': base})
            wait_for(lambda: driver.js("return !!window.NavigationProductApp && document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
            prefix = f'{width}x{height}'
            capture(prefix + '-01-overview', require_overview=True)
            # Select and expand through actual controls. No test route or bundle is injected.
            task = driver.js("var b=NavigationProductApp.getBundle();var p=Object.values(b.researchMap.positions).find(p=>p.sourceScopeId==='task:category-objectnav'&&p.sourceRootPositionIds);return document.getElementById('np-node-'+p.id).querySelector('.np-node-toggle');")
            driver.click(task)
            driver.settle()
            root_origin = driver.js("var a=NavigationProductApp;return a.getState().originTrail.find(e=>e.route.tree==='g'&&e.route.node===a.getBundle().researchMap.roots[0]);")
            if not root_origin:
                raise RuntimeError('Expanded task did not preserve global origin')
            capture(prefix + '-02-task-expanded')
            target = driver.js("var b=NavigationProductApp.getBundle();return Object.values(b.positions).find(p=>p.tree==='g'&&p.sourceScopeId==='task:category-objectnav'&&p.paperId==='vlfm'&&p.kind==='pipeline_recipe').id;")
            for _ in range(8):
                element = driver.js("return document.getElementById('np-node-'+arguments[0])?.querySelector('.np-node-label')||null", target)
                if element:
                    break
                toggle = driver.js("var b=NavigationProductApp.getBundle(),p=b.positions[arguments[0]],a=[];while(p){a.unshift(p.id);p=b.positions[p.parentId]}for(var id of a){var n=document.getElementById('np-node-'+id);if(n&&n.getAttribute('aria-expanded')==='false')return n.querySelector('.np-node-toggle')}return null", target)
                if not toggle:
                    raise RuntimeError('Method has no reachable rendered ancestor control')
                driver.click(toggle)
                driver.settle()
            if not element:
                raise RuntimeError('Method control did not become reachable')
            driver.click(element)
            wait_for(lambda: driver.js("var a=NavigationProductApp,p=a.getBundle().positions[arguments[0]],s=document.querySelector('.np-reading-pane .np-method-mechanism');return a.getState().route.node===p.id && a.getState().route.paper===p.paperId && a.getState().route.version===p.versionId && a.getContent().ready(p.entityId) && s?.dataset.mechanismEntity===p.entityId && s.querySelectorAll('.np-method-flow dd').length>0", target))
            capture(prefix + '-03-method-reader')
            if driver.js('return NavigationProductApp.getState().route.paper') != 'vlfm':
                raise RuntimeError('Selected method identity mismatch')
            driver.js("document.querySelector('.np-reading-pane .np-method-flow').scrollIntoView({block:'start',inline:'nearest'});")
            capture(prefix + '-03b-reader-visible', require_tree=False, require_flow=True)
            driver.js("document.getElementById('np-workspace').scrollIntoView({block:'start'});")
            driver.click(driver.selector('[data-tree-tab="g"]'))
            driver.settle()
            capture(prefix + '-04-return', require_overview=True)
            if driver.js('var a=NavigationProductApp;return a.getState().route.node===a.getBundle().researchMap.roots[0]') is not True:
                raise RuntimeError('Return did not restore the global root')
            restored = driver.js("var e=document.getElementById('np-tree-scroll');return {top:e.scrollTop,left:e.scrollLeft,window:scrollY,focus:document.activeElement?.dataset.position||document.activeElement?.id};")
            bucket = root_origin['bucket']
            if restored != {'top': bucket['treeScrollByTree']['g'], 'left': bucket.get('treeScrollLeftByTree', {}).get('g', 0), 'window': bucket['windowScroll'], 'focus': bucket['focusTarget']}:
                raise RuntimeError('Return changed saved overview scroll or focus')
            report.setdefault('returnChecks', []).append({'viewport': prefix, 'actual': restored})
            route_before = driver.js('return NavigationProductApp.getState().route')
            scale_before = driver.js('return NavigationProductModel.getBucket(NavigationProductApp.getState()).graphScale')
            driver.click(driver.selector('#np-zoom-out'))
            capture(prefix + '-05-zoom-out')
            if driver.js('return NavigationProductApp.getState().route') != route_before:
                raise RuntimeError('Zoom changed evidence route')
            if not driver.js("return NavigationProductModel.getBucket(NavigationProductApp.getState()).graphScale<arguments[0]&&document.activeElement.id==='np-zoom-out'", scale_before):
                raise RuntimeError('Zoom did not change scale or retain its active control')
            driver.click(driver.selector('#np-zoom-reset'))
            if not driver.js("return NavigationProductModel.getBucket(NavigationProductApp.getState()).graphScale===1&&document.activeElement.id==='np-zoom-reset'"):
                raise RuntimeError('Zoom reset did not restore scale and control focus')
            # Cold canonical CI deep link, then actual global entry and browser Back.
            ci_target = 'pos:c:6dcc2ce43c02d908266f20'
            ci_hash = driver.js("var a=NavigationProductApp;return NavigationProductModel.encodeRoute(NavigationProductModel.routeForPosition(a.getBundle(),a.getState().route,arguments[0]));", ci_target)
            driver.call('POST', '/url', {'url': 'about:blank'})
            driver.call('POST', '/url', {'url': base + ci_hash})
            wait_for(lambda: driver.js("var a=window.NavigationProductApp;if(!a)return false;var p=a.getBundle().positions[arguments[0]];return a.getState().route.node===p.id&&a.getContent().ready(p.entityId)&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready';", ci_target))
            driver.settle()
            context = driver.js("""
                var a=NavigationProductApp,b=a.getBundle(),r=a.getState().route,p=b.positions[r.node],expected=[];
                while(p){expected.unshift(p.id);p=p.parentId?b.positions[p.parentId]:null;}
                var host=document.getElementById('np-global-context'),entry=host.querySelector('[data-path-kind="global-entry"]'),local=host.querySelector('[data-path-kind="local-ancestry"]');
                function rect(n){var q=n.getBoundingClientRect();return {x:q.x,y:q.y,width:q.width,height:q.height};}
                function ids(n){return Array.from(n.querySelectorAll('[data-context-position]'),x=>x.dataset.contextPosition);}
                var root=b.researchMap.roots[0],scope=b.researchMap.canonicalScopePositionIds[r.scope];
                return {route:r,expectedIds:expected,localIds:ids(local),localTrees:ids(local).map(id=>b.positions[id].tree),globalIds:ids(entry),expectedGlobalIds:scope&&scope!==root?[root,scope]:[root],globalSeparators:entry.querySelectorAll('.np-path-separator').length,labels:[entry,local].map(n=>n.querySelector('.np-context-label').textContent),rows:[entry,local].map(rect),viewport:{x:0,y:0,width:innerWidth,height:innerHeight},buttons:Array.from(host.querySelectorAll('[data-context-position]'),n=>{var q=rect(n),points=[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]],uncovered=points.every(v=>{var hit=document.elementFromPoint(q.x+q.width*v[0],q.y+q.height*v[1]);return !!hit&&(hit===n||n.contains(hit));});return {id:n.dataset.contextPosition,text:n.textContent,rect:q,row:rect(n.closest('[data-path-kind]')),clipped:n.scrollWidth>n.clientWidth+1||n.scrollHeight>n.clientHeight+1,uncovered:uncovered};})};
            """)
            check_context_path(context)
            report.setdefault('contextPathChecks', []).append({'viewport': prefix, 'evidence': context})
            capture(prefix + '-06-audiogoal-ci-path')
            driver.click(driver.selector('[data-path-kind="global-entry"] [data-context-position]'))
            driver.settle()
            capture(prefix + '-07-ci-return-overview', require_overview=True)
            if not driver.js("var a=NavigationProductApp,r=a.getState().route;return r.tree==='g'&&r.node===a.getBundle().researchMap.roots[0];"):
                raise RuntimeError('Challenge global entry did not restore the global root route')
            driver.call('POST', '/back', {})
            wait_for(lambda: driver.js('return NavigationProductApp.getState().route.node===arguments[0]', ci_target))
            driver.settle()
            if driver.js('return NavigationProductApp.getState().route') != context['route']:
                raise RuntimeError('Back from global entry changed the challenge identity')
            report['contextPathChecks'][-1]['backRouteRestored'] = True
        report['status'] = 'captured_for_human_review'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)[:2000]
        if driver and driver.session:
            try:
                (out / 'failure.png').write_bytes(base64.b64decode(driver.call('GET', '/screenshot')))
                report['failureConsole'] = driver.call('POST', '/log', {'type': 'browser'})
            except Exception as diagnostic_error:
                report['diagnosticError'] = type(diagnostic_error).__name__
        raise
    finally:
        save()
        if driver and driver.session:
            try:
                driver.call('DELETE', '')
            except Exception:
                pass
        if process:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=5)
        if server:
            server.shutdown()
            server.server_close()
        logs.close()


if __name__ == '__main__':
    main()
