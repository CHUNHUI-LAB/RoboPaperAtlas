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
import math
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


TASK_INDEX = [('task:audiogoal', 'AudioGoal', '声音→声源'), ('task:audiopointgoal', 'AudioPointGoal', '声音＋位置→到达'), ('task:aerial-visual-object-search', 'AVOS', '图文→飞行搜索'), ('task:comon', 'CoMON', '特权协作→多目标'), ('task:ddn', 'DDN', '需求→可用物体'), ('task:goat', 'GOAT', '类别/实例图/语言序列'), ('task:hieranav', 'HieraNav', '多级约束→物体'), ('task:imagenav', 'ImageNav', '地点图→地点'), ('task:instanceimagenav', 'InstanceImageNav', '实例图→同一物'), ('task:ivln', 'IVLN', '同环境多段指令'), ('task:lamon', 'LaMoN', '逐个描述→对象'), ('task:multion', 'MultiON', '有序目标→逐个找'), ('task:namo', 'NAMO', '移障→创造通路'), ('task:ndh', 'NDH', '对话历史→进展'), ('task:category-objectnav', 'ObjectNav', '类别→任一实例'), ('task:pointnav', 'PointNav', '坐标→位置'), ('task:remote-referent-navigation', 'REVERIE式', '描述→到达并指认'), ('task:roomnav', 'RoomNav', '区域→进入区域'), ('task:soon', 'SOON', '物体及周边描述→定位'), ('task:vln', 'VLN', '路线语句→执行'), ('task:person-finding-following', '找人并跟随', '人物→持续跟随'), ('task:language-objectnav', '语言物体目标', '描述→合格对象')]


CHALLENGE_LABELS = {'legacy:ci_search_unknown_target': '未见目标，怎样少走冤路？', 'legacy:ci_generalize_environments': '路线更多，新屋仍难适应？', 'legacy:ci_instruction_progress': '指令哪段真正完成？', 'legacy:ci_recover_route_error': '走错后如何少代价纠正？', 'legacy:ci_candidate_verification': '看见候选，为何不能停？', 'legacy:ci_semantic_commitment': '语义有分歧，单标签丢什么？', 'legacy:ci_dynamic_revisit': '旧地图哪部分仍可信？', 'legacy:ci_negative_evidence': '未找到，何时算可信反证？', 'legacy:ci_long_horizon_evidence': '跨调用如何保留证据与待办？', 'methods:ci_ground_dynamic_plan': '未知布局为何难预先完整规划？', 'methods:ci_hierarchical_spatial_query': '扁平检索为何丢失楼层房间？', 'methods:ci_spatial_language_grounding': '仅图文匹配，怎样找两地标之间？', 'methods:ci_compact_relational_memory': '逐点语义冗余且缺少对象关系'}


RELATION_EVIDENCE_ELEMENT_JS = "var e=[...document.querySelectorAll('[data-task-relation]')].find(n=>n.dataset.taskRelation===arguments[0]),s=arguments[1];if(s.kind==='heading')return e.querySelector('strong');if(s.kind==='locator')return [...e.querySelectorAll('p')].find(n=>n.textContent===s.text);var a=[...e.querySelectorAll('[data-task-relation-source]')].find(n=>n.dataset.taskRelationSource===s.id);if(!a)throw Error('Exact source anchor missing');if(s.kind==='source')return a;var status=a.nextElementSibling;if(!status||status.tagName!=='SPAN'||status.parentElement!==a.parentElement)throw Error('Exact source status sibling missing');return status;"


VISUAL_GEOMETRY = r"""
function rect(e){var r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
function color(v){var m=/^rgba?\(([^)]+)\)$/.exec(v);if(!m)return null;var n=m[1].split(',').map(Number);if(![3,4].includes(n.length)||n.some(x=>!Number.isFinite(x))||n.slice(0,3).some(x=>x<0||x>255))return null;return {rgb:n.slice(0,3),alpha:n.length===4?n[3]:1};}
function bg(e){while(e){var c=color(getComputedStyle(e).backgroundColor);if(!c)return [];if(c.alpha===1)return c.rgb;if(c.alpha!==0)return [];e=e.parentElement;}return [255,255,255];}
function box(e){var r=rect(e),style=getComputedStyle(e),fg=color(style.color),opaque=true,unscaled=true;for(var n=e;n;n=n.parentElement){var cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility!=='visible'||Number(cs.opacity)!==1)opaque=false;var transform=cs.transform;if(transform!=='none'){try{if(!new DOMMatrixReadOnly(transform).isIdentity)unscaled=false;}catch(_){unscaled=false;}}if(!['normal','1',''].includes(String(cs.zoom)))unscaled=false;}
var visible=opaque&&[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!hit&&(hit===e||e.contains(hit));});
return {text:e.textContent,rect:r,visible:visible,opaque:opaque,unscaled:unscaled,fontSize:parseFloat(style.fontSize),foreground:fg&&fg.alpha===1?fg.rgb:[],background:bg(e),clipped:e.scrollWidth>e.clientWidth+1||e.scrollHeight>e.clientHeight+1};}
"""


def check_reading_home(data):
    if not data['home'] or not data['panelsHidden'] or data['route']['paper'] or data['route']['version']:
        raise RuntimeError('Default reading overview is hidden or implicitly selects paper evidence')
    if data['windowScroll'] != 0 or data['landingScroll'] != 0 or data['scale'] != 1:
        raise RuntimeError('Initial overview was scrolled or shrunk to pass')
    actual = [(x['id'], x['name']['text'], x['contract']['text']) for x in data['entries']]
    if actual != TASK_INDEX:
        raise RuntimeError('Default overview lost or altered a reviewed task contract')
    boxes = data['headings'] + [v for e in data['entries'] for v in (e['name'], e['contract'])]
    if len(data['headings']) != 3 or not all(x['visible'] and x['opaque'] and x['unscaled'] and len(x['foreground']) == 3 and len(x['background']) == 3 and contrast_ratio(x['foreground'], x['background']) >= 4.5 and not x['clipped'] and x['fontSize'] >= 15 and rect_inside(x['rect'], data['viewport']) and rect_inside(x['rect'], data['landing']) for x in boxes):
        raise RuntimeError('All22 contracts and three headings must be fully readable on the unscrolled default screen')


