"""Deterministic, script-free views of the reviewed per-paper analysis inputs.

This renderer neither edits the inputs nor reclassifies their claims. It retains
legacy HarnessVLN fragment IDs and namespaces NavHarness DOM IDs only. Run with
--output-dir pointing at the public preview, or --check to detect stale pages.
No PDF, full paper text, image, retrieval, or Stage import is performed.
"""
import argparse
from collections import Counter
from html import escape
import json
from pathlib import Path
import re
from urllib.parse import quote, urlsplit


LABELS = {
    'evidence_linked': '有原文定位', 'author_claim_only': '作者主张',
    'partially_reported': '部分已报告，仍有缺口', 'not_reported': '原文未报告',
    'source_missing': '来源未核读',
    'not_reviewed_implementation_unknown': '实现未核验，具体实现未知',
    'not_applicable_to_this_answer': '本条未涉及实现核验',
}
STYLE = '''body{max-width:1000px;margin:28px auto;padding:0 22px;background:#fbf9f4;color:#24251e;font:16px/1.8 system-ui,sans-serif}h1,h2{font-family:Georgia,serif}a{color:#a4482c;text-underline-offset:3px;overflow-wrap:anywhere}article,.paper-section{border-top:1px solid #d9cbb8;padding:22px 0;scroll-margin-top:15px}.notice{background:#f7ebd9;border:1px solid #dbc3a3;padding:12px;border-radius:6px}.answer,.original,.raw-value{white-space:pre-wrap;overflow-wrap:anywhere}.meta,dt{font-size:13px;color:#755a3c}nav ol{columns:2;column-gap:35px}li{margin:7px 0}dl{margin:8px 0}dd{margin:0 0 12px 16px;min-width:0;overflow-wrap:anywhere}dd dl{border-left:2px solid #e3d5c3;padding-left:12px}dt{font-weight:650}h3{margin-bottom:8px}.source-locators{padding-left:24px}:focus-visible{outline:3px solid #a4482c;outline-offset:4px}@media(max-width:650px){nav ol{columns:1}body{padding:0 15px}dd{margin-left:8px}}'''
RANGE = '<p class="notice" data-c2-range="baseline-weekly">新树重构 39 篇 baseline；<a href="../../radar-trees-c/weekly-2026-10-04.html">旧周窗 6 篇及完整归档</a>，跨范围去重 43 篇。4 篇 weekly 独有候选未进入本次重构双树或论文解析，继续保留旧记录；未补造映射。</p>'


def esc(value):
    return escape(str(value), quote=True)


def scalar(value):
    if value is None:
        return 'null'
    if isinstance(value, bool):
        return 'true' if value else 'false'
    return str(value)


def link(url, label=None, **attrs):
    # Exact approved URLs are preserved, never normalized or guessed.
    if not (url.startswith('#') or url.startswith('../') or url.startswith('analysis/')
            or url.startswith('index.html#') or urlsplit(url).scheme in ('http', 'https')):
        raise ValueError('Unsupported link: ' + url)
    extra = ''.join(f' {esc(k.replace("_", "-"))}="{esc(v)}"' for k, v in attrs.items())
    return f'<a href="{esc(url)}"{extra}>{esc(url if label is None else label)}</a>'


def node_anchor(paper_id, node_id):
    return 'node-' + ('' if paper_id == 'harnessvln' else paper_id + '-') + node_id


def issue_anchor(paper_id, issue, index):
    return f'unknown-{paper_id}-' + str(issue.get('id', index + 1))


def evidence_anchor(paper_id, evidence_id):
    return f'evidence-{paper_id}-{evidence_id}'


def route(paper_id, node=None):
    state = {'paperId': paper_id}
    if node is not None:
        state.update(focus=node.get('parentId') or 'paper-analysis-tree',
                     selected=node.get('id', node.get('nodeId')), drawer='evidence')
    return '../index.html#analysis=' + quote(json.dumps(state, ensure_ascii=False, separators=(',', ':')), safe='')


def source_locators(items, paper_id, context):
    return '<ol class="source-locators">' + ''.join(
        f'<li data-source-locator="{esc(context)}">' + fields(item, paper_id, context='locator') + '</li>'
        for item in items) + '</ol>'


