"""Reading directory derived only from the catalog's imported stage artifacts."""
from current_reader import entry_path


def render(data, shell, esc, display_title, stages):
    papers = [p for p in data['papers']
              if any(s['status'] == 'imported' and s['artifacts']
                     for s in p['stages'].values())]
    count = sum(s['status'] == 'imported' and bool(s['artifacts'])
                for p in papers for s in p['stages'].values())
    sections = []
    for position, paper in enumerate(papers, 1):
        rows = []
        for key, number, name, label, description in stages:
            state = paper['stages'][key]
            if state['status'] != 'imported' or not state['artifacts']:
                rows.append(f'<li class="reading-stage unavailable"><span class="reading-stage-number">{number}</span>'
                            f'<h3>{label}</h3><p>{description}</p>'
                            '<span class="reading-stage-status">尚未导入</span></li>')
                continue
            artifact = state['artifacts'][0]
            path = entry_path(paper['id'], key) or artifact['path']
            review = '内容已审阅' if artifact['review_status'] == 'content_approved' else '已导入'
            history = ''.join(f'<a href="../{esc(a["path"])}">{"当前固定版本" if index == 0 else "历史版本"} {esc(a["version"])} ↗</a>' for index, a in enumerate(state['artifacts']))
            rows.append(f'<li class="reading-stage"><span class="reading-stage-number">{number}</span>'
                        f'<h3><a class="reading-stage-link" href="../{esc(path)}">{label}<span aria-hidden="true"> ↗</span></a></h3>'
                        f'<span class="reading-stage-status">{esc(artifact["version"])} · {review}</span>'
                        f'<p class="reading-stage-edition">{esc(artifact["source_edition"])}</p>'
                        f'<details class="reading-version-history"><summary>固定与历史版本 <span>{len(state["artifacts"])}</span></summary><div>{history}</div></details></li>')
        edition = ' · '.join(str(v) for v in (paper.get('bibliographic_year'), paper.get('venue')) if v)
        sections.append(f'<section class="reading-paper" aria-labelledby="{esc(paper["id"])}">'
                        f'<div class="reading-paper-heading"><div><p class="eyebrow">{position:02d} / READING DOSSIER</p>'
                        f'<h2 id="{esc(paper["id"])}">{esc(display_title(paper))}</h2>'
                        f'<p class="reading-paper-meta">{esc(edition)}</p></div>'
                        f'<a class="text-link" href="../papers/{esc(paper["id"])}/index.html#reading">论文详情 <span aria-hidden="true">↗</span></a></div>'
                        f'<ul class="reading-stage-list">{"".join(rows)}</ul></section>')
    body = ('<main id="main" class="about-main reading-index">'
            '<header class="reading-hero"><p class="eyebrow">READING ARCHIVE</p><h1>把论文，读成理解。</h1>'
            '<p class="reading-intro">从研究问题到写作脉络，再走进方法与代码。每一阶段，都有清晰的来源。</p>'
            f'<p class="reading-summary">{len(papers)} 篇论文 · {count} 份已导入阶段报告</p>'
            '<p class="fine-print">分阶段阅读档案 · 按论文打开当前报告，固定与历史版本收在各阶段下方。历史版本不重复计入报告数量。</p></header>'
            '<p class="reading-scope-note">阅读范围、来源版本和未核验项见各报告；阅读完成不等于独立复现。</p>'
            + (''.join(sections) or '<p class="reading-empty">阅读报告尚未导入。</p>') + '</main>')
    return shell('Reading · 分阶段阅读档案', body, prefix='../', page='reading')
