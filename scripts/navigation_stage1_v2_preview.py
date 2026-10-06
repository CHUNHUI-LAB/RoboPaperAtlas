"""Final v2 bytes on isolated HTTPS QA routes; no canonical registration.

Pending records stay pending throughout validation and rendering. The dedicated
candidate entry point shares only passive parsing/presentation internals with
canonical readers. Neither approval nor catalog state is inferred from QA.
"""
import json,hashlib
from pathlib import Path
from html import escape
import reports as r
from current_reader import render_navigation_v2_candidate,NAVIGATION_CANONICAL_FROZEN
from report_navigation_stage1 import IDS,prepare_candidate_v2
BASE='reader-integration-preview/navigation-stage1-v2-20261005'
MANIFEST='candidates/navigation-stage1-v2-pending.json'
TITLES={'harnessvln':'HarnessVLN','navharness':'NavHarness','holoagent-0':'HoloAgent-0'}


def load_sources(root):
    root=r._root(root)
    obj=json.loads(r._read(root,MANIFEST,2_000_000).decode('utf-8'),object_pairs_hook=r._json_object)
    r._keys(obj,{'schema_version','status','base_B_commit','base_B_tree','gates','reports','facts_audit'},'V2 candidate manifest')
    r.require(type(obj['schema_version'])is int and obj['schema_version']==1 and obj['status']=='pending_candidate','Wrong v2 candidate manifest state')
    r.require(obj['base_B_commit']=='e06c49085b82687cd28e03673574777bb848800e' and obj['base_B_tree']=='e32e817a9fe52411e29bf6d472754f9e255af5eb','Wrong preserved B baseline')
    r.require(isinstance(obj['gates'],dict) and obj['facts_audit']=='candidates/navigation-stage1-v2-facts-audit.json','Missing candidate gate disclosure')
    recs=obj['reports']
    r.require(isinstance(recs,list)and all(isinstance(x,dict)for x in recs)and[x.get('paper_id')for x in recs]==list(IDS),'Wrong v2 candidate identities/order')
    result=[]
    for record in recs:
        r._validate_record_fields(record)
        r.require(record['stage']=='stage1'and record['version']=='v2'and record['filename']=='first-pass.html'and record['review_status']=='pending_candidate','Wrong v2 candidate identity/state')
        chunks=[]
        for part in record['parts']:
            raw=r._read(root,r._parts_path(record)+'/'+part['file'],r.CHUNK_BYTES)
            raw.decode('utf-8')
            r.require(len(raw)==part['bytes']and r.sha(raw)==part['sha256'],'V2 candidate chunk fingerprint differs')
            chunks.append(raw)
        payload=b''.join(chunks)
        text,parser=prepare_candidate_v2(root,record,payload)
        parser=r._finish_html_parse(record,text,parser)
        r.require(all(target==record['filename']for target,fragment in parser.links),'Unregistered candidate sibling link')
        result.append((record,payload))
    return result


def output_payloads(root):
    outputs={};links=[]
    for record,raw in load_sources(root):
        pid=record['paper_id'];page=render_navigation_v2_candidate(root,record,raw)
        fixed=f'../../../artifacts/{pid}/v2/first-pass.html'
        r.require(page.count('href="'+fixed+'"')==1,'Unknown v2 fixed-link signature')
        page=page.replace('href="'+fixed+'"','href="first-pass.html"',1)
        old=NAVIGATION_CANONICAL_FROZEN[pid]['current_return']
        r.require(page.count(old)==1,'Unknown v2 return signature')
        page=page.replace(old,f'<a class="atlas-return" href="https://chunhui-lab.github.io/RoboPaperAtlas/papers/{pid}/index.html#reading">回到正式论文档案</a>',1)
        # Versioned presentation-only addition; immutable reports and v1 routes
        # are deliberately untouched. The original inline runtime stays intact.
        # Native Tab scrolling exposes the link box, not an exterior outline.
        # Keep the existing 3px/color focus indicator 1px inside the visible box;
        # scope this addition to preview TOC links without changing scroll code.
        ring='<style data-reader-toc-focus-ring="v1">.f2-current-reader .reader-toc a:focus-visible{outline-offset:-4px}</style>'
        r.require(page.count('</head>')==1,'Unknown v2 preview head signature')
        page=page.replace('</head>',ring+'</head>',1)
        ui='reader-toc-focus-v1.js'
        digest=hashlib.sha256((Path(root)/'assets'/ui).read_bytes()).hexdigest()[:12]
        page=page.replace('</body>',f'<script src="../../../assets/{ui}?v={digest}" defer></script></body>',1)
        outputs[f'{BASE}/{pid}/first-pass.html']=raw
        outputs[f'{BASE}/{pid}/stage1.html']=page.encode('utf-8')
        links.append(f'<li><a href="{pid}/stage1.html">{TITLES[pid]} · Stage 1 · 报告v2</a><small>固定源版本：{escape(record["source_edition"].split(";")[0])} · <a href="{pid}/first-pass.html">核对最终固定报告</a></small></li>')
    page='''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,follow"><title>Stage 1 v2最终报告验收入口</title><style>body{max-width:860px;margin:40px auto;padding:0 24px;font:18px/1.8 system-ui,sans-serif;color:#24352e;background:#fff}a{color:#235d48}li{margin:24px 0}small{display:block;color:#5b6560}h1{font-size:30px}aside{padding:16px;background:#fff5dc;border-left:3px solid #aa791a}</style></head><body><main><h1>三篇Stage 1 · v2最终报告验收</h1><aside>这里提供拟用于正式收录的固定报告字节，供桌面、窄屏、交互与打印检查。本入口不会修改正式目录的阅读状态，也不表示已通过全部验收。正式收录状态以论文档案为准。Stage 2、Stage 3未提供。</aside><ul>'''+''.join(links)+'''</ul><p>来源一致性检查、实际浏览器检查与打印检查分别记录。报告页保留noindex，正式论文详情承担索引；报告版本与论文版本分别标明，不暗示独立实验复现。</p><p><a href="../navigation-stage1-20261004/index.html">查看保留的v1集成预览</a> · <a href="../../reading/index.html">返回正式阅读档案</a></p></main></body></html>'''
    outputs[BASE+'/index.html']=page.encode('utf-8')
    return outputs


def write_preview(root,target):
    root=r._root(root);target=r._root(target)
    for path,payload in output_payloads(root).items():r._atomic_write(target,path,payload)


def validate_preview(root,target):
    root=Path(root);target=Path(target);folder=target/BASE
    required=(target/'data/catalog.json').exists()
    if not(root/MANIFEST).exists():
        r.require(not folder.exists(),'Unregistered v2 candidate output');return set()
    if not required and not folder.exists():return set()
    expected=output_payloads(root)
    r.require(folder.is_dir()and not folder.is_symlink(),'Missing/unsafe v2 preview directory')
    actual={str(p.relative_to(target))for p in folder.rglob('*')if p.is_file()}
    r.require(actual==set(expected),'Unexpected or missing v2 preview file')
    for path,payload in expected.items():
        r.require(r._read(target,path,r.MAX_REPORT_BYTES)==payload,'V2 preview output differs from exact final bytes')
    return set(expected)
