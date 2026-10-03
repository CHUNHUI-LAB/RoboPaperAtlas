"""Content-first Library. Existing catalogue evidence and routes remain intact."""
from pathlib import Path
import hashlib
from topic_labels import TOPIC_LABELS, method_tags, resource_kinds, RESOURCE_LABELS, OVERLAY, CHINESE
from discovery_facets import GROUPS, for_catalog, counts as group_counts, method_label


# Official abstract: https://proceedings.mlr.press/v270/liu25b.html (checked 2026-10-03).
# Presentation copy only; does not mutate canonical metadata or reading status.
FEATURE_SUMMARIES = {'rpa-0067': '以视觉输入生成移动与末端目标，通过低层全身跟踪协调腿与臂。'}


def render(data, card, categories, shell, esc):
    root = Path(__file__).resolve().parents[1]
    papers = data['papers']
    total = len(papers)
    report_count = sum(s['status'] == 'imported' for p in papers for s in p['stages'].values())
    memberships = for_catalog(papers, OVERLAY['records'])
    counts = group_counts(memberships)
    topic_labels = {key: label for key, label, _ in GROUPS}
    hints = {key: english for key, _, english in GROUPS}
    short_labels = {**topic_labels, 'methods-resources': '方法与资源'}
    tabs = f'<button class="topic-filter active" type="button" data-topic="all" aria-pressed="true"><span>全部</span><b>{total}</b></button>'
    tabs += ''.join(
        f'<button class="topic-filter" type="button" data-topic="{key}" aria-pressed="false" title="{esc(hints[key])}" aria-label="{esc(short_labels[key])}"><span>{esc(short_labels[key])}</span><b>{counts[key]}</b></button>'
        for key in topic_labels)
    topic_options = ''.join(f'<option value="{key}">{esc(short_labels[key])} · {counts[key]}</option>' for key in topic_labels)
    years = sorted({p['publication_year'] for p in papers if p.get('publication_year')}, reverse=True)
    methods = sorted({t for p in papers for t in method_tags(p)}, key=str.casefold)
    method_options = ''.join(f'<option value="{esc(t)}">{esc(method_label(t))}</option>' for t in methods)
    resources = sorted({t for p in papers for t in resource_kinds(p)})
    resource_options = ''.join(f'<option value="{t}">{RESOURCE_LABELS[t]}</option>' for t in resources)
    direction_options = ''.join(f'<option value="{key}">{esc(CHINESE[key])}</option>' for key in TOPIC_LABELS)
    common_methods = ''.join(f'<button type="button" class="method-chip" data-method-chip="{t}" aria-pressed="false">{esc(method_label(t))}</button>' for t in ['WBC', 'MPC', 'RL', 'Imitation Learning', 'VLA', 'World Model'])
    year_options = ''.join(f'<option value="{y}">{y}</option>' for y in years)
    ordered = sorted(papers, key=lambda p: (not p['citation_verified'], -(p.get('bibliographic_year') or 0), p['title'].casefold()))

    body = f'''<main id="main" class="atlas-experience library-main">
  <header class="f2-page-intro"><h1>论文库</h1><p>从研究问题出发，连接方法、证据与实现。</p></header>
  <section class="catalog-section" id="catalog" aria-labelledby="catalog-title">
    <form class="library-search" role="search" aria-label="搜索当前论文目录">
      <label class="sr-only" for="search">搜索标题、作者或关键词</label><span class="library-search-icon" aria-hidden="true">⌕</span>
      <input id="search" class="catalog-search-trigger" type="search" maxlength="512" placeholder="搜索论文、作者或关键词" autocomplete="off" aria-controls="paper-grid">
      <button id="clear-catalog-search" type="button" aria-label="清除目录搜索" hidden>✕</button><button class="library-search-submit" type="submit" aria-label="搜索论文"><span aria-hidden="true">→</span></button>
    </form>
    <div class="catalog-toolbar">
      <div class="topic-filters" role="group" aria-label="交叉浏览入口，选择一个方向">{tabs}</div>
      <label class="mobile-topic-select">研究方向<select id="topic-select"><option value="all">全部 · {total}</option>{topic_options}</select></label>
    </div>
    <div class="catalog-heading" id="catalog-results"><div><p class="library-eyebrow">论文库</p><h2 id="catalog-title">全部论文 · {total} 篇</h2></div><button type="button" id="clear-all-filters" hidden>清除筛选 ×</button></div>
    <p id="topic-description" class="topic-description">按研究问题查找论文，再查看概览、原文和阅读报告。</p><p class="catalog-scope-note">分组可交叉，数量不可相加 · 来源核验与全文阅读分开记录</p>
    <div class="catalog-main">
      <div class="results-bar"><p id="result-count" role="status" aria-live="polite">共 {total} 篇论文</p>
        <div class="results-actions">
          <details class="filter-disclosure"><summary>更多筛选 <span aria-hidden="true">＋</span></summary>
            <div class="filter-panel">
              <div class="filter-panel-heading"><h2 id="catalog-filter-title">筛选论文</h2><button type="button" data-filter-close aria-label="关闭筛选">✕</button></div>
              <div class="common-methods" role="group" aria-label="常用方法">{common_methods}</div>
              <div class="filter-fields">
                <label>细分研究方向<select id="direction-filter"><option value="all">全部细分方向</option>{direction_options}</select></label>
                <label>全部方法<select id="method-filter"><option value="all">全部方法</option>{method_options}</select></label>
                <label>资源类型<select id="resource-filter"><option value="all">全部类型</option>{resource_options}</select></label>
                <label>出版年份<select id="year-filter"><option value="all">全部年份</option>{year_options}<option value="unknown">未知 / 尚无正式出版年</option></select></label>
                <label>原始书目核验状态<select id="status-filter"><option value="all">全部状态</option><option value="verified">原始书目已核验</option><option value="pending">原始书目待核验</option></select></label>
                <label>阅读报告<select id="reading-filter"><option value="all">全部阅读状态</option><option value="imported">已有阶段报告</option><option value="not-imported">尚未导入报告</option></select></label>
              </div>
              <p>核验状态筛选只依据原始书目记录；独立补充的核验状态见各条详情。正式出版年份只使用已核验值。细分方向、方法与资源类型独立保留；四条分类边界仍待复核。</p>
              <button id="apply-catalog-filters" class="primary-link" type="button" data-filter-close>查看 {total} 篇结果</button>
            </div>
          </details>
          <label class="sort-label"><span class="sr-only">排序</span><select id="sort"><option value="curated">来源核验优先</option><option value="newest">记录年份降序</option><option value="title">标题 A → Z</option></select></label>
          <div class="view-switch" role="group" aria-label="目录显示方式"><button type="button" data-view="list" aria-pressed="true" aria-label="列表视图">☷</button><button type="button" data-view="cards" aria-pressed="false" aria-label="卡片视图">▦</button></div>
        </div>
      </div>
      <div class="active-filters" id="active-filters" aria-label="当前筛选条件" hidden></div>
      <div class="paper-grid list-view" id="paper-grid" data-default-view="list">{''.join(card(p, library=True) for p in ordered)}</div>
      <div class="empty-state" id="empty-state" hidden><h3>暂时没有匹配的论文</h3><p id="empty-query">试试作者或方法名，或放宽当前筛选条件。</p><button class="secondary-button" id="reset-filters" type="button">清除搜索与筛选</button></div>
      <button class="load-more" id="load-more" type="button" hidden>显示更多论文 ↓</button>
      <noscript><p class="noscript-note">当前已显示全部论文。搜索、筛选和快捷预览需要 JavaScript；点击题名仍可打开完整详情页。</p></noscript>
    </div>
  </section>
  <section class="reading-roadmap" aria-labelledby="reading-roadmap-title">
    <div><p class="library-eyebrow">READING / 阅读档案</p><h2 id="reading-roadmap-title">每次阅读，都有迹可循</h2><p>按论文、阶段与版本查阅实际报告。阅读完成与独立复现分别记录。</p><a class="text-link" href="reading/index.html">浏览阅读档案 · {report_count} 份报告已导入 ↗</a></div>
    <div class="roadmap-stages"><div><span>01</span><h3>初读</h3><p>建立研究问题、核心贡献与证据入口。</p></div><div><span>02</span><h3>写作精读</h3><p>梳理论证结构、研究缺口与表达。</p></div><div><span>03</span><h3>方法精读</h3><p>结合公式、框架与公开代码理解方法。</p></div></div>
  </section>
</main>'''
    return shell('RoboPaperAtlas', body, library=True)