def value_html(value, paper_id, key='', context='metadata'):
    if key == 'sourceLocators':
        return source_locators(value, paper_id, context)
    if key in ('evidenceRecordIds', 'sourceGapIds'):
        anchor = evidence_anchor if key == 'evidenceRecordIds' else lambda p, i: 'unknown-' + p + '-' + i
        return '<ul>' + ''.join('<li>' + link('#' + anchor(paper_id, i), i) + '</li>' for i in value) + '</ul>' if value else '<span class="raw-value">[]</span>'
    if key == 'remainingQuestionId':
        return link('#unknown-' + paper_id + '-' + value, value)
    if isinstance(value, dict):
        return fields(value, paper_id, context=context)
    if isinstance(value, list):
        return '<ul>' + ''.join('<li>' + value_html(v, paper_id, context=context) + '</li>' for v in value) + '</ul>' if value else '<span class="raw-value">[]</span>'
    text = scalar(value)
    if isinstance(value, str) and urlsplit(value).scheme in ('http', 'https'):
        kind = 'PDF 原页链接' if '/pdf/' in value else 'HTML 精确锚点链接' if '/html/' in value and '#' in value else '来源链接'
        return link(value, value) + ('<span class="meta"> · ' + kind + '</span>' if context == 'locator' else '')
    return '<span class="raw-value">' + esc(text) + '</span>' + (' · ' + esc(LABELS[text]) if key in ('state', 'status') and text in LABELS else '')


def fields(record, paper_id, context='metadata', omit=()):
    return '<dl>' + ''.join(f'<dt>{esc(key)}</dt><dd data-field="{esc(key)}">{value_html(value, paper_id, key, context)}</dd>'
                           for key, value in record.items() if key not in omit) + '</dl>'


def paper_stats(schema, mapping, unknowns):
    return {'original': len(schema['nodes']), 'instances': len(mapping['expandedNodes']),
            'nodes': len(schema['nodes']) + len(mapping['expandedNodes']), 'answers': len(mapping['answers']),
            'unknowns': len(unknowns), 'statuses': Counter(a.get('status', a.get('state')) for a in mapping['answers']),
            'implementation_unknown': sum(a.get('codeEvidence', {}).get('status') == 'not_reviewed_implementation_unknown' for a in mapping['answers']),
            'implementation_verified': sum(a.get('codeEvidence', {}).get('status') == 'implementation_verified' for a in mapping['answers'])}


def summary(schema, mapping, unknowns):
    s = paper_stats(schema, mapping, unknowns)
    return (f'{s["original"]} 个原模板节点 + {s["instances"]} 个论文实例 = {s["nodes"]} 个节点；'
            f'{s["answers"]} 项内容记录、{s["unknowns"]} 项未答 / 未知。既有 Stage 未改；未独立复现实验。')


def global_summary(catalog, mappings):
    supported = len(set(mappings) & {p['canonical_id'] for p in catalog['papers']})
    return f'{len(catalog["papers"])} 篇原记录保留；{supported} 篇有内容视图、{len(catalog["papers"]) - supported} 篇待填。原文定位不等于实现核验或独立复现；既有 Stage 未改。'


