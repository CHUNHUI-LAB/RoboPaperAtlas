#!/usr/bin/env python3
"""Dependency-free deterministic publisher for the public catalog."""
import argparse, html, json, shutil, hashlib
from validate import validate_catalog, validate_frontier, check_url
from pathlib import Path
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
from topic_labels import TOPIC_LABELS, TOPIC_FULL_NAMES, TOPIC_HINTS, paper_topics, primary_topic, classification, method_tags, resource_kinds, taxonomy_search, RESOURCE_LABELS, TAXONOMY
CATEGORIES={key:(TOPIC_LABELS[key],TOPIC_FULL_NAMES[key]) for key in TOPIC_LABELS}
REPO='https://github.com/CHUNHUI-LAB/RoboPaperAtlas'
STAGES=[('stage1','01','Stage 1','初读','建立研究问题、核心贡献与证据入口。'),('stage2','02','Stage 2','写作精读','梳理论文论证、研究缺口与表达结构。'),('stage3','03','Stage 3','方法精读','结合公式、框架与公开代码理解方法。')]
def esc(s): return html.escape(str(s) if s is not None else '',quote=True)
def link(url,text,cls=''):
    if not url: return ''
    check_url(url)
    return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{esc(text)} <span aria-hidden="true">↗</span></a>'
def yearlabel(p):
    y=p.get('bibliographic_year')
    return str(y) if y else '年份待核验'
def display_title(p): return (p.get('verified_overlay') or {}).get('title') or p['title']
def author_text(p):
    a=(p.get('verified_overlay') or {}).get('authors') or p.get('authors') or ['作者待核验']
    return ', '.join(a) if isinstance(a,list) else a


def asset_url(prefix,name):
    digest=hashlib.sha256((ROOT/'assets'/name).read_bytes()).hexdigest()[:12]
    return prefix+'assets/'+name+'?v='+digest

def data_version():
    return hashlib.sha256((ROOT/'data/catalog.json').read_bytes()+(ROOT/'scripts/build.py').read_bytes()+(ROOT/'data/classification.json').read_bytes()+(ROOT/'scripts/topic_labels.py').read_bytes()).hexdigest()[:12]

def shell(title,body,prefix='',page='catalog',description='RoboPaperAtlas：从研究方向、问题与原始证据探索机器人论文。'):
    theme_assets='' if page=='preview' else f'<link rel="stylesheet" href="{asset_url(prefix,"experience.css")}"><script src="{asset_url(prefix,"experience.js")}" defer></script>'
    if page=='catalog':theme_assets+=f'<link rel="stylesheet" href="{asset_url(prefix,"hero-atlas.css")}"><script src="{asset_url(prefix,"hero-atlas.js")}" defer></script>'
    nav=''.join(f'<a href="{prefix}{href}"'+(' aria-current="page"' if page==name else '')+f'>{label}</a>' for name,href,label in [('catalog','index.html#catalog','Library'),('map','map/index.html','Atlas'),('frontier','frontier/index.html','Radar'),('about','about/index.html','关于与贡献')])
    return f'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="color-scheme" content="light"><meta name="description" content="{esc(description)}"><meta name="theme-color" content="#f8f7f2"><title>RoboPaperAtlas</title><link rel="icon" type="image/svg+xml" href="{asset_url(prefix,'favicon.svg')}"><link rel="stylesheet" href="{asset_url(prefix,'preview-base.css' if page=='preview' else 'styles.css')}"><script src="{asset_url(prefix,'app.js')}" defer></script><script src="{asset_url(prefix,'frontier.js')}" defer></script><script src="{asset_url(prefix,'interface.js')}" defer></script><script src="{asset_url(prefix,'motion.js')}" defer></script><script src="{asset_url(prefix,'brief-reader.js')}" defer></script>{theme_assets}</head>
