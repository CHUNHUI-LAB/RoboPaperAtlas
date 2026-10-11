"""Publish the audited, version-isolated navigation research workspace."""
from pathlib import Path
import hashlib
import gzip
import html
import json
import os
import stat
import tempfile
from urllib.parse import urlencode, urlsplit
from build_topic_preview import require, safe_path, safe_target
from radar_c2_preview import read_regular, SOURCE_DIRS
from navigation_transport import project
from navigation_native_trees import render_native_trees
from navigation_research_map import build_research_map, render_global_native, write_scope_pages

ROUTE = 'research/navigation'
SOURCE = 'data/navigation-product'
MODEL_SHA256 = '9069c6a11ae9a867671522d04e6a24b4edcada660d03feb2f41340bfc395825c'
PUBLIC_FILES = frozenset(('index.html','product-data.json','content','branches'))
ASSETS = ('navigation-product-model.js','navigation-product.js','navigation-product.css','navigation-bootstrap.js','navigation-content.js')

def exact_json(raw):
    def pairs(items):
        out={}
        for key,value in items:
            require(key not in out, 'Duplicate product JSON key: '+key)
            out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs)

def payloads(root):
    root=Path(root).absolute();folder=safe_path(root,root/SOURCE)
    manifest=exact_json(read_regular(root,folder/'manifest.json'))
    require(manifest['schemaVersion']=='navigation-product-input/1','Unknown product input version')
    require(manifest['status']=='scoped_science_reviewed_ui_acceptance_pending','Do not silently promote acceptance')
    require(manifest['encoding']=='gzip','Unknown product encoding')
    require({p.name for p in folder.iterdir()}=={'manifest.json','model.json.gz'},'Unexpected product input file')
    compressed=read_regular(root,folder/'model.json.gz')
    require(len(compressed)==manifest['compressedBytes'] and hashlib.sha256(compressed).hexdigest()==manifest['compressedSha256']=='8559287ceaccf360ac234e013ef485693b162b3ea8d23aa447b34398f69456e0','Frozen compressed model mismatch')
    raw=gzip.decompress(compressed);require(len(raw)==manifest['bytes']==9657324,'Product model length mismatch')
    require(hashlib.sha256(raw).hexdigest()==manifest['sha256']==MODEL_SHA256,'Reviewed product science mismatch')
    model=exact_json(raw);require(model['schemaVersion']=='navigation-product/1','Unknown product schema')
    require(len(model['papers'])==manifest['expected']['papers'] and len(model['claims'])==manifest['expected']['claims'] and len(model['positions'])==manifest['expected']['positions'],'Product coverage count mismatch')
    require(model['template']['nodeCount']==59 and len(model['template']['nodes'])==59,'Original template boundary changed')
    require(set(model['analyses'])=={'poni','harnessvln','navharness'},'Actual analysis identity set changed')
    for name in ASSETS:read_regular(root,root/'assets'/name)
    return raw,model

def validate_preview(root,target):
    root=Path(root).absolute();target=safe_target(root,target)
    require(target.relative_to(root).parts[0] not in SOURCE_DIRS,'Output must not overlap protected source namespace')
    raw,model=payloads(root)
    return root,target,raw,model

def esc(value):return html.escape(str(value),quote=True)