def render_paper(schema, mapping, ledger, unknowns, paper):
    pid = mapping['paperId']
    nodes = [dict(n) for n in schema['nodes']] + [dict(n, id=n['nodeId']) for n in mapping['expandedNodes']]
    answers = {a['nodeId']: a for a in mapping['answers']}
    all_node_ids = {n['id'] for n in nodes}
    evidence_ids = {r.get('id', r.get('evidenceRecordId')) for r in ledger['records']}
    unknown_ids = {q.get('id') for q in unknowns if q.get('id')}
    for a in mapping['answers']:
        if not set(a.get('sourceGapIds', [])) <= unknown_ids or not set(a.get('evidenceRecordIds', [])) <= evidence_ids:
            raise ValueError('Unresolved per-paper reference')
    s = paper_stats(schema, mapping, unknowns)
    parts = [f'<section class="paper-section" data-paper-id="{esc(pid)}"><h2 id="paper-{esc(pid)}">{esc(paper["short_name"])} · 原方法解析</h2>',
             '<p>' + esc(paper['title']) + '</p>', '<p class="notice">' + esc(summary(schema, mapping, unknowns)) + '</p>',
             '<p class="meta">canonical paper ID: ' + esc(pid) + ' · 固定版 ' + esc(mapping['sourceVersion']) + '</p>',
             '<p>' + '；'.join(f'{esc(LABELS.get(k, k))}（{esc(k)}）：{v}' for k, v in s['statuses'].items()) + '</p>']
    if pid == 'navharness':
        parts.append(f'<p class="notice">{s["implementation_unknown"]} 条方法内容记录的实现未知（not_reviewed_implementation_unknown）；{s["implementation_verified"]} 条实现已核验。PDF 图号与 HTML 锚点分别保留；图号依 PDF，不互换编号。此 NavHarness 固定为 2609.34276v1，与目录中的 Adaptive Goals 2609.39915 不同。</p>')
    else:
        parts.append('<p class="notice">相关源码尚未阅读；代码未运行、实验未独立复现。混合陈述按句内“作者／原文结果／读者解释／证据边界”区分。</p>')
    coverage_id = 'source-coverage' if pid == 'harnessvln' else 'source-coverage-' + pid
    parts.extend(['<p>' + link(route(pid), '在 C2 树中打开这篇论文') + ' · ' + link('#unknowns-' + pid, '全部未答 / 未知') + ' · ' + link('#ledger-' + pid, '本篇证据台账') + ' · ' + link('#' + coverage_id, '核读范围') + '</p>',
                  '<nav aria-label="' + esc(paper['short_name']) + ' 全部节点目录"><h3>全部' + str(s['nodes']) + '个节点目录</h3><ol>'])
    for n in nodes:
        parts.append('<li>' + link('#' + node_anchor(pid, n['id']), n['labelOriginal']) + ('（论文实例）' if n.get('isPaperSpecificInstantiation') else '') + '</li>')
    parts.append('</ol></nav>')
    for n in nodes:
        nid = n['id']
        parts.extend([f'<article id="{esc(node_anchor(pid, nid))}" data-node-key="{esc(nid)}" data-paper-id="{esc(pid)}">',
                      '<h3 class="original">' + esc(n['labelOriginal']) + '</h3>',
                      '<p class="meta">' + esc(nid) + ' · ' + ('论文特定实例' if n.get('isPaperSpecificInstantiation') else '原模板节点') + '</p>'])
        title = mapping.get('contentTitles', {}).get(nid) or n.get('contentTitle')
        if title:
            parts.append('<p>' + esc(title) + '</p>')
        if n.get('parentId'):
            parts.append('<p>父节点：' + link('#' + node_anchor(pid, n['parentId']), n['parentId']) + '</p>')
        for key in ('repeatOfSchemaNode', 'expansionSlot'):
            if n.get(key):
                parts.append('<p>' + key + '：' + link('#' + node_anchor(pid, n[key]), n[key]) + '</p>')
        if nid in answers:
            answer = answers[nid]
            parts.append(f'<section class="answer-record" data-answer-node="{esc(nid)}"><h4>内容记录</h4><div class="answer">{esc(answer["answer"])}</div>')
            parts.append(fields(answer, pid, context='answer', omit=('answer',)))
            parts.append('</section>')
        else:
            parts.append('<p>这是原结构或省略占位；没有为它编写实质回答。下层原问题保持可达。</p>')
        parts.append(link(route(pid, n), '在 C2 树中打开此节点 →') + '</article>')
    parts.append(f'<section id="unknowns-{esc(pid)}"><h3>全部 {len(unknowns)} 项未答 / 未知</h3><p>以下状态值、问题、边界和来源保持原记录；没有答案关联的缺口仍在全篇清单可达。</p><ol>')
    for index, q in enumerate(unknowns):
        parts.append('<li>' + link('#' + issue_anchor(pid, q, index), (q.get('id', '') + ' ' + q.get('topic', q.get('question', ''))).strip()) + '</li>')
    parts.append('</ol>')
    for index, q in enumerate(unknowns):
        qid = q.get('id')
        parts.append(f'<article id="{esc(issue_anchor(pid, q, index))}" data-unknown-id="{esc(qid or index + 1)}" data-paper-id="{esc(pid)}"><h4>{esc(q.get("topic", q.get("question", "未答问题")))}</h4>' + fields(q, pid, context='unknown'))
        backlinks = [a['nodeId'] for a in mapping['answers'] if qid and qid in a.get('sourceGapIds', [])]
        if q.get('nodeId') in all_node_ids:
            backlinks.append(q['nodeId'])
        if backlinks:
            parts.append('<p>原记录关联答案 / 节点：</p><ul>' + ''.join('<li>' + link('#' + node_anchor(pid, nid), nid) + '</li>' for nid in dict.fromkeys(backlinks)) + '</ul>')
        else:
            parts.append('<p class="meta">全篇层级未知项；原记录未给出答案 / 节点关联。</p>')
        parts.append('</article>')
    parts.append('</section>')
    parts.append(f'<section id="ledger-{esc(pid)}"><h3>本篇证据台账：{len(ledger["records"])} 组</h3><p>E 编号只在本篇内解析；作者陈述、原文观察、读者解释和证据限制按原字段显示。</p>')
    parts.append(fields(ledger, pid, omit=('records',)))
    for record in ledger['records']:
        eid = record.get('id', record.get('evidenceRecordId'))
        parts.append(f'<article id="{esc(evidence_anchor(pid, eid))}" data-evidence-id="{esc(eid)}" data-paper-id="{esc(pid)}"><h4>{esc(eid)} · {esc(record.get("title", record.get("summaryZh", "")))}</h4>' + fields(record, pid, context='ledger') + '</article>')
    parts.append('</section>')
    parts.append(f'<section id="{esc(coverage_id)}"><h3>实际核读范围与保留边界</h3>' + value_html(mapping.get('sourceCoverage', []), pid) + '</section>')
    parts.append('<details><summary>原分析元数据、方法归属与备注</summary>' + fields(mapping, pid, omit=('contentTitles', 'structuralNodes', 'expandedNodes', 'answers', 'unresolvedQuestions', 'templateNodes', 'sourceCoverage')) + '</details></section>')
    return '\n'.join(parts)


