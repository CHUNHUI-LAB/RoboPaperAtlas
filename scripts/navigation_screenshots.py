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
import re
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
SCENE_NAMES = (
    '-00-default-reading-overview', '-01-overview', '-02-task-expanded', '-03-method-reader',
    '-03b-reader-visible', '-04-return', '-05-zoom-out', '-06-audiogoal-ci-path', '-07-ci-return-overview',
    '-08-active-audio', '-08-active-goat', '-08-active-condition', '-09-audio-local-insight',
    '-10-goat-local-condition', '-11-active-method-reader', '-11b-reader-collapsed', '-11c-reader-reopened',
    '-12-directory-return', '-13-relation-88', '-13-relation-90', '-13-relation-94', '-14-original-challenge-reader',
    '-21-initial-objectnav-routes', '-21-initial-imagenav-routes', '-21-initial-portable-variants', '-21-initial-avos-inventory-gap',
    '-22-methods-relation-90', '-23-poni-method', '-24-poni-claim', '-25-return-methods-relation-90', '-26-return-objectnav-task',
    '-27-imagenav-zhu-route-condition', '-27-imagenav-zhu', '-27-imagenav-sptm-route-condition', '-27-imagenav-sptm', '-27-imagenav-ving',
    '-28-portable-rl', '-28-portable-llm', '-29-literature-before-switch', '-29-challenge-selected', '-29-literature-restored',
    '-30-analysis-imported-entry', '-30-analysis-imported', '-30-analysis-not-imported', '-30-analysis-template-explicit',
)


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
        raise RuntimeError('Task did not enter its own active reading view')
    if (data['activeTree'] not in ('l', 'c') or [x['tree'] for x in data['panels']] != [data['activeTree']] or
            data['treeCount'] != 1 or data['rovingCount'] != 1 or data['inactiveItemCount'] or
            data['selectedTree'] != data['activeTree']):
        raise RuntimeError('Task must contain one actual active forest and one roving keyboard scope')
    for panel in data['panels']:
        if panel['scope'] != data['scope'] or panel['roots'] != panel['expectedRoots']:
            raise RuntimeError('Active forest identity differs from original scope roots')
        if not panel['headingVisible'] or not rect_inside(panel['heading'], data['viewport']):
            raise RuntimeError('Active task tree heading is not visible')
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
        hold = getattr(self.server, 'packet_hold', None)
        if hold and urllib.parse.urlsplit(self.path).path == hold.path:
            hold.seen.set()
            if not hold.released.wait(8):
                hold.expired = True
        super().do_GET()


class PacketHold:
    """Bounded timing for one existing, SHA-pinned public loopback packet."""
    def __init__(self, server, path, dist, expected_sha):
        if (server.server_address[0] != '127.0.0.1' or
                not re.fullmatch(r'/research/navigation/content/[a-f0-9]{64}\.json', path) or
                path.rsplit('/', 1)[1] != expected_sha + '.json' or
                sha(Path(dist) / path.lstrip('/')) != expected_sha):
            raise RuntimeError('Delayed-content fixture is not an existing pinned loopback packet')
        self.server, self.path = server, path
        self.seen, self.released = threading.Event(), threading.Event()
        self.expired = False

    def __enter__(self):
        if getattr(self.server, 'packet_hold', None) is not None:
            raise RuntimeError('Only one bounded packet hold is allowed')
        self.server.packet_hold = self
        return self

    def __exit__(self, *_):
        self.released.set()
        self.server.packet_hold = None


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


# One CSS pixel covers integer client/scroll metrics versus subpixel DOMRects.
# It is not a percentage allowance for lost row anchors or missing panel space.
READER_GEOMETRY_TOLERANCE = 1
READER_TOGGLE_SELECTOR = 'button#np-reader-toggle[aria-controls="np-detail-scroll"]'
READER_TOGGLE_SNAPSHOT_JS = VISUAL_GEOMETRY + r"""
var a=NavigationProductApp,m=NavigationProductModel,state=a.getState(),bucket=m.getBucket(state),
    app=document.getElementById('navigation-product'),p=a.getBundle().positions[state.route.node],
    tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll'),
    toggle=document.getElementById('np-reader-toggle'),selected=document.getElementById('np-node-'+state.route.node),
    row=selected&&selected.querySelector(':scope > .np-node-row'),label=row&&row.querySelector('.np-node-label'),
    mechanism=reader.querySelector('.np-method-mechanism'),context=m.contextKey(state.route);
function proof(e){return e?box(e):null;}
function scrollBox(e){var r=rect(e);return {rect:r,client:{x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight},
  left:e.scrollLeft,top:e.scrollTop,scrollWidth:e.scrollWidth,scrollHeight:e.scrollHeight,
  maxLeft:Math.max(0,e.scrollWidth-e.clientWidth),maxTop:Math.max(0,e.scrollHeight-e.clientHeight)};}
function preserved(value){
  if(!value||!value.route||!value.contexts)return null;
  var result=JSON.parse(JSON.stringify(value)),b=result.contexts[m.contextKey(result.route)],t=result.route.tree;
  // Only current view offsets and focus may be updated by saveCurrent().
  // Keep all other buckets, origin snapshots, revision and presentation settings.
  if(b){delete b.focusTarget;delete b.windowScroll;['treeScrollByTree','treeScrollLeftByTree','detailScrollByTree'].forEach(k=>{if(b[k])delete b[k][t];});}
  return result;
}
var historyState=history.state,unrelated=historyState&&typeof historyState==='object'?Object.assign({},historyState):historyState;
if(unrelated&&typeof unrelated==='object')delete unrelated[m.KEY];
var ts=scrollBox(tree),rr=row&&rect(row);
return {route:state.route,taskContextKey:m.taskContextKey(state.route),position:p?{id:p.id,scope:p.scopeId,tree:p.tree,paper:p.paperId,version:p.versionId,entity:p.entityId,kind:p.kind}:null,
  graphScale:bucket.graphScale,expanded:bucket.expandedByTree,preservedState:preserved(state),
  history:{length:history.length,url:location.href,modelKey:m.KEY,contextKey:context,
    entryKey:window.navigation&&window.navigation.currentEntry?window.navigation.currentEntry.key:null,
    timeOrigin:performance.timeOrigin,model:preserved(historyState&&historyState[m.KEY]),unrelated:unrelated},
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},window:{x:scrollX,y:scrollY},
  layout:app.dataset.readingLayout,collapsed:app.dataset.readerCollapsed,focus:document.activeElement.id,
  panels:rect(document.querySelector('.np-panels')),columnGap:parseFloat(getComputedStyle(document.querySelector('.np-panels')).columnGap),
  treePane:proof(document.querySelector('.np-tree-pane')),tree:ts,treeProof:proof(tree),title:proof(document.getElementById('np-tree-heading')),
  selected:{count:document.querySelectorAll('#np-tree [aria-selected="true"]').length,id:selected&&selected.dataset.position,
    tree:selected&&selected.dataset.tree,entity:selected&&selected.dataset.entity,aria:selected&&selected.getAttribute('aria-selected'),
    scope:selected&&selected.closest('[data-parallel-tree]')?.dataset.scopeId,row:proof(row),label:proof(label),
    content:rr?{x:rr.x-ts.client.x+ts.left,y:rr.y-ts.client.y+ts.top}:null},
  toggle:{tag:toggle.tagName,hidden:toggle.hidden,disabled:toggle.disabled,controls:toggle.getAttribute('aria-controls'),expanded:toggle.getAttribute('aria-expanded'),proof:proof(toggle)},
  reader:{hidden:reader.hidden,display:getComputedStyle(reader).display,tabIndex:reader.tabIndex,proof:proof(reader),scroll:scrollBox(reader),
    heading:proof(reader.querySelector('.np-reader-heading')),entity:mechanism&&mechanism.dataset.mechanismEntity,
    flowCount:mechanism?mechanism.querySelectorAll('.np-method-flow dd').length:0,
    savedScroll:bucket.detailScrollByTree[state.route.tree],persistedScroll:historyState&&historyState[m.KEY]?.contexts[context]?.detailScrollByTree[state.route.tree]}};
"""


READER_DOM_ELEMENTS_JS = "var s=document.getElementById('np-node-'+NavigationProductApp.getState().route.node);return [document.getElementById('np-tree'),s,s&&s.querySelector(':scope > .np-node-row'),document.getElementById('np-detail-scroll'),document.querySelector('#np-detail-scroll .np-method-mechanism')];"
READER_DOM_IDENTITY_JS = "var old=arguments[0],s=document.getElementById('np-node-'+NavigationProductApp.getState().route.node),current=[document.getElementById('np-tree'),s,s&&s.querySelector(':scope > .np-node-row'),document.getElementById('np-detail-scroll'),document.querySelector('#np-detail-scroll .np-method-mechanism')];return ['tree','selected','row','reader','method'].map((name,i)=>({name:name,same:!!old[i]&&old[i].isConnected&&old[i]===current[i]}));"


def check_reader_dom_identity(data):
    if [item['name'] for item in data] != ['tree', 'selected', 'row', 'reader', 'method'] or any(item['same'] is not True for item in data):
        raise RuntimeError('Reader toggle rebuilt the original tree, selected row or reader DOM')


def _reader_close(actual, expected):
    return (isinstance(actual, (int, float)) and isinstance(expected, (int, float)) and
            math.isfinite(actual) and math.isfinite(expected) and
            abs(actual - expected) <= READER_GEOMETRY_TOLERANCE)


def _reader_proof(proof, *areas, font_size=None):
    if not proof or not all(proof.get(k) for k in ('visible', 'opaque', 'unscaled')):
        return False
    if not all(rect_inside(proof['rect'], area, READER_GEOMETRY_TOLERANCE) for area in areas):
        return False
    return font_size is None or (not proof['clipped'] and proof['fontSize'] >= font_size and
                                len(proof['foreground']) == len(proof['background']) == 3 and
                                contrast_ratio(proof['foreground'], proof['background']) >= 4.5)


