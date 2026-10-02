"""Reading directory derived only from the catalog's imported stage artifacts."""
from current_reader import entry_path


def render(data, shell, esc, display_title, stages):
    papers = [p for p in data['papers']
              if any(s['status'] == 'imported' and s['artifacts']
                     for s in p['stages'].values())]
    count = sum(s['status'] == 'imported' and bool(s['artifacts'])
                for p in papers for s in p['stages'].values())
    sections = []
    for paper in papers:
        rows = []
        for key, number, name, label, description in stages:
            state = paper['stages'][key]
            if state['status'] != 'imported' or not state['artifacts']:
                rows.append(f'<li class="reading-stage unavailable"><span>{name} · {label}</span>'
                            '<small>尚未导入</small></li>')
                continue
            artifact = state['artifacts'][0]
            path = entry_path(paper['id'], key) or artifact['path']
            review = '内容已审阅' if artifact['review_status'] == 'content_approved' else '已导入'
            rows.append(f'<li class="reading-stage"><a class="reading-stage-link" href="../{esc(path)}">'
                        f'<span>{name} · {label} ↗</span>'
                        f'<small>{esc(artifact["version"])} · {review}</small></a>'
                        f'<p>{esc(artifact["source_edition"])}</p></li>')
        sections.append(f'<section class="reading-paper" aria-labelledby="{esc(paper["id"])}">'
                        f'<h2 id="{esc(paper["id"])}">{esc(display_title(paper))}</h2>'
                        f'<p><a href="../papers/{esc(paper["id"])}/index.html#reading">论文详情与历史版本 ↗</a></p>'
                        f'<ul class="reading-stage-list">{"".join(rows)}</ul></section>')
    body = ('<main id="main" class="about-main reading-index">'
            '<a class="back-link" href="../index.html#catalog">← 返回论文目录</a>'
            '<p class="eyebrow">READING ARCHIVE</p><h1>分阶段阅读档案</h1>'
            f'<p class="reading-summary">{len(papers)} 篇论文 · {count} 份已导入阶段报告</p>'
            '<p>按论文和阶段打开当前报告。历史版本保留在论文详情中，不重复计入报告数量。</p>'
            '<p>具体阅读范围、来源版本和未核验项以报告内说明为准；阅读完成不等于独立复现。</p>'
            + (''.join(sections) or '<p class="reading-empty">阅读报告尚未导入。</p>') + '</main>')
    return shell('Reading · 分阶段阅读档案', body, prefix='../', page='reading')