<body class="page-{page}" data-root="{prefix}" data-data-version="{data_version()}"><a class="skip-link" href="#main">跳到主要内容</a><header class="site-header"><div class="header-inner"><a class="brand" href="{prefix}index.html" aria-label="RoboPaperAtlas 首页"><span class="brand-mark" aria-hidden="true"><i></i><i></i><i></i><i></i></span><span>RoboPaper<span class="brand-light">Atlas</span></span></a><nav id="main-nav" aria-label="主导航">{nav}{link(REPO,'GitHub','github-link')}</nav><div class="header-actions"><button type="button" class="global-search-trigger" aria-label="搜索论文（Control 或 Command K）" aria-haspopup="dialog"><span aria-hidden="true">⌕</span><span class="search-trigger-label">搜索论文</span><kbd>⌘ K</kbd></button><button type="button" class="mobile-menu" aria-expanded="false" aria-controls="main-nav">菜单 <span aria-hidden="true">☰</span></button></div></div></header>{body}<footer class="site-footer"><div><a class="footer-brand" href="{prefix}index.html">RoboPaperAtlas<span>机器人研究的开放地图</span></a><p>从原始论文出发，让每一次理解都有据可查。</p></div><div class="footer-right"><span>编目核验 ≠ 阅读完成 ≠ 独立复现</span><span>© 2026 · 第三方论文与代码遵循各自许可</span></div></footer><dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-heading"><h2 id="search-title">搜索论文目录</h2><button class="dialog-close" type="button" aria-label="关闭搜索">✕</button></div><form id="global-search-form" role="search"><label class="global-input-label"><span class="sr-only">论文标题、作者或关键词</span><input id="global-search-input" type="search" placeholder="标题、作者或关键词…" autocomplete="off"></label></form><p class="global-search-scope">检索公开书目与编目备注，不检索阅读报告正文</p><p id="global-search-status" role="status" aria-live="polite">输入关键词开始搜索</p><ul id="global-search-results"></ul><div class="dialog-footer"><span>↑ ↓ 选择 · Enter 打开 · Esc 关闭</span><a id="global-all-results" href="{prefix}index.html#catalog">进入完整目录 ↗</a></div></dialog><dialog class="paper-drawer" id="paper-drawer" aria-labelledby="drawer-title"><div class="drawer-top"><span>论文速览</span><button type="button" class="drawer-close" aria-label="关闭论文速览">✕</button></div><div id="drawer-body"><h2 id="drawer-title">正在载入</h2></div></dialog><div class="toast" role="status" aria-live="polite" hidden></div></body></html>'''

def badge(p): return '<span class="badge verified"><span aria-hidden="true">●</span> 来源已核验</span>' if p['citation_verified'] else '<span class="badge pending"><span aria-hidden="true">○</span> 书目待核验</span>'
def imported_count(p):return sum(s['status']=='imported' for s in p['stages'].values())
def card(p):
    title=display_title(p); authors=author_text(p); cat=CATEGORIES[primary_topic(p)][0]
    desc=p.get('summary') or '已收录原始书目。题名、作者、年份与出版版本尚待逐项核验，阅读档案尚未导入。'
    c=classification(p)
    tags=''.join(f'<span>{esc(t)}</span>' for t in method_tags(p)[:3])
    resource_tags=''.join(f'<span>{esc(RESOURCE_LABELS[t])}</span>' for t in resource_kinds(p))
    report_count=imported_count(p)
    stage_badge=(f'<a class="card-report-link" href="papers/{p["id"]}/index.html#reading">{report_count} 份阅读报告 ↗</a>' if report_count else '<span class="card-stage" title="三个阶段的阅读报告均尚未导入">S1 <i></i> S2 <i></i> S3 <i></i><span class="sr-only">均未导入</span></span>')
    yearkind={'publication':'出版','preprint':'预印本','user_provided':'原始记录'}.get(p.get('year_basis'),'待核验')
    q=' '.join([p['title'],title,p.get('short_name',''),authors,desc,taxonomy_search(p),*p.get('tags',[])])
    return f'''<article class="paper-card" data-search="{esc(q.casefold())}" data-category="{primary_topic(p)}" data-canonical-category="{p['category']}" data-topics="{' '.join(paper_topics(p))}" data-methods="{esc('|'.join(method_tags(p)))}" data-resources="{'|'.join(resource_kinds(p))}" data-year="{p.get('publication_year') or 'unknown'}" data-status="{'verified' if p['citation_verified'] else 'pending'}" data-title="{esc(title.casefold())}" data-sort-year="{p.get('bibliographic_year') or 0}"><span class="paper-art" aria-hidden="true" style="position:absolute"></span><div class="card-top"><span class="card-category" title="{esc(TOPIC_HINTS[primary_topic(p)])}">{esc(cat)}</span>{badge(p)}</div><h3><a href="papers/{p['id']}/index.html">{esc(title)}</a></h3><p class="authors" title="{esc(authors)}">{esc(authors)}</p><p class="card-summary">{esc(desc)}</p><div class="tags">{tags}</div><div class="topic-crosslabels" aria-label="研究问题与资源类型"><span>{esc(c["problemLabel"])}</span>{resource_tags}{'<span>分类边界待复核</span>' if c["needsReview"] else ''}</div><div class="card-bottom"><span class="paper-year">{esc(yearlabel(p))}<small>{yearkind}</small></span>{stage_badge}<button class="card-arrow" type="button" data-direction-label="{esc(cat)}" data-problem-label="{esc(c['problemLabel'])}" data-preview="{p['id']}" aria-label="快速查看 {esc(title)}">↗</button></div></article>'''