def check_reader_toggle_snapshot(data, collapsed):
    """Measure the actual selected ObjectNav/VLFM reading UI, including occlusion."""
    route, position, selected = data['route'], data['position'], data['selected']
    if (not position or route['scope'] != 'task:category-objectnav' or route['tree'] != 'l' or
            route['paper'] != 'vlfm' or position['kind'] != 'pipeline_recipe' or
            any(route[key] != position[other] for key, other in
                (('node', 'id'), ('scope', 'scope'), ('tree', 'tree'), ('paper', 'paper'), ('version', 'version'))) or
            selected['count'] != 1 or selected['id'] != route['node'] or selected['aria'] != 'true' or
            selected['scope'] != route['scope'] or selected['tree'] != route['tree'] or selected['entity'] != position['entity']):
        raise RuntimeError('Reader toggle lost exact ObjectNav/VLFM source or selected-row identity')
    if (data['layout'] != 'reading' or data['collapsed'] != str(collapsed).lower() or
            data['reader']['hidden'] != collapsed or data['reader']['entity'] != position['entity'] or
            data['reader']['flowCount'] != 5 or data['history']['model'] != data['preservedState']):
        raise RuntimeError('Reader toggle layout, source content or persisted route is inconsistent')
    viewport, panels, tree = data['viewport'], data['panels'], data['tree']
    if (viewport['width'], viewport['height']) not in VIEWPORTS:
        raise RuntimeError('Reader toggle evidence is not a required desktop viewport')
    if (not rect_inside(panels, viewport) or
            not _reader_proof(data['treePane'], panels, viewport) or
            not _reader_proof(data['treeProof'], data['treePane']['rect'], viewport) or
            # Keep a readable forest column and several full node rows on screen.
            tree['client']['width'] < 360 or tree['client']['height'] < 240 or
            not _reader_proof(data['title'], data['treePane']['rect'], viewport, font_size=14) or
            not _reader_proof(selected['row'], tree['client'], viewport) or
            not _reader_proof(selected['label'], selected['row']['rect'], tree['client'], viewport, font_size=15)):
        raise RuntimeError('Reader toggle branch title, tree viewport or selected row is hidden, clipped or covered')
    for axis, scroll, size, total, maximum in (('x', 'left', 'width', 'scrollWidth', 'maxLeft'), ('y', 'top', 'height', 'scrollHeight', 'maxTop')):
        values = [tree[scroll], tree[total], tree[maximum], tree['client'][size], selected['content'][axis]]
        if (not all(isinstance(v, (int, float)) and math.isfinite(v) for v in values) or
                tree[maximum] != max(0, tree[total] - tree['client'][size]) or
                tree[scroll] < 0 or tree[scroll] > tree[maximum] or
                not _reader_close(selected['content'][axis], selected['row']['rect'][axis] - tree['client'][axis] + tree[scroll])):
            raise RuntimeError('Reader toggle scroll metrics do not describe the measured selected row')
    toggle = data['toggle']
    if (toggle['tag'] != 'BUTTON' or toggle['hidden'] or toggle['disabled'] or toggle['controls'] != 'np-detail-scroll' or
            toggle['expanded'] != str(not collapsed).lower() or
            toggle['proof']['text'] != ('展开所选节点正文' if collapsed else '收起阅读栏') or
            not _reader_proof(toggle['proof'], viewport, font_size=14)):
        raise RuntimeError('Reader toggle is not the visible, enabled, correctly labelled disclosure button')
    reader = data['reader']
    if collapsed:
        if reader['display'] != 'none' or reader['proof']['rect']['width'] or reader['proof']['rect']['height']:
            raise RuntimeError('Collapsed reader still occupies visible layout space')
        if not _reader_close(data['treePane']['rect']['width'], panels['width']):
            raise RuntimeError('Collapsed tree does not recover the complete panel width')
    else:
        rr, tr = reader['proof']['rect'], data['treePane']['rect']
        expected_reader_width = min(720, max(520, viewport['width'] * .38))
        if (reader['display'] == 'none' or reader['tabIndex'] != -1 or
                not _reader_close(rr['width'], expected_reader_width) or
                not _reader_close(tr['width'], panels['width'] - data['columnGap'] - expected_reader_width) or rr['height'] < 320 or
                not _reader_proof(reader['proof'], panels, viewport) or
                not _reader_proof(reader['heading'], reader['scroll']['client'], viewport, font_size=11) or
                not _reader_close(rr['x'] - (tr['x'] + tr['width']), data['columnGap']) or
                not _reader_close(tr['width'] + data['columnGap'] + rr['width'], panels['width'])):
            raise RuntimeError('Expanded reader, sticky heading or separate tree/reader boundaries are not visible')


def _reader_toggle_preserved(data, expected_focus):
    """Validate the one intended neutral focus update before projecting it out."""
    route = data['route']
    key = json.dumps([route['scope'], route.get('bench') or None, route.get('protocol') or None,
                      None, None, None], separators=(',', ':'))
    dom_focus = 'np-node-' + route['node'] if expected_focus == route['node'] else expected_focus
    if data.get('taskContextKey') != key or data['focus'] != dom_focus:
        raise RuntimeError('Reader toggle has an incorrect task context or actual focus')
    preserved, history = json.loads(json.dumps([data['preservedState'], data['history']]))
    for state in (preserved, history['model']):
        view = state.get('contexts', {}).get(key, {}).get('taskView', {})
        targets = view.get('focusTargetByTree', {})
        if targets.get(route['tree']) != expected_focus:
            raise RuntimeError('Reader toggle did not persist the exact current-tree neutral focus')
        # This is the sole additional exclusion. Keep taskView routes, its other
        # tree focus, all other buckets and every origin snapshot byte-equivalent.
        del targets[route['tree']]
    return preserved, history


def check_reader_toggle_transition(before, after, original, collapsed):
    check_reader_toggle_snapshot(after, collapsed)
    original_preserved = _reader_toggle_preserved(original, original['route']['node'])
    before_preserved = _reader_toggle_preserved(before, before['route']['node'] if collapsed else 'np-reader-toggle')
    after_preserved = _reader_toggle_preserved(after, 'np-reader-toggle' if collapsed else 'np-detail-scroll')
    if before_preserved != after_preserved or original_preserved != after_preserved:
        raise RuntimeError('Reader toggle changed preserved navigation state beyond the current neutral focus')
    for key in ('route', 'position', 'graphScale', 'expanded', 'taskContextKey', 'viewport', 'window'):
        if before[key] != after[key] or original[key] != after[key]:
            raise RuntimeError('Reader toggle changed preserved navigation state: ' + key)
    if after['title']['text'] != original['title']['text'] or after['selected']['label']['text'] != original['selected']['label']['text']:
        raise RuntimeError('Reader toggle substituted the selected branch title or row label')
    if after['focus'] != ('np-reader-toggle' if collapsed else 'np-detail-scroll'):
        raise RuntimeError('Reader toggle did not focus the visible disclosure or restored reader')
    for axis, scroll, maximum in (('x', 'left', 'maxLeft'), ('y', 'top', 'maxTop')):
        # Reflow may move content or reduce the scroll range. Preserve the immediately
        # preceding pixel anchor unless that exact position is beyond a legal endpoint.
        # Content coordinates are independently measured from the actual row and viewport.
        wanted = after['selected']['content'][axis] + after['tree']['client'][axis] - before['selected']['row']['rect'][axis]
        target = min(max(0, wanted), after['tree'][maximum])
        expected_anchor = after['selected']['content'][axis] + after['tree']['client'][axis] - target
        if (not _reader_close(after['tree'][scroll], target) or
                not _reader_close(after['selected']['row']['rect'][axis], expected_anchor)):
            raise RuntimeError('Reader toggle lost the selected-row anchor beyond legal scroll clamping: ' + axis)
    if not _reader_close(after['panels']['width'], original['panels']['width']):
        raise RuntimeError('Reader toggle changed the available panel width')
    if collapsed:
        recovered = after['treePane']['rect']['width'] - original['treePane']['rect']['width']
        if not _reader_close(recovered, original['reader']['proof']['rect']['width'] + original['columnGap']):
            raise RuntimeError('Collapsing the reader did not give its width and gap to the tree')
    else:
        if (not _reader_close(after['treePane']['rect']['width'], original['treePane']['rect']['width']) or
                not _reader_close(after['reader']['proof']['rect']['width'], original['reader']['proof']['rect']['width']) or
                after['reader']['scroll']['top'] != original['reader']['scroll']['top']):
            raise RuntimeError('Reopening the reader did not restore its width and original nonzero scroll')
    if (original['reader']['scroll']['top'] <= 0 or
            after['reader']['savedScroll'] != original['reader']['scroll']['top'] or
            after['reader']['persistedScroll'] != original['reader']['scroll']['top']):
        raise RuntimeError('Reader toggle lost the nonzero reader scroll in current/history snapshots')


def reader_toggle_checks(driver, report, save, capture, prefix):
    """Append two real-control scenes; keep diagnostics even when a new gate fails."""
    driver.settle()
    initial = driver.js(READER_TOGGLE_SNAPSHOT_JS)
    record = {'viewport': prefix, 'initial': initial, 'phases': []}
    report.setdefault('readerToggleChecks', []).append(record)
    save()
    check_reader_toggle_snapshot(initial, False)
    # Exercise a genuine nonzero reading offset using a WebDriver wheel action.
    # Do not call navigate(), write model/history/DOM state, or assign scrollTop.
    if initial['reader']['scroll']['top'] <= 0:
        try:
            driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 'reader-scroll', 'actions': [
                {'type': 'scroll', 'origin': driver.selector('#np-detail-scroll'), 'x': 0, 'y': 0,
                 'deltaX': 0, 'deltaY': 160, 'duration': 100}]}]})
            wait_for(lambda: driver.js("return document.getElementById('np-detail-scroll').scrollTop>0"), 5)
        finally:
            driver.settle()
            record['afterWheel'] = driver.js(READER_TOGGLE_SNAPSHOT_JS)
            save()
    before = original = driver.js(READER_TOGGLE_SNAPSHOT_JS)
    record['original'] = original
    save()
    check_reader_toggle_snapshot(original, False)
    if original['reader']['scroll']['top'] <= 0 or original['window'] != initial['window']:
        raise RuntimeError('Reader toggle setup did not obtain a nonzero internal reader scroll')
    original_elements = driver.js(READER_DOM_ELEMENTS_JS)
    for collapsed, scene in ((True, '-11b-reader-collapsed'), (False, '-11c-reader-reopened')):
        phase = {'scene': prefix + scene, 'before': before}
        record['phases'].append(phase)
        save()
        try:
            driver.click(driver.selector(READER_TOGGLE_SELECTOR))
            driver.settle()
        finally:
            phase['after'] = driver.js(READER_TOGGLE_SNAPSHOT_JS)
            save()
        after = phase['after']
        try:
            phase['domIdentity'] = driver.js(READER_DOM_IDENTITY_JS, original_elements)
        except Exception as exc:
            # A stale WebDriver reference itself proves that an original node was
            # replaced; retain that failure beside the already saved geometry.
            phase['domIdentityError'] = str(exc)[:2000]
            raise
        finally:
            save()
        check_reader_dom_identity(phase['domIdentity'])
        check_reader_toggle_transition(before, after, original, collapsed)
        capture(prefix + scene, require_tree=collapsed)
        before = after


TASK_ROUTE_PROOF_JS = VISUAL_GEOMETRY + r"""
var spec=arguments[0],matches=[...document.querySelectorAll(spec.selector)].filter(n=>spec.text===undefined||n.textContent===spec.text),
    e=matches.length===1?matches[0]:null,reader=document.getElementById(spec.region==='canvas'?'np-tree-scroll':'np-detail-scroll');
if(!e||!reader.contains(e))throw Error('Exact task-route proof is missing, duplicated or outside its measured region: '+JSON.stringify(spec));
var rr=rect(reader),heading=reader.querySelector('.np-reader-heading'),hr=heading?rect(heading):null,
    top=Math.max(rr.y+reader.clientTop,hr&&['sticky','fixed'].includes(getComputedStyle(heading).position)?hr.y+hr.height:rr.y+reader.clientTop),content={x:rr.x+reader.clientLeft,y:top,width:reader.clientWidth,height:Math.max(0,rr.y+reader.clientTop+reader.clientHeight-top)},b=box(e);
// A whole article's textContent cannot prove that a collapsed/hidden sentence is visible.
// Measure the original text itself, including every wrapped line, with a DOM Range.
var texts=[],walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),n;
while(n=walker.nextNode()){if(n.parentElement.closest('.np-sr'))continue;if(n.textContent.trim())texts.push(n);}
function clips(element){var result=[];for(var a=element;a&&a!==reader;a=a.parentElement){var cs=getComputedStyle(a);if(/auto|scroll|hidden|clip/.test(cs.overflowY+' '+cs.overflowX)){var ar=rect(a);result.push({x:ar.x+a.clientLeft,y:ar.y+a.clientTop,width:a.clientWidth,height:a.clientHeight});}}return result;}
var fragments=[],textRuns=[];
texts.forEach(n=>{var range=document.createRange();range.selectNodeContents(n);var parent=box(n.parentElement),run={text:n.textContent,fontSize:parent.fontSize,foreground:parent.foreground,background:parent.background,opaque:parent.opaque,unscaled:parent.unscaled,clipAreas:clips(n.parentElement),fragments:[]};[...range.getClientRects()].filter(r=>r.width>0&&r.height>0).forEach(r=>{var visible=parent.opaque&&parent.unscaled&&[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return hit===n.parentElement||n.parentElement.contains(hit);});var fragment={x:r.x,y:r.y,width:r.width,height:r.height,visible:visible};fragments.push(fragment);run.fragments.push(fragment);});textRuns.push(run);});
if(getComputedStyle(e).display==='inline'){b.visible=b.opaque&&fragments.length>0&&fragments.every(r=>r.visible);b.clipped=false;}
var ancestors=clips(e);
return Object.assign(b,{id:e.id,tag:e.tagName,disabled:!!e.disabled,href:e.tagName==='A'?e.href:null,
  renderedText:texts.map(n=>n.textContent).join(''),fragments:fragments,textRuns:textRuns,clipAreas:ancestors,
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},readerContent:content});
"""


