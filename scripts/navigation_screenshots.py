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
import tempfile
import time
import urllib.request
import urllib.error
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
    '-30-analysis-root-coverage', '-31-s0-reading-hierarchy', '-32-s1-relation-90', '-33-s2-first-answer',
    '-34-version-title-langmap', '-34-version-title-cow-objectnav',
    '-34-version-title-cow-language', '-34-version-title-cow-open-vocabulary',
)


# The existing glossary-open directory-return scene intentionally overlays the
# landing; it retains shell/state gates but is not a footer-readability scene.
S0_FOOTER_SCENES = ('-00-default-reading-overview', '-31-s0-reading-hierarchy',
                    '-13-relation-88', '-13-relation-90', '-13-relation-94')


def s0_footer_required(name):
    return any(name.endswith(suffix) for suffix in S0_FOOTER_SCENES)


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


# Every point is checked; only bounded diagnostics are returned in the receipt.
# The source map uses straight M/L/H/V segments. Unknown geometry fails closed,
# rather than granting an occlusion exception to arbitrary SVG descendants.
RELATION_PATH_SAMPLES_JS = r"""
function relationPathSamples(e,m,len,matrix){
  var limit=24,svg=e.closest('svg'),cs=getComputedStyle(e),mr=rect(m),ownHits=[],blockedHits=[],crossings=[],roundtripDifferences=[],roundtripDifferenceCount=0,counts={own:0,gap:0,crossing:0,endpoint:0,blocked:0};
  function scale(a){return Math.sqrt(Math.max(Math.abs(a.a)+Math.abs(a.b),Math.abs(a.c)+Math.abs(a.d))*Math.max(Math.abs(a.a)+Math.abs(a.c),Math.abs(a.b)+Math.abs(a.d)));}
  function point(a,x,y){var p=new DOMPoint(x,y).matrixTransform(a);return {x:p.x,y:p.y};}
  function segments(path){
    var d=path.getAttribute('d')||'',token=/[MLHV]|[-+]?(?:\d*\.\d+|\d+\.?\d*)(?:[eE][-+]?\d+)?/g,t=d.match(token)||[];
    if(d.replace(token,'').replace(/[\s,]/g,'')||!t.length)return null;
    var a=path.getScreenCTM(),out=[],i=0,cmd=null,x=0,y=0,started=false;
    while(i<t.length){
      if(/^[MLHV]$/.test(t[i]))cmd=t[i++];
      if(!cmd||(!started&&cmd!=='M'))return null;
      var n=cmd==='M'||cmd==='L'?2:1,v=t.slice(i,i+n);
      if(v.length!==n||v.some(z=>/^[MLHV]$/.test(z)||!Number.isFinite(Number(z))))return null;
      i+=n;var nx=cmd==='V'?x:Number(v[0]),ny=cmd==='H'?y:Number(v[cmd==='V'?0:1]);
      if(cmd!=='M'){var from=point(a,x,y),to=point(a,nx,ny);if(from.x!==to.x||from.y!==to.y)out.push({from:from,to:to});}
      x=nx;y=ny;started=true;if(cmd==='M')cmd='L';
    }
    return out.length?out:null;
  }
  function identity(n){return n?{tag:n.tagName,id:n.id||'',relation:n.dataset&&n.dataset.mapRelation||null,parent:n.dataset&&n.dataset.mapParent||null,child:n.dataset&&n.dataset.mapChild||null,position:n.dataset&&n.dataset.mapPosition||null}:null;}
  function registered(n){return !!n&&n!==e&&n.closest('svg')===svg&&n.matches('path[data-map-relation][data-from-entity][data-to-entity],path[data-map-parent][data-map-child]');}
  function opaque(n){for(;n;n=n.parentElement){var s=getComputedStyle(n);if(s.display==='none'||s.visibility!=='visible'||Number(s.opacity)===0)return false;}return true;}
  function intersectsCard(s,r){
    // Clip the complete centreline against the closed card. A point contact at
    // an endpoint is valid; following a card border is a real partial overlap.
    var lo=0,hi=1,dx=s.to.x-s.from.x,dy=s.to.y-s.from.y;
    for(var row of [[s.from.x,dx,r.x,r.x+r.width],[s.from.y,dy,r.y,r.y+r.height]]){
      if(row[1]===0){if(row[0]<row[2]||row[0]>row[3])return false;}
      else{var a=(row[2]-row[0])/row[1],b=(row[3]-row[0])/row[1];lo=Math.max(lo,Math.min(a,b));hi=Math.min(hi,Math.max(a,b));}
    }
    return hi>lo&&Math.hypot(dx,dy)*(hi-lo)>.01;
  }
  var line=segments(e),cards=[...m.querySelectorAll('[data-map-position]')].filter(opaque),cardIntersections=[];
  if(line)for(var card of cards){var r=rect(card);for(var k=0;k<line.length;k++)if(intersectsCard(line[k],r))cardIntersections.push({position:card.dataset.mapPosition,segment:k,rect:r});}
  var factor=scale(matrix),dash=cs.strokeDasharray==='none'?[]:cs.strokeDasharray.split(/[ ,]+/).filter(Boolean).map(v=>/^\d*\.?\d+(?:px)?$/.test(v)?parseFloat(v):NaN);
  var pathLength=e.getAttribute('pathLength'),calibration=pathLength===null?1:len/Number(pathLength),positive=dash.filter(n=>n>0);
  var step=Math.min(.5/factor,positive.length?Math.min(...positive)*calibration/4:Infinity),count=Math.ceil(len/step);
  var valid=!!line&&!!svg&&Number.isFinite(len)&&len>0&&Number.isFinite(step)&&step>0&&Number.isFinite(calibration)&&calibration>0&&dash.every(Number.isFinite)&&count>=1&&count<=20000&&typeof e.isPointInStroke==='function';
  var inverse=matrix.inverse();valid=valid&&['a','b','c','d','e','f'].every(key=>Number.isFinite(inverse[key]));
  var inBounds=valid,cache=new Map();
  function bounds(z){return Number.isFinite(z.x)&&Number.isFinite(z.y)&&z.x>=mr.x-1&&z.y>=mr.y-1&&z.x<=mr.x+mr.width+1&&z.y<=mr.y+mr.height+1&&z.x>=0&&z.y>=0&&z.x<=innerWidth&&z.y<=innerHeight;}
  function crossing(hit,z){
    if(!registered(hit)||!opaque(hit))return null;
    if(!cache.has(hit))cache.set(hit,segments(hit));var other=cache.get(hit);if(!other)return null;
    var style=getComputedStyle(hit),width=parseFloat(style.strokeWidth)*(style.vectorEffect==='non-scaling-stroke'?1:scale(hit.getScreenCTM()));
    if(!Number.isFinite(width)||width<=0||style.stroke==='none'||Number(style.strokeOpacity)<=0)return null;
    for(var a of line)for(var b of other){
      var ax=a.to.x-a.from.x,ay=a.to.y-a.from.y,bx=b.to.x-b.from.x,by=b.to.y-b.from.y,al=Math.hypot(ax,ay),bl=Math.hypot(bx,by),cross=ax*by-ay*bx,sine=Math.abs(cross)/(al*bl);
      if(sine<.5)continue; // No parallel/near-parallel/coincident-path exception.
      var qx=b.from.x-a.from.x,qy=b.from.y-a.from.y,t=(qx*by-qy*bx)/cross,u=(qx*ay-qy*ax)/cross;
      if(t<0||t>1||u<0||u>1)continue;
      var at={x:a.from.x+t*ax,y:a.from.y+t*ay},along=((z.x-a.from.x)*ax+(z.y-a.from.y)*ay)/(al*al),distance=Math.abs((z.x-a.from.x)*ay-(z.y-a.from.y)*ax)/al;
      if(along>=0&&along<=1&&distance<.01&&Math.hypot(z.x-at.x,z.y-at.y)<=width/(2*sine)+.01)return {hit:identity(hit),at:at,sine:sine};
    }
    return null;
  }
  function endpointContact(hit,arc){
    if(!hit)return false;var id=arc*factor<=1?e.dataset.fromEntity:(len-arc)*factor<=1?e.dataset.toEntity:null;
    var card=id&&cards.find(n=>n.dataset.taskOpen===id);return !!card&&(hit===card||card.contains(hit));
  }
  if(valid){
    for(var end of [0,len]){var q=e.getPointAtLength(end);if(!bounds(point(matrix,q.x,q.y)))inBounds=false;}
    for(var i=0;i<count;i++){
      var arc=len*(i+.5)/count,q=e.getPointAtLength(arc),rawScreen=point(matrix,q.x,q.y);
      // Blink's screen hit-test takes float32 coordinates. Query local stroke
      // geometry at that same screen point, not the pre-roundtrip path point.
      var z={x:Math.fround(rawScreen.x),y:Math.fround(rawScreen.y)},localProbe=point(inverse,z.x,z.y),hit=document.elementFromPoint(z.x,z.y),rawPainted=e.isPointInStroke(q),painted=e.isPointInStroke(localProbe),kind='blocked',proof=null;
      if(!bounds(z))inBounds=false;
      if(hit===e)kind='own';
      else if((hit===m||hit===svg)&&!painted)kind='gap';
      else if(endpointContact(hit,arc))kind='endpoint';
      else if(registered(hit)){
        proof=crossing(hit,z);
        var stack=document.elementsFromPoint(z.x,z.y),index=stack.indexOf(e),above=index<0?[]:stack.slice(0,index);
        if(proof&&(!painted||index>0&&above.every(n=>crossing(n,z))))kind='crossing';
      }
      counts[kind]++;var sample={x:z.x,y:z.y,fraction:arc/len,arc:arc,rawLocal:{x:q.x,y:q.y},rawScreen:rawScreen,localProbe:localProbe,rawPainted:rawPainted,painted:painted};
      if(rawPainted!==painted){roundtripDifferenceCount++;if(roundtripDifferences.length<limit)roundtripDifferences.push(sample);}
      if(kind==='own'&&ownHits.length<limit)ownHits.push(sample);
      if(kind==='blocked'&&blockedHits.length<limit)blockedHits.push(Object.assign(sample,{hit:identity(hit),painted:painted}));
      if(kind==='crossing'&&crossings.length<limit)crossings.push(Object.assign(sample,{painted:painted},proof));
    }
  }
  return {inBounds:inBounds,uncovered:valid&&counts.own>0&&counts.own+counts.gap>=3&&counts.blocked===0&&cardIntersections.length===0,ownHits:ownHits,
    sampling:{method:'uniform-full-arc',coordinates:'float32-screen-roundtrip',matrix:{a:matrix.a,b:matrix.b,c:matrix.c,d:matrix.d,e:matrix.e,f:matrix.f},inverse:{a:inverse.a,b:inverse.b,c:inverse.c,d:inverse.d,e:inverse.e,f:inverse.f},strokeDasharray:cs.strokeDasharray,strokeDashoffset:cs.strokeDashoffset,strokeLinecap:cs.strokeLinecap,strokeLinejoin:cs.strokeLinejoin,roundtripDifferenceCount:roundtripDifferenceCount,valid:valid,count:valid?count:0,firstArc:valid?len/(2*count):null,lastArc:valid?len-len/(2*count):null,maxArcStep:valid?len/count:null,maxScreenStep:valid?len/count*factor:null,counts:counts,diagnosticLimit:limit},
    blockedHits:blockedHits,crossings:crossings,roundtripDifferences:roundtripDifferences,cardIntersections:cardIntersections};
}
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
        if (panel['headingSelector'] != '#np-tree-heading' or panel['headingTree'] != panel['tree'] or not panel['headingInPane'] or
                panel['headingProof']['rect'] != panel['heading']):
            raise RuntimeError('Active task heading is not the visible fixed heading of this exact forest')
        check_task_route_proof(panel['headingProof'], {'l': '文献树', 'c': '挑战–思路树'}[panel['tree']])
        records = panel['rootRecords']; expected = panel['expectedRootRecords']
        if ([row['id'] for row in expected] != panel['expectedRoots'] or len(records) != len(expected) or
                any({key: row[key] for key in ('id', 'entity', 'tree', 'scope')} != {key: source[key] for key in ('id', 'entity', 'tree', 'scope')}
                    for row, source in zip(records, expected))):
            raise RuntimeError('Active task visible root identity differs from its original tree and scope')
        for row, source in zip(records, expected):
            if source['tree'] != panel['tree'] or source['scope'] != panel['scope']:
                raise RuntimeError('Active task expected root belongs to another tree or scope')
            check_task_route_proof(row['proof'], source['label'])
            if not rect_inside(row['proof']['rect'], panel['rect']):
                raise RuntimeError('Active task original root label is outside its actual forest')
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
    if (len(actual) != 7 or actual != expected or
            sorted(data['relationControls']) != sorted(e[0] for e in expected) or
            data['relationsVisible'] not in ('true', 'false') or
            data['selectedRelation'] is not None and data['selectedRelation'] not in data['relationControls']):
        raise RuntimeError('Typed relationship paths or text controls lost their exact scientific identity')
    for edge in data['relations']:
        visible = data['relationsVisible'] == 'true' or edge['id'] == data['selectedRelation']
        if (edge['visible'] is not visible or not math.isfinite(edge['length']) or edge['length'] <= 0 or
                not edge['endpointsMatch'] or not edge['inBounds'] or
                visible and (not edge['uncovered'] or not edge['ownHits'] or
                             len(edge['foreground']) != 3 or len(edge['background']) != 3 or
                             contrast_ratio(edge['foreground'], edge['background']) < 3)):
            raise RuntimeError('Selected/all relationship display lost real path geometry or exposed an unselected line')



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
    specs = [{'kind': 'heading'}, *[{'kind': 'locator', 'text': loc['locator']} for loc in expected['locators']],
             *[{'kind': kind, 'text': '原文来源 · ' + (ref.get('descriptor') or ref['sourceId']) if kind == 'source' else
                ' · ' + {'snapshot_not_version_pinned': '未固定全文快照', 'fixed_arxiv_version_url': '来源URL限定版本'}.get(ref['versionStatus'], ref['versionStatus']),
                'source': {'id': ref['sourceId'], 'url': ref['url'], 'version': ref['versionId'], 'status': ref['versionStatus']}}
               for ref in expected['sourceRefs'] for kind in ('source', 'status')]]
    for proof, spec in zip(data['visibleProofs'], specs):
        if (proof.get('kind') != spec['kind'] or proof.get('sourceRecord') != spec.get('source') or
                'text' in spec and proof['text'] != spec['text']):
            raise RuntimeError('Relationship visible fragment belongs to another source, version or locator')
        if spec['kind'] != 'source' and proof.get('accessibilitySuffix') is not None:
            raise RuntimeError('Only an exact source anchor may exclude the original screen-reader suffix')
        if spec['kind'] == 'source' and (proof.get('elementTag') != 'A' or proof.get('accessibilitySuffix') != {'tag': 'SPAN', 'className': 'np-sr', 'text': '（新标签页）'} or
                proof.get('accessibleText') != proof['text'] + '（新标签页）'):
            raise RuntimeError('Relationship source proof lost or misused its exact original screen-reader suffix')
        if proof.get('expectedText') is not None and proof['text'] != proof['expectedText']:
            raise RuntimeError('Visible relationship source version status contradicts the original inventory')
        if not proof['visible'] or not proof['opaque'] or not proof['unscaled'] or proof['fontSize'] < 15 or proof['clipped'] or len(proof['foreground']) != 3 or len(proof['background']) != 3 or contrast_ratio(proof['foreground'], proof['background']) < 4.5 or not rect_inside(proof['rect'], proof['viewport']):
            raise RuntimeError('Relationship source or locator is unreadable, hidden or off screen')
        if (proof.get('panelId') != 'np-overview-relation-panel' or not proof.get('panelContains') or
                proof.get('relationId') != expected['id'] or not proof.get('panelClientRect')):
            raise RuntimeError('Relationship proof did not measure this exact source inside the actual panel client region')
        check_s0_text(proof, spec.get('text', proof.get('expectedText', proof['text'])), proof['panelClientRect'], proof['viewport'])


def check_context_path(data):
    """Verify local ancestry independently from the separately labelled global navigation."""
    if data['route']['tree'] != 'c' or data['route']['node'] != 'pos:c:6dcc2ce43c02d908266f20':
        raise RuntimeError('Wrong AudioGoal challenge route')
    if data['localIds'] != data['expectedIds'] or any(t != 'c' for t in data['localTrees']):
        raise RuntimeError('Current challenge path differs from actual parent chain')
    if data['globalIds'] != data['expectedGlobalIds'] or data['globalSeparators'] != 0:
        raise RuntimeError('Global entry links imply a false ancestry chain')
    if data['labels'] != ['领域', '挑战–思路树']:
        raise RuntimeError('Compact global entry and actual local ancestry need distinct readable labels')
    if data.get('desktopDisclosure') is not None:
        check_context_disclosure(data)
        return
    if (len(data['rows']) != 2 or abs(data['rows'][0]['y'] - data['rows'][1]['y']) > 1 or
            data['rows'][0]['x'] + data['rows'][0]['width'] > data['rows'][1]['x'] + 1):
        raise RuntimeError('Global links and local ancestry do not share the compact, non-overlapping context row')
    if not all(rect_inside(r, data['viewport']) for r in data['rows']):
        raise RuntimeError('Context rows are outside the screenshot')
    if not data['buttons'] or not all(x['uncovered'] and rect_inside(x['rect'], data['viewport']) and rect_inside(x['rect'], x['row']) and not x['clipped'] for x in data['buttons']):
        raise RuntimeError('Context link is clipped, covered or outside the screenshot')


CONTEXT_ANCESTRY_SUMMARY_SELECTOR = '#np-global-context .np-ancestry-disclosure > summary'
CONTEXT_ANCESTRY_STATE_JS = r"""
var a=NavigationProductApp,s=a.getState(),tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll'),disclosure=document.querySelector('#np-global-context .np-ancestry-disclosure');
return {open:disclosure?disclosure.open:null,route:s.route,originTrail:s.originTrail,historyLength:history.length,
  window:{x:scrollX,y:scrollY},treeScroll:{top:tree.scrollTop,left:tree.scrollLeft},readerScroll:{top:reader.scrollTop,left:reader.scrollLeft}};
"""
CONTEXT_PATH_SNAPSHOT_JS = VISUAL_GEOMETRY + r"""
var a=NavigationProductApp,b=a.getBundle(),r=a.getState().route,p=b.positions[r.node],expected=[];
while(p){expected.unshift(p.id);p=p.parentId?b.positions[p.parentId]:null;}
var host=document.getElementById('np-global-context'),entry=host.querySelector('[data-path-kind="global-entry"]'),local=host.querySelector('[data-path-kind="local-ancestry"]'),disclosure=local.closest('.np-ancestry-disclosure'),summary=disclosure.querySelector(':scope > summary');
function ids(n){return Array.from(n.querySelectorAll('[data-context-position]'),x=>x.dataset.contextPosition);}
function sourceLabel(id){var p=b.positions[id],e=b.entities[p.entityId];return e&&e.label||p.sourceLabel||p.label;}
function proof(e){var result=box(e),range=document.createRange();range.selectNodeContents(e);
  result.fragments=[...range.getClientRects()].filter(r=>r.width>0&&r.height>0).map(r=>({x:r.x,y:r.y,width:r.width,height:r.height,visible:[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!hit&&(hit===e||e.contains(hit));})}));return result;}
function buttons(n){return [...n.querySelectorAll('[data-context-position]')].map(e=>({id:e.dataset.contextPosition,text:e.textContent,title:e.title,aria:e.getAttribute('aria-label'),proof:proof(e)}));}
var root=b.researchMap.roots[0],scope=b.researchMap.canonicalScopePositionIds[r.scope];
return {route:r,expectedIds:expected,localIds:ids(local),localTrees:ids(local).map(id=>b.positions[id].tree),globalIds:ids(entry),expectedGlobalIds:scope&&scope!==root?[root,scope]:[root],globalSeparators:entry.querySelectorAll('.np-path-separator').length,
  labels:[entry.querySelector('[data-context-position]').textContent,local.querySelector('.np-context-label').textContent],viewport:{x:0,y:0,width:innerWidth,height:innerHeight},
  desktopDisclosure:{tag:disclosure.tagName,open:disclosure.open,summary:proof(summary),compactRows:[rect(entry),rect(summary)],popover:rect(local),localLabel:proof(local.querySelector('.np-context-label')),
    expectedLocalLabels:expected.map(sourceLabel),globalButtons:buttons(entry),localButtons:buttons(local)}};
"""


def check_context_disclosure(data):
    """Desktop migration: compact entry/summary, then the complete original path."""
    d, viewport = data['desktopDisclosure'], data['viewport']
    def readable(proof, *areas):
        return (_reader_proof(proof, viewport, *areas, font_size=15) and proof.get('fragments') and
                all(f.get('visible') and all(rect_inside(f, area) for area in (viewport, *areas)) for f in proof['fragments']))
    rows = d['compactRows']
    if (d['tag'] != 'DETAILS' or type(d['open']) is not bool or len(rows) != 2 or
            abs(rows[0]['y'] + rows[0]['height'] / 2 - rows[1]['y'] - rows[1]['height'] / 2) > 1 or rows[0]['x'] + rows[0]['width'] > rows[1]['x'] + 1 or
            not all(rect_inside(row, viewport) for row in rows) or
            d['summary']['text'] != data['labels'][1] + ' · 原树路径' or not readable(d['summary'], rows[1])):
        raise RuntimeError('Compact context entry or original-path disclosure summary is hidden, covered or misplaced')
    globals_, locals_ = d['globalButtons'], d['localButtons']
    if ([item['id'] for item in globals_] != data['expectedGlobalIds'] or
            not all(readable(item['proof'], rows[0]) for item in globals_) or
            [item['id'] for item in locals_] != data['expectedIds'] or
            [item['text'] for item in locals_] != d['expectedLocalLabels'] or
            any(item['title'] != text or item['aria'] != text for item, text in zip(locals_, d['expectedLocalLabels']))):
        raise RuntimeError('Context disclosure changed ordered original ancestors, full labels or visible global controls')
    if d['open']:
        if (not rect_inside(d['popover'], viewport) or not readable(d['localLabel'], d['popover']) or
                not all(readable(item['proof'], d['popover']) for item in locals_)):
            raise RuntimeError('Original-path popover label or ancestor link is hidden, clipped or covered')
    elif any(f.get('visible') for item in locals_ for f in item['proof']['fragments']):
        raise RuntimeError('Closed original-path disclosure still exposes ancestor text')


def check_context_ancestry_transition(before, after, opened):
    if type(after.get('open')) is not bool or after['open'] is not opened:
        raise RuntimeError('Original-path disclosure did not reach the requested open state')
    for key in ('route', 'originTrail', 'historyLength', 'window', 'treeScroll', 'readerScroll'):
        if before[key] != after[key]:
            raise RuntimeError('Original-path disclosure changed preserved navigation: ' + key)


def set_context_ancestry_open(driver, opened):
    before = driver.js(CONTEXT_ANCESTRY_STATE_JS)
    if type(before.get('open')) is not bool:
        raise RuntimeError('Original-path disclosure is missing')
    if before['open'] is not opened:
        driver.click(driver.selector(CONTEXT_ANCESTRY_SUMMARY_SELECTOR))
        driver.settle()
    after = driver.js(CONTEXT_ANCESTRY_STATE_JS)
    check_context_ancestry_transition(before, after, opened)
    return {'before': before, 'after': after}


def context_path_checks(driver, report, save, capture, prefix):
    """Read the real popover through native open/close/reopen controls."""
    record = {'viewport': prefix, 'disclosureChecks': {'transitions': []}}
    report.setdefault('contextPathChecks', []).append(record)
    initial = driver.js(CONTEXT_PATH_SNAPSHOT_JS)
    record['disclosureChecks']['initial'] = initial
    save()
    check_context_path(initial)
    if initial['desktopDisclosure']['open']:
        raise RuntimeError('Cold original-path disclosure must start closed')
    for opened in (True, False, True):
        phase = set_context_ancestry_open(driver, opened)
        record['disclosureChecks']['transitions'].append(phase)
        phase['evidence'] = driver.js(CONTEXT_PATH_SNAPSHOT_JS)
        save()
        check_context_path(phase['evidence'])
    context = phase['evidence']
    record['evidence'] = context
    save()
    closed = set_context_ancestry_open(driver, False)
    record['disclosureChecks']['transitions'].append(closed)
    closed['evidence'] = driver.js(CONTEXT_PATH_SNAPSHOT_JS)
    save()
    check_context_path(closed['evidence'])
    # The temporary path overlay may cover fixed reader identity; photograph
    # its closed default after recording complete open/reopen visibility proofs.
    capture(prefix + '-06-audiogoal-ci-path')
    return context


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



def write_receipt(path, report):
    """Preserve every checkpoint, without pretty-print cost or partial targets."""
    payload = json.dumps(report, ensure_ascii=False, separators=(',', ':')) + '\n'
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                         prefix='.' + path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(payload)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class ReceiptSnapshotCache:
    """Reuse JSON encoding, never checkpoints or observations.

    Every call still publishes the complete ordinary JSON document atomically.
    The capture's report is main-thread owned; server diagnostics are copied
    into it. Every item is freshly marshalled before consulting its cache, so
    later fields, nested mutations, aliases, and type changes are never hidden.
    Marshal bytes are only decoded directly from that new in-memory snapshot,
    never from an artifact or cache file. This is not an artifact format change.
    """
    def __init__(self, path, max_cache_bytes=2 * 1024 ** 3, progress_every=50):
        import marshal
        self.marshal = marshal
        self.path = Path(path)
        self.directory = tempfile.TemporaryDirectory(prefix='.receipt-cache-', dir=self.path.parent)
        self.root = Path(self.directory.name)
        self.entries, self.serial, self.bytes = {}, 0, 0
        self.limit, self.progress_every, self.closed = max_cache_bytes, progress_every, False
        if type(max_cache_bytes) is not int or max_cache_bytes < 0 or type(progress_every) is not int or progress_every < 0:
            self.directory.cleanup()
            raise ValueError('Invalid receipt cache budget')
        self.stats = dict(writes=0, hits=0, misses=0, fingerprintSeconds=0.0,
                          encodeSeconds=0.0, copySeconds=0.0, totalSeconds=0.0)

    def close(self):
        if not self.closed:
            self.directory.cleanup()
            self.entries.clear()
            self.bytes, self.closed = 0, True

    def _remove(self, entry):
        for path in entry[:2]:
            path.unlink(missing_ok=True)

    def _chunk(self, slot, value):
        started = time.perf_counter()
        frozen = self.marshal.dumps(value, 4)
        old = self.entries.get(slot)
        same = old is not None and old[5] and old[0].is_file() and old[1].is_file() and old[0].read_bytes() == frozen
        self.stats['fingerprintSeconds'] += time.perf_counter() - started
        if same:
            self.stats['hits'] += 1
            return slot, old[1], old[3], old[4]
        self.stats['misses'] += 1
        started = time.perf_counter()
        payload = json.dumps(self.marshal.loads(frozen), ensure_ascii=False,
                             separators=(',', ':')).encode('utf-8')
        self.stats['encodeSeconds'] += time.perf_counter() - started
        size = len(frozen) + len(payload)
        remaining = self.bytes - (old[2] if old is not None else 0)
        if remaining + size > self.limit:
            # No uncached disk sidecars: write this single encoded item directly
            # to the final temporary receipt, then release it before the next.
            return payload
        if old is not None:
            self._remove(old)
            del self.entries[slot]
            self.bytes -= old[2]
        self.serial += 1
        stamp, encoded = (self.root / (str(self.serial) + suffix) for suffix in ('.snapshot', '.json'))
        stored = False
        digest = hashlib.sha256(payload).digest()
        # Reserve the full staging cost before writing. Failed cleanup leaves
        # this incomplete entry conservatively charged until removal succeeds.
        entry = (stamp, encoded, size, len(payload), digest, False)
        self.entries[slot] = entry
        self.bytes += size
        try:
            # The cap includes retained AND staged auxiliary files. The old
            # entry was removed before staging its replacement; ordinary old
            # receipt + final atomic temporary receipt remain outside this cap.
            if stamp.write_bytes(frozen) != len(frozen) or encoded.write_bytes(payload) != len(payload):
                raise OSError('Incomplete receipt cache write')
            self.entries[slot] = (stamp, encoded, size, len(payload), digest, True)
            stored = True
            return slot, encoded, len(payload), digest
        finally:
            if not stored:
                self._remove(entry)
                del self.entries[slot]
                self.bytes -= size

    @staticmethod
    def _write(stream, payload):
        if stream.write(payload) != len(payload):
            raise OSError('Incomplete receipt temporary write')

    def _copy(self, chunk, stream):
        slot, path, length, digest = chunk
        actual, total = hashlib.sha256(), 0
        with path.open('rb') as source:
            while True:
                block = source.read(1024 * 1024)
                if not block:
                    break
                actual.update(block)
                total += len(block)
                self._write(stream, block)
        if total != length or actual.digest() != digest:
            old = self.entries.get(slot)
            if old is not None and old[1] == path:
                self._remove(old)
                del self.entries[slot]
                self.bytes -= old[2]
            raise RuntimeError('Receipt cache payload integrity check failed')

    def __call__(self, path, report):
        if self.closed or Path(path) != self.path:
            raise ValueError('Receipt cache is closed or changed target')
        if type(report) is not dict or any(type(key) is not str for key in report):
            raise TypeError('Receipt cache requires original named report fields')
        started = time.perf_counter()
        seen, target = set(), None
        try:
            with tempfile.NamedTemporaryFile(mode='wb', dir=self.path.parent,
                                             prefix='.' + self.path.name + '.', suffix='.tmp', delete=False) as stream:
                target = Path(stream.name)
                self._write(stream, b'{')
                for number, (key, value) in enumerate(report.items()):
                    if number:
                        self._write(stream, b',')
                    self._write(stream, json.dumps(key, ensure_ascii=False).encode('utf-8') + b':')
                    items = enumerate(value) if type(value) is list else [(None, value)]
                    if type(value) is list:
                        self._write(stream, b'[')
                    for index, item in items:
                        if type(value) is list and index:
                            self._write(stream, b',')
                        slot = (key, index)
                        seen.add(slot)
                        chunk = self._chunk(slot, item)
                        copy_started = time.perf_counter()
                        if isinstance(chunk, bytes):
                            self._write(stream, chunk)
                        else:
                            self._copy(chunk, stream)
                        self.stats['copySeconds'] += time.perf_counter() - copy_started
                    if type(value) is list:
                        self._write(stream, b']')
                self._write(stream, b'}\n')
            os.replace(target, self.path)
            self.stats['writes'] += 1
            for slot in list(self.entries):
                if slot not in seen:
                    old = self.entries[slot]
                    self._remove(old)
                    del self.entries[slot]
                    self.bytes -= old[2]
        finally:
            if target is not None:
                target.unlink(missing_ok=True)
            self.stats['totalSeconds'] += time.perf_counter() - started
        if self.progress_every and self.stats['writes'] % self.progress_every == 0:
            print('receipt_checkpoint ' + json.dumps(dict(self.stats, cacheBytes=self.bytes), separators=(',', ':')), flush=True)


def wait_for(check, timeout=45):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        result = check()
        if result:
            return result
        time.sleep(.1)
    raise TimeoutError('Browser condition did not become ready within bounded wait')


WEBDRIVER_HTTP_BODY_LIMIT = 16384
WEBDRIVER_ERRORS = frozenset((
    'element click intercepted', 'element not interactable', 'insecure certificate',
    'invalid argument', 'invalid cookie domain', 'invalid element state', 'invalid selector',
    'invalid session id', 'javascript error', 'move target out of bounds', 'no such alert',
    'no such cookie', 'no such element', 'no such frame', 'no such shadow root', 'no such window',
    'script timeout', 'session not created', 'stale element reference', 'timeout',
    'unable to capture screen', 'unable to set cookie', 'unexpected alert open',
    'unknown command', 'unknown error', 'unknown method', 'unsupported operation',
))


def webdriver_http_diagnostic(error, method, path):
    """Read one bounded response; export only recognized diagnostic vocabulary."""
    commands = (r'/session', r'/session/[^/]+', r'/session/[^/]+/element/[^/]+/click',
                r'/session/[^/]+/(?:element|elements|back|forward|refresh|screenshot|log|actions)',
                r'/session/[^/]+/(?:execute/(?:sync|async)|goog/cdp/execute)')
    command = '[unrecognized command]'
    if any(re.fullmatch(pattern, path) for pattern in commands):
        command = re.sub(r'^/session/[^/]+', '/session/:session', path)
        command = re.sub(r'/element/[^/]+/click$', '/element/:element/click', command)
    result = {'httpStatus': error.code if type(error.code) is int else None,
              'method': method if method in ('GET', 'POST', 'DELETE') else 'OTHER',
              'command': command, 'bodyReadLimit': WEBDRIVER_HTTP_BODY_LIMIT, 'truncated': False}
    try:
        body = error.read(WEBDRIVER_HTTP_BODY_LIMIT + 1)
        if len(body) > WEBDRIVER_HTTP_BODY_LIMIT:
            result['truncated'] = True
            return result
        payload = json.loads(body)
        value = payload.get('value') if isinstance(payload, dict) else None
        if not isinstance(value, dict) or not isinstance(value.get('error'), str) or value['error'] not in WEBDRIVER_ERRORS:
            result['unrecognizedResponse'] = True
            return result
        result['error'] = value['error']
        if isinstance(value.get('message'), str):
            message = value['message'].lower()
            # Do not export arbitrary plain text, HTML attributes, URLs, stack
            # traces or token-like strings, even if they occur in `message`.
            parts = [value['error']]
            recognized = value['error'] in message
            point = re.search(r'not clickable at point\s*\(\s*(-?\d{1,7}(?:\.\d{1,3})?),\s*(-?\d{1,7}(?:\.\d{1,3})?)\s*\)', message)
            if point:
                recognized = True
                parts.append('not clickable at point (' + point[1] + ', ' + point[2] + ')')
            for phrase in ('other element would receive the click', 'element is not attached to the page document',
                           'element has zero size', 'element is outside of the viewport', 'target frame detached'):
                if phrase in message:
                    recognized = True
                    parts.append(phrase)
            result['message'] = '; '.join(parts)[:512] if recognized else '[unrecognized message omitted]'
            result['messageRedacted'] = True
        else:
            result['messageOmitted'] = True
    except Exception:
        # Diagnostic failure must never replace the HTTPError being investigated.
        result['diagnosticUnavailable'] = True
    return result


class Driver:
    def __init__(self, port):
        self.url = f'http://127.0.0.1:{port}'
        self.session = None

    def request(self, method, path, data=None):
        raw = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(self.url + path, data=raw, method=method,
                                     headers={'Content-Type': 'application/json'})
        try:
            with urllib.request.urlopen(req, timeout=50) as response:
                value = json.load(response)['value']
        except urllib.error.HTTPError as exc:
            try:
                exc.navigation_webdriver_diagnostic = webdriver_http_diagnostic(exc, method, path)
            except Exception:
                pass
            raise
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

    def send_response(self, code, message=None):
        hold = getattr(self, '_capture_packet_hold', None)
        if hold is not None:
            hold.note('response', status=code, request=self._capture_packet_request)
        super().send_response(code, message)

    def do_GET(self):
        if self.path == '/favicon.ico':
            self.send_response(204)
            self.end_headers()
            return
        hold = getattr(self.server, 'packet_hold', None)
        if hold and urllib.parse.urlsplit(self.path).path == hold.path:
            self._capture_packet_hold = hold
            request = self._capture_packet_request = hold.start_request()
            hold.note('seen', request=request)
            hold.seen.set()
            hold.note('held', request=request)
            if not hold.released.wait(8):
                hold.expired = True
                hold.note('expired', request=request)
            else:
                hold.note('release-observed', request=request)
            try:
                super().do_GET()
            finally:
                hold.note('request-finished', request=request)
                self._capture_packet_hold = None
        else:
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
        self.events, self.truncated, self.lock = [], False, threading.Lock()
        self.started = time.monotonic()
        self.request_count = 0

    def start_request(self):
        with self.lock:
            self.request_count += 1
            return self.request_count

    def note(self, event, status=None, request=None):
        with self.lock:
            if len(self.events) >= 32:
                self.truncated = True
                return
            row = {'event': event, 'elapsedMs': round((time.monotonic() - self.started) * 1000, 3)}
            if isinstance(status, int) and not isinstance(status, bool):
                row['status'] = int(status)
            if type(request) is int:
                row['request'] = request
            self.events.append(row)

    def diagnostic(self):
        with self.lock:
            return {'path': self.path, 'seen': self.seen.is_set(), 'released': self.released.is_set(),
                    'expired': self.expired, 'requestCount': self.request_count, 'events': list(self.events),
                    'eventLimit': 32, 'truncated': self.truncated}

    def __enter__(self):
        if getattr(self.server, 'packet_hold', None) is not None:
            raise RuntimeError('Only one bounded packet hold is allowed')
        self.server.packet_hold = self
        self.note('armed')
        return self

    def __exit__(self, *_):
        self.released.set()
        self.server.packet_hold = None
        self.note('disarmed')


class DelayedRequestCacheControl:
    """Test-owned fresh requests only; normal-cache cold scenarios stay separate."""
    def __init__(self, driver, record, save, hold):
        self.driver, self.record, self.save = driver, record, save
        self.hold = hold
        self.state = record['cacheControl'] = {
            'scope': 'this delayedRestore case only; all resources on this browser target',
            'normalCacheColdChecksSeparate': True, 'disableAttempted': False,
            'disableAcknowledged': False, 'restoreAttempted': False, 'restoreAcknowledged': False}

    def __enter__(self):
        self.state['disableAttempted'] = True
        try:
            self.driver.cdp('Network.setCacheDisabled', {'cacheDisabled': True})
            self.state['disableAcknowledged'] = True
            self.save()
        except Exception as exc:
            self._restore(exc)
            raise
        return self

    def _restore(self, original=None):
        failure = None
        self.state['restoreAttempted'] = True
        try:
            self.driver.cdp('Network.setCacheDisabled', {'cacheDisabled': False})
            self.state['restoreAcknowledged'] = True
        except Exception as exc:
            self.state['restoreErrorType'] = type(exc).__name__
            failure = exc
        try:
            self.record['hold'] = self.hold.diagnostic()
        except Exception as exc:
            self.state['holdDiagnosticErrorType'] = type(exc).__name__
            if failure is None:
                failure = exc
        try:
            self.save()
        except Exception as exc:
            self.state['saveErrorType'] = type(exc).__name__
            if failure is None:
                failure = exc
        if original is None and failure is not None:
            raise failure

    def __exit__(self, kind, value, traceback):
        self._restore(value)
        return False


DELAYED_PACKET_DIAGNOSTIC_JS = r"""
var sha=arguments[0],owner=arguments[1],path='/research/navigation/content/'+sha+'.json',a=window.NavigationProductApp;
if(!/^[a-f0-9]{64}$/.test(sha))throw Error('Unexpected diagnostic packet identity');
var all=performance.getEntriesByType('resource').filter(function(e){try{var u=new URL(e.name,location.href);return u.origin===location.origin&&u.pathname===path;}catch(_){return false;}});
function number(v){return typeof v==='number'&&Number.isFinite(v)?v:null;}
var content=a&&a.getContent(),info=content&&content.diagnostics(owner),packet=a&&a.getBundle().delivery.packets[owner],nav=performance.getEntriesByType('navigation')[0];
return {packetSha256:sha,timeOriginMs:performance.timeOrigin,relativeTimeMs:performance.now(),documentReadyState:document.readyState,
  navigationType:nav&&['navigate','reload','back_forward','prerender'].includes(nav.type)?nav.type:null,
  ownerPacketMatches:!!packet&&packet.sha256===sha,contentReady:!!content&&content.ready(owner),
  contentStatus:content&&['ready','loading','failed','idle'].includes(content.status(owner))?content.status(owner):null,
  progress:info?{phase:['fetch','body','hash','parse','identity','ready'].includes(info.phase)?info.phase:null,
    elapsedMs:number(info.elapsedMs),receivedBytes:number(info.receivedBytes),expectedBytes:number(info.expectedBytes),attempt:number(info.attempt)}:null,
  resourceEntryCount:all.length,resourceEntryLimit:8,resourceEntriesTruncated:all.length>8,
  resources:all.slice(-8).map(function(e){return {initiatorType:['fetch','xmlhttprequest','other'].includes(e.initiatorType)?e.initiatorType:'other',
    startTime:number(e.startTime),duration:number(e.duration),transferSize:number(e.transferSize),encodedBodySize:number(e.encodedBodySize),decodedBodySize:number(e.decodedBodySize),
    responseStatus:number(e.responseStatus),deliveryType:['cache','navigational-prefetch',''].includes(e.deliveryType)?e.deliveryType:null,
    workerStart:number(e.workerStart)};})};
"""


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
return {view:{focus:active.id,window:scrollY,landing:landing.scrollTop,relationPanel:document.getElementById('np-overview-relation-panel').scrollTop,selectedRelation:document.getElementById('np-overview-map').dataset.selectedRelation||null,
    open:document.getElementById('np-task-relations').open,
    lines:document.getElementById('np-overview-map').dataset.relationsVisible},
  diagnostic:{runtime:bucketRecord(runtime),persisted:bucketRecord(persisted),
    landing:geometry(landing),relationPanel:geometry(document.getElementById('np-overview-relation-panel')),active:geometry(active),map:geometry(document.getElementById('np-overview-map')),
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
    pane=document.querySelector('.np-reading-pane'),toggle=document.getElementById('np-reader-toggle'),selected=document.getElementById('np-node-'+state.route.node),
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
  layout:app.dataset.readingLayout,methodReading:app.dataset.methodReading,collapsed:app.dataset.readerCollapsed,focus:document.activeElement.id,
  panels:rect(document.querySelector('.np-panels')),columnGap:parseFloat(getComputedStyle(document.querySelector('.np-panels')).columnGap),
  treePane:proof(document.querySelector('.np-tree-pane')),tree:ts,treeProof:proof(tree),title:proof(document.getElementById('np-tree-heading')),
  selected:{count:document.querySelectorAll('#np-tree [aria-selected="true"]').length,id:selected&&selected.dataset.position,
    tree:selected&&selected.dataset.tree,entity:selected&&selected.dataset.entity,aria:selected&&selected.getAttribute('aria-selected'),
    scope:selected&&selected.closest('[data-parallel-tree]')?.dataset.scopeId,row:proof(row),label:proof(label),
    content:rr?{x:rr.x-ts.client.x+ts.left,y:rr.y-ts.client.y+ts.top}:null},
  toggle:{tag:toggle.tagName,hidden:toggle.hidden,disabled:toggle.disabled,controls:toggle.getAttribute('aria-controls'),expanded:toggle.getAttribute('aria-expanded'),proof:proof(toggle)},
  reader:{hidden:pane.hidden,display:getComputedStyle(pane).display,tabIndex:reader.tabIndex,proof:proof(pane),scroll:scrollBox(reader),
    heading:proof(document.getElementById('np-reader-heading')),entity:mechanism&&mechanism.dataset.mechanismEntity,
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


# Display-only migrations are explicit. Original source, route, restoration,
# diagnostic, content-delay and native-input predicates remain independent.
DISPLAY_CONTRACT_MIGRATIONS = {
    'shared_chrome_budget': 'shared site header, global navigation, four-field selection identity and workspace toolbar retain their measured natural flow; remaining desktop height is proved against the viewport bottom and actual layout width, including a reserved scrollbar gutter; short S0 retains 4px outer bottom padding, otherwise16px; overview toolbar is deducted before the map; source task cards retain the current56px placement contract and C cards37px; first-screen route/answer/entry budgets remain relative to their verified panels',
    'workspace_branch_tabs': 'global root highlights g; a global descendant retains its exact g source route while its source-verified Literature or Challenge ancestry uniquely selects l or c; ordinary l/c/a routes retain their own tab; all four selected states remain exact',
    'relation_picker': 'same IDs, types, endpoints and controls; outside tree scroll in fixed toolbar',
    'reader_identity': 'fixed current title and exact version replace generic sticky READING DESK',
    'context_path': 'one compact row; original global links and real local parent chain remain distinct',
    'outer_scroll': 'ready desktop window is zero; exact effective tree/reader offsets and other buckets retained',
    's0_footer': 'unchanged legend/readout and source-derived coverage in one natural-flow footer after the original map; only the in-map C-column evidence panel scrolls',
    's0_adaptive_spacing': 'compact editorial task rows and source-ordered C cards now receive bounded extra vertical gaps from actual positive desktop map client height: reserve 12px, cap task-row extra at 24px and C-gap extra at 7px; unchanged card dimensions, x positions, typography, headers, task bus, footer and source paths; 12px is an extra-allocation reserve, not a new compact-map bottom-clearance rule; closed-state labels remain uncovered, while exact native open-selector occlusion is proved by actual hit ancestry and popup bounds',
    'overview_relations': 'all seven paths and controls retained; selected-only default plus explicit show-all',
    'analysis_entry': 'first actual version answer; explicit legacy root remains coverage and full original topology',
    'active_forest_heading': 'same active source forest and roots; visible #np-tree-heading plus exact root-label proofs replace the deliberately hidden duplicate forest h3',
    'method_geometry': 'actual desktop g/L method only: 400/448px real-path pane, 16px gap, 992/1424px reader; task/relation/A unchanged',
    'method_ancestry': 'user-approved 2026-10-13: full original root-to-current path remains readable together; each originally expanded direct child keeps its source identity and receives native-keyboard full-label/role proof in the original scroll pane, followed by exact runtime/history/DOM/focus/scroll return; real-parent siblings remain native disclosures',
    'method_introduction': 'desktop selected method hides only repeated interface introduction; original mechanism and source boundaries remain natural flow',
    'source_scroll_fixtures': 'S1 fitting body proves stationary identity only; mandatory positive wheel uses measured genuine PONI content; L/C nonzero history uses same-version original technical child, measured offscreen last-row End target, then real pipeline ancestor for A and claim links',
    'method_analysis_controls': 'full fixed title/version/warning and genuine analysis controls in a compact status row; no cropped identity',
}


# Count open scroll containers even below the current viewport. Only actual
# non-rendering states suppress a candidate; clipping and occlusion are not exemptions.
SCROLL_REGION_VISIBILITY_JS = r"""
function renderedElementState(e){
  var cs=getComputedStyle(e),r=rect(e),blocked=null,ancestors=[];
  function block(reason,n){if(!blocked)blocked={reason:reason,tag:n.tagName,id:n.id||null};}
  if(cs.visibility==='hidden'||cs.visibility==='collapse')block('visibility',e);
  for(var n=e;n&&n.nodeType===1;n=n.parentElement){var style=getComputedStyle(n),opacity=Number(style.opacity);
    ancestors.push({tag:n.tagName,id:n.id||null,hidden:!!n.hidden,display:style.display,visibility:style.visibility,opacity:style.opacity,closedDetails:n.tagName==='DETAILS'&&!n.open});
    if(n.hidden)block('hidden',n);
    if(style.display==='none')block('display-none',n);
    if(Number.isFinite(opacity)&&opacity===0)block('opacity-zero',n);
    if(n.tagName==='DETAILS'&&!n.open&&n!==e){var summary=[...n.children].find(child=>child.tagName==='SUMMARY');
      if(!summary||!(summary===e||summary.contains(e)))block('closed-details',n);}
  }
  if(!(r.width>0&&r.height>0))block('empty-bounds',e);
  return {id:e.id||e.className,rect:r,display:cs.display,visibility:cs.visibility,opacity:cs.opacity,overflowX:cs.overflowX,overflowY:cs.overflowY,rendered:!blocked,blockedBy:blocked,ancestors:ancestors};
}
function scrollRegionCandidate(e){var cs=getComputedStyle(e);return /auto|scroll/.test(cs.overflowY+' '+cs.overflowX)?renderedElementState(e):null;}
"""


# Fixed footer labels use actual text-node ranges, including every wrapped line.
# This adds evidence; it never replaces the fixed title's original five-point box hit test.
FIXED_TEXT_PROOF_JS = r"""
function fixedTextProof(e,ignoredTextParent){
  var result=box(e),fragments=[],textRuns=[],walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),n;
  function clips(element){var areas=[];for(var a=element;a;a=a.parentElement){var cs=getComputedStyle(a);
    if(/auto|scroll|hidden|clip/.test(cs.overflowX+' '+cs.overflowY)){var r=rect(a);areas.push({x:r.x+a.clientLeft,y:r.y+a.clientTop,width:a.clientWidth,height:a.clientHeight});}}
    return areas;}
  while(n=walker.nextNode()){if(n.parentElement===ignoredTextParent||!n.textContent.trim())continue;var parent=n.parentElement,style=box(parent),range=document.createRange();range.selectNodeContents(n);
    var run={text:n.textContent,opaque:style.opaque,unscaled:style.unscaled,fontSize:style.fontSize,foreground:style.foreground,background:style.background,clipAreas:clips(parent),fragments:[]};
    [...range.getClientRects()].filter(r=>r.width>0&&r.height>0).forEach(r=>{var f={x:r.x,y:r.y,width:r.width,height:r.height,
      visible:style.opaque&&style.unscaled&&[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!hit&&(hit===parent||parent.contains(hit));})};
      fragments.push(f);run.fragments.push(f);});textRuns.push(run);}
  // Inline text has no client box; its real fragments still must pass every gate.
  if(getComputedStyle(e).display==='inline'){result.visible=result.opaque&&fragments.length>0&&fragments.every(f=>f.visible);result.clipped=false;}
  return Object.assign(result,{renderedText:textRuns.map(run=>run.text).join(''),fragments:fragments,textRuns:textRuns,clipAreas:clips(e)});
}
"""


# Only the original link's exact screen-reader suffix is non-visual. Footer and
# answer-row callers never supply an excluded parent; arbitrary hidden text fails.
RELATION_EVIDENCE_PROOF_JS = VISUAL_GEOMETRY + FIXED_TEXT_PROOF_JS + r"""
var e=arguments[0],panel=document.getElementById('np-overview-relation-panel'),r=rect(panel),suffix=null,
    source=e.matches('[data-task-relation-source]')?e:e.previousElementSibling?.matches('[data-task-relation-source]')?e.previousElementSibling:null;
if(e.matches('[data-task-relation-source]')){
  var notes=e.querySelectorAll(':scope > span.np-sr');suffix=notes.length===1?notes[0]:null;
  if(e.tagName!=='A'||!suffix||suffix!==e.lastChild||suffix.className!=='np-sr'||suffix.textContent!=='（新标签页）'||suffix.children.length)
    throw Error('Original source link screen-reader suffix was changed or duplicated');
}
var proof=fixedTextProof(e,suffix),accessibleText=proof.text;
if(suffix)proof.text=proof.renderedText;
return Object.assign(proof,{elementTag:e.tagName,accessibleText:accessibleText,accessibilitySuffix:suffix?{tag:suffix.tagName,className:suffix.className,text:suffix.textContent}:null,
  panelId:panel.id,panelContains:panel.contains(e),relationId:e.closest('[data-task-relation]')?.dataset.taskRelation,
  sourceRecord:source?{id:source.dataset.taskRelationSource,url:source.href,version:source.dataset.sourceVersion,status:source.dataset.sourceStatus}:null,
  panelClientRect:{x:r.x+panel.clientLeft,y:r.y+panel.clientTop,width:panel.clientWidth,height:panel.clientHeight},viewport:{x:0,y:0,width:innerWidth,height:innerHeight}});
"""


# Presentation labels are reviewed copy; identities, parentage and coverage come
# from the frozen scientific source, never from the DOM being tested.
S0_RELATION_LABELS = {
    'tasks:relation:88': '同环境 tour 内多条指令，段间接驳依协议',
    'tasks:relation:89': '类别目标按序组合', 'tasks:relation:90': '提供类别目标',
    'tasks:relation:91': '提供实例图片目标', 'tasks:relation:92': '提供语言描述目标',
    'tasks:relation:93': '语言目标按序接续', 'tasks:relation:94': '成功对象不同：地点与物体实例',
}


# Reviewed display arrangement, independent of controller coordinates/metadata.
# This is not scientific parentage; source IDs/parents still come from science.
S0_TASK_ROWS = (
    ('task:pointnav', 'task:ddn', 'task:vln', 'task:multion'),
    ('task:imagenav', 'task:instanceimagenav', 'task:ivln', 'task:goat'),
    ('task:roomnav', 'task:category-objectnav', 'task:ndh', 'task:lamon'),
    ('task:audiogoal', 'task:language-objectnav', 'task:remote-referent-navigation', 'task:comon'),
    ('task:audiopointgoal', 'task:hieranav', 'task:soon'),
    ('task:aerial-visual-object-search', 'task:person-finding-following', 'task:namo'),
)
S0_SPACING_TOLERANCE = 1 / 16  # CSS pixel rounding only; never a whole-pixel drift.
S0_TOOLBAR_LABELS = (
    ('np-all-scopes', 'DETAILS', '全部阅读范围与术语'),
    ('np-overview-comparison', 'DETAILS', '任务输入与完成要求'),
    ('np-task-relations', 'DETAILS', '7条有据对照与组合'),
    ('np-overview-notes', 'DETAILS', '范围说明'),
    ('np-overview-analysis', 'BUTTON', '单篇论文解析'),
    ('np-map-relations-toggle', 'BUTTON', None),
)
WORKSPACE_CONTROL_SPECS = (
    ('.np-tabs > [data-tree-tab="g"]', 'BUTTON', '', 'g', '全景', 15),
    ('.np-tabs > [data-tree-tab="l"]', 'BUTTON', '', 'l', '文献发展', 15),
    ('.np-tabs > [data-tree-tab="c"]', 'BUTTON', '', 'c', '困难与思路', 15),
    ('.np-tabs > [data-tree-tab="a"]', 'BUTTON', '', 'a', '论文解析', 15),
    ('#np-reading-tools > summary', 'SUMMARY', '', None, '阅读工具', 16),
    ('#np-overview-toggle', 'BUTTON', 'np-overview-toggle', None, None, 15),
    ('.np-identity-controls > summary', 'SUMMARY', '', None, '论文身份与来源版本', 15),
    ('#np-graph-fullscreen', 'BUTTON', 'np-graph-fullscreen', None, '全屏查看', 14),
)


def s0_footer_expected(science):
    from navigation_research_map import build_research_map, NATIVE_RELATION_LABELS
    graph = build_research_map(science)
    positions = graph['positions']; root = graph['roots'][0]
    literature = next(pid for pid in positions[root]['childIds'] if positions[pid]['entityId'] == 'legacy:nav:l')
    challenge = next(pid for pid in positions[root]['childIds'] if positions[pid]['entityId'] == 'legacy:nav:c')
    directory = next(pid for pid in positions[literature]['childIds'] if positions[pid].get('sourceDirectoryGroupId') == 'task')
    scopes = {scope['id']: scope for scope in science['scopes']}
    tasks = [{'scope': sid, 'id': next(row['canonicalPositionId'] for row in graph['scopeEntries'] if row['scopeId'] == sid)} for sid, _, _ in TASK_INDEX]
    ids = [root, literature, challenge, directory] + [row['id'] for row in tasks] + positions[challenge]['childIds']
    def counts(field):
        result = dict(direct=0, condition=0, gap=0)
        for task in tasks:
            coverage = scopes[task['scope']]['coverage']
            result['direct' if coverage.get('direct', {}).get(field) else 'condition' if coverage.get('condition', {}).get(field) else 'gap'] += 1
        return result
    method, ci = counts('methodCount'), counts('challengeCount')
    coverage = ('当前方法：{direct}个入口直接关联、{condition}个仅条件关联、{gap}个未整理；'.format(**method) +
                'CI：{direct}个直接关联、{condition}个仅条件关联、{gap}个未整理。'.format(**ci) +
                '选段覆盖，不代表全文精读或领域穷尽。')
    return {'root': root, 'literature': literature, 'directory': directory,
            'challenge': challenge, 'challengeIds': list(positions[challenge]['childIds']), 'tasks': tasks,
            'nodes': [{'id': pid, 'parent': positions[pid]['parentId'], 'entity': positions[pid]['entityId']} for pid in ids],
            'coverage': coverage, 'legend': ['实线：原目录父子', '虚线：有据对照／组合'],
            'defaultReadout': '按需选择关系核对来源',
            'readouts': {rid: label + ' · ' + NATIVE_RELATION_LABELS[science['relations'][rid]['relationType']] for rid, label in S0_RELATION_LABELS.items()}}


DESKTOP_CHROME_GEOMETRY_JS = 'var workspaceControlSpecs=' + json.dumps(WORKSPACE_CONTROL_SPECS, ensure_ascii=False) + ';\n' + r"""
function desktopChromeGeometry(){
  function frame(selector){var matches=document.querySelectorAll(selector),e=matches[0];if(!e)return {selector:selector,count:0};
    var r=rect(e),cs=getComputedStyle(e),p=box(e),number=k=>parseFloat(cs[k])||0;
    return {selector:selector,count:matches.length,rect:r,clientRect:{x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight},
      position:cs.position,display:cs.display,opaque:p.opaque,unscaled:p.unscaled,top:e.scrollTop,left:e.scrollLeft,
      marginTop:number('marginTop'),marginBottom:number('marginBottom'),marginLeft:number('marginLeft'),marginRight:number('marginRight'),paddingTop:number('paddingTop'),paddingBottom:number('paddingBottom'),
      paddingLeft:number('paddingLeft'),paddingRight:number('paddingRight'),rowGap:number('rowGap')};}
  var header=document.querySelector('.site-header'),app=document.getElementById('navigation-product'),start=app?.querySelector('.np-global-start'),
    workspace=document.getElementById('np-workspace'),identity=document.getElementById('np-selection-context'),bar=workspace?.querySelector('.np-workspace-bar');
  var a=window.NavigationProductApp,b=a?.getBundle(),r=a?.getState().route,source=null;
  if(b&&r&&Array.isArray(b.scopes)&&b.researchMap){var path=[],p=b.positions[r.node],seen=new Set(),pathValid=!!p;while(p&&!seen.has(p.id)&&path.length<256){seen.add(p.id);path.push(p);if(p.parentId&&!b.positions[p.parentId])pathValid=false;p=b.positions[p.parentId];}if(p)pathValid=false;
    var scopes=new Map(b.scopes.map(s=>[s.id,s])),scope=r.tree==='g'?path.map(p=>scopes.get(p.sourceScopeId)).find(s=>s&&s.id!=='scope:all'):null;
    scope=scope||scopes.get(r.scope);var route=path.find(p=>['pipeline','pipeline_family','pipeline_or_representation','development_group'].includes(p.kind)),
      routeEntity=route&&b.entities[route.entityId],paper=r.paper&&b.papers[r.paper],version=r.version&&b.versions[r.version],
      names={poni:'PONI',semexp:'SemExp',vlfm:'VLFM',harnessvln:'HarnessVLN',navharness:'NavHarness（终身导航）',goat:'GOAT',modiin:'ModIIN',esc:'ESC',zson:'ZSON',cow:'CoW',cmp:'CMP',duet:'DUET',hamt:'HAMT',l3mvn:'L3MVN',vlmaps:'VLMaps',conceptgraphs:'ConceptGraphs',hovsg:'HOV-SG'},
      versionText=version?(version.label||version.descriptor||r.version):'来源版本待选择';if(versionText==='unknown')versionText='来源版本待核';
    source={route:r,scopeId:scope?.id,routePositionId:route?.id||null,atRoot:r.tree==='g'&&r.node===b.researchMap.roots[0],
      tabSourceSha256:b.delivery?.sourceModelSha256||null,tabPath:r.tree==='g'?(pathValid?path.slice().reverse().map(p=>({id:p.id,parentId:p.parentId||null,entityId:p.entityId,tree:p.tree,scopeId:p.scopeId})):null):[],
      fields:[['当前'+(scope?.displayRole||'阅读范围'),scope?.label],['当前路线',route?(routeEntity?.label||route.sourceLabel||route.label):{g:'全局研究图',l:'文献树',c:'挑战–思路树',a:'论文解析树'}[r.tree]],
        ['当前论文',r.paper?(names[r.paper]||paper?.label||paper?.title||r.paper):'尚未选择'],['来源版本',r.version?versionText+(version?.status==='snapshot_not_version_pinned'?' · 未固定快照':''):'尚未选择']]};}
  function text(e){return e?fixedTextProof(e):null;}
  return {layoutWidth:document.body.clientWidth,rootClientWidth:document.documentElement.clientWidth,rootRect:rect(document.documentElement),rootGutter:getComputedStyle(document.documentElement).scrollbarGutter,
    body:frame('body'),header:frame('.site-header'),app:frame('#navigation-product'),
    start:frame('#navigation-product > .np-global-start'),workspace:frame('#np-workspace'),identity:frame('#np-selection-context'),bar:frame('#np-workspace > .np-workspace-bar'),
    identitySource:source,identityFields:identity?[...identity.children].map(e=>({tag:e.tagName,className:e.className,children:[...e.children].map(n=>n.tagName),label:text(e.querySelector(':scope > dt')),value:text(e.querySelector(':scope > dd'))})):[],
    controls:workspaceControlSpecs.map(spec=>{var matches=bar?bar.querySelectorAll(':scope > '+spec[0]):[],e=matches[0];return {selector:spec[0],count:matches.length,tag:e?.tagName,id:e?.id,tree:e?.dataset.treeTab||null,hidden:!!e?.hidden,disabled:!!e?.disabled,hover:!!e?.matches(':hover'),selected:e?.getAttribute('aria-selected')||null,proof:text(e)};}),
    topology:!!header&&header.nextElementSibling===app&&start?.parentElement===app&&workspace?.parentElement===app&&
      identity?.parentElement===workspace&&identity.nextElementSibling===bar};
}
"""


WORKSPACE_TAB_SCIENCE_SHA256 = '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c'


def workspace_tab_source_contract(graph):
    """Derive the one legal highlighted tab from frozen source parent edges."""
    positions, roots = graph['positions'], graph['roots']
    if (graph.get('sourceModelSha256') != WORKSPACE_TAB_SCIENCE_SHA256 or len(roots) != 1 or
            roots[0] not in positions or positions[roots[0]].get('entityId') != 'legacy:nav:goal' or
            positions[roots[0]].get('parentId') is not None):
        raise RuntimeError('Workspace tabs lack the exact reviewed global source root')
    result = {}
    for identity in positions:
        path, seen, current = [], set(), identity
        while current is not None:
            if current not in positions or current in seen or len(path) >= 256:
                raise RuntimeError('Workspace tab source parent chain is missing, cyclic or excessive')
            seen.add(current); position = positions[current]
            if position.get('id') != current or position.get('tree') != 'g' or position.get('scopeId') != 'scope:all':
                raise RuntimeError('Workspace tab source ancestry changed its exact position identity')
            parent = position.get('parentId')
            if parent is not None and (parent not in positions or current not in positions[parent]['childIds']):
                raise RuntimeError('Workspace tab source parent and child edges disagree')
            path.append({key: position.get(key) for key in ('id', 'parentId', 'entityId', 'tree', 'scopeId')})
            current = parent
        path.reverse()
        branches = [row['entityId'] for row in path if row['entityId'] in ('legacy:nav:l', 'legacy:nav:c')]
        if path[0]['id'] != roots[0] or len(branches) != (0 if identity == roots[0] else 1):
            raise RuntimeError('Workspace tab source path has a wrong root or ambiguous branch')
        result[identity] = {'tab': {'legacy:nav:l': 'l', 'legacy:nav:c': 'c'}[branches[0]] if branches else 'g', 'path': path}
    return result


@functools.lru_cache(maxsize=2)
def load_workspace_tab_sources(model_path, source_sha256):
    """The cache key includes source location and reviewed science identity."""
    import gzip
    try:
        from navigation_research_map import build_research_map
    except ModuleNotFoundError:
        from scripts.navigation_research_map import build_research_map
    raw = gzip.decompress(Path(model_path).read_bytes())
    if source_sha256 != WORKSPACE_TAB_SCIENCE_SHA256 or hashlib.sha256(raw).hexdigest() != source_sha256:
        raise RuntimeError('Workspace tab model differs from the reviewed scientific source')
    return workspace_tab_source_contract(build_research_map(json.loads(raw)))


def workspace_selected_tree(route, source):
    tree = route.get('tree')
    if tree in ('l', 'c', 'a'):
        return tree
    if tree != 'g' or route.get('scope') != 'scope:all':
        raise RuntimeError('Workspace tab route has no exact source tree')
    model_path = str(Path(__file__).resolve().parents[1] / 'data/navigation-product/model.json.gz')
    expected = load_workspace_tab_sources(model_path, WORKSPACE_TAB_SCIENCE_SHA256).get(route.get('node'))
    if (not expected or source.get('tabSourceSha256') != WORKSPACE_TAB_SCIENCE_SHA256 or
            source.get('tabPath') != expected['path']):
        raise RuntimeError('Workspace tab ancestry differs from the exact reviewed source path')
    return expected['tab']


def check_desktop_chrome(data):
    """Budget from independently measured, contiguous chrome to the viewport edge.

    The old y132 assumed no shared header or selection identity. Never infer the
    available height from the landing itself, or trust a product CSS variable.
    """
    chrome, viewport = data.get('chrome'), data['viewport']
    if not chrome or not chrome.get('topology'):
        raise RuntimeError('Desktop viewport-filling budget lacks its exact chrome structure')
    width = chrome['layoutWidth']
    if not isinstance(width, (int, float)) or not math.isfinite(width) or not 1200 <= width <= viewport['width']:
        raise RuntimeError('Desktop viewport-filling budget has an invalid layout viewport')
    selectors = {'body': 'body', 'header': '.site-header', 'app': '#navigation-product', 'start': '#navigation-product > .np-global-start',
                 'workspace': '#np-workspace', 'identity': '#np-selection-context', 'bar': '#np-workspace > .np-workspace-bar'}
    for key, selector in selectors.items():
        frame = chrome[key]
        if (frame.get('count') != 1 or frame.get('selector') != selector or not frame.get('opaque') or not frame.get('unscaled') or
                frame.get('top') != 0 or frame.get('left') != 0 or not rect_inside(frame['rect'], viewport) or
                not rect_inside(frame['clientRect'], frame['rect']) or
                frame['display'] == 'none' or frame['position'] not in (('static', 'relative', 'sticky') if key == 'header' else ('static', 'relative'))):
            raise RuntimeError('Desktop viewport-filling chrome is missing, shifted, hidden or scaled')
    body, header, app, start, workspace, identity, bar = (chrome[key] for key in selectors)
    root = chrome['rootRect']
    if (chrome['rootGutter'] != 'stable' or not width <= chrome['rootClientWidth'] <= viewport['width'] or
            not _reader_close(root['x'], 0) or not width <= root['width'] <= viewport['width'] or
            not _reader_close(width, min(root['width'], chrome['rootClientWidth'])) or
            any(body[key] != 0 for key in ('marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'paddingTop', 'paddingBottom', 'paddingLeft', 'paddingRight')) or
            not _reader_close(body['rect']['x'], 0) or not _reader_close(body['rect']['y'], 0) or
            not _reader_close(body['rect']['width'], width) or not _reader_close(body['clientRect']['width'], width)):
        raise RuntimeError('Desktop layout width is not its actual zero-margin body and reserved root gutter')
    bottom = lambda row: row['rect']['y'] + row['rect']['height']
    end = lambda row: row['clientRect']['y'] + row['clientRect']['height'] - row['paddingBottom']
    checks = [(header['rect']['x'], 0), (header['rect']['y'], 0), (header['rect']['width'], width),
              (app['rect']['x'], 0), (app['rect']['width'], width), (app['rect']['y'], bottom(header)),
              (bottom(app), viewport['height']), (app['paddingLeft'], 16), (app['paddingRight'], 16),
              (app['paddingBottom'], 4 if data['home'] and viewport['height'] <= 950 else 16),
              (start['rect']['y'], app['clientRect']['y'] + app['paddingTop'] + start['marginTop']),
              (workspace['rect']['y'], bottom(start) + start['marginBottom'] + workspace['marginTop'] + app['rowGap']),
              (bottom(workspace) + workspace['marginBottom'], end(app)),
              (workspace['rect']['x'], 16), (workspace['rect']['width'], width - 32),
              (identity['rect']['y'], workspace['clientRect']['y'] + workspace['paddingTop'] + identity['marginTop']),
              (bar['rect']['y'], bottom(identity) + identity['marginBottom'] + bar['marginTop'] + workspace['rowGap'])]
    if any(not _reader_close(actual, expected) for actual, expected in checks):
        raise RuntimeError('Desktop viewport-filling budget has a chrome gap, overlap or wrong bottom edge')
    top = bottom(bar) + bar['marginBottom'] + workspace['rowGap']
    area = dict(x=workspace['clientRect']['x'] + workspace['paddingLeft'], y=top,
                width=workspace['clientRect']['width'] - workspace['paddingLeft'] - workspace['paddingRight'], height=end(workspace) - top)
    if not rect_inside(area, viewport):
        raise RuntimeError('Desktop viewport-filling chrome leaves no positive content budget')
    source, fields = chrome.get('identitySource'), chrome.get('identityFields', [])
    if not source or source.get('route') != data['route'] or not source.get('scopeId') or len(source.get('fields', [])) != 4 or len(fields) != 4:
        raise RuntimeError('Desktop selection identity lacks all four original source-bound fields')
    for field, texts in zip(fields, source['fields']):
        if field.get('tag') != 'DIV' or field.get('className') != 'np-context-field' or field.get('children') != ['DT', 'DD']:
            raise RuntimeError('Desktop selection identity changed its four DT/DD pairs')
        for key, font, text in zip(('label', 'value'), (11, 13), texts):
            proof = field.get(key)
            if not proof or not text or abs(proof['fontSize'] - font) > S0_SPACING_TOLERANCE:
                raise RuntimeError('Desktop selection identity lost its original labels or type size')
            check_chrome_text(proof, text, font, identity['clientRect'], viewport)
    selected_tree = workspace_selected_tree(data['route'], source)
    controls = chrome.get('controls', [])
    if len(controls) != len(WORKSPACE_CONTROL_SPECS):
        raise RuntimeError('Desktop workspace omitted an original control')
    for control, (selector, tag, identity, tree, text, font) in zip(controls, WORKSPACE_CONTROL_SPECS):
        hidden = selector == '#np-overview-toggle' and not source['atRoot']
        if (control.get('selector') != selector or control.get('count') != 1 or control.get('tag') != tag or
                control.get('id') != identity or control.get('tree') != tree or control.get('hidden') != hidden or control.get('disabled')):
            raise RuntimeError('Desktop workspace control identity or legitimate hidden state changed')
        if tree and control.get('selected') != str(tree == selected_tree).lower():
            raise RuntimeError('Desktop workspace tab lost its actual selected source tree')
        if hidden:
            if control['proof']['opaque'] or control['proof']['visible']:
                raise RuntimeError('Desktop workspace exposed its route-inapplicable original-map control')
            continue
        text = text or ('原全局树图' if data['home'] else '回到差异概览')
        proof = control.get('proof')
        if not proof or abs(proof['fontSize'] - font) > S0_SPACING_TOLERANCE:
            raise RuntimeError('Desktop workspace control changed original type size')
        check_chrome_text(proof, text, font, app['clientRect'], viewport)
    return area


def check_chrome_text(proof, text, font, *areas):
    """Record current chrome colors, including legitimate native transitions.

    CSS tests preserve the original color declarations. Scientific text retains
    its independent 4.5 contrast gate; chrome gains no new color redesign here.
    """
    areas = list(areas)
    color = lambda value: (isinstance(value, list) and len(value) == 3 and
                           all(type(channel) in (int, float) and math.isfinite(channel) and 0 <= channel <= 255 for channel in value))
    if (proof['text'] != text or proof['renderedText'] != text or not proof['fragments'] or not proof['textRuns'] or
            ''.join(run['text'] for run in proof['textRuns']) != text or not _reader_proof(proof, *areas) or proof['clipped'] or
            abs(proof['fontSize'] - font) > S0_SPACING_TOLERANCE or not color(proof['foreground']) or not color(proof['background'])):
        raise RuntimeError('Desktop chrome text changed, disappeared, clipped or lost its current styling')
    for run in proof['textRuns']:
        if (not run['opaque'] or not run['unscaled'] or abs(run['fontSize'] - font) > S0_SPACING_TOLERANCE or
                not color(run['foreground']) or not color(run['background']) or not run['fragments'] or
                any(not fragment['visible'] or not all(rect_inside(fragment, area) for area in areas + run['clipAreas']) for fragment in run['fragments'])):
            raise RuntimeError('Desktop chrome text fragment is hidden, covered, restyled or clipped')
    if any(not fragment['visible'] or not all(rect_inside(fragment, area) for area in areas + proof['clipAreas']) for fragment in proof['fragments']):
        raise RuntimeError('Desktop chrome final text fragment is not fully visible')


# A visible relation button must not be centred inside its scrollable menu:
# centring R91 unnecessarily scrolls the menu's summary out of its client area.
RELATION_SELECTOR_REVEAL_JS = VISUAL_GEOMETRY + r"""
var e=arguments[0],relation=arguments[1],menu=e.closest('#np-task-relations'),summary=menu&&menu.querySelector(':scope > summary');
if(!menu||!summary)throw Error('Exact relationship selector menu is missing');
function measure(){var r=rect(menu);return {relation:relation,buttonId:e.id,buttonTag:e.tagName,buttonRelation:e.dataset.relationSelect,
  menuId:menu.id,menuCount:document.querySelectorAll('#np-task-relations').length,open:menu.open,
  topology:menu.matches('#np-reading-landing>.np-overview-map-toolbar>#np-task-relations')&&e.matches('.np-relation-selectors>button')&&menu.contains(e),
  scrollTop:menu.scrollTop,scrollLeft:menu.scrollLeft,scrollHeight:menu.scrollHeight,scrollWidth:menu.scrollWidth,
  menuRect:r,clientRect:{x:r.x+menu.clientLeft,y:r.y+menu.clientTop,width:menu.clientWidth,height:menu.clientHeight},
  buttonRect:rect(e),summaryRect:rect(summary),viewport:{x:0,y:0,width:innerWidth,height:innerHeight},window:{x:scrollX,y:scrollY}};}
var before=measure();e.scrollIntoView({block:'nearest',inline:'nearest'});
return {relation:relation,requested:{block:'nearest',inline:'nearest'},before:before,after:measure()};
"""


def check_relation_selector_reveal(data, relation):
    if data.get('relation') != relation or data.get('requested') != {'block': 'nearest', 'inline': 'nearest'}:
        raise RuntimeError('Relationship selector reveal did not request the exact minimal native scroll')
    before, after = data['before'], data['after']
    for frame in (before, after):
        if (frame.get('relation') != relation or frame.get('buttonRelation') != relation or
                frame.get('buttonId') != 'np-relation-select-' + relation or frame.get('buttonTag') != 'BUTTON' or
                frame.get('menuId') != 'np-task-relations' or frame.get('menuCount') != 1 or
                frame.get('open') is not True or frame.get('topology') is not True or
                frame.get('window') != {'x': 0, 'y': 0}):
            raise RuntimeError('Relationship selector reveal lost its exact native target or stationary page')
    for key in ('menuRect', 'clientRect', 'viewport', 'scrollHeight', 'scrollWidth'):
        if before[key] != after[key]:
            raise RuntimeError('Relationship selector reveal changed its containing geometry')
    was_inside = all(rect_inside(before['buttonRect'], before[area], tolerance=0) for area in ('clientRect', 'viewport'))
    if was_inside and any(before[key] != after[key] for key in ('scrollTop', 'scrollLeft', 'buttonRect', 'summaryRect')):
        raise RuntimeError('Already visible relationship selector was unnecessarily scrolled')
    if not all(rect_inside(after['buttonRect'], after[area]) for area in ('clientRect', 'viewport')):
        raise RuntimeError('Relationship selector reveal left the native target clipped or outside its client area')


def reveal_relation_selector(driver, control, relation, report, save):
    data = driver.js(RELATION_SELECTOR_REVEAL_JS, control, relation)
    report.setdefault('relationSelectorRevealChecks', []).append(data)
    save()
    check_relation_selector_reveal(data, relation)
    return data


# The toolbars' 160ms hover/selection colour transitions can outlive Driver.settle's two
# frames. Wait for their natural completion, not for a readability gate to pass.
# This local wait never finishes/cancels animations or changes rendered styles.
S0_TOOLBAR_PAINT_TIMEOUT_MS = 2000
SCOPED_TOOLBAR_PAINT_SETTLE_JS = r"""
var budget=arguments[0],done=arguments[arguments.length-1],start=performance.now();
var toolbar=null,timer=null,frame=null,completed=false,quietFrames=0,observed=new Map();
var result={status:'pending',scopeSelector:paintScopeSelector,timeoutMs:budget,elapsedMs:0,before:null,after:null,observedTransitions:[]};
function identity(e){return {id:e.id||'',tag:e.tagName,className:e.getAttribute('class')||'',treeTab:e.getAttribute('data-tree-tab'),selected:e.getAttribute('aria-selected')};}
function paintProperty(p){return /^(?:color|background-color|border-(?:(?:top|right|bottom|left)-)?color)$/.test(p);}
function metadata(a){var t=a.effect.getComputedTiming();return {target:identity(a.effect.target),property:a.transitionProperty,playState:a.playState,pending:a.pending,currentTime:a.currentTime,playbackRate:a.playbackRate,duration:t.duration,endTime:t.endTime};}
function relevant(){return toolbar.getAnimations({subtree:true}).filter(a=>a instanceof CSSTransition&&paintProperty(a.transitionProperty));}
function snapshot(){
  if(!toolbar)return null;
  return {colors:[toolbar,...toolbar.querySelectorAll('*')].map(e=>{var s=getComputedStyle(e);return {...identity(e),color:s.color,backgroundColor:s.backgroundColor,borderTopColor:s.borderTopColor,borderRightColor:s.borderRightColor,borderBottomColor:s.borderBottomColor,borderLeftColor:s.borderLeftColor};}),transitions:relevant().map(metadata)};
}
function finish(status,reason){
  if(completed)return;completed=true;clearTimeout(timer);cancelAnimationFrame(frame);
  result.status=status;result.reason=reason||'';
  try{result.after=snapshot();}catch(e){result.status='error';result.reason='Final paint diagnostics unavailable: '+String(e);}
  result.elapsedMs=performance.now()-start;
  if(result.status==='settled'&&result.elapsedMs>=budget){result.status='timeout';result.reason='Final paint diagnostics exceeded the fixed budget';}
  result.observedTransitions=[...observed.values()];done(result);
}
function inspect(){
  if(performance.now()-start>=budget){finish('timeout','Toolbar paint transitions did not settle within the fixed budget');return null;}
  if(document.querySelectorAll(paintScopeSelector).length!==1||document.querySelectorAll(paintScopeSelector)[0]!==toolbar||!toolbar.isConnected){finish('error',paintScopeName+' changed or disappeared during paint settlement');return null;}
  var active=false;
  for(var a of relevant()){
    var m=metadata(a),elapsed=performance.now()-start;
    if(!observed.has(a)){
      if(observed.size>=64){finish('error','Excessive toolbar transition churn');return null;}
      observed.set(a,{firstSeenMs:elapsed,lastSeenMs:elapsed,first:m,last:m});
    }else{var seen=observed.get(a);seen.lastSeenMs=elapsed;seen.last=m;}
    if(m.playState==='finished'||(m.playState==='idle'&&!m.pending))continue;
    if(!Number.isFinite(m.endTime)||m.endTime<0||!Number.isFinite(m.duration)||m.duration<0||!Number.isFinite(m.playbackRate)||m.playbackRate<=0||m.playState==='paused'){
      finish('error','Toolbar paint transition cannot finish naturally with finite timing');return null;
    }
    active=true;
  }
  return active;
}
function tick(){
  if(completed)return;
  try{
    var active=inspect();if(active===null)return;
    quietFrames=active?0:quietFrames+1;
    if(quietFrames>=2){finish('settled');return;}
    frame=requestAnimationFrame(tick);
  }catch(e){finish('error','Toolbar paint inspection failed: '+String(e));}
}
try{
  if(!Number.isFinite(budget)||budget<=0)throw Error('Invalid toolbar paint budget');
  timer=setTimeout(()=>finish('timeout','Toolbar paint settlement exceeded the fixed budget'),budget);
  var roots=document.querySelectorAll(paintScopeSelector);
  if(roots.length!==1)throw Error('Expected exactly one '+paintScopeName);
  toolbar=roots[0];
  if(typeof CSSTransition!=='function'||typeof toolbar.getAnimations!=='function')throw Error('CSS transition inspection unavailable');
  result.before=snapshot();
  if(inspect()!==null)frame=requestAnimationFrame(tick);
}catch(e){finish('error','Toolbar paint inspection failed: '+String(e));}
"""


S0_TOOLBAR_PAINT_SELECTOR = '#np-reading-landing .np-overview-map-toolbar'
DESKTOP_CHROME_PAINT_SELECTOR = '#np-workspace > .np-workspace-bar'
S0_TOOLBAR_PAINT_SETTLE_JS = ('var paintScopeSelector=' + json.dumps(S0_TOOLBAR_PAINT_SELECTOR) +
                            ',paintScopeName="S0 toolbar";\n' + SCOPED_TOOLBAR_PAINT_SETTLE_JS)
DESKTOP_CHROME_PAINT_SETTLE_JS = ('var paintScopeSelector=' + json.dumps(DESKTOP_CHROME_PAINT_SELECTOR) +
                                ',paintScopeName="Desktop workspace toolbar";\n' + SCOPED_TOOLBAR_PAINT_SETTLE_JS)


def settle_s0_toolbar_paint(driver, report, save, phase):
    data = driver.call('POST', '/execute/async', {
        'script': S0_TOOLBAR_PAINT_SETTLE_JS, 'args': [S0_TOOLBAR_PAINT_TIMEOUT_MS]})
    report.setdefault('s0ToolbarPaintSettles', []).append({'phase': phase, 'scope': 's0-map-toolbar', 'settle': data})
    save()  # Preserve even timeout/error diagnostics before raising.
    if (not isinstance(data, dict) or data.get('status') != 'settled' or
            data.get('scopeSelector') != S0_TOOLBAR_PAINT_SELECTOR or
            data.get('timeoutMs') != S0_TOOLBAR_PAINT_TIMEOUT_MS or
            not isinstance(data.get('elapsedMs'), (int, float)) or
            not 0 <= data['elapsedMs'] < S0_TOOLBAR_PAINT_TIMEOUT_MS or
            not data.get('before') or not data.get('after')):
        raise RuntimeError('S0 toolbar paint transitions failed to settle within the fixed budget')
    return data


def desktop_chrome_snapshot(driver, report, save, phase, script, *args):
    """Settle only the audited workspace bar before either chrome-bearing snapshot."""
    if script not in (DESKTOP_SHELL_SNAPSHOT_JS, S0_FOOTER_SNAPSHOT_JS):
        raise RuntimeError('Desktop chrome paint wait requires an exact chrome-bearing snapshot')
    data = driver.call('POST', '/execute/async', {
        'script': DESKTOP_CHROME_PAINT_SETTLE_JS, 'args': [S0_TOOLBAR_PAINT_TIMEOUT_MS]})
    report.setdefault('desktopChromePaintSettles', []).append({
        'phase': phase, 'scope': 'desktop-workspace-toolbar', 'settle': data})
    save()  # Preserve diagnostics on the new scope, including every timeout/error.
    if (not isinstance(data, dict) or data.get('status') != 'settled' or
            data.get('scopeSelector') != DESKTOP_CHROME_PAINT_SELECTOR or
            data.get('timeoutMs') != S0_TOOLBAR_PAINT_TIMEOUT_MS or
            not isinstance(data.get('elapsedMs'), (int, float)) or
            not 0 <= data['elapsedMs'] < S0_TOOLBAR_PAINT_TIMEOUT_MS or
            not data.get('before') or not data.get('after')):
        raise RuntimeError('Desktop workspace paint transitions failed to settle within the fixed budget')
    return driver.js(script, *args)


S0_FOOTER_SNAPSHOT_JS = VISUAL_GEOMETRY + DESKTOP_CHROME_GEOMETRY_JS + FIXED_TEXT_PROOF_JS + SCROLL_REGION_VISIBILITY_JS + r"""
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),b=a.getBundle(),landing=document.getElementById('np-reading-landing'),
    map=document.getElementById('np-overview-map'),panels=document.querySelectorAll('#np-overview-relation-panel'),panel=panels[0],
    footers=document.querySelectorAll('#np-overview-footer,.np-overview-footer'),footer=footers.length===1?footers[0]:null,
    legends=document.querySelectorAll('.np-map-legend'),legend=legends.length===1?legends[0]:null,
    coverages=document.querySelectorAll('.np-map-coverage'),coverage=coverages.length===1?coverages[0]:null,
    persisted=history.state&&history.state[m.KEY],expected=arguments[0];
function frame(e){if(!e)return null;var cs=getComputedStyle(e),r=rect(e);return {id:e.id,tag:e.tagName,className:e.className,parent:e.parentElement?.id,
  rect:r,clientRect:{x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight},
  position:cs.position,display:cs.display,flexDirection:cs.flexDirection,flexGrow:cs.flexGrow,flexShrink:cs.flexShrink,flexBasis:cs.flexBasis,
  rowGap:parseFloat(cs.rowGap),marginTop:parseFloat(cs.marginTop),marginBottom:parseFloat(cs.marginBottom),
  paddingTop:parseFloat(cs.paddingTop),paddingBottom:parseFloat(cs.paddingBottom),borderTop:parseFloat(cs.borderTopWidth),borderBottom:parseFloat(cs.borderBottomWidth),
  minHeight:cs.minHeight,maxHeight:cs.maxHeight,overflowX:cs.overflowX,overflowY:cs.overflowY,
  top:e.scrollTop,left:e.scrollLeft,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,
  maxTop:Math.max(0,e.scrollHeight-e.clientHeight),inline:{top:e.style.top,left:e.style.left,width:e.style.width,height:e.style.height}};}
function overview(value){return value&&value.contexts?.[m.contextKey(value.route)]?.overviewView||null;}
function labelBox(e){var proof=box(e),r=proof.rect;if(proof.visible||!proof.opaque)return proof;proof.hitProbes=[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].map(([fx,fy])=>{var x=r.x+r.width*fx,y=r.y+r.height*fy,hit=document.elementFromPoint(x,y),ids=[];for(var n=hit;n;n=n.parentElement)if(n.id)ids.push(n.id);return {x:x,y:y,label:!!hit&&(hit===e||e.contains(hit)),selector:!!hit&&(hit===selector||selector.contains(hit)),ancestorIds:ids,hitId:hit?.id||'',hitTag:hit?.tagName||null};});return proof;}
var selector=document.getElementById('np-task-relations');
function nodeLabels(e){var result={};[['name','.np-task-reading-name'],['contract','.np-task-reading-contract'],['challenge','.np-map-challenge-label'],['title','h2,h3'],['subtitle','.np-overview-goal p']].forEach(([key,selector])=>{var n=e.querySelector(selector);if(n)result[key]=labelBox(n);});if(e.matches('.np-map-task-root'))result.title=labelBox(e);return result;}
var candidates=[landing,...landing.querySelectorAll('*')].filter(e=>!e.closest('.np-overview-map-toolbar')).map(scrollRegionCandidate).filter(Boolean),
    selected=map.dataset.selectedRelation||null;
var toolbar=landing.querySelector(':scope > .np-overview-map-toolbar');
return {chrome:desktopChromeGeometry(),expected:expected,ready:document.getElementById('navigation-product').dataset.loadState,home:!landing.hidden,
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},window:{x:scrollX,y:scrollY},scale:m.getBucket(s).graphScale,
  route:s.route,historyRoute:persisted?.route||null,focus:document.activeElement.id,selectedRelation:selected,relationsVisible:map.dataset.relationsVisible,
  selectorOpen:selector.open,relationSelector:{id:selector.id,tag:selector.tagName,open:selector.open,inToolbar:selector.matches('#np-reading-landing>.np-overview-map-toolbar>#np-task-relations'),count:document.querySelectorAll('#np-task-relations').length,proof:box(selector)},runtimeOverview:overview(s),historyOverview:overview(persisted),
  landing:frame(landing),map:frame(map),toolbar:toolbar?Object.assign(frame(toolbar),{count:landing.querySelectorAll(':scope > .np-overview-map-toolbar').length,beforeMap:toolbar.nextElementSibling===map,first:landing.firstElementChild===toolbar,
    controls:[...toolbar.children].map(e=>({id:e.id,tag:e.tagName,proof:fixedTextProof(e.tagName==='DETAILS'?e.querySelector(':scope > summary'):e)}))}):null,footerCount:footers.length,legendCount:legends.length,coverageCount:coverages.length,
  footer:footer?Object.assign(frame(footer),{afterMap:map.nextElementSibling===footer,insideMap:map.contains(footer),children:[...footer.children].map(e=>({id:e.id,className:e.className})),proof:fixedTextProof(footer)}):null,
  legend:legend?Object.assign(frame(legend),{inFooter:legend.parentElement===footer,labels:[...legend.children].map(e=>({id:e.id,className:e.className,proof:fixedTextProof(e)}))}):null,
  coverage:coverage?Object.assign(frame(coverage),{inFooter:coverage.parentElement===footer,proof:fixedTextProof(coverage)}):null,
  nodes:[...map.querySelectorAll('[data-map-position]')].map(e=>({id:e.dataset.mapPosition,parent:b.positions[e.dataset.mapPosition]?.parentId,
    entity:b.positions[e.dataset.mapPosition]?.entityId,scope:e.dataset.taskOpen||null,visibility:getComputedStyle(e).visibility,display:getComputedStyle(e).display,opacity:getComputedStyle(e).opacity,proof:box(e),labels:nodeLabels(e)})),
  layoutNotes:[...map.querySelectorAll('[data-layout-note]')].map(e=>({key:e.dataset.layoutNote,hidden:e.hidden,proof:box(e)})),
  panel:Object.assign(frame(panel),{count:panels.length,hidden:panel.hidden,articles:[...panel.querySelectorAll('[data-task-relation]')].filter(e=>!e.hidden).map(e=>e.dataset.taskRelation)}),
  scrollRegionCandidates:candidates,scrollIds:candidates.filter(e=>e.rendered).map(e=>e.id)};
"""


def check_s0_text(proof, text, *areas, font_size=15):
    areas = list(areas) + [proof['rect']] + proof['clipAreas']
    if (proof['text'] != text or proof['renderedText'] != text or
            ''.join(run['text'] for run in proof['textRuns']) != text or
            not _reader_proof(proof, *areas, font_size=font_size) or not proof['fragments'] or not proof['textRuns']):
        raise RuntimeError('S0 complete footer/source text is shortened, hidden, clipped or unreadable')
    for run in proof['textRuns']:
        if (not run['opaque'] or not run['unscaled'] or run['fontSize'] < font_size or
                len(run['foreground']) != 3 or len(run['background']) != 3 or
                contrast_ratio(run['foreground'], run['background']) < 4.5 or not run['fragments'] or
                any(not fragment['visible'] or not all(rect_inside(fragment, area) for area in areas + run['clipAreas']) for fragment in run['fragments'])):
            raise RuntimeError('S0 original wrapped text is covered, scaled or clipped by its actual client region')
    if any(not fragment['visible'] or not all(rect_inside(fragment, area) for area in areas) for fragment in proof['fragments']):
        raise RuntimeError('S0 final text fragment is covered or clipped')


def s0_label_exposed(proof, data):
    """A closed selector requires exposure; only exact open-popup hits may cover it."""
    if proof.get('visible') is True:
        return True
    selector = data.get('relationSelector') or {}
    popup = selector.get('proof') or {}
    if (data.get('selectorOpen') is not True or selector.get('open') is not True or
            selector.get('id') != 'np-task-relations' or selector.get('tag') != 'DETAILS' or
            selector.get('count') != 1 or selector.get('inToolbar') is not True or not all(popup.get(key) is True for key in ('visible', 'opaque', 'unscaled')) or
            not popup.get('rect') or not rect_inside(popup['rect'], data['viewport'])):
        return False
    probes = proof.get('hitProbes', [])
    fractions = ((.5, .5), (.1, .1), (.9, .1), (.1, .9), (.9, .9))
    if len(probes) != len(fractions):
        return False
    label_rect, popup_rect = proof['rect'], popup['rect']
    covered = False
    for probe, (fx, fy) in zip(probes, fractions):
        x, y = label_rect['x'] + label_rect['width'] * fx, label_rect['y'] + label_rect['height'] * fy
        if (any(not isinstance(probe.get(key), (int, float)) or not math.isfinite(probe[key]) or
                abs(probe[key] - wanted) > S0_SPACING_TOLERANCE for key, wanted in (('x', x), ('y', y))) or
                type(probe.get('label')) is not bool or type(probe.get('selector')) is not bool):
            return False
        if probe['label']:
            if probe['selector']:
                return False
            continue
        if (not probe['selector'] or 'np-task-relations' not in probe.get('ancestorIds', []) or
                not popup_rect['x'] <= x <= popup_rect['x'] + popup_rect['width'] or
                not popup_rect['y'] <= y <= popup_rect['y'] + popup_rect['height']):
            return False
        covered = True
    return covered


def check_s0_adaptive_spacing(data):
    """Reconstruct the compact baseline from source membership and DOM measures.

    No product-computed spacing data or final y positions establish the baseline.
    Only actual row heights affect compactBottom; the reviewed compact arrangement
    plus measured header-note height establishes each baseline y independently.
    """
    expected, map_box = data['expected'], data['map']
    mr, client = map_box['rect'], map_box['clientRect']
    close = lambda a, b: (isinstance(a, (int, float)) and math.isfinite(a) and
                          abs(a - b) <= S0_SPACING_TOLERANCE)
    if (data['viewport']['width'] < 1200 or map_box['clientHeight'] <= 0 or map_box['clientWidth'] <= 0 or
            not close(client['height'], map_box['clientHeight']) or not close(client['width'], map_box['clientWidth']) or
            abs(mr['height'] - map_box['clientHeight']) > .5 or abs(mr['width'] - map_box['clientWidth']) > .5):
        raise RuntimeError('S0 adaptive spacing requires actual positive desktop map client dimensions')
    rows = data['nodes']; by_id = {row['id']: row for row in rows}
    if (len(rows) != len(expected['nodes']) or len(by_id) != len(expected['nodes']) or
            [{key: row[key] for key in ('id', 'parent', 'entity')} for row in rows] != expected['nodes'] or
            [{'scope': row['scope'], 'id': row['id']} for row in rows if row['scope'] is not None] != expected['tasks']):
        raise RuntimeError('S0 adaptive spacing lost exact source node/task identity or count')
    tasks = {row['scope']: row for row in rows if row['scope'] is not None}
    if set(tasks) != {scope for group in S0_TASK_ROWS for scope in group}:
        raise RuntimeError('S0 adaptive spacing lost an original editorial task row')
    challenge_ids = expected['challengeIds']
    if (len(set(challenge_ids)) != len(challenge_ids) or
            [row['id'] for row in expected['nodes'] if row['parent'] == expected['challenge']] != challenge_ids or
            [row['id'] for row in rows if row['parent'] == expected['challenge']] != challenge_ids):
        raise RuntimeError('S0 adaptive spacing changed original C-child order or count')
    width = map_box['clientWidth']
    cw = min(520, max(408, 408 + (width - 1360) * 112 / 480))
    lw, cx = width - cw - 24, width - cw
    tw = (lw - 8 - 3 * 16) / 4
    notes = data.get('layoutNotes', [])
    if [note['key'] for note in notes] != ['0', '1', '2', '3', 'editorial', 'process']:
        raise RuntimeError('S0 adaptive spacing lost original measured header notes')
    notes_bottom = 0
    for note in notes:
        key, proof = note['key'], note['proof']
        if key == 'process':
            if not note['hidden']:
                raise RuntimeError('S0 adaptive spacing exposed the original hidden process note')
            continue
        nr = proof['rect']; editorial = key == 'editorial'
        x = max(5, lw / 2 - 130) if editorial else 8 + int(key) * (tw + 16)
        # Decorative notes have pointer-events:none, so their box hit test is
        # intentionally not an uncovered-text predicate. Measure actual layout.
        if (note['hidden'] or not proof['opaque'] or not proof['unscaled'] or proof['clipped'] or
                not rect_inside(nr, client) or not rect_inside(nr, data['viewport']) or
                not close(proof['fontSize'], 15) or not close(nr['x'] - mr['x'], x) or
                not close(nr['y'] - mr['y'], 104 if editorial else 124) or
                not close(nr['width'], 260 if editorial else tw)):
            raise RuntimeError('S0 adaptive spacing moved, reduced or covered original header notes')
        if not editorial:
            notes_bottom = max(notes_bottom, nr['y'] - mr['y'] + nr['height'])
    task_start = max(150, notes_bottom + 5) + 8
    baseline = {expected['root']: (math.floor((width - 540) / 2 + .5), 0, 540),
                expected['literature']: (0, 60, lw), expected['challenge']: (cx, 60, cw),
                expected['directory']: (8, 104, 130)}
    task_ranks = {}
    for rank, group in enumerate(S0_TASK_ROWS):
        for column, scope in enumerate(group):
            row = tasks[scope]; task_ranks[row['id']] = rank
            baseline[row['id']] = (8 + column * (tw + 16), task_start + rank * 76, tw)
    challenge_y = 108
    for identity in challenge_ids:
        baseline[identity] = (cx, challenge_y, cw)
        challenge_y += by_id[identity]['proof']['rect']['height'] + 5
    compact_bottom = max(baseline[row['id']][1] + row['proof']['rect']['height'] for row in rows)
    available = max(0, map_box['clientHeight'] - compact_bottom - 12)
    row_count = len(set(task_ranks.values()))
    task_extra = min(24, available / (row_count - 1)) if row_count > 1 else 0
    c_extra = min(7, available / (len(challenge_ids) - 1)) if len(challenge_ids) > 1 else 0
    challenge_ranks = {identity: index for index, identity in enumerate(challenge_ids)}
    contracts = {scope: (name, contract) for scope, name, contract in TASK_INDEX}
    for row in rows:
        identity, proof = row['id'], row['proof']; r = proof['rect']
        x, y, w = baseline[identity]
        y += task_ranks.get(identity, 0) * task_extra + challenge_ranks.get(identity, 0) * c_extra
        if any(not close(actual, wanted) for actual, wanted in ((r['x'] - mr['x'], x), (r['y'] - mr['y'], y), (r['width'], w))):
            raise RuntimeError('S0 adaptive spacing differs from bounded measured source-row placement')
        is_task, is_c = identity in task_ranks, identity in challenge_ranks
        if (is_task and not close(r['height'], 56) or is_c and not close(r['height'], 37) or
                not rect_inside(r, client, S0_SPACING_TOLERANCE) or
                data['footer']['rect']['y'] - r['y'] - r['height'] < 12 - S0_SPACING_TOLERANCE):
            raise RuntimeError('S0 adaptive spacing stretched a card, overflowed the map or lost footer clearance')
        labels = row.get('labels', {})
        if is_task:
            name, contract = contracts[row['scope']]
            wanted = {'name': (15, name), 'contract': (16, contract)}
        elif is_c:
            wanted = {'challenge': (15, CHALLENGE_LABELS[row['entity']])}
        elif identity == expected['root']:
            wanted = {'title': (20, None), 'subtitle': (15, None)}
        else:
            wanted = {'title': (15 if identity == expected['directory'] else 18, None)}
        if set(labels) != set(wanted):
            raise RuntimeError('S0 adaptive spacing lost original node text proofs')
        replaced = is_c and data['selectedRelation'] is not None
        for key, (font, text) in wanted.items():
            label = labels[key]
            if (not close(label['fontSize'], font) or text is not None and label['text'] != text or
                    label['clipped'] or not label['unscaled'] or not rect_inside(label['rect'], r) or
                    (replaced and (label['opaque'] or label['visible'])) or
                    (not replaced and not _reader_proof(dict(label, visible=s0_label_exposed(label, data)), r, client, data['viewport'], font_size=font))):
                raise RuntimeError('S0 adaptive spacing reduced, substituted, covered or clipped original node text')
    for index, row in enumerate(rows):
        if any(rects_intersect(row['proof']['rect'], other['proof']['rect']) for other in rows[index + 1:]):
            raise RuntimeError('S0 adaptive spacing overlaps original map nodes')
    return dict(compactBottom=compact_bottom, availableExtra=available, taskRowCount=row_count,
                challengeCount=len(challenge_ids), taskExtra=task_extra, challengeExtra=c_extra)


def check_s0_footer(data):
    expected, viewport = data['expected'], data['viewport']
    landing, map_box, footer = data['landing'], data['map'], data['footer']
    fill = check_desktop_chrome(data)
    if (not data['home'] or data['ready'] != 'ready' or (viewport['width'], viewport['height']) not in VIEWPORTS or
            data['window'] != {'x': 0, 'y': 0} or data['scale'] != 1 or
            any(not _reader_close(landing['rect'][key], value) for key, value in fill.items()) or
            data['route'].get('node') != expected['root'] or data['route'].get('tree') != 'g' or
            data['route'].get('paper') is not None or data['route'].get('version') is not None or data['historyRoute'] != data['route']):
        raise RuntimeError('S0 lost its exact source root, unscaled full-height landing or zero outer position')
    if (data['footerCount'] != 1 or not footer or footer['id'] != 'np-overview-footer' or
            footer['className'] != 'np-overview-footer' or footer['parent'] != 'np-reading-landing' or
            not footer['afterMap'] or footer['insideMap'] or data['legendCount'] != 1 or data['coverageCount'] != 1 or
            not data['legend']['inFooter'] or not data['coverage']['inFooter'] or
            footer['children'] != [{'id': '', 'className': 'np-map-legend'}, {'id': '', 'className': 'np-overview-coverage np-map-coverage'}]):
        raise RuntimeError('S0 requires one exact normal-flow footer immediately after the map with both original rows')
    toolbar = data.get('toolbar')
    if (not toolbar or toolbar['count'] != 1 or not toolbar['first'] or not toolbar['beforeMap'] or
            toolbar['parent'] != 'np-reading-landing' or toolbar['position'] not in ('static', 'relative') or
            toolbar['flexGrow'] != '0' or toolbar['flexShrink'] != '0' or toolbar['flexBasis'] != 'auto' or
            toolbar['top'] != 0 or toolbar['left'] != 0 or not rect_inside(toolbar['rect'], landing['clientRect']) or
            not _reader_close(toolbar['rect']['y'], landing['clientRect']['y'] + landing['paddingTop'] + toolbar['marginTop'])):
        raise RuntimeError('S0 map toolbar lost its original natural-flow height and position')
    toolbar_height = toolbar['rect']['height'] + toolbar['marginTop'] + toolbar['marginBottom']
    controls = toolbar.get('controls', [])
    if [(row['id'], row['tag']) for row in controls] != [(identity, tag) for identity, tag, _ in S0_TOOLBAR_LABELS]:
        raise RuntimeError('S0 toolbar dropped or substituted an original control')
    for control, (_, _, label) in zip(controls, S0_TOOLBAR_LABELS):
        text = label if label is not None else ('仅显示所选关系' if data['relationsVisible'] == 'true' else '显示全部关系')
        if abs(control['proof']['fontSize'] - 15) > S0_SPACING_TOLERANCE:
            raise RuntimeError('S0 toolbar changed original control type size')
        check_s0_text(control['proof'], text, landing['clientRect'], viewport)
    if (landing['display'] != 'flex' or landing['flexDirection'] != 'column' or landing['rowGap'] != 0 or
            map_box['parent'] != 'np-reading-landing' or map_box['position'] != 'relative' or
            map_box['flexGrow'] != '1' or map_box['flexShrink'] != '1' or map_box['flexBasis'] != 'auto' or map_box['minHeight'] != '0px' or
            not _reader_close(map_box['rect']['y'], landing['clientRect']['y'] + landing['paddingTop'] + toolbar_height) or
            not _reader_close(map_box['rect']['x'], footer['rect']['x']) or not _reader_close(map_box['rect']['width'], footer['rect']['width']) or
            not _reader_close(map_box['rect']['height'], landing['clientHeight'] - landing['paddingTop'] - landing['paddingBottom'] -
                              toolbar_height - footer['rect']['height'] - footer['marginTop'] - footer['marginBottom'])):
        raise RuntimeError('S0 original map no longer receives the remaining natural-flow landing height')
    for region in (landing, map_box, footer, data['legend'], data['coverage']):
        if (region['top'] != 0 or region['left'] != 0 or region['scrollHeight'] > region['clientHeight'] + 1 or
                region['scrollWidth'] > region['clientWidth'] + 1):
            raise RuntimeError('S0 stationary landing/map/footer has an offset or hidden overflow')
    for row in (footer, data['legend'], data['coverage']):
        if (row['position'] not in ('static', 'relative') or row['overflowX'] != 'visible' or row['overflowY'] != 'visible' or
                any(row['inline'].values()) or not rect_inside(row['rect'], landing['clientRect'])):
            raise RuntimeError('S0 footer or metadata row kept absolute offsets, clipping or its own scrolling region')
    if (footer['display'] != 'flex' or footer['flexDirection'] != 'column' or footer['flexGrow'] != '0' or footer['flexShrink'] != '0' or
            footer['flexBasis'] != 'auto' or footer['maxHeight'] != 'none' or not _reader_close(footer['rowGap'], 4) or
            not rect_inside(map_box['rect'], landing['clientRect']) or rects_intersect(map_box['rect'], footer['rect']) or
            footer['rect']['y'] - (map_box['rect']['y'] + map_box['rect']['height']) < 12 - READER_GEOMETRY_TOLERANCE):
        raise RuntimeError('S0 footer must use natural nonshrinking height and a separate map gap of at least 12px')
    legend, coverage = data['legend'], data['coverage']
    natural = sum(row['rect']['height'] + row['marginTop'] + row['marginBottom'] for row in (legend, coverage)) + footer['rowGap'] + sum(footer[key] for key in ('paddingTop', 'paddingBottom', 'borderTop', 'borderBottom'))
    if (not _reader_close(footer['rect']['height'], natural) or rects_intersect(legend['rect'], coverage['rect']) or
            not _reader_close(coverage['rect']['y'] - legend['rect']['y'] - legend['rect']['height'], 4) or
            not _reader_close(footer['rect']['y'] + footer['rect']['height'], landing['clientRect']['y'] + landing['clientRect']['height'] - landing['paddingBottom'])):
        raise RuntimeError('S0 map did not leave exactly the natural footer rows and bottom padding')
    selected = data['selectedRelation']
    if selected is not None and selected not in expected['readouts']:
        raise RuntimeError('S0 footer readout identifies an unknown source relationship')
    texts = expected['legend'] + [expected['readouts'][selected] if selected else expected['defaultReadout']]
    labels = legend['labels']
    if [(row['id'], row['className']) for row in labels] != [('', 'np-map-parent-key'), ('', 'np-map-relation-key'), ('np-map-relation-readout', '')]:
        raise RuntimeError('S0 legend/readout identities are missing, duplicated or substituted')
    for label, text in zip(labels, texts):
        check_s0_text(label['proof'], text, legend['rect'], footer['rect'], landing['clientRect'], viewport)
    check_s0_text(coverage['proof'], expected['coverage'], footer['rect'], landing['clientRect'], viewport)
    check_s0_text(footer['proof'], ''.join(texts) + expected['coverage'], landing['clientRect'], viewport)
    if [{key: row[key] for key in ('id', 'parent', 'entity')} for row in data['nodes']] != expected['nodes']:
        raise RuntimeError('S0 footer repair changed original map node IDs, source identities or parents')
    tasks = [{'scope': row['scope'], 'id': row['id']} for row in data['nodes'] if row['scope'] is not None]
    if tasks != expected['tasks']:
        raise RuntimeError('S0 footer repair changed original task identities')
    check_s0_adaptive_spacing(data)
    for row in data['nodes']:
        proof = row['proof']
        replaced_challenge = selected is not None and row['id'] in expected['challengeIds']
        if (not proof['unscaled'] or not rect_inside(proof['rect'], map_box['clientRect']) or rects_intersect(proof['rect'], footer['rect']) or
                row['display'] == 'none' or row['opacity'] != '1' or
                (replaced_challenge and (row['visibility'] != 'hidden' or proof['opaque'] or proof['visible'])) or
                (not replaced_challenge and (row['visibility'] != 'visible' or not proof['opaque']))):
            raise RuntimeError('S0 original map node is scaled, incorrectly hidden, clipped or overlaps the footer')
    panel = data['panel']
    if panel['count'] != 1 or panel['parent'] != 'np-overview-map' or panel['hidden'] != (selected is None) or panel['articles'] != ([selected] if selected else []):
        raise RuntimeError('S0 temporary relation panel lost its map parent or exact selected source')
    if data['scrollIds'] != ([] if selected is None else ['np-overview-relation-panel']):
        raise RuntimeError('S0 acquired an extra permanent or nested scrolling region')
    if selected is not None:
        column = next(row['proof']['rect'] for row in data['nodes'] if row['id'] == expected['challenge'])
        pr = panel['rect']; mr = map_box['rect']
        if (panel['position'] != 'absolute' or panel['overflowY'] != 'auto' or panel['overflowX'] != 'auto' or
                not rect_inside(pr, map_box['clientRect']) or not rect_inside(panel['clientRect'], pr) or
                not _reader_close(pr['x'], column['x']) or not _reader_close(pr['width'], column['width']) or
                not _reader_close(pr['y'] - mr['y'], 108) or not _reader_close(pr['height'], mr['height'] - 120) or
                rects_intersect(pr, footer['rect']) or
                any(rects_intersect(pr, row['proof']['rect']) for row in data['nodes'] if row['scope'] is not None)):
            raise RuntimeError('S0 selected panel escapes its actual map/C column or overlaps footer/L tasks')
        if (panel['maxTop'] != max(0, panel['scrollHeight'] - panel['clientHeight']) or
                panel['left'] != 0 or panel['top'] < 0 or panel['top'] > panel['maxTop'] or panel['scrollWidth'] > panel['clientWidth'] + 1):
            raise RuntimeError('S0 temporary evidence panel has invalid effective scrolling')


def check_s0_stability(before, after, restore=False):
    """Only the temporary evidence selection/offset may change the S0 view."""
    for snapshot in (before, after):
        check_s0_footer(snapshot)
    for key in ('expected', 'route', 'historyRoute', 'window', 'scale', 'landing', 'map'):
        if before[key] != after[key]:
            raise RuntimeError('S0 relation interaction moved the landing/map/window or changed the source route')
    if any(before['chrome'][key] != after['chrome'][key] for key in ('layoutWidth', 'rootClientWidth', 'rootRect', 'body', 'header', 'app', 'start', 'workspace', 'identity', 'bar')):
        raise RuntimeError('S0 relation interaction moved its measured chrome budget')
    if (before['toolbar']['rect'] != after['toolbar']['rect'] or before['footer']['rect'] != after['footer']['rect'] or
            [(row['id'], row['proof']['rect']) for row in before['nodes']] != [(row['id'], row['proof']['rect']) for row in after['nodes']]):
        raise RuntimeError('S0 relation interaction shifted the footer or an original task/node')
    if restore:
        for key in ('focus', 'selectedRelation', 'selectorOpen', 'relationsVisible'):
            if before[key] != after[key]:
                raise RuntimeError('S0 restoration lost exact focus, disclosure or selected relationship')
        if before['panel']['top'] != after['panel']['top']:
            raise RuntimeError('S0 restoration lost the exact effective temporary-panel offset')
        check_s0_panel_saved(after)


def check_s0_panel_saved(data):
    for state in (data['runtimeOverview'], data['historyOverview']):
        if (not state or state['selectedRelation'] != data['selectedRelation'] or state['relationScrollTop'] != data['panel']['top'] or
                state['scrollTop'] != data['landing']['top'] or state['relationsOpen'] != data['selectorOpen'] or
                state['linesVisible'] != (data['relationsVisible'] == 'true')):
            raise RuntimeError('S0 history/runtime lost exact effective panel offset or selected source identity')


def check_s0_wheel(before, after, delta):
    check_s0_stability(before, after)
    for key in ('focus', 'selectedRelation', 'selectorOpen', 'relationsVisible'):
        if before[key] != after[key]:
            raise RuntimeError('S0 native wheel changed focus, disclosure or selected source')
    maximum, start, end = before['panel']['maxTop'], before['panel']['top'], after['panel']['top']
    if maximum != after['panel']['maxTop'] or not maximum > 0 or delta == 0 or (end - start) * delta <= 0:
        raise RuntimeError('S0 positive wheel needs real source overflow and a positive native effective movement')
    check_s0_panel_saved(after)


# Hidden overflow can still scroll through focus/scrollIntoView. Record every
# stationary shell ancestor separately from the two legitimate inner scrollers.
STATIONARY_SHELL_SELECTORS = ('html', 'body', '#navigation-product', '#np-workspace', '.np-panels', '.np-tree-pane', '.np-reading-pane')
STATIONARY_SHELL_ANCESTORS_JS = r"""
function stationaryShellAncestors(){return ['html','body','#navigation-product','#np-workspace','.np-panels','.np-tree-pane','.np-reading-pane'].map(selector=>{
  var e=document.querySelector(selector);if(!e)return {selector:selector,missing:true};var r=e.getBoundingClientRect(),cs=getComputedStyle(e);
  return {selector:selector,id:e.id||null,tag:e.tagName,top:e.scrollTop,left:e.scrollLeft,
    scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,
    overflowX:cs.overflowX,overflowY:cs.overflowY,rect:{x:r.x,y:r.y,width:r.width,height:r.height}};
});}
"""


def check_stationary_shell_ancestors(rows):
    if (not isinstance(rows, list) or [r.get('selector') for r in rows] != list(STATIONARY_SHELL_SELECTORS) or
            any(r.get('missing') or any(type(r.get(axis)) not in (int, float) or not math.isfinite(r[axis]) or r[axis] != 0
                                     for axis in ('top', 'left')) for r in rows)):
        raise RuntimeError('A stationary desktop shell ancestor is missing or has a hidden scroll offset')


DESKTOP_SHELL_SNAPSHOT_JS = VISUAL_GEOMETRY + DESKTOP_CHROME_GEOMETRY_JS + SCROLL_REGION_VISIBILITY_JS + FIXED_TEXT_PROOF_JS + STATIONARY_SHELL_ANCESTORS_JS + r"""
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),app=document.getElementById('navigation-product'),
    tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll'),
    pane=document.querySelector('.np-reading-pane'),header=document.getElementById('np-reader-heading'),
    title=document.getElementById('np-reader-object-title'),meta=document.getElementById('np-reader-object-meta'),
    picker=document.getElementById('np-task-route-canvas'),host=document.getElementById('np-tree'),p=a.getBundle().positions[s.route.node],
    returns=document.querySelectorAll('#np-task-route-return'),back=returns.length===1?returns[0]:null,
    treePane=document.querySelector('.np-tree-pane'),footers=document.querySelectorAll('.np-canvas-footer'),footer=footers.length===1?footers[0]:null;
function proof(e){return e?box(e):null;}
function scroll(e){return {top:e.scrollTop,left:e.scrollLeft};}
function metrics(e){return {top:e.scrollTop,left:e.scrollLeft,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,maxTop:Math.max(0,e.scrollHeight-e.clientHeight)};}
var roots=host.querySelectorAll('[data-parallel-tree] > [role=tree] > [role=treeitem]'),b=a.getBundle(),
    scrollCandidates=[tree,reader,...tree.querySelectorAll('*'),...reader.querySelectorAll('*'),...(footer?[footer,...footer.querySelectorAll('*')]:[])].map(scrollRegionCandidate).filter(Boolean);
return {chrome:desktopChromeGeometry(),stationaryAncestors:stationaryShellAncestors(),ready:app.dataset.loadState,route:s.route,methodReading:app.dataset.methodReading,readingLayout:app.dataset.readingLayout,window:{x:scrollX,y:scrollY},
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},home:!document.getElementById('np-reading-landing').hidden,
  landing:rect(document.getElementById('np-reading-landing')),landingOffsets:{top:document.getElementById('np-reading-landing').scrollTop,left:document.getElementById('np-reading-landing').scrollLeft},
  collapsed:app.dataset.readerCollapsed==='true',sourceOverview:app.dataset.activeTree==='g'&&app.dataset.globalFocus==='overview',panels:rect(document.querySelector('.np-panels')),
  tree:rect(tree),treePane:rect(document.querySelector('.np-tree-pane')),reader:rect(reader),pane:rect(pane),
  fixedIdentity:title?{position:title.dataset.objectPosition||null,paper:title.dataset.objectPaper||null,version:title.dataset.objectVersion||null}:null,
  offsets:{tree:scroll(tree),reader:scroll(reader)},scrollMetrics:{tree:metrics(tree),reader:metrics(reader)},heading:proof(header),title:proof(title),meta:proof(meta),
  titleRelation:title?.dataset.objectRelation||null,returnControlCount:returns.length,
  returnControl:back?{tag:back.tagName,disabled:back.disabled,inHeading:back.parentElement===header,insideScroll:reader.contains(back),proof:proof(back)}:null,
  treeFooter:app.dataset.methodReading==='true'?{count:footers.length,proof:proof(footer),inPane:!!footer&&footer.parentElement===treePane,insideTree:!!footer&&tree.contains(footer),
    sourcePosition:p?.id||null,sourceChildCount:p?.childIds.length,
    labels:footer?[...footer.children].map(e=>({id:e.id,tag:e.tagName,proof:fixedTextProof(e)})):[]}:null,
  pickerDisclosure:document.getElementById('np-task-route-relations')?{open:document.getElementById('np-task-route-relations').open,rect:rect(document.getElementById('np-task-route-relations')),position:getComputedStyle(document.getElementById('np-task-route-relations')).position}:null,
  headingInsideScroll:!!header&&reader.contains(header),pickerInsideTree:tree.contains(picker),pickerInToolbar:!!picker.closest('.np-workspace-bar'),
  permanentScrollIds:scrollCandidates.filter(candidate=>candidate.rendered).map(candidate=>candidate.id),scrollRegionCandidates:scrollCandidates,
  rootRows:[...roots].map(e=>({id:e.dataset.position,proof:proof(e.querySelector(':scope > .np-node-row'))})),
  routeRows:[...host.querySelectorAll('[role=treeitem]')].map(e=>({id:e.dataset.position,entity:e.dataset.entity,proof:proof(e.querySelector(':scope > .np-node-row'))})),
  position:p?{id:p.id,kind:p.kind,paper:p.paperId,version:p.versionId,parent:p.parentId}:null,
  relation:document.querySelector('[data-selected-task-relation]')?.dataset.selectedTaskRelation||null,
  visibleTaskDefinitions:[...reader.querySelectorAll('p')].filter(e=>e.textContent===b.scopes.find(scope=>scope.id===s.route.scope)?.definition&&box(e).visible).length,
  analysisEntry:proof(document.getElementById('np-open-version-analysis')),
  analysisStatus:proof(document.querySelector('#np-reader-analysis-entry [data-analysis-state] > p')),
  answer:proof(document.querySelector('#np-detail-content .np-analysis-answer > p'))};
"""


def rects_intersect(left, right):
    """Any positive-area intersection is overlap; shared box edges are allowed."""
    return (min(left['x'] + left['width'], right['x'] + right['width']) > max(left['x'], right['x']) and
            min(left['y'] + left['height'], right['y'] + right['height']) > max(left['y'], right['y']))


def check_desktop_return_control(data):
    control = data.get('returnControl')
    if (data.get('returnControlCount') != 1 or not control or control['tag'] != 'BUTTON' or control['disabled'] or
            not control['inHeading'] or control['insideScroll'] or
            not _reader_proof(control['proof'], data['heading']['rect'], data['viewport'], font_size=15) or
            control['proof']['text'] != '返回路线概览'):
        raise RuntimeError('Fixed relationship return action is hidden, clipped, duplicated or outside its heading')
    if any(rects_intersect(control['proof']['rect'], data[key]['rect']) for key in ('title', 'meta')):
        raise RuntimeError('Fixed relationship title/version overlaps its return action')


def check_method_footer(data):
    """Method footer keeps both complete metadata labels in its own fixed space."""
    footer, viewport, pane = data.get('treeFooter'), data['viewport'], data['treePane']
    if (not footer or footer['count'] != 1 or not footer['inPane'] or footer['insideTree'] or
            not _reader_proof(footer['proof'], pane, viewport, font_size=12) or
            rects_intersect(footer['proof']['rect'], data['tree']) or
            data['tree']['y'] + data['tree']['height'] > footer['proof']['rect']['y'] + 1):
        raise RuntimeError('Method footer is clipped, covered, outside its fixed pane or overlapping the tree viewport')
    labels = footer['labels']
    if (footer['sourcePosition'] != data['route']['node'] or not isinstance(footer['sourceChildCount'], int) or
            footer['sourceChildCount'] < 0 or len(labels) != 2 or
            [(label['tag'], label['id']) for label in labels] != [('SPAN', 'np-canvas-count'), ('SPAN', '')]):
        raise RuntimeError('Method footer lost its exact source count or both original labels')
    expected = [str(len(data['routeRows'])) + ' 个来路与分枝节点 · ' + str(footer['sourceChildCount']) + ' 个直接子节点',
                '选择节点深入 · ＋展开 · 拖动空白平移']
    if footer['proof']['text'] != ''.join(expected):
        raise RuntimeError('Method footer shortened or substituted its complete original metadata')
    for label, text in zip(labels, expected):
        proof = label['proof']
        areas = [proof['rect'], footer['proof']['rect'], pane, viewport] + proof['clipAreas']
        if (proof['text'] != text or proof['renderedText'] != text or
                ''.join(run['text'] for run in proof['textRuns']) != text or
                not _reader_proof(proof, *areas, font_size=12) or not proof['fragments'] or not proof['textRuns']):
            raise RuntimeError('Method footer original label is hidden, shortened, clipped or unreadable')
        for run in proof['textRuns']:
            if (not run['opaque'] or not run['unscaled'] or run['fontSize'] < 12 or
                    len(run['foreground']) != 3 or len(run['background']) != 3 or
                    contrast_ratio(run['foreground'], run['background']) < 4.5 or not run['fragments'] or
                    any(not f['visible'] or not all(rect_inside(f, area) for area in areas + run['clipAreas']) for f in run['fragments'])):
                raise RuntimeError('Method footer original text is hidden, covered or clipped by an ancestor')
        if any(not f['visible'] or not all(rect_inside(f, area) for area in areas) for f in proof['fragments']):
            raise RuntimeError('Method footer wrapped text is covered or outside its full fixed bounds')
    if rects_intersect(labels[0]['proof']['rect'], labels[1]['proof']['rect']):
        raise RuntimeError('Method footer labels overlap each other')


def check_desktop_relation_heading(data, expected):
    check_desktop_shell(data)
    if (data['relation'] != expected['relation']['id'] or data.get('titleRelation') != expected['relation']['id'] or
            data['title']['text'] != 'SemExp → PONI · 复用组件并替换策略' or
            data['meta']['text'] != '当前范围关系' + expected['claimSourceStatus']):
        raise RuntimeError('Fixed relationship heading changed its exact title, relation or source version')


def check_desktop_shell(data, require_s0_footer=False):
    """The ready desktop document is fixed; only the tree and reader scroll."""
    viewport = data['viewport']
    if ((viewport['width'], viewport['height']) not in VIEWPORTS or data['ready'] != 'ready' or
            data['window'] != {'x': 0, 'y': 0}):
        raise RuntimeError('Ready desktop shell is unready or has outer window scroll')
    check_stationary_shell_ancestors(data.get('stationaryAncestors'))
    position = data.get('position')
    method = bool(position and position['kind'] in ('pipeline_recipe', 'versioned_method_card') and
                  data['route']['tree'] in ('g', 'l') and not data.get('relation') and not data['home'])
    if data.get('methodReading') != str(method).lower():
        raise RuntimeError('Desktop method presentation does not match the actual selected source object')
    if method and (data.get('readingLayout') != 'reading' or any(data['route'].get(k) != position.get(v) for k, v in
            (('node', 'id'), ('paper', 'paper'), ('version', 'version')))):
        raise RuntimeError('Desktop method presentation changed reading layout or exact source identity')
    expected = check_desktop_chrome(data)
    if require_s0_footer and not data['home']:
        raise RuntimeError('Designated S0 footer capture did not retain the original home')
    if data['home']:
        if (data.get('landingOffsets') != {'top': 0, 'left': 0} or not data.get('landing') or
                any(not _reader_close(data['landing'][key], value) for key, value in expected.items())):
            raise RuntimeError('Desktop home lost its full-height unscrolled landing')
        if require_s0_footer:
            if not data.get('s0Footer'):
                raise RuntimeError('Designated desktop home capture omitted its S0 footer proof')
            check_s0_footer(data['s0Footer'])
        return
    if any(not _reader_close(data['panels'][k], v) for k, v in expected.items()):
        raise RuntimeError('Desktop workspace differs from the viewport-filling reading contract')
    if data['pickerInsideTree'] or not data['pickerInToolbar'] or data['headingInsideScroll']:
        raise RuntimeError('Relationship picker or fixed object title still belongs to scrolling content')
    if not rect_inside(data['tree'], data['treePane']) or not rect_inside(data['treePane'], expected):
        raise RuntimeError('Desktop tree viewport is outside its fixed pane')
    if method:
        check_method_footer(data)
    if data['collapsed'] or data.get('sourceOverview', False):
        if data['permanentScrollIds'] != ['np-tree-scroll'] or not _reader_close(data['treePane']['width'], expected['width']):
            raise RuntimeError('Collapsed reading pane left another permanent scrolling region')
        return
    if data['permanentScrollIds'] != ['np-tree-scroll', 'np-detail-scroll']:
        raise RuntimeError('Desktop reading needs exactly the tree and reader permanent scroll regions')
    if (not rect_inside(data['pane'], expected) or not rect_inside(data['reader'], data['pane']) or
            not _reader_proof(data['heading'], data['pane'], viewport) or
            not _reader_proof(data['title'], data['heading']['rect'], viewport, font_size=15) or
            not _reader_proof(data['meta'], data['heading']['rect'], viewport, font_size=15) or
            not data['title']['text'].strip() or not data['meta']['text'].strip() or
            data['heading']['rect']['y'] + data['heading']['rect']['height'] > data['reader']['y'] + 1):
        raise RuntimeError('Current object title/version or natural reader content is hidden, clipped or scrolling')
    if data.get('relation') or data.get('returnControlCount', 0):
        check_desktop_return_control(data)
    analysis = data['route']['tree'] == 'a'
    gap = 24 if analysis else 16
    tree_width = (400 if viewport['width'] == 1440 else 448) if analysis or method else (expected['width'] - gap) * 1.1 / 2.1
    if (not _reader_close(data['treePane']['width'], tree_width) or
            not _reader_close(data['pane']['width'], expected['width'] - tree_width - gap) or
            not _reader_close(data['pane']['x'], expected['x'] + tree_width + gap)):
        raise RuntimeError('Tree/reader widths do not match the desktop task or single-paper reading state')


def check_relation_canvas_stability(before, opened, selected, required_positions):
    """Opening a selector and choosing a relation cannot push the actual tree down."""
    for value in (before, opened, selected):
        if value['window'] != {'x': 0, 'y': 0} or value['route'] != before['route']:
            raise RuntimeError('Relation disclosure changed the science route or outer document position')
        if (value['tree'] != before['tree'] or value['treePane'] != before['treePane'] or
                value['offsets']['tree'] != before['offsets']['tree'] or value['rootRows'] != before['rootRows']):
            raise RuntimeError('Relation selector displaced the tree viewport, original root or exact tree offsets')
    overlay = opened['pickerDisclosure']
    if (not overlay or overlay['open'] is not True or overlay['position'] not in ('absolute', 'fixed') or
            not _reader_close(overlay['rect']['width'], 360) or overlay['rect']['height'] > 288 or
            overlay['rect']['x'] < opened['pane']['x'] - 1 or not rect_inside(overlay['rect'], opened['viewport'])):
        raise RuntimeError('Relationship dropdown is not a bounded 360px by at-most-288px overlay over the reader')
    if selected['visibleTaskDefinitions'] != 0:
        raise RuntimeError('Selected relationship repeats a task definition in its visible reader content')
    if selected['relation'] != 'methods:relation:90':
        raise RuntimeError('Reading hierarchy selected another relation')
    for pid in required_positions:
        rows = [r for r in selected['routeRows'] if r['id'] == pid]
        if len(rows) != 1 or not _reader_proof(rows[0]['proof'], selected['tree'], selected['viewport']):
            raise RuntimeError('Relation scene does not show its real root, route and endpoint methods together')
    root = next(r['proof']['rect'] for r in selected['routeRows'] if r['id'] == required_positions[0])
    poni = next(r['proof']['rect'] for r in selected['routeRows'] if r['id'] == required_positions[-1])
    if root['y'] - selected['panels']['y'] > 72 or poni['y'] + poni['height'] - selected['panels']['y'] > 388:
        raise RuntimeError('Relation scene spends the initial tree viewport on controls instead of its source route')


def first_analysis_answer(science, entry):
    """Original preorder, using source kinds rather than a label or hard-coded ID."""
    def visit(pid):
        p = science['positions'][pid]
        yield p
        for child in p['childIds']:
            yield from visit(child)
    return next((p for root in entry['roots'] for p in visit(root) if p['kind'] == 'analysis_answer'), None)


def check_analysis_first_answer(data, answer, entry, answer_text, version_label):
    check_desktop_shell(data)
    if (answer is None or data['fixedIdentity'] != {'position': answer['id'], 'paper': answer['paperId'], 'version': answer['versionId']} or data['position'] != {k: answer[v] for k, v in
            {'id': 'id', 'kind': 'kind', 'paper': 'paperId', 'version': 'versionId', 'parent': 'parentId'}.items()} or
            data['route']['node'] != answer['id'] or data['route']['paper'] != answer['paperId'] or
            data['route']['version'] != answer['versionId'] or data['route']['template'] is not None or
            entry['answeredOriginalCount'] <= 0 or data['offsets']['reader'] != {'top': 0, 'left': 0}):
        raise RuntimeError('Main analysis entry did not reach the first real answer in this exact version')
    coverage = str(entry['answeredOriginalCount']) + '/' + str(entry['originalNodeCount']) + ' 原节点已填 · ' + str(entry['answeredInstanceCount']) + ' 个实例答案'
    if version_label not in data['meta']['text'] or coverage not in data['meta']['text']:
        raise RuntimeError('Fixed analysis heading omitted the exact source version or actual answer coverage')
    if (not data['answer'] or data['answer']['text'] != answer_text or
            not _reader_proof(data['answer'], data['reader'], data['viewport'], font_size=15) or data['answer']['rect']['y'] - data['panels']['y'] > 168):
        raise RuntimeError('First source answer does not start visibly in the initial reader')


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
    if (data['layout'] != 'reading' or data.get('methodReading') != 'true' or data['collapsed'] != str(collapsed).lower() or
            data['reader']['hidden'] != collapsed or data['reader']['entity'] != position['entity'] or
            data['reader']['flowCount'] != 5 or data['history']['model'] != data['preservedState']):
        raise RuntimeError('Reader toggle layout, source content or persisted route is inconsistent')
    viewport, panels, tree = data['viewport'], data['panels'], data['tree']
    if (viewport['width'], viewport['height']) not in VIEWPORTS:
        raise RuntimeError('Reader toggle evidence is not a required desktop viewport')
    if (data['window'] != {'x': 0, 'y': 0} or not rect_inside(panels, viewport) or
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
        expected_reader_width = panels['width'] - data['columnGap'] - (400 if viewport['width'] == 1440 else 448)
        if (reader['display'] == 'none' or reader['tabIndex'] != -1 or
                not _reader_close(rr['width'], expected_reader_width) or
                not _reader_close(tr['width'], panels['width'] - data['columnGap'] - expected_reader_width) or rr['height'] < 320 or
                not _reader_proof(reader['proof'], panels, viewport) or
                not _reader_proof(reader['heading'], rr, viewport, font_size=15) or
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
    for key in ('route', 'position', 'graphScale', 'expanded', 'taskContextKey', 'viewport', 'window', 'methodReading'):
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


# Read-only measurements bind every positive-scroll fixture to actual source state.
END_TARGET_SNAPSHOT_JS = r"""
function actualTreeEndTarget(){
  var a=NavigationProductApp,b=a.getBundle(),s=a.getState(),tree=document.getElementById('np-tree-scroll'),
      rows=[...document.querySelectorAll('#np-tree [data-parallel-tree] [role=treeitem]')],last=rows.at(-1),p=last&&b.positions[last.dataset.position],row=last?.firstElementChild;
  if(!tree||!p||!row)return null;var tr=tree.getBoundingClientRect(),rr=row.getBoundingClientRect();
  return {position:p.id,scope:p.scopeId,tree:p.tree,isFirstNodeRow:row.matches('.np-node-row'),
    row:{x:rr.x,y:rr.y,width:rr.width,height:rr.height},
    viewport:{x:tr.x+tree.clientLeft,y:tr.y+tree.clientTop,width:tree.clientWidth,height:tree.clientHeight}};
}
"""


SCROLL_FIXTURE_SNAPSHOT_JS = END_TARGET_SNAPSHOT_JS + r"""
var a=NavigationProductApp,b=a.getBundle(),s=a.getState(),p=b.positions[s.route.node];
function metrics(id){var e=document.getElementById(id);return {id:id,top:e.scrollTop,left:e.scrollLeft,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,maxTop:Math.max(0,e.scrollHeight-e.clientHeight)};}
return {route:s.route,position:p?{id:p.id,entity:p.entityId,scope:p.scopeId,tree:p.tree,paper:p.paperId,version:p.versionId}:null,
 relation:document.querySelector('[data-selected-task-relation]')?.dataset.selectedTaskRelation||null,window:{x:scrollX,y:scrollY},
 historyIdentity:{url:location.href,length:history.length,entryKey:window.navigation?.currentEntry?.key||null,revision:s.revision,originTrail:s.originTrail},
 treeState:{expanded:NavigationProductModel.getBucket(s).expandedByTree,positions:[...document.querySelectorAll('#np-tree [role=treeitem]')].map(e=>({id:e.dataset.position,selected:e.getAttribute('aria-selected')}))},
 focusPosition:document.activeElement.closest('#np-tree [data-parallel-tree] [role=treeitem]')?.dataset.position||null,
 tree:metrics('np-tree-scroll'),reader:metrics('np-detail-scroll'),treeEndTarget:actualTreeEndTarget(),
 disclosures:[...document.querySelectorAll('#np-detail-scroll details')].map(e=>({id:e.id,classes:e.className,open:e.open,hidden:e.hidden,summary:e.querySelector(':scope > summary')?.textContent||null,claims:[...e.querySelectorAll('[data-claim-id]')].map(c=>c.dataset.claimId)})),
 branches:[...document.querySelectorAll('#np-tree [data-parallel-tree] [role=treeitem][aria-expanded="false"]')].map(e=>{var p=b.positions[e.dataset.position];return {id:p.id,tree:p.tree,scope:p.scopeId,children:p.childIds,control:e.id,label:e.querySelector(':scope > .np-node-row > .np-node-label').textContent};})};
"""


def check_scroll_fixture_source(before, after):
    for key in ('route', 'position', 'relation', 'window'):
        if before[key] != after[key]:
            raise RuntimeError('Native scroll fixture changed exact source identity or outer position: ' + key)


def check_scroll_metrics(metrics, *, headroom=False, require_overflow=True):
    values = [metrics.get(k) for k in ('top', 'left', 'scrollHeight', 'clientHeight', 'maxTop')]
    if (not all(isinstance(n, (int, float)) and not isinstance(n, bool) and math.isfinite(n) for n in values) or metrics['clientHeight'] <= 0 or
            metrics['top'] < 0 or metrics['maxTop'] != max(0, metrics['scrollHeight'] - metrics['clientHeight']) or
            metrics['top'] > metrics['maxTop']):
        raise RuntimeError('Scroll fixture lacks consistent actual scrollHeight/clientHeight measurements')
    if (require_overflow and metrics['maxTop'] <= 0) or (headroom and metrics['maxTop'] - metrics['top'] <= 0):
        raise RuntimeError('Positive-scroll fixture has no measured overflow or remaining headroom')


def check_native_wheel_progress(before, after, region):
    check_scroll_fixture_source(before, after)
    for key in ('historyIdentity', 'treeState'):
        if before[key] != after[key]:
            raise RuntimeError('Native wheel changed history/origin or actual tree state: ' + key)
    check_scroll_metrics(before[region], headroom=True)
    check_scroll_metrics(after[region])
    if after[region]['top'] <= before[region]['top'] or after[region]['top'] <= 0:
        raise RuntimeError('Native wheel did not produce a positive actual internal scroll')
    other = 'tree' if region == 'reader' else 'reader'
    if any(before[other][key] != after[other][key] for key in ('top', 'left')):
        raise RuntimeError('Native wheel moved the other permanent scroll region')


def measured_fixture_action(driver, record, save, description, action):
    item = dict(description, before=driver.js(SCROLL_FIXTURE_SNAPSHOT_JS))
    record.setdefault('nativeScrollActions', []).append(item)
    save()
    try:
        action()
        driver.settle()
    except Exception as exc:
        item['actionError'] = str(exc)[:2000]
        raise
    finally:
        try:
            item['after'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
            save()
        except Exception as exc:
            item['diagnosticError'] = str(exc)[:2000]
            save()
            if 'actionError' not in item:
                raise
    return item['after']


def native_scroll(driver, record, save, region, delta, action_id='source-bound-scroll'):
    return measured_fixture_action(driver, record, save, {'kind': 'wheel', 'region': region, 'delta': delta, 'actionId': action_id},
        lambda: driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': action_id, 'actions': [
            {'type': 'scroll', 'origin': driver.selector('#np-detail-scroll' if region == 'reader' else '#np-tree-scroll'),
             'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': delta, 'duration': 100}]}]}))


def end_target_below_viewport(snapshot):
    """End reveals the last firstElementChild row, not trailing LI text/padding."""
    target = snapshot.get('treeEndTarget')
    positions = snapshot['treeState']['positions']
    if (not target or not positions or not target.get('isFirstNodeRow') or
            target.get('position') != positions[-1]['id'] or
            target.get('scope') != snapshot['route']['scope'] or target.get('tree') != snapshot['route']['tree'] or
            snapshot['tree']['top'] != 0):
        raise RuntimeError('End fixture lacks the exact original last-row target at zero scroll')
    for key in ('row', 'viewport'):
        rect = target.get(key, {})
        if (not all(type(rect.get(axis)) in (int, float) and math.isfinite(rect[axis]) for axis in ('x', 'y', 'width', 'height')) or
                rect['width'] <= 0 or rect['height'] <= 0):
            raise RuntimeError('End fixture lacks actual last-row and tree-viewport geometry')
    # Nearest can also be a no-op when an oversized target spans both edges.
    return (target['row']['y'] > target['viewport']['y'] and
            target['row']['y'] + target['row']['height'] > target['viewport']['y'] + target['viewport']['height'])


def prepare_scroll_fixture(driver, record, save, region, *, require_end_target=False):
    """Only native existing disclosures/real tree branches may supply overflow."""
    if require_end_target and region != 'tree':
        raise RuntimeError('Only the original tree keyboard fixture has an End target')
    initial = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
    item = {'region': region, 'initial': initial, 'steps': [], 'scenario': 'native_original_end_row_below_viewport' if require_end_target else 'native_original_content_overflow'}
    record.setdefault('scrollPreparations', []).append(item)
    save()
    def reset_end_start(current):
        if current['tree']['top'] > 0:
            current = native_scroll(driver, record, save, 'tree', -current['tree']['scrollHeight'], 'end-fixture-start')
            item.setdefault('endStartResets', []).append(current)
            save()
            check_scroll_fixture_source(initial, current)
        return current

    current = reset_end_start(initial) if require_end_target else initial
    if region == 'reader':
        # Original detail and claim/source disclosures, never generated padding.
        for selector in ('#np-evidence-panel', '#np-detail-content .np-evidence', '#np-detail-content .np-source-disclosure', '#np-reading-context-wrap'):
            if current[region]['maxTop'] > 0:
                break
            control = driver.js("var all=[...document.querySelectorAll(arguments[0])].filter(e=>!e.open&&!e.hidden&&!e.closest('[hidden]'));if(all.length>1)throw Error('Ambiguous original content disclosure');var e=all[0];return e?{selector:arguments[0]+' > summary',text:e.querySelector(':scope > summary').textContent}:null;", selector)
            if control:
                current = measured_fixture_action(driver, record, save, {'kind': 'original-disclosure', 'control': control},
                    lambda: driver.click(reveal_control(driver, control)))
                item['steps'].append({'nativeDisclosure': control, 'after': current})
                save()
                check_scroll_fixture_source(initial, current)
    else:
        expanded = set()
        while current[region]['maxTop'] <= 0 or (require_end_target and not end_target_below_viewport(current)):
            candidates = [row for row in current['branches'] if row['id'] not in expanded and row['children'] and
                          row['tree'] == initial['route']['tree'] and row['scope'] == initial['route']['scope']]
            if not candidates:
                break
            branch = candidates[0]
            expanded.add(branch['id'])
            current = measured_fixture_action(driver, record, save, {'kind': 'original-source-branch', 'branch': branch},
                lambda: driver.click(reveal_control(driver, {'selector': '[id="' + branch['control'] + '"] > .np-node-row > .np-node-toggle'})))
            item['steps'].append({'nativeSourceBranch': branch, 'after': current})
            save()
            check_scroll_fixture_source(initial, current)
            if require_end_target:
                current = reset_end_start(current)
    check_scroll_metrics(current[region])
    # A disclosure may reveal itself at the end. Establish real upward headroom
    # through native input, before the positive wheel/End/history fixture begins.
    if current[region]['top'] > 0:
        native_scroll(driver, record, save, region, -current[region]['scrollHeight'], 'source-fixture-start')
        current = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
        item['resetByNativeWheel'] = current
        save()
        check_scroll_fixture_source(initial, current)
    check_scroll_metrics(current[region], headroom=True)
    if current[region]['top'] != 0:
        raise RuntimeError('Native fixture setup did not reach the measured scroll start')
    if require_end_target and not end_target_below_viewport(current):
        raise RuntimeError('Original End target is already visible; positive total overflow alone is insufficient')
    item['ready'] = current
    save()
    return current


def check_fixed_reader_scroll(before, after, *, positive):
    for key in ('route', 'position', 'fixedIdentity', 'relation', 'title', 'meta', 'window'):
        if before[key] != after[key]:
            raise RuntimeError('Reader input moved fixed identity or changed its source: ' + key)
    if before['offsets']['tree'] != after['offsets']['tree']:
        raise RuntimeError('Reader input moved the tree')
    check_scroll_metrics(before['scrollMetrics']['reader'], require_overflow=positive)
    check_scroll_metrics(after['scrollMetrics']['reader'], require_overflow=positive)
    if positive:
        check_scroll_metrics(before['scrollMetrics']['reader'], headroom=True)
        if after['offsets']['reader']['top'] <= before['offsets']['reader']['top']:
            raise RuntimeError('Fixed reader proof did not exercise positive actual scrolling')
    elif (before['scrollMetrics']['reader']['maxTop'] != 0 or
          before['offsets']['reader'] != after['offsets']['reader']):
        raise RuntimeError('Short reader proof must explicitly measure no overflow and no movement')


SELECTED_TREE_FOCUS_JS = r"""
var id='np-node-'+NavigationProductApp.getState().route.node,e=document.getElementById(id),active=document.activeElement;
return {target:id,active:active.id,valid:!!e&&e.tabIndex===0&&e.getAttribute('aria-selected')==='true'&&!!e.closest('#np-tree [data-parallel-tree]'),
 bound:[...document.querySelectorAll('a[href],button,input,select,textarea,summary,[tabindex]')].filter(n=>n.tabIndex>=0&&!n.disabled&&n.getClientRects().length).length+1};
"""


def restore_selected_tree_focus(driver, record, save):
    """Native reverse Tab, without activating/rebuilding the selected source."""
    before = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
    elements = driver.js(READER_DOM_ELEMENTS_JS)
    focus = driver.js(SELECTED_TREE_FOCUS_JS)
    item = {'before': before, 'focusPath': [focus]}
    record['nativeSelectedFocus'] = item
    save()
    if not focus['valid']:
        raise RuntimeError('Selected original tree position is not a native roving focus stop')
    for _ in range(focus['bound']):
        if focus['active'] == focus['target']:
            break
        driver.call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'selected-tree-focus', 'actions': [
            {'type': 'keyDown', 'value': '\ue008'}, {'type': 'keyDown', 'value': '\ue004'},
            {'type': 'keyUp', 'value': '\ue004'}, {'type': 'keyUp', 'value': '\ue008'}]}]})
        driver.settle()
        focus = driver.js(SELECTED_TREE_FOCUS_JS)
        item['focusPath'].append(focus)
        save()
        if not focus['valid'] or focus['target'] != item['focusPath'][0]['target']:
            raise RuntimeError('Native focus traversal changed the selected source target')
    item['afterFocus'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
    save()
    if item['afterFocus']['reader']['top'] > 0:
        native_scroll(driver, record, save, 'reader', -item['afterFocus']['reader']['scrollHeight'], 'selected-focus-reader-start')
    item['after'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
    item['domIdentity'] = driver.js(READER_DOM_IDENTITY_JS, elements)
    save()
    if focus['active'] != focus['target']:
        raise RuntimeError('Native reverse Tab could not reach the selected original tree position')
    check_scroll_fixture_source(before, item['after'])
    check_reader_dom_identity(item['domIdentity'])
    for key in ('historyIdentity', 'treeState', 'reader', 'tree'):
        if before[key] != item['after'][key]:
            raise RuntimeError('Native focus traversal changed source state or prepared offsets: ' + key)


def reader_toggle_checks(driver, report, save, capture, prefix):
    """Append two real-control scenes; keep diagnostics even when a new gate fails."""
    driver.settle()
    initial = driver.js(READER_TOGGLE_SNAPSHOT_JS)
    record = {'viewport': prefix, 'initial': initial, 'phases': []}
    report.setdefault('readerToggleChecks', []).append(record)
    save()
    check_reader_toggle_snapshot(initial, False)
    if initial['reader']['scroll']['maxTop'] <= 0:
        preparation_elements = driver.js(READER_DOM_ELEMENTS_JS)
        prepare_scroll_fixture(driver, record, save, 'reader')
        # Disclosure focus is legitimate setup, not the collapse fixture origin.
        # Restore the existing selected roving item before the positive wheel
        # persists its exact current-tree neutral focus. Do not reselect/rebuild.
        restore_selected_tree_focus(driver, record, save)
        record['preparationDomIdentity'] = driver.js(READER_DOM_IDENTITY_JS, preparation_elements)
        save()
        check_reader_dom_identity(record['preparationDomIdentity'])
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
    e=matches.length===1?matches[0]:null,reader=spec.region==='toolbar'?document.querySelector('.np-workspace-bar'):spec.region==='tree-heading'?document.querySelector('.np-tree-pane .np-pane-top'):document.getElementById(spec.region==='canvas'?'np-tree-scroll':spec.region==='heading'?'np-reader-heading':spec.region==='analysis-entry'?'np-reader-analysis-entry':'np-detail-scroll');
if(!e||!reader.contains(e))throw Error('Exact task-route proof is missing, duplicated or outside its measured region: '+JSON.stringify(spec));
// Only the generated method-name prefix may be represented by the exact fixed title.
// Never skip arbitrary hidden descendants or scientific text in a proof.
var representedPrefix=null;
if(spec.methodIdentity){
  var i=spec.methodIdentity,route=NavigationProductApp.getState().route,host=document.getElementById('np-reader-object-title'),titles=host?.querySelectorAll(':scope > h2'),prefix=e.firstElementChild;
  if(spec.selector!=='[data-mechanism-entity="'+i.entity+'"] > h3'||spec.region||
      e.tagName!=='H3'||e.parentElement.dataset.mechanismEntity!==i.entity||e.childNodes.length!==2||e.children.length!==1||
      !prefix||!prefix.matches('span.np-method-identity-prefix.np-reader-identity-duplicate')||prefix.childNodes.length!==1||prefix.firstChild.nodeType!==Node.TEXT_NODE||
      prefix.dataset.readerDuplicatePosition!==i.position||prefix.textContent!==i.title+' · '||getComputedStyle(prefix).display!=='none'||
      e.lastChild.nodeType!==Node.TEXT_NODE||e.lastChild.textContent!=='方法内部结构'||
      spec.text!==i.title+' · 方法内部结构'||spec.renderedText!=='方法内部结构'||
      titles?.length!==1||titles[0].textContent!==i.title||host.dataset.objectPosition!==i.position||host.dataset.objectEntity!==i.entity||
      host.dataset.objectPaper!==i.paper||host.dataset.objectVersion!==i.version||route.node!==i.position||route.paper!==i.paper||route.version!==i.version)
    throw Error('Method section duplicate does not match the exact fixed source identity');
  representedPrefix=prefix;
}
var rr=rect(reader),heading=reader.querySelector('.np-reader-heading'),hr=heading?rect(heading):null,
    top=Math.max(rr.y+reader.clientTop,hr&&['sticky','fixed'].includes(getComputedStyle(heading).position)?hr.y+hr.height:rr.y+reader.clientTop),content={x:rr.x+reader.clientLeft,y:top,width:reader.clientWidth,height:Math.max(0,rr.y+reader.clientTop+reader.clientHeight-top)},b=box(e);
// A whole article's textContent cannot prove that a collapsed/hidden sentence is visible.
// Measure the original text itself, including every wrapped line, with a DOM Range.
var texts=[],walker=document.createTreeWalker(e,NodeFilter.SHOW_TEXT),n;
while(n=walker.nextNode()){if(n.parentElement.closest('.np-sr')||n.parentElement===representedPrefix)continue;if(n.textContent.trim())texts.push(n);}
function clips(element){var result=[];for(var a=element;a&&a!==reader;a=a.parentElement){var cs=getComputedStyle(a);if(/auto|scroll|hidden|clip/.test(cs.overflowY+' '+cs.overflowX)){var ar=rect(a);result.push({x:ar.x+a.clientLeft,y:ar.y+a.clientTop,width:a.clientWidth,height:a.clientHeight});}}return result;}
var fragments=[],textRuns=[];
texts.forEach(n=>{var range=document.createRange();range.selectNodeContents(n);var parent=box(n.parentElement),run={text:n.textContent,fontSize:parent.fontSize,foreground:parent.foreground,background:parent.background,opaque:parent.opaque,unscaled:parent.unscaled,clipAreas:clips(n.parentElement),fragments:[]};[...range.getClientRects()].filter(r=>r.width>0&&r.height>0).forEach(r=>{var visible=parent.opaque&&parent.unscaled&&[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return hit===n.parentElement||n.parentElement.contains(hit);});var fragment={x:r.x,y:r.y,width:r.width,height:r.height,visible:visible};fragments.push(fragment);run.fragments.push(fragment);});textRuns.push(run);});
if(getComputedStyle(e).display==='inline'){b.visible=b.opaque&&fragments.length>0&&fragments.every(r=>r.visible);b.clipped=false;}
var ancestors=clips(e);
return Object.assign(b,{id:e.id,tag:e.tagName,disabled:!!e.disabled,href:e.tagName==='A'?e.href:null,
  renderedText:texts.map(n=>n.textContent).join(''),fragments:fragments,textRuns:textRuns,clipAreas:ancestors,
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},readerContent:content});
"""


PARALLEL_SCOPE_SNAPSHOT_JS = VISUAL_GEOMETRY + r"""
function measured(spec){return (function(){
""" + TASK_ROUTE_PROOF_JS + r"""
}).call(null,spec);}
var a=NavigationProductApp,b=a.getBundle(),r=a.getState().route,expectedScope=arguments[0],rootSelector=arguments[1],sourceRoots=arguments[2],sourceChildren=arguments[3],rootRecords=arguments[4];
return {scope:r.scope,expectedScope:expectedScope,activeTree:r.tree,selectedTree:document.querySelector('[data-tree-tab][aria-selected=true]')?.dataset.treeTab,
  treeCount:document.querySelectorAll('#np-tree [role=tree]').length,rovingCount:document.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]').length,
  inactiveItemCount:[...document.querySelectorAll('#np-tree [role=treeitem]')].filter(e=>e.dataset.tree!==r.tree).length,
  home:!document.getElementById('np-reading-landing').hidden,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},
  panels:[...document.querySelectorAll('#np-tree [data-parallel-tree]')].map(e=>{var tree=e.dataset.parallelTree,roots=sourceRoots[tree],
    heading=measured({selector:'#np-tree-heading',region:'tree-heading'}),old=e.querySelector(':scope > h3');
    return {tree:tree,scope:e.dataset.scopeId,roots:[...e.querySelectorAll(rootSelector)].map(n=>n.dataset.position),expectedRoots:roots,
      expectedChildren:sourceChildren[tree],children:[...e.querySelectorAll('[role=treeitem]')].filter(n=>!roots.includes(n.dataset.position)).map(n=>box(n.querySelector(':scope > .np-node-row'))),rect:rect(e),
      heading:heading.rect,headingVisible:heading.visible&&heading.opaque&&!heading.clipped,headingProof:heading,headingSelector:'#np-tree-heading',
      headingTree:document.getElementById('navigation-product').dataset.activeTree,headingInPane:e.closest('.np-tree-pane')?.contains(document.getElementById('np-tree-heading'))===true,
      legacyHeading:old?box(old):null,expectedRootRecords:rootRecords[tree],
      rootRecords:[...e.querySelectorAll(rootSelector)].map(n=>({id:n.dataset.position,entity:n.dataset.entity,tree:n.dataset.tree,scope:e.dataset.scopeId,
        proof:measured({selector:'[id='+JSON.stringify(n.id)+'] > .np-node-row > .np-node-label',region:'canvas'})}))};})};
"""


# This receipt is collected for existing method scenes. The 98-image plan is unchanged.
METHOD_READING_SNAPSHOT_JS = VISUAL_GEOMETRY + SCROLL_REGION_VISIBILITY_JS + r"""
function measured(spec){return (function(){
""" + TASK_ROUTE_PROOF_JS + r"""
}).call(null,spec);}
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),b=a.getBundle(),app=document.getElementById('navigation-product'),
    host=document.getElementById('np-tree'),tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll'),
    title=document.getElementById('np-reader-object-title'),mechanism=reader.querySelector('[data-mechanism-entity]'),p=b.positions[s.route.node],
    siblings=[...host.querySelectorAll('details[data-method-siblings]')],intro=[...reader.querySelectorAll('.np-selection-intro')];
function proof(e){return e?box(e):null;}
function field(e){return {text:e.textContent,rendering:renderedElementState(e),proof:box(e)};}
var fields=mechanism?[...mechanism.querySelectorAll('.np-method-flow dd,.np-detail-block > p,.np-method-scope,.np-reading-association,[data-method-claim] > p')]:[];
return {route:s.route,expanded:m.getBucket(s).expandedByTree,methodReading:app.dataset.methodReading,readingLayout:app.dataset.readingLayout,
  selectedRelation:reader.querySelector('[data-selected-task-relation]')?.dataset.selectedTaskRelation||null,
  title:measured({selector:'#np-reader-object-title > h2',region:'heading'}),meta:measured({selector:'#np-reader-object-meta',region:'heading'}),
  fixedIdentity:{position:title.dataset.objectPosition||null,entity:title.dataset.objectEntity||null,paper:title.dataset.objectPaper||null,version:title.dataset.objectVersion||null},
  treeHeading:proof(document.getElementById('np-tree-heading')),tree:rect(tree),reader:rect(reader),pane:rect(document.querySelector('.np-reading-pane')),heading:proof(document.getElementById('np-reader-heading')),
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight},
  rows:[...host.querySelectorAll('[role=treeitem]')].map(e=>({id:e.dataset.position,parent:e.dataset.parent||null,domParent:e.parentElement.closest('[role=treeitem]')?.dataset.position||null,
    entity:e.dataset.entity,tree:e.dataset.tree,level:Number(e.getAttribute('aria-level')),ancestor:e.dataset.methodAncestor==='true',selected:e.getAttribute('aria-selected')==='true',
    tabIndex:e.tabIndex,label:e.querySelector(':scope > .np-node-row > .np-node-label')?.textContent||null,
    sourceLabel:e.querySelector(':scope > .np-node-row > .np-node-label')?.title||null,
    role:e.querySelector(':scope > .np-node-row > .np-node-kind')?.textContent||null,roleProof:proof(e.querySelector(':scope > .np-node-row > .np-node-kind')),proof:proof(e.querySelector(':scope > .np-node-row > .np-node-label'))})),
  siblings:siblings.map(e=>({tag:e.tagName,parent:e.dataset.methodSiblings,open:e.open,summary:proof(e.querySelector(':scope > summary')),
    controls:[...e.querySelectorAll('[data-method-sibling]')].map(c=>({tag:c.tagName,id:c.dataset.methodSibling,treeRole:!!c.closest('[role=treeitem],[role=group]'),text:c.textContent,sourceLabel:c.title,meta:c.querySelector('.np-method-sibling-meta')?.textContent||null,disabled:c.disabled}))})),
  introductions:intro.map(e=>({text:e.textContent,rendering:renderedElementState(e)})),
  mechanism:mechanism?{entity:mechanism.dataset.mechanismEntity,ready:a.getContent().ready(p.entityId),rect:rect(mechanism),fields:fields.map(field)}:null,
  analysisControls:[...document.querySelectorAll('#np-reader-analysis-entry [data-analysis-state] > p,#np-reader-analysis-entry [data-analysis-state] > button,#np-reader-analysis-entry [data-analysis-state] > details > summary')].map(proof)};
"""


def method_reading_expected(science, position, source_positions=None):
    """Original source path and siblings; never a same-paper inferred placement."""
    positions = source_positions if source_positions is not None else science['positions']
    if position['kind'] not in ('pipeline_recipe', 'versioned_method_card') or position['tree'] not in ('g', 'l'):
        raise RuntimeError('Method receipt requires a real selected g/L source method')
    chain, seen, current = [], set(), position
    while current:
        if current['id'] in seen:
            raise RuntimeError('Original method ancestry contains a cycle')
        seen.add(current['id']); chain.insert(0, current['id'])
        parent = positions.get(current.get('parentId'))
        if current.get('parentId') and (not parent or current['id'] not in parent['childIds'] or parent['tree'] != position['tree']):
            raise RuntimeError('Original method ancestry has no matching parent edge')
        current = parent
    parent = positions.get(position.get('parentId'))
    siblings = [pid for pid in parent['childIds'] if pid != position['id']] if parent else []
    def text(value):
        if isinstance(value, str): return value.replace('\\n', '\n')
        if isinstance(value, list): return '；'.join(filter(None, (text(v) for v in value)))
        if isinstance(value, dict): return text(next((value[k] for k in ('text', 'value', 'description', 'statement') if value.get(k)), None))
        return '' if value is None else str(value)
    detail = science['entities'][position['entityId']].get('detail', {})
    flow = detail.get('pipeline') or detail.get('pipeline_contract') or {}
    snippets = ['以下为该方法记录的内部结构；不表示所有关联任务与评测协议都启用全部组件。']
    snippets += [text(flow[k]) for k in ('input', 'representation', 'decision', 'execution', 'feedback') if flow.get(k)]
    snippets += [text(detail[k]) for k in ('change', 'insight', 'scope', 'requiredDisplayConditions', 'boundaries', 'limits') if text(detail.get(k))]
    if detail.get('condition') and not detail.get('requiredDisplayConditions'):
        snippets.append(text(detail['condition']))
    if position.get('association') in ('condition', 'context'):
        snippets.append('条件关联，不能按同一任务或同一评测协议理解。' if position['association'] == 'condition' else '跨任务相关阅读，不作为本任务的解法子节点。')
    child_display = {}
    # Source-bound technical and environment children in the13 reviewed scenes.
    # Unknown/new display transformations require explicit review, not DOM text
    # as an expectation or a permissive shortened-title fallback.
    child_roles = {'technical_improvement': '技术改进', 'technical_design': '技术设计', 'environment': '有来源的阅读条目'}
    for pid in position['childIds']:
        child = positions[pid]; entity = science['entities'][child['entityId']]
        role = child.get('displayRole') or child_roles.get(child['kind'])
        if child['kind']=='environment' and not child.get('displayRole'):
            role = '跨任务相关阅读' if child.get('association')=='context' else '条件投影 · 非协议等同' if child.get('association')=='condition' else '有来源的阅读条目'
        if role:
            role += ' · 条件关联' if child.get('association') == 'condition' else ' · 跨范围相关阅读' if child.get('association') == 'context' else ''
        child_display[pid] = {'label': (entity.get('label') or child.get('sourceLabel') or child['label']) if child['kind'] in child_roles else None,
                              'role': role}
    return {'position': position, 'chain': chain, 'children': position['childIds'], 'siblings': siblings, 'childDisplay': child_display,
            'version': science['versions'][position['versionId']], 'snippets': snippets,
            'siblingLabels': {pid: positions[pid].get('sourceLabel') or positions[pid]['label'] for pid in siblings},
            'siblingVersions': {pid: science['versions'][positions[pid]['versionId']]['label'] for pid in siblings if positions[pid].get('versionId')}}


def method_visible_source_ids(expected, source_positions, expanded):
    """Existing expansion governs original descendants; ancestry is a filtered projection."""
    chain = expected['chain']; path = set(chain); result = []
    def visit(pid):
        result.append(pid)
        if pid not in expanded: return
        children = source_positions[pid]['childIds']
        if any(cid in path for cid in children): children = [cid for cid in children if cid in path]
        for child in children: visit(child)
    visit(chain[0])
    return result


def check_method_reading(data, expected, source_positions, *, compact=False, visual=True):
    """Keep science/source ancestry strict; geometry changes only this presentation."""
    p = expected['position']
    identity = {'position': p['id'], 'entity': p['entityId'], 'paper': p['paperId'], 'version': p['versionId']}
    if (data['methodReading'] != 'true' or data['readingLayout'] != 'reading' or data['selectedRelation'] or
            data['fixedIdentity'] != identity or any(data['route'].get(k) != p.get(v) for k, v in
                (('node', 'id'), ('tree', 'tree'), ('scope', 'scopeId'), ('paper', 'paperId'), ('version', 'versionId')))):
        raise RuntimeError('Method reading receipt substituted its exact route, entity, tree, scope or version')
    rows = data['rows']; ids = [row['id'] for row in rows]
    # Preserve original expanded descendants and closed children without inventing peers.
    wanted = method_visible_source_ids(expected, source_positions, data['expanded'][p['tree']])
    if any(pid not in ids for pid in expected['chain']) or ids != wanted or len(set(ids)) != len(ids) or sum(row['tabIndex'] == 0 for row in rows) != 1:
        raise RuntimeError('Method path lost a real node, added fake peers or changed its one keyboard scope')
    for row in rows:
        source = source_positions[row['id']]
        ancestors = expected['chain'][:-1]
        depth, ancestor = 1, source
        while ancestor.get('parentId'):
            depth += 1; ancestor = source_positions[ancestor['parentId']]
        if (row['parent'] != source.get('parentId') or row['domParent'] != source.get('parentId') or
                row['entity'] != source['entityId'] or row['tree'] != p['tree'] or row['level'] != depth or
                row['ancestor'] != (row['id'] in ancestors) or row['selected'] != (row['id'] == p['id']) or
                row['sourceLabel'] != (source.get('sourceLabel') or source['label']) or not row['label'] or not row['role']):
            raise RuntimeError('Method path changed an original parent edge, role, label or ARIA hierarchy')
        if visual and row['id'] in expected['chain'] and any(not _reader_proof(row[key], data['tree'], data['viewport'], font_size=15) for key in ('proof', 'roleProof')):
            raise RuntimeError('Method current position and full original ancestor labels are not readable together')
    if visual:
        check_method_child_audit(data, expected, source_positions)
    selected = rows[len(expected['chain']) - 1]
    if data['title']['text'] != selected['label'] or data['treeHeading']['text'] != '当前位置与来路':
        raise RuntimeError('Method fixed title and real-path navigation describe different selected objects')
    siblings = data['siblings']
    if expected['siblings']:
        if len(siblings) != 1 or siblings[0]['tag'] != 'DETAILS' or siblings[0]['parent'] != p['parentId']:
            raise RuntimeError('Method sibling navigation is not its real-parent native disclosure')
        controls = siblings[0]['controls']
        if [c['id'] for c in controls] != expected['siblings'] or any(c['tag'] != 'BUTTON' or c['treeRole'] or c['disabled'] or not c['text'] for c in controls):
            raise RuntimeError('Method sibling navigation invented, merged or reordered original positions')
        for control in controls:
            pid = control['id']
            if (control['sourceLabel'] != expected['siblingLabels'][pid] or not control['text'].startswith(expected['siblingLabels'][pid]) or
                    not control['meta'] or (pid in expected['siblingVersions'] and expected['siblingVersions'][pid] not in control['meta'])):
                raise RuntimeError('Method sibling navigation shortened its original source label or full version')
    elif siblings:
        raise RuntimeError('Method without original siblings must not manufacture alternatives')
    if (len(data['introductions']) != 1 or (visual and (data['introductions'][0]['rendering']['display'] != 'none' or
            data['introductions'][0]['rendering']['rendered'] is not False))):
        raise RuntimeError('Method repeated interface introduction remains visible or was removed rather than desktop-hidden')
    mechanism = data['mechanism']
    if not mechanism or mechanism['entity'] != p['entityId'] or not mechanism['ready']:
        raise RuntimeError('Method original mechanism is unready or belongs to another entity')
    fields = mechanism['fields']
    for snippet in expected['snippets']:
        if not any(snippet in field['text'] for field in fields):
            raise RuntimeError('Method natural-flow body lost an original mechanism or scope boundary')
    version = expected['version']
    if version['label'] not in data['meta']['text'] or (version.get('versionStatus') == 'snapshot_not_version_pinned' and '未固定快照' not in data['meta']['text']):
        raise RuntimeError('Method fixed heading omitted its full source version or snapshot warning')
    if not data['analysisControls']:
        raise RuntimeError('Method fixed heading lost its genuine version-analysis state and controls')
    if visual:
        for key in ('title', 'meta'):
            check_task_route_proof(data[key])
        if not _reader_proof(data['treeHeading'], data['viewport'], font_size=15):
            raise RuntimeError('Method real-path heading is unreadable')
        for field in fields:
            proof = field['proof']
            if (not field['rendering']['rendered'] or not proof['opaque'] or not proof['unscaled'] or proof['clipped'] or
                    proof['fontSize'] < 15 or len(proof['foreground']) != 3 or len(proof['background']) != 3 or
                    contrast_ratio(proof['foreground'], proof['background']) < 4.5):
                raise RuntimeError('Method mechanism or scientific boundary is hidden, clipped, scaled or unreadable')
        for control in data['analysisControls']:
            if not _reader_proof(control, data['heading']['rect'], data['viewport'], font_size=15):
                raise RuntimeError('Method fixed analysis state or action is unreadable')
        if compact and (data['heading']['rect']['height'] > 128 or not data.get('pane') or
                        data['reader']['y'] - data['pane']['y'] > 129):
            raise RuntimeError('Reviewed method acceptance case exceeds its 128px fixed heading or relative body-entry budget')
        if not 720 <= mechanism['rect']['width'] <= 880:
            raise RuntimeError('Desktop method prose does not keep the approved natural-flow reading measure')


# User-approved staged reading: first-screen ancestors/current, every rendered
# direct child proved after genuine keyboard reveal, then exact original return.
METHOD_CHILD_SCENES = (
    '-03-method-reader', '-03b-reader-visible', '-11-active-method-reader', '-11c-reader-reopened',
    '-23-poni-method', '-24-poni-claim', '-27-imagenav-zhu', '-27-imagenav-sptm', '-27-imagenav-ving',
    '-28-portable-rl', '-28-portable-llm', '-30-analysis-imported-entry', '-30-analysis-not-imported',
)
METHOD_CHILD_PROBE_START_JS = r"""
if(window.__npMethodChildProbe)throw Error('Method child probe already installed');
var a=NavigationProductApp,m=NavigationProductModel,tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll'),host=document.getElementById('np-tree');
var refs=[host,tree,reader,document.getElementById('np-reader-object-title'),reader.querySelector('[data-mechanism-entity]'),...[...host.querySelectorAll('[role=treeitem]')].flatMap(e=>[e,e.querySelector(':scope > .np-node-row'),e.querySelector(':scope > .np-node-row > .np-node-label'),e.querySelector(':scope > .np-node-row > .np-node-kind')])],active=document.activeElement;
if(!refs.every(n=>n&&n.isConnected)||!active||document.getElementById('navigation-product').dataset.methodReading!=='true')throw Error('Method child probe lacks its real method DOM');
var p={refs:refs,active:active,originalFocus:{id:active.id||null,tag:active.tagName,tabIndex:active.tabIndex},hover:[...document.querySelectorAll(':hover')],events:[],overflow:0,lastScroll:performance.now(),lastFocus:performance.now(),started:performance.now()};
// A Tab search limit is a baseline budget, not a live UI-state counter.
// Keep every workspace candidate object (also hidden/-1) separately bound.
p.workspace=document.getElementById('np-workspace');if(!p.workspace||!p.workspace.contains(host)||!p.workspace.contains(reader))throw Error('Method child workspace is unavailable');
p.candidateSelector='a[href],button,input,select,textarea,summary,[tabindex]';p.candidateTokens=new WeakMap();p.nextCandidateToken=0;
p.token=function(n){if(!p.candidateTokens.has(n))p.candidateTokens.set(n,'method-focus-'+(++p.nextCandidateToken));return p.candidateTokens.get(n);};
p.describe=function(n){var ancestors=[],parent=n;while(parent){var css=getComputedStyle(parent);ancestors.push({token:p.token(parent),hidden:!!parent.hidden,inert:!!parent.inert,display:css.display,visibility:css.visibility,detailsOpen:parent.tagName==='DETAILS'?parent.open:null});if(parent===p.workspace)break;parent=parent.parentElement;}
 return {token:p.token(n),id:n.id||null,tag:n.tagName,role:n.getAttribute('role'),type:n.getAttribute('type'),href:n.getAttribute('href'),name:n.getAttribute('name'),title:n.getAttribute('title'),ariaLabel:n.getAttribute('aria-label'),ariaControls:n.getAttribute('aria-controls'),
  text:n.getAttribute('role')==='treeitem'?null:n.textContent,value:n.matches('input,select,textarea')?n.value:null,checked:n.tagName==='INPUT'?n.checked:null,attributes:[...n.attributes].map(a=>({name:a.name,value:a.value})),sourcePosition:p.sourceItems?.includes(n)?n.dataset.position:null,tabIndex:n.tabIndex,disabled:!!n.disabled,hidden:!!n.hidden,inert:!!n.inert,layout:n.getClientRects().length>0,ancestors:ancestors};};
p.inventory=function(){var all=[...document.querySelectorAll(p.candidateSelector)],eligible=all.filter(n=>n.tabIndex>=0&&!n.disabled&&n.getClientRects().length);return {scopeRoot:p.token(p.workspace),candidateCount:all.length,eligibleCount:eligible.length,eligible:eligible.map(n=>Object.assign(p.describe(n),{inWorkspace:p.workspace.contains(n)}))};};
p.bindCandidates=function(){if(document.getElementById('np-workspace')!==p.workspace)throw Error('Method child workspace was replaced before baseline');p.scopeCandidates=[...p.workspace.querySelectorAll(p.candidateSelector)];p.sourceItems=[...host.querySelectorAll('[role=treeitem]')];p.latestCandidates=p.inventory();p.tabBound=null;};
p.scopeState=function(){var now=[...p.workspace.querySelectorAll(p.candidateSelector)],rootStyle=getComputedStyle(p.workspace);
 return {same:document.getElementById('np-workspace')===p.workspace&&p.workspace.isConnected&&now.length===p.scopeCandidates.length&&now.every((n,i)=>n===p.scopeCandidates[i]&&n.isConnected),
  root:{token:p.token(p.workspace),id:p.workspace.id,tag:p.workspace.tagName,hidden:!!p.workspace.hidden,inert:!!p.workspace.inert,display:rootStyle.display,visibility:rootStyle.visibility},
  items:now.map(n=>{var item=p.describe(n);return p.sourceItems.includes(n)?Object.assign(item,{tabIndex:'native-tree-roving',attributes:item.attributes.map(a=>a.name==='tabindex'?{name:a.name,value:'native-tree-roving'}:a)}):item;}),
  treeTabIndexes:p.sourceItems.map(n=>({position:n.dataset.position,tabIndex:n.tabIndex}))};};
p.bindCandidates();
p.listener=function(e){if(e.type==='scroll')p.lastScroll=performance.now();if(e.type==='focusin')p.lastFocus=performance.now();if(p.events.length>=24){p.overflow=Math.min(25,p.overflow+1);return;}p.events.push({type:e.type,key:e.key||null,trusted:e.isTrusted,target:e.target.id||null,originalTarget:e.target===p.active,readerTarget:e.target===reader});};
p.types=['keydown','pointerdown','pointerup','click','focusin','scroll'];try{p.types.forEach(t=>document.addEventListener(t,p.listener,true));window.__npMethodChildProbe=p;}catch(e){p.types.forEach(t=>document.removeEventListener(t,p.listener,true));delete window.__npMethodChildProbe;throw e;}
return true;
"""
METHOD_CHILD_STATE_JS = r"""
var p=window.__npMethodChildProbe,a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),key=m.contextKey(s.route),host=document.getElementById('np-tree'),tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll');
if(!p)throw Error('Method child state lacks probe');
function rect(e){var r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
function scroll(e){var r=rect(e);return {top:e.scrollTop,left:e.scrollLeft,maxTop:Math.max(0,e.scrollHeight-e.clientHeight),maxLeft:Math.max(0,e.scrollWidth-e.clientWidth),client:{x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight}};}
var active=document.activeElement,current=[host,tree,reader,document.getElementById('np-reader-object-title'),reader.querySelector('[data-mechanism-entity]'),...[...host.querySelectorAll('[role=treeitem]')].flatMap(e=>[e,e.querySelector(':scope > .np-node-row'),e.querySelector(':scope > .np-node-row > .np-node-label'),e.querySelector(':scope > .np-node-row > .np-node-kind')])];
// Freeze the budget and its matching inventory in the first baseline STATE,
// so an external change between baseline setup and this read is not misbound.
p.latestCandidates=p.inventory();if(p.tabBound===null)p.tabBound=Math.min(256,p.latestCandidates.eligibleCount+1);
return {route:s.route,runtime:s,history:history.state,historyKey:m.KEY,contextKey:key,historyLength:history.length,
 viewport:{x:0,y:0,width:innerWidth,height:innerHeight,dpr:devicePixelRatio},window:{x:scrollX,y:scrollY},tree:scroll(tree),reader:scroll(reader),
 active:{id:active.id||null,tag:active.tagName,position:active.closest('[data-position]')?.dataset.position||null,tabIndex:active.tabIndex,original:active===p.active},
 roving:[...host.querySelectorAll('[role=treeitem][tabindex="0"]')].map(e=>e.dataset.position),
 hoverSame:(()=>{var h=[...document.querySelectorAll(':hover')];return h.length===p.hover.length&&h.every((n,i)=>n===p.hover[i]);})(),
 domSame:current.length===p.refs.length&&current.every((n,i)=>n===p.refs[i]&&n.isConnected)&&p.active.isConnected,
 originalFocus:p.originalFocus,scopeCandidates:p.scopeState(),tabBound:p.tabBound};
"""
METHOD_CHILD_ACTION_JS = r"""
var p=window.__npMethodChildProbe;if(!p)throw Error('Method child action lacks probe');
if(arguments[0]==='baseline'){p.active=document.activeElement;p.originalFocus={id:p.active.id||null,tag:p.active.tagName,tabIndex:p.active.tabIndex};p.hover=[...document.querySelectorAll(':hover')];p.bindCandidates();return true;}
if(arguments[0]==='candidates')return p.latestCandidates;
if(arguments[0]==='reset'){p.events=[];p.overflow=0;return true;}
return {events:p.events,overflow:p.overflow};
"""
METHOD_CHILD_IDLE_JS = r"""
var done=arguments[arguments.length-1],p=window.__npMethodChildProbe,start=performance.now(),last=null,since=start,finished=false;
if(!p){done({ok:false,error:'missing probe'});return;}
var watchdog=setTimeout(()=>finish(false,'method state exceeded2000ms'),2000);
function finish(ok,error){if(finished)return;finished=true;clearTimeout(watchdog);var now=performance.now();done({ok:ok&&now-start<=2000,error:error||null,elapsed:now-start,quietMs:now-Math.max(since,p.lastScroll,p.lastFocus)});}
function read(){var a=NavigationProductApp;return JSON.stringify([a.getState(),history.state,document.activeElement?.id,document.activeElement?.tagName,scrollX,scrollY,document.getElementById('np-tree-scroll').scrollTop,document.getElementById('np-tree-scroll').scrollLeft,document.getElementById('np-detail-scroll').scrollTop,document.getElementById('np-detail-scroll').scrollLeft]);}
function tick(){if(finished)return;var now=performance.now(),value=read();if(value!==last){last=value;since=now;}
 if(now-start>=2000){finish(false,'method state did not naturally settle');return;}
 if(now-Math.max(since,p.lastScroll,p.lastFocus)>=160){requestAnimationFrame(()=>requestAnimationFrame(()=>{if(finished)return;if(performance.now()-start>=2000){finish(false,'method frames exceeded2000ms');return;}if(read()===last&&performance.now()-Math.max(p.lastScroll,p.lastFocus)>=160)finish(true);else tick();}));return;}setTimeout(tick,20);}
tick();
"""
METHOD_CHILD_READER_POINT_JS = r"""
var p=window.__npMethodChildProbe,e=document.getElementById('np-detail-scroll');
if(!p||p.active!==e||!e.isConnected||e.tabIndex!==-1)throw Error('Native pointer return is only for the original reader container');
var r=e.getBoundingClientRect(),a={x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight},points=[];
for(var dx of [2,5,10])for(var fy of [.25,.5,.75]){var x=Math.ceil(a.x+dx),y=Math.floor(a.y+a.height*fy);
 if(x-1<a.x||x+1>=a.x+a.width||y-1<a.y||y+1>=a.y+a.height||x<1||y<1||x>=innerWidth-1||y>=innerHeight-1)continue;
 if([[0,0],[-1,0],[1,0],[0,-1],[0,1]].every(([ox,oy])=>document.elementFromPoint(x+ox,y+oy)===e))points.push({x:x,y:y});}
return {id:e.id,client:a,point:points[0]||null,candidateCount:points.length};
"""
METHOD_CHILD_HOVER_POINT_JS = r"""
var p=window.__npMethodChildProbe,e=p?.hover[p.hover.length-1];if(!e||!e.isConnected)throw Error('Original hover target is unavailable');
var r=e.getBoundingClientRect(),points=[];for(var fx of [.5,.1,.9,.02,.98])for(var fy of [.5,.1,.9,.02,.98]){
 var x=Math.floor(r.x+r.width*fx),y=Math.floor(r.y+r.height*fy);if(x<0||y<0||x>=innerWidth||y>=innerHeight)continue;
 if(document.elementFromPoint(x,y)===e)points.push({x:x,y:y});}
return {point:points[0]||null,id:e.id||null,tag:e.tagName};
"""
METHOD_CHILD_PROBE_STOP_JS = r"""
var p=window.__npMethodChildProbe;if(!p)throw Error('Method child probe missing during cleanup');
try{p.types.forEach(t=>document.removeEventListener(t,p.listener,true));return {cleanedUp:true};}finally{delete window.__npMethodChildProbe;}
"""


def method_child_binding(name, data, expected):
    return dict(scene=name, scienceSha256='9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c',
                route=data['route'], identity=data['fixedIdentity'], viewport=data['viewport'],
                expanded=data['expanded'], source=expected['position']['id'])


def method_child_baseline_mode(before):
    """Do not canonicalize a stable runtime/history focus-only difference."""
    import copy
    state, history = before['runtime'], before['history'][before['historyKey']]
    if state == history:
        return 'coherent'
    key = before['contextKey']; normalized = copy.deepcopy(state)
    normalized['contexts'][key]['focusTarget'] = history['contexts'][key]['focusTarget']
    if (normalized != history or before['active']['position'] != before['roving'][0] or
            state['contexts'][key]['focusTarget'] != before['roving'][0]):
        raise RuntimeError('Method child audit cannot natively restore this non-focus baseline history difference')
    return 'stable-keyboard-focus-only'


def check_method_child_state(before, after, *, exact=False):
    if after.get('domSame') is not True or len(after.get('roving', [])) != 1:
        raise RuntimeError('Method child audit replaced its original DOM or one roving scope')
    for key in ('route', 'viewport', 'window', 'historyLength', 'contextKey', 'historyKey', 'originalFocus', 'tabBound'):
        if before[key] != after[key]:
            raise RuntimeError('Method child audit changed its bound source/viewport/window: ' + key)
    for key in ('route', 'originTrail', 'revision'):
        if before['runtime'].get(key) != after['runtime'].get(key):
            raise RuntimeError('Method child keyboard audit navigated or rewrote source history: ' + key)
    scope=after.get('scopeCandidates') or {}; original=before.get('scopeCandidates') or {}
    if (original.get('same') is not True or scope.get('same') is not True or not scope.get('items') or
            any(scope.get(k)!=original.get(k) for k in ('root','items'))):
        raise RuntimeError('Method child audit changed its original workspace focus candidates')
    tree_tabs=scope.get('treeTabIndexes',[])
    if ([row.get('position') for row in tree_tabs]!=[row.get('position') for row in original.get('treeTabIndexes',[])] or
            any(type(row.get('tabIndex')) is not int or row['tabIndex'] not in (-1,0) for row in tree_tabs+original.get('treeTabIndexes',[])) or
            [row.get('position') for row in tree_tabs if row.get('tabIndex')==0]!=after['roving'] or
            [row.get('position') for row in original.get('treeTabIndexes',[]) if row.get('tabIndex')==0]!=before['roving']):
        raise RuntimeError('Method child audit changed its source-bound tree roving candidates')
    context = before['contextKey']
    for key in ('expandedByTree', 'selectedByTree'):
        if before['runtime']['contexts'][context][key] != after['runtime']['contexts'][context][key]:
            raise RuntimeError('Method child keyboard audit changed original expansion or selection')
    for region in ('tree','reader'):
        for key in ('client','maxTop','maxLeft'):
            if before[region][key]!=after[region][key]:
                raise RuntimeError('Method child audit changed original scroll geometry: '+region+'/'+key)
    if exact:
        for key in ('runtime', 'history', 'tree', 'reader', 'active', 'roving', 'hoverSame', 'scopeCandidates'):
            if before[key] != after[key]:
                raise RuntimeError('Method child audit did not restore the exact original state: ' + key)


def check_method_child_candidates(state, inventory):
    """Keep dynamic external diagnostics separate from the frozen input budget."""
    scope=state.get('scopeCandidates') or {}; items=scope.get('items',[])
    if not isinstance(inventory,dict):raise RuntimeError('Method child audit lacks its actual focus candidate inventory')
    eligible=inventory.get('eligible',[])
    if (inventory.get('scopeRoot')!=scope.get('root',{}).get('token') or
            type(inventory.get('candidateCount')) is not int or type(inventory.get('eligibleCount')) is not int or
            inventory['candidateCount']<inventory['eligibleCount'] or inventory['eligibleCount']!=len(eligible) or
            len({row.get('token') for row in eligible})!=len(eligible)):
        raise RuntimeError('Method child focus candidate diagnostics lost their actual identities or counts')
    indexes={row['position']:row['tabIndex'] for row in scope.get('treeTabIndexes',[])}
    actual=[]
    for item in items:
        row=dict(item);row['tabIndex']=indexes.get(row['sourcePosition']) if row.get('sourcePosition') else row['tabIndex']
        if type(row['tabIndex']) is not int:
            raise RuntimeError('Method child candidate has no exact source-bound tabindex')
        if row.get('sourcePosition') and 'attributes' in row:
            row['attributes']=[dict(a,value=str(row['tabIndex'])) if a['name']=='tabindex' else a for a in row['attributes']]
        if row['tabIndex']>=0 and not row['disabled'] and row['layout']:
            actual.append(dict(row,inWorkspace=True))
    if ([row for row in eligible if row.get('inWorkspace') is True]!=actual or
            any(type(row.get('inWorkspace')) is not bool or not row.get('token') or
                type(row.get('tabIndex')) is not int or row['tabIndex']<0 or row.get('disabled') is not False or row.get('layout') is not True for row in eligible)):
        raise RuntimeError('Method child scope candidates were omitted or mislabeled as external')


def check_method_child_audit(data, expected, source_positions):
    audit = data.get('childReadability')
    if not isinstance(audit, dict) or audit.get('status') != 'verified_native_children' or audit.get('cleanedUp') is not True:
        raise RuntimeError('Method capture lacks its complete native child readability audit')
    name = data.get('captureName', '')
    if ((data['viewport']['width'],data['viewport']['height']) not in VIEWPORTS or
            not any(name == str(data['viewport']['width'])+'x'+str(data['viewport']['height'])+suffix for suffix in METHOD_CHILD_SCENES)):
        raise RuntimeError('Method child audit is not bound to an original method capture')
    if audit.get('binding') != method_child_binding(name, data, expected):
        raise RuntimeError('Method child proof was reused across source, claim, scene, expansion or viewport')
    path = method_visible_source_ids(expected, source_positions, data['expanded'][expected['position']['tree']])
    children = [pid for pid in path if pid in expected['children']]
    if audit.get('required') != children or [p.get('id') for p in audit.get('proofs', [])] != children:
        raise RuntimeError('Method child audit omitted, duplicated or invented a rendered source child')
    if audit['before'].get('domSame') is not True or audit['before']['active'].get('original') is not True or audit['before'].get('hoverSame') is not True:
        raise RuntimeError('Method child audit did not bind its settled original DOM focus and hover')
    check_method_child_candidates(audit['before'],audit.get('tabCandidatesBefore'))
    check_method_child_candidates(audit['after'],audit.get('tabCandidatesAfter'))
    if audit['before']['tabBound']!=min(256,audit['tabCandidatesBefore']['eligibleCount']+1):
        raise RuntimeError('Method child audit changed its original bounded native Tab budget')
    if [row['position'] for row in audit['before']['scopeCandidates']['treeTabIndexes']]!=path:
        raise RuntimeError('Method child focus candidates are not the complete source-bound method tree')
    check_method_child_state(audit['before'], audit['after'], exact=True)
    if (audit['before']['runtime']['contexts'][audit['before']['contextKey']]['expandedByTree']!=data['expanded'] or
            audit['before']['route'] != data['route'] or audit['before']['viewport'] != dict(data['viewport'], dpr=1)):
        raise RuntimeError('Method child audit does not describe the photographed source and viewport')
    if audit.get('baselineMode') != method_child_baseline_mode(audit['before']):
        raise RuntimeError('Method child audit changed its original persistence semantics')
    settles=audit.get('settles')
    if not isinstance(settles,list) or not settles or any(s.get('ok') is not True or not 160<=s.get('quietMs',-1)<=s.get('elapsed',-1)<=2000 for s in settles):
        raise RuntimeError('Method child audit lacks its bounded naturally stable state windows')
    actions=audit.get('actions',[])
    key_indexes=[k.get('actionIndex') for k in audit.get('keys',[])]
    if key_indexes!=[i for i,a in enumerate(actions) if a.get('kind')=='tree-key']:
        raise RuntimeError('Method child native keys are not bound one-to-one to actual actions')
    for key in audit.get('keys',[]):
        action=actions[key['actionIndex']];trace=key['trace'];target=key['target'];requested='Home' if key['input']=='\ue011' else 'ArrowDown' if key['input']=='\ue015' else None
        if requested is None or target not in path or (requested=='Home' and target!=path[0]):raise RuntimeError('Method child audit invented a native source traversal')
        check_method_key_trace(trace,expected['position']['id'],path[0],target,requested)
        events=[e for e in action['events']['events'] if e.get('type')=='keydown']
        if (len(events)!=1 or events[0].get('key')!=requested or events[0].get('target')!=trace['events'][0]['eventTarget'] or
                action['after']['active']['position']!=target or action['after']['roving']!=[target] or trace['after']['active']!='np-node-'+target):
            raise RuntimeError('Method key trace and actual action focus disagree')
    prior=audit['before']
    for action in actions:
        if action.get('kind') not in ('tree-key','tab','reverse-tab','pointer-move-reader','pointer-return-reader','wheel-tree','wheel-reader','restore-original-hover') or action.get('before')!=prior:
            raise RuntimeError('Method child actions are unsupported or omit an intervening state')
        if action['kind']!='tree-key' and (action['before']['roving']!=action['after']['roving'] or
                action['before']['scopeCandidates']['treeTabIndexes']!=action['after']['scopeCandidates']['treeTabIndexes']):
            raise RuntimeError('Non-tree-key method action changed its original tree roving candidates')
        check_method_child_candidates(action['before'],action.get('tabCandidatesBefore'))
        check_method_child_candidates(action['after'],action.get('tabCandidatesAfter'))
        prior=action['after']
        events=action.get('events',{}); rows=events.get('events',[])
        if events.get('overflow')!=0 or len(rows)>24 or any(e.get('trusted') is not True for e in rows):
            raise RuntimeError('Method child receipt lost bounded trusted native actions')
        check_method_child_state(audit['before'],action['after'])
        if action['kind'] in ('tree-key','tab','reverse-tab') and not any(e.get('type')=='keydown' for e in rows):
            raise RuntimeError('Method child receipt lost native keyboard input')
        if action['kind']=='pointer-return-reader' and (not action['after']['active']['original'] or
                any(not any(e.get('type')==t and e.get('readerTarget') for e in rows) for t in ('pointerdown','pointerup','click','focusin'))):
            raise RuntimeError('Method child receipt lost exact original reader pointer focus')
        if action['kind'].startswith('wheel-'):
            region=action['kind'].split('-',1)[1]
            if not any(e.get('type')=='scroll' for e in rows) or all(action['before'][region][k]==action['after'][region][k] for k in ('top','left')):
                raise RuntimeError('Method child receipt invented native scroll progress')
    if prior!=audit['after']:raise RuntimeError('Method child final state is not its actual last native action')
    for item in audit['proofs']:
        pid=item['id']; row=item['row']; original=next(r for r in data['rows'] if r['id']==pid)
        display=expected['childDisplay'][pid]
        if not display['label'] or not display['role'] or any(row[k]!=display[k] for k in ('label','role')):
            raise RuntimeError('Native child full label or role differs from its independent scientific source')
        for key in ('id','parent','domParent','entity','tree','level','ancestor','selected','label','sourceLabel','role'):
            if row[key] != original[key]:
                raise RuntimeError('Native child reveal changed its exact source label/role/parent: '+key)
        frame=item['state']; check_method_child_state(audit['before'],frame)
        if frame['active']['position']!=pid or frame['roving']!=[pid]:
            raise RuntimeError('Native child proof did not focus its exact original child')
        key=item.get('keyTrace', {})
        check_method_key_trace(key,expected['position']['id'],path[0],pid,'ArrowDown')
        matched=[k for k in audit.get('keys',[]) if k.get('trace')==key]
        if (len(matched)!=1 or actions[matched[0]['actionIndex']]['after']!=frame or key['after']['tree']['clientRect']!=frame['tree']['client'] or
                key['after']['tree']['top']!=frame['tree']['top'] or key['after']['tree']['left']!=frame['tree']['left'] or
                row['proof'].get('text')!=row['label'] or row['roleProof'].get('text')!=row['role']):
            raise RuntimeError('Child text or geometry is not bound to its actual native key frame')
        if any(not _reader_proof(row[k],frame['tree']['client'],data['viewport'],font_size=15) for k in ('proof','roleProof')):
            raise RuntimeError('Native child full label or role is clipped, covered, small or unreadable')
    if children and (not actions or not audit.get('keys')):
        raise RuntimeError('Method child proof lacks its actual native actions and geometry records')
    if audit.get('afterSnapshot')!={k:v for k,v in data.items() if k not in ('captureName','childReadability')}:
        raise RuntimeError('Method child audit lost the exact final original text, paint and geometry snapshot')


def method_child_readability_checks(driver, report, save, name, data, expected, source_positions):
    """Bounded native input only. JavaScript measures/observes; it never focuses or scrolls."""
    import copy
    record=dict(binding=method_child_binding(name,data,expected),status='started',proofs=[],actions=[],keys=[])
    report.setdefault('methodChildReadabilityChecks',[]).append(record)
    def checkpoint():
        save()
    def state():
        return driver.js(METHOD_CHILD_STATE_JS)
    def idle():
        result=driver.call('POST','/execute/async',{'script':METHOD_CHILD_IDLE_JS,'args':[]})
        record.setdefault('settles',[]).append(result); checkpoint()
        if result.get('ok') is not True: raise RuntimeError('Method child native input did not naturally settle')
    def native(kind, actions):
        before=state(); driver.js(METHOD_CHILD_ACTION_JS,'reset')
        item=dict(kind=kind,before=before,tabCandidatesBefore=driver.js(METHOD_CHILD_ACTION_JS,'candidates')); record['actions'].append(item); checkpoint()
        try:
            driver.call('POST','/actions',{'actions':actions}); idle()
        finally:
            item['events']=driver.js(METHOD_CHILD_ACTION_JS,'read'); item['after']=state(); item['tabCandidatesAfter']=driver.js(METHOD_CHILD_ACTION_JS,'candidates'); checkpoint()
        check_method_child_state(record['before'],item['after'])
        if item['events']['overflow'] or any(e['trusted'] is not True for e in item['events']['events']):
            raise RuntimeError('Method child native input lacks bounded trusted events')
        return item
    def tab(backwards=False):
        actions=([{'type':'keyDown','value':'\ue008'}] if backwards else [])+[{'type':'keyDown','value':'\ue004'},{'type':'keyUp','value':'\ue004'}]+([{'type':'keyUp','value':'\ue008'}] if backwards else [])
        item=native('reverse-tab' if backwards else 'tab',[{'type':'key','id':'method-child-focus','actions':actions}])
        if not any(e['type']=='keydown' and e['key']=='Tab' for e in item['events']['events']):raise RuntimeError('Method child focus lacked native Tab')
    def focus_roving():
        for _ in range(record['before']['tabBound']):
            now=state()
            if now['active']['position']==now['roving'][0] and now['active']['tag']=='LI':return
            tab(True)
        raise RuntimeError('Native Tab could not reach original method keyboard scope')
    def key(value,target):
        item=dict(input=value,target=target);record['keys'].append(item);checkpoint();installed=False
        try:
            item['trace']=driver.js(METHOD_KEY_TRACE_START_JS,expected['position']['id'],path[0],target,'Home' if value=='\ue011' else 'ArrowDown');installed=True
            item['actionIndex']=len(record['actions'])
            native('tree-key',[{'type':'key','id':'method-child-tree','actions':[{'type':'keyDown','value':value},{'type':'keyUp','value':value}]}])
        finally:
            if installed:item['trace']=driver.js(METHOD_KEY_TRACE_STOP_JS)
            checkpoint()
        check_method_key_trace(item['trace'],expected['position']['id'],path[0],target,'Home' if value=='\ue011' else 'ArrowDown')
        now=state()
        if now['active']['position']!=target or now['roving']!=[target]:raise RuntimeError('Method child native traversal missed source position')
        return item['trace']
    def to_position(target,no_scroll=False):
        if target not in path:raise RuntimeError('Original stored method focus is not a rendered source position')
        focus_roving();start=state()
        start_index=path.index(start['roving'][0]);target_index=path.index(target)
        # Preserve a legitimate nonzero original tree offset: replay forward
        # from the persisted ancestor rather than needlessly Home-clamping it.
        sequence=([('\ue015',p) for p in path[start_index+1:target_index+1]] if no_scroll and start_index<=target_index else
                  [('\ue011',path[0])]+[('\ue015',p) for p in path[1:target_index+1]])
        for value,pid in sequence:
            key(value,pid)
            if no_scroll and (any(state()[k]!=start[k] for k in ('tree','reader','window','history')) or
                              any(e['type']=='scroll' for e in record['actions'][-1]['events']['events'])):
                raise RuntimeError('Transient method focus return caused a forbidden persistence or scroll change')
    def wheel(region,dx,dy):
        now=state();box=now[region]['client'];x=math.floor(box['x']+box['width']/2);y=math.floor(box['y']+box['height']/2)
        item=native('wheel-'+region,[{'type':'wheel','id':'method-child-return','actions':[{'type':'scroll','origin':'viewport','x':x,'y':y,'deltaX':dx,'deltaY':dy,'duration':80}]}])
        after=item['after']
        if (dx and (after[region]['left']-now[region]['left'])*dx<=0) or (dy and (after[region]['top']-now[region]['top'])*dy<=0):
            raise RuntimeError('Method child native wheel made no effective progress')
        if not any(e['type']=='scroll' for e in item['events']['events']):raise RuntimeError('Method child return lacks actual scroll event')
    def offsets():
        for region in ('tree','reader'):
            for _ in range(4):
                now=state();target=record['before'][region]
                dx=target['left']-now[region]['left'];dy=target['top']-now[region]['top']
                if not dx and not dy:break
                if dx!=int(dx) or dy!=int(dy):raise RuntimeError('Exact original offset is not reachable with integer native wheel')
                wheel(region,int(dx),int(dy))
            else:raise RuntimeError('Bounded method child native return did not reach exact offsets')
    def pulse():
        now=state()
        for region in ('reader','tree'):
            for offset,maximum in (('top','maxTop'),('left','maxLeft')):
                if now[region][maximum]<1:continue
                delta=1 if now[region][offset]<now[region][maximum] else -1
                wheel(region,delta if offset=='left' else 0,delta if offset=='top' else 0);offsets();return
        raise RuntimeError('No actual scroll range is available for native persistence return')
    def original_focus():
        if state()['active']['original']:return
        if record['before']['originalFocus']['id']=='np-detail-scroll':
            point=driver.js(METHOD_CHILD_READER_POINT_JS);record['readerReturnPoint']=point;checkpoint()
            if not point['point']:raise RuntimeError('Original reader has no safe self-hit native pointer target')
            xy=point['point'];native('pointer-move-reader',[{'type':'pointer','id':'method-child-pointer','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','origin':'viewport','x':xy['x'],'y':xy['y'],'duration':0}]}])
            if driver.js(METHOD_CHILD_READER_POINT_JS)['point']!=xy:raise RuntimeError('Reader self-hit target moved before native click')
            item=native('pointer-return-reader',[{'type':'pointer','id':'method-child-pointer','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerDown','button':0},{'type':'pointerUp','button':0}]}])
            events=item['events']['events']
            if any(not any(e['type']==t and e['readerTarget'] for e in events) for t in ('pointerdown','pointerup','click','focusin')):raise RuntimeError('Reader native pointer return lacks trusted exact-target focus')
        elif record['before']['originalFocus']['tabIndex']>=0:
            for _ in range(record['before']['tabBound']):
                if state()['active']['original']:break
                tab()
        else:raise RuntimeError('Original non-tabstop focus has no reviewed native return path')
        if not state()['active']['original']:raise RuntimeError('Native input did not restore the original active DOM object')
    driver.js(METHOD_CHILD_PROBE_START_JS)
    try:
        idle();driver.js(METHOD_CHILD_ACTION_JS,'baseline');data.clear();data.update(driver.js(METHOD_READING_SNAPSHOT_JS));record['binding']=method_child_binding(name,data,expected)
        original_snapshot=copy.deepcopy(data)
        before=record['before']=state();record['tabCandidatesBefore']=driver.js(METHOD_CHILD_ACTION_JS,'candidates');record['baselineMode']=method_child_baseline_mode(before)
        if before['domSame'] is not True or before['active']['original'] is not True or before['hoverSame'] is not True or len(before['roving'])!=1:raise RuntimeError('Method child baseline DOM or roving focus is invalid')
        path=method_visible_source_ids(expected,source_positions,data['expanded'][expected['position']['tree']])
        if not path or len(path)>256:raise RuntimeError('Method child traversal is not within its source bound')
        record['required']=[pid for pid in path if pid in expected['children']];checkpoint()
        if record['required']:
            focus_roving();key('\ue011',path[0])
            for pid in path[1:]:
                trace=key('\ue015',pid)
                if pid in record['required']:
                    snapshot=driver.js(METHOD_READING_SNAPSHOT_JS)
                    row=next((r for r in snapshot['rows'] if r['id']==pid),None)
                    if row is None:raise RuntimeError('Method child disappeared during its native reveal')
                    record['proofs'].append(dict(id=pid,row=row,state=state(),keyTrace=trace));checkpoint()
            if record['baselineMode']=='stable-keyboard-focus-only':
                stored=before['history'][before['historyKey']]['contexts'][before['contextKey']]['focusTarget']
                to_position(stored);offsets();idle()
                if state()['history']!=before['history']:pulse()
                idle();record['persistedReturn']=state();checkpoint()
                if record['persistedReturn']['history']!=before['history']:raise RuntimeError('Method child return could not reconstruct original persisted history')
                to_position(before['roving'][0],no_scroll=True);original_focus()
            else:
                to_position(before['roving'][0]);original_focus();offsets();idle()
                if state()['runtime']!=before['runtime'] or state()['history']!=before['history']:pulse()
            if not state()['hoverSame']:
                point=driver.js(METHOD_CHILD_HOVER_POINT_JS);record['hoverReturnPoint']=point;checkpoint()
                if not point['point']:raise RuntimeError('Original hover target has no genuine pointer return point')
                xy=point['point'];native('restore-original-hover',[{'type':'pointer','id':'method-child-pointer','parameters':{'pointerType':'mouse'},'actions':[{'type':'pointerMove','origin':'viewport','x':xy['x'],'y':xy['y'],'duration':0}]}])
            idle()
        record['afterSnapshot']=driver.js(METHOD_READING_SNAPSHOT_JS)
        if record['afterSnapshot']!=original_snapshot:raise RuntimeError('Native method child audit changed original source text, geometry, paint or reader state')
        record['after']=state();record['tabCandidatesAfter']=driver.js(METHOD_CHILD_ACTION_JS,'candidates');check_method_child_state(before,record['after'],exact=True)
        record['status']='inputs_returned'
    except Exception as exc:
        record['status']='failed';record['error']=str(exc)[:2000]
        raise
    finally:
        try:
            record['cleanedUp']=driver.js(METHOD_CHILD_PROBE_STOP_JS)['cleanedUp']
        except Exception as exc:
            record['status']='failed';record['cleanupError']=str(exc)[:2000]
            raise
        finally:
            checkpoint()
    data['captureName']=name;data['childReadability']=record;record['status']='verified_native_children'
    try:
        check_method_child_audit(data,expected,source_positions)
    except Exception as exc:
        record['status']='failed';record['error']=str(exc)[:2000];data.pop('childReadability',None)
        raise
    finally:
        checkpoint()
    return record


METHOD_NAVIGATION_STATE_JS = r"""
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),tree=document.getElementById('np-tree-scroll'),reader=document.getElementById('np-detail-scroll');
return {route:s.route,originTrail:s.originTrail,historyLength:history.length,expanded:m.getBucket(s).expandedByTree,
  window:{x:scrollX,y:scrollY},treeScroll:{top:tree.scrollTop,left:tree.scrollLeft},readerScroll:{top:reader.scrollTop,left:reader.scrollLeft},
  focus:document.activeElement.id,roving:[...document.querySelectorAll('#np-tree [role=treeitem][tabindex="0"]')].map(e=>e.dataset.position),
  methodReading:document.getElementById('navigation-product').dataset.methodReading,
  siblings:[...document.querySelectorAll('#np-tree details[data-method-siblings]')].map(e=>({parent:e.dataset.methodSiblings,open:e.open}))};
"""


METHOD_KEY_TRACE_START_JS = r"""
var source=arguments[0],root=arguments[1],target=arguments[2],key=arguments[3],slot='__npMethodKeyTrace';
if(window[slot])throw Error('A method keyboard trace is already installed');
var tree=document.getElementById('np-tree-scroll'),app=document.getElementById('navigation-product');
if(!tree||app?.dataset.methodReading!=='true'||!['Home','ArrowDown'].includes(key))throw Error('Method keyboard trace lacks its exact method scope');
function rect(e){if(!e)return null;var r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
function row(id){var e=document.getElementById('np-node-'+id),r=e?.firstElementChild;if(!e||!r)return null;var cs=getComputedStyle(e),rs=getComputedStyle(r);return {id:e.id,position:e.dataset.position,rect:rect(r),itemMarginTop:parseFloat(cs.marginTop),rowScrollMarginBlockStart:rs.scrollMarginBlockStart};}
function snapshot(){var r=tree.getBoundingClientRect(),s=getComputedStyle(tree),a=window.NavigationProductApp;return {
  route:Object.assign({},a.getState().route),methodReading:app.dataset.methodReading,window:{x:scrollX,y:scrollY},active:document.activeElement?.id||null,
  tree:{id:tree.id,connected:tree.isConnected,top:tree.scrollTop,left:tree.scrollLeft,scrollHeight:tree.scrollHeight,scrollWidth:tree.scrollWidth,
    rect:rect(tree),clientRect:{x:r.x+tree.clientLeft,y:r.y+tree.clientTop,width:tree.clientWidth,height:tree.clientHeight},paddingTop:parseFloat(s.paddingTop),scrollPaddingBlockStart:s.scrollPaddingBlockStart},
  root:row(root),target:row(target)};}
var state={scope:'method-tree-key',source:source,root:root,target:target,key:key,eventLimit:2,before:snapshot(),events:[],overflow:0,after:null,cleanedUp:false};
if(!state.before.root||!state.before.target||state.before.route.node!==source)throw Error('Method keyboard trace lost an exact source row');
function observe(phase,event){if(state.events.length>=2){state.overflow=Math.min(3,state.overflow+1);return;}
  state.events.push({phase:phase,key:event.key,code:event.code,isTrusted:event.isTrusted,defaultPrevented:event.defaultPrevented,eventTarget:event.target.id||null,snapshot:snapshot()});}
function capture(event){observe('capture',event);}
function bubble(event){observe('bubble',event);}
try{tree.addEventListener('keydown',capture,true);tree.addEventListener('keydown',bubble,false);
  window[slot]={state:state,snapshot:snapshot,tree:tree,capture:capture,bubble:bubble};
}catch(e){tree.removeEventListener('keydown',capture,true);tree.removeEventListener('keydown',bubble,false);delete window[slot];throw e;}
return state;
"""

METHOD_KEY_TRACE_STOP_JS = r"""
var slot='__npMethodKeyTrace',probe=window[slot];
if(!probe)throw Error('Method keyboard trace cleanup lacks its installed probe');
try{probe.state.after=probe.snapshot();return probe.state;}
finally{probe.tree.removeEventListener('keydown',probe.capture,true);probe.tree.removeEventListener('keydown',probe.bubble,false);probe.state.cleanedUp=true;delete window[slot];}
"""


def check_method_key_trace(data, source, root, target, key):
    """Trace proves native ordering and cleanup; the existing exact-scroll gate decides restoration."""
    if (data.get('scope') != 'method-tree-key' or data.get('source') != source or data.get('root') != root or
            data.get('target') != target or data.get('key') != key or data.get('eventLimit') != 2 or
            data.get('overflow') != 0 or data.get('cleanedUp') is not True):
        raise RuntimeError('Method keyboard trace lost its bounded exact-source lifecycle')
    events = data.get('events', [])
    if len(events) != 2 or [row.get('phase') for row in events] != ['capture', 'bubble']:
        raise RuntimeError('Method keyboard trace omitted or duplicated a native keydown phase')
    for row in events:
        if row.get('key') != key or row.get('isTrusted') is not True or not row.get('eventTarget'):
            raise RuntimeError('Method keyboard trace did not observe the exact native key')
    if events[-1].get('defaultPrevented') is not True:
        raise RuntimeError('Method keyboard handler did not consume its native navigation key')
    frames = [data.get('before'), *(row.get('snapshot') for row in events), data.get('after')]
    if any(not isinstance(frame, dict) for frame in frames):
        raise RuntimeError('Method keyboard trace omitted a before, event or after snapshot')
    for frame in frames:
        tree = frame.get('tree') or {}
        if (frame.get('route') != data['before']['route'] or frame['route'].get('node') != source or
                frame.get('methodReading') != 'true' or frame.get('window') != {'x': 0, 'y': 0} or
                tree.get('id') != 'np-tree-scroll' or tree.get('connected') is not True):
            raise RuntimeError('Method keyboard trace changed its source or containing pane')
        for name, identity in (('root', root), ('target', target)):
            proof = frame.get(name) or {}
            if proof.get('id') != 'np-node-' + identity or proof.get('position') != identity or not proof.get('rect'):
                raise RuntimeError('Method keyboard trace lost a source row rectangle')
        for box in (tree.get('rect'), tree.get('clientRect'), frame['root']['rect'], frame['target']['rect']):
            if (not isinstance(box, dict) or any(type(box.get(k)) not in (int, float) or not math.isfinite(box[k]) for k in ('x', 'y', 'width', 'height')) or
                    box['width'] <= 0 or box['height'] <= 0):
                raise RuntimeError('Method keyboard trace lacks finite actual pane and row geometry')


def check_method_navigation_transition(before, after, focus=None, exact_tree_scroll=False):
    for key in ('route', 'originTrail', 'historyLength', 'expanded', 'window', 'readerScroll', 'methodReading'):
        if before[key] != after[key]:
            raise RuntimeError('Method navigation controls changed preserved source context: ' + key)
    if after['methodReading'] != 'true' or len(after['roving']) != 1:
        raise RuntimeError('Method navigation lost the actual method presentation or single keyboard tree')
    if focus is not None and (after['focus'] != 'np-node-' + focus or after['roving'] != [focus]):
        raise RuntimeError('Method keyboard traversal did not reach the exact original position')
    if exact_tree_scroll and before['treeScroll'] != after['treeScroll']:
        raise RuntimeError('Method navigation changed the exact tree scroll without leaving the source object')


def method_navigation_checks(driver, report, save, prefix, expected, source_positions):
    """Native keyboard traverses every displayed original parent edge without navigation."""
    before = driver.js(METHOD_NAVIGATION_STATE_JS)
    record = {'viewport': prefix, 'position': expected['position']['id'], 'before': before, 'steps': []}
    report.setdefault('methodNavigationChecks', []).append(record)
    save()
    path = method_visible_source_ids(expected, source_positions, before['expanded'][expected['position']['tree']])
    def key(value, target):
        element = driver.selector('[id="' + ('np-node-' + expected['position']['id'] if not record['steps'] else record['steps'][-1]['after']['focus']) + '"]')
        step = {'input': value, 'expectedFocus': target}
        record['steps'].append(step); save()
        installed = False
        try:
            step['trace'] = driver.js(METHOD_KEY_TRACE_START_JS, expected['position']['id'], path[0], target, 'Home' if value == '\ue011' else 'ArrowDown')
            installed = True
            driver.call('POST', '/element/' + element[ELEMENT] + '/value', {'text': value, 'value': [value]})
            driver.settle()
        finally:
            try:
                if installed: step['trace'] = driver.js(METHOD_KEY_TRACE_STOP_JS)
            finally:
                step['after'] = driver.js(METHOD_NAVIGATION_STATE_JS); save()
        check_method_key_trace(step['trace'], expected['position']['id'], path[0], target, 'Home' if value == '\ue011' else 'ArrowDown')
        check_method_navigation_transition(before, step['after'], target)
    key('\ue011', path[0])  # Home
    for pid in path[1:]:
        key('\ue015', pid)  # ArrowDown
    key('\ue011', path[0])
    for pid in expected['chain'][1:]:
        key('\ue015', pid)
    record['after'] = driver.js(METHOD_NAVIGATION_STATE_JS); save()
    check_method_navigation_transition(before, record['after'], expected['position']['id'], exact_tree_scroll=True)
    record['status'] = 'verified_native_keyboard'
    save()


def check_method_layout_return(before, after):
    """Return rederives the original non-method geometry before restoring offsets."""
    check_desktop_shell(before); check_desktop_shell(after)
    for key in ('route', 'methodReading', 'treePane', 'tree', 'pane', 'reader', 'offsets', 'relation'):
        if before[key] != after[key]:
            raise RuntimeError('Return from method did not restore original layout and exact effective offsets: ' + key)


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


TASK_RELATION_HISTORY_WAIT_JS = r"""
var wanted=arguments[2],current=NavigationProductApp.getState(),relation=document.querySelector('[data-selected-task-relation]');
if(window.navigation?.currentEntry?.key!==wanted.historyEntryKey||current.revision!==wanted.runtime.revision||
   (relation?relation.dataset.selectedTaskRelation:null)!==wanted.selectedRelation)return false;
""" + TASK_ROUTE_RETURN_WAIT_JS


TASK_ROUTE_DIAGNOSTIC_JS = STATIONARY_SHELL_ANCESTORS_JS + r"""
function relationReturnClickDiagnostic(){
  var nodes=document.querySelectorAll('#np-task-route-return'),button=nodes[0],reader=document.getElementById('np-detail-scroll'),
      header=reader&&document.getElementById('np-reader-heading'),tree=document.getElementById('np-tree-scroll');
  function rect(e){if(!e)return null;var r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
  function intersect(a,b){var x=Math.max(a.x,b.x),y=Math.max(a.y,b.y);return {x:x,y:y,width:Math.max(0,Math.min(a.x+a.width,b.x+b.width)-x),height:Math.max(0,Math.min(a.y+a.height,b.y+b.height)-y)};}
  function identity(e){if(!e)return null;var id=e.id||'',cls=typeof e.className==='string'?e.className:'';return {tag:e.tagName,id:id.slice(0,256)||null,className:cls.slice(0,256)||null,identityTruncated:id.length>256||cls.length>256};}
  function position(e){return e?{top:e.scrollTop,left:e.scrollLeft,clientHeight:e.clientHeight,scrollHeight:e.scrollHeight}:null;}
  var viewport={x:0,y:0,width:innerWidth,height:innerHeight},rr=rect(reader),hr=rect(header),br=rect(button),
      client=reader&&{x:rr.x+reader.clientLeft,y:rr.y+reader.clientTop,width:reader.clientWidth,height:reader.clientHeight},
      visible=client&&intersect(client,viewport),effective=visible&&Object.assign({},visible),hs=header&&getComputedStyle(header),
      headerVisible=!!(header&&hr.width>0&&hr.height>0&&hs.display!=='none'&&hs.visibility!=='hidden'&&parseFloat(hs.opacity)>0);
  if(effective&&headerVisible&&(hs.position==='sticky'||hs.position==='fixed')&&intersect(hr,visible).height>0){
    var bottom=effective.y+effective.height;effective.y=Math.max(effective.y,hr.y+hr.height);effective.height=Math.max(0,bottom-effective.y);}
  var buttonRegion=button&&header&&header.contains(button)?'fixed-heading':'reader-content',effectiveTarget=buttonRegion==='fixed-heading'&&hr?intersect(hr,viewport):effective;
  var chain=[],computedVisible=!!(button&&br.width>0&&br.height>0),n=button;
  while(n&&n.nodeType===1&&chain.length<10){var cs=getComputedStyle(n);chain.push({element:identity(n),rect:rect(n),display:cs.display,visibility:cs.visibility,opacity:cs.opacity,pointerEvents:cs.pointerEvents,overflowX:cs.overflowX,overflowY:cs.overflowY});
    if(cs.display==='none'||cs.visibility==='hidden'||cs.visibility==='collapse'||parseFloat(cs.opacity)===0)computedVisible=false;
    n=n.parentElement;}
  function contains(r,p){return !!r&&p.x>=r.x&&p.x<r.x+r.width&&p.y>=r.y&&p.y<r.y+r.height;}
  function hit(name,x,y){var point={x:x,y:y},inside=contains(viewport,point),top=inside?document.elementFromPoint(x,y):null,
      stack=inside&&typeof document.elementsFromPoint==='function'?document.elementsFromPoint(x,y).slice(0,5):[];
    return {name:name,x:x,y:y,inViewport:inside,inReader:contains(visible,point),inEffectiveReader:contains(effective,point),inEffectiveTarget:contains(effectiveTarget,point),
      hitsTarget:!!(top&&button&&(top===button||button.contains(top))),top:identity(top),stack:stack.map(identity)};}
  var points=br?[hit('center',br.x+br.width/2,br.y+br.height/2),hit('upper-left',br.x+br.width*.2,br.y+br.height*.2),
    hit('upper-right',br.x+br.width*.8,br.y+br.height*.2),hit('lower-left',br.x+br.width*.2,br.y+br.height*.8),hit('lower-right',br.x+br.width*.8,br.y+br.height*.8)]:[];
  var inView=br&&intersect(br,viewport);
  return {time:performance.now(),limitation:'Geometry reads can force layout; hit samples alone do not identify the WebDriver failure.',
    count:nodes.length,button:button?{element:identity(button),rect:br,computedVisible:computedVisible,disabled:button.disabled,hidden:button.hidden,
      clientRects:[...button.getClientRects()].slice(0,5).map(r=>({x:r.x,y:r.y,width:r.width,height:r.height}))}:null,
    viewport:viewport,reader:rr,readerClient:client,readerVisible:visible,effectiveReader:effective,buttonRegion:buttonRegion,effectiveTarget:effectiveTarget,
    sticky:header?{element:identity(header),rect:hr,position:hs.position,visible:headerVisible}:null,
    scroll:{window:{x:scrollX,y:scrollY},reader:position(reader),tree:position(tree)},ancestors:chain,ancestorLimitReached:!!n&&chain.length===10,
    points:points,inViewCenter:inView&&inView.width>0&&inView.height>0?hit('viewport-clipped-center',inView.x+inView.width/2,inView.y+inView.height/2):null};
}
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
  var runtime=stateRecord(state),persisted=stateRecord(history.state&&history.state[model.KEY]),heading=document.getElementById('np-reader-heading'),
      rr=reader.getBoundingClientRect(),hr=heading&&heading.getBoundingClientRect(),active=document.activeElement,
      focusId=model.getBucket(state).focusTarget,focus=focusId&&(document.getElementById(focusId)||document.getElementById('np-node-'+focusId));
  return {stationaryAncestors:stationaryShellAncestors(),reader:geometry(reader),readerHeading:geometry(heading),
    availableContent:{x:rr.x+reader.clientLeft,y:Math.max(rr.y+reader.clientTop,hr?hr.y+hr.height:rr.y+reader.clientTop),
      bottom:rr.y+reader.clientTop+reader.clientHeight,width:reader.clientWidth},
    activeElement:active?target(active):null,runtimeFocusTarget:{value:focusId,element:focus?target(focus):null},
    targetControls:[...new Set([...(panel?panel.querySelectorAll('[data-change-target],[data-route-method] > button'):[]),...reader.querySelectorAll('[data-change-target]')])].map(target),
    directReaderChildren:[...reader.children].map(geometry),taskOverview:geometry(panel),
    overviewBlocks:panel?[...panel.children].map(geometry):[],
    disclosures:[...reader.querySelectorAll('details')].map(e=>({id:e.id,summaryId:e.querySelector(':scope > summary')?.id,
      relation:e.dataset.taskChange||null,open:e.open,geometry:geometry(e),directChildren:[...e.children].map(geometry)})),
    textBlocks:[...reader.querySelectorAll('[data-task-route-scope] h2,[data-task-route-scope] h3,[data-task-route-scope] p,[data-task-route-scope] summary,[data-selected-task-relation] h2,[data-selected-task-relation] h3,[data-selected-task-relation] p,[data-selected-task-relation] summary')].map(textGeometry),
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
  panelScope:panel&&panel.dataset.taskRouteScope,readerHidden:document.querySelector('.np-reading-pane').hidden,canvasState:panel&&panel.dataset.taskRouteState,
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
  relationDisclosure:panel?{open:panel.open,tag:panel.tagName,id:panel.id,summary:panel.querySelector(':scope > summary')?.id,current:panel.dataset.currentRelationCount,outside:panel.dataset.outsideRelationCount,beforeTree:!!(panel.compareDocumentPosition(host)&Node.DOCUMENT_POSITION_FOLLOWING),insideTree:host.contains(panel),insideTreeScroll:tree.contains(panel),toolbar:!!panel.closest('.np-workspace-bar')}:null,
  readerLists:reader.querySelectorAll('[data-route-method],[data-route-group],[data-task-route-scope]').length,
  activeTree:host.dataset.activeTaskTree||null,treeCount:host.querySelectorAll('[role=tree]').length,forestCount:host.querySelectorAll('[data-parallel-tree]').length,
  rovingCount:host.querySelectorAll('[role=treeitem][tabindex="0"]').length,inactiveItemCount:all.filter(e=>e.dataset.tree!==s.route.tree).length,
  selected:all.filter(e=>e.getAttribute('aria-selected')==='true').map(e=>e.dataset.position),expanded:bucket.expandedByTree,taskView:m.taskView(s),relationView:bucket.relationViewByTree||{},
  runtime:s,persisted:history.state&&history.state[m.KEY],historyLength:history.length,url:location.href,
  historyEntryKey:window.navigation?.currentEntry?.key||null,
  analysisEntry:document.querySelector('#np-reader-analysis-entry [data-analysis-state]')?{state:document.querySelector('#np-reader-analysis-entry [data-analysis-state]').dataset.analysisState,paper:document.querySelector('#np-reader-analysis-entry [data-analysis-state]').dataset.analysisPaper,version:document.querySelector('#np-reader-analysis-entry [data-analysis-state]').dataset.analysisVersion}:null,
  widths:{canvas:tree.getBoundingClientRect().width,tree:host.getBoundingClientRect().width,forest:host.querySelector('[data-parallel-tree]')?.getBoundingClientRect().width||0,reader:reader.getBoundingClientRect().width}};
"""


# Same snapshot round trip and original action timing; only this transition reads hit geometry.
TASK_ROUTE_RETURN_SNAPSHOT_JS = TASK_ROUTE_SNAPSHOT_JS.replace(
    'return {route:s.route,', 'return {returnClickDiagnostic:relationReturnClickDiagnostic(),route:s.route,', 1)


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


def portable_method_proof_specs(science, position, claim):
    title = science['entities'][position['entityId']]['label']
    identity = {'position': position['id'], 'entity': position['entityId'],
                'paper': position['paperId'], 'version': position['versionId'], 'title': title}
    version = science['versions'][position['versionId']]
    meta = '具体方法 · ' + version['label'] + (' · 未固定快照' if version.get('versionStatus') == 'snapshot_not_version_pinned' else '')
    fixed = '#np-reader-object-title' + ''.join('[data-object-' + key + '=' + json.dumps(value) + ']'
        for key, value in identity.items() if key != 'title') + ' > h2'
    return [
        {'selector': '[data-mechanism-entity="' + position['entityId'] + '"] > h3',
         'text': title + ' · 方法内部结构', 'renderedText': '方法内部结构', 'methodIdentity': identity},
        {'selector': '[data-method-claim="' + claim['id'] + '"] > p:first-child', 'text': claim['statement']},
        {'selector': fixed, 'text': title, 'region': 'heading'},
        {'selector': '#np-reader-object-meta', 'text': meta, 'region': 'heading'},
    ]


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


def task_route_origin_overview(before, origin, source_roots):
    """Prove only saveCurrent's absent-current -> explicit closed materialization."""
    same = lambda a, b: json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    if not isinstance(origin, dict) or not same(origin.get('route'), before['route']):
        raise RuntimeError('Method origin overview lost its complete original route')
    prior = before['relationOverview']
    actual = origin.get('bucket', {}).get('relationOverviewByTree', {})
    if not isinstance(prior, dict) or not isinstance(actual, dict):
        raise RuntimeError('Method origin overview is not an exact per-tree map')
    if same(prior, actual):
        return json.loads(json.dumps(prior))
    route, position, dom = before['route'], before.get('position'), before.get('relationDisclosure')
    tree = route['tree']
    roots = [p for p in source_roots if p['id'] == route['node']]
    root = roots[0] if len(roots) == 1 else None
    identity = ({'id': root['id'], 'entity': root['entityId'], 'scope': root['scopeId'], 'tree': root['tree'],
                 'paper': root['paperId'], 'version': root['versionId'], 'kind': root['kind']} if root else None)
    if (tree not in ('l', 'c') or tree in prior or root is None or root['parentId'] is not None or
            root['scopeId'] != route['scope'] or root['tree'] != tree or
            root['paperId'] != route['paper'] or root['versionId'] != route['version'] or
            set(route) != {'nav', 'scope', 'tree', 'node', 'paper', 'version', 'bench', 'protocol', 'template', 'claim', 'mode'} or
            any(route[k] is not None for k in ('paper', 'version', 'template', 'claim')) or
            not same(position, identity) or before['panelScope'] != route['scope'] or before['selectedRelation'] is not None or
            not isinstance(dom, dict) or dom.get('tag') != 'DETAILS' or dom.get('id') != 'np-task-route-relations' or
            dom.get('summary') != 'np-task-route-relations-summary' or dom.get('open') is not False or
            dom.get('insideTree') is not False or dom.get('insideTreeScroll') is not False or dom.get('toolbar') is not True):
        raise RuntimeError('Method origin overview is not a missing current closed task-root default')
    expected = json.loads(json.dumps(prior))
    expected[tree] = {'route': json.loads(json.dumps(route)), 'open': False}
    if not same(expected, actual):
        raise RuntimeError('Method origin overview changed a strict route, open flag or existing tree field')
    return expected


def check_task_route_return(before, after, expected_control):
    expected_overview = before['relationOverview']
    if 'expectedOverviewMaterialization' in before:
        proof = before['expectedOverviewMaterialization']
        expected_overview = task_route_origin_overview(before, before['actualOrigin'], proof['sourceRoots'])
        if (json.dumps(expected_overview, sort_keys=True) != json.dumps(proof['overview'], sort_keys=True) or
                json.dumps(before['relationDisclosure'], sort_keys=True) != json.dumps(after['relationDisclosure'], sort_keys=True)):
            raise RuntimeError('Task-route return lost its proven closed overview materialization')
    if after['window'] != {'x': 0, 'y': 0}:
        raise RuntimeError('Task-route return retained forbidden ready-desktop outer scroll')
    for key in ('route', 'panelScope', 'scale', 'readerScroll', 'treeScroll', 'selectedRelation', 'expanded', 'relationOverview'):
        expected = expected_overview if key == 'relationOverview' else before[key]
        changed = (json.dumps(expected, sort_keys=True) != json.dumps(after[key], sort_keys=True)) if key == 'relationOverview' else expected != after[key]
        if changed:
            raise RuntimeError('Task-route return lost saved context: ' + key)
    if before['activatedControl'] != expected_control or after['focus'] != expected_control:
        raise RuntimeError('Task-route return lost the exact activated control focus')


def transition_record(driver, record, save, kind, action, ready=None):
    """Save before/after even on action failure; never replace the original error."""
    snapshot_script = TASK_ROUTE_RETURN_SNAPSHOT_JS if kind == 'relation-to-task' else TASK_ROUTE_SNAPSHOT_JS
    phase = {'kind': kind, 'before': driver.js(snapshot_script)}
    record.setdefault('transitions', []).append(phase)
    save()
    completed = False
    try:
        action()
        if ready:
            wait_for(ready)
        driver.settle()
        completed = True
    except Exception as exc:
        if isinstance(exc, urllib.error.HTTPError) and hasattr(exc, 'navigation_webdriver_diagnostic'):
            phase['webdriverError'] = exc.navigation_webdriver_diagnostic
        raise
    finally:
        diagnostic_error = None
        for name, script in (('after', snapshot_script), ('origin', 'var trail=NavigationProductApp.getState().originTrail;return trail[trail.length-1]')):
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


# Diagnostic instrumentation only. Geometry reads can force layout and therefore
# perturb browser scroll anchoring; they are not evidence of an unobserved run.
COLD_GEOMETRY_PROBE_JS = r"""
(function(){
'use strict';
var name='__captureColdGeometryProbe',events=[],bytes=0,seq=0,frames=0,raf=null,observer=null,stopped=false,truncated=false,
    limits={events:128,bytes:65536,frames:8},restorers=[],capabilities={},errors=[],last=null;
function err(stage,error){if(errors.length<8)errors.push({stage:stage,name:error&&error.name||'Error'});}
function safely(fn){try{fn();}catch(e){err('observation',e);}}
function element(id){return document.getElementById(id);}
function inside(node){try{return !!(node&&node.nodeType===1&&node.closest('#navigation-product'));}catch(_){return false;}}
function identity(node){return node&&node.nodeType===1?{id:(node.id||'').slice(0,180),tag:node.tagName}:null;}
function box(node){if(!node)return null;var r=node.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
function scroll(node){return node?{top:node.scrollTop,left:node.scrollLeft,height:node.scrollHeight,client:node.clientHeight,rect:box(node)}:null;}
function geometry(){var tree=element('np-tree-scroll'),reader=element('np-detail-scroll'),canvas=element('np-task-route-canvas'),
    relation=document.querySelector('#np-reader-summary [data-selected-task-relation]'),selected=document.querySelector('#np-tree [aria-selected="true"]');
  return {tree:scroll(tree),reader:scroll(reader),canvas:box(canvas),relation:relation?{id:relation.dataset.selectedTaskRelation,rect:box(relation)}:null,
    selected:selected?{id:selected.dataset.position,rect:box(selected)}:null,active:inside(document.activeElement)?identity(document.activeElement):null};}
function stack(){var page=location.pathname,allowPage=/^\/research\/navigation\/(?:index\.html)?$/.test(page);
  return (new Error().stack||'').split('\n').map(function(line){var m=line.match(/^\s*at (?:(.*?) \()?((?:https?):\/\/[^\s)]+):(\d+):(\d+)\)?$/);if(!m)return null;
    try{var url=new URL(m[2]);if(url.origin!==location.origin||!((allowPage&&url.pathname===page)||url.pathname==='/assets/navigation-product.js'))return null;
      return 'at '+(m[1]?m[1].replace(/[^\w.$ <>\[\]-]/g,'?').slice(0,80)+' ':'')+url.pathname+':'+m[3]+':'+m[4];
    }catch(_){return null;}}).filter(Boolean).slice(0,6);}
function record(kind,extra){if(stopped||truncated)return;try{var row={seq:++seq,time:performance.now(),kind:kind,geometry:geometry()};
  if(extra)Object.assign(row,extra);var size=new TextEncoder().encode(JSON.stringify(row)).byteLength;
  if(events.length>=limits.events||bytes+size>limits.bytes){truncated=true;return;}
  events.push(row);bytes+=size;last={seq:row.seq,time:row.time,geometry:row.geometry};
}catch(e){err('record',e);}}
function frame(){if(stopped||truncated||raf!==null||frames>=limits.frames)return;raf=requestAnimationFrame(function(time){raf=null;frames++;record('animation-frame',{frameTime:time,frame:frames});});}
function observeCall(kind,target,args,call){var watch=!stopped&&!truncated&&inside(target);
  if(watch)safely(function(){record(kind+'-before',{target:identity(target),argumentCount:args.length,stack:stack()});});
  try{return call();}finally{if(watch)safely(function(){record(kind+'-after',{target:identity(target)});frame();});}}
function wrapMethod(proto,key){var descriptor=Object.getOwnPropertyDescriptor(proto,key);if(!descriptor||typeof descriptor.value!=='function'){capabilities[key]=false;return;}
  var original=descriptor.value,wrapper=function(){var target=this,args=arguments;return observeCall(key,target,args,function(){return Reflect.apply(original,target,args);});};
  Object.defineProperty(proto,key,Object.assign({},descriptor,{value:wrapper}));capabilities[key]=true;
  restorers.push(function(){if(Object.getOwnPropertyDescriptor(proto,key)?.value!==wrapper)throw Error('Changed method descriptor');Object.defineProperty(proto,key,descriptor);});}
function install(){
  var proto=Element.prototype,descriptor;while(proto&&!(descriptor=Object.getOwnPropertyDescriptor(proto,'scrollTop')))proto=Object.getPrototypeOf(proto);
  if(proto&&descriptor&&descriptor.set){var original=descriptor.set,wrapper=function(value){var target=this,args=arguments,watch=!stopped&&!truncated&&target===element('np-tree-scroll');
      if(watch)safely(function(){record('tree-scrollTop-before',{value:typeof value==='number'&&Number.isFinite(value)?value:null,valueType:typeof value,stack:stack()});});
      try{return Reflect.apply(original,target,args);}finally{if(watch)safely(function(){record('tree-scrollTop-after');frame();});}};
    Object.defineProperty(proto,'scrollTop',Object.assign({},descriptor,{set:wrapper}));capabilities.scrollTop=true;
    restorers.push(function(){if(Object.getOwnPropertyDescriptor(proto,'scrollTop')?.set!==wrapper)throw Error('Changed scroll descriptor');Object.defineProperty(proto,'scrollTop',descriptor);});
  }else capabilities.scrollTop=false;
  wrapMethod(HTMLElement.prototype,'focus');wrapMethod(Element.prototype,'scrollIntoView');
  observer=new MutationObserver(function(records){safely(function(){if(stopped||truncated)return;var relevant=records.some(function(m){return inside(m.target)||[...m.addedNodes,...m.removedNodes].some(function(n){return n.nodeType===1&&(n.id==='navigation-product'||inside(n));});});
    if(relevant){var previous=last;record('ui-dom-observed',{mutationCount:records.length,lastObserved:previous,preMeaning:'previous observation, not synchronous install-before'});frame();}});});
  observer.observe(document,{childList:true,subtree:true,attributes:true,attributeFilter:['open','hidden','aria-selected','data-selected-task-relation','data-relation-state']});
  document.addEventListener('scroll',onScroll,true);
}
function onScroll(event){safely(function(){if(event.target===element('np-tree-scroll')||event.target===element('np-detail-scroll')){record('scroll-event',{target:identity(event.target),trusted:event.isTrusted});frame();}});}
function offsets(){return {window:[window.scrollX,window.scrollY],panes:['np-tree-scroll','np-detail-scroll'].map(function(id){var e=element(id);return e?[e.scrollTop,e.scrollLeft]:null;})};}
function liveState(){return JSON.stringify({history:history.state,url:location.href,length:history.length,entry:window.navigation?.currentEntry?.key||null,
  model:window.NavigationProductApp?NavigationProductApp.getState():null});}
function stop(){if(stopped)return null;stopped=true;var cleanup={descriptors:true,observer:true,listener:true,raf:true,container:true,integrityObserver:true,
    liveStateUnchanged:false,domUnchanged:false,focusUnchanged:false,scrollUnchanged:false},guard=null,guardStarted=false,baseline=null,active=null,scrollBefore=null;
  try{active=document.activeElement;scrollBefore=JSON.stringify(offsets());baseline=liveState();guard=new MutationObserver(function(){});var root=element('navigation-product');if(root){guard.observe(root,{subtree:true,childList:true,attributes:true,characterData:true});guardStarted=true;}}catch(e){err('cleanup-baseline',e);} 
  try{if(observer)observer.disconnect();}catch(e){cleanup.observer=false;err('disconnect',e);}
  try{document.removeEventListener('scroll',onScroll,true);}catch(e){cleanup.listener=false;err('remove-listener',e);}
  try{if(raf!==null)cancelAnimationFrame(raf);raf=null;}catch(e){cleanup.raf=false;err('cancel-frame',e);}
  restorers.reverse().forEach(function(restore){try{restore();}catch(e){cleanup.descriptors=false;err('restore-descriptor',e);}});
  try{delete window[name];}catch(e){cleanup.container=false;err('remove-container',e);}
  try{cleanup.liveStateUnchanged=baseline!==null&&baseline===liveState();cleanup.domUnchanged=guardStarted&&guard.takeRecords().length===0;
    cleanup.focusUnchanged=active!==null&&document.activeElement===active;cleanup.scrollUnchanged=scrollBefore!==null&&JSON.stringify(offsets())===scrollBefore;
  }catch(e){err('cleanup-integrity',e);}finally{try{if(guard)guard.disconnect();}catch(e){cleanup.integrityObserver=false;err('cleanup-integrity-observer',e);}}
  return {schema:1,limits:limits,eventBytes:bytes,truncated:truncated,events:events,capabilities:capabilities,errors:errors,cleanup:cleanup,
    privateEpoch:{available:false,reason:'Controller epochs are private closures; no product debug API is added.'},
    limitations:['Geometry reads may force layout and affect browser scroll anchoring or timing.','Mutation observations occur after DOM work; lastObserved is not a synchronous install-before sample.','No causal attribution to browser anchoring follows from an unpaired scroll event.']};
}
Object.defineProperty(window,name,{value:{stop:stop},configurable:true});
try{install();record('probe-installed');}catch(e){err('install',e);}
})();
"""

COLD_GEOMETRY_STOP_JS = "return window.__captureColdGeometryProbe ? window.__captureColdGeometryProbe.stop() : null;"
COLD_GEOMETRY_ABSENT_JS = "return !('__captureColdGeometryProbe' in window);"


def cold_relation_refresh(driver, record, save, ready):
    """Observe only this cold refresh; preserve native calls and original errors."""
    diagnostic = {'scope': 'cold-selected-relation', 'instrumented': True,
                  'limitation': 'Synchronous geometry reads can affect layout, anchoring and timing.'}
    record['coldGeometryDiagnostic'] = diagnostic
    save()
    identifier, completed, diagnostic_error = None, False, None
    try:
        result = driver.cdp('Page.addScriptToEvaluateOnNewDocument', {'source': COLD_GEOMETRY_PROBE_JS})
        identifier = result['identifier']
        phase = transition_record(driver, record, save, 'cold-selected-relation',
                                  lambda: driver.call('POST', '/refresh', {}), ready)
        completed = True
        return phase
    finally:
        # Remove current-document hooks as well as the script for future documents.
        for name, action in (('observation', lambda: driver.js(COLD_GEOMETRY_STOP_JS)),
                             ('removeScript', lambda: driver.cdp('Page.removeScriptToEvaluateOnNewDocument', {'identifier': identifier}) if identifier else None)):
            try:
                diagnostic[name] = action()
                if name == 'removeScript' and identifier:
                    diagnostic['futureScriptRemoved'] = True
            except Exception as exc:
                diagnostic[name + 'Error'] = str(exc)[:2000]
                diagnostic_error = diagnostic_error or exc
        observation = diagnostic.get('observation')
        if completed and (not observation or not all(observation.get('cleanup', {}).get(k) is True for k in ('descriptors', 'observer', 'listener', 'raf', 'container', 'integrityObserver', 'liveStateUnchanged', 'domUnchanged', 'focusUnchanged', 'scrollUnchanged'))):
            diagnostic['cleanupIncomplete'] = True
            diagnostic_error = diagnostic_error or RuntimeError('Cold geometry diagnostic did not fully clean up the current document')
        try:
            save()
        except Exception as exc:
            diagnostic['saveError'] = str(exc)[:2000]
            diagnostic_error = diagnostic_error or exc
        if completed and diagnostic_error:
            raise diagnostic_error


def cold_relation_refresh_comparison(driver, record, save, expected, ready):
    """Retain the same strict gate on instrumented and then uninstrumented refresh."""
    observed = cold_relation_refresh(driver, record, save, ready)
    check_exploration_restore(expected, observed['after'])
    clearance = {'currentProbeAbsent': driver.js(COLD_GEOMETRY_ABSENT_JS),
                 'futureScriptRemoved': record['coldGeometryDiagnostic'].get('futureScriptRemoved') is True}
    record['coldGeometryDiagnostic']['nativeComparisonClearance'] = clearance
    save()
    if not all(value is True for value in clearance.values()):
        raise RuntimeError('Cold refresh comparison still has diagnostic hooks registered')
    # cold_relation_refresh asserts current-page cleanup and removes the early
    # script before this original refresh path. No probe is registered again.
    native = transition_record(driver, record, save, 'cold-selected-relation-uninstrumented',
                               lambda: driver.call('POST', '/refresh', {}), ready)
    check_exploration_restore(expected, native['after'])
    return native


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
    if after['window'] != {'x': 0, 'y': 0}:
        raise RuntimeError('Exploration restore retained forbidden ready-desktop outer scroll')
    for key in ('route', 'selectedRelation', 'expanded', 'treeScroll', 'readerScroll', 'relationOverview', 'relationView', 'scale'):
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
        source_contexts = (inactive_before or before)['runtime']['contexts']
        preserved_keys = set(source_contexts) - {key, neutral}
        if set(after['runtime']['contexts']) - {key, neutral} != preserved_keys or any(
                after['runtime']['contexts'][saved] != source_contexts[saved] for saved in preserved_keys):
            raise RuntimeError('Desktop restore erased or rewrote an unrelated saved context bucket')
        other = 'c' if tree == 'l' else 'l'
        inactive = (inactive_before or before)['taskView']
        if inactive and any(view[field][other] != inactive[field][other] for field in ('lastRouteByTree', 'focusTargetByTree')):
            raise RuntimeError('Current view restore overwrote the inactive tree route or focus pointer')


def check_relation_history_entry(before, selected):
    """Length alone cannot prove pushState when the browser trims old entries."""
    for state in (before, selected):
        if (not isinstance(state.get('historyEntryKey'), str) or not state['historyEntryKey'] or
                type(state['runtime']['revision']) is not int or
                type(state['persisted']['revision']) is not int or
                type(state['historyLength']) is not int or state['historyLength'] < 1 or
                state['persisted']['revision'] != state['runtime']['revision'] or
                state['runtime']['route'] != state['route'] or state['persisted']['route'] != state['route']):
            raise RuntimeError('Relation history entry lacks an exact native key, revision or persisted route')
    if (selected['route'] != before['route'] or before['selectedRelation'] is not None or
            selected['selectedRelation'] != 'methods:relation:90' or
            selected['focus'] != 'np-task-relation-title' or
            selected['historyEntryKey'] == before['historyEntryKey'] or
            selected['runtime']['revision'] != before['runtime']['revision'] + 1 or
            selected['historyLength'] not in (before['historyLength'], before['historyLength'] + 1)):
        raise RuntimeError('Relation selection changed science or replaced its presentation history entry')
    other = 'c' if before['route']['tree'] == 'l' else 'l'
    if any(before['taskView'][field][other] != selected['taskView'][field][other]
           for field in ('lastRouteByTree', 'focusTargetByTree')):
        raise RuntimeError('Relation selection changed the inactive tree route or focus pointer')
    for name in ('runtime', 'persisted'):
        if before[name]['originTrail'] != selected[name]['originTrail']:
            raise RuntimeError('Relation selection changed the original origin trail')


def check_relation_history_restore(expected, restored, focus, history_length):
    if (type(restored['runtime']['revision']) is not int or type(restored['persisted']['revision']) is not int or
            restored['historyEntryKey'] != expected['historyEntryKey'] or
            restored['runtime']['revision'] != expected['runtime']['revision'] or
            restored['persisted']['revision'] != expected['runtime']['revision'] or
            restored['historyLength'] != history_length):
        raise RuntimeError('Relation history traversal did not restore the exact entry and revision')
    check_exploration_restore(expected, restored, focus=focus)
    if restored['relationDisclosure'] != expected['relationDisclosure']:
        raise RuntimeError('Relation history traversal changed the actual relationship disclosure')
    for name in ('runtime', 'persisted'):
        if restored[name]['originTrail'] != expected[name]['originTrail']:
            raise RuntimeError('Relation history traversal changed the original origin trail')


def relation_history_checks(driver, record, save, before, selected):
    """Prove two real browser entries before continuing the selected relation."""
    check_relation_history_entry(before, selected)
    control = 'np-task-change-' + before['route']['scope'] + '-methods:relation:90'
    for direction, expected, focus in (('back', before, control), ('forward', selected, selected['focus'])):
        phase = transition_record(driver, record, save, 'browser-' + direction + '-relation-selection',
            lambda d=direction: driver.call('POST', '/' + d, {}),
            lambda e=expected, f=focus: driver.js(TASK_RELATION_HISTORY_WAIT_JS, e['route'], f, e))
        check_relation_history_restore(expected, phase['after'], focus, selected['historyLength'])


TASK_OVERVIEW_RETURN_WAIT_JS = r"""
var disclosure=document.getElementById('np-task-route-relations');
if(!disclosure||disclosure.open||document.querySelector('[data-selected-task-relation]'))return false;
""" + TASK_ROUTE_RETURN_WAIT_JS


def task_return_state_with_focus(state, route, focus):
    """Only the native clicked control changes focus in the saved predecessor."""
    result = json.loads(json.dumps(state))
    key = json.dumps([route.get(k) for k in ('scope', 'bench', 'protocol', 'paper', 'version', 'template')], separators=(',', ':'), ensure_ascii=False)
    neutral = json.dumps([route.get(k) for k in ('scope', 'bench', 'protocol')] + [None, None, None], separators=(',', ':'), ensure_ascii=False)
    result['contexts'][key]['focusTarget'] = focus
    result['contexts'][neutral]['taskView']['focusTargetByTree'][route['tree']] = focus
    return result


def check_task_overview_return(before, after):
    """Permit only the explicit relationship-to-overview presentation change."""
    same = lambda a, b: json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    tree = before['route']['tree']
    if tree not in ('l', 'c') or before['selectedRelation'] != 'methods:relation:90':
        raise RuntimeError('Overview return did not begin at the selected relation')
    for value in (before, after):
        if (not isinstance(value['historyEntryKey'], str) or not value['historyEntryKey'] or
                type(value['historyLength']) is not int or value['historyLength'] < 1 or
                any(type(value[name]['revision']) is not int for name in ('runtime', 'persisted')) or
                any(not same(value[name]['route'], value['route']) for name in ('runtime', 'persisted')) or
                value['runtime']['revision'] != value['persisted']['revision']):
            raise RuntimeError('Overview return lacks exact native history entry and revision')
    if (before['historyEntryKey'] == after['historyEntryKey'] or
            after['historyLength'] not in (before['historyLength'], before['historyLength'] + 1)):
        raise RuntimeError('Overview return replaced its browser history entry')
    for key in ('route', 'position', 'expanded', 'selected', 'window', 'scale', 'readerHidden'):
        if not same(before[key], after[key]):
            raise RuntimeError('Overview return changed preserved ' + key)
    if (after['selectedRelation'] is not None or after['focus'] != 'np-task-route-relations-summary' or
            after['relationDisclosure']['open'] is not False or after['readerLists'] != 0 or
            after['readerHidden'] is not False or
            any(type(after['treeScroll'][axis]) not in (int, float) or after['treeScroll'][axis] != 0 for axis in ('top', 'left')) or
            type(after['readerScroll']['top']) not in (int, float) or after['readerScroll']['top'] != 0 or
            after['readerScroll']['left'] != before['readerScroll']['left']):
        raise RuntimeError('Overview return did not expose the collapsed task at its summary')
    overview = json.loads(json.dumps(before['relationOverview']))
    overview[tree] = {'route': before['route'], 'open': False}
    view = json.loads(json.dumps(before['relationView'])); view[tree] = None
    disclosure = dict(before['relationDisclosure'], open=False)
    for expected, actual in ((overview, after['relationOverview']), (view, after['relationView']), (disclosure, after['relationDisclosure'])):
        if not same(expected, actual):
            raise RuntimeError('Overview return changed unrelated relation presentation')
    key = json.dumps([before['route'].get(k) for k in ('scope', 'bench', 'protocol', 'paper', 'version', 'template')], separators=(',', ':'), ensure_ascii=False)
    for name in ('runtime', 'persisted'):
        expected = task_return_state_with_focus(before[name], before['route'], after['focus'])
        expected['revision'] += 1
        bucket = expected['contexts'][key]
        bucket['relationViewByTree'][tree] = None
        bucket['relationOverviewByTree'][tree] = {'route': before['route'], 'open': False}
        bucket['treeScrollByTree'][tree] = 0
        bucket['treeScrollLeftByTree'][tree] = 0
        bucket['detailScrollByTree'][tree] = 0
        if not same(expected, after[name]):
            raise RuntimeError('Overview return changed unrelated ' + name + ' state or a strict field type')
    check_exploration_restore(after, after, inactive_before=before)


def task_overview_history_checks(driver, record, save, before, collapsed):
    """Explicit return collapses; browser traversal restores each exact presentation."""
    check_task_overview_return(before, collapsed)
    for direction, expected, focus in (('back', before, 'np-task-route-return'),
                                       ('forward', collapsed, 'np-task-route-relations-summary')):
        phase = transition_record(driver, record, save, 'browser-' + direction + '-task-overview-return',
            lambda d=direction: driver.call('POST', '/' + d, {}),
            lambda e=expected, f=focus: driver.js(TASK_RELATION_HISTORY_WAIT_JS, e['route'], f, e))
        restored = phase['after']
        check_relation_history_restore(expected, restored, focus, collapsed['historyLength'])
        for name in ('runtime', 'persisted'):
            wanted = task_return_state_with_focus(expected[name], expected['route'], focus)
            if json.dumps(wanted, sort_keys=True) != json.dumps(restored[name], sort_keys=True):
                raise RuntimeError('Overview history traversal changed exact ' + name + ' state')


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
            # Fixed title/version proofs stay visible independently of reader scrolling.
            scrolling_specs = [spec for spec in specs if spec.get('region') not in ('heading', 'analysis-entry')]
            if scroll and scrolling_specs:
                reveal_control(driver, scrolling_specs[0])
                for _ in range(4):
                    boxes = [proof(spec) for spec in scrolling_specs]
                    # Align only the photographed text that belongs to the scrolling region.
                    area = boxes[0]['readerContent']
                    top, bottom = min(b['rect']['y'] for b in boxes), max(b['rect']['y'] + b['rect']['height'] for b in boxes)
                    if top >= area['y'] and bottom <= area['y'] + area['height']:
                        break
                    delta = round((top + bottom - 2 * area['y'] - area['height']) / 2)
                    if bottom - top > area['height'] or not delta:
                        break
                    region = '#np-tree-scroll' if scrolling_specs[0].get('region') == 'canvas' else '#np-detail-scroll'
                    alignment = {'region': region, 'delta': delta, 'before': driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)}
                    item.setdefault('alignmentScrollMetrics', []).append(alignment)
                    save()
                    transition_record(driver, record, save, 'align-selected-object-with-wheel', lambda: driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 'selected-object-scroll', 'actions': [{'type': 'scroll', 'origin': driver.selector(region), 'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': delta, 'duration': 100}]}]}))
                    alignment['after'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
                    save()
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
        before['desktopShell'] = desktop_chrome_snapshot(driver, report, save, prefix + '-method-origin', DESKTOP_SHELL_SNAPSHOT_JS)
        before['activatedControl'] = driver.js("return arguments[0].id||arguments[0].closest('[role=treeitem]').id;", element)
        before['originFocusTarget'] = driver.js("return arguments[0].closest('[data-position]')?.dataset.position||arguments[0].id;", element)
        phase = transition_record(driver, record, save, 'select-exact-method', lambda: driver.click(element),
            lambda: driver.js("var a=NavigationProductApp,p=arguments[0],r=a.getState().route,m=document.querySelector('[data-mechanism-entity]');return r.node===p.id&&r.scope===p.scopeId&&r.tree===p.tree&&r.paper===p.paperId&&r.version===p.versionId&&a.getContent().ready(p.entityId)&&m?.dataset.mechanismEntity===p.entityId;", position))
        phase['desktopShellBefore'] = before['desktopShell']
        save()
        origin = phase['origin']
        if not origin or origin['route'] != before['route'] or origin['bucket']['focusTarget'] != before['originFocusTarget']:
            raise RuntimeError('Method click lost its exact original route/control')
        roots = [science['positions'][pid] for pid in science['forests'][before['route']['scope']].get(before['route']['tree'], [])]
        proposal = json.loads(json.dumps(before['relationOverview']))
        tree = before['route']['tree']
        if tree not in proposal:
            proposal[tree] = {'route': before['route'], 'open': False}
        phase['overviewMaterialization'] = {'reason': 'verify missing current closed task-root default or exact existing map',
            'currentTree': tree, 'beforeOverview': before['relationOverview'], 'expectedOverview': proposal,
            'actualOriginOverview': origin['bucket'].get('relationOverviewByTree', {}), 'sourceRoots': roots, 'validated': False}
        save()
        overview = task_route_origin_overview(before, origin, roots)
        phase['overviewMaterialization']['expectedOverview'] = overview
        phase['overviewMaterialization']['validated'] = True
        if overview != before['relationOverview']:
            before['expectedOverviewMaterialization'] = {'overview': overview, 'sourceRoots': roots}
            before['actualOrigin'] = origin
        save()
        return before

    def return_method(before):
        phase = transition_record(driver, record, save, 'explicit-return-method-origin', lambda: driver.click(driver.selector('.np-return-previous')),
            lambda: driver.js(TASK_ROUTE_RETURN_WAIT_JS, before['route'], before['activatedControl']))
        check_task_route_return(before, phase['after'], before['activatedControl'])
        phase['desktopShellAfter'] = desktop_chrome_snapshot(driver, report, save, prefix + '-method-return', DESKTOP_SHELL_SNAPSHOT_JS)
        save()
        check_method_layout_return(before['desktopShell'], phase['desktopShellAfter'])

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
    relation_history_checks(driver, record, save, before_relation, phase['after'])
    rel = '[data-selected-task-relation="methods:relation:90"]'
    claim = expected['claim']
    cs = rel + ' [data-task-change-claim="' + claim['id'] + '"]'
    specs = [{'selector': cs + ' .np-change-claim', 'text': claim['statement']},
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
    cold_relation_refresh_comparison(driver, record, save, restored_relation,
        lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
    returned = transition_record(driver, record, save, 'relation-to-task', lambda: driver.click(driver.selector('#np-task-route-return')),
        lambda: driver.js(TASK_OVERVIEW_RETURN_WAIT_JS, restored_relation['route'], 'np-task-route-relations-summary'))
    check_task_overview_return(returned['before'], returned['after'])
    scene('-26-return-objectnav-task', [{'selector': '#np-task-route-relations-summary', 'region': 'toolbar'},
        {'selector': tree_label_selector(restored_relation['route']['node']), 'region': 'canvas',
         'text': science['positions'][restored_relation['route']['node']]['label']}], scroll=False)
    task_overview_history_checks(driver, record, save, returned['before'], returned['after'])
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
            set_context_ancestry_open(driver, True)
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
              portable_method_proof_specs(science, p, claim), method=p)
        return_method(before)
    if server is not None:
        for interrupt in ('none', 'wheel', 'scope'):
            open_scope(poni['scopeId'])
            transition_record(driver, record, save, 'open-delayed-relation-disclosure', lambda: driver.click(driver.selector('#np-task-route-relations-summary')))
            transition_record(driver, record, save, 'select-delayed-relation', lambda: driver.click(reveal_control(driver, {'selector': selector})),
                lambda: driver.js("return document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
            if interrupt == 'wheel':
                prepare_scroll_fixture(driver, record, save, 'tree')
            packet = driver.js('return NavigationProductApp.getBundle().delivery.packets[arguments[0]]', poni['entityId'])
            delayed = {'interrupt': interrupt, 'before': snapshot(), 'packetSha256': packet['sha256'],
                       'resourceBefore': driver.js(DELAYED_PACKET_DIAGNOSTIC_JS, packet['sha256'], poni['entityId'])}
            record.setdefault('delayedRestore', []).append(delayed)
            save()
            completed = False
            with PacketHold(server, '/research/navigation/content/' + packet['sha256'] + '.json', dist, packet['sha256']) as hold, DelayedRequestCacheControl(driver, delayed, save, hold):
                try:
                    delayed['stage'] = 'native-refresh'
                    hold.note('refresh-start')
                    driver.call('POST', '/refresh', {})
                    hold.note('refresh-return')
                    delayed['stage'] = 'waiting-for-server-request'
                    wait_for(lambda: hold.seen.is_set(), timeout=5)
                    hold.note('seen-confirmed')
                    delayed['stage'] = 'waiting-for-relation-loading'
                    wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-relation-state]')?.dataset.relationState==='loading'"), timeout=5)
                    hold.note('loading-confirmed')
                    delayed['stage'] = 'pending-user-action'
                    delayed['pending'] = snapshot()
                    save()
                    if interrupt == 'wheel':
                        delayed['pendingScrollMetrics'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
                        save()
                        check_scroll_metrics(delayed['pendingScrollMetrics']['tree'], headroom=True)
                        driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 'newer-reader-input', 'actions': [{'type': 'scroll', 'origin': driver.selector('#np-tree-scroll'), 'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': 160, 'duration': 80}]}]})
                        driver.settle()
                        delayed['newer'] = snapshot()
                        delayed['newerScrollMetrics'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
                        save()
                        check_native_wheel_progress(delayed['pendingScrollMetrics'], delayed['newerScrollMetrics'], 'tree')
                        if delayed['newer']['treeScroll'] == delayed['pending']['treeScroll']:
                            raise RuntimeError('Interrupted cold restore was not exercised by an actual scroll')
                    elif interrupt == 'scope':
                        driver.click(driver.selector('[data-tree-tab="g"]'))
                        wait_for(lambda: driver.js('return !document.getElementById("np-reading-landing").hidden'))
                        driver.click(driver.selector('[data-task-open="task:imagenav"]'))
                        wait_for(lambda: driver.js("return NavigationProductApp.getState().route.scope==='task:imagenav'&&document.querySelector('[data-task-route-state=ready]')"))
                        driver.settle()
                        delayed['newer'] = snapshot()
                    hold.note('planned-release')
                    hold.released.set()
                    delayed['stage'] = 'waiting-for-ready-after-release'
                    wait_for(lambda: driver.js('return NavigationProductApp.getContent().ready(arguments[0])', poni['entityId']))
                    driver.settle()
                    delayed['after'] = snapshot()
                    delayed['afterScrollMetrics'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
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
                    delayed['stage'] = 'completed'
                finally:
                    hold.note('finally-release')
                    hold.released.set()
                    delayed['hold'] = hold.diagnostic()
                    try:
                        delayed['resourceFinal'] = driver.js(DELAYED_PACKET_DIAGNOSTIC_JS, packet['sha256'], poni['entityId'])
                    except Exception as exc:
                        delayed['resourceDiagnosticErrorType'] = type(exc).__name__
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


ORIGINAL_CHALLENGE_TITLE_SELECTOR = '#np-reader-object-title h2'
ORIGINAL_CHALLENGE_ROLE_SELECTOR = '#np-reader-object-meta .np-reader-field-role[data-reader-field-role="plain_language_question"]'
ORIGINAL_CHALLENGE_SNAPSHOT_JS = VISUAL_GEOMETRY + SCROLL_REGION_VISIBILITY_JS + r"""
function measured(spec){return (function(){
""" + TASK_ROUTE_PROOF_JS + r"""
}).call(null,spec);}
var expected=arguments[0],questionText=arguments[1],titleSelector=arguments[2],roleSelector=arguments[3],
    summarySelector='#np-reader-summary [data-reading-node="'+expected.id+'"]',summaries=document.querySelectorAll(summarySelector),
    summary=summaries.length===1?summaries[0]:null,header=document.getElementById('np-reader-object-title'),
    titles=document.querySelectorAll(titleSelector),roles=document.querySelectorAll(roleSelector),
    scopeSelector=summarySelector+' [data-challenge-scope]',scopes=document.querySelectorAll(scopeSelector),scope=scopes.length===1?scopes[0]:null,
    questions=summary?[...summary.querySelectorAll(':scope > .np-detail-block')].filter(e=>e.querySelector(':scope > h3')?.textContent==='研究问题'):[],question=questions.length===1?questions[0]:null,
    questionSelector=question?summarySelector+' > .np-detail-block:nth-child('+([...summary.children].indexOf(question)+1)+') > p':null,
    generatedHeadings=summary?summary.querySelectorAll(':scope > h3'):[];
function duplicate(e){return {tag:e.tagName,marked:e.classList.contains('np-reader-identity-duplicate'),position:e.dataset.readerDuplicatePosition||null,field:e.dataset.readerDuplicateField||null,owner:e.closest('[data-reading-node]')?.dataset.readingNode||null,directChild:e.parentElement===summary,text:e.textContent,rendering:renderedElementState(e)};}
return {route:NavigationProductApp.getState().route,summaryCount:summaries.length,summaryPosition:summary?.dataset.readingNode||null,
  titleCount:titles.length,title:titles.length===1?measured({selector:titleSelector,region:'heading'}):null,
  titleIdentity:header?{position:header.dataset.objectPosition||null,entity:header.dataset.objectEntity||null,paper:header.dataset.objectPaper||null,version:header.dataset.objectVersion||null}:null,
  identityHeadingCount:generatedHeadings.length,identityHeading:generatedHeadings.length===1?duplicate(generatedHeadings[0]):null,
  questionDuplicate:question?duplicate(question):null,markedDuplicates:summary?[...summary.querySelectorAll('.np-reader-identity-duplicate')].map(duplicate):[],
  roleCount:roles.length,questionRole:roles.length===1?measured({selector:roleSelector,region:'heading'}):null,
  questionCount:questions.length,questionText:question?.querySelector(':scope > p')?.textContent||null,
  question:question&&questionText!==titles[0]?.textContent?measured({selector:questionSelector,region:'reader'}):null,
  scopeCount:scopes.length,scopeEntity:scope?.dataset.challengeScope||null,scope:scope?box(scope):null,
  scopeParagraphs:scope?[...scope.querySelectorAll(':scope > p')].map((p,i)=>measured({selector:scopeSelector+' > p:nth-of-type('+(i+1)+')',region:'reader'})):[],
  viewport:{x:0,y:0,width:innerWidth,height:innerHeight}};
"""


def check_original_challenge_reading(data, position, original):
    """Fixed identity may represent an identical question, never another source field."""
    identity = {'position': position['id'], 'entity': position['entityId'],
                'paper': position.get('paperId'), 'version': position.get('versionId')}
    if (position['entityId'] != original['id'] or data['titleIdentity'] != identity or
            data['titleCount'] != 1 or data['summaryCount'] != 1 or data['summaryPosition'] != position['id'] or
            data['scopeCount'] != 1 or data['scopeEntity'] != original['id'] or
            any(key not in data['route'] or data['route'][key] != position.get(field) for key, field in
                (('node', 'id'), ('tree', 'tree'), ('scope', 'scopeId'), ('paper', 'paperId'), ('version', 'versionId')))):
        raise RuntimeError('Challenge fixed title or scope belongs to another source position, entity, paper or version')
    for key in ('title', 'scope'):
        proof = data[key]
        if (proof is None or not proof['visible'] or not proof['opaque'] or not proof['unscaled'] or
                proof['fontSize'] < 15 or proof['clipped'] or len(proof['foreground']) != 3 or len(proof['background']) != 3 or
                contrast_ratio(proof['foreground'], proof['background']) < 4.5 or not rect_inside(proof['rect'], data['viewport'])):
            raise RuntimeError('Challenge original question and scope are not visible together')
    check_task_route_proof(data['title'], original['label'])
    def hidden_duplicate(record, tag, field=None):
        if (record is None or record['tag'] != tag or record['field'] != field or record['marked'] is not True or
                record['owner'] != position['id'] or record['position'] != position['id'] or record['directChild'] is not True or
                record['rendering']['display'] != 'none' or
                record['rendering']['rendered'] is not False or not record['rendering']['blockedBy'] or
                record['rendering']['blockedBy']['reason'] not in ('hidden', 'display-none', 'visibility', 'opacity-zero', 'closed-details')):
            raise RuntimeError('Challenge generated identity duplicate is not actually hidden for the exact current object')
    if data['identityHeadingCount'] != 1 or data['identityHeading'] is None or data['identityHeading']['text'] != original['label']:
        raise RuntimeError('Challenge generated identity heading changed or lost its exact source label')
    hidden_duplicate(data['identityHeading'], 'H3')
    question = original['detail'].get('plain_language_question')
    expected_duplicates = [('H3', None)] + ([('SECTION', 'plain_language_question')] if question == original['label'] else [])
    actual_duplicates = [(item['tag'], item['field']) for item in data['markedDuplicates']]
    if actual_duplicates != expected_duplicates:
        raise RuntimeError('Challenge deduplication marked another field or omitted an approved duplicate')
    for item in data['markedDuplicates']:
        hidden_duplicate(item, item['tag'], item['field'])
    if question:
        if data['questionCount'] != 1 or data['questionText'] != question:
            raise RuntimeError('Challenge original research-question field was removed or changed')
        if question == original['label']:
            hidden_duplicate(data['questionDuplicate'], 'SECTION', 'plain_language_question')
            if data['roleCount'] != 1 or data['questionRole'] is None:
                raise RuntimeError('Identical fixed question lacks its explicit research-question field role')
            check_task_route_proof(data['questionRole'], ' · 研究问题')
        else:
            if data['roleCount'] or data['question'] is None:
                raise RuntimeError('Different research-question text cannot be represented by the fixed title')
            check_task_route_proof(data['question'], question)
    if len(data['scopeParagraphs']) < 3:
        raise RuntimeError('Challenge applicability paragraphs are incomplete')
    for proof in data['scopeParagraphs']:
        if not _reader_proof(proof, data['viewport'], font_size=15):
            raise RuntimeError('Challenge applicability paragraph is not visibly readable')
        check_task_route_proof(proof)
    scope = original['detail']['condition_scope']
    required = [scope['condition'], *scope['tasks'], scope['remaining_limit']]
    if any(not any(text in proof['renderedText'] for proof in data['scopeParagraphs']) for text in required):
        raise RuntimeError('Challenge reader omitted an original visible condition, task or remaining limit')


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
        summary = '方法关系 ' + str(local_count) + (' · 范围外 ' + str(outside_count) if outside_count else '')
        proofs = [{'selector': '#np-task-route-relations-summary', 'region': 'toolbar', 'text': summary}, label(expected['roots'][0])]
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
                  'proofs': [{'selector': '#np-task-route-relations-summary', 'region': 'toolbar', 'text': '方法关系 0'}, label(roots[0]), {'selector': '#np-tree .np-parallel-gap', 'region': 'canvas', 'text': '当前范围尚无已整理的方法分枝；保留任务定义和原文入口。'}], 'empty': True})
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
            data['window'] != {'x': 0, 'y': 0} or data['readerScroll'] != {'top': 0, 'left': 0} or data['treeScroll'] != {'top': 0, 'left': 0} or
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
            disclosure['insideTree'] or disclosure['insideTreeScroll'] or not disclosure['toolbar'] or
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
              'screenKind': 'natural_initial_task_workspace', 'documentTopClaimed': True}
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


def desktop_hierarchy_checks(driver, report, save, capture, prefix, base, science):
    """Natural S1/S2 screens and fixed identity while real reader input scrolls."""
    expected = task_route_expected(science)
    poni = expected['poni']
    record = {'viewport': prefix, 'status': 'checking', 'transitions': []}
    report.setdefault('desktopHierarchyChecks', []).append(record)
    save()

    def shell():
        return desktop_chrome_snapshot(driver, report, save, prefix + '-hierarchy-shell', DESKTOP_SHELL_SNAPSHOT_JS)

    def ready(pid):
        return driver.js("var a=window.NavigationProductApp,p=a&&a.getBundle().positions[arguments[0]];return p&&a.getState().route.node===p.id&&a.getContent().ready(p.entityId)&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready';", pid)

    driver.call('POST', '/url', {'url': base})
    wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
    driver.click(driver.selector('[data-task-open="task:category-objectnav"]'))
    wait_for(lambda: driver.js("return document.querySelector('#np-task-route-canvas [data-task-route-state=ready]')"))
    driver.settle()
    record['taskBeforePicker'] = shell()
    check_desktop_shell(record['taskBeforePicker'])
    driver.click(driver.selector('#np-task-route-relations-summary'))
    driver.settle()
    record['taskWithPicker'] = shell()
    driver.click(driver.selector('[data-task-change="methods:relation:90"]'))
    wait_for(lambda: driver.js("return document.querySelector('[data-selected-task-relation=\"methods:relation:90\"]')&&document.querySelector('[data-relation-state]')?.dataset.relationState==='ready'"))
    driver.settle()
    record['relation'] = shell()
    save()
    check_desktop_shell(record['relation'])
    roots = expected['scopes'][poni['scopeId']]['roots']
    first_group = expected['scopes'][poni['scopeId']]['groups'][0]
    semexp = next(p for p in science['positions'].values() if p['scopeId'] == poni['scopeId'] and p['tree'] == 'l' and p['entityId'] == 'methods:pipeline-semexp')
    check_relation_canvas_stability(record['taskBeforePicker'], record['taskWithPicker'], record['relation'], [roots[0], first_group, semexp['id'], poni['id']])
    check_desktop_relation_heading(record['relation'], expected)
    capture(prefix + '-32-s1-relation-90')

    # Deduplicated S1 can genuinely fit without overflow. Keep its native input
    # invariance proof, but do not mislabel zero movement as a positive scroll.
    native_scroll(driver, record, save, 'reader', 180, 'fixed-relation-identity')
    record['relationScrolled'] = shell()
    record['relationScrollScenario'] = ('original_relation_positive_scroll' if record['relation']['scrollMetrics']['reader']['maxTop'] > 0 else 'original_relation_short_no_overflow')
    save()
    check_desktop_relation_heading(record['relationScrolled'], expected)
    check_fixed_reader_scroll(record['relation'], record['relationScrolled'], positive=record['relation']['scrollMetrics']['reader']['maxTop'] > 0)
    endpoint = reveal_control(driver, {'selector': '[data-selected-task-relation="methods:relation:90"] [data-change-target="' + poni['id'] + '"]'})
    driver.click(endpoint)
    wait_for(lambda: ready(poni['id']))
    driver.settle()
    record['method'] = shell()
    save()
    check_desktop_shell(record['method'])
    for key in ('analysisEntry', 'analysisStatus'):
        if not _reader_proof(record['method'][key], record['method']['pane'], record['method']['viewport'], font_size=15):
            raise RuntimeError('Imported version analysis status and main action are not immediately readable')
    entry_box = record['method']['analysisEntry']['rect']
    if entry_box['y'] + entry_box['height'] - record['method']['panels']['y'] > 188:
        raise RuntimeError('Version analysis main action is below its fixed first-screen entry')
    # The mandatory positive-wheel proof uses this existing exact PONI source.
    # Measure first; expand original evidence only if the natural body fits.
    prepared = prepare_scroll_fixture(driver, record, save, 'reader')
    if prepared['position']['id'] != poni['id'] or prepared['position']['paper'] != poni['paperId'] or prepared['position']['version'] != poni['versionId']:
        raise RuntimeError('Positive reader fixture is not the exact original PONI version')
    record['positiveWheelSource'] = 'original_poni_method_with_native_evidence_if_needed'
    record['methodBeforeWheel'] = shell()
    native_scroll(driver, record, save, 'reader', 180, 'fixed-method-identity')
    record['methodScrolled'] = shell()
    record['methodWheelMetrics'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
    save()
    check_native_wheel_progress(prepared, record['methodWheelMetrics'], 'reader')
    check_desktop_shell(record['methodScrolled'])
    check_fixed_reader_scroll(record['methodBeforeWheel'], record['methodScrolled'], positive=True)
    driver.click(driver.selector('#np-open-version-analysis'))
    entry = science['analyses'][poni['paperId']][poni['versionId']]
    answer = first_analysis_answer(science, entry)
    if answer is None:
        raise RuntimeError('Reviewed imported version has no original analysis answer')
    wait_for(lambda: ready(answer['id']))
    driver.settle()
    record['analysis'] = shell()
    save()
    check_analysis_first_answer(record['analysis'], answer, entry, science['entities'][answer['entityId']]['detail']['answer']['answer'], science['versions'][answer['versionId']]['label'])
    capture(prefix + '-33-s2-first-answer')
    record['status'] = 'captured_for_human_review'
    save()


def literature_scroll_position(science, pipeline):
    """Retain the exact original same-version child while the full forest scrolls."""
    rows = [science['positions'][pid] for pid in pipeline['childIds']]
    rows = [p for p in rows if p['kind'] == 'technical_improvement' and p['parentId'] == pipeline['id'] and
            all(p[key] == pipeline[key] for key in ('scopeId', 'tree', 'paperId', 'versionId'))]
    if len(rows) != 1:
        raise RuntimeError('Original PONI same-version retention child is missing or ambiguous')
    return rows[0]


ANALYSIS_ROUTE_FIELDS = ('nav', 'scope', 'tree', 'node', 'paper', 'version', 'bench', 'protocol', 'template', 'claim', 'mode')


def analysis_answer_rows_expected(science, root_id):
    root = science['positions'][root_id]
    if root['tree'] != 'a' or root['kind'] == 'analysis_answer' or root['parentId'] is not None:
        raise RuntimeError('Answer-row source must be an original structural analysis root')
    def walk(pid):
        position = science['positions'][pid]
        yield position
        for child in position['childIds']:
            yield from walk(child)
    rows, chapters = [], []
    for chapter_id in root['childIds']:
        original = [p for p in walk(chapter_id) if not p.get('isPaperSpecificInstantiation')]
        answers = [p for p in original if p['kind'] == 'analysis_answer']
        chapters.append(chapter_id)
        for p in answers:
            if p['paperId'] != root['paperId'] or p['versionId'] != root['versionId']:
                raise RuntimeError('Answer-row original source borrowed another paper/version')
            rows.append({'id': p['id'], 'parent': p['parentId'], 'entity': p['entityId'], 'chapter': chapter_id,
                         'paper': p['paperId'], 'version': p['versionId'], 'scope': p['scopeId'],
                         'label': science['entities'][p['entityId']].get('label') or p.get('sourceLabel') or p['label']})
    pair = next(([left['id'], right['id']] for i, left in enumerate(rows) for right in rows[i + 1:]
                 if left['label'] == right['label'] and left['id'] != right['id']), None)
    if len(rows) < 2:
        raise RuntimeError('Answer-row keyboard proof needs two distinct original destinations')
    return {'root': root_id, 'paper': root['paperId'], 'version': root['versionId'], 'chapters': chapters, 'rows': rows,
            'keyboardTargets': pair or [rows[0]['id'], rows[-1]['id']],
            'keyboardSelection': 'same-label-distinct-original-IDs' if pair else 'two-distinct-original-IDs-no-repeated-source-label'}


ANALYSIS_ANSWER_ROWS_SNAPSHOT_JS = VISUAL_GEOMETRY + FIXED_TEXT_PROOF_JS + STATIONARY_SHELL_ANCESTORS_JS + r"""
var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),b=a.getBundle(),reader=document.getElementById('np-detail-scroll'),tree=document.getElementById('np-tree-scroll'),
    title=document.getElementById('np-reader-object-title'),roots=reader.querySelectorAll('[data-analysis-root]'),root=roots.length===1?roots[0]:null,
    historyModel=history.state&&history.state[m.KEY],rr=rect(reader),client={x:rr.x+reader.clientLeft,y:rr.y+reader.clientTop,width:reader.clientWidth,height:reader.clientHeight};
function metrics(e){return {top:e.scrollTop,left:e.scrollLeft,scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,maxTop:Math.max(0,e.scrollHeight-e.clientHeight)};}
function contentRect(e){var r=rect(e);return {x:r.x-client.x+reader.scrollLeft,y:r.y-client.y+reader.scrollTop,width:r.width,height:r.height};}
function saved(value){return value&&value.contexts?.[m.contextKey(value.route)]?.detailScrollByTree?.[value.route.tree];}
return {ready:document.getElementById('navigation-product').dataset.loadState,route:s.route,historyRoute:historyModel?.route||null,
  window:{x:scrollX,y:scrollY},viewport:{x:0,y:0,width:innerWidth,height:innerHeight},stationaryAncestors:stationaryShellAncestors(),
  reader:metrics(reader),readerClient:client,readerRect:rr,tree:metrics(tree),expanded:m.getBucket(s).expandedByTree,
  runtimeReader:saved(s),historyReader:saved(historyModel),focus:{id:document.activeElement.id,answer:document.activeElement.dataset.analysisAnswerPosition||null},
  fixedIdentity:{position:title.dataset.objectPosition||null,paper:title.dataset.objectPaper||null,version:title.dataset.objectVersion||null},
  answerBodyCount:reader.querySelectorAll('.np-analysis-answer').length,coverageCount:roots.length,root:root?.dataset.analysisRoot||null,
  chapters:root?[...root.querySelectorAll(':scope > [data-analysis-chapter]')].map(e=>e.dataset.analysisChapter):[],
  rows:root?[...root.querySelectorAll('[data-analysis-answer-position]')].map(e=>{var p=b.positions[e.dataset.analysisAnswerPosition],li=e.parentElement,list=li.parentElement;return {
    id:e.dataset.analysisAnswerPosition,parent:p?.parentId,entity:p?.entityId,chapter:e.closest('[data-analysis-chapter]')?.dataset.analysisChapter,
    paper:p?.paperId,version:p?.versionId,scope:p?.scopeId,tag:e.tagName,type:e.type,disabled:e.disabled,hidden:e.hidden,role:e.getAttribute('role'),tabIndex:e.tabIndex,
    itemTag:li.tagName,itemChildren:li.children.length,listTag:list.tagName,listClass:list.className,listRole:list.getAttribute('role'),
    itemRect:rect(li),contentRect:contentRect(e),proof:fixedTextProof(e)};}):[]};
"""

ANALYSIS_EXACT_ROUTE_READY_JS = r"""
var a=window.NavigationProductApp,expected=arguments[0];if(!a)return false;var actual=a.getState().route,keys=Object.keys(actual).sort(),wanted=Object.keys(expected).sort(),p=a.getBundle().positions[actual.node];
return keys.length===wanted.length&&keys.every((key,i)=>key===wanted[i]&&actual[key]===expected[key])&&
  document.querySelector('[data-load-state]')?.dataset.loadState==='ready'&&p&&a.getContent().ready(p.entityId)&&
  document.getElementById('np-reader-object-title')?.dataset.objectPosition===expected.node;
"""


def exact_analysis_route(actual, expected):
    return (isinstance(actual, dict) and isinstance(expected, dict) and set(actual) == set(expected) == set(ANALYSIS_ROUTE_FIELDS) and
            all(type(actual[key]) is type(expected[key]) and actual[key] == expected[key] for key in ANALYSIS_ROUTE_FIELDS))


def check_analysis_answer_rows(data, expected):
    route = data['route']
    if (data['ready'] != 'ready' or data['window'] != {'x': 0, 'y': 0} or
            set(route) != set(ANALYSIS_ROUTE_FIELDS) or not exact_analysis_route(data['historyRoute'], route) or
            (route['tree'], route['node'], route['paper'], route['version'], route['template'], route['claim']) !=
            ('a', expected['root'], expected['paper'], expected['version'], None, None) or
            data['fixedIdentity'] != {'position': expected['root'], 'paper': expected['paper'], 'version': expected['version']} or
            data['coverageCount'] != 1 or data['root'] != expected['root'] or data['answerBodyCount'] != 0 or data['chapters'] != expected['chapters']):
        raise RuntimeError('Analysis answer rows lost their exact original root, chapters or source-version route')
    check_stationary_shell_ancestors(data['stationaryAncestors'])
    check_scroll_metrics(data['reader'])
    if data['reader']['left'] != 0 or not rect_inside(data['readerClient'], data['viewport']):
        raise RuntimeError('Analysis answer-row reader is outside its real desktop viewport')
    fields = ('id', 'parent', 'entity', 'chapter', 'paper', 'version', 'scope')
    if [{key: row[key] for key in fields} for row in data['rows']] != [{key: row[key] for key in fields} for row in expected['rows']]:
        raise RuntimeError('Analysis answer rows are missing, merged, reordered or borrowed from another version')
    previous = None
    for row, source in zip(data['rows'], expected['rows']):
        if (row['tag'] != 'BUTTON' or row['type'] != 'button' or row['disabled'] or row['hidden'] or row['role'] is not None or row['tabIndex'] != 0 or
                row['itemTag'] != 'LI' or row['itemChildren'] != 1 or row['listTag'] != 'UL' or row['listClass'] != 'np-analysis-answer-index' or row['listRole'] is not None or
                row['proof']['text'] != source['label'] or row['proof']['renderedText'] != source['label'] or
                not row['proof']['opaque'] or not row['proof']['unscaled'] or row['proof']['clipped'] or
                row['contentRect']['height'] < 36 or row['contentRect']['width'] <= 0):
            raise RuntimeError('Analysis answer destination lost its complete original label or native one-row button')
        if previous and (rects_intersect(previous['contentRect'], row['contentRect']) or
                         row['contentRect']['y'] < previous['contentRect']['y'] + previous['contentRect']['height']):
            raise RuntimeError('Analysis answer destinations overlap or share the same visual line')
        if not rect_inside(row['proof']['rect'], row['itemRect']):
            raise RuntimeError('Analysis answer button escapes its own separate list row')
        previous = row


def analysis_answer_visible(row, data, label):
    try:
        check_s0_text(row['proof'], label, row['itemRect'], data['readerClient'], data['viewport'])
    except RuntimeError:
        return False
    return True


def check_analysis_answer_scan(record, expected):
    frames = record['frames']
    if len(frames) < 2 or record['positiveWheelCount'] != len(frames) - 1:
        raise RuntimeError('Analysis answer scan has no positive native reader-wheel evidence')
    for data in frames:
        check_analysis_answer_rows(data, expected)
        if (not exact_analysis_route(data['route'], frames[0]['route']) or data['readerClient'] != frames[0]['readerClient'] or
                data['tree'] != frames[0]['tree'] or data['expanded'] != frames[0]['expanded'] or
                [row['contentRect'] for row in data['rows']] != [row['contentRect'] for row in frames[0]['rows']]):
            raise RuntimeError('Analysis native scan shifted another pane, row layout or original route')
    if frames[0]['reader']['top'] != 0 or frames[-1]['reader']['top'] != frames[-1]['reader']['maxTop'] or frames[-1]['reader']['top'] <= 0:
        raise RuntimeError('Analysis answer scan did not reach the real source-content bottom from the top')
    for before, after in zip(frames, frames[1:]):
        if after['reader']['top'] <= before['reader']['top'] or before['reader']['maxTop'] != after['reader']['maxTop']:
            raise RuntimeError('Analysis answer scan claims positive wheel without positive actual offset')
    visible = []
    for source in expected['rows']:
        matches = [(index, next(row for row in frame['rows'] if row['id'] == source['id'])) for index, frame in enumerate(frames)]
        proven = next((index for index, row in matches if analysis_answer_visible(row, frames[index], source['label'])), None)
        if proven is None:
            raise RuntimeError('Analysis scan never shows a complete original answer row inside the actual reader: ' + source['id'])
        visible.append({'id': source['id'], 'frame': proven, 'label': source['label']})
    if record['visibleRows'] != visible or record['bottom'] != frames[-1]:
        raise RuntimeError('Analysis answer scan substituted its ordered complete-row or bottom proof')


def analysis_answer_route(root_route, source):
    return dict(root_route, tree='a', node=source['id'], scope=source['scope'] or root_route['scope'],
                paper=source['paper'], version=source['version'], claim=None, template=None)


def check_analysis_answer_keyboard(record, expected, index):
    source = next(row for row in expected['rows'] if row['id'] == expected['keyboardTargets'][index])
    before, selected, after = record['before'], record['selected'], record['after']
    check_analysis_answer_rows(before, expected); check_analysis_answer_rows(after, expected)
    if before['reader']['top'] <= 0 or before['reader']['scrollHeight'] <= before['reader']['clientHeight']:
        raise RuntimeError('Both answer keyboard Back proofs need a genuine positive original reader offset')
    key = 'Enter' if index == 0 else ' '
    wanted = analysis_answer_route(before['route'], source)
    if (record['target'] != source['id'] or record['key'] != key or before['focus']['answer'] != source['id'] or
            record['expectedRoute'] != wanted or not exact_analysis_route(selected['route'], wanted) or
            not exact_analysis_route(selected['historyRoute'], wanted) or selected['answerBodyCount'] != 1 or selected['coverageCount'] != 0 or
            selected['fixedIdentity'] != {'position': source['id'], 'paper': source['paper'], 'version': source['version']} or
            selected['ready'] != 'ready' or selected['window'] != {'x': 0, 'y': 0}):
        raise RuntimeError('Native answer keyboard activation selected the wrong key, full route, object or source version')
    events = record['events']
    if (len(events) != 2 or [event['type'] for event in events] != ['keydown', 'keyup'] or
            any(event['key'] != key or event['trusted'] is not True for event in events) or events[0]['target'] != source['id'] or
            key == ' ' and events[1]['target'] != source['id']):
        raise RuntimeError('Answer-row Enter/Space proof is not a genuine native keyboard event on the exact target')
    row = next(row for row in before['rows'] if row['id'] == source['id'])
    if not analysis_answer_visible(row, before, source['label']):
        raise RuntimeError('Native answer keyboard target was not fully readable inside the actual reader')
    if (not exact_analysis_route(after['route'], before['route']) or after['reader'] != before['reader'] or
            after['tree'] != before['tree'] or after['expanded'] != before['expanded'] or
            after['historyReader'] != before['reader']['top'] or after['runtimeReader'] != before['reader']['top']):
        raise RuntimeError('Native browser Back lost the original analysis root or exact effective reader offset')


def analysis_answer_rows_checks(driver, record, save, science, root_id):
    """Real wheel/keyboard evidence inside the existing A-root scene; no new image."""
    expected = analysis_answer_rows_expected(science, root_id)
    audit = {'expected': expected, 'frames': [], 'visibleRows': [], 'positiveWheelCount': 0, 'keyboard': []}
    record['analysisAnswerRows'] = audit
    def snapshot():
        return driver.js(ANALYSIS_ANSWER_ROWS_SNAPSHOT_JS)
    initial = snapshot(); audit['initial'] = initial; save()
    check_analysis_answer_rows(initial, expected)
    def wheel(delta):
        before = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
        after = native_scroll(driver, audit, save, 'reader', int(delta), 'original-analysis-answer-scroll')
        check_scroll_fixture_source(before, after)
        if before['tree'] != after['tree'] or before['treeState'] != after['treeState'] or before['historyIdentity'] != after['historyIdentity']:
            raise RuntimeError('Answer scan native wheel moved the source tree or history')
        check_scroll_metrics(after['reader'])
        if (after['reader']['top'] - before['reader']['top']) * delta <= 0:
            raise RuntimeError('Answer scan wheel produced no actual effective progress')
        if delta > 0:
            check_native_wheel_progress(before, after, 'reader')
        return snapshot()
    def scroll_to(target):
        current = snapshot()
        if target != int(target):
            raise RuntimeError('Original analysis reader offset is not exactly reachable by integer native wheel')
        while current['reader']['top'] != target:
            current = wheel(target - current['reader']['top'])
        return current
    current = scroll_to(0)
    audit['frames'].append(current); save()
    while current['reader']['top'] < current['reader']['maxTop']:
        current = wheel(max(1, int(current['reader']['clientHeight'] / 2)))
        audit['positiveWheelCount'] += 1; audit['frames'].append(current); save()
    audit['bottom'] = current
    for source in expected['rows']:
        frame_index = next((i for i, frame in enumerate(audit['frames']) if analysis_answer_visible(
            next(row for row in frame['rows'] if row['id'] == source['id']), frame, source['label'])), None)
        audit['visibleRows'].append({'id': source['id'], 'frame': frame_index, 'label': source['label']})
    save(); check_analysis_answer_scan(audit, expected)
    for index, target in enumerate(expected['keyboardTargets']):
        row = next(row for row in current['rows'] if row['id'] == target)
        current = scroll_to(int(max(0, min(current['reader']['maxTop'], row['contentRect']['y'] - 16))))
        element = driver.selector('[data-analysis-answer-position="' + target + '"]')
        driver.js("arguments[0].focus({preventScroll:true});", element)
        before = snapshot(); source = next(row for row in expected['rows'] if row['id'] == target)
        key = 'Enter' if index == 0 else ' '
        item = {'target': target, 'key': key, 'before': before, 'expectedRoute': analysis_answer_route(before['route'], source)}
        audit['keyboard'].append(item); save()
        driver.js("window.__npAnswerKeyProbe={events:[],handler:function(e){this.events.push({type:e.type,key:e.key,trusted:e.isTrusted,target:e.target.dataset.analysisAnswerPosition||null});}};var p=window.__npAnswerKeyProbe;p.listener=p.handler.bind(p);document.addEventListener('keydown',p.listener,true);document.addEventListener('keyup',p.listener,true);")
        try:
            code = '\ue007' if index == 0 else ' '
            driver.call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'original-analysis-answer-keyboard', 'actions': [
                {'type': 'keyDown', 'value': code}, {'type': 'keyUp', 'value': code}]}]})
            wait_for(lambda: driver.js(ANALYSIS_EXACT_ROUTE_READY_JS, item['expectedRoute']))
            driver.settle(); item['selected'] = snapshot()
        finally:
            item['events'] = driver.js("var p=window.__npAnswerKeyProbe;document.removeEventListener('keydown',p.listener,true);document.removeEventListener('keyup',p.listener,true);delete window.__npAnswerKeyProbe;return p.events;")
            save()
        driver.call('POST', '/back', {})
        wait_for(lambda: driver.js(ANALYSIS_EXACT_ROUTE_READY_JS, before['route']) and
                 driver.js("return document.getElementById('np-detail-scroll').scrollTop") == before['reader']['top'])
        driver.settle(); item['after'] = current = snapshot(); save()
        check_analysis_answer_keyboard(item, expected, index)
    final = scroll_to(initial['reader']['top']); audit['final'] = final; save()
    check_analysis_answer_rows(final, expected)
    if (not exact_analysis_route(final['route'], initial['route']) or final['reader'] != initial['reader'] or
            final['tree'] != initial['tree'] or final['expanded'] != initial['expanded'] or final['focus'] != initial['focus']):
        raise RuntimeError('Analysis evidence pass did not restore the original root capture state')


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
        before = prepare_scroll_fixture(driver, record, save, 'tree', require_end_target=True)
        if before['focusPosition'] not in [p['id'] for p in before['treeState']['positions']]:
            raise RuntimeError('Native End must begin inside the original active tree')
        item = {'before': before}
        record.setdefault('nativeEndProofs', []).append(item)
        save()
        try:
            # End is handled by the product's one actual tree keyboard scope.
            transition_record(driver, record, save, 'keyboard-end-in-active-tree', lambda: driver.call('POST', '/actions', {'actions': [{'type': 'key', 'id': 'active-tree-keyboard', 'actions': [{'type': 'keyDown', 'value': '\ue010'}, {'type': 'keyUp', 'value': '\ue010'}]}]}),
                lambda: driver.js("var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),t=document.getElementById('np-tree-scroll'),stored=history.state&&history.state[m.KEY],k=m.contextKey(s.route);return t.scrollTop>0&&stored&&stored.contexts[k].treeScrollByTree[s.route.tree]===t.scrollTop&&document.activeElement.closest('#np-tree [data-parallel-tree]');"))
        finally:
            item['after'] = driver.js(SCROLL_FIXTURE_SNAPSHOT_JS)
            save()
        after = item['after']
        check_native_wheel_progress(before, after, 'tree')
        if after['focusPosition'] != before['treeState']['positions'][-1]['id']:
            raise RuntimeError('Native End did not focus the last original active-tree position')

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
    retention = literature_scroll_position(science, expected['poni'])
    record['literatureScrollSource'] = {'scenario': 'original_poni_technical_child_full_forest', 'position': retention}
    select(retention['id'])
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
    transition_record(driver, record, save, 'return-literature-for-analysis', lambda: driver.click(driver.selector('[data-tree-tab="l"]')), lambda: ready_node(literature['route']['node']))
    select(expected['poni']['id'])  # The real source ancestor, not a remapped child route.
    pipeline = snapshot()
    record['pipelineAnalysisSource'] = pipeline
    imported = pipeline['analysisEntry']
    if imported != {'state': 'imported', 'paper': 'poni', 'version': expected['poni']['versionId']}:
        raise RuntimeError('PONI imported-analysis entry belongs to another source version')
    entry = science['analyses']['poni'][expected['poni']['versionId']]
    first_answer = first_analysis_answer(science, entry)
    if first_answer is None:
        raise RuntimeError('Imported source version has no actual analysis answer')
    analysis_scene('-30-analysis-imported-entry', [
        {'selector': '[data-analysis-state="imported"] > p', 'region': 'analysis-entry', 'text': '本版本部分解析：' + str(entry['answeredOriginalCount']) + '/' + str(entry['originalNodeCount']) + ' 原节点已填 · ' + str(entry['answeredInstanceCount']) + ' 个实例答案'},
        {'selector': '#np-open-version-analysis', 'region': 'analysis-entry', 'text': '阅读本版本已有回答'},
        {'selector': '#np-open-analysis-structure', 'region': 'analysis-entry', 'text': '查看完整' + str(entry['originalNodeCount']) + '节点结构'}])
    transition_record(driver, record, save, 'open-imported-version-analysis', lambda: driver.click(reveal_control(driver, {'selector': '#np-open-version-analysis'})),
        lambda: ready_node(first_answer['id']))
    analysis = snapshot()
    entry = science['analyses']['poni'][expected['poni']['versionId']]
    if (analysis['route']['node'] != first_answer['id'] or analysis['route']['template'] is not None or
            analysis['route']['paper'] != 'poni' or analysis['route']['version'] != expected['poni']['versionId'] or entry['answeredOriginalCount'] != 22):
        raise RuntimeError('Imported A was replaced with a generic template or another version')
    record['scenes'].append({'name': prefix + '-30-analysis-imported', 'state': analysis, 'sourceAnalysis': entry})
    save()
    capture(prefix + '-30-analysis-imported')
    transition_record(driver, record, save, 'return-from-imported-analysis', lambda: driver.click(driver.selector('.np-return-previous')), lambda: ready_node(expected['poni']['id']))
    transition_record(driver, record, save, 'open-explicit-analysis-root-coverage', lambda: driver.click(driver.selector('#np-open-analysis-structure')),
        lambda: ready_node(entry['roots'][0]))
    root_coverage = snapshot()
    root_contract = driver.js("var a=NavigationProductApp,b=a.getBundle(),r=a.getState().route,p=b.positions[r.node],ids=NavigationProductModel.descendants(b,arguments[0].roots);return {root:document.querySelector('[data-analysis-root]')?.dataset.analysisRoot,kind:p.kind,positions:ids.map(id=>({id:id,parent:b.positions[id].parentId})),chapters:[...document.querySelectorAll('[data-analysis-chapter]')].map(e=>e.dataset.analysisChapter)};", entry)
    root_coverage['rootContract'] = root_contract
    record['analysisRootCoverage'] = root_coverage
    save()
    def source_preorder(pid):
        return [pid] + [item for child in science['positions'][pid]['childIds'] for item in source_preorder(child)]
    original_positions = [pid for root in entry['roots'] for pid in source_preorder(root)]
    if (root_contract['root'] != entry['roots'][0] or root_contract['kind'] == 'analysis_answer' or
            root_contract['positions'] != [{'id': pid, 'parent': science['positions'][pid]['parentId']} for pid in original_positions] or
            root_contract['chapters'] != science['positions'][entry['roots'][0]]['childIds']):
        raise RuntimeError('Explicit analysis root lost original topology, chapter coverage or structural role')
    if root_coverage['route']['node'] != entry['roots'][0] or root_coverage['route']['template'] is not None:
        raise RuntimeError('Explicit source root no longer opens the version coverage view')
    analysis_answer_rows_checks(driver, record, save, science, entry['roots'][0])
    record['scenes'].append({'name': prefix + '-30-analysis-root-coverage', 'state': root_coverage})
    save()
    capture(prefix + '-30-analysis-root-coverage')
    transition_record(driver, record, save, 'return-from-analysis-root-coverage', lambda: driver.click(driver.selector('.np-return-previous')), lambda: ready_node(expected['poni']['id']))
    vlfm = next(p for p in science['positions'].values() if p['scopeId'] == 'task:category-objectnav' and p['tree'] == 'l' and p['paperId'] == 'vlfm' and p['kind'] == 'pipeline_recipe')
    select(expected['scopes'][expected['poni']['scopeId']]['roots'][0])
    select(vlfm['id'])
    missing_spec = {'selector': '[data-analysis-state="not-imported"] > p', 'region': 'analysis-entry', 'text': '本版本未导入逐节点解析；未填状态保留。'}
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
    transition_record(driver, record, save, 'open-analysis-template-disclosure', lambda: driver.click(driver.selector('#np-reader-analysis-entry .np-analysis-reference > summary')),
        lambda: driver.js("return document.querySelector('#np-reader-analysis-entry .np-analysis-reference').open"))
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
    routes = [literature['route'], pipeline['route'], challenge['route'], analysis['route'], root_coverage['route']]
    global_route = driver.js('var a=NavigationProductApp;return NavigationProductModel.routeForPosition(a.getBundle(),a.getState().route,a.getBundle().researchMap.roots[0]);')
    routes.append(global_route)
    claim_route = dict(pipeline['route'], claim=task_route_claims(science, expected['poni'])[0]['id'])
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


# The stationary reading-pane wrapper and its inner scrolling body are distinct.
# Collect both, but only the real reader ID can satisfy a reader-only capture.
CAPTURE_BOUNDS_SELECTOR = '#np-workspace,#np-tree-scroll,.np-reading-pane,#np-detail-scroll,#np-tree .np-node-row'


def check_capture_visible_regions(data, require_tree=True, require_home=False):
    visible = [r for r in data['bounds'] if r['width'] > 0 and r['height'] > 0 and r['x'] < data['viewport']['width'] and r['y'] < data['viewport']['height'] and r['x'] + r['width'] > 0 and r['y'] + r['height'] > 0]
    if require_tree and not require_home and not any(r.get('position') for r in visible):
        raise RuntimeError('No actual tree node visible in captured viewport')
    if not require_tree and not require_home and not any(r.get('id') == 'np-detail-scroll' for r in visible):
        raise RuntimeError('Reader is not visible in reader screenshot')


# These four display occurrences were independently reviewed at 7d34188. Each
# scene shows the native full-title surface with optional site chrome, not a short method label.
VERSION_TITLE_CASES = (
    ('-34-version-title-langmap', 'pos:g:18a33fba17e8e92ee1ed5d', 'langmap26', 'arxiv:2602.02220v3',
     'LangMap: A Human-Verified Benchmark for Hierarchical Open-Vocabulary Goal Navigation'),
    ('-34-version-title-cow-objectnav', 'pos:g:751e83079cd6d4ffeaf58a', 'cow', 'publication:cow:a7abf1e326e6',
     'CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation'),
    ('-34-version-title-cow-language', 'pos:g:e45df86dddd9cb1b67463c', 'cow', 'publication:cow:a7abf1e326e6',
     'CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation'),
    ('-34-version-title-cow-open-vocabulary', 'pos:g:31c6cd8857132fbe346c39', 'cow', 'publication:cow:a7abf1e326e6',
     'CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation'),
)


def version_title_expected(science):
    from navigation_research_map import build_research_map, _node_name, _enhanced
    positions = build_research_map(science)['positions']
    rows = []
    for suffix, pid, paper, version, title in VERSION_TITLE_CASES:
        p = positions[pid]
        old = science['positions'][p['sourcePositionId']]
        if (p['paperId'], p['versionId'], p['label']) != (paper, version, title):
            raise RuntimeError('Version-title capture target differs from the reviewed source')
        if (p['kind'] != 'pipeline_recipe' or p['tree'] != 'g' or
                old['paperId'] != paper or old['versionId'] != version or
                old['entityId'] != p['entityId'] or p['sourceLabel'] != old['label'] or
                science['versions'][version]['paperId'] != paper):
            raise RuntimeError('Version-title source position or paper/version binding changed')
        ancestors, cursor = [], p
        while cursor:
            if cursor['id'] in ancestors: raise RuntimeError('Version-title ancestry cycle')
            ancestors.insert(0, cursor['id'])
            cursor = positions.get(cursor['parentId'])
        route = dict(nav='1', tree='g', node=pid, scope='scope:all', bench=None, protocol=None,
                     paper=paper, version=version, claim=None, mode='tree', template=None)
        rows.append(dict(suffix=suffix, position=pid, sourcePosition=p['sourcePositionId'],
                         entity=p['entityId'], paper=paper, version=version, title=title,
                         sourceScope=p['sourceScopeId'], sourceLabel=p['sourceLabel'], ancestors=ancestors,
                         branch=_node_name(pid), enhancedHref=_enhanced(p), route=route))
    if len(rows) != 4 or len({row['position'] for row in rows}) != 4:
        raise RuntimeError('Version-title capture inventory is incomplete or duplicated')
    return rows


# Native summary hover paint also lasts 160ms. Keep this wait local to the
# exact original control; never wait for a readability predicate to become true.
VERSION_TITLE_PAINT_TIMEOUT_MS = 2000
VERSION_TITLE_PAINT_SETTLE_JS = ('var paintScopeSelector=arguments[1],paintScopeName="Native version title";\n' +
                               SCOPED_TOOLBAR_PAINT_SETTLE_JS)


def settle_version_title_paint(driver, report, save, phase, selector):
    data = driver.call('POST', '/execute/async', {
        'script': VERSION_TITLE_PAINT_SETTLE_JS, 'args': [VERSION_TITLE_PAINT_TIMEOUT_MS, selector]})
    report.setdefault('versionTitlePaintSettles', []).append({'phase': phase, 'scope': selector, 'settle': data})
    save()  # Retain real raw colors and timeout/error diagnostics before failing.
    if (not isinstance(data, dict) or data.get('status') != 'settled' or
            data.get('scopeSelector') != selector or data.get('timeoutMs') != VERSION_TITLE_PAINT_TIMEOUT_MS or
            type(data.get('elapsedMs')) not in (int, float) or
            not 0 <= data['elapsedMs'] < VERSION_TITLE_PAINT_TIMEOUT_MS or
            not data.get('before') or not data.get('after')):
        raise RuntimeError('Native version-title paint did not settle within the fixed budget')
    return data


VERSION_TITLE_PAINT_DIAGNOSTIC_JS = r"""
function nativeVersionTitlePaint(summary){
 var layers=[],transitions=[],error=null;
 for(var e=summary;e;e=e.parentElement){
  var s=getComputedStyle(e),identity={tag:e.tagName,id:e.id||'',position:e.dataset.nativePosition||null,className:e.getAttribute('class')||''};
  layers.push({...identity,color:s.color,backgroundColor:s.backgroundColor});
  try{
   if(typeof CSSTransition!=='function'||typeof e.getAnimations!=='function')throw Error('CSS transition inspection unavailable');
   for(var a of e.getAnimations({subtree:false})){
    if(!(a instanceof CSSTransition)||!/^(?:color|background-color|border-(?:(?:top|right|bottom|left)-)?color)$/.test(a.transitionProperty))continue;
    if(a.playState==='finished'||(a.playState==='idle'&&!a.pending))continue;
    var t=a.effect.getComputedTiming();
    transitions.push({target:identity,property:a.transitionProperty,playState:a.playState,pending:a.pending,currentTime:a.currentTime,playbackRate:a.playbackRate,duration:t.duration,endTime:t.endTime});
   }
  }catch(err){error=String(err);}
 }
 return {layers:layers,transitions:transitions,error:error};
}
"""


VERSION_TITLE_SNAPSHOT_JS = VISUAL_GEOMETRY + VERSION_TITLE_PAINT_DIAGNOSTIC_JS + r"""
var expected=arguments[0],matches=[...document.querySelectorAll('[data-native-position]')].filter(e=>e.dataset.nativePosition===expected.position);
if(matches.length!==1)throw Error('Exact native title occurrence missing or duplicated');
var node=matches[0],summary=node.querySelector(':scope > summary'),ancestors=[],open=[],cursor=node;
while(cursor){ancestors.unshift(cursor.dataset.nativePosition);open.unshift(cursor.open);cursor=cursor.parentElement.closest('details[data-native-position]');}
function clips(e){var areas=[];for(var n=e;n;n=n.parentElement){var cs=getComputedStyle(n);if(/auto|scroll|hidden|clip/.test(cs.overflowX+' '+cs.overflowY)){var r=rect(n);areas.push({x:r.x+n.clientLeft,y:r.y+n.clientTop,width:n.clientWidth,height:n.clientHeight});}}return areas;}
var proof=box(summary),style=getComputedStyle(summary),runs=[],fragments=[];
for(var text of [...summary.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim())){
 var range=document.createRange();range.selectNodeContents(text);var run={text:text.textContent,opaque:proof.opaque,unscaled:proof.unscaled,fontSize:proof.fontSize,foreground:proof.foreground,background:proof.background,clipAreas:clips(summary),fragments:[]};
 for(var r of [...range.getClientRects()].filter(r=>r.width>0&&r.height>0)){
  var visible=proof.opaque&&proof.unscaled&&[[.5,.5],[.1,.1],[.9,.1],[.1,.9],[.9,.9]].every(([x,y])=>{var hit=document.elementFromPoint(r.x+r.width*x,r.y+r.height*y);return !!hit&&(hit===summary||summary.contains(hit));});
  var fragment={x:r.x,y:r.y,width:r.width,height:r.height,visible:visible};run.fragments.push(fragment);fragments.push(fragment);
 }runs.push(run);
}
var viewport={x:0,y:0,width:innerWidth,height:innerHeight},main=rect(document.querySelector('main'));
Object.assign(proof,{renderedText:runs.map(r=>r.text).join(''),textRuns:runs,fragments:fragments,clipAreas:clips(summary),viewport:viewport,readerContent:{x:main.x,y:0,width:main.width,height:innerHeight},textOverflow:style.textOverflow,lineClamp:style.webkitLineClamp});
var links=[...node.querySelectorAll(':scope > .native-body > p > a')];
return {screenKind:'native_version_title',position:node.dataset.nativePosition,ancestors:ancestors,ancestorOpen:open,
        focusedSummary:document.activeElement===summary,paint:nativeVersionTitlePaint(summary),
        title:proof,linkCount:links.length,branchHref:links[0]?.getAttribute('href'),pagePath:location.pathname,
        readyState:document.readyState,scriptCount:document.scripts.length,
        scripts:[...document.scripts].map(s=>({src:s.getAttribute('src'),defer:s.defer,inline:s.textContent.trim()})),
        appPresent:!!window.NavigationProductApp,
        fonts:document.fonts.status,viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
        bodyWidth:document.body.scrollWidth,windowScroll:scrollY};
"""


def check_version_title_capture_stability(before, after):
    # Bracket the PNG with the same unmodified DOM proof and actual paint state.
    # Unknown colors still fail the original contrast gate; they gain no fallback.
    for data in (before, after):
        paint = data.get('paint')
        if (not isinstance(paint, dict) or not paint.get('layers') or
                paint.get('error') is not None or paint.get('transitions') != []):
            raise RuntimeError('Native version-title capture has active or unknown paint state')
    if before != after:
        raise RuntimeError('Native version-title DOM or paint changed across the PNG capture')


def check_version_title_capture(data, expected, require_navigation=True):
    # Native scientific content remains entirely in HTML; only these shared,
    # deferred navigation/search scripts may be present on the surrounding page.
    chrome_scripts = [dict(src='../../../assets/' + name, defer=True, inline='')
                      for name in ('catalog-navigation.js', 'presentation.js', 'interface.js', 'chrome.js')]
    if (data['screenKind'] != 'native_version_title' or data['position'] != expected['position'] or
            data['ancestors'] != expected['ancestors'] or
            data['ancestorOpen'] != [True] * len(expected['ancestors']) or
            data['linkCount'] != 1 or data['branchHref'] != expected['branch'] or
            data['pagePath'] != '/research/navigation/branches/index.html' or
            data['readyState'] != 'complete' or data['scriptCount'] != len(chrome_scripts) or
            data.get('scripts') != chrome_scripts or data['appPresent'] or
            data.get('sourceBinding') != expected or data.get('focusedSummary') is not True):
        raise RuntimeError('Version-title native occurrence, ancestry or source link is incorrect')
    actions = data.get('nativeActions', [])
    if (len(actions) != len(expected['ancestors']) or
            any(row['position'] != pid or type(row['beforeOpen']) is not bool or row['afterOpen'] is not True or
                row['clicked'] is not (not row['beforeOpen']) for row, pid in zip(actions, expected['ancestors'])) or
            actions[-1]['clicked'] is not True):
        raise RuntimeError('Version-title path was not opened by the original native summary controls')
    viewport = data['viewport']
    if ((viewport['width'], viewport['height']) not in VIEWPORTS or viewport['dpr'] != 1 or
            data['bodyWidth'] > viewport['width'] + 1 or data['windowScroll'] < 0 or data['fonts'] != 'loaded'):
        raise RuntimeError('Version-title page bounds or actual font readiness failed')
    proof = data['title']
    area = dict(x=0, y=0, width=viewport['width'], height=viewport['height'])
    if (proof['viewport'] != area or not rect_inside(proof['readerContent'], area) or
            proof['fontSize'] < 16 or any(run['fontSize'] < 16 for run in proof['textRuns'])):
        raise RuntimeError('Version-title full text must use unshrunk native 16px type inside the actual viewport')
    if proof['textOverflow'] == 'ellipsis' or proof['lineClamp'] not in ('none', '0', ''):
        raise RuntimeError('Version-title text was ellipsized or line-clamped')
    check_task_route_proof(proof, expected['title'])
    if (data.get('pngDimensions') != [viewport['width'], viewport['height']] or
            not data.get('pixelVariation') or not re.fullmatch('[a-f0-9]{64}', data.get('screenshotSha256', '')) or
            not any(font.get('glyphCount', 0) > 0 for font in data.get('renderedFonts', []))):
        raise RuntimeError('Version-title screenshot or rendered-font evidence is incomplete')
    if any(item.get('level') == 'SEVERE' for item in data['console']) or data['networkFailures']:
        raise RuntimeError('Version-title page has browser or resource failures')
    if require_navigation:
        nav = data.get('enhancedNavigation', {})
        if (nav.get('branchPath') != '/research/navigation/branches/' + expected['branch'] or
                nav.get('branchTitle') != expected['title'] or nav.get('enhancedHref') != expected['enhancedHref'] or
                nav.get('route') != expected['route'] or nav.get('ready') is not True or
                nav.get('sourcePosition') != expected['sourcePosition'] or nav.get('entity') != expected['entity'] or
                nav.get('label') != expected['title'] or nav.get('sourceScope') != expected['sourceScope'] or
                nav.get('sourceLabel') != expected['sourceLabel']):
            raise RuntimeError('Native version-title link did not select the exact enhanced source identity')
        if any(item.get('level') == 'SEVERE' for item in nav['console']) or nav['networkFailures']:
            raise RuntimeError('Version-title source navigation has browser or resource failures')


def version_title_browser_logs(driver):
    console = driver.call('POST', '/log', {'type': 'browser'})
    failures = []
    for entry in driver.call('POST', '/log', {'type': 'performance'}):
        message = json.loads(entry['message'])['message']
        if message['method'] == 'Network.loadingFailed':
            p = message['params']
            failures.append({'type': p.get('type'), 'error': p.get('errorText'), 'cancelled': p.get('canceled', False)})
        elif message['method'] == 'Network.responseReceived' and message['params']['response']['status'] >= 400:
            response = message['params']['response']
            failures.append({'status': response['status'], 'path': urllib.parse.urlsplit(response['url']).path})
    return console, failures


def version_title_checks(driver, report, save, prefix, base, science, out):
    cases = version_title_expected(science)
    record = {'viewport': prefix, 'surface': 'script_free_native_global_tree', 'cases': []}
    report.setdefault('versionTitleChecks', []).append(record)
    save()
    for expected in cases:
        driver.call('POST', '/url', {'url': base + 'branches/index.html'})
        driver.settle()
        actions = []
        for pid in expected['ancestors']:
            selector = '[data-native-position="' + pid + '"]'
            before = driver.js("var n=document.querySelectorAll(arguments[0]);if(n.length!==1)throw Error('Native position missing or duplicated');return n[0].open;", selector)
            if not before:
                driver.click(driver.selector(selector + ' > summary'))
                driver.settle()
            after = driver.js('return document.querySelector(arguments[0]).open;', selector)
            if after is not True: raise RuntimeError('Native summary did not expand through its real control')
            actions.append({'position': pid, 'beforeOpen': before, 'afterOpen': after, 'clicked': not before})
        summary_selector = '[data-native-position="' + expected['position'] + '"] > summary'
        driver.js("arguments[0].scrollIntoView({block:'center',inline:'nearest'});", driver.selector(summary_selector))
        driver.settle()
        root_node = driver.cdp('DOM.getDocument', {'depth': 1})['root']['nodeId']
        title_node = driver.cdp('DOM.querySelector', {'nodeId': root_node, 'selector': summary_selector})['nodeId']
        rendered_fonts = driver.cdp('CSS.getPlatformFontsForNode', {'nodeId': title_node})['fonts']
        settle_version_title_paint(driver, report, save, prefix + expected['suffix'], summary_selector)
        data = driver.js(VERSION_TITLE_SNAPSHOT_JS, expected)
        before_capture = dict(data)
        image = base64.b64decode(driver.call('GET', '/screenshot'), validate=True)
        try:
            after_capture = driver.js(VERSION_TITLE_SNAPSHOT_JS, expected)
        except Exception as exc:
            # A disappearing/duplicated summary must retain the PNG and pre-proof
            # already obtained. The unavailable post-proof always fails below.
            after_capture = {'snapshotError': str(exc)}
        data.update(name=prefix + expected['suffix'], sourceBinding=expected, nativeActions=actions,
                    captureAfter=after_capture, renderedFonts=rendered_fonts)
        if not image.startswith(b'\x89PNG\r\n\x1a\n'): raise RuntimeError('Version-title screenshot is not PNG')
        data['pngDimensions'] = list(struct.unpack('>II', image[16:24]))
        data['screenshotSha256'] = hashlib.sha256(image).hexdigest()
        data['pixelVariation'] = png_has_visible_variation(image)
        data['console'], data['networkFailures'] = version_title_browser_logs(driver)
        (out / (data['name'] + '.png')).write_bytes(image)
        report['captures'].append(data)
        record['cases'].append(data)
        save()
        check_version_title_capture_stability(before_capture, after_capture)
        check_version_title_capture(data, expected, require_navigation=False)
        link_selector = '[data-native-position="' + expected['position'] + '"] > .native-body > p > a'
        driver.click(driver.selector(link_selector))
        driver.settle()
        nav = driver.js("var links=[...document.querySelectorAll('main > p > a')].filter(a=>a.getAttribute('href')===arguments[0]);return {branchPath:location.pathname,branchTitle:document.querySelector('main > h1')?.textContent,enhancedHref:links.length===1?links[0].getAttribute('href'):null};", expected['enhancedHref'])
        if (nav['branchPath'] != '/research/navigation/branches/' + expected['branch'] or
                nav['branchTitle'] != expected['title'] or nav['enhancedHref'] != expected['enhancedHref']):
            raise RuntimeError('Native title branch does not retain its exact reviewed title and source link')
        control = driver.js("return [...document.querySelectorAll('main > p > a')].find(a=>a.getAttribute('href')===arguments[0]);", expected['enhancedHref'])
        driver.click(control)
        wait_for(lambda: driver.js("var a=window.NavigationProductApp;if(!a)return false;var r=a.getState().route;return r.node===arguments[0]&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'&&a.getContent().ready(a.getBundle().positions[r.node].entityId);", expected['position']))
        driver.settle()
        nav.update(driver.js("var a=NavigationProductApp,r=a.getState().route,p=a.getBundle().positions[r.node];return {route:r,ready:a.getContent().ready(p.entityId),sourcePosition:p.sourcePositionId,entity:p.entityId,label:p.label,sourceScope:p.sourceScopeId,sourceLabel:p.sourceLabel};"))
        nav['console'], nav['networkFailures'] = version_title_browser_logs(driver)
        data['enhancedNavigation'] = nav
        check_version_title_capture(data, expected)
        save()


DISCLOSURE_AUDIT_SECONDS = 420
DISCLOSURE_IDS = tuple(row[0] for row in S0_TOOLBAR_LABELS if row[1] == 'DETAILS')
DISCLOSURE_NOTES_END = '地图中的区域与邻近位置只按已有目标输入、完成要求和过程属性组织阅读，不是科学父类。实线保持原目录父子；虚线分别表示已有对照、按序组合或目标类型构成，不表示方法继承。'
DISCLOSURE_RELATIONS_END = '这些是已有的非树关系；没有据此增加科学父节点，也没有预选一条示范主线。'


def disclosure_expected(science):
    """Original directory order is reconstructed from frozen source, not tested DOM."""
    scopes = {row['id']: row for row in science['scopes']}
    directory, seen = [], set()
    def visit(identity):
        if identity in seen:
            return
        if identity not in scopes:
            raise RuntimeError('Disclosure source directory has a missing scope')
        seen.add(identity); row = scopes[identity]
        directory.append({'scope': identity, 'parent': row.get('parentScopeId') or '',
                          'text': row['label'] + ' · ' + (row.get('displayRole') or row['kind'])})
        for child in row.get('childScopeIds', []):
            visit(child)
    for group in science['directoryGroups']:
        for identity in group['scopeIds']:
            visit(identity)
    for row in science['scopes']:
        if row['id'] != 'scope:all':
            visit(row['id'])
    visit('scope:all')
    if len(directory) != 64 or directory[-1]['scope'] != 'scope:all':
        raise RuntimeError('Disclosure source directory lost its original 64-entry boundary')
    last = TASK_INDEX[-1][0]
    if last != 'task:language-objectnav':
        raise RuntimeError('Reviewed final comparison source changed')
    scope = scopes[last]
    coverage = scope['coverage']
    def status(field):
        return '有直接关联' if coverage.get('direct', {}).get(field) else '仅条件关联' if coverage.get('condition', {}).get(field) else '当前未整理'
    row = '[data-task-comparison="' + last + '"]'
    comparison = [
        {'selector': row + ' > td:first-child > button', 'text': scope['label']},
        {'selector': row + ' > td:first-child > p', 'text': scope.get('displayRole') or scope['kind']},
        {'selector': row + ' > [data-task-field="input"]', 'text': '目标物体或实例描述'},
        {'selector': row + ' > [data-task-field="completion"]', 'text': '自主搜索符合描述的目标'},
        {'selector': row + ' > [data-task-field="boundary"]', 'text': '不是路线指令；现有方法/CI仅条件关联，预建图、楼层/房间条件不得隐藏。'},
        {'selector': row + ' > [data-task-field="sources"] > p:first-child', 'text': status('methodCount') + ' / ' + status('challengeCount')},
    ]
    for index, (version, url) in enumerate((('arxiv:2203.10421v2', 'https://arxiv.org/html/2203.10421v2'),
                                           ('source:src_ef717861b303', 'https://arxiv.org/html/2512.22342v5')), 2):
        base = row + ' > [data-task-field="sources"] > p:nth-child(' + str(index) + ')'
        comparison.extend([{'selector': base + ' > a', 'text': version, 'url': url},
                           {'selector': base + ' > span', 'text': ' · 固定来源版本'}])
    return {'directory': directory, 'comparisonOrder': [item[0] for item in TASK_INDEX], 'comparisonLast': last,
            'targets': {'np-all-scopes': [{'selector': '[data-scope-open="' + item['scope'] + '"]', 'text': item['text']}
                                          for item in (directory[0], directory[-1])],
                        'np-overview-comparison': comparison,
                        'np-task-relations': [{'selector': ':scope > p:last-child', 'text': DISCLOSURE_RELATIONS_END}],
                        'np-overview-notes': [{'selector': ':scope > p.np-index-boundary:last-child', 'text': DISCLOSURE_NOTES_END}]}}


DISCLOSURE_SNAPSHOT_JS = VISUAL_GEOMETRY + FIXED_TEXT_PROOF_JS + STATIONARY_SHELL_ANCESTORS_JS + r"""
var requested=arguments[0],specs=arguments[1],a=NavigationProductApp,s=a.getState(),landing=document.getElementById('np-reading-landing'),toolbar=landing.querySelector(':scope > .np-overview-map-toolbar');
function frame(e){var r=rect(e),cs=getComputedStyle(e);return {id:e.id,tag:e.tagName,open:!!e.open,rect:r,
 clientRect:{x:r.x+e.clientLeft,y:r.y+e.clientTop,width:e.clientWidth,height:e.clientHeight},top:e.scrollTop,left:e.scrollLeft,
 scrollHeight:e.scrollHeight,clientHeight:e.clientHeight,scrollWidth:e.scrollWidth,clientWidth:e.clientWidth,maxTop:Math.max(0,e.scrollHeight-e.clientHeight),
 overflowX:cs.overflowX,overflowY:cs.overflowY,paddingBottom:parseFloat(cs.paddingBottom),maxHeight:cs.maxHeight,
 borderTop:parseFloat(cs.borderTopWidth),borderRight:parseFloat(cs.borderRightWidth),borderBottom:parseFloat(cs.borderBottomWidth),borderLeft:parseFloat(cs.borderLeftWidth),
 opaque:box(e).opaque,unscaled:box(e).unscaled};}
function identity(e){return {id:e?.id||'',tag:e?.tagName||'',summaryFor:e?.tagName==='SUMMARY'?e.parentElement.id:null,scope:e?.dataset.scopeOpen||null};}
var panels=[...toolbar.querySelectorAll(':scope > details')],panel=panels.find(e=>e.id===requested),active=document.activeElement;
function target(spec){var matches=panel?[...panel.querySelectorAll(spec.selector)]:[],e=matches[0],suffix=null;
 if(!e)return {selector:spec.selector,count:matches.length};
 if(spec.url){var suffixes=e.querySelectorAll(':scope > span.np-sr');suffix=suffixes.length===1?suffixes[0]:null;
  if(e.tagName!=='A'||!suffix||suffix!==e.lastChild||suffix.textContent!=='（新标签页）'||suffix.children.length)throw Error('Disclosure source link lost its exact accessibility suffix');}
 var p=fixedTextProof(e,suffix);if(suffix)p.text=p.renderedText;
 return {selector:spec.selector,count:matches.length,tag:e.tagName,id:e.id,scope:e.dataset.scopeOpen||null,disabled:!!e.disabled,tabIndex:e.tabIndex,
  panel:e.closest('.np-overview-map-toolbar > details')?.id,url:e.tagName==='A'?e.href:null,proof:p};}
return {ready:document.getElementById('navigation-product').dataset.loadState,home:!landing.hidden,route:s.route,
 historyRoute:history.state&&history.state[NavigationProductModel.KEY]?.route,historyLength:history.length,scale:NavigationProductModel.getBucket(s).graphScale,
 originTrail:s.originTrail,historyOriginTrail:history.state&&history.state[NavigationProductModel.KEY]?.originTrail,
 expanded:NavigationProductModel.getBucket(s).expandedByTree,selected:NavigationProductModel.getBucket(s).selectedByTree,
 selectedRelation:document.getElementById('np-overview-map').dataset.selectedRelation||null,
 window:{x:scrollX,y:scrollY},viewport:{x:0,y:0,width:innerWidth,height:innerHeight},stationaryAncestors:stationaryShellAncestors(),
 landing:frame(landing),toolbar:frame(toolbar),panels:panels.map(e=>Object.assign(frame(e),{count:document.querySelectorAll('[id="'+e.id+'"]').length,
  topology:e.parentElement===toolbar,summary:fixedTextProof(e.querySelector(':scope > summary'))})),focus:identity(active),
 directory:[...document.querySelectorAll('#np-all-scopes [data-scope-open]')].map(e=>({scope:e.dataset.scopeOpen,parent:e.parentElement.dataset.parentScope,
  domParent:e.parentElement.parentElement.closest('[data-directory-scope]')?.dataset.directoryScope||'',text:e.textContent,id:e.id,tag:e.tagName,type:e.type,disabled:e.disabled,tabIndex:e.tabIndex})),
 comparisonOrder:[...document.querySelectorAll('#np-overview-comparison [data-task-comparison]')].map(e=>e.dataset.taskComparison),
 comparisonLast:panel?.id==='np-overview-comparison'?{id:panel.querySelector('tr:last-child')?.dataset.taskComparison,cells:panel.querySelector('tr:last-child')?.children.length,rect:rect(panel.querySelector('tr:last-child'))}:null,
 requested:requested,targets:specs.map(target)};
"""

DISCLOSURE_PROBE_JS = r"""
var mode=arguments[0],slot='__npDisclosureAudit',owner=arguments[mode==='start'?2:1];
if(typeof owner!=='string'||!owner)throw Error('Disclosure audit probe lacks its owner');
function identity(e){return {id:e?.id||'',tag:e?.tagName||'',summaryFor:e?.tagName==='SUMMARY'?e.parentElement.id:null,scope:e?.dataset.scopeOpen||null};}
if(mode==='start'){
 if(window[slot])throw Error('Disclosure audit probe already installed');
 var p={owner:owner,events:[],overflow:0,limit:arguments[1]};p.listener=function(e){if(p.events.length>=p.limit){p.overflow++;return;}
  p.events.push({type:e.type,key:e.key||null,trusted:e.isTrusted,target:identity(e.target),panel:e.target.closest?.('.np-overview-map-toolbar > details')?.id||null});};
 window[slot]=p;for(var kind of ['keydown','keyup','focusin','wheel','scroll','click'])document.addEventListener(kind,p.listener,true);return true;
}
var p=window[slot];
if(!p&&mode==='stop')return {owner:owner,events:[],overflow:0,limit:0,cleanedUp:true,absent:true};
if(!p)throw Error('Disclosure audit probe is missing');
if(p.owner!==owner)throw Error('Disclosure audit cannot access another observer owner');
if(mode==='reset'){p.events=[];p.overflow=0;return true;}
try{return {owner:owner,events:p.events,overflow:p.overflow,limit:p.limit,cleanedUp:mode==='stop',absent:false};}
finally{if(mode==='stop'){for(var kind of ['keydown','keyup','focusin','wheel','scroll','click'])document.removeEventListener(kind,p.listener,true);delete window[slot];}}
"""


def check_disclosure_scroll_metrics(panel):
    """CSSOM offsets are double; the integer extent is only a rounding sanity bound."""
    values = [panel.get(k) for k in ('top', 'left', 'scrollHeight', 'clientHeight', 'maxTop')]
    if (not all(type(n) in (int, float) and math.isfinite(n) for n in values) or
            panel['scrollHeight'] < 0 or panel['clientHeight'] <= 0 or
            any(int(panel[k]) != panel[k] for k in ('scrollHeight', 'clientHeight')) or
            panel['top'] < 0 or panel['maxTop'] != max(0, panel['scrollHeight'] - panel['clientHeight']) or
            panel['top'] - panel['maxTop'] >= 1):
        raise RuntimeError('Disclosure lacks consistent CSSOM double offsets and rounded integer extents')


def check_disclosure_snapshot(data, expected, baseline=None):
    if (data['ready'] != 'ready' or not data['home'] or data['window'] != {'x': 0, 'y': 0} or
            (data['viewport']['width'], data['viewport']['height']) not in VIEWPORTS or data['scale'] != 1 or
            data['landing']['top'] != 0 or data['landing']['left'] != 0 or
            data['historyRoute'] != data['route'] or [p['id'] for p in data['panels']] != list(DISCLOSURE_IDS)):
        raise RuntimeError('Disclosure audit lost the exact stationary desktop home')
    check_stationary_shell_ancestors(data['stationaryAncestors'])
    actual = data['directory']
    if len(actual) != len(expected['directory']):
        raise RuntimeError('Disclosure audit lost the complete source directory')
    for row, source in zip(actual, expected['directory']):
        if (any(row.get(key) != value for key, value in source.items()) or row.get('domParent') != source['parent'] or
                row.get('id') != 'np-scope-entry-' + source['scope'] or row.get('tag') != 'BUTTON' or
                row.get('type') != 'button' or row.get('disabled') or row.get('tabIndex') != 0):
            raise RuntimeError('Disclosure audit changed a source directory label, order, parent or native control')
    if data['comparisonOrder'] != expected['comparisonOrder']:
        raise RuntimeError('Disclosure audit changed the original comparison order')
    if baseline:
        for key in ('route', 'historyRoute', 'historyLength', 'scale', 'window', 'originTrail', 'historyOriginTrail', 'expanded', 'selected', 'selectedRelation'):
            if data[key] != baseline[key]:
                raise RuntimeError('Disclosure input changed source/history identity: ' + key)
        for key in ('landing', 'toolbar'):
            if data[key]['rect'] != baseline[key]['rect']:
                raise RuntimeError('Disclosure input moved the original landing or toolbar')
    for panel in data['panels']:
        if panel['count'] != 1 or panel['tag'] != 'DETAILS' or not panel['topology']:
            raise RuntimeError('Disclosure audit lost an original native toolbar details')
        if not panel['open']:
            continue
        check_disclosure_scroll_metrics(panel)
        landing = data['landing']; bounds = landing['rect']
        inner = dict(x=bounds['x'] + landing['borderLeft'], y=bounds['y'] + landing['borderTop'],
                     width=bounds['width'] - landing['borderLeft'] - landing['borderRight'],
                     height=bounds['height'] - landing['borderTop'] - landing['borderBottom'] - landing['paddingBottom'])
        room = min(data['viewport']['height'], inner['y'] + inner['height']) - panel['rect']['y']
        cap = min(324 if panel['id'] == 'np-task-relations' else data['viewport']['height'] - 240, room)
        if (not math.isfinite(cap) or cap <= 0 or
                panel['rect']['height'] > cap + S0_SPACING_TOLERANCE or not panel['opaque'] or not panel['unscaled'] or
                not rect_inside(panel['rect'], inner, S0_SPACING_TOLERANCE) or
                not rect_inside(panel['rect'], data['viewport'], S0_SPACING_TOLERANCE) or
                panel['left'] != 0 or panel['scrollWidth'] > panel['clientWidth'] + 1 or panel['overflowY'] not in ('auto', 'scroll')):
            raise RuntimeError('Toolbar disclosure exceeds its independent actual available-height cap or clipping bounds')


def check_disclosure_targets(data, expected, indexes=None):
    panel = next(p for p in data['panels'] if p['id'] == data['requested'])
    specs = expected['targets'][panel['id']]
    if not panel['open'] or len(data['targets']) != len(specs):
        raise RuntimeError('Disclosure reachability proof lost its open original target set')
    for index in range(len(specs)) if indexes is None else indexes:
        actual, spec = data['targets'][index], specs[index]
        if (actual.get('selector') != spec['selector'] or actual.get('count') != 1 or actual.get('panel') != panel['id'] or
                spec.get('url') and (actual.get('tag') != 'A' or actual.get('url') != spec['url'])):
            raise RuntimeError('Disclosure reachability proof substituted or duplicated an original target')
        for paint in [actual['proof'], *actual['proof']['textRuns']]:
            for field in ('foreground', 'background'):
                color = paint.get(field)
                if (not isinstance(color, list) or len(color) != 3 or
                        any(type(v) not in (int, float) or not math.isfinite(v) or not 0 <= v <= 255 for v in color)):
                    raise RuntimeError('Disclosure text has unknown or invalid actual paint')
        check_s0_text(actual['proof'], spec['text'], panel['clientRect'], data['landing']['clientRect'], data['viewport'])
    if panel['id'] == 'np-overview-comparison':
        row = data['comparisonLast']
        if (row['id'] != expected['comparisonLast'] or row['cells'] != 5 or
                not rect_inside(row['rect'], panel['clientRect']) or not rect_inside(row['rect'], data['viewport'])):
            raise RuntimeError('Complete final comparison row is not reachable inside its disclosure')


def check_disclosure_action(item, expected):
    before, after, trace = item['before'], item['after'], item['events']
    check_disclosure_snapshot(after, expected, before)
    if (trace['limit'] != 4 * (len(expected['directory']) + 1) + 16 or trace['overflow'] or
            len(trace['events']) > trace['limit'] or any(event.get('trusted') is not True for event in trace['events'])):
        raise RuntimeError('Disclosure input lost its bounded trusted native trace')
    panel_id = item['panel']
    b = next(p for p in before['panels'] if p['id'] == panel_id)
    a = next(p for p in after['panels'] if p['id'] == panel_id)
    if item['kind'] in ('wheel', 'wheel-boundary'):
        check_disclosure_scroll_metrics(b)
        if (not b['open'] or not a['open'] or b['maxTop'] != a['maxTop'] or b['clientRect'] != a['clientRect'] or
                type(item['delta']) is not int or item['delta'] == 0 or before['focus'] != after['focus'] or
                not any(e['type'] == 'wheel' and e['panel'] == panel_id for e in trace['events'])):
            raise RuntimeError('Disclosure wheel lost its real isolated native input')
        if item['kind'] == 'wheel':
            if ((a['top'] - b['top']) * item['delta'] <= 0 or
                    not any(e['type'] == 'scroll' and e['target']['id'] == panel_id for e in trace['events'])):
                raise RuntimeError('Disclosure wheel did not produce real isolated internal progress')
        elif (item['delta'] <= 0 or a['top'] != b['top'] or abs(a['top'] - a['maxTop']) >= 1):
            raise RuntimeError('Disclosure native end overshoot did not remain at a stable real boundary')
    elif item['kind'] in ('tab', 'escape'):
        key = 'Tab' if item['kind'] == 'tab' else 'Escape'
        keys = [e for e in trace['events'] if e['type'] in ('keydown', 'keyup')]
        count = item.get('count', 1)
        if (type(count) is not int or count < 1 or count > len(expected['directory']) + 1 or
                len(keys) != count * 2 or [e['type'] for e in keys] != ['keydown', 'keyup'] * count or
                any(e['key'] != key for e in keys)):
            raise RuntimeError('Disclosure keyboard trace is missing the exact native key sequence')
        if item['kind'] == 'escape':
            if not b['open'] or a['open'] or after['focus']['summaryFor'] != panel_id or keys[0]['target'] != before['focus']:
                raise RuntimeError('Disclosure Escape lost its closed state or exact summary focus')
            label = next(row[2] for row in S0_TOOLBAR_LABELS if row[0] == panel_id)
            check_chrome_text(a['summary'], label, 15, after['landing']['clientRect'], after['viewport'])
        else:
            wanted = item['scopes']
            focuses = [e['target']['scope'] for e in trace['events'] if e['type'] == 'focusin']
            if (count != len(wanted) or focuses != wanted or [e['target']['scope'] for e in keys if e['type'] == 'keyup'] != wanted or
                    after['focus']['scope'] != wanted[-1] or not a['open']):
                raise RuntimeError('Native Tab did not reach the exact source-bound directory path')
    elif item['kind'] == 'open':
        if (b['open'] or not a['open'] or after['focus']['summaryFor'] != panel_id or
                not any(e['type'] == 'click' and e['target']['summaryFor'] == panel_id for e in trace['events'])):
            raise RuntimeError('Native summary click did not open the exact disclosure with focus')
    else:
        raise RuntimeError('Unsupported disclosure audit action')
    for other_before, other_after in zip(before['panels'], after['panels']):
        if other_before['id'] != panel_id and any(other_before[key] != other_after[key] for key in ('open', 'top', 'left')):
            raise RuntimeError('Disclosure input changed another toolbar panel')


class DisclosureBudgetDriver(Driver):
    """Only this additional audit uses the remaining deadline; normal Driver is unchanged."""
    def __init__(self, driver, deadline):
        self.url, self.session, self.deadline = driver.url, driver.session, deadline

    def remaining(self):
        remaining = self.deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError('Disclosure audit exceeded its fixed ' + str(DISCLOSURE_AUDIT_SECONDS) + '-second input/checkpoint budget')
        return remaining

    def request(self, method, path, data=None):
        raw = None if data is None else json.dumps(data).encode()
        req = urllib.request.Request(self.url + path, data=raw, method=method, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=min(50, self.remaining())) as response:
            value = json.load(response)['value']
        self.remaining()
        if isinstance(value, dict) and value.get('error'):
            raise RuntimeError(value['error'] + ': ' + value.get('message', ''))
        return value


class DisclosureCheckpointSave:
    """Measure every unchanged checkpoint call, including the reused paint helper."""
    def __init__(self, callback, record):
        self.callback, self.record = callback, record

    def __call__(self):
        timing = self.record['checkpointTiming']
        timing['attempts'] += 1; timing['inProgress'] = True
        started = time.monotonic()
        try:
            self.callback()
            timing['completed'] += 1
        finally:
            timing['seconds'] += time.monotonic() - started
            timing['inProgress'] = False


def disclosure_bounds_checks(driver, report, save, prefix, science):
    """Additional native interaction evidence after the existing -12 PNG; no new scene."""
    expected = disclosure_expected(science)
    record = {'viewport': prefix, 'budgetSeconds': DISCLOSURE_AUDIT_SECONDS, 'expected': expected, 'actions': [], 'proofs': [],
              'tabLimit': len(expected['directory']) + 1, 'wheelLimitPerPanel': 4, 'status': 'started',
              'checkpointTiming': {'attempts': 0, 'completed': 0, 'seconds': 0.0, 'inProgress': False}, 'budgetExhausted': False}
    started = time.monotonic(); bounded = DisclosureBudgetDriver(driver, started + DISCLOSURE_AUDIT_SECONDS)
    report.setdefault('disclosureBoundsChecks', []).append(record)
    save = DisclosureCheckpointSave(save, record)
    attempted = False; owner = prefix + ':' + str(started)
    record['probeOwner'] = owner; record['probeStartAcknowledged'] = False
    def snapshot(identity):
        return bounded.js(DISCLOSURE_SNAPSHOT_JS, identity, expected['targets'][identity])
    def action(kind, identity, perform, **fields):
        before = snapshot(identity)
        item = dict(kind=kind, panel=identity, before=before, status='pending', actionAcknowledged=False, **fields)
        record['actions'].append(item); bounded.remaining(); save(); bounded.remaining()
        bounded.js(DISCLOSURE_PROBE_JS, 'reset', owner)
        try:
            input_started = time.monotonic()
            try:
                perform()
            finally:
                item['nativeActionSeconds'] = time.monotonic() - input_started
            item['actionAcknowledged'] = True; bounded.settle()
            settle_s0_toolbar_paint(bounded, report, save, prefix + '-disclosure-' + str(len(record['actions'])))
            bounded.remaining()
        except Exception as exc:
            item['actionError'] = str(exc)[:2000]
            raise
        finally:
            for key, script, args in (('events', DISCLOSURE_PROBE_JS, ['read', owner]),
                                      ('after', DISCLOSURE_SNAPSHOT_JS, [identity, expected['targets'][identity]])):
                try:
                    item[key] = (driver if 'actionError' in item else bounded).js(script, *args)
                except Exception as exc:
                    item[key + 'Error'] = str(exc)[:2000]
                    if 'actionError' not in item:
                        item['actionError'] = str(exc)[:2000]
            try:
                save()
                if 'actionError' not in item:
                    bounded.remaining()
            except Exception as exc:
                item['checkpointError'] = str(exc)[:2000]
                if 'actionError' not in item:
                    raise
        if 'actionError' in item:
            raise RuntimeError(item['actionError'])
        check_disclosure_action(item, expected)
        item['status'] = 'verified'; save(); bounded.remaining()
        return item['after']
    def key(identity, kind, scopes=None):
        values = scopes or [None]
        count = len(values)
        if kind == 'tab' and sum(a.get('count', 0) for a in record['actions'] if a['kind'] == 'tab') + count > record['tabLimit']:
            raise RuntimeError('Disclosure audit exceeded its source-bound native Tab limit')
        code = '\ue004' if kind == 'tab' else '\ue00c'
        sequence = [{'type': kind_, 'value': code} for _ in values for kind_ in ('keyDown', 'keyUp')]
        return action(kind, identity, lambda: bounded.call('POST', '/actions', {'actions': [
            {'type': 'key', 'id': 'toolbar-disclosure-keyboard', 'actions': sequence}]}), count=count, scopes=scopes)
    def wheel_to(identity, boundary):
        before = snapshot(identity); panel = next(p for p in before['panels'] if p['id'] == identity)
        check_disclosure_scroll_metrics(panel)
        if boundary not in ('start', 'end'):
            raise RuntimeError('Disclosure wheel requires a reviewed real boundary')
        if boundary == 'start' and panel['top'] == 0 or boundary == 'end' and panel['maxTop'] == 0 and panel['top'] == 0:
            return before
        # Integers scrollHeight/clientHeight are not the exact double endpoint.
        # A full-content native overshoot reaches it; a second same-direction
        # input must then leave the actual offset exactly stable. Tail proof is
        # checked separately before any success is claimed.
        delta = math.ceil(panel['scrollHeight'] + abs(panel['top']) + 1) * (-1 if boundary == 'start' else 1)
        for kind in (('wheel',) if boundary == 'start' else ('wheel', 'wheel-boundary')):
            if sum(a['kind'] in ('wheel', 'wheel-boundary') and a['panel'] == identity for a in record['actions']) >= record['wheelLimitPerPanel']:
                raise RuntimeError('Disclosure audit exceeded its bounded native wheel steps')
            r = panel['clientRect']; x, y = math.floor(r['x'] + r['width'] / 2), math.floor(r['y'] + r['height'] / 2)
            after = action(kind, identity, lambda: bounded.call('POST', '/actions', {'actions': [
                {'type': 'wheel', 'id': 'toolbar-disclosure-scroll', 'actions': [{'type': 'scroll', 'origin': 'viewport',
                 'x': x, 'y': y, 'deltaX': 0, 'deltaY': delta, 'duration': 100}]}]}), delta=delta)
            panel = next(p for p in after['panels'] if p['id'] == identity)
            if boundary == 'start' and panel['top'] != 0 or boundary == 'end' and abs(panel['top'] - panel['maxTop']) >= 1:
                raise RuntimeError('Native disclosure wheel did not reach its real content boundary')
        return after
    def proof(data, indexes=None):
        record['proofs'].append({'panel': data['requested'], 'indexes': indexes, 'snapshot': data}); save(); bounded.remaining()
        check_disclosure_targets(data, expected, indexes)
    try:
        save(); bounded.remaining()
        attempted = True
        bounded.js(DISCLOSURE_PROBE_JS, 'start', 4 * record['tabLimit'] + 16, owner)
        record['probeStartAcknowledged'] = True
        baseline = record['initial'] = snapshot('np-all-scopes'); save(); bounded.remaining(); check_disclosure_snapshot(baseline, expected)
        if ([p['id'] for p in baseline['panels'] if p['open']] != ['np-all-scopes'] or
                baseline['focus']['scope'] != 'task:dialnav'):
            raise RuntimeError('Disclosure audit must start after the unchanged original directory-return scene')
        key('np-all-scopes', 'escape')
        for identity in DISCLOSURE_IDS:
            opened = action('open', identity, lambda identity=identity: bounded.click(bounded.selector('#' + identity + ' > summary')))
            check_disclosure_snapshot(opened, expected, baseline)
            current = wheel_to(identity, 'start')
            if identity == 'np-all-scopes':
                current = key(identity, 'tab', [expected['directory'][0]['scope']]); proof(current, [0])
            bottom = wheel_to(identity, 'end')
            proof(bottom, [1] if identity == 'np-all-scopes' else None)
            if identity == 'np-all-scopes':
                wheel_to(identity, 'start')
                last = key(identity, 'tab', [row['scope'] for row in expected['directory'][1:]])
                proof(last, [1])
            key(identity, 'escape')
        final = record['final'] = snapshot('np-all-scopes'); save(); bounded.remaining(); check_disclosure_snapshot(final, expected, baseline)
        if any(p['open'] for p in final['panels']):
            raise RuntimeError('Disclosure audit did not leave all temporary menus natively closed')
        bounded.remaining(); record['status'] = 'native_bounds_and_reachability_verified'
    except Exception as exc:
        record['status'] = 'failed'; record['error'] = str(exc)[:2000]
        record['budgetExhausted'] = time.monotonic() >= started + DISCLOSURE_AUDIT_SECONDS
        raise
    finally:
        cleanup_started = time.monotonic()
        record['inputAndCheckpointElapsedSeconds'] = cleanup_started - started
        record['nativeActionSeconds'] = sum(a.get('nativeActionSeconds', 0) for a in record['actions'])
        try:
            if attempted:
                try:
                    record['cleanup'] = driver.js(DISCLOSURE_PROBE_JS, 'stop', owner)
                    if record['cleanup'].get('cleanedUp') is not True or record['cleanup'].get('owner') != owner:
                        raise RuntimeError('Disclosure native-input observer was not removed')
                except Exception as exc:
                    record['cleanupError'] = str(exc)[:2000]
                    if record['status'] != 'failed':
                        record['status'] = 'failed'; save(); raise
        finally:
            record['diagnosticCleanupSeconds'] = time.monotonic() - cleanup_started
            try:
                save()
                if record['status'] != 'failed':
                    bounded.remaining()
            except Exception as exc:
                record['terminalCheckpointError'] = str(exc)[:2000]
                record['budgetExhausted'] = time.monotonic() >= started + DISCLOSURE_AUDIT_SECONDS
                if record['status'] != 'failed':
                    record['status'] = 'failed'; record['error'] = str(exc)[:2000]
                    raise
            finally:
                record['totalObservedSeconds'] = time.monotonic() - started
                print('disclosure_audit ' + json.dumps({key: record[key] for key in (
                    'viewport', 'budgetSeconds', 'status', 'nativeActionSeconds', 'checkpointTiming',
                    'inputAndCheckpointElapsedSeconds', 'diagnosticCleanupSeconds', 'totalObservedSeconds', 'budgetExhausted')},
                    separators=(',', ':')), flush=True)


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
              'browserFullscreenRequested': False, 'displayContractMigrations': DISPLAY_CONTRACT_MIGRATIONS,
              's0FooterScope': {'sceneSuffixes': list(S0_FOOTER_SCENES), 'relations': 'all selections, per-source scrolling, native wheel, close, reload and endpoint Back',
                                'adaptiveSpacing': 'independent DOM/source reconstruction in designated S0 scenes, default/show-all and every existing S0 lifecycle check; actual map client dimensions and label/card proofs, with no controller spacing metadata',
                                'directoryReturn': 'Original -12 scene keeps its native glossary open; full-height/outer0 and all original gates remain, without requiring uncovered footer beneath that intentional overlay'},
              'capturePlan': [str(w) + 'x' + str(h) + suffix for w, h in VIEWPORTS for suffix in SCENE_NAMES]}
    report['frontendSources'] = {name: sha(name) for name in ('assets/navigation-product.js', 'assets/navigation-product-model.js', 'assets/navigation-product.css', 'scripts/navigation_product.py')}
    report['captureSources'] = {name: sha(name) for name in ('scripts/navigation_screenshots.py', 'tests/test_navigation_screenshots.py', 'tests/test_navigation_disclosure_bounds.py')}
    report['servedFiles'] = {str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'research/navigation').rglob('*')) if p.is_file()}
    report['servedFiles'].update({str(p.relative_to(dist)): sha(p) for p in sorted((dist / 'assets').glob('navigation-*.js'))})
    report['servedFiles']['assets/navigation-product.css'] = sha(dist / 'assets/navigation-product.css')
    if report['scienceSha256'] != '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c':
        raise RuntimeError('Screenshot scientific identity differs from reviewed9069 source')
    science = json.loads((dist / 'research/navigation/product-data.json').read_text())
    from navigation_research_map import build_research_map
    method_positions = dict(science['positions'])
    method_positions.update(build_research_map(science)['positions'])
    footer_expected = s0_footer_expected(science)
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
                refs.append({'sourceId': sid, 'url': ref['url'], 'versionId': ref['versionId'], 'versionStatus': ref['versionStatus'], 'descriptor': ref.get('descriptor')})
        relation_expected.append({'id': rel['id'], 'from': rel['from'], 'to': rel['to'], 'relationType': rel['relationType'], 'locators': rel['detail']['locators'], 'sourceRefs': refs})
    driver = None
    process = None
    server = None
    logs = (out / 'chromedriver.log').open('w')
    # Preserve the original save wrapper and all checkpoint call sites.
    receipt_cache = ReceiptSnapshotCache(out / 'receipt.json')
    write_receipt = receipt_cache

    def save():
        write_receipt(out / 'receipt.json', report)

    def capture(name, require_tree=True, require_overview=False, require_flow=False, require_home=False):
        driver.settle()
        data = driver.js('''return {viewport:{width:innerWidth,height:innerHeight,dpr:devicePixelRatio},
          loadState:document.querySelector('[data-load-state]')?.dataset.loadState,
          route:window.NavigationProductApp?.getState().route,
          fonts:document.fonts.status, ready:!!window.NavigationProductApp,
          fallbackHidden:document.getElementById('np-static-reading')?.hidden,
          bounds:[...document.querySelectorAll(arguments[0])].map(e=>{let r=e.getBoundingClientRect();return {id:e.id,position:e.closest('[data-position]')?.dataset.position,text:e.textContent.slice(0,180),x:r.x,y:r.y,width:r.width,height:r.height};}),
          nodeCount:document.querySelectorAll('#np-tree [role=treeitem]').length,
          focus:document.activeElement?.id, bodyWidth:document.body.scrollWidth};''', CAPTURE_BOUNDS_SELECTOR)
        data['desktopShell'] = desktop_chrome_snapshot(driver, report, save, name, DESKTOP_SHELL_SNAPSHOT_JS)
        requires_s0_footer = s0_footer_required(name)
        data['s0FooterRequired'] = requires_s0_footer
        if data['desktopShell']['home'] and requires_s0_footer:
            data['desktopShell']['s0Footer'] = s0_footer_check(name)
        if data['desktopShell'].get('methodReading') == 'true' and not data['desktopShell']['collapsed']:
            data['methodReading'] = driver.js(METHOD_READING_SNAPSHOT_JS)
            method_expected = method_reading_expected(science, method_positions[data['route']['node']], method_positions)
            method_child_readability_checks(driver, report, save, name, data['methodReading'], method_expected, method_positions)
        data['screenKind'] = 'default_reading_overview' if require_home else 'tree_or_reader'
        data['readingVisibility'] = driver.js('''function rect(e){if(!e)return null;let r=e.getBoundingClientRect();return {x:r.x,y:r.y,width:r.width,height:r.height};}
          let a=NavigationProductApp,b=a.getBundle(),root=b.researchMap.roots[0];
          function color(value){let m=/^rgba?\\(([^)]+)\\)$/.exec(value);if(!m)return null;let v=m[1].split(',').map(Number);if(![3,4].includes(v.length)||v.some(n=>!Number.isFinite(n))||v.slice(0,3).some(n=>n<0||n>255))return null;return {rgb:v.slice(0,3),alpha:v.length===4?v[3]:1};}
          function foreground(e){let c=color(getComputedStyle(e).color);return c&&c.alpha===1?c.rgb:[];}
          function background(e){while(e){let c=color(getComputedStyle(e).backgroundColor);if(!c)return [];if(c.alpha===1)return c.rgb;if(c.alpha!==0)return [];e=e.parentElement;}return [255,255,255];}
          function opaqueVisible(e){while(e){let s=getComputedStyle(e);if(Number(s.opacity)!==1||s.visibility!=='visible'||s.display==='none')return false;e=e.parentElement;}return true;}
          let reader=document.getElementById('np-detail-scroll'),readerRect=rect(reader),heading=document.getElementById('np-reader-heading'),headingRect=rect(heading),contentTop=readerRect.y;
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
        check_desktop_shell(data['desktopShell'], require_s0_footer=requires_s0_footer)
        if 'methodReading' in data:
            method_expected = method_reading_expected(science, method_positions[data['route']['node']], method_positions)
            check_method_reading(data['methodReading'], method_expected, method_positions,
                                 compact=name.endswith(('-03-method-reader', '-03b-reader-visible', '-11-active-method-reader', '-11c-reader-reopened')))
        if not data['ready'] or data['loadState'] != 'ready' or not data['fallbackHidden'] or (not require_home and not data['nodeCount']) or data['fonts'] != 'loaded':
            raise RuntimeError('Blank, unready, or font-pending capture')
        if not data['pixelVariation']:
            raise RuntimeError('Screenshot has insufficient nonblank pixel variation')
        if any(e.get('level') == 'SEVERE' for e in data['console']):
            raise RuntimeError('Browser console contains severe errors')
        if data['networkFailures']:
            raise RuntimeError('Candidate resource request failed')
        check_capture_visible_regions(data, require_tree, require_home)
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

    def s0_footer_check(phase):
        settle_s0_toolbar_paint(driver, report, save, phase)
        data = desktop_chrome_snapshot(driver, report, save, phase, S0_FOOTER_SNAPSHOT_JS, footer_expected)
        report.setdefault('s0FooterChecks', []).append({'phase': phase, 'snapshot': data})
        save()
        check_s0_footer(data)
        return data

    def reading_home(relation_mode='default'):
        driver.settle()
        data = driver.js(VISUAL_GEOMETRY + """
          var a=NavigationProductApp,state=a.getState(),landing=document.getElementById('np-reading-landing');
          return {route:state.route,home:!landing.hidden,panelsHidden:document.querySelector('.np-panels').hidden,windowScroll:scrollY,landingScroll:landing.scrollTop,scale:NavigationProductModel.getBucket(state).graphScale,viewport:{x:0,y:0,width:innerWidth,height:innerHeight},landing:rect(landing),headings:[...landing.querySelectorAll('#np-overview-heading,[data-reading-branch] h3')].map(box),entries:[...landing.querySelectorAll('[data-task-open]')].map(e=>({id:e.dataset.taskOpen,name:box(e.querySelector('.np-task-reading-name')),contract:box(e.querySelector('.np-task-reading-contract'))}))};
        """)
        report.setdefault('defaultOverviewChecks', []).append(data)
        save()
        check_reading_home(data)

        graph = driver.js(VISUAL_GEOMETRY + RELATION_PATH_SAMPLES_JS + """
          var a=NavigationProductApp,b=a.getBundle(),m=document.getElementById('np-overview-map'),root=b.researchMap.roots[0],p=b.positions;
          var l=p[root].childIds.find(id=>p[id].entityId==='legacy:nav:l'),c=p[root].childIds.find(id=>p[id].entityId==='legacy:nav:c'),td=p[l].childIds.find(id=>p[id].sourceDirectoryGroupId==='task');
          var wanted=[root,l,c,td,...arguments[0].map(s=>b.researchMap.scopeEntries.find(e=>e.scopeId===s).canonicalPositionId),...p[c].childIds];
          function opaque(e){for(var n=e;n;n=n.parentElement){var cs=getComputedStyle(n);if(cs.display==='none'||cs.visibility!=='visible'||Number(cs.opacity)!==1)return false;}return true;}
          function endpoint(e,end){var q=e.getPointAtLength(end?e.getTotalLength():0),r=new DOMPoint(q.x,q.y).matrixTransform(e.getScreenCTM());return {x:r.x,y:r.y};}
          function touches(q,r){return q.x>=r.x-2&&q.x<=r.x+r.width+2&&q.y>=r.y-2&&q.y<=r.y+r.height+2&&Math.min(Math.abs(q.x-r.x),Math.abs(q.x-r.x-r.width),Math.abs(q.y-r.y),Math.abs(q.y-r.y-r.height))<=3;}
          function node(id){return [...m.querySelectorAll('[data-map-position]')].find(n=>n.dataset.mapPosition===id);}
          function edge(e){var cs=getComputedStyle(e),stroke=color(cs.stroke),alpha=stroke?stroke.alpha*Number(cs.strokeOpacity):0,display=true;for(var n=e;n;n=n.parentElement){var st=getComputedStyle(n);alpha*=Number(st.opacity);if(st.display==='none'||st.visibility!=='visible')display=false;}var background=bg(m),foreground=stroke&&background.length===3?stroke.rgb.map((v,i)=>v*alpha+background[i]*(1-alpha)):[],len=e.getTotalLength(),matrix=e.getScreenCTM(),mr=rect(m),inBounds=true,uncovered=0,ownHits=[];if(e.dataset.mapRelation)return Object.assign({visible:display&&alpha>0&&foreground.length===3&&parseFloat(cs.strokeWidth)>0,length:len,foreground:foreground,background:background},relationPathSamples(e,m,len,matrix));for(var i=1;i<20;i++){var q=e.getPointAtLength(len*i/20),z=new DOMPoint(q.x,q.y).matrixTransform(matrix);if(z.x<mr.x-1||z.y<mr.y-1||z.x>mr.x+mr.width+1||z.y>mr.y+mr.height+1||z.x<0||z.y<0||z.x>innerWidth||z.y>innerHeight)inBounds=false;var hit=document.elementFromPoint(z.x,z.y);if(hit&&(hit===e||hit===m||hit===e.closest('svg')))uncovered++;if(hit===e)ownHits.push({x:z.x,y:z.y,fraction:i/20});}return {visible:display&&alpha>0&&foreground.length===3&&parseFloat(cs.strokeWidth)>0,length:len,foreground:foreground,background:background,inBounds:inBounds,uncovered:uncovered>=3,ownHits:ownHits};}
          return {relationsVisible:m.dataset.relationsVisible,selectedRelation:m.dataset.selectedRelation||null,relationControls:[...document.querySelectorAll('[data-relation-select]')].map(e=>e.dataset.relationSelect),viewport:{x:0,y:0,width:innerWidth,height:innerHeight},map:rect(m),mapVisible:!m.hidden&&opaque(m)&&m.clientWidth>0&&m.clientHeight>0,expectedIds:wanted,expectedEdges:wanted.filter(id=>p[id].parentId&&wanted.includes(p[id].parentId)).map(id=>[p[id].parentId,id]),expectedChallengeLabels:arguments[1],expectedRelations:arguments[2],
            directoryTitle:box(node(td)),
            nodes:[...m.querySelectorAll('[data-map-position]')].map(n=>Object.assign({id:n.dataset.mapPosition},box(n))),
            edges:[...m.querySelectorAll('path[data-map-parent][data-map-child]')].map(e=>Object.assign({parent:e.dataset.mapParent,child:e.dataset.mapChild,endpointsMatch:!!node(e.dataset.mapParent)&&!!node(e.dataset.mapChild)&&touches(endpoint(e,false),rect(node(e.dataset.mapParent)))&&touches(endpoint(e,true),rect(node(e.dataset.mapChild)))},edge(e))),
            tasks:[...m.querySelectorAll('[data-task-open]')].map(n=>({scope:n.dataset.taskOpen,expectedScope:p[n.dataset.mapPosition].sourceScopeId,position:n.dataset.mapPosition,expectedPosition:b.researchMap.scopeEntries.find(e=>e.scopeId===n.dataset.taskOpen).canonicalPositionId})),
            challenges:[...m.querySelectorAll('[data-challenge-open]')].map(n=>{var q=p[n.dataset.mapPosition];return {position:n.dataset.mapPosition,challengeOpen:n.dataset.challengeOpen,entity:q.entityId,expectedEntity:p[n.dataset.challengeOpen].entityId,title:n.title,aria:n.getAttribute('aria-label')||'',expectedTitle:arguments[3][q.entityId],label:box(n.querySelector('.np-map-challenge-label'))};}),
            relations:[...m.querySelectorAll('path[data-map-relation]')].map(e=>Object.assign({id:e.dataset.mapRelation,from:e.dataset.fromEntity,to:e.dataset.toEntity,type:e.dataset.relationType,endpointsMatch:(()=>{var from=[...m.querySelectorAll('[data-task-open]')].find(n=>n.dataset.taskOpen===e.dataset.fromEntity),to=[...m.querySelectorAll('[data-task-open]')].find(n=>n.dataset.taskOpen===e.dataset.toEntity);return !!from&&!!to&&touches(endpoint(e,false),rect(from))&&touches(endpoint(e,true),rect(to));})()},edge(e)))};
        """, [x[0] for x in TASK_INDEX], CHALLENGE_LABELS, [[r['id'],r['from'],r['to'],r['relationType']] for r in relation_expected], {entity:science['entities'][entity]['label'] for entity in CHALLENGE_LABELS})
        graph['s0AdaptiveSpacing'] = desktop_chrome_snapshot(driver, report, save, 'reading-home-' + relation_mode, S0_FOOTER_SNAPSHOT_JS, footer_expected)
        report.setdefault('graphicalOverviewChecks', []).append(graph)
        save()
        if (graph['relationsVisible'] != ('true' if relation_mode == 'all' else 'false') or
                graph['selectedRelation'] is not None):
            raise RuntimeError('Initial/show-all overview relationship mode differs from its explicit display contract')
        graph['checkedRelationMode'] = relation_mode
        check_graphical_map(graph)
        check_s0_footer(graph['s0AdaptiveSpacing'])


    def relationship_checks(prefix, base):
        before_route = driver.js('return NavigationProductApp.getState().route')
        if driver.js("return document.getElementById('np-overview-map').dataset.relationsVisible") != 'false':
            raise RuntimeError('Default overview must not expose every non-tree relationship')
        driver.click(driver.selector('#np-map-relations-toggle'))
        if driver.js("return document.getElementById('np-overview-map').dataset.relationsVisible") != 'true':
            raise RuntimeError('Show-all relationship lines control failed')
        reading_home(relation_mode='all')
        driver.click(driver.selector('#np-map-relations-toggle'))
        if driver.js("return document.getElementById('np-overview-map').dataset.relationsVisible") != 'false':
            raise RuntimeError('Single-selection relationship lines control failed')
        driver.click(driver.selector('#np-task-relations > summary'))

        def evidence(expected, expected_focus=None):
            before_footer = s0_footer_check('relation-evidence-before-' + expected['id'])
            data = driver.js("""var id=arguments[0],e=[...document.querySelectorAll('[data-task-relation]')].find(n=>n.dataset.taskRelation===id);return {id:e.dataset.taskRelation,type:e.dataset.relationType,from:e.dataset.fromEntity,to:e.dataset.toEntity,open:!e.hidden&&!document.getElementById('np-overview-relation-panel').hidden,selectorOpen:document.getElementById('np-task-relations').open,focus:document.activeElement.id,route:NavigationProductApp.getState().route,text:e.textContent,sources:[...e.querySelectorAll('[data-task-relation-source]')].map(n=>({id:n.dataset.taskRelationSource,url:n.href,version:n.dataset.sourceVersion,status:n.dataset.sourceStatus}))};""", expected['id'])
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
                proof = driver.js(RELATION_EVIDENCE_PROOF_JS, element)
                after_footer = s0_footer_check('relation-fragment-' + expected['id'] + '-' + spec['kind'])
                check_s0_stability(before_footer, after_footer)
                proof['kind'] = spec['kind']
                if spec['kind'] == 'heading':
                    proof['expectedText'] = S0_RELATION_LABELS[expected['id']]
                elif spec['kind'] == 'locator':
                    proof['expectedText'] = spec['text']
                if spec['kind'] == 'source':
                    ref = next(ref for ref in expected['sourceRefs'] if ref['sourceId'] == spec['id'])
                    proof['expectedText'] = '原文来源 · ' + (ref.get('descriptor') or ref['sourceId'])
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
            if not driver.js("return document.getElementById('np-task-relations').open"):
                driver.click(driver.selector('#np-task-relations > summary'))
            control = driver.selector('[data-relation-select="' + expected['id'] + '"]')
            reveal_relation_selector(driver, control, expected['id'], report, save)
            driver.settle()
            native = driver.js(VISUAL_GEOMETRY + "return {tag:arguments[0].tagName,type:arguments[0].type,disabled:arguments[0].disabled,tabIndex:arguments[0].tabIndex,target:arguments[0].getAttribute('aria-controls'),box:box(arguments[0])};", control)
            if native['tag'] != 'BUTTON' or native['type'] != 'button' or native['disabled'] or native['tabIndex'] != 0 or native['target'] != 'np-map-relation-evidence-' + expected['id'] or not native['box']['visible'] or native['box']['clipped']:
                raise RuntimeError('Relationship text selection is not a usable exact native button')
            before_selection = s0_footer_check('before-selection-' + expected['id'])
            driver.click(control)
            driver.settle()
            selected_footer = s0_footer_check('selected-' + expected['id'])
            check_s0_stability(before_selection, selected_footer)
            evidence(expected)
            selected_lines = driver.js("return [...document.querySelectorAll('path[data-map-relation]')].filter(e=>{var s=getComputedStyle(e);return s.display!=='none'&&s.visibility==='visible'&&Number(s.opacity)>0;}).map(e=>e.dataset.mapRelation);")
            if selected_lines != [expected['id']]:
                raise RuntimeError('Choosing one relationship must expose only its exact source path')
            if i in (0, 2, 6):
                driver.js("document.getElementById(arguments[0]).scrollIntoView({block:'start'});", 'np-map-relation-evidence-' + expected['id'])
                driver.settle()
                capture(prefix + '-13-relation-' + expected['id'].split(':')[-1], require_home=True)
                # Wheel only a genuinely overflowing current source. No padding,
                # scale change or assigned scrollTop manufactures the fixture.
                wheel_before = s0_footer_check('native-wheel-before-' + expected['id'])
                wheel_record = {'relation': expected['id'], 'before': wheel_before,
                                'positive': wheel_before['panel']['maxTop'] > 0}
                report.setdefault('s0PanelWheelChecks', []).append(wheel_record)
                save()
                if wheel_record['positive']:
                    delta = 137 if wheel_before['panel']['top'] < wheel_before['panel']['maxTop'] else -137
                    wheel_record['delta'] = delta
                    try:
                        driver.call('POST', '/actions', {'actions': [{'type': 'wheel', 'id': 's0-source-scroll', 'actions': [
                            {'type': 'scroll', 'origin': driver.selector('#np-overview-relation-panel'), 'x': 0, 'y': 0, 'deltaX': 0, 'deltaY': delta, 'duration': 100}]}]})
                        wait_for(lambda: driver.js("var a=NavigationProductApp,m=NavigationProductModel,s=a.getState(),p=document.getElementById('np-overview-relation-panel'),h=history.state&&history.state[m.KEY];return p.scrollTop!==arguments[0]&&h&&m.getBucket(h).overviewView.relationScrollTop===p.scrollTop&&m.getBucket(s).overviewView.relationScrollTop===p.scrollTop;", wheel_before['panel']['top']))
                        driver.settle()
                    finally:
                        wheel_record['after'] = s0_footer_check('native-wheel-after-' + expected['id'])
                        save()
                    check_s0_wheel(wheel_before, wheel_record['after'], delta)
                else:
                    # Fitting source is reported as zero-range, never positive.
                    if wheel_before['panel']['scrollHeight'] > wheel_before['panel']['clientHeight']:
                        raise RuntimeError('S0 fitting-source report contradicts actual scroll metrics')
                before_close = s0_footer_check('before-close-' + expected['id'])
                driver.click(driver.selector('#np-overview-relation-close'))
                driver.settle()
                closed = s0_footer_check('closed-' + expected['id'])
                check_s0_stability(before_close, closed)
                if (closed['selectedRelation'] is not None or not closed['selectorOpen'] or
                        closed['focus'] != 'np-relation-select-' + expected['id']):
                    raise RuntimeError('S0 close lost exact native relation-selection focus')
        # Exercise native keyboard activation, not a script-generated click event.
        expected = relation_expected[2]
        if not driver.js("return document.getElementById('np-task-relations').open"):
            driver.click(driver.selector('#np-task-relations > summary'))
        control = driver.selector('[data-relation-select="' + expected['id'] + '"]')
        driver.js("arguments[0].scrollIntoView({block:'center'});arguments[0].focus({preventScroll:true});", control)
        driver.call('POST', '/element/' + control[ELEMENT] + '/value', {'text': '\ue007', 'value': ['\ue007']})
        driver.settle()
        evidence(expected)
        footer_before_reload = s0_footer_check('before-relation-reload')
        before_snapshot = driver.js(COLD_RESTORE_SNAPSHOT_JS)
        stored = before_snapshot['view']
        driver.call('POST', '/refresh', {})
        wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
        driver.settle()
        after_snapshot = driver.js(COLD_RESTORE_SNAPSHOT_JS)
        restored = after_snapshot['view']
        footer_after_reload = s0_footer_check('after-relation-reload')
        check_s0_stability(footer_before_reload, footer_after_reload, restore=True)
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
        footer_before_endpoint = s0_footer_check('before-relation-endpoint')
        endpoint_origin = driver.js("return {focus:document.activeElement.id,window:scrollY,landing:document.getElementById('np-reading-landing').scrollTop,relationPanel:document.getElementById('np-overview-relation-panel').scrollTop};")
        driver.click(control)
        driver.settle()
        if driver.js('return NavigationProductApp.getState().route.scope') != expected['to']:
            raise RuntimeError('Relationship endpoint entered another scope')
        driver.call('POST', '/back', {})
        driver.settle()
        if driver.js('return NavigationProductApp.getState().route') != before_route or not driver.js("return !document.getElementById('np-overview-relation-panel').hidden"):
            raise RuntimeError('Relationship Back lost the original route or evidence disclosure')
        back_origin = driver.js("return {focus:document.activeElement.id,window:scrollY,landing:document.getElementById('np-reading-landing').scrollTop,relationPanel:document.getElementById('np-overview-relation-panel').scrollTop};")
        footer_after_back = s0_footer_check('after-relation-endpoint-back')
        check_s0_stability(footer_before_endpoint, footer_after_back, restore=True)
        if back_origin != endpoint_origin:
            raise RuntimeError('Relationship endpoint Back lost exact saved focus or reading scroll')
        evidence(expected, expected_focus=endpoint_origin['focus'])
        # Fresh document for real SVG hit tests; do not force a hidden path click.
        for rid in ('tasks:relation:90', 'tasks:relation:92'):
            driver.call('POST', '/url', {'url': 'about:blank'})
            driver.call('POST', '/url', {'url': base})
            wait_for(lambda: driver.js("return !!window.NavigationProductApp&&document.querySelector('[data-load-state]')?.dataset.loadState==='ready'"))
            driver.settle()
            driver.click(driver.selector('#np-map-relations-toggle'))
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
        challenge_reading = driver.js(ORIGINAL_CHALLENGE_SNAPSHOT_JS, q, original['detail'].get('plain_language_question'),
                                      ORIGINAL_CHALLENGE_TITLE_SELECTOR, ORIGINAL_CHALLENGE_ROLE_SELECTOR)
        report.setdefault('graphChallengeReadingChecks', []).append(challenge_reading)
        save()
        check_original_challenge_reading(challenge_reading, q, original)
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
        root_records = {tree: [{'id': pid, 'entity': science['positions'][pid]['entityId'], 'tree': tree, 'scope': scope,
            'label': science['entities'][science['positions'][pid]['entityId']]['label']} for pid in science['forests'][scope][tree]] for tree in ('l', 'c')}
        data = driver.js(PARALLEL_SCOPE_SNAPSHOT_JS, scope, PARALLEL_ROOT_SELECTOR, science['forests'][scope],
            {tree: any(science['positions'][pid]['childIds'] for pid in science['forests'][scope][tree]) for tree in ('l', 'c')}, root_records)
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
            capture(prefix + '-31-s0-reading-hierarchy', require_home=True)
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
            method_navigation_checks(driver, report, save, prefix, method_reading_expected(science, method_positions[target], method_positions), method_positions)
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
            context = context_path_checks(driver, report, save, capture, prefix)
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
                    method_navigation_checks(driver, report, save, prefix, method_reading_expected(science, method_positions[method], method_positions), method_positions)
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
            disclosure_bounds_checks(driver, report, save, prefix, science)
            task_density_checks(driver, report, save, capture, prefix, base, science)
            desktop_hierarchy_checks(driver, report, save, capture, prefix, base, science)
            task_route_checks(driver, report, save, capture, prefix, base, science, server, dist)
            exploration_state_checks(driver, report, save, capture, prefix, base, science)
            version_title_checks(driver, report, save, prefix, base, science, out)
        planned = [str(w) + 'x' + str(h) + suffix for w, h in VIEWPORTS for suffix in SCENE_NAMES]
        report['capturePlan'] = planned
        if sorted(c['name'] for c in report['captures']) != sorted(planned):
            raise RuntimeError('Actual desktop screenshots differ from the declared bounded exploration plan')
        report['status'] = 'captured_for_human_review'
    except Exception as exc:
        report['status'] = 'failed'
        report['error'] = str(exc)[:2000]
        if isinstance(exc, urllib.error.HTTPError) and hasattr(exc, 'navigation_webdriver_diagnostic'):
            report['webdriverError'] = exc.navigation_webdriver_diagnostic
        if driver and driver.session:
            try:
                (out / 'failure.png').write_bytes(base64.b64decode(driver.call('GET', '/screenshot')))
                report['failureConsole'] = driver.call('POST', '/log', {'type': 'browser'})
            except Exception as diagnostic_error:
                report['diagnosticError'] = type(diagnostic_error).__name__
        raise
    finally:
        try:
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
        finally:
            receipt_cache.close()


if __name__ == '__main__':
    main()