PARALLEL_ROOT_SELECTOR = ':scope > [role=tree] > [role=treeitem]'


def check_parallel_scope(data):
    if data['scope'] != data['expectedScope'] or data['home']:
        raise RuntimeError('Task did not enter its own parallel reading view')
    if [x['tree'] for x in data['panels']] != ['l', 'c']:
        raise RuntimeError('Task must retain both literature and challenge forests')
    for panel in data['panels']:
        if panel['scope'] != data['scope'] or panel['roots'] != panel['expectedRoots']:
            raise RuntimeError('Parallel forest identity differs from original scope roots')
        if not panel['headingVisible'] or not rect_inside(panel['heading'], data['viewport']):
            raise RuntimeError('Both task tree headings must be visible together')
        visible_children = [x for x in panel['children'] if x['visible'] and x['opaque'] and rect_inside(x['rect'], data['viewport']) and rect_inside(x['rect'], panel['rect'])]
        if panel['expectedChildren'] and not visible_children:
            raise RuntimeError('Task forest with recorded descendants shows only a folded root')


def check_graphical_map(data):
    """Require actual source-parent geometry, independently of hidden legacy trees."""
    if not data['mapVisible'] or len(data['nodes']) != 39:
        raise RuntimeError('Default overview is not the visible39-node source graph')
    ids = [n['id'] for n in data['nodes']]
    if len(set(ids)) != 39 or sorted(ids) != sorted(data['expectedIds']):
        raise RuntimeError('Overview mapped identities differ from original source positions')
    if sorted((e['parent'], e['child']) for e in data['edges']) != sorted(map(tuple, data['expectedEdges'])):
        raise RuntimeError('Overview parent edges differ from source containment')
    if len(data['edges']) != 38 or any(not e['visible'] or not math.isfinite(e['length']) or e['length'] <= 0 or not e['endpointsMatch'] or not e['inBounds'] or not e['uncovered'] or contrast_ratio(e['foreground'], e['background']) < 3 for e in data['edges']):
        raise RuntimeError('Source parent lines are missing, hidden or detached from their nodes')
    if len(data['challenges']) != 13 or sorted(n['entity'] for n in data['challenges']) != sorted(data['expectedChallengeLabels']):
        raise RuntimeError('Default overview lost a challenge entry')
    for n in data['nodes']:
        if not n['visible'] or not n['opaque'] or not n['unscaled'] or not rect_inside(n['rect'], data['viewport']) or not rect_inside(n['rect'], data['map']):
            raise RuntimeError('A source node is hidden, scaled or outside the default map')
    d = data['directoryTitle']
    if not d['visible'] or not d['opaque'] or d['clipped'] or d['fontSize'] < 15 or len(d['foreground']) != 3 or len(d['background']) != 3 or contrast_ratio(d['foreground'], d['background']) < 4.5:
        raise RuntimeError('Original task directory title is not readable')
    for n in data['challenges']:
        b = n['label']
        if n['entity'] not in data['expectedChallengeLabels'] or b['text'] != data['expectedChallengeLabels'][n['entity']]:
            raise RuntimeError('Challenge short label differs from the reviewed presentation')
        if n['position'] != n['challengeOpen'] or n['entity'] != n['expectedEntity']:
            raise RuntimeError('Challenge button identity differs from its real source position')
        if n['title'] != n['expectedTitle'] or not n['aria'].startswith(n['expectedTitle']):
            raise RuntimeError('Challenge full source identity was lost')
        if not b['visible'] or not b['opaque'] or not b['unscaled'] or b['clipped'] or b['fontSize'] < 15 or len(b['foreground']) != 3 or len(b['background']) != 3 or contrast_ratio(b['foreground'], b['background']) < 4.5 or not rect_inside(b['rect'], data['viewport']) or not rect_inside(b['rect'], data['map']):
            raise RuntimeError('A challenge label is clipped, covered, unreadable or off screen')
    if len(data['tasks']) != 22 or any(n['scope'] != n['expectedScope'] or n['position'] != n['expectedPosition'] for n in data['tasks']):
        raise RuntimeError('Task control is mapped to another source position')
    actual = sorted((e['id'], e['from'], e['to'], e['type']) for e in data['relations'])
    expected = sorted(tuple(e) for e in data['expectedRelations'])
    if len(actual) != 7 or actual != expected or any(not e['visible'] or not math.isfinite(e['length']) or e['length'] <= 0 or not e['endpointsMatch'] or not e['inBounds'] or not e['uncovered'] or not e['ownHits'] or contrast_ratio(e['foreground'], e['background']) < 3 for e in data['relations']):
        raise RuntimeError('Typed relationship lines lost their exact scientific identity or geometry')