TASK_ROUTE_RETURN_WAIT_JS = r"""
var a=NavigationProductApp,p=document.querySelector('[data-task-route-scope]'),actual=a.getState().route,expected=arguments[0];
// WebDriver object serialization may reorder keys. Retain every own route field,
// including null values, with the same key set and strict value/type identity.
function sameRoute(left,right){
  if(!left||!right||typeof left!=='object'||typeof right!=='object'||Array.isArray(left)||Array.isArray(right))return false;
  var keys=Object.keys(left).sort(),other=Object.keys(right).sort();
  return keys.length===other.length&&keys.every((key,i)=>key===other[i]&&left[key]===right[key]);
}
return sameRoute(actual,expected)&&p&&p.dataset.taskRouteState==='ready'&&document.activeElement.id===arguments[1]&&a.getContent().ready(a.getBundle().positions[actual.node].entityId)&&(!document.querySelector('[data-selected-task-relation]')||document.querySelector('[data-relation-state]')?.dataset.relationState==='ready');
"""


TASK_ROUTE_DIAGNOSTIC_JS = r"""
function taskRouteDiagnostic(api,model,state,reader,panel){
  function rect(node){if(!node)return null;var r=node.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
  function geometry(node){
    if(!node)return null;
    var cs=getComputedStyle(node),r=rect(node);
    return {id:node.id,tag:node.tagName,className:node.getAttribute('class'),rect:r,
      scrollTop:node.scrollTop,scrollLeft:node.scrollLeft,scrollHeight:node.scrollHeight,scrollWidth:node.scrollWidth,
      clientHeight:node.clientHeight,clientWidth:node.clientWidth,offsetHeight:node.offsetHeight,offsetWidth:node.offsetWidth,
      maxTop:Math.max(0,node.scrollHeight-node.clientHeight),maxLeft:Math.max(0,node.scrollWidth-node.clientWidth),
      style:{display:cs.display,visibility:cs.visibility,position:cs.position,font:cs.font,fontSize:cs.fontSize,lineHeight:cs.lineHeight,
        overflowX:cs.overflowX,overflowY:cs.overflowY,overflowAnchor:cs.overflowAnchor,scrollBehavior:cs.scrollBehavior,
        scrollbarGutter:cs.scrollbarGutter,boxSizing:cs.boxSizing,paddingTop:cs.paddingTop,paddingBottom:cs.paddingBottom,
        borderTopWidth:cs.borderTopWidth,borderBottomWidth:cs.borderBottomWidth,transform:cs.transform,zoom:cs.zoom}};
  }
  function bucket(value){return value?{focusTarget:value.focusTarget,windowScroll:value.windowScroll,
    detailScrollByTree:value.detailScrollByTree,treeScrollByTree:value.treeScrollByTree,treeScrollLeftByTree:value.treeScrollLeftByTree,
    selectedByTree:value.selectedByTree,expandedByTree:value.expandedByTree}:null;}
  function stateRecord(value){
    if(!value||!value.route||!value.contexts)return null;
    var key=model.contextKey(value.route);
    return {route:value.route,contextKey:key,revision:value.revision,bucket:bucket(value.contexts[key]),
      // After returning, this is the remaining trail. The popped entry is still
      // retained in the earlier activation receipt; it is not this last entry.
      originTrail:(value.originTrail||[]).map(e=>({route:e.route,bucket:bucket(e.bucket)}))};
  }
  function ancestors(node){var result=[];for(var n=node&&node.parentElement;n&&n!==reader;n=n.parentElement)if(n.tagName==='DETAILS')result.push({id:n.id,summaryId:n.querySelector(':scope > summary')?.id,open:n.open,geometry:geometry(n)});return result;}
  function target(node){return {id:node.id,position:node.dataset.changeTarget||node.closest('[data-route-method]')?.dataset.routeMethod||null,
    geometry:geometry(node),ancestorDisclosures:ancestors(node)};}
  function textGeometry(node){
    var range=document.createRange();range.selectNodeContents(node);var rs=typeof range.getClientRects==='function'?[...range.getClientRects()]:null;
    var nonempty=rs&&rs.filter(r=>r.width>0&&r.height>0),top=nonempty&&nonempty.length?Math.min(...nonempty.map(r=>r.y)):null,
        bottom=nonempty&&nonempty.length?Math.max(...nonempty.map(r=>r.y+r.height)):null;
    return {geometry:geometry(node),textLength:node.textContent.length,textStart:node.textContent.slice(0,160),
      textGeometryAvailable:rs!==null,textFragmentCount:nonempty?nonempty.length:null,textTop:top,textBottom:bottom,
      textHeight:top===null?null:bottom-top,ancestorDisclosures:ancestors(node)};
  }
  var runtime=stateRecord(state),persisted=stateRecord(history.state&&history.state[model.KEY]),heading=reader.querySelector('.np-reader-heading'),
      rr=reader.getBoundingClientRect(),hr=heading&&heading.getBoundingClientRect(),active=document.activeElement,
      focusId=model.getBucket(state).focusTarget,focus=focusId&&(document.getElementById(focusId)||document.getElementById('np-node-'+focusId));
  return {reader:geometry(reader),readerHeading:geometry(heading),
    availableContent:{x:rr.x+reader.clientLeft,y:Math.max(rr.y+reader.clientTop,hr?hr.y+hr.height:rr.y+reader.clientTop),
      bottom:rr.y+reader.clientTop+reader.clientHeight,width:reader.clientWidth},
    activeElement:active?target(active):null,runtimeFocusTarget:{value:focusId,element:focus?target(focus):null},
    targetControls:panel?[...panel.querySelectorAll('[data-change-target],[data-route-method] > button')].map(target):[],
    directReaderChildren:[...reader.children].map(geometry),taskOverview:geometry(panel),
    overviewBlocks:panel?[...panel.children].map(geometry):[],
    disclosures:[...reader.querySelectorAll('details')].map(e=>({id:e.id,summaryId:e.querySelector(':scope > summary')?.id,
      relation:e.dataset.taskChange||null,open:e.open,geometry:geometry(e),directChildren:[...e.children].map(geometry)})),
    textBlocks:[...reader.querySelectorAll('[data-task-route-scope] h2,[data-task-route-scope] h3,[data-task-route-scope] p,[data-task-route-scope] summary')].map(textGeometry),
    runtime:runtime,persisted:persisted,historyScrollRestoration:history.scrollRestoration,
    fonts:{status:document.fonts?document.fonts.status:null,faces:document.fonts?[...document.fonts].map(f=>({family:f.family,status:f.status,style:f.style,weight:f.weight,display:f.display})):[]},
    documentReadyState:document.readyState,timeOriginMs:performance.timeOrigin,relativeTimeMs:performance.now(),
    readerLayout:document.getElementById('navigation-product').dataset.readingLayout,
    restoring:{value:null,available:false,reason:'The controller keeps restoring in a private closure; no public getter exists.'}};
}
"""


TASK_ROUTE_SNAPSHOT_JS = TASK_ROUTE_DIAGNOSTIC_JS + r"""
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),b=a.getBundle(),reader=document.getElementById('np-detail-scroll'),
    tree=document.getElementById('np-tree-scroll'),host=document.getElementById('np-tree'),panel=document.querySelector('#np-task-route-canvas [data-task-route-scope]'),p=b.positions[s.route.node],mechanism=reader.querySelector('[data-mechanism-entity]'),bucket=m.getBucket(s);
function identity(p){return p?{id:p.id,entity:p.entityId,scope:p.scopeId,tree:p.tree,paper:p.paperId,version:p.versionId,kind:p.kind}:null;}
function domIdentity(e){var p=b.positions[e.dataset.position],v=identity(p);v.entity=e.dataset.entity;v.tree=e.dataset.tree;v.scope=e.closest('[data-scope-id]')?.dataset.scopeId||p.scopeId;return v;}
var all=[...host.querySelectorAll('[role=treeitem]')],methodKinds=['pipeline_recipe','versioned_method_card'],roots=b.forests[s.route.scope]?.l||[],groups=roots.flatMap(id=>b.positions[id].childIds).filter(id=>!methodKinds.includes(b.positions[id].kind)&&m.descendants(b,[id]).some(pid=>methodKinds.includes(b.positions[pid].kind))),selected=reader.querySelector('[data-selected-task-relation]');
return {route:s.route,position:identity(p),ready:document.querySelector('[data-load-state]').dataset.loadState,
  home:!document.getElementById('np-reading-landing').hidden,scale:bucket.graphScale,
  viewport:{width:innerWidth,height:innerHeight},window:{x:scrollX,y:scrollY},readerScroll:{top:reader.scrollTop,left:reader.scrollLeft},
  treeScroll:{top:tree.scrollTop,left:tree.scrollLeft},focus:document.activeElement.id,
  panelScope:panel&&panel.dataset.taskRouteScope,readerHidden:reader.hidden,canvasState:panel&&panel.dataset.taskRouteState,
  groups:all.filter(e=>groups.includes(e.dataset.position)).map(e=>e.dataset.position),
  groupReadiness:all.filter(e=>groups.includes(e.dataset.position)).map(e=>({position:e.dataset.position,entity:e.dataset.entity,ready:a.getContent().ready(e.dataset.entity)})),
  diagnostic:taskRouteDiagnostic(a,m,s,reader,panel),
  methods:all.filter(e=>methodKinds.includes(b.positions[e.dataset.position].kind)).map(e=>{var p=b.positions[e.dataset.position],stamp=e.querySelector(':scope > [data-route-association]');return {position:domIdentity(e),parent:e.dataset.parent,control:e.id,label:e.querySelector(':scope > .np-node-row > .np-node-label').textContent,association:stamp?.dataset.routeAssociation,version:stamp?.dataset.routeVersion,ready:a.getContent().ready(p.entityId)};}),
  mechanism:mechanism?{entity:mechanism.dataset.mechanismEntity,ready:a.getContent().ready(p.entityId),flow:[...mechanism.querySelectorAll('.np-method-flow dd')].map(e=>e.textContent),claims:[...mechanism.querySelectorAll('[data-method-claim]')].map(e=>({id:e.dataset.methodClaim,statement:e.querySelector(':scope > p').textContent}))}:null,
  changes:[...reader.querySelectorAll('[data-selected-task-relation]')].map(e=>({id:e.dataset.selectedTaskRelation,type:e.dataset.relationType,renderAsTree:e.dataset.renderAsTree,scope:e.dataset.changeScope,from:e.dataset.fromEntity,to:e.dataset.toEntity,open:!e.hidden,
    claims:[...e.querySelectorAll('[data-task-change-claim]')].map(c=>({id:c.dataset.taskChangeClaim,version:c.dataset.evidenceVersion,relation:c.dataset.versionRelation,statement:c.querySelector('.np-change-claim').textContent,sources:[...c.querySelectorAll('.np-source a')].map(a=>({url:a.href,status:a.nextElementSibling&&a.nextElementSibling.tagName==='SPAN'&&a.nextElementSibling.parentElement===a.parentElement?a.nextElementSibling.textContent:null}))})),
    targets:[...e.querySelectorAll('[data-change-target]')].map(c=>({position:c.dataset.changeTarget,control:c.id}))})),
  relationEntries:panel?[...panel.querySelectorAll('[data-task-change]')].map(e=>({id:e.dataset.taskChange,type:e.dataset.relationType,renderAsTree:e.dataset.renderAsTree,scope:e.dataset.changeScope,from:e.dataset.fromEntity,to:e.dataset.toEntity,control:e.id,selected:e.getAttribute('aria-pressed')})):[],
  selectedRelation:selected&&selected.dataset.selectedTaskRelation,relationState:reader.querySelector('[data-relation-state]')?.dataset.relationState||null,
  relationOverview:bucket.relationOverviewByTree||{},
  relationDisclosure:panel?{open:panel.open,tag:panel.tagName,id:panel.id,summary:panel.querySelector(':scope > summary')?.id,current:panel.dataset.currentRelationCount,outside:panel.dataset.outsideRelationCount,beforeTree:!!(panel.compareDocumentPosition(host)&Node.DOCUMENT_POSITION_FOLLOWING),insideTree:host.contains(panel)}:null,
  readerLists:reader.querySelectorAll('[data-route-method],[data-route-group],[data-task-route-scope]').length,
  activeTree:host.dataset.activeTaskTree||null,treeCount:host.querySelectorAll('[role=tree]').length,forestCount:host.querySelectorAll('[data-parallel-tree]').length,
  rovingCount:host.querySelectorAll('[role=treeitem][tabindex="0"]').length,inactiveItemCount:all.filter(e=>e.dataset.tree!==s.route.tree).length,
  selected:all.filter(e=>e.getAttribute('aria-selected')==='true').map(e=>e.dataset.position),expanded:bucket.expandedByTree,taskView:m.taskView(s),relationView:bucket.relationViewByTree||{},
  runtime:s,persisted:history.state&&history.state[m.KEY],historyLength:history.length,url:location.href,
  analysisEntry:reader.querySelector('[data-analysis-state]')?{state:reader.querySelector('[data-analysis-state]').dataset.analysisState,paper:reader.querySelector('[data-analysis-state]').dataset.analysisPaper,version:reader.querySelector('[data-analysis-state]').dataset.analysisVersion}:null,
  widths:{canvas:tree.getBoundingClientRect().width,tree:host.getBoundingClientRect().width,forest:host.querySelector('[data-parallel-tree]')?.getBoundingClientRect().width||0,reader:reader.getBoundingClientRect().width}};
"""


