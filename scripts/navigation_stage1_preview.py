"""Isolated HTTPS-review routes, independent of canonical reading state.

Only three exact hash-pinned Stage1 sources in a dedicated preview manifest are
read. No catalogue mutation, arbitrary file discovery, workflow change or broad
HTML-policy relaxation is involved. A preview is not visual acceptance.
"""
import copy,json
from html import escape
from pathlib import Path
import reports as r
from current_reader import render,NAVIGATION_FROZEN
from report_navigation_stage1 import IDS
BASE='reader-integration-preview/navigation-stage1-20261004'
MANIFEST='data/navigation-stage1-preview.json'
TITLES={'harnessvln':'HarnessVLN','navharness':'NavHarness','holoagent-0':'HoloAgent-0'}

def load_sources(root):
    root=r._root(root)
    obj=json.loads(r._read(root,MANIFEST,2_000_000).decode('utf-8'),object_pairs_hook=r._json_object)
    r._keys(obj,{'schema_version','reports'},'Navigation preview manifest')
    r.require(type(obj['schema_version']) is int and obj['schema_version']==1,'Wrong preview schema')
    recs=obj['reports']
    r.require(isinstance(recs,list) and all(isinstance(x,dict)for x in recs) and [x.get('paper_id')for x in recs]==list(IDS),'Unknown preview identities/order')
    result=[]
    for record in recs:
        r._validate_record(record)
        r.require(record['review_status']=='preview_pending','Preview is not an approval state')
        chunks=[]
        for part in record['parts']:
            chunk=r._read(root,f'data/navigation-stage1-preview-parts/{record["paper_id"]}/v1/stage1/'+part['file'],r.CHUNK_BYTES)
            chunk.decode('utf-8')
            r.require(len(chunk)==part['bytes'] and r.sha(chunk)==part['sha256'],'Preview part fingerprint differs')
            chunks.append(chunk)
        raw=b''.join(chunks)
        r.require(len(raw)==record['bytes'] and r.sha(raw)==record['sha256'],'Preview source fingerprint differs')
        parser=r._parse_html(record,raw,root)
        r.require(all(target==record['filename'] for target,fragment in parser.links),'Unimported sibling preview link')
        result.append((record,raw))
    return result

def output_payloads(root):
    sources=load_sources(root);outputs={};links=[]
    for record,raw in sources:
        pid=record['paper_id']
        # A local view-model only: the canonical catalog is never modified.
        paper={'id':pid,'stages':{key:{'status':'not_imported','artifacts':[]}for key in ('stage1','stage2','stage3')}}
        paper['stages']['stage1']={'status':'imported','artifacts':[{'path':r.report_path(record)}]}
        page=render(root,paper,'stage1',[record],preview_payload=raw)
        fixed=f'../../../{r.report_path(record)}'
        r.require(page.count('href="'+fixed+'"')==1,'Unknown fixed-version preview signature')
        page=page.replace('href="'+fixed+'"','href="first-pass.html"',1)
        old=NAVIGATION_FROZEN[pid]['current_return']
        r.require(page.count(old)==1,'Unknown preview return signature')
        page=page.replace(old,f'<a class="atlas-return" href="https://chunhui-lab.github.io/RoboPaperAtlas/papers/{pid}/index.html#reading">回到正式论文档案</a>',1)
        outputs[f'{BASE}/{pid}/stage1.html']=page.encode('utf-8')
        outputs[f'{BASE}/{pid}/first-pass.html']=raw
        links.append(f'<li><a href="{pid}/stage1.html">{TITLES[pid]} · Stage 1集成预览</a> <small>待桌面／窄屏／打印与交互验收</small></li>')
    index='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Stage 1阅读器集成预览</title><style>body{max-width:860px;margin:40px auto;padding:0 24px;font:18px/1.8 system-ui,sans-serif;color:#24352e;background:#fff}a{color:#235d48}li{margin:24px 0}small{display:block;color:#5b6560}h1{font-size:30px}aside{padding:16px;background:#fff5dc;border-left:3px solid #aa791a}</style></head><body><main><h1>三篇Stage 1阅读器集成预览</h1><aside>这是受控验收入口，尚未正式收录。静态检查与浏览器视觉验收分别记录；本页不宣称完成验收或独立实验复现。正式目录中的阅读状态未因本预览改变。</aside><ul>'''+''.join(links)+'''</ul><p>HarnessVLN、NavHarness保留有CC BY4.0来源说明的图像；HoloAgent-0公开预览不含论文原图，使用独立中文说明和作者原文定位链接。</p><p><a href="../../reading/index.html">返回正式阅读档案</a></p></main></body></html>'''
    outputs[BASE+'/index.html']=index.encode('utf-8')
    return outputs

def write_preview(root,target):
    root=r._root(root);target=r._root(target)
    for path,payload in output_payloads(root).items():r._atomic_write(target,path,payload)

def validate_preview(root,target):
    root=Path(root);target=Path(target);folder=target/BASE
    # Partial artifact-only regression fixtures have no site catalog or preview.
    required=(target/'data/catalog.json').exists()
    if not (root/MANIFEST).exists():
        r.require(not folder.exists(),'Unregistered navigation preview output')
        return set()
    if not required and not folder.exists():return set()
    expected=output_payloads(root)
    r.require(folder.is_dir() and not folder.is_symlink(),'Missing/unsafe navigation preview directory')
    actual={str(p.relative_to(target)) for p in folder.rglob('*')if p.is_file()}
    r.require(actual==set(expected),'Unexpected or missing navigation preview file')
    for path,payload in expected.items():
        actual=r._read(target,path,r.MAX_REPORT_BYTES)
        r.require(actual==payload,'Navigation preview output differs from exact derived bytes')
    return set(expected)
