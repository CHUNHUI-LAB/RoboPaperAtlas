"""Public topic-map view. Uses the catalogue's existing validation and metadata rules.

Integration: map_html(catalog, '../', hashed_css_url, hashed_js_url) returns a
<main> fragment for build.shell(..., prefix='../', page='map').
"""
import html
import json
from urllib.parse import quote
from validate import validate_catalog
from atlas_taxonomy import atlas_projection
from topic_labels import TOPIC_CHINESE
from presentation import map_year_label, metadata_label, pdf_note_heading, translate, evidence_label


# Display-only translations. Unknown future labels remain unchanged, never guessed.
PROBLEM_LABELS = {
    'Robust Motion Planning': '鲁棒运动规划', 'Controller Deployment': '控制器部署',
    'Coordinated Motion': '协调运动', 'Skill Acquisition': '技能习得',
    'Object Interaction': '物体交互', 'Long-horizon Tasks': '长时程任务',
    'Sequence Modeling': '序列建模', 'Mobile Skill Learning': '移动技能学习',
    'Action & World Modeling': '动作与世界建模', 'Generative Modeling': '生成式建模',
    'Dynamic Manipulation': '动态操作', 'Generalist Policies': '通用策略',
    'Shared infrastructure': '共享基础设施', 'Contact & Force': '接触与力',
    'Scene Representation': '场景表征', 'Terrain Adaptation': '地形适应',
    'Goal Search': '目标搜索', 'Cross-task Transfer': '跨任务迁移',
    'Instruction Following': '指令遵循', 'Policy Optimization': '策略优化',
    'Remote Interaction': '远程交互', 'Multi-goal Navigation': '多目标导航',
    'Cross-domain research': '跨领域研究', 'Local Navigation': '局部导航',
    'Long-horizon & Lifelong': '长时程与终身学习',
}

def problem_label(label):
    return PROBLEM_LABELS.get(label, label)

def esc(value):
    return html.escape(str(value) if value is not None else '', quote=True)


def map_data(catalog, base='../',report_records=()):
    """Explicit public projection: no private provenance or speculative relations."""
    validate_catalog(catalog,report_records)
    taxonomy = atlas_projection(catalog['papers'])
    papers = []
    for p in catalog['papers']:
        overlay = p.get('verified_overlay') or {}
        authors = overlay.get('authors') or p.get('authors') or []
        papers.append({
            'id': p['id'], 'title': overlay.get('title') or p['title'],
            'shortName': p.get('short_name') or '',
            'authors': ', '.join(authors) if isinstance(authors, list) else authors,
            'category': p['category'], 'mapTopic': taxonomy['placements'][p['id']]['direction'],
            'topics': [taxonomy['placements'][p['id']]['direction']], 'classification': taxonomy['placements'][p['id']], 'tags': p.get('tags') or [],
            'year': p.get('bibliographic_year'), 'yearBasis': p.get('year_basis'),
            'display': {
                'yearLabel': map_year_label(p), 'metadataLabel': metadata_label(p),
                'pdfNoteHeading': pdf_note_heading(p), 'codeNote': translate(p.get('code_note') or ''),
                'classificationRationale': translate(taxonomy['placements'][p['id']]['rationale']),
                'classificationEvidenceScope': evidence_label(taxonomy['placements'][p['id']]['evidenceScope']),
            },
            'originalRecord': bool(p.get('original_metadata')),
            'sourceChecked': p['citation_verified'],
            'hasVerifiedOverlay': bool(p.get('verified_overlay')),
            'verificationScope': p.get('verification_scope') or '',
            'summary': p.get('summary') or '',
            'paperUrl': p.get('paper_url'), 'pdfUrl': p.get('pdf_url'),
            'pdfKind': p.get('pdf_kind'), 'pdfNote': p.get('pdf_note') or '',
            'projectUrl': p.get('project_url'), 'codeUrls': p.get('code_urls') or [],
            'codeNote': p.get('code_note') or '',
            'detailUrl': f'{base}papers/{p["id"]}/index.html',
            'catalogUrl': f'{base}index.html?q={quote(overlay.get("title") or p["title"], safe="")}#catalog',
            'stages': {key: {'status': value['status'], 'artifacts': [{'url':base+a['path'],'version':a['version']} for a in value['artifacts']]}
                       for key, value in p['stages'].items()},
        })
    return {'schemaVersion': 1, 'updatedAt': catalog['updated_at'],
            'relationMode': 'topic-only', 'verifiedRelations': [],
            'categories': [{**c, 'displayLabel': TOPIC_CHINESE.get(c['id'], c['label'])} for c in taxonomy['directions']],
            'problems': [{**p, 'displayLabel': problem_label(p['label'])} for p in taxonomy['problems']],
            'classificationScope': taxonomy['scope'], 'classificationStatus': taxonomy['status'],
            'papers': papers}