def task_route_expected(science):
    """Independent expectations from the already SHA-pinned original 9069 export."""
    def identity(p):
        return {k: p.get(v) for k, v in {'id': 'id', 'entity': 'entityId', 'scope': 'scopeId',
                'tree': 'tree', 'paper': 'paperId', 'version': 'versionId', 'kind': 'kind'}.items()}

    def descendants(pid):
        p = science['positions'][pid]
        return [p] + [v for cid in p['childIds'] for v in descendants(cid)]

    scopes = {}
    for sid in ('task:category-objectnav', 'task:imagenav', 'setting:portable-objectnav'):
        roots = science['forests'][sid]['l']
        rows = [p for root in roots for p in descendants(root) if p['kind'] in ('pipeline_recipe', 'versioned_method_card')]
        groups = [cid for root in roots for cid in science['positions'][root]['childIds']
                  if science['positions'][cid]['kind'] not in ('pipeline_recipe', 'versioned_method_card')
                  and any(p['kind'] in ('pipeline_recipe', 'versioned_method_card') for p in descendants(cid))]
        scopes[sid] = {'roots': roots, 'groups': groups, 'methods': [
            {'position': identity(p), 'parent': p['parentId'], 'association': p['association'],
             'version': p['versionId'], 'control': 'np-node-' + p['id']} for p in rows]}
        allowed_types = {'explicit_method_adaptation', 'explicit_component_reuse_and_policy_replacement',
            'explicit_mapping_reuse_with_alternative_search_scorer', 'editorial_route_comparison_only',
            'cited_baseline_and_problem_response', 'explicit_design_revision', 'cited_architectural_lineage_with_ablated_changes',
            'explicit_model_reuse', 'cited_architectural_response', 'cited_limitation_response_and_training_component_lineage',
            'explicit_framework_extension', 'cited_modular_transfer', 'cited_prior_and_shared_component_family'}
        papers = {p['paperId'] for p in rows}
        relations = []
        for rel in science['relations'].values():
            left, right = science['entities'].get(rel.get('from')), science['entities'].get(rel.get('to'))
            if (rel.get('renderAsTree') is not False or rel.get('relationType') not in allowed_types or
                    not left or not right or left.get('kind') != 'paper' or right.get('kind') != 'paper' or
                    not ({left.get('paperId'), right.get('paperId')} & papers)):
                continue
            relations.append({'id': rel['id'], 'type': rel['relationType'], 'renderAsTree': 'false',
                'scope': 'current-scope' if left.get('paperId') in papers and right.get('paperId') in papers else 'outside-scope',
                'from': rel['from'], 'to': rel['to'], 'control': 'np-task-change-' + sid + '-' + rel['id']})
        scopes[sid]['relations'] = sorted(relations, key=lambda r: (r['id'].rsplit(':', 1)[0], int(r['id'].rsplit(':', 1)[1])))

    def method(scope, entity):
        matches = [p for p in science['positions'].values() if p['tree'] == 'l' and p['scopeId'] == scope and p['entityId'] == entity]
        if len(matches) != 1:
            raise RuntimeError('Task-route source method identity is ambiguous: ' + entity)
        return matches[0]

    poni = method('task:category-objectnav', 'methods:pipeline-poni')
    relation = science['relations']['methods:relation:90']
    claim = science['claims']['method-edge:89']
    if (relation['detail']['claimIds'] != [claim['id']] or relation['renderAsTree'] is not False or
            claim['versionId'] != 'publication:poni:e83f98bb7132' or claim['versionId'] != poni['versionId']):
        raise RuntimeError('Task-route original PONI relation/claim/version contract changed')
    image = [method('task:imagenav', 'methods:pipeline-' + name) for name in ('zhu', 'sptm', 'ving')]
    portable = [method('setting:portable-objectnav', 'methods:pipeline-tap-' + name) for name in ('rl', 'llm')]
    if len({p['id'] for p in portable}) != 2 or len({p['entityId'] for p in portable}) != 2:
        raise RuntimeError('Portable source variants were merged')
    return {'scopes': scopes, 'poni': poni, 'relation': relation, 'claim': claim,
            'claimSourceStatus': ' · ' + science['versions'][claim['versionId']]['label'],
            'image': image, 'portable': portable}


def check_task_route_proof(proof, text=None):
    areas = [proof['viewport'], proof['readerContent']] + proof['clipAreas']
    if text is not None and proof['renderedText'] != text:
        raise RuntimeError('Task-route visible text differs from the original source field')
    if not _reader_proof(proof, *areas, font_size=15) or not proof['fragments'] or not proof['textRuns']:
        raise RuntimeError('Task-route proof is hidden, clipped, scaled, covered or below 15px')
    for run in proof['textRuns']:
        if (not run['opaque'] or not run['unscaled'] or run['fontSize'] < 15 or
                len(run['foreground']) != 3 or len(run['background']) != 3 or
                contrast_ratio(run['foreground'], run['background']) < 4.5 or not run['fragments']):
            raise RuntimeError('Task-route nested text is hidden, transparent, small or has no rendered fragment')
        if any(not f['visible'] or not all(rect_inside(f, area) for area in areas + run['clipAreas']) for f in run['fragments']):
            raise RuntimeError('Task-route nested text is clipped or covered inside its own ancestor')
    if any(not f['visible'] or not all(rect_inside(f, area) for area in areas) for f in proof['fragments']):
        raise RuntimeError('Task-route original text is not fully visible inside the reader')


def check_task_route_scope(data, scope, expected):
    if (data['ready'] != 'ready' or data['home'] or data['readerHidden'] or data['scale'] != 1 or
            (data['viewport']['width'], data['viewport']['height']) not in VIEWPORTS or
            data['route']['scope'] != scope or data['route']['tree'] != 'l' or
            data['route']['node'] not in expected['roots'] or data['route']['paper'] or data['route']['version'] or
            data['panelScope'] != scope or data['groups'] != expected['groups']):
        raise RuntimeError('Task-route root, scope, original groups or desktop reading state changed')
    if (data['activeTree'] != 'l' or data['treeCount'] != 1 or data['forestCount'] != 1 or
            data['rovingCount'] != 1 or data['inactiveItemCount'] or data['readerLists'] or
            data['canvasState'] != 'ready'):
        raise RuntimeError('Task-route inventory is not the single active source tree')
    actual = [{key: row[key] for key in ('position', 'parent', 'association', 'version', 'control')} for row in data['methods']]
    if actual != expected['methods'] or not all(row['ready'] for row in data['methods']):
        raise RuntimeError('Task-route methods differ from original positions or their content is not ready')
    actual_relations = [{k: r.get(k) for k in ('id', 'type', 'renderAsTree', 'scope', 'from', 'to', 'control')} for r in data['relationEntries']]
    if actual_relations != expected['relations']:
        raise RuntimeError('Task-root choices differ from the source-grounded typed relationship inventory')


def task_route_claims(science, position):
    entity = science['entities'][position['entityId']]
    ids = list(dict.fromkeys(position.get('claimIds', []) + entity.get('claimIds', [])))
    return [science['claims'][cid] for cid in ids if cid in science['claims'] and
            science['claims'][cid].get('paperId', position['paperId']) == position['paperId'] and
            science['claims'][cid].get('versionId', position['versionId']) == position['versionId']]


def check_task_route_method(data, position, entity, claims=()):
    if (data['ready'] != 'ready' or data['home'] or data['readerHidden'] or data['scale'] != 1 or
            any(data['route'][key] != position[other] for key, other in
                (('node', 'id'), ('scope', 'scopeId'), ('tree', 'tree'), ('paper', 'paperId'), ('version', 'versionId'))) or
            data['position']['entity'] != position['entityId'] or not data['mechanism'] or
            data['mechanism']['entity'] != position['entityId'] or not data['mechanism']['ready']):
        raise RuntimeError('Task-route method control opened the wrong source position or unready content')
    flow = entity.get('detail', {}).get('pipeline', {})
    if flow and data['mechanism']['flow'] != [flow[k] for k in ('input', 'representation', 'decision', 'execution', 'feedback') if flow.get(k)]:
        raise RuntimeError('Selected task-route method substituted its original pipeline fields')
    if not flow and (data['mechanism']['flow'] or data['mechanism']['claims'] != [{'id': c['id'], 'statement': c.get('statement') or c['label']} for c in claims]):
        raise RuntimeError('Selected task-route variant substituted its original method claims')


def check_task_route_relation(data, expected):
    rel, claim = expected['relation'], expected['claim']
    matches = [r for r in data['changes'] if r['id'] == rel['id']]
    if len(matches) != 1:
        raise RuntimeError('Exact task-route relation is absent or duplicated')
    row = matches[0]
    wanted = {'id': claim['id'], 'version': claim['versionId'], 'relation': 'same-version',
              'statement': claim['statement'], 'sources': [{'url': ref['url'], 'status': expected['claimSourceStatus']} for ref in claim['sourceRefs']]}
    if (row['type'] != rel['relationType'] or row['renderAsTree'] != 'false' or row['scope'] != 'current-scope' or
            not row['open'] or row.get('from') != rel['from'] or row.get('to') != rel['to'] or row['claims'] != [wanted] or
            not any(t['position'] == expected['poni']['id'] for t in row['targets'])):
        raise RuntimeError('Task-route relation lost exact claim, version, source or PONI endpoint')


def check_task_route_return(before, after, expected_control):
    for key in ('route', 'panelScope', 'scale', 'readerScroll', 'treeScroll', 'window', 'selectedRelation', 'expanded', 'relationOverview'):
        if before[key] != after[key]:
            raise RuntimeError('Task-route return lost saved context: ' + key)
    if before['activatedControl'] != expected_control or after['focus'] != expected_control:
        raise RuntimeError('Task-route return lost the exact activated control focus')