def classification_html(p):
    c=classification(p)
    methods=''.join('<li>'+link(t['source'],t['label'])+'<small>'+esc(t['evidence_scope'])+' · '+esc(t['confidence'])+'</small></li>' for t in c['methodTags']) or '<li>当前证据范围未列出方法标签</li>'
    resources=', '.join(RESOURCE_LABELS[x] for x in c['resourceKinds']) or '未列为资源型贡献'
    sources=''.join('<li>'+link(u,'分类来源 '+str(i+1))+'</li>' for i,u in enumerate(c['sources']))
    review=('<p class="classification-review">分类边界待复核：'+esc(c['reviewNote'])+'</p>') if c['needsReview'] else ''
    return f'<section class="classification-note" aria-labelledby="classification-title"><h3 id="classification-title">研究问题与分类证据</h3><dl><div><dt>主研究方向</dt><dd>{esc(TOPIC_LABELS[c["direction"]])}</dd></div><div><dt>具体问题</dt><dd>{esc(c["problemLabel"])}</dd></div><div><dt>资源类型</dt><dd>{esc(resources)}</dd></div></dl><p>{esc(c["rationale"])}</p>{review}<p class="fine-print">依据主来源的摘要、贡献或项目说明进行编辑归类；方法标签记录有证据支持的组成部分，并不表示它就是论文的主要创新。分类核查不代表全文精读，未列出的标签也不表示该方法不存在。</p><details><summary>方法标签与来源</summary><ul>{methods}</ul><ul>{sources}</ul></details></section>'

def home(data):
    from home_page import render
    return render(data,card,CATEGORIES,shell,esc)

