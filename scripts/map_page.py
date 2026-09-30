"""Public topic-map view. Uses the catalogue's existing validation and metadata rules.

Integration: map_html(catalog, '../', hashed_css_url, hashed_js_url) returns a
<main> fragment for build.shell(..., prefix='../', page='map').
"""
import html
import json
from validate import validate_catalog

CATEGORIES = {
    'navigation': ('具身导航', 'Navigation', '#526e83'),
    'wbc': ('全身控制与移动操作', 'Whole-body & Loco-manipulation', '#96734f'),
    'vla': ('视觉语言动作', 'Vision-Language-Action', '#82708e'),
    'foundations': ('基础、数据与评测', 'Foundations & Benchmarks', '#647c6b'),
}


def esc(value):
    return html.escape(str(value) if value is not None else '', quote=True)


def map_data(catalog, base='../',report_records=()):
    """Explicit public projection: no private provenance or speculative relations."""
    validate_catalog(catalog,report_records)
    papers = []
    for p in catalog['papers']:
        overlay = p.get('verified_overlay') or {}
        authors = overlay.get('authors') or p.get('authors') or []
        papers.append({
            'id': p['id'], 'title': overlay.get('title') or p['title'],
            'shortName': p.get('short_name') or '',
            'authors': ', '.join(authors) if isinstance(authors, list) else authors,
            'category': p['category'], 'tags': p.get('tags') or [],
            'year': p.get('bibliographic_year'), 'yearBasis': p.get('year_basis'),
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
            'catalogUrl': f'{base}index.html?topic={p["category"]}#catalog',
            'stages': {key: {'status': value['status'], 'artifacts': [{'url':base+a['path'],'version':a['version']} for a in value['artifacts']]}
                       for key, value in p['stages'].items()},
        })
    return {'schemaVersion': 1, 'updatedAt': catalog['updated_at'],
            'relationMode': 'topic-only', 'verifiedRelations': [],
            'categories': [{'id': key, 'label': label, 'english': english, 'color': color}
                           for key, (label, english, color) in CATEGORIES.items()],
            'papers': papers}