def transition_record(driver, record, save, kind, action, ready=None):
    """Save before/after even on action failure; never replace the original error."""
    phase = {'kind': kind, 'before': driver.js(TASK_ROUTE_SNAPSHOT_JS)}
    record.setdefault('transitions', []).append(phase)
    save()
    completed = False
    try:
        action()
        if ready:
            wait_for(ready)
        driver.settle()
        completed = True
    finally:
        diagnostic_error = None
        for name, script in (('after', TASK_ROUTE_SNAPSHOT_JS), ('origin', 'var trail=NavigationProductApp.getState().originTrail;return trail[trail.length-1]')):
            try:
                phase[name] = driver.js(script)
            except Exception as exc:
                phase[name + 'Error'] = str(exc)[:2000]
                diagnostic_error = diagnostic_error or exc
        try:
            save()
        except Exception as exc:
            phase['saveError'] = str(exc)[:2000]
            diagnostic_error = diagnostic_error or exc
        if completed and diagnostic_error:
            raise diagnostic_error
    return phase


def tree_label_selector(position):
    return '[id="np-node-' + position + '"] > .np-node-row > .np-node-label'


def reveal_control(driver, spec):
    element = driver.js("var s=arguments[0],all=[...document.querySelectorAll(s.selector)].filter(n=>s.text===undefined||n.textContent===s.text);if(all.length!==1)throw Error('Exact visible control absent or duplicated');return all[0];", spec)
    driver.js("arguments[0].scrollIntoView({block:'center',inline:'nearest'});", element)
    driver.settle()
    return element


def expose_source_position(driver, position, record, save):
    """Expand only actual ancestor toggles; expected path comes from the source model."""
    path = driver.js("var b=NavigationProductApp.getBundle(),p=b.positions[arguments[0]],ids=[];while(p){ids.unshift(p.id);p=b.positions[p.parentId]}return ids;", position)
    for ancestor in path[:-1]:
        selector = '[id="np-node-' + ancestor + '"] > .np-node-row > .np-node-toggle'
        if driver.js("return document.getElementById('np-node-'+arguments[0])?.getAttribute('aria-expanded')==='false';", ancestor):
            transition_record(driver, record, save, 'expand-source-ancestor',
                              lambda s=selector: driver.click(reveal_control(driver, {'selector': s})))
    return reveal_control(driver, {'selector': tree_label_selector(position)})


def check_exploration_restore(before, after, focus=None, nonzero=False, inactive_before=None):
    for key in ('route', 'selectedRelation', 'expanded', 'treeScroll', 'readerScroll', 'window', 'relationOverview', 'relationView', 'scale'):
        if before[key] != after[key]:
            raise RuntimeError('Exploration restore changed ' + key)
    if after['focus'] != (focus or before['focus']):
        raise RuntimeError('Exploration restore changed the exact focused control')
    if nonzero and before['treeScroll']['top'] <= 0:
        raise RuntimeError('Independent tree restore was not tested at nonzero scroll')
    if after['route']['tree'] in ('l', 'c'):
        tree = after['route']['tree']
        view = after['taskView']
        expected_focus = after['focus'][len('np-node-'):] if after['focus'].startswith('np-node-') else after['focus']
        if (not view or view['lastRouteByTree'][tree] != after['route'] or
                view['focusTargetByTree'][tree] != expected_focus or
                after['treeCount'] != 1 or after['forestCount'] != 1 or
                after['rovingCount'] != 1 or after['inactiveItemCount']):
            raise RuntimeError('Restored neutral task view or single keyboard scope is stale')
        key = json.dumps([after['route'].get(k) for k in ('scope', 'bench', 'protocol', 'paper', 'version', 'template')], separators=(',', ':'), ensure_ascii=False)
        persisted = after['persisted']
        if not persisted or persisted['route'] != after['route'] or persisted['contexts'].get(key) != after['runtime']['contexts'].get(key):
            raise RuntimeError('Restored exact context was not persisted')
        neutral = json.dumps([after['route'].get(k) for k in ('scope', 'bench', 'protocol')] + [None, None, None], separators=(',', ':'), ensure_ascii=False)
        if (persisted['contexts'].get(neutral) != after['runtime']['contexts'].get(neutral) or
                after['runtime']['contexts'].get(neutral, {}).get('taskView') != view):
            raise RuntimeError('Restored neutral task pointer was not independently persisted')
        other = 'c' if tree == 'l' else 'l'
        inactive = (inactive_before or before)['taskView']
        if inactive and any(view[field][other] != inactive[field][other] for field in ('lastRouteByTree', 'focusTargetByTree')):
            raise RuntimeError('Current view restore overwrote the inactive tree route or focus pointer')