def render_reading(schema, mappings, ledgers, unknowns, catalog):
    papers = {p['canonical_id']: p for p in catalog['papers']}
    parts = ['<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>多篇论文 · C2 解析完整文字替代</title><style>' + STYLE + '</style></head><body>', RANGE,
             '<a href="../index.html">← 返回三树导航</a><h1>C2 论文解析 · 完整文字替代</h1>',
             '<p class="notice" data-c2-analysis-counts="derived">' + esc(global_summary(catalog, mappings)) + '</p>',
             '<p>此页无需 JavaScript；可用浏览器文字搜索所有内容、未知项与证据。仅展示已审分析及来源链接，不嵌入论文全文、PDF 或原图。</p><nav aria-label="有内容视图的论文"><ul>']
    parts.extend('<li>' + link('#paper-' + pid, papers[pid]['short_name']) + '</li>' for pid in mappings)
    parts.append('</ul></nav>')
    parts.extend(render_paper(schema, m, ledgers[pid], unknowns[pid], papers[pid]) for pid, m in mappings.items())
    pending = [p for p in catalog['papers'] if p['canonical_id'] not in mappings]
    parts.append('<section><h2>其余' + str(len(pending)) + '篇的解析状态</h2>')
    for p in pending:
        pid = p['canonical_id']
        parts.append(f'<article id="paper-{esc(pid)}"><h3>{esc(p["short_name"])}</h3><p>解析树尚未建立。原有目录、已读证据及 Stage 状态未改；没有复用其他论文答案。</p>' + link('../all-papers.html#paper-' + pid, '查看原记录证据') + '</article>')
    return '\n'.join(parts + ['</section></body></html>\n'])


def load_inputs(source):
    load = lambda name: json.loads((source / 'data' / name).read_text())
    schema, harness = load('method.json'), load('mapping.json')
    mappings = {'harnessvln': harness, 'navharness': load('navharness.mapping.json')}
    ledgers = {'harnessvln': load('ledger.json'), 'navharness': load('navharness.ledger.json')}
    unknowns = {'harnessvln': harness['unresolvedQuestions'], 'navharness': load('navharness.unknowns.json')}
    catalog = json.loads((source.parent / 'data/catalog.json').read_text())
    return schema, mappings, ledgers, unknowns, catalog


def replace_marker(text, name, content):
    pattern = r'<!-- c2-' + re.escape(name) + r':start -->.*?<!-- c2-' + re.escape(name) + r':end -->'
    result, count = re.subn(pattern, lambda _: '<!-- c2-' + name + ':start -->' + content + '<!-- c2-' + name + ':end -->', text, flags=re.S)
    if count != 1:
        raise ValueError('Expected one static marker: ' + name)
    return result


def outputs(source, output):
    schema, mappings, ledgers, unknowns, catalog = load_inputs(source)
    result = {output / 'analysis/reading.html': render_reading(schema, mappings, ledgers, unknowns, catalog)}
    global_html = '<p class="notice" data-c2-analysis-counts="derived">' + esc(global_summary(catalog, mappings)) + '</p>'
    for name in ('index.html', 'all-papers.html', 'harnessvln.html'):
        path = output / name
        text = replace_marker(path.read_text(), 'analysis-summary', global_html)
        if name == 'all-papers.html':
            for pid, mapping in mappings.items():
                text = replace_marker(text, 'paper-summary-' + pid,
                    '<p>' + esc(summary(schema, mapping, unknowns[pid])) + ' '
                    + link('analysis/reading.html#paper-' + pid, '完整解析文字替代') + ' · '
                    + link('analysis/reading.html#unknowns-' + pid, '全部未答 / 未知') + ' · '
                    + link('index.html#analysis=' + quote(json.dumps({'paperId': pid}, separators=(',', ':')), safe=''), '打开论文解析树') + '</p>')
        result[path] = text
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-dir', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--output-dir', type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for path, content in outputs(args.source_dir, args.output_dir).items():
        if args.check:
            if not path.exists() or path.read_text() != content:
                stale.append(str(path))
        else:
            path.write_text(content)
    if stale:
        raise SystemExit('Stale generated static views: ' + ', '.join(stale))
    print('PASS deterministic script-free multi-paper views' if args.check else 'Generated reviewed script-free multi-paper views')


if __name__ == '__main__':
    main()