def check_relation_evidence(data, expected):
    if data['id'] != expected['id'] or data['type'] != expected['relationType'] or data['from'] != expected['from'] or data['to'] != expected['to']:
        raise RuntimeError('Relationship selection opened another relationship')
    if not data['open'] or data['focus'] != data.get('expectedFocus', 'np-map-relation-evidence-' + expected['id']) or data['route'] != data['beforeRoute']:
        raise RuntimeError('Relationship evidence lost disclosure, focus or original route')
    actual = [(s['id'], s['url'], s['version'], s['status']) for s in data['sources']]
    wanted = [(s['sourceId'], s['url'], s['versionId'], s['versionStatus']) for s in expected['sourceRefs']]
    if actual != wanted:
        raise RuntimeError('Relationship source IDs, URLs or version status differ from the original inventory')
    if any(loc['locator'] not in data['text'] for loc in expected['locators']):
        raise RuntimeError('Relationship original source locator was omitted')
    if len(data['visibleProofs']) != 1 + len(expected['locators']) + 2 * len(expected['sourceRefs']):
        raise RuntimeError('Relationship evidence visibility checks are incomplete')
    for proof in data['visibleProofs']:
        if proof.get('expectedText') is not None and proof['text'] != proof['expectedText']:
            raise RuntimeError('Visible relationship source version status contradicts the original inventory')
        if not proof['visible'] or not proof['opaque'] or not proof['unscaled'] or proof['fontSize'] < 15 or proof['clipped'] or len(proof['foreground']) != 3 or len(proof['background']) != 3 or contrast_ratio(proof['foreground'], proof['background']) < 4.5 or not rect_inside(proof['rect'], proof['viewport']):
            raise RuntimeError('Relationship source or locator is unreadable, hidden or off screen')


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


