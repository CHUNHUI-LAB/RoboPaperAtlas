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

VIEWPORTS = [(1440, 900), (1180, 757), (659, 757), (390, 844)]
ELEMENT = 'element-6066-11e4-a52e-4f735466cecf'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


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
              'visualAcceptance': 'pending_human_review', 'captures': [], 'status': 'starting'}
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

    def capture(name, require_tree=True):
        driver.settle()
        data = driver.js('''return {viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
          loadState:document.querySelector('[data-load-state]')?.dataset.loadState,
          route:window.NavigationProductApp?.getState().route,
          fonts:document.fonts.status, ready:!!window.NavigationProductApp,
          fallbackHidden:document.getElementById('np-static-reading')?.hidden,
          bounds:[...document.querySelectorAll('#np-workspace,#np-tree-scroll,.np-reading-pane,#np-tree .np-node-row')].map(e=>{let r=e.getBoundingClientRect();return {id:e.id,position:e.closest('[data-position]')?.dataset.position,text:e.textContent.slice(0,180),x:r.x,y:r.y,width:r.width,height:r.height};}),
          nodeCount:document.querySelectorAll('#np-tree [role=treeitem]').length,
          focus:document.activeElement?.id, bodyWidth:document.body.scrollWidth};''')
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
            capture(prefix + '-01-overview')
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
            driver.js("document.getElementById('np-detail-scroll').scrollIntoView({block:'start'});")
            capture(prefix + '-03b-reader-visible', require_tree=False)
            driver.js("document.getElementById('np-workspace').scrollIntoView({block:'start'});")
            driver.click(driver.selector('[data-tree-tab="g"]'))
            driver.settle()
            capture(prefix + '-04-return')
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