def static_reading(model):
    """A public, exact-data reading surface which never depends on scripts."""
    scopes={x['id']:x for x in model['scopes']}
    def route(position=None,scope=None):
        values={'nav':'1','scope':scope or position['scopeId'] or 'scope:all','tree':position['tree'] if position else 'l'}
        if position:
            values.update(node=position['id'])
            if position.get('paperId'):values['paper']=position['paperId']
            if position.get('versionId'):values['version']=position['versionId']
        values['mode']='tree'
        return '#'+urlencode(values)
    def refs(entity):
        out=[];seen=set()
        for ref in entity.get('sourceRefs',[]):
            url=ref.get('url') or ref.get('sourceURL') or ''
            if url in seen or urlsplit(url).scheme not in ('http','https'):continue
            seen.add(url)
            out.append('<a href="'+esc(url)+'" target="_blank" rel="noopener noreferrer">'+esc(ref.get('descriptor') or ref.get('versionId') or '原文来源')+' ↗</a>'+(' · '+esc(ref.get('locator') or ref.get('detail',{}).get('locator')) if (ref.get('locator') or ref.get('detail',{}).get('locator')) else ''))
        return ' · '.join(out[:2])
    cards=[]
    for sid in model['recommendedScopeIds'][:6]:
        scope=scopes[sid];bench=[model['entities'][bid]['label'] for bid in scope.get('benchmarkIds',[])[:3] if bid in model['entities']]
        cards.append('<article class="np-static-card"><h3><a href="'+esc(route(scope=sid))+'">'+esc(scope['label'])+'</a></h3><p>'+esc(scope.get('definition',''))+'</p><p class="np-note">'+esc('代表评测入口：'+' · '.join(bench) if bench else '评测条件按具体来源核对')+'</p></article>')
    rows=[]
    positions=list(model['positions'].values())
    for tree,kind,title in [('l','pipeline_recipe','文献树 · ObjectNav 方法选读'),('c','insight','挑战–思路树 · ObjectNav 选读')]:
        parts=[]
        for paper in ('semexp','poni','vlfm'):
            matches=[x for x in positions if x['scopeId']=='task:category-objectnav' and x['tree']==tree and x['kind']==kind and x.get('paperId')==paper]
            if not matches:continue
            x=matches[0];entity=model['entities'][x['entityId']];detail=entity.get('detail',{});pipeline=detail.get('pipeline',{})
            text='；'.join(str(pipeline[k]) for k in ('input','representation','decision','execution','feedback') if pipeline.get(k))
            if not text:text=detail.get('design') or x['label']
            if detail.get('limits'):text+='；边界：'+str(detail['limits'])
            parts.append('<article class="np-static-card"><h4><a href="'+esc(route(x))+'">'+esc(x['label'])+'</a></h4><p>'+esc(text)+'</p><p class="np-note">'+esc(model['versions'].get(x.get('versionId'),{}).get('label') or x.get('versionId') or '版本待核')+'</p><p>'+refs(entity)+'</p></article>')
        rows.append('<details open><summary>'+title+'</summary><div class="np-static-grid">'+''.join(parts)+'</div></details>')
    analyses=[]
    for paper,versions in model['analyses'].items():
        for version,entry in versions.items():
            x=model['positions'][entry['roots'][0]]
            analyses.append('<li><a href="'+esc(route(x))+'">'+esc(model['papers'][paper].get('label') or paper)+' · '+esc(model['versions'][version].get('label') or version)+'</a>：'+str(entry['answeredOriginalCount'])+' 个原模板节点已填；'+str(entry['answeredInstanceCount'])+' 个实例节点已填。</li>')
    return '<section id="np-static-reading" class="np-static-reading" aria-labelledby="np-static-heading"><h2 id="np-static-heading">加载期间可读摘要</h2><p>这部分直接包含在页面中。完整三棵联动树正在准备，默认摘要只列ObjectNav选读，不是全站范围。其他任务可从下列六个入口或来源索引继续选择。</p><div class="np-static-grid">'+''.join(cards)+'</div><p><a href="../../map/index.html">打开完整来源与论文索引</a></p>'+''.join(rows)+'<details><summary>论文解析树 · 当前已有回答的版本</summary><p>只有以下版本已有部分答案。其余论文可进入原59节点参考模板，答案保持未填。</p><ul>'+''.join(analyses)+'</ul></details></section>'