def details(p):
    title=display_title(p); prefix='../../'; authors=author_text(p); cat=CATEGORIES[primary_topic(p)][0]
    original=p.get('original_metadata'); overlay=p.get('verified_overlay')
    original_html=''
    if original:
        original_html=f'<details class="original-record"><summary>查看保留的原始书目</summary><p><strong>题名</strong> {esc(original.get("title"))}</p><p><strong>作者</strong> {esc(original.get("authors"))}</p><p><strong>年份</strong> {esc(original.get("year") or "未提供")}</p><p>原始书目为用户提供、尚未核验的信息；核验结果独立保留，不覆盖原记录。</p></details>'
    links=link(p.get('paper_url'),'出版 / 论文页面','resource-link')+link(p.get('pdf_url'),'出版方 PDF' if p.get('pdf_kind')=='publisher' else '预印本替代 PDF','resource-link')+link(p.get('project_url'),'官方项目','resource-link')+''.join(link(x,'代码 / 数据入口'+(f' {i+1}' if len(p.get('code_urls',[]))>1 else ''),'resource-link') for i,x in enumerate(p.get('code_urls',[])))
    if not links: links='<p class="muted">官方论文、PDF 与代码链接尚待核验。</p>'
    vals=[('正式出版年',p.get('publication_year') or '尚未核验 / 未确认正式出版'),('首次预印本年',p.get('preprint_year') or '尚未核验'),('记录年份',yearlabel(p)),('出版 / 载体',p.get('venue') or '尚未核验'),('PDF 版本',p.get('pdf_edition') or '尚未核验'),('出版 DOI',p.get('doi') or '尚未核验'),('最近核验',p.get('verified_at') or '待开展')]
    facts=''.join(f'<div><dt>{label}</dt><dd>{esc(val)}</dd></div>' for label,val in vals)
    notes=[n for n in p.get('notes',[]) if n]
    caveats='<ul class="notes-list">'+''.join(f'<li>{esc(n)}</li>' for n in notes)+'</ul>' if notes else '<p class="muted">暂无补充核验记录。</p>'
    sources=''.join(f'<li>{link(s,urlsplit(s).netloc + urlsplit(s).path)}</li>' for s in dict.fromkeys(p.get('sources',[]))) or '<li>尚无核验来源记录。</li>'
    report_count=imported_count(p);stage_rows=[]
    for key,num,name,label,description in STAGES:
        state=p['stages'][key]
        if state['status']=='imported':
            artifact=state['artifacts'][0];entry=f'<a class="stage-report-link" href="{prefix}{esc(artifact["path"])}">阅读 HTML ↗<small>{esc(artifact["version"])} · 已导入</small></a>'
        else:entry='<span class="unavailable">尚未导入</span>'
        stage_rows.append(f'<div class="stage-slot"><span class="stage-index">{num}</span><div><h3>{name} · {label}</h3><p>{description}</p></div>{entry}</div>')
    stages=''.join(stage_rows)
    reading_note='已导入独立中文阅读分析；代码审阅以报告所列范围为准，未运行训练、仿真或硬件复现。' if report_count else '阅读报告尚未导入；本页不是论文精读、实验复现或代码审计。'

    desc=p.get('summary') or '本条保留原始书目；研究问题分类另据主来源摘要或项目说明整理，全文方法与结论未因此视为已精读。'
    c=classification(p)
    taxonomy_html=classification_html(p)
    body=f'''<main id="main" class="detail-main"><a class="back-link" href="../../index.html#catalog">← 返回论文目录</a><div class="detail-toolbar"><span>论文详情 / 公开书目 · <a href="../../map/index.html?paper={p['id']}">在地图中查看 ↗</a></span><button class="copy-page" type="button">复制本页链接 ↗</button></div><div class="detail-heading"><div class="detail-kicker"><span title="{esc(TOPIC_HINTS[primary_topic(p)])}">{esc(cat)}</span><span> / </span><span>{esc(yearlabel(p))}</span>{badge(p)}</div><p class="detail-topic-description">{esc(TOPIC_HINTS[primary_topic(p)])}</p><h1>{esc(title)}</h1><p class="detail-authors">{esc(authors)}</p><div class="tags" aria-label="有来源支持的方法标签">{''.join(f'<span>{esc(t)}</span>' for t in method_tags(p))}</div></div><nav class="detail-toc" aria-label="本页导航"><span>本页内容</span><a href="#overview">编目说明</a><a href="#reading">阅读档案</a><a href="#versions">版本提醒</a><a href="#sources">核验来源</a></nav><div class="detail-layout"><div class="detail-content"><section class="detail-section" id="overview"><p class="eyebrow">CATALOG NOTE</p><h2>为什么收录</h2><p class="lead-note">{esc(desc)}</p><div class="verification-box"><strong>{'来源核验范围' if p['citation_verified'] else '书目待核验'}</strong><p>{esc(p.get('verification_scope') or '题名、作者和年份由用户提供，尚未完成完整书目核验；研究分类的证据与范围单独列出。')}</p><p>{reading_note}</p></div>{original_html}{taxonomy_html}</section><section class="detail-section" id="reading"><div class="section-title-row"><div><p class="eyebrow">READING ARCHIVE</p><h2>分阶段阅读档案</h2></div><span class="tiny-pill">{report_count} 个已导入报告</span></div><div class="stage-slots">{stages}</div><p class="fine-print">只有经过检查、标明来源版本的实际报告才会显示阅读入口。报告版本独立保留，避免新旧结论混用。</p></section><section class="detail-section" id="versions"><p class="eyebrow">SOURCE & VERSION NOTES</p><h2>来源与版本提醒</h2>{caveats}</section><section class="detail-section" id="sources"><p class="eyebrow">EVIDENCE TRAIL</p><h2>核验来源</h2><ol class="source-list">{sources}</ol></section></div><aside class="detail-sidebar"><section class="resource-panel"><p class="eyebrow">GO TO THE SOURCE</p><h2>原文与资源</h2><div class="resource-links">{links}</div><div class="resource-note"><strong>PDF 选择</strong><p>{esc(p.get('pdf_note') or '优先链接正式出版方版本；未核验前不补造链接。')}</p></div><div class="resource-note"><strong>代码可用性</strong><p>{esc(p.get('code_note') or '尚未核验。未提供链接不代表代码不存在。')}</p></div></section><section class="metadata-panel"><h2>书目信息</h2><dl>{facts}</dl></section><a class="correction-link" href="{REPO}/issues/new?title=Metadata%20correction%3A%20{p['id']}" target="_blank" rel="noopener noreferrer">发现信息有误？提交修正 ↗</a></aside></div></main>'''
    return shell(title,body,prefix=prefix,page='detail',description=desc)