def task_route_checks(driver, report, save, capture, prefix, base, science, server=None, dist=None):
    """Actual active-tree traversal, selected relation, method, claim and return."""
    expected = task_route_expected(science)
    record = {'viewport': prefix, 'scenes': [], 'inventories': [], 'sceneLimit': 22}
    report.setdefault('taskRouteChecks', []).append(record)
    save()

    def snapshot():
        return driver.js(TASK_ROUTE_SNAPSHOT_JS)

    def proof(spec):
        return driver.js(TASK_ROUTE_PROOF_JS, spec)

    def scene(name, specs, method=None, relation=False, scroll=True):
        item = {'name': prefix + name, 'specs': specs, 'proofs': [], 'phase': 'before-proof', 'before': snapshot()}
        record['scenes'].append(item)
        save()
        completed = False
        try:
            if scroll:
                reveal_control(driver, specs[0])
                for _ in range(4):
                    boxes = [proof(spec) for spec in specs]
                    # One photographed proof set always belongs to one region.
                    area = boxes[0]['readerContent']
                    top, bottom = min(b['rect']['y'] for b in boxes), max(b['rect']['y'] + b['rect']['height'] for b in boxes)
                    if top >= area['y'] and bottom <= area['y'] + area['height']:
                        break
                    delta = round((top + bottom - 2 * area['y'] - area['height']) / 2)
                    if bottom - top > area['height'] or not delta:
                        break
                    region = '#np-tree-scroll' if specs[0].get('region') == 'canvas' else '#np-detail-scroll'
                    transition_record(driver, record, save, 'align-selected-object-with-wheel', lambda: driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 'selected-object-scroll', 'actions': [{'type': 'scroll', 'origin': driver.selector(region), 'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': delta, 'duration': 100}]}]}))
            item['state'] = snapshot()
            item['proofs'] = driver.js(TASK_DENSITY_PROOFS_JS, specs)
            save()
            if not specs or [row['spec'] for row in item['proofs']] != specs:
                raise RuntimeError('Selected-object proof batch is incomplete or reordered')
            if method:
                check_task_route_method(item['state'], method, science['entities'][method['entityId']], task_route_claims(science, method))
            if relation:
                check_task_route_relation(item['state'], expected)
            for row in item['proofs']:
                if 'error' in row:
                    raise RuntimeError(row['error'])
                check_task_route_proof(row['actual'], row['spec'].get('renderedText', row['spec'].get('text')))
                if row['spec'].get('href') and row['actual']['href'] != row['spec']['href']:
                    raise RuntimeError('Selected-object source URL differs from the original source')
            capture(item['name'], require_tree=specs[0].get('region') == 'canvas')
            item['afterProofs'] = driver.js(TASK_DENSITY_PROOFS_JS, specs)
            save()
            if item['proofs'] != item['afterProofs']:
                raise RuntimeError('Selected-object photographed text or geometry changed during capture')
            completed = True
            item['phase'] = 'captured'
        finally:
            try:
                item['after'] = snapshot()
                save()
            except Exception as exc:
                item['diagnosticError'] = str(exc)[:2000]
                if completed:
                    raise
        return item['state']

    def open_scope(sid, directory=False):
        driver.call('POST', '/url', {'url': base})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
        if directory:
            driver.click(driver.selector('#np-all-scopes > summary'))
        selector = '[data-' + ('scope' if directory else 'task') + '-open="' + sid + '"]'
        transition_record(driver, record, save, 'open-source-scope', lambda: driver.click(reveal_control(driver, {'selector': selector})),
                          lambda: driver.js("var a=NavigationProductApp,r=a.getState().route,p=document.querySelector('#np-task-route-canvas [data-task-route-scope]');return r.scope===arguments[0]&&r.tree==='l'&&p?.dataset.taskRouteScope===arguments[0]&&p.dataset.taskRouteState==='ready'&&a.getContent().ready(a.getBundle().positions[r.node].entityId);", sid))

    def inventory(sid):
        wanted = expected['scopes'][sid]
        item = {'scope': sid, 'reachable': []}
        record['inventories'].append(item)
        save()
        for row in wanted['methods']:
            expose_source_position(driver, row['position']['id'], record, save)
            spec = {'selector': tree_label_selector(row['position']['id']), 'region': 'canvas'}
            actual = proof(spec)
            item['reachable'].append({'position': row['position'], 'proof': actual})
            save()
            check_task_route_proof(actual)
        item['state'] = snapshot()
        save()
        check_task_route_scope(item['state'], sid, wanted)

    def select_method(position, selector=None):
        element = reveal_control(driver, {'selector': selector}) if selector else expose_source_position(driver, position['id'], record, save)
        before = snapshot()
        before['activatedControl'] = driver.js("return arguments[0].id||arguments[0].closest('[role=treeitem]').id;", element)
        before['originFocusTarget'] = driver.js("return arguments[0].closest('[data-position]')?.dataset.position||arguments[0].id;", element)
        phase = transition_record(driver, record, save, 'select-exact-method', lambda: driver.click(element),
            lambda: driver.js("var a=NavigationProductApp,p=arguments[0],r=a.getState().route,m=document.querySelector('[data-mechanism-entity]');return r.node===p.id&&r.scope===p.scopeId&&r.tree===p.tree&&r.paper===p.paperId&&r.version===p.versionId&&a.getContent().ready(p.entityId)&&m?.dataset.mechanismEntity===p.entityId;", position))
        origin = phase['origin']
        if not origin or origin['route'] != before['route'] or origin['bucket']['focusTarget'] != before['originFocusTarget']:
            raise RuntimeError('Method click lost its exact original route/control')
        return before

    def return_method(before):
        phase = transition_record(driver, record, save, 'explicit-return-method-origin', lambda: driver.click(driver.selector('.np-return-previous')),
            lambda: driver.js(TASK_ROUTE_RETURN_WAIT_JS, before['route'], before['activatedControl']))
        check_task_route_return(before, phase['after'], before['activatedControl'])

    poni = expected['poni']
    open_scope(poni['scopeId'])
    inventory(poni['scopeId'])
    transition_record(driver, record, save, 'open-method-relationship-disclosure',
        lambda: driver.click(reveal_control(driver, {'selector': '#np-task-route-relations-summary'})),
        lambda: driver.js("return document.getElementById('np-task-route-relations').open"))
    selector = '[data-task-change="methods:relation:90"]'
    entry = reveal_control(driver, {'selector': selector})
    before_relation = snapshot()
    phase = transition_record(driver, record, save, 'select-methods-relation-90', lambda: driver.click(entry),
        lambda: driver.js("return document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
    if phase['after']['route'] != before_relation['route'] or phase['after']['historyLength'] != before_relation['historyLength'] + 1 or phase['after']['runtime']['revision'] <= before_relation['runtime']['revision']:
        raise RuntimeError('Relation selection changed science or failed to create its presentation history entry')
    rel = '[data-selected-task-relation="methods:relation:90"]'
    claim = expected['claim']
    cs = rel + ' [data-task-change-claim="' + claim['id'] + '"]'
    specs = [{'selector': rel + ' > h2', 'text': 'SemExp → PONI · 复用组件并替换策略'},
             {'selector': cs + ' .np-change-claim', 'text': claim['statement']},
             {'selector': cs + ' > p', 'text': '原文定位：' + '；'.join(claim['locator'])},
             {'selector': cs + ' .np-source a', 'renderedText': '；'.join(claim['sourceRefs'][0]['locator']) + ' ↗', 'href': claim['sourceRefs'][0]['url']},
             {'selector': cs + ' .np-source > a + span', 'text': expected['claimSourceStatus']}]
    scene('-22-methods-relation-90', specs, relation=True)
    before = select_method(poni, rel + ' [data-change-target="' + poni['id'] + '"]')
    flow = science['entities'][poni['entityId']]['detail']['pipeline']
    scene('-23-poni-method', [{'selector': '[data-mechanism-entity="' + poni['entityId'] + '"] .np-method-flow dd', 'text': flow['representation']}], method=poni)
    # Pin the actual method claim with the product's real evidence control.
    method_claim = task_route_claims(science, poni)[0]
    transition_record(driver, record, save, 'open-method-evidence', lambda: driver.click(reveal_control(driver, {'selector': '[data-mechanism-entity] > .np-text-button'})))
    disclosure = '#np-detail-content .np-evidence'
    if not driver.js('return document.querySelector(arguments[0]).open', disclosure):
        transition_record(driver, record, save, 'open-claim-disclosure', lambda: driver.click(reveal_control(driver, {'selector': disclosure + ' > summary'})))
    pinned = disclosure + ' [data-claim-id="' + method_claim['id'] + '"]'
    transition_record(driver, record, save, 'pin-exact-method-claim', lambda: driver.click(reveal_control(driver, {'selector': pinned + ' > button'})),
        lambda: driver.js('return NavigationProductApp.getState().route.claim===arguments[0]', method_claim['id']))
    scene('-24-poni-claim', [{'selector': pinned + ' > p:first-child', 'text': method_claim['statement']}], method=poni)
    claim_state = snapshot()
    return_method(before)
    scene('-25-return-methods-relation-90', [{'selector': rel + ' [data-change-target="' + poni['id'] + '"]'}], relation=True, scroll=False)
    restored_relation = snapshot()
    # Back/Forward is independent of the explicit return above.
    transition_record(driver, record, save, 'browser-back-to-claim', lambda: driver.call('POST', '/back', {}),
        lambda: driver.js('return NavigationProductApp.getState().route.claim===arguments[0]', method_claim['id']))
    if snapshot()['route'] != claim_state['route']:
        raise RuntimeError('Back from relation return lost exact method claim identity')
    transition_record(driver, record, save, 'browser-forward-to-relation', lambda: driver.call('POST', '/forward', {}),
        lambda: driver.js(TASK_ROUTE_RETURN_WAIT_JS, before['route'], before['activatedControl']))
    check_exploration_restore(restored_relation, snapshot())
    phase = transition_record(driver, record, save, 'cold-selected-relation', lambda: driver.call('POST', '/refresh', {}),
        lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
    check_exploration_restore(restored_relation, phase['after'])
    transition_record(driver, record, save, 'relation-to-task', lambda: driver.click(driver.selector('#np-task-route-return')),
        lambda: driver.js("return !document.querySelector('[data-selected-task-relation]')&&document.activeElement.id===arguments[0]", 'np-task-change-task:category-objectnav-methods:relation:90'))
    scene('-26-return-objectnav-task', [{'selector': selector, 'region': 'canvas'}], scroll=False)
    transition_record(driver, record, save, 'task-to-global', lambda: driver.click(driver.selector('[data-tree-tab="g"]')),
        lambda: driver.js('return !document.getElementById("np-reading-landing").hidden'))
    if driver.js('return NavigationProductApp.getState().route.paper') is not None:
        raise RuntimeError('Return to S0 retained a paper evidence selection')

    open_scope('task:imagenav')
    inventory('task:imagenav')
    for p in expected['image']:
        parent = science['positions'][p['parentId']]
        if p['paperId'] in ('zhu', 'sptm'):
            element = expose_source_position(driver, parent['id'], record, save)
            transition_record(driver, record, save, 'select-original-route-group', lambda: driver.click(element),
                lambda: driver.js('var a=NavigationProductApp;return a.getState().route.node===arguments[0]&&a.getContent().ready(arguments[1])', parent['id'], parent['entityId']))
            evidence = science['entities'][parent['entityId']]['detail']['evidence']
            scene('-27-imagenav-' + p['paperId'] + '-route-condition', [{'selector': '#np-reader-summary .np-node-meaning .np-detail-block > p', 'text': evidence}])
            # Explicitly return to the task snapshot before choosing a method.
            transition_record(driver, record, save, 'return-route-group', lambda: driver.click(driver.selector('[data-path-kind="local-ancestry"] [data-context-position="' + expected['scopes']['task:imagenav']['roots'][0] + '"]')),
                lambda: driver.js('return NavigationProductApp.getState().route.node===arguments[0]', expected['scopes']['task:imagenav']['roots'][0]))
        before = select_method(p)
        flow = science['entities'][p['entityId']]['detail']['pipeline']
        scene('-27-imagenav-' + p['paperId'],
              [{'selector': '[data-mechanism-entity="' + p['entityId'] + '"] .np-reading-association', 'text': '条件关联，不能按同一任务或同一评测协议理解。'}] +
              [{'selector': '[data-mechanism-entity="' + p['entityId'] + '"] .np-method-flow dd', 'text': flow[k]} for k in ('input', 'representation', 'decision')], method=p)
        return_method(before)

    open_scope('setting:portable-objectnav', directory=True)
    inventory('setting:portable-objectnav')
    for p in expected['portable']:
        before = select_method(p)
        claim = task_route_claims(science, p)[0]
        scene('-28-portable-' + p['entityId'].split('pipeline-tap-')[-1],
              [{'selector': '[data-mechanism-entity="' + p['entityId'] + '"] > h3', 'text': science['entities'][p['entityId']]['label'] + ' · 方法内部结构'},
               {'selector': '[data-method-claim="' + claim['id'] + '"] > p:first-child', 'text': claim['statement']}], method=p)
        return_method(before)
    if server is not None:
        for interrupt in ('none', 'wheel', 'scope'):
            open_scope(poni['scopeId'])
            transition_record(driver, record, save, 'open-delayed-relation-disclosure', lambda: driver.click(driver.selector('#np-task-route-relations-summary')))
            transition_record(driver, record, save, 'select-delayed-relation', lambda: driver.click(reveal_control(driver, {'selector': selector})),
                lambda: driver.js("return document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
            packet = driver.js('return NavigationProductApp.getBundle().delivery.packets[arguments[0]]', poni['entityId'])
            delayed = {'interrupt': interrupt, 'before': snapshot(), 'packetSha256': packet['sha256']}
            record.setdefault('delayedRestore', []).append(delayed)
            save()
            completed = False
            with PacketHold(server, '/research/navigation/content/' + packet['sha256'] + '.json', dist, packet['sha256']) as hold:
                try:
                    driver.call('POST', '/refresh', {})
                    wait_for(lambda: hold.seen.is_set(), timeout=5)
                    wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-relation-state]')?.dataset.relationState==='loading'"), timeout=5)
                    delayed['pending'] = snapshot()
                    save()
                    if interrupt == 'wheel':
                        driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 'newer-reader-input', 'actions': [{'type': 'scroll', 'origin': driver.selector('#np-tree-scroll'), 'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': 160, 'duration': 80}]}]})
                        driver.settle()
                        delayed['newer'] = snapshot()
                        if delayed['newer']['treeScroll'] == delayed['pending']['treeScroll']:
                            raise RuntimeError('Interrupted cold restore was not exercised by an actual scroll')
                    elif interrupt == 'scope':
                        driver.click(driver.selector('[data-tree-tab="g"]'))
                        wait_for(lambda: driver.js('return !document.getElementById("np-reading-landing").hidden'))
                        driver.click(driver.selector('[data-task-open="task:imagenav"]'))
                        wait_for(lambda: driver.js("return NavigationProductApp.getState().route.scope==='task:imagenav'&&document.querySelector('[data-task-route-state=ready]')"))
                        driver.settle()
                        delayed['newer'] = snapshot()
                    hold.released.set()
                    wait_for(lambda: driver.js('return NavigationProductApp.getContent().ready(arguments[0])', poni['entityId']))
                    driver.settle()
                    delayed['after'] = snapshot()
                    delayed['holdExpired'] = hold.expired
                    save()
                    if hold.expired:
                        raise RuntimeError('Bounded loopback hold expired before the planned user action')
                    if interrupt == 'none':
                        check_exploration_restore(delayed['before'], delayed['after'])
                    else:
                        for key in ('route', 'treeScroll', 'readerScroll', 'window', 'focus', 'taskView'):
                            if delayed['newer'][key] != delayed['after'][key]:
                                raise RuntimeError('Delayed old content overrode newer ' + interrupt + ': ' + key)
                    completed = True
                finally:
                    hold.released.set()
                    try:
                        delayed['final'] = snapshot()
                        save()
                    except Exception as exc:
                        delayed['diagnosticError'] = str(exc)[:2000]
                        if completed:
                            raise
    if len(record['scenes']) > record['sceneLimit']:
        raise RuntimeError('Selected-object screenshot plan exceeded its declared bound')


TASK_DENSITY_SNAPSHOT_JS = 'var original=(function(){' + TASK_ROUTE_SNAPSHOT_JS + r"""
}).call(null);
var a=NavigationProductApp,reader=document.getElementById('np-detail-scroll'),tree=document.getElementById('np-tree-scroll');
return Object.assign(original,{density:{state:original.canvasState,
  selectedReady:a.getContent().ready(a.getBundle().positions[original.route.node].entityId),
  internalScroll:[reader,tree,...reader.querySelectorAll('*'),...tree.querySelectorAll('*')].filter(e=>{var s=getComputedStyle(e);return e===reader||e===tree||/auto|scroll|hidden|clip/.test(s.overflowX+' '+s.overflowY)||e.scrollTop||e.scrollLeft;}).map(e=>({id:e.id,className:e.className,top:e.scrollTop,left:e.scrollLeft})),
  roots:[...document.querySelectorAll('#np-tree [data-parallel-tree] > [role=tree] > [role=treeitem]')].map(e=>e.dataset.position),
  gap:document.querySelector('#np-tree .np-parallel-gap')?.textContent||null}});
"""


# All photographed fields are measured in the same synchronous browser task.
TASK_DENSITY_PROOFS_JS = 'return arguments[0].map(spec=>{try{return {spec:spec,actual:(function(){' + TASK_ROUTE_PROOF_JS + r"""
}).call(null,spec)};}catch(error){return {spec:spec,error:String(error)};}});
"""


def task_density_expected(science):
    """Four bounded natural main-canvas entries; details are checked after selection."""
    original = task_route_expected(science)
    cases = []
    def label(pid):
        return {'selector': tree_label_selector(pid), 'region': 'canvas', 'text': science['positions'][pid]['label'].removesuffix(' 输入到反馈')}
    for sid, name in (('task:category-objectnav', 'objectnav-routes'), ('task:imagenav', 'imagenav-routes'), ('setting:portable-objectnav', 'portable-variants')):
        expected = original['scopes'][sid]
        local_count = sum(r['scope'] == 'current-scope' for r in expected['relations'])
        outside_count = len(expected['relations']) - local_count
        summary = '方法之间的已核关系（' + str(local_count) + '）' + (' · 范围外关联（' + str(outside_count) + '）' if outside_count else '')
        proofs = [{'selector': '#np-task-route-relations-summary', 'region': 'canvas', 'text': summary}, label(expected['roots'][0])]
        if sid == 'task:category-objectnav':
            proofs += [label(expected['groups'][0]), {'selector': tree_label_selector(original['poni']['id']), 'region': 'canvas', 'text': 'PONI'}]
        elif sid == 'task:imagenav':
            proofs += [label(pid) for pid in expected['groups'][:2]]
        else:
            proofs += [label(p['id']) for p in original['portable']]
            proofs += [{'selector': '[id="np-node-' + p['id'] + '"] > [data-route-version] > span:nth-child(2)', 'region': 'canvas', 'text': ' · ' + science['versions'][p['versionId']]['label']} for p in original['portable']]
        cases.append({'scope': sid, 'name': name, 'directory': sid.startswith('setting:'), 'expected': expected, 'proofs': proofs})
    sid = 'task:aerial-visual-object-search'
    roots = science['forests'][sid]['l']
    if any(science['positions'][pid]['childIds'] for pid in roots):
        raise RuntimeError('AVOS source inventory changed; review the natural-entry contract')
    cases.append({'scope': sid, 'name': 'avos-inventory-gap', 'expected': {'roots': roots, 'groups': [], 'methods': [], 'relations': []},
                  'proofs': [{'selector': '#np-task-route-relations-summary', 'region': 'canvas', 'text': '方法之间的已核关系（0）'}, label(roots[0]), {'selector': '#np-tree .np-parallel-gap', 'region': 'canvas', 'text': '当前范围尚无已整理的方法分枝；保留任务定义和原文入口。'}], 'empty': True})
    return cases