def render(root,model,delivery=None):
    delivery=delivery or project(model,MODEL_SHA256)
    def asset(name):return '../../assets/'+name+'?v='+hashlib.sha256((root/'assets'/name).read_bytes()).hexdigest()[:16]
    bootstrap=(root/'assets/navigation-bootstrap.js').read_text()
    require('</script' not in bootstrap.lower(),'Unsafe bootstrap script boundary')
    inline_scripts=[]
    for phase,name in [('module_model','navigation-product-model.js'),('module_content','navigation-content.js'),('module_app','navigation-product.js')]:
        code=(root/'assets'/name).read_text()
        require('</script' not in code.lower(),'Unsafe inline script boundary')
        inline_scripts.append('<script>window.NavigationProductLoader.stage(window.NavigationProductLoader.attempt,"正在准备交互模块…","'+phase+'");</script><script data-navigation-module="'+phase+'">'+code+'</script>')
    css=(root/'assets/navigation-product.css').read_text()
    require('</style' not in css.lower(),'Unsafe inline style boundary')
    startup='<script type="application/json" id="np-navigation-index">'+delivery['inline'].decode()+'</script><script>'+bootstrap+'</script>'+''.join(inline_scripts)
    global_href=html.escape('#'+urlencode({'nav':'1','scope':'scope:all','tree':'g','node':delivery['index']['delivery']['researchMap']['roots'][0],'mode':'tree'}),quote=True)
    native='<section id="np-static-reading" class="np-static-reading">'+render_global_native(model,delivery['researchMap'])+'</section>'
    return '''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>导航研究地图 · 文献发展与挑战–思路 · RoboPaperAtlas</title><meta name="description" content="从共同研究目标看文献发展与挑战–思路全景，再沿具体工作下钻原论文与版本证据。"><link rel="icon" href="../../assets/favicon.svg"><style data-css-source="'''+asset('navigation-product.css')+'''">'''+css+'''</style></head><body><a class="np-skip" href="#np-workspace">跳到三棵树</a><header class="np-header"><a class="np-brand" href="../../index.html">RoboPaperAtlas</a><h1>导航研究地图</h1><details class="np-header-links"><summary>历史与索引</summary><nav aria-label="研究导航"><a href="../../map/index.html">Atlas</a><a href="../../review/radar-c2-analysis/index.html">原三树与历史</a><a href="../../review/objectnav-reading-v1/index.html">ObjectNav试读档案</a></nav></details></header><main id="navigation-product" data-inline-start="1" data-index-sha="'''+delivery['indexSha256']+'''" data-content-source="'''+asset('navigation-content.js')+'''" data-model-sha="'''+MODEL_SHA256+'''" data-model-url="product-data.json" data-state-url="'''+asset('navigation-product-model.js')+'''" data-app-url="'''+asset('navigation-product.js')+'''" data-bootstrap-source="'''+asset('navigation-bootstrap.js')+'''"><section class="np-start np-global-start" aria-label="全局研究导航"><nav class="np-global-navigation"><a href="'''+global_href+'''">全局研究图</a><a href="branches/directory.html">资料索引</a><details id="np-catalog"><summary>直接查找具体任务或条件</summary><label>查找阅读范围<input id="np-directory-search" type="search" placeholder="任务名、目标形式或条件" autocomplete="off"></label><div id="np-directory-list" class="np-directory-list"></div><button id="np-global-index" type="button">全部来源与论文索引</button></details></nav></section><div id="np-loading" class="np-loading" role="status" aria-live="polite"><span id="np-load-message">全局图准备中；下方原生全局层级与普通链接无需等待即可使用。</span><button id="np-retry" type="button" hidden>重试加载交互（最多2次）</button></div>'''+native+'''<div class="np-current-scope"><span id="np-scope-role" class="np-kicker"></span><h2 id="np-active-scope">阅读范围</h2><button id="np-open-conditions" type="button" aria-controls="np-task-conditions">任务与评测条件</button></div><p id="np-status" class="np-status" role="status" aria-live="polite"></p><p id="np-navigation-error" class="np-navigation-error" role="alert" hidden></p><section id="np-workspace" class="np-workspace" aria-label="全局研究图与单篇论文证据" hidden><div class="np-workspace-bar"><button id="np-graph-fullscreen" type="button">全屏查看</button><button id="np-reader-toggle" type="button" aria-controls="np-detail-scroll" aria-expanded="true" hidden>收起阅读栏</button><button id="np-overview-toggle" class="np-text-button" type="button" hidden>原全局树图</button><div class="np-tabs" role="tablist" aria-label="研究地图视角"><button role="tab" data-tree-tab="g" aria-selected="true">全景</button><button role="tab" data-tree-tab="l" aria-selected="false" tabindex="-1">文献发展</button><button role="tab" data-tree-tab="c" aria-selected="false" tabindex="-1">挑战–思路</button></div><nav id="np-global-context" class="np-global-context" aria-label="全局研究来路"></nav><details class="np-identity-controls"><summary>论文身份与来源版本</summary><div class="np-context-controls"><label>论文身份<select id="np-paper"></select></label><label>来源版本<select id="np-version"></select></label><div><p class="np-note">论文与版本不会跨树混用。未导入解析的版本可看原模板，答案保持未填。</p></div></div><p id="np-version-note" class="np-version-note"></p><button data-tree-tab="a" type="button">打开这篇论文的版本证据解析</button><div class="np-share"><label class="np-sr" for="np-share-link">当前任务、节点、论文版本与证据的分享链接</label><input id="np-share-link" type="text" readonly><button id="np-copy-link" type="button">复制精确阅读链接</button></div></details><nav id="np-origin-trail" class="np-origin-trail" aria-label="阅读来路与返回"></nav></div><section id="np-reading-landing" class="np-reading-landing" aria-label="任务差异概览与完整范围入口" hidden></section><div class="np-panels"><section class="np-tree-pane" aria-labelledby="np-tree-heading"><div class="np-pane-top"><h2 id="np-tree-heading" tabindex="-1">全局研究图</h2><div class="np-view-tools" aria-label="画布视图"><div id="np-graph-zoom" class="np-graph-zoom"><button id="np-zoom-out" type="button" aria-label="缩小全景图">−</button><span id="np-zoom-value">100%</span><button id="np-zoom-in" type="button" aria-label="放大全景图">+</button><button id="np-zoom-reset" type="button">原比例</button><button id="np-zoom-fit" type="button">适配画布</button></div></div><details class="np-tree-options"><summary>图例与查找</summary><p id="np-tree-caption" class="np-tree-caption"></p><p class="np-reading-legend">目录分组仅组织阅读；任务、条件、协议保持原角色，不自动视作milestone。选择节点后，在阅读栏核对直接关联、条件关联及有据技术变化；版本与原文限制保留在对应证据中。</p><div class="np-tree-tools"><button id="np-layout-toggle" type="button" aria-pressed="false">切换为等价提纲</button><button id="np-locate-current" type="button">定位所选节点</button></div><label>查找本树节点<input id="np-node-search" type="search" placeholder="方法、思路或原模板节点" autocomplete="off"></label><div id="np-node-results" class="np-search-results" hidden></div></details></div><div id="np-tree-scroll" class="np-tree-scroll" tabindex="0" aria-label="研究树画布；可用滚动、缩放按钮或拖动空白区域浏览"><div id="np-task-route-canvas" class="np-task-route-canvas" hidden></div><div id="np-tree" class="np-tree" data-mode="tree"></div></div><div class="np-canvas-footer"><span id="np-canvas-count"></span><span>选择节点深入 · ＋展开 · 拖动空白平移</span></div></section><aside id="np-detail-scroll" class="np-reading-pane" aria-label="所选节点阅读" tabindex="-1"><div class="np-reader-heading"><span>READING DESK</span><span>所选节点</span></div><div id="np-reader-summary" class="np-reader-summary"></div><details id="np-evidence-panel" class="np-detail-pane"><summary>原文证据、评测与固定版本</summary><div class="np-detail-scroll"><h2 id="np-detail-title" class="np-detail-title" tabindex="-1">节点内容</h2><div id="np-detail-identity" class="np-detail-identity"></div><div id="np-detail-content"></div></div></details><details id="np-reading-context-wrap" class="np-reading-context-wrap"><summary>任务范围与同层对照</summary><div id="np-reading-context" class="np-reading-context"></div></details></aside></div></section><a id="np-scope-map-section" class="np-index-link" href="branches/directory.html">资料索引 · 全部阅读范围</a><details id="np-task-conditions" class="np-supporting"><summary>任务与评测条件 · 定义、边界、协议与原文</summary><p>先辨清任务和评测条件，再读方法怎样发展、思路如何回应困难。全局研究图与单篇解析共享论文身份和来源版本，按需要进入证据。</p><section class="np-overview"><div><div id="np-scope-summary"></div><div id="np-coverage-summary"></div></div><div><div class="np-bench-controls"><label>Benchmark / 评估设置<select id="np-benchmark"><option value="">正在加载</option></select></label><label>协议记录（保持版本差异）<select id="np-protocol"><option value="">正在加载</option></select></label></div><div id="np-benchmark-summary" class="np-benchmark-summary"></div></div></section></details><details class="np-supporting" id="np-method-comparison"><summary>同页比较当前范围的方法</summary><p class="np-note">比较输入、表示、决策、执行与反馈。相似接口不等于同一评测协议，也不把不同论文指标拼成排行榜。</p><div id="np-comparison-cards" class="np-comparison-cards"></div></details><details class="np-supporting"><summary>查看真实内容覆盖与待补部分</summary><p>产品中的任务、条件、协议、benchmark和论文是不同角色。方法/挑战选段有据，不等于全部论文全文精读；原59节点模板包含根、章节、分组与40个叶节点，不是59个独立已答问题。</p><div id="np-coverage-table" class="np-coverage-table"></div></details><noscript><p class="np-boundary">交互聚焦需要JavaScript；原生全局层级与全部范围的普通阅读链接仍可使用。未填答案不会被虚构补齐。</p><a href="../../review/radar-c2-analysis/index.html">原三树阅读</a> · <a href="../../review/objectnav-reading-v1/index.html">ObjectNav静态试读</a></noscript><footer class="np-footer">所有判断保持来源、版本与范围。技术界面就绪不等于全领域穷尽、所有论文精读完成或独立复现。</footer></main>'''+startup+'''</body></html>'''