def map_html(catalog, base='../', css='../assets/paper-map.css', js='../assets/paper-map.js',report_records=()):
    data = map_data(catalog, base,report_records)
    counts = {key: sum(p['category'] == key for p in data['papers']) for key in CATEGORIES}
    topics = ''.join(f'<button type="button" data-map-topic="{key}" aria-pressed="false" style="--topic:{color}"><i aria-hidden="true"></i>{esc(label)}<span>{counts[key]}</span></button>' for key, (label, _, color) in CATEGORIES.items())
    rows = ''.join(f'<li data-map-row="{esc(p["id"])}"><a href="{esc(p["detailUrl"])}" data-map-paper="{esc(p["id"])}"><span class="map-list-dot" style="--topic:{CATEGORIES[p["category"]][2]}" aria-hidden="true"></span><span class="map-list-copy"><strong>{esc(p["title"])}</strong><small>{esc(CATEGORIES[p["category"]][0])} · {esc(p["year"] or "年份待核验")} · {"原始书目 · 初步分类" if p["originalRecord"] else "增补书目 · 元数据编目"}</small></span><span aria-hidden="true">↗</span></a></li>' for p in data['papers'])
    payload = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f'''<link rel="stylesheet" href="{esc(css)}"><script src="{esc(js)}" defer></script>
<main id="main" class="paper-map-page">
  <section class="map-heading"><div><p class="eyebrow">THE PAPER ATLAS / TOPIC EXPLORER</p><h1>论文地图</h1></div><p>按主题探索 {len(data['papers'])} 篇论文。<br>查看原文、代码与阅读状态。</p></section>
  <section class="paper-map" id="paper-map" aria-label="论文主题地图" data-view="list">
    <div class="map-toolbar" hidden>
      <div class="map-search-wrap"><label for="map-search" class="sr-only">搜索地图中的论文</label><span aria-hidden="true">⌕</span><input id="map-search" type="search" role="combobox" autocomplete="off" aria-autocomplete="list" aria-controls="map-suggestions" aria-expanded="false" placeholder="搜索标题、作者、标签…"><button type="button" id="map-search-clear" aria-label="清空地图搜索" hidden>×</button><ul id="map-suggestions" role="listbox" aria-label="匹配的论文" hidden></ul></div>
      <p id="map-result-count" role="status" aria-live="polite">{len(data['papers'])} 篇论文</p>
      <div class="map-view-toggle" role="group" aria-label="浏览方式"><button type="button" data-map-view="map" aria-pressed="false"><span aria-hidden="true">⊙</span> 地图</button><button type="button" data-map-view="list" aria-pressed="true"><span aria-hidden="true">☷</span> 列表</button></div>
    </div>
    <div class="map-topics" aria-label="主题筛选" hidden><button type="button" data-map-topic="all" aria-pressed="true">全部主题<span>{len(data['papers'])}</span></button>{topics}</div>
    <div class="map-workspace">
      <div class="map-explore">
        <div class="map-canvas-wrap" hidden>
          <svg id="map-canvas" role="group" aria-label="论文主题地图。方向键切换论文，Enter 查看，加减键缩放，Home 显示全部。" aria-describedby="map-help map-legend" tabindex="0"><defs><pattern id="map-dot-grid" width="30" height="30" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".7" fill="#d7dad9"/></pattern></defs><rect width="100%" height="100%" fill="url(#map-dot-grid)" aria-hidden="true"/><g class="map-world"><g class="map-regions" aria-hidden="true"></g><g class="map-edges" aria-hidden="true"></g><g class="map-nodes"></g></g></svg>
          <div class="map-canvas-top"><span><i aria-hidden="true"></i> 主题地图</span><span>95 PAPERS / 4 TOPICS</span></div>
          <div class="map-controls" role="group" aria-label="地图缩放"><button type="button" data-camera="in" aria-label="放大地图">+</button><button type="button" data-camera="out" aria-label="缩小地图">−</button><span id="map-zoom" aria-live="off">100%</span><button type="button" data-camera="fit" aria-label="显示当前筛选的全部论文">全览 <span aria-hidden="true">↗</span></button></div>
          <p id="map-help" class="map-help">拖动平移 · Ctrl / ⌘ + 滚轮缩放 · 方向键选择</p>
          <p class="map-empty" hidden>没有匹配论文。<br><button type="button" data-map-reset>清空筛选</button></p>
          <div class="map-hover-card" hidden aria-hidden="true"></div>
        </div>
        <div class="map-list-wrap"><p class="map-list-intro">按主题浏览全部书目。选择论文查看资源，也可直接进入完整详情。</p><ul class="map-paper-list">{rows}</ul><p class="map-list-empty" hidden>没有匹配论文。<button type="button" data-map-reset>清空筛选</button></p></div>
      </div>
      <aside class="map-sidebar" aria-label="论文详情与资源">
        <div class="map-panel-welcome"><span class="map-welcome-symbol" aria-hidden="true">✳</span><p class="eyebrow">A PLACE TO START</p><h2>从一篇论文，<br>继续探索。</h2><p>选择一个节点，查看论文、PDF、代码与阅读状态，再沿共享标签发现其他条目。</p><div class="map-welcome-facts"><div><strong>{len(data['papers'])}</strong><span>已收录论文</span></div><div><strong>04</strong><span>目录主题</span></div><div><strong>00</strong><span>已核验引用关系</span></div></div><p class="map-truth-note">73 条原始书目的分类仅按题名初步整理；22 条增补记录为元数据编目。地图不会把编目状态当成精读或复现结论。</p><a class="map-catalog-link" href="{esc(base)}index.html#catalog">回到完整目录 <span aria-hidden="true">↗</span></a></div>
        <div class="map-panel-selected" hidden><div class="map-panel-top"><span>论文与资源</span><button type="button" id="map-panel-close" aria-label="关闭论文详情">关闭 ×</button></div><div id="map-panel-content"></div></div>
      </aside>
    </div>
    <div id="map-legend" class="map-legend"><p><span class="map-legend-node" aria-hidden="true"></span> 同尺寸节点代表论文，颜色代表目录主题</p><p><span class="map-legend-edge" aria-hidden="true"></span> 虚线 = 共享标签的主题相近（推断），不是引用或方法继承</p><p>位置与距离仅用于导航排布，不代表学术影响力或测得的相似度</p></div>
    <p class="map-access-note">不便操作地图？列表提供同一组论文与全部资源入口。普通滚轮保持页面滚动；移动端默认列表，地图可选。</p>
    <noscript><p class="map-noscript">交互地图需要 JavaScript；全部 {len(data['papers'])} 篇论文的详情链接仍可直接使用。</p></noscript>
    <script type="application/json" id="paper-map-data">{payload}</script>
  </section>
</main>'''