def about(report_count=0):
    pilot_link='<p><a class="primary-link" href="../papers/rpa-0062/index.html#reading">查看 UMI-on-Legs 三阶段报告 ↗</a></p>' if report_count else ''
    body=f'''<main id="main" class="about-main"><a class="back-link" href="../index.html#catalog">← 返回论文目录</a><p class="eyebrow">ABOUT THE ATLAS</p><h1>一张持续生长的<br><span class="serif-accent">机器人研究地图</span>。</h1><p class="about-lead">RoboPaperAtlas 是一个中文机器人论文目录与阅读档案。我们把文献、原始证据和阅读产物放在同一条可追溯的路径上，方便检索、理解与持续补充。</p><div class="about-grid"><section id="standards"><p class="eyebrow">01 / EDITORIAL STANDARDS</p><h2>收录与核验标准</h2><ul><li><strong>书目待核验</strong>：原始题名、作者和年份按提供内容保存；研究方向按另外保存的来源证据整理，不等于原始书目已全部核验。</li><li><strong>来源已核验</strong>：已检查主来源中的书目信息或官方资源，核验范围和日期写在详情页。</li><li><strong>核验与阅读分开</strong>：来源核验不代表完成全文阅读、代码审计或独立复现。当前已导入 {report_count} 份实际报告；其他入口仍保持未导入。</li><li><strong>出版与预印本分开</strong>：正式出版年、首次预印本年和记录年份分别保存；未知值不猜测。</li><li><strong>版本明确</strong>：优先正式出版方 PDF；使用预印本时标明版本和原因。同名不同论文不合并。</li></ul></section><section><p class="eyebrow">02 / THE READING ARCHIVE</p><h2>阅读档案如何生长</h2>{pilot_link}<p>每篇论文预留 Stage 1 初读、Stage 2 写作精读、Stage 3 方法精读三个独立入口。实际报告导入前，入口始终标记为“尚未导入”。</p><p>导入的报告需要注明对应论文版本、产物版本、公开授权与内容检查结果。更新不抹除历史版本；论文、报告和代码使用不同的版本标识。</p><p>当前搜索是本地书目检索，覆盖标题、作者、关键词与编目备注，不宣称已检索尚未导入的全文报告。</p></section><section><p class="eyebrow">03 / OPEN CONTRIBUTIONS</p><h2>一起补全地图</h2><p>欢迎补充遗漏文献、修正元数据、核验官方来源，以及贡献有权公开的原创阅读报告。</p><ol><li>先查找目录，确认不是重复条目。</li><li>在仓库提交 Issue 或 Pull Request，附官方来源。</li><li>说明变化、来源版本和权限；通过检查后再合并。</li></ol>{link(REPO+'/blob/main/CONTRIBUTING.md','阅读贡献指南','primary-link')}{link(REPO+'/issues','浏览问题与建议','text-link')}</section><section><p class="eyebrow">04 / RIGHTS & LIMITS</p><h2>开放目录，尊重原作</h2><p>论文 PDF 仅以外部链接形式提供，不在本库重新分发。可公开访问不等于可转载，第三方论文、数据、图表和代码遵循各自许可。</p><p>引用和简短编目说明不替代原文。代码仓库存在不等于权重、数据或完整实现已发布；未检查的可用性会明确标注。</p><p>初始版本没有账户、追踪脚本或外部字体。搜索与筛选在浏览器本地运行。访问外部资源后，适用对应网站的政策。</p></section></div></main>'''
    return shell('关于与贡献',body,prefix='../',page='about')

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--output',default='dist'); args=parser.parse_args()
    target=(ROOT/args.output).resolve()
    if target==ROOT or ROOT not in target.parents: raise SystemExit('Output must be a subdirectory of this repository.')
    if not (ROOT/'data/frontier.json').exists():
        from assemble_frontier import assemble
        assemble()
    from reports import assemble_reports,report_path
    reports=assemble_reports(ROOT)
    data=json.loads((ROOT/'data/catalog.json').read_text()); validate_catalog(data,reports); target.mkdir(parents=True,exist_ok=True)
    # Remove only generated output; input and versioned report directories stay intact.
    shutil.rmtree(target); target.mkdir(); shutil.copytree(ROOT/'assets',target/'assets')
    from design_preview import render as render_design_preview
    (target/'design-preview').mkdir(); (target/'design-preview/index.html').write_text(render_design_preview(data,shell,card,asset_url))
    (target/'index.html').write_text(home(data)); (target/'about').mkdir(); (target/'about/index.html').write_text(about(len(reports)))
    from map_page import map_html
    (target/'map').mkdir()
    map_body=map_html(data,base='../',css=asset_url('../','paper-map.css'),js=asset_url('../','paper-map.js'),report_records=reports)
    (target/'map/index.html').write_text(shell('Atlas',map_body,prefix='../',page='map'))
    from reader_preview import render as render_reader_preview
    (target/'reader-preview/umi-on-legs').mkdir(parents=True)
    (target/'reader-preview/umi-on-legs/index.html').write_text(render_reader_preview(ROOT,shell,asset_url))
    from preview_artifacts import write_preview
    write_preview(ROOT,target)
    for p in data['papers']:
        d=target/'papers'/p['id']; d.mkdir(parents=True); (d/'index.html').write_text(details(p))
    from frontier_page import render as frontier_render
    frontier=json.loads((ROOT/'data/frontier.json').read_text()); validate_frontier(frontier)
    from briefs import load_archive, section as brief_section
    brief_index, brief_records=load_archive(ROOT)
    latest_brief=brief_records[brief_index['latest']]
    (target/'frontier').mkdir(); (target/'frontier/index.html').write_text(frontier_render(frontier,data,shell,link,brief_section(latest_brief,brief_index,prefix='../')))
    for date,record in brief_records.items():
        folder=target/'frontier/briefs'/date;folder.mkdir(parents=True)
        content='<main id="main" class="brief-archive-page"><a class="back-link" href="../../index.html#daily-brief">← 返回前沿动态</a>'+brief_section(record,brief_index,prefix='../../../',archive=True)+'</main>'
        (folder/'index.html').write_text(shell(record['title'],content,prefix='../../../',page='frontier'))
    (target/'data').mkdir(); (target/'data/briefs').mkdir(); shutil.copyfile(ROOT/'data/briefs/index.json',target/'data/briefs/index.json')
    for entry in brief_index['briefs']:
        shutil.copyfile(ROOT/'data/briefs'/entry['path'],target/'data/briefs'/entry['path'])
    (target/'data/frontier.json').write_text(json.dumps(frontier,ensure_ascii=False,indent=2)+'\n'); (target/'data/search-index.json').write_text(json.dumps([{'id':p['id'],'title':display_title(p),'authors':author_text(p),'category':CATEGORIES[primary_topic(p)][0],'text':' '.join([p['title'],display_title(p),p.get('short_name') or '',author_text(p),p.get('summary') or '',taxonomy_search(p),*p.get('tags',[])])} for p in data['papers']],ensure_ascii=False,separators=(',',':'))+'\n'); (target/'data/catalog.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    for report in reports:
        path=report_path(report);dest=target/path;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/path,dest)
    shutil.copyfile(ROOT/'data/reports.json',target/'data/reports.json')
    (target/'.nojekyll').write_text(''); (target/'404.html').write_text(shell('未找到页面','<main id="main" class="about-main"><p class="eyebrow">404 / OFF THE MAP</p><h1>这条路径暂未收录。</h1><p>页面可能移动了，试试从目录重新寻找。</p><a class="primary-link" href="/RoboPaperAtlas/index.html">返回论文目录 →</a></main>',prefix='/RoboPaperAtlas/'))
    print(f'Built {len(data["papers"])} papers → {target.relative_to(ROOT)}')
if __name__=='__main__': main()