def write_preview(root,target):
    root,target,raw,model=validate_preview(root,target);dest=safe_path(root,target/ROUTE)
    delivery=project(model,MODEL_SHA256)
    if dest.exists():
        require({p.name for p in dest.iterdir()}<=PUBLIC_FILES,'Unexpected navigation output')
        for p in dest.iterdir():
            safe_path(root,p)
            require(stat.S_ISDIR(p.stat().st_mode) if p.name in ('content','branches') else stat.S_ISREG(p.stat().st_mode),'Unexpected navigation output type')
    dest.mkdir(parents=True,exist_ok=True)
    content_dir=safe_path(root,dest/'content');content_dir.mkdir(exist_ok=True)
    if any(content_dir.iterdir()):
        require({p.name for p in content_dir.iterdir()}==set(delivery['files']),'Unexpected content output')
        for p in content_dir.iterdir():safe_path(root,p);require(stat.S_ISREG(p.stat().st_mode),'Content output must be regular')
    outputs={dest/'index.html':render(root,model,delivery).encode(),dest/'product-data.json':raw}
    outputs.update({content_dir/name:data for name,data in delivery['files'].items()})
    for path,content in outputs.items():
        path=safe_path(root,path);fd,tmp=tempfile.mkstemp(prefix='.navigation-',dir=path.parent)
        try:
            with os.fdopen(fd,'wb') as f:f.write(content)
            os.replace(tmp,path)
        finally:
            if os.path.exists(tmp):os.unlink(tmp)
    write_scope_pages(root,target,model,delivery['researchMap'])
    return dest