COLD_RESTORE_SNAPSHOT_JS = r"""
var landing=document.getElementById('np-reading-landing'),active=document.activeElement,
    api=window.NavigationProductApp,model=window.NavigationProductModel,runtime=api.getState(),
    persisted=window.history.state&&window.history.state[model.KEY];
function bucketRecord(value){
  if(!value||!value.route||!value.contexts)return null;
  var bucket=value.contexts[model.contextKey(value.route)];if(!bucket)return null;
  return {contextKey:model.contextKey(value.route),revision:value.revision,scope:value.route.scope,tree:value.route.tree,node:value.route.node,
    focus:bucket.focusTarget,window:bucket.windowScroll,
    overview:bucket.overviewView||null,originalMapOpen:bucket.originalMapOpen};
}
function geometry(element){if(!element)return null;var r=element.getBoundingClientRect();
  return {x:r.x,y:r.y,width:r.width,height:r.height,scrollTop:element.scrollTop,
    scrollHeight:element.scrollHeight,clientHeight:element.clientHeight};}
var style=getComputedStyle(landing);
return {view:{focus:active.id,window:scrollY,landing:landing.scrollTop,
    open:document.getElementById('np-task-relations').open,
    lines:document.getElementById('np-overview-map').dataset.relationsVisible},
  diagnostic:{runtime:bucketRecord(runtime),persisted:bucketRecord(persisted),
    landing:geometry(landing),active:geometry(active),map:geometry(document.getElementById('np-overview-map')),
    document:geometry(document.scrollingElement),viewport:{width:innerWidth,height:innerHeight},
    scrollRestoration:history.scrollRestoration,readyState:document.readyState,
    fontsStatus:document.fonts.status,landingStyle:{overflowY:style.overflowY,scrollBehavior:style.scrollBehavior,
      overflowAnchor:style.overflowAnchor,fontSize:style.fontSize,lineHeight:style.lineHeight},
    hasHash:!!location.hash,timeOriginMs:performance.timeOrigin,relativeTimeMs:performance.now()}};
"""


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
    report['frontendSources'] = {name: sha(name) for name in ('assets/navigation-product.js', 'assets/navigation-product-model.js', 'assets/navigation-product.css', 'scripts/navigation_product.py')}
    report['servedFiles'] = {str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'research/navigation').rglob('*')) if p.is_file()}
    report['servedFiles'].update({str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'assets').glob('navigation-*.js'))})
    report['servedFiles']['assets/navigation-product.css'] = sha(dist / 'assets/navigation-product.css')
    if report['scienceSha256'] != '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c':
        raise RuntimeError('Screenshot scientific identity differs from reviewed9069 source')
    science = json.loads((dist / 'research/navigation/product-data.json').read_text())
    relation_expected = []
    for number in range(88, 95):
        rel = science['relations']['tasks:relation:' + str(number)]
        refs = []
        seen = set()
        for locator in rel['detail']['locators']:
            for sid in locator['sourceIds']:
                if sid in seen:
                    continue
                seen.add(sid)
                ref = science['sources'][sid]
                refs.append({'sourceId': sid, 'url': ref['url'], 'versionId': ref['versionId'], 'versionStatus': ref['versionStatus']})
        relation_expected.append({'id': rel['id'], 'from': rel['from'], 'to': rel['to'], 'relationType': rel['relationType'], 'locators': rel['detail']['locators'], 'sourceRefs': refs})
    driver = None
    process = None
    server = None
    logs = (out / 'chromedriver.log').open('w')

    def save():
        (out / 'receipt.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')

    def capture(name, require_tree=True, require_overview=False, require_flow=False, require_home=False):
        driver.settle()
        data = driver.js('''return {viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
          loadState:document.querySelector('[data-load-state]')?.dataset.loadState,
          route:window.NavigationProductApp?.getState().route,
          fonts:document.fonts.status, ready:!!window.NavigationProductApp,
          fallbackHidden:document.getElementById('np-static-reading')?.hidden,
          bounds:[...document.querySelectorAll('#np-workspace,#np-tree-scroll,.np-reading-pane,#np-tree .np-node-row')].map(e=>{let r=e.getBoundingClientRect();return {id:e.id,position:e.closest('[data-position]')?.dataset.position,text:e.textContent.slice(0,180),x:r.x,y:r.y,width:r.width,height:r.height};}),
          nodeCount:document.querySelectorAll('#np-tree [role=treeitem]').length,
          focus:document.activeElement?.id, bodyWidth:document.body.scrollWidth};''')
        data['screenKind'] = 'default_reading_overview' if require_home else 'tree_or_reader'
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
        selector = '#np-reading-landing .np-task-reading-contract' if require_home else driver.js("var n=[...document.querySelectorAll('#np-tree .np-node-label')].find(e=>/[\\u3400-\\u9fff]/.test(e.textContent));return n?'[id='+JSON.stringify(n.closest('[id]').id)+'] > .np-node-row .np-node-label':null")
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
        if not data['ready'] or data['loadState'] != 'ready' or not data['fallbackHidden'] or (not require_home and not data['nodeCount']) or data['fonts'] != 'loaded':
            raise RuntimeError('Blank, unready, or font-pending capture')
        if not data['pixelVariation']:
            raise RuntimeError('Screenshot has insufficient nonblank pixel variation')
        if any(e.get('level') == 'SEVERE' for e in data['console']):
            raise RuntimeError('Browser console contains severe errors')
        if data['networkFailures']:
            raise RuntimeError('Candidate resource request failed')
        visible = [r for r in data['bounds'] if r['width'] > 0 and r['height'] > 0 and r['x'] < data['viewport']['width'] and r['y'] < data['viewport']['height'] and r['x'] + r['width'] > 0 and r['y'] + r['height'] > 0]
        if require_tree and not require_home and not any(r.get('position') for r in visible):
            raise RuntimeError('No actual tree node visible in captured viewport')
        if not require_tree and not require_home and not any(r.get('id') == 'np-detail-scroll' for r in visible):
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

    def reading_home():
        driver.settle()
        data = driver.js(VISUAL_GEOMETRY + """
          var a=NavigationProductApp,state=a.getState(),landing=document.getElementById('np-reading-landing');
          return {route:state.route,home:!landing.hidden,panelsHidden:document.querySelector('.np-panels').hidden,windowScroll:scrollY,landingScroll:landing.scrollTop,scale:NavigationProductModel.getBucket(state).graphScale,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},landing:rect(landing),headings:[...landing.querySelectorAll('#np-overview-heading,[data-reading-branch] h3')].map(box),entries:[...landing.querySelectorAll('[data-task-open]')].map(e=>({id:e.dataset.taskOpen,name:box(e.querySelector('.np-task-reading-name')),contract:box(e.querySelector('.np-task-reading-contract'))}))};
        """)
        report.setdefault('defaultOverviewChecks', []).append(data)
        save()
        check_reading_home(data)

        graph = driver.js(VISUAL_GEOMETRY + """
          var a=NavigationProductApp,b=a.getBundle(),m=document.getElementById('np-overview-map'),root=b.researchMap.roots[0],p=b.positions;
          var l=p[root].childIds.find(id=>p[id].entityId==='legacy:nav:l'),c=p[root].childIds.find(id=>p[id].entityId==='legacy:nav:c'),td=p[l].childIds.find(id=>p[id].sourceDirectoryGroupId==='task');
          var wanted=[root,l,c,td,...arguments[0].map(s=>b.researchMap.scopeEntries.find(e=>e.scopeId===s).canonicalPositionId),...p[c].childIds];
          function opaque(e){for(var n=e;n;n=n.parentElement){var cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility!=='visible'||Number(cs.opacity)!==1)return false;}return true;}
          function endpoint(e,end){var q=e.getPointAtLength(end?e.getTotalLength():0),r=new DOMPoint(q.x,q.y).matrixTransform(e.getScreenCTM());return {x:r.x,y:r.y};}
          function touches(q,r){return q.x>=r.x-2&&q.x<=r.x+r.width+2&&q.y>=r.y-2&&q.y<=r.y+r.height+2&&Math.min(Math.abs(q.x-r.x),Math.abs(q.x-r.x-r.width),Math.abs(q.y-r.y),Math.abs(q.y-r.y-r.height))<=3;}
          function node(id){return [...m.querySelectorAll('[data-map-position]')].find(n=>n.dataset.mapPosition===id);}
          function edge(e){var cs=getComputedStyle(e),stroke=color(cs.stroke),alpha=stroke?stroke.alpha*Number(cs.strokeOpacity):0,display=true;for(var n=e;n;n=n.parentElement){var st=getComputedStyle(n);alpha*=Number(st.opacity);if(st.display==='none'||st.visibility!=='visible')display=false;}var background=bg(m),foreground=stroke&&background.length===3?stroke.rgb.map((v,i)=>v*alpha+background[i]*(1-alpha)):[],len=e.getTotalLength(),matrix=e.getScreenCTM(),mr=rect(m),inBounds=true,uncovered=0,ownHits=[];for(var i=1;i<20;i++){var q=e.getPointAtLength(len*i/20),z=new DOMPoint(q.x,q.y).matrixTransform(matrix);if(z.x<mr.x-1||z.y<mr.y-1||z.x>mr.x+mr.width+1||z.y>mr.y+mr.height+1||z.x<0||z.y<0||z.x>innerWidth||z.y>innerHeight)inBounds=false;var hit=document.elementFromPoint(z.x,z.y);if(hit&&(hit===e||hit===m||hit===e.closest('svg')))uncovered++;if(hit===e)ownHits.push({x:z.x,y:z.y,fraction:i/20});}return {visible:display&&alpha>0&&foreground.length===3&&parseFloat(cs.strokeWidth)>0,length:len,foreground:foreground,background:background,inBounds:inBounds,uncovered:uncovered>=3,ownHits:ownHits};}
          return {viewport:{x:0,y:0,width:innerWidth,height:innerHeight},map:rect(m),mapVisible:!m.hidden&&opaque(m)&&m.clientWidth>0&&m.clientHeight>0,expectedIds:wanted,expectedEdges:wanted.filter(id=>p[id].parentId&&wanted.includes(p[id].parentId)).map(id=>[p[id].parentId,id]),expectedChallengeLabels:arguments[1],expectedRelations:arguments[2],
            directoryTitle:box(node(td)),
            nodes:[...m.querySelectorAll('[data-map-position]')].map(n=>Object.assign({id:n.dataset.mapPosition},box(n))),
            edges:[...m.querySelectorAll('path[data-map-parent][data-map-child]')].map(e=>Object.assign({parent:e.dataset.mapParent,child:e.dataset.mapChild,endpointsMatch:!!node(e.dataset.mapParent)&&!!node(e.dataset.mapChild)&&touches(endpoint(e,false),rect(node(e.dataset.mapParent)))&&touches(endpoint(e,true),rect(node(e.dataset.mapChild)))},edge(e))),
            tasks:[...m.querySelectorAll('[data-task-open]')].map(n=>({scope:n.dataset.taskOpen,expectedScope:p[n.dataset.mapPosition].sourceScopeId,position:n.dataset.mapPosition,expectedPosition:b.researchMap.scopeEntries.find(e=>e.scopeId===n.dataset.taskOpen).canonicalPositionId})),
            challenges:[...m.querySelectorAll('[data-challenge-open]')].map(n=>{var q=p[n.dataset.mapPosition];return {position:n.dataset.mapPosition,challengeOpen:n.dataset.challengeOpen,entity:q.entityId,expectedEntity:p[n.dataset.challengeOpen].entityId,title:n.title,aria:n.getAttribute('aria-label')||'',expectedTitle:arguments[3][q.entityId],label:box(n.querySelector('.np-map-challenge-label'))};}),
            relations:[...m.querySelectorAll('path[data-map-relation]')].map(e=>Object.assign({id:e.dataset.mapRelation,from:e.dataset.fromEntity,to:e.dataset.toEntity,type:e.dataset.relationType,endpointsMatch:(()=>{var from=[...m.querySelectorAll('[data-task-open]')].find(n=>n.dataset.taskOpen===e.dataset.fromEntity),to=[...m.querySelectorAll('[data-task-open]')].find(n=>n.dataset.taskOpen===e.dataset.toEntity);return !!from&&!!to&&touches(endpoint(e,false),rect(from))&&touches(endpoint(e,true),rect(to));})()},edge(e)))};
        """, [x[0] for x in TASK_INDEX], CHALLENGE_LABELS, [[r['id'],r['from'],r['to'],r['relationType']] for r in relation_expected], {entity:science['entities'][entity]['label'] for entity in CHALLENGE_LABELS})
        report.setdefault('graphicalOverviewChecks', []).append(graph)
        save()
        check_graphical_map(graph)


    def relationship_checks(prefix, base):
        before_route = driver.js('return NavigationProductApp.getState().route')
        driver.click(driver.selector('#np-map-relations-toggle'))
        if driver.js("return document.getElementById('np-overview-map').dataset.relationsVisible") != 'false':
            raise RuntimeError('Relationship lines visibility control failed')
        driver.click(driver.selector('#np-task-relations > summary'))

        def evidence(expected, expected_focus=None):
            data = driver.js("""var id=arguments[0],e=[...document.querySelectorAll('[data-task-relation]')].find(n=>n.dataset.taskRelation===id);return {id:e.dataset.taskRelation,type:e.dataset.relationType,from:e.dataset.fromEntity,to:e.dataset.toEntity,open:document.getElementById('np-task-relations').open,focus:document.activeElement.id,route:NavigationProductApp.getState().route,text:e.textContent,sources:[...e.querySelectorAll('[data-task-relation-source]')].map(n=>({id:n.dataset.taskRelationSource,url:n.href,version:n.dataset.sourceVersion,status:n.dataset.sourceStatus}))};""", expected['id'])
            data['beforeRoute'] = before_route
            if expected_focus is not None:
                data['expectedFocus'] = expected_focus
            proofs = []
            specs = [{'kind':'heading'}] + [{'kind':'locator','text':loc['locator']} for loc in expected['locators']] + [{'kind':kind,'id':ref['sourceId']} for ref in expected['sourceRefs'] for kind in ('source','status')]
            for spec in specs:
                element = driver.js(RELATION_EVIDENCE_ELEMENT_JS,expected['id'],spec)
                if element is None:
                    raise RuntimeError('Exact relationship visible source element is missing')
                driver.js("arguments[0].scrollIntoView({block:'center'});", element)
                driver.settle()
                proof = driver.js(VISUAL_GEOMETRY + "var e=arguments[0],b=box(e),rs=[...e.getClientRects()].filter(r=>r.width>0&&r.height>0);if(getComputedStyle(e).display==='inline'){b.visible=b.opaque&&rs.length>0&&rs.every(r=>[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return hit===e||e.contains(hit);}));b.clipped=false;}b.clientRects=rs.map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}));return Object.assign(b,{viewport:{x:0,y:0,width:innerWidth,height:innerHeight}});", element)
                proof['kind'] = spec['kind']
                if spec['kind'] == 'status':
                    status = next(ref['versionStatus'] for ref in expected['sourceRefs'] if ref['sourceId'] == spec['id'])
                    proof['expectedText'] = ' · ' + {'snapshot_not_version_pinned':'未固定全文快照','fixed_arxiv_version_url':'来源URL限定版本'}.get(status,status)
                proofs.append(proof)
            data['visibleProofs'] = proofs
            report.setdefault('relationEvidenceChecks', []).append(data)
            save()
            check_relation_evidence(data, expected)
            return data

        for i, expected in enumerate(relation_expected):
            control = driver.selector('[data-relation-select="' + expected['id'] + '"]')
            driver.js("arguments[0].scrollIntoView({block:'center'});", control)
            driver.settle()
            native = driver.js(VISUAL_GEOMETRY + "return {tag:arguments[0].tagName,type:arguments[0].type,disabled:arguments[0].disabled,tabIndex:arguments[0].tabIndex,target:arguments[0].getAttribute('aria-controls'),box:box(arguments[0])};", control)
            if native['tag'] != 'BUTTON' or native['type'] != 'button' or native['disabled'] or native['tabIndex'] != 0 or native['target'] != 'np-map-relation-evidence-' + expected['id'] or not native['box']['visible'] or native['box']['clipped']:
                raise RuntimeError('Relationship text selection is not a usable exact native button')
            driver.click(control)
            driver.settle()
            evidence(expected)
            if i in (0, 2, 6):
                driver.js("document.getElementById(arguments[0]).scrollIntoView({block:'start'});", 'np-map-relation-evidence-' + expected['id'])
                driver.settle()
                capture(prefix + '-13-relation-' + expected['id'].split(':')[-1], require_home=True)
        # Exercise native keyboard activation, not a script-generated click event.
        expected = relation_expected[2]
        control = driver.selector('[data-relation-select="' + expected['id'] + '"]')
        driver.js("arguments[0].scrollIntoView({block:'center'});arguments[0].focus({preventScroll:true});", control)
        driver.call('POST', '/element/' + control[ELEMENT] + '/value', {'text': '\ue007', 'value': ['\ue007']})
        driver.settle()
        evidence(expected)
        before_snapshot = driver.js(COLD_RESTORE_SNAPSHOT_JS)
        stored = before_snapshot['view']
        driver.call('POST', '/refresh', {})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
        driver.settle()
        after_snapshot = driver.js(COLD_RESTORE_SNAPSHOT_JS)
        restored = after_snapshot['view']
        report.setdefault('relationColdRestoreChecks', []).append({'before':stored,'after':restored,
            'differentFields':sorted(key for key in set(stored) | set(restored) if stored.get(key) != restored.get(key)),
            'beforeDiagnostic':before_snapshot['diagnostic'],'afterDiagnostic':after_snapshot['diagnostic']})
        save()
        if restored != stored:
            raise RuntimeError('Cold relationship restoration lost disclosure, line visibility, focus or scroll')
        evidence(expected)
        # Visit the exact relation endpoint and restore through actual browser Back.
        control = driver.js("return document.getElementById(arguments[0]);", 'np-relation-entry-' + expected['id'] + '-' + expected['to'])
        driver.js("arguments[0].scrollIntoView({block:'center'});arguments[0].focus({preventScroll:true});", control)
        driver.settle()
        endpoint_origin = driver.js("return {focus:document.activeElement.id,window:scrollY,landing:document.getElementById('np-reading-landing').scrollTop};")
        driver.click(control)
        driver.settle()
        if driver.js('return NavigationProductApp.getState().route.scope') != expected['to']:
            raise RuntimeError('Relationship endpoint entered another scope')
        driver.call('POST', '/back', {})
        driver.settle()
        if driver.js('return NavigationProductApp.getState().route') != before_route or not driver.js("return document.getElementById('np-task-relations').open"):
            raise RuntimeError('Relationship Back lost the original route or evidence disclosure')
        back_origin = driver.js("return {focus:document.activeElement.id,window:scrollY,landing:document.getElementById('np-reading-landing').scrollTop};")
        if back_origin != endpoint_origin:
            raise RuntimeError('Relationship endpoint Back lost exact saved focus or reading scroll')
        evidence(expected, expected_focus=endpoint_origin['focus'])
        # Fresh document for real SVG hit tests; do not force a hidden path click.
        for rid in ('tasks:relation:90', 'tasks:relation:92'):
            driver.call('POST', '/url', {'url': 'about:blank'})
            driver.call('POST', '/url', {'url': base})
            wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
            driver.settle()
            point = driver.js("""var e=[...document.querySelectorAll('path[data-map-relation]')].find(n=>n.dataset.mapRelation===arguments[0]),len=e.getTotalLength(),matrix=e.getScreenCTM();for(var i=10;i<=90;i++){var q=e.getPointAtLength(len*i/100),p=new DOMPoint(q.x,q.y).matrixTransform(matrix),x=Math.round(p.x),y=Math.round(p.y);if(x<1||y<1||x>=innerWidth-1||y>=innerHeight-1)continue;if(document.elementFromPoint(x,y)===e)return {x:x,y:y,id:e.dataset.mapRelation,fraction:i/100};}return null;""",rid)
            if not point:
                raise RuntimeError('Relationship SVG has no independently hittable visible segment: ' + rid)
            driver.call('POST', '/actions', {'actions':[{'type':'pointer','id':'relation-pointer','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','duration':0,'origin':'viewport','x':point['x'],'y':point['y']},{'type':'pointerDown','button':0},{'type':'pointerUp','button':0}]}]})
            driver.settle()
            expected = next(r for r in relation_expected if r['id']==rid)
            evidence(expected)
            report.setdefault('relationPointerChecks', []).append(point)
        # Read one real challenge through its map control, including original applicability.
        driver.call('POST', '/url', {'url': 'about:blank'})
        driver.call('POST', '/url', {'url': base})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
        driver.settle()
        challenge = driver.js("var b=NavigationProductApp.getBundle(),p=Object.values(b.researchMap.positions).find(p=>p.entityId==='legacy:ci_search_unknown_target');return {position:p,control:document.querySelector('[data-challenge-open=\"'+p.id+'\"]')};")
        driver.click(challenge['control'])
        q = challenge['position']
        wait_for(lambda: driver.js("var a=NavigationProductApp,r=a.getState().route,q=arguments[0];return r.node===q.id&&r.tree===q.tree&&r.scope===q.scopeId&&r.paper===(q.paperId||null)&&r.version===(q.versionId||null)&&a.getContent().ready(q.entityId)&&!!document.querySelector('[data-reading-node=\"'+q.id+'\"]');", q))
        driver.settle()
        original = science['entities'][q['entityId']]
        challenge_reading = driver.js(VISUAL_GEOMETRY + "var e=document.querySelector('[data-reading-node=\"'+arguments[0]+'\"]'),h=e.querySelector('h3'),scope=e.querySelector('[data-challenge-scope]');return {route:NavigationProductApp.getState().route,title:box(h),text:e.textContent,scope:scope?box(scope):null,scopeParagraphs:scope?[...scope.querySelectorAll('p')].map(box):[],viewport:{x:0,y:0,width:innerWidth,height:innerHeight}};",q['id'])
        required = [original['label'],original['detail']['condition_scope']['condition'],*original['detail']['condition_scope']['tasks'],original['detail']['condition_scope']['remaining_limit']]
        if any(text not in challenge_reading['text'] for text in required):
            raise RuntimeError('Challenge reader omitted the original question or applicability')
        for key in ('title','scope'):
            proof = challenge_reading[key]
            if proof is None or not proof['visible'] or not proof['opaque'] or not proof['unscaled'] or proof['fontSize'] < 15 or proof['clipped'] or len(proof['foreground']) != 3 or len(proof['background']) != 3 or contrast_ratio(proof['foreground'],proof['background']) < 4.5 or not rect_inside(proof['rect'],challenge_reading['viewport']):
                raise RuntimeError('Challenge original question and scope are not visible together')
        if len(challenge_reading['scopeParagraphs']) < 3:
            raise RuntimeError('Challenge applicability paragraphs are incomplete')
        for proof in challenge_reading['scopeParagraphs']:
            if not proof['visible'] or not proof['opaque'] or not proof['unscaled'] or proof['fontSize'] < 15 or proof['clipped'] or len(proof['foreground']) != 3 or len(proof['background']) != 3 or contrast_ratio(proof['foreground'],proof['background']) < 4.5 or not rect_inside(proof['rect'],challenge_reading['viewport']):
                raise RuntimeError('Challenge applicability paragraph is not visibly readable')
        report.setdefault('graphChallengeReadingChecks', []).append(challenge_reading)
        capture(prefix + '-14-original-challenge-reader')
        driver.click(driver.selector('.np-return-previous'))
        driver.settle()
        if not driver.js("return !document.getElementById('np-reading-landing').hidden&&document.activeElement.id===arguments[0];",'np-challenge-entry-'+q['id']):
            raise RuntimeError('Challenge reader return lost the original map entry focus')
        # Leave the preserved old16 scenarios at a clean, unscrolled entry.
        driver.call('POST', '/url', {'url': 'about:blank'})
        driver.call('POST', '/url', {'url': base})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
        driver.settle()

    def parallel_scope(scope):
        data = driver.js(VISUAL_GEOMETRY + """
          var a=NavigationProductApp,b=a.getBundle(),r=a.getState().route;
          return {scope:r.scope,expectedScope:arguments[0],home:!document.getElementById('np-reading-landing').hidden,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},panels:[...document.querySelectorAll('#np-tree [data-parallel-tree]')].map(e=>{var tree=e.dataset.parallelTree,roots=b.forests[r.scope][tree],h=e.querySelector('h3'),hb=box(h),q=hb.rect;return {tree:tree,scope:e.dataset.scopeId,roots:[...e.querySelectorAll(arguments[1])].map(n=>n.dataset.position),expectedRoots:roots,expectedChildren:roots.some(id=>b.positions[id].childIds.length>0),children:[...e.querySelectorAll('[role=treeitem]')].filter(n=>!roots.includes(n.dataset.position)).map(n=>box(n.querySelector(':scope > .np-node-row'))),rect:rect(e),heading:q,headingVisible:hb.visible&&hb.opaque&&!hb.clipped};})};
        """, scope, PARALLEL_ROOT_SELECTOR)
        report.setdefault('parallelScopeChecks', []).append(data)
        save()
        check_parallel_scope(data)

    def select_node(target):
        for _ in range(16):
            element = driver.js("return document.getElementById('np-node-'+arguments[0])?.querySelector('.np-node-label')||null", target)
            if element:
                driver.click(element)
                wait_for(lambda: driver.js("""
                  var a=NavigationProductApp,b=a.getBundle(),p=b.positions[arguments[0]],r=a.getState().route;
                  if(r.node!==p.id||r.tree!==p.tree||r.scope!==p.scopeId||r.paper!==p.paperId||r.version!==p.versionId||!a.getContent().ready(p.entityId))return false;
                  var method=document.querySelector('.np-reading-pane .np-method-mechanism'),meaning=document.querySelector('.np-reading-pane .np-node-meaning');
                  return (method&&method.dataset.mechanismEntity===p.entityId&&method.querySelectorAll('.np-method-flow dd').length>0)||(meaning&&meaning.dataset.readingNode===p.id&&!meaning.querySelector('.np-content-pending,.np-content-failed'));
                """, target))
                driver.settle()
                return
            toggle = driver.js("var b=NavigationProductApp.getBundle(),p=b.positions[arguments[0]],ids=[];while(p){ids.unshift(p.id);p=b.positions[p.parentId]}for(var id of ids){var n=document.getElementById('np-node-'+id);if(n&&n.getAttribute('aria-expanded')==='false')return n.querySelector('.np-node-toggle')}return null", target)
            if not toggle:
                raise RuntimeError('Recorded node has no reachable real ancestor control')
            driver.click(toggle)
            driver.settle()
        raise RuntimeError('Recorded node did not become reachable')

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
            reading_home()
            capture(prefix + '-00-default-reading-overview', require_home=True)
            relationship_checks(prefix, base)
            driver.click(driver.selector('#np-overview-toggle'))
            driver.settle()
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
            report.setdefault('contextPathChecks', []).append({'viewport': prefix, 'evidence': context})
            save()
            check_context_path(context)
            capture(prefix + '-06-audiogoal-ci-path')
            driver.click(driver.selector('[data-path-kind="global-entry"] [data-context-position]'))
            driver.settle()
            if driver.js('return !document.getElementById("np-reading-landing").hidden'):
                driver.click(driver.selector('#np-overview-toggle'))
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
            driver.call('POST', '/url', {'url': 'about:blank'})
            driver.call('POST', '/url', {'url': base})
            wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
            named_cases = {'task:audiogoal': 'audio', 'task:goat': 'goat', 'task:language-objectnav': 'condition', 'task:aerial-visual-object-search': 'gap', 'task:category-objectnav': 'objectnav'}
            for scope, _, _ in TASK_INDEX:
                name = named_cases.get(scope)
                driver.click(driver.selector('[data-task-open="' + scope + '"]'))
                driver.settle()
                parallel_scope(scope)
                if name:
                    capture(prefix + '-08-parallel-' + name)
                if name == 'audio':
                    select_node(ci_target)
                    wait_for(lambda: driver.js('var a=NavigationProductApp;return a.getContent().ready(a.getBundle().positions[arguments[0]].entityId)', ci_target))
                    capture(prefix + '-09-audio-local-insight')
                elif name == 'goat':
                    for target in ['pos:c:6c467a403479ac834b4f4b', 'pos:c:3ca63b00ad82d0661153fc']:
                        select_node(target)
                        actual = driver.js('var a=NavigationProductApp;return {route:a.getState().route,position:a.getBundle().positions[arguments[0]]}', target)
                        expected_association = 'direct' if target == 'pos:c:6c467a403479ac834b4f4b' else 'condition'
                        if actual['position']['association'] != expected_association or actual['route']['paper'] != actual['position']['paperId'] or actual['route']['version'] != actual['position']['versionId']:
                            raise RuntimeError('GOAT direct and condition evidence identity was merged')
                        if actual['route']['node'] != target or actual['route']['scope'] != scope:
                            raise RuntimeError('GOAT local challenge identity changed')
                        report.setdefault('goatLocalChecks', []).append(actual)
                    capture(prefix + '-10-goat-local-condition')
                elif name == 'objectnav':
                    method = driver.js("var b=NavigationProductApp.getBundle();return Object.values(b.positions).find(p=>p.tree==='l'&&p.scopeId==='task:category-objectnav'&&p.paperId==='vlfm'&&p.kind==='pipeline_recipe').id;")
                    select_node(method)
                    wait_for(lambda: driver.js('var a=NavigationProductApp;return a.getContent().ready(a.getBundle().positions[arguments[0]].entityId)&&document.querySelectorAll(".np-method-flow dd").length===5', method))
                    capture(prefix + '-11-parallel-method-reader', require_flow=True)
                # Exact origin is the real overview entry, not a reconstructed route.
                for _ in range(20):
                    if driver.js('return !document.getElementById("np-reading-landing").hidden'):
                        break
                    driver.click(driver.selector('.np-return-previous'))
                    driver.settle()
                if not driver.js('return !document.getElementById("np-reading-landing").hidden&&document.activeElement.id===arguments[0]', 'np-task-entry-' + scope):
                    raise RuntimeError('Task return lost exact overview entry focus')
            driver.click(driver.selector('#np-all-scopes > summary'))
            directory = driver.js("var b=NavigationProductApp.getBundle();return {expected:b.scopes.map(s=>({id:s.id,parent:s.parentScopeId||'',domParent:s.parentScopeId||''})).sort((a,b)=>a.id.localeCompare(b.id)),actual:[...document.querySelectorAll('#np-all-scopes [data-directory-scope]')].map(n=>({id:n.dataset.directoryScope,parent:n.dataset.parentScope,domParent:n.parentElement.closest('[data-directory-scope]')?.dataset.directoryScope||''})).sort((a,b)=>a.id.localeCompare(b.id))};")
            if directory['actual'] != directory['expected'] or len(directory['actual']) != 64:
                raise RuntimeError('Complete64-scope directory lost identity or original parent')
            for scope in ['task:coin', 'task:iign', 'task:dialnav']:
                control = driver.selector('[data-scope-open="' + scope + '"]')
                driver.js("arguments[0].scrollIntoView({block:'center'});arguments[0].focus({preventScroll:true});", control)
                driver.settle()
                before = driver.js('return {window:scrollY,landing:document.getElementById("np-reading-landing").scrollTop,focus:document.activeElement.id};')
                driver.click(control)
                driver.settle()
                parallel_scope(scope)
                driver.click(driver.selector('.np-return-previous'))
                driver.settle()
                after = driver.js('return {window:scrollY,landing:document.getElementById("np-reading-landing").scrollTop,focus:document.activeElement.id};')
                if before != after or not driver.js('return document.getElementById("np-all-scopes").open'):
                    raise RuntimeError('Directory return lost open state, scroll or exact entry focus')
                report.setdefault('directoryReturnChecks', []).append({'scope': scope, 'before': before, 'after': after})
            capture(prefix + '-12-directory-return', require_home=True)
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