def check_task_density_snapshot(data, case):
    expected = case['expected']
    if (data['ready'] != 'ready' or data['home'] or data['readerHidden'] or data['scale'] != 1 or
            (data['viewport']['width'], data['viewport']['height']) not in VIEWPORTS or
            data['route']['scope'] != case['scope'] or data['route']['tree'] != 'l' or
            data['route']['node'] not in expected['roots'] or data['route']['paper'] or data['route']['version'] or
            data['panelScope'] != case['scope'] or data['density']['roots'] != expected['roots'] or
            data['density']['state'] != 'ready' or not data['density']['selectedReady'] or
            data['activeTree'] != 'l' or data['treeCount'] != 1 or data['forestCount'] != 1 or
            data['rovingCount'] != 1 or data['inactiveItemCount'] or data['readerLists'] or data['selectedRelation'] or
            data['readerScroll'] != {'top': 0, 'left': 0} or data['treeScroll'] != {'top': 0, 'left': 0} or
            any(p['top'] != 0 or p['left'] != 0 for p in data['density']['internalScroll'])):
        raise RuntimeError('Natural entry is not its ready, unscrolled, single-tree task root')
    known = {r['position']['id']: r for r in expected['methods']}
    for row in data['methods']:
        if row['position']['id'] not in known or any(row[k] != known[row['position']['id']][k] for k in ('position', 'parent', 'association', 'version', 'control')) or not row['ready']:
            raise RuntimeError('Natural canvas substituted a source method identity or version')
    if len({r['position']['id'] for r in data['methods']}) != len(data['methods']):
        raise RuntimeError('Natural canvas duplicates a source method')
    disclosure = data['relationDisclosure']
    local_count = sum(r['scope'] == 'current-scope' for r in expected['relations'])
    if (not disclosure or disclosure['tag'] != 'DETAILS' or disclosure['open'] or
            disclosure['id'] != 'np-task-route-relations' or disclosure['summary'] != 'np-task-route-relations-summary' or
            not disclosure['beforeTree'] or disclosure['insideTree'] or
            disclosure['current'] != str(local_count) or disclosure['outside'] != str(len(expected['relations']) - local_count)):
        raise RuntimeError('Natural relationship disclosure is misplaced, expanded or miscounts source relationships')
    actual_relations = [{k: r.get(k) for k in ('id', 'type', 'renderAsTree', 'scope', 'from', 'to', 'control')} for r in data['relationEntries']]
    if actual_relations != expected['relations']:
        raise RuntimeError('Natural relationship choices changed exact namespace, type, endpoints or scope')
    if case.get('empty') and (data['methods'] or data['relationEntries'] or data['changes'] or not data['density']['gap']):
        raise RuntimeError('Natural AVOS view invents methods or relations for an empty inventory')


def task_density_checks(driver, report, save, capture, prefix, base, science):
    """Four natural entry viewports; no scroll, reveal, fit, focus or disclosure setup."""
    cases = task_density_expected(science)
    record = {'viewport': prefix, 'capturesExpected': 4, 'scenes': [],
              'screenKind': 'natural_initial_task_workspace', 'documentTopClaimed': False}
    report.setdefault('taskDensityChecks', []).append(record)
    save()
    for case in cases:
        item = {'scope': case['scope'], 'name': prefix + '-21-initial-' + case['name'], 'actions': [], 'proofs': []}
        record['scenes'].append(item)

        def action(kind, **details):
            item['actions'].append(dict(kind=kind, **details))
            save()

        def snapshot_diagnostics(key, preserve_error):
            failure = None
            try:
                item[key] = driver.js(TASK_DENSITY_SNAPSHOT_JS)
                if key == 'initial':
                    item['naturalEntryWindow'] = item[key]['window']
            except Exception as exc:
                item[key + 'SnapshotError'] = str(exc)[:2000]
                failure = exc
            try:
                save()
            except Exception as exc:
                item[key + 'SaveError'] = str(exc)[:2000]
                failure = failure or exc
            if failure is not None and not preserve_error:
                raise failure

        action('navigate-home', url=base)
        driver.call('POST', '/url', {'url': base})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'&&!document.getElementById('np-reading-landing').hidden"))
        if case.get('directory'):
            action('click-directory-disclosure', selector='#np-all-scopes > summary')
            driver.click(driver.selector('#np-all-scopes > summary'))
        selector = '[data-' + ('scope' if case.get('directory') else 'task') + '-open="' + case['scope'] + '"]'
        action('click-task-entry', selector=selector)
        entry_completed = False
        try:
            driver.click(driver.selector(selector))
            action('wait-root-content')
            wait_for(lambda: driver.js("var a=NavigationProductApp,r=a.getState().route,p=document.querySelector('#np-task-route-canvas [data-task-route-scope]'),wanted=arguments[1];return r.scope===arguments[0]&&r.tree==='l'&&wanted.roots.includes(r.node)&&a.getContent().ready(a.getBundle().positions[r.node].entityId)&&p?.dataset.taskRouteScope===arguments[0]&&p.dataset.taskRouteState==='ready';", case['scope'], case['expected']))
            driver.settle()
            entry_completed = True
        finally:
            item['actions'].append({'kind': 'read-natural-entry'})
            snapshot_diagnostics('initial', preserve_error=not entry_completed)
        check_task_density_snapshot(item['initial'], case)

        def read_proofs(key):
            action('read-visible-proof-batch', phase=key, selectors=[s['selector'] for s in case['proofs']])
            item[key] = driver.js(TASK_DENSITY_PROOFS_JS, case['proofs'])
            save()
            if [p['spec'] for p in item[key]] != case['proofs']:
                raise RuntimeError('Natural task-entry proof set changed')
            for row in item[key]:
                if 'error' in row:
                    raise RuntimeError(row['error'])
                check_task_route_proof(row['actual'], row['spec']['text'])

        read_proofs('proofs')
        action('capture-natural-entry')
        capture_completed = False
        try:
            capture(item['name'], require_tree=False)
            capture_completed = True
        finally:
            snapshot_diagnostics('afterCapture', preserve_error=not capture_completed)
        check_task_density_snapshot(item['afterCapture'], case)
        read_proofs('afterCaptureProofs')
        if item['proofs'] != item['afterCaptureProofs']:
            raise RuntimeError('Natural task-entry fields changed visibility or geometry across capture')
        for key in ('route', 'readerScroll', 'treeScroll', 'window', 'focus', 'scale'):
            if item['initial'][key] != item['afterCapture'][key]:
                raise RuntimeError('Natural task-entry screenshot changed its initial view: ' + key)
        item['status'] = 'captured_for_human_review'
        save()