def map_html(catalog, base='../', css='../assets/paper-map.css', js='../assets/paper-map.js',report_records=()):
    data = map_data(catalog, base,report_records)
    categories = {c['id']: c for c in data['categories']}
    counts = {key: sum(p['mapTopic'] == key for p in data['papers']) for key in categories}
    topics = ''.join(f'<button type="button" data-map-topic="{key}" aria-pressed="false" title="{esc(c["english"])}" style="--topic:{c["color"]}"><i aria-hidden="true"></i>{esc(c["displayLabel"])}<span>{counts[key]}</span></button>' for key,c in categories.items())
    rows = ''.join(f'<li data-map-row="{esc(p["id"])}"><a href="{esc(p["detailUrl"])}" data-map-paper="{esc(p["id"])}"><span class="map-list-dot" style="--topic:{categories[p["mapTopic"]]["color"]}" aria-hidden="true"></span><span class="map-list-copy"><strong>{esc(p["title"])}</strong><small>{esc(categories[p["mapTopic"]]["displayLabel"])} / {esc(problem_label(p["classification"]["problemLabel"]))} · {esc(p["display"]["yearLabel"])} · {"分类暂定" if p["classification"]["needsReview"] else "主来源支持的编目判断"}</small></span><span aria-hidden="true">↗</span></a></li>' for p in data['papers'])
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f'''<link rel="stylesheet" href="{esc(css)}"><script src="{esc(js)}" defer></script>
<main id="main" class="paper-map-page">
  <section class="map-heading"><div><p class="eyebrow">ROBO PAPER ATLAS / 研究地图</p><h1>Atlas</h1></div><p>{len(data['papers'])} 个星点，{len(data['papers'])} 篇真实论文。<br>从研究方向进入问题，再抵达论文与证据。</p></section>
  <section class="paper-map" id="paper-map" aria-label="论文主题地图" data-view="list">
    <div class="map-toolbar" hidden>
      <div class="map-search-wrap"><label for="map-search" class="sr-only">搜索地图中的论文</label><span aria-hidden="true">⌕</span><input id="map-search" type="search" role="combobox" autocomplete="off" aria-autocomplete="list" aria-controls="map-suggestions" aria-expanded="false" placeholder="搜索标题、作者、标签…"><button type="button" id="map-search-clear" aria-label="清空地图搜索" hidden>×</button><ul id="map-suggestions" role="listbox" aria-label="匹配的论文" hidden></ul></div>
      <p id="map-result-count" role="status" aria-live="polite">{len(data['papers'])} 篇论文</p>
      <div class="map-view-toggle" role="group" aria-label="浏览方式"><button type="button" data-map-view="map" aria-pressed="false"><span aria-hidden="true">⊙</span> 地图</button><button type="button" data-map-view="list" aria-pressed="true"><span aria-hidden="true">☷</span> 列表</button></div>
    </div>
    <div class="map-topics" aria-label="研究方向与独立资源区域" hidden><button type="button" data-map-topic="all" aria-pressed="true">全部方向<span>{len(data['papers'])}</span></button>{topics}</div>
    <div class="atlas-navigation" hidden><nav id="atlas-breadcrumbs" aria-label="地图当前位置"></nav><button type="button" id="atlas-back" disabled>← 返回上一级</button><p id="atlas-level-description" role="status" aria-live="polite"></p></div>
    <div class="map-workspace">
      <div class="map-explore">
        <div class="map-canvas-wrap" hidden>
          <svg id="map-canvas" role="group" aria-label="论文主题地图。方向键切换论文，Enter 查看，加减键缩放，Home 显示全部。" aria-describedby="map-help map-legend" tabindex="0"><defs><radialGradient id="map-nebula"><stop offset="0" stop-color="#b5cae0" stop-opacity=".16"/><stop offset=".4" stop-color="#7995b3" stop-opacity=".07"/><stop offset="1" stop-color="#597086" stop-opacity="0"/></radialGradient><radialGradient id="map-star-glow"><stop offset="0" stop-color="#f1f8ff" stop-opacity=".8"/><stop offset=".24" stop-color="#d8e8ff" stop-opacity=".22"/><stop offset="1" stop-color="#acc8f0" stop-opacity="0"/></radialGradient></defs><g class="map-world"><g class="map-regions" aria-hidden="true"></g><g class="map-edges" aria-hidden="true"></g><g class="map-nodes"></g><g class="atlas-systems"></g><g class="atlas-problems"></g></g></svg>
          <div class="map-canvas-top"><span><i aria-hidden="true"></i> 研究地图</span><span>{len(data['papers'])} 篇论文 / 按问题探索</span></div>
          <div class="map-controls" role="group" aria-label="地图缩放"><button type="button" data-camera="in" aria-label="放大地图">+</button><button type="button" data-camera="out" aria-label="缩小地图">−</button><span id="map-zoom" aria-live="off">100%</span><button type="button" data-camera="fit" aria-label="显示当前筛选的全部论文">全览 <span aria-hidden="true">↗</span></button></div>
          <p class="map-empty" hidden>没有匹配论文。<br><button type="button" data-map-reset>清空筛选</button></p>
          <div class="map-hover-card" hidden aria-hidden="true"></div>
        </div>
        <p id="map-help" class="map-help">拖动平移 · Ctrl / ⌘ + 滚轮缩放 · 方向键选择</p>
        <div class="map-list-wrap"><p class="map-list-intro">按主题浏览全部书目。选择论文查看资源，也可直接进入完整详情。</p><ul class="map-paper-list">{rows}</ul><p class="map-list-empty" hidden>没有匹配论文。<button type="button" data-map-reset>清空筛选</button></p></div>
      </div>
      <aside class="map-sidebar" aria-label="论文详情与资源">
        <div class="map-panel-welcome"><span class="map-welcome-symbol" aria-hidden="true">✦</span><p class="eyebrow">从这里开始</p><h2>从研究问题<br>找到论文</h2><p>选择彩色星系进入研究方向，再展开问题子系统。每颗论文星都通向原文、代码与阅读状态。</p><div class="map-welcome-facts"><div><strong>{len(data['papers'])}</strong><span>已收录论文</span></div><div><strong>{len(data['categories']):02d}</strong><span>导航区域</span></div><div><strong>00</strong><span>已核验引用关系</span></div></div><p class="map-truth-note">研究方向、方法标签和资源类型分开展示。分类属于编辑判断；题名暂定与主来源核验范围会逐篇说明，不等于全文精读或复现。73 条原始书目与 22 条增补记录的来源状态保留。</p><a class="map-catalog-link" href="{esc(base)}index.html#catalog">回到完整目录 <span aria-hidden="true">↗</span></a></div>
        <div class="map-panel-selected" hidden><div class="map-panel-top"><span>论文与资源</span><button type="button" id="map-panel-close" aria-label="关闭论文详情">关闭 ×</button></div><div id="map-panel-content"></div></div>
      </aside>
    </div>
    <div id="map-legend" class="map-legend"><p><span class="map-legend-node" aria-hidden="true"></span> 小星点代表论文，大光点为层级入口；颜色区分研究方向。跨领域资源与跨领域研究单列</p><p><span class="map-legend-edge" aria-hidden="true"></span> 虚线 = 共享标签的主题相近（推断），不是引用或方法继承</p><p>每篇论文只有一个主位置；方法与资源标签可交叉。星云辉光仅为背景；轨道与距离仅用于层级导航，不代表引用、时间，不代表学术影响力或测得的相似度</p></div>
    <p class="map-access-note">不便操作地图？列表提供同一组论文与全部资源入口。普通滚轮保持页面滚动；移动端默认列表，地图可选。</p>
    <noscript><p class="map-noscript">交互地图需要 JavaScript；全部 {len(data['papers'])} 篇论文的详情链接仍可直接使用。</p></noscript>
    <script type="application/json" id="paper-map-data">{payload}</script>
  </section>
</main>'''