def exploration_state_checks(driver, report, save, capture, prefix, base, science):
    """Independent per-view scroll/focus, source A, old links and cold identity."""
    record = {'viewport': prefix, 'scenes': [], 'deepLinks': []}
    report.setdefault('explorationStateChecks', []).append(record)
    expected = task_route_expected(science)

    def snapshot():
        return driver.js(TASK_ROUTE_SNAPSHOT_JS)

    def analysis_scene(name, specs):
        item = {'name': prefix + name, 'specs': specs, 'before': snapshot(), 'screenKind': 'selected_analysis_scrolled'}
        record['scenes'].append(item)
        save()
        completed = False
        try:
            reveal_control(driver, specs[0])
            item['proofs'] = driver.js(TASK_DENSITY_PROOFS_JS, specs)
            save()
            if not specs or [row['spec'] for row in item['proofs']] != specs:
                raise RuntimeError('Analysis proof batch is incomplete or reordered')
            for row in item['proofs']:
                if 'error' in row:
                    raise RuntimeError(row['error'])
                check_task_route_proof(row['actual'], row['spec']['text'])
            capture(item['name'], require_tree=False)
            item['afterProofs'] = driver.js(TASK_DENSITY_PROOFS_JS, specs)
            save()
            if item['proofs'] != item['afterProofs']:
                raise RuntimeError('Analysis identity text changed visibility during capture')
            completed = True
        finally:
            try:
                item['after'] = snapshot()
                save()
            except Exception as exc:
                item['diagnosticError'] = str(exc)[:2000]
                if completed:
                    raise

    def ready_node(pid):
        return driver.js("var a=window.NavigationProductApp;if(!a)return false;var p=a.getBundle().positions[arguments[0]],r=a.getState().route;return r.node===p.id&&r.paper===p.paperId&&r.version===p.versionId&&a.getContent().ready(p.entityId)&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready';", pid)

    def select(pid):
        element = expose_source_position(driver, pid, record, save)
        return transition_record(driver, record, save, 'select-state-fixture', lambda: driver.click(element), lambda: ready_node(pid))['after']

    def actual_end_scroll():
        # End is handled by the product's one actual tree keyboard scope.
        transition_record(driver, record, save, 'keyboard-end-in-active-tree', lambda: driver.call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'active-tree-keyboard', 'actions': [{'type': 'keyDown', 'value': '\ue010'}, {'type': 'keyUp', 'value': '\ue010'}]}]}),
            lambda: driver.js("var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),t=document.getElementById('np-tree-scroll'),stored=history.state&&history.state[m.KEY],k=m.contextKey(s.route);return t.scrollTop>0&&stored&&stored.contexts[k].treeScrollByTree[s.route.tree]===t.scrollTop&&document.activeElement.closest('#np-tree [data-parallel-tree]');"))

    def state_scene(name):
        state = snapshot()
        record['scenes'].append({'name': prefix + name, 'state': state})
        save()
        if (state['forestCount'] != 1 or state['treeCount'] != 1 or state['rovingCount'] != 1 or
                state['inactiveItemCount'] or state['readerLists'] or
                state['widths']['forest'] < state['widths']['tree'] - 20):
            raise RuntimeError('Active forest no longer occupies the supplied main canvas')
        capture(prefix + name)
        return state

    driver.call('POST', '/url', {'url': base})
    wait_for(lambda: driver.js('return !!window.NavigationProductApp'))
    transition_record(driver, record, save, 'open-objectnav-for-view-retention', lambda: driver.click(driver.selector('[data-task-open="task:category-objectnav"]')),
        lambda: driver.js("return document.querySelector('#np-task-route-canvas [data-task-route-state=ready]')"))
    select(expected['poni']['id'])
    actual_end_scroll()
    literature = state_scene('-29-literature-before-switch')
    transition_record(driver, record, save, 'switch-literature-to-challenge', lambda: driver.click(driver.selector('[data-tree-tab="c"]')),
        lambda: driver.js("return NavigationProductApp.getState().route.tree==='c'"))
    ci = 'pos:c:6a8a9d2f7b1f3ab3a8ada5'
    select(ci)
    actual_end_scroll()
    challenge = state_scene('-29-challenge-selected')
    if literature['route']['paper'] == challenge['route']['paper'] or literature['route']['version'] == challenge['route']['version']:
        raise RuntimeError('Independent view retention did not cross paper and source-version contexts')
    phase = transition_record(driver, record, save, 'restore-literature', lambda: driver.click(driver.selector('[data-tree-tab="l"]')),
        lambda: driver.js('return NavigationProductApp.getState().route.node===arguments[0]', literature['route']['node']))
    check_exploration_restore(literature, phase['after'], nonzero=True, inactive_before=phase['before'])
    state_scene('-29-literature-restored')
    phase = transition_record(driver, record, save, 'restore-challenge', lambda: driver.click(driver.selector('[data-tree-tab="c"]')),
        lambda: driver.js('return NavigationProductApp.getState().route.node===arguments[0]', ci))
    check_exploration_restore(challenge, phase['after'], nonzero=True, inactive_before=phase['before'])
    # A second fast switch must not overwrite the inactive tree's saved pointer.
    phase = transition_record(driver, record, save, 'rapid-challenge-literature-challenge', lambda: (
        driver.click(driver.selector('[data-tree-tab="l"]')), driver.click(driver.selector('[data-tree-tab="c"]'))),
        lambda: driver.js('return NavigationProductApp.getState().route.node===arguments[0]', ci))
    check_exploration_restore(challenge, phase['after'], nonzero=True, inactive_before=phase['before'])
    phase = transition_record(driver, record, save, 'cold-deep-challenge', lambda: driver.call('POST', '/refresh', {}), lambda: ready_node(ci))
    check_exploration_restore(challenge, phase['after'], nonzero=True, inactive_before=phase['before'])
    # Resizing is explicit and preserves identity. Geometry may legally clamp.
    other = (1920, 1080) if prefix == '1440x900' else (1440, 900)
    width, height = map(int, prefix.split('x'))
    for w, h in (other, (width, height)):
        phase = transition_record(driver, record, save, 'resize-desktop', lambda w=w, h=h: driver.cdp('Emulation.setDeviceMetricsOverride', {'width': w, 'height': h, 'deviceScaleFactor': 1, 'mobile': False}))
        if phase['after']['route'] != challenge['route'] or phase['after']['selected'] != challenge['selected'] or phase['after']['expanded'] != challenge['expanded']:
            raise RuntimeError('Desktop resize changed source identity, selection or expansion')

    # Imported A belongs to PONI's exact source version and is partial (22/59).
    transition_record(driver, record, save, 'return-literature-for-analysis', lambda: driver.click(driver.selector('[data-tree-tab="l"]')), lambda: ready_node(expected['poni']['id']))
    imported = snapshot()['analysisEntry']
    if imported != {'state': 'imported', 'paper': 'poni', 'version': expected['poni']['versionId']}:
        raise RuntimeError('PONI imported-analysis entry belongs to another source version')
    analysis_scene('-30-analysis-imported-entry', [
        {'selector': '[data-analysis-state="imported"] > p', 'text': '本版本已导入：22 个原模板节点已填，0 个实例节点已填。'},
        {'selector': '#np-open-version-analysis', 'text': '打开本版本解析'},
        {'selector': '#np-open-analysis-template', 'text': '通用原59节点模板（未填答参考）'}])
    transition_record(driver, record, save, 'open-imported-version-analysis', lambda: driver.click(reveal_control(driver, {'selector': '#np-open-version-analysis'})),
        lambda: ready_node(science['analyses']['poni'][expected['poni']['versionId']]['roots'][0]))
    analysis = snapshot()
    entry = science['analyses']['poni'][expected['poni']['versionId']]
    if (analysis['route']['node'] != entry['roots'][0] or analysis['route']['template'] is not None or
            analysis['route']['paper'] != 'poni' or analysis['route']['version'] != expected['poni']['versionId'] or entry['answeredOriginalCount'] != 22):
        raise RuntimeError('Imported A was replaced with a generic template or another version')
    record['scenes'].append({'name': prefix + '-30-analysis-imported', 'state': analysis, 'sourceAnalysis': entry})
    save()
    capture(prefix + '-30-analysis-imported')
    transition_record(driver, record, save, 'return-from-imported-analysis', lambda: driver.click(driver.selector('.np-return-previous')), lambda: ready_node(expected['poni']['id']))
    vlfm = next(p for p in science['positions'].values() if p['scopeId'] == 'task:category-objectnav' and p['tree'] == 'l' and p['paperId'] == 'vlfm' and p['kind'] == 'pipeline_recipe')
    select(vlfm['id'])
    missing_spec = {'selector': '[data-analysis-state="not-imported"] > p', 'text': '本版本尚未导入逐节点解析；未填状态保留。'}
    missing = snapshot()
    if missing['analysisEntry'] != {'state': 'not-imported', 'paper': vlfm['paperId'], 'version': vlfm['versionId'] or ''}:
        raise RuntimeError('Missing A was presented as imported answers')
    analysis_scene('-30-analysis-not-imported', [missing_spec])
    transition_record(driver, record, save, 'open-missing-version-state', lambda: driver.click(driver.selector('#np-open-version-analysis')),
        lambda: driver.js("return NavigationProductApp.getState().route.tree==='a'"))
    no_answer = snapshot()
    if no_answer['route']['node'] is not None or no_answer['route']['template'] is not None or not driver.js("return document.querySelector('#np-tree .np-empty')?.textContent.includes('尚未导入原59节点解析')"):
        raise RuntimeError('Unimported version silently opened a template as its answers')
    transition_record(driver, record, save, 'return-missing-version-state', lambda: driver.click(driver.selector('.np-return-previous')), lambda: ready_node(vlfm['id']))
    transition_record(driver, record, save, 'open-explicit-reference-template', lambda: driver.click(reveal_control(driver, {'selector': '#np-open-analysis-template'})),
        lambda: driver.js("return NavigationProductApp.getState().route.template==='1'"))
    template_root = science['template']['roots'][0]
    transition_record(driver, record, save, 'select-original-reference-template-root',
        lambda: driver.click(expose_source_position(driver, template_root, record, save)),
        lambda: driver.js("return NavigationProductApp.getState().route.template==='1'&&NavigationProductApp.getState().route.node===arguments[0]", template_root))
    template = snapshot()
    if template['route']['paper'] != vlfm['paperId'] or template['route']['version'] != vlfm['versionId'] or len(science['template']['nodes']) != 59:
        raise RuntimeError('Reference template lost explicit zero-answer source identity')
    analysis_scene('-30-analysis-template-explicit', [
        {'selector': '#np-detail-content .np-detail-body > .np-boundary', 'text': '参考模式：原59节点模板，当前论文/版本未填答；0答案，不计入解析覆盖。'},
        {'selector': '#np-detail-content .np-detail-block > p', 'text': '这是通用模板问题，当前论文版本未填答；不表示原论文没有讨论，也不借用其他论文的答案。'}])

    # Legacy routes are real cold URL loads, not injected application state.
    routes = [literature['route'], challenge['route'], analysis['route']]
    global_route = driver.js('var a=NavigationProductApp;return NavigationProductModel.routeForPosition(a.getBundle(),a.getState().route,a.getBundle().researchMap.roots[0]);')
    routes.append(global_route)
    claim_route = dict(literature['route'], claim=task_route_claims(science, expected['poni'])[0]['id'])
    routes.append(claim_route)
    for route in routes:
        encoded = driver.js('return NavigationProductModel.encodeRoute(arguments[0])', route)
        driver.call('POST', '/url', {'url': 'about:blank'})
        driver.call('POST', '/url', {'url': base + encoded})
        wait_for(lambda: driver.js("var a=window.NavigationProductApp;return !!a&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'&&(!a.getState().route.node||a.getContent().ready(a.getBundle().positions[a.getState().route.node].entityId));"))
        driver.settle()
        actual = snapshot()
        record['deepLinks'].append({'expected': route, 'actual': actual})
        save()
        if actual['route'] != route:
            raise RuntimeError('Cold legacy URL changed a scientific route field')
    before_anchor = snapshot()
    transition_record(driver, record, save, 'legacy-workspace-anchor', lambda: driver.call('POST', '/url', {'url': base + '#np-workspace'}),
        lambda: driver.js('return !!window.NavigationProductApp'))
    if snapshot()['route'] != before_anchor['route']:
        raise RuntimeError('Legacy workspace anchor reset evidence identity')


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
              'browserFullscreenRequested': False,
              'capturePlan': [str(w) + 'x' + str(h) + suffix for w, h in VIEWPORTS for suffix in SCENE_NAMES]}
    report['frontendSources'] = {name: sha(name) for name in ('assets/navigation-product.js', 'assets/navigation-product-model.js', 'assets/navigation-product.css', 'scripts/navigation_product.py')}
    report['captureSources'] = {name: sha(name) for name in ('scripts/navigation_screenshots.py', 'tests/test_navigation_screenshots.py')}
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
          return {scope:r.scope,expectedScope:arguments[0],activeTree:r.tree,selectedTree:document.querySelector('[data-tree-tab][aria-selected=true]')?.dataset.treeTab,treeCount:document.querySelectorAll('#np-tree [role=tree]').length,rovingCount:document.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]').length,inactiveItemCount:[...document.querySelectorAll('#np-tree [role=treeitem]')].filter(e=>e.dataset.tree!==r.tree).length,home:!document.getElementById('np-reading-landing').hidden,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},panels:[...document.querySelectorAll('#np-tree [data-parallel-tree]')].map(e=>{var tree=e.dataset.parallelTree,roots=arguments[2][tree],h=e.querySelector('h3'),hb=box(h),q=hb.rect;return {tree:tree,scope:e.dataset.scopeId,roots:[...e.querySelectorAll(arguments[1])].map(n=>n.dataset.position),expectedRoots:roots,expectedChildren:arguments[3][tree],children:[...e.querySelectorAll('[role=treeitem]')].filter(n=>!roots.includes(n.dataset.position)).map(n=>box(n.querySelector(':scope > .np-node-row'))),rect:rect(e),heading:q,headingVisible:hb.visible&&hb.opaque&&!hb.clipped};})};
        """, scope, PARALLEL_ROOT_SELECTOR, science['forests'][scope], {t: any(science['positions'][pid]['childIds'] for pid in science['forests'][scope][t]) for t in ('l', 'c')})
        report.setdefault('parallelScopeChecks', []).append(data)
        save()
        check_parallel_scope(data)

    def select_node(target):
        target_tree = driver.js('return NavigationProductApp.getBundle().positions[arguments[0]].tree', target)
        if driver.js('return NavigationProductApp.getState().route.tree') != target_tree:
            driver.click(driver.selector('[data-tree-tab="' + target_tree + '"]'))
            driver.settle()
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
                if name and name not in ('objectnav', 'gap'):
                    capture(prefix + '-08-active-' + name)
                for active_tree in ('c', 'l'):
                    driver.click(driver.selector('[data-tree-tab="' + active_tree + '"]'))
                    driver.settle()
                    parallel_scope(scope)
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
                    capture(prefix + '-11-active-method-reader', require_flow=True)
                    reader_toggle_checks(driver, report, save, capture, prefix)
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
                for active_tree in ('c', 'l'):
                    driver.click(driver.selector('[data-tree-tab="' + active_tree + '"]'))
                    driver.settle()
                    parallel_scope(scope)
                for _ in range(6):
                    if driver.js('return !document.getElementById("np-reading-landing").hidden'):
                        break
                    driver.click(driver.selector('.np-return-previous'))
                    driver.settle()
                after = driver.js('return {window:scrollY,landing:document.getElementById("np-reading-landing").scrollTop,focus:document.activeElement.id};')
                if before != after or not driver.js('return document.getElementById("np-all-scopes").open'):
                    raise RuntimeError('Directory return lost open state, scroll or exact entry focus')
                report.setdefault('directoryReturnChecks', []).append({'scope': scope, 'before': before, 'after': after})
            capture(prefix + '-12-directory-return', require_home=True)
            task_density_checks(driver, report, save, capture, prefix, base, science)
            task_route_checks(driver, report, save, capture, prefix, base, science, server, dist)
            exploration_state_checks(driver, report, save, capture, prefix, base, science)
        planned = [str(w) + 'x' + str(h) + suffix for w, h in VIEWPORTS for suffix in SCENE_NAMES]
        report['capturePlan'] = planned
        if sorted(c['name'] for c in report['captures']) != sorted(planned):
            raise RuntimeError('Actual desktop screenshots differ from the declared bounded exploration plan')
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
