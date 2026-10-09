"""Script-free, source-bound default trees; no network, state mutation or raw model dump."""
import html
from urllib.parse import urlencode, urlsplit

DEFAULT_SCOPE = 'task:category-objectnav'
PONI_VERSION = 'publication:poni:e83f98bb7132'
TEXT_FIELDS = (
    ('definition', '定义'), ('example', '例子'), ('inputGoalSuccess', '输入、目标与成功条件'),
    ('distinctions', '区别与边界'), ('researchQuestions', '研究问题'),
    ('condition', '条件'), ('challenge', '困难'), ('mechanism', '原因'),
    ('design', '具体设计'), ('change', '技术变化'), ('evidence', '证据'),
    ('statement', '原有表述'), ('scope', '适用范围'), ('limits', '限制'),
    ('boundary', '边界'), ('residual', '尚未解决'), ('attribution', '归属'),
    ('seminalScope', '历史定位范围'), ('crossTaskRelevance', '跨任务关联'),
)
PIPELINE_FIELDS = (('input', '输入'), ('representation', '表示'), ('decision', '决策'),
                   ('execution', '执行'), ('feedback', '反馈'))


def _esc(value):
    return html.escape(str(value), quote=True)


def _text(value):
    """Only explicitly requested textual leaves; never stringify unknown mappings."""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return '；'.join(filter(None, (_text(item) for item in value)))
    return ''


def _safe_url(value):
    if not isinstance(value, str) or not value or any(ord(c) <= 32 or ord(c) == 127 for c in value) or '\\' in value:
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            return None
        _ = parsed.port
    except ValueError:
        return None
    return value


def _locator(value):
    if isinstance(value, dict):
        return _locator(value.get('locator') or value.get('sectionOrAppendix') or value.get('pageOrAnchor') or value.get('text'))
    if isinstance(value, list):
        return '；'.join(filter(None, (_locator(x) for x in value)))
    return _text(value)


def _sources(refs):
    rows, seen = [], set()
    for ref in refs or []:
        if not isinstance(ref, dict):
            continue
        url = _safe_url(ref.get('url') or ref.get('sourceURL') or ref.get('sourceUrl') or ref.get('source_url'))
        if not url:
            continue
        detail = ref.get('detail') if isinstance(ref.get('detail'), dict) else {}
        locator = _locator(ref.get('locator') or detail.get('locator'))
        label = _text(ref.get('descriptor')) or '原文来源'
        key = (url, locator)
        if key in seen:
            continue
        seen.add(key)
        rows.append('<li><a href="' + _esc(url) + '" target="_blank" rel="noopener noreferrer">' + _esc(label) + '</a>' + (' · ' + _esc(locator) if locator else '') + '</li>')
    return '<ul class="np-native-sources">' + ''.join(rows) + '</ul>' if rows else ''


def _block(label, value):
    value = _text(value)
    return '<p><strong>' + _esc(label) + '：</strong>' + _esc(value) + '</p>' if value else ''


def canonical_link(position):
    """Use real position identity. Analysis is explicitly in the default ObjectNav scope."""
    route = {'nav': '1', 'scope': position.get('scopeId') or DEFAULT_SCOPE, 'tree': position['tree'], 'node': position['id']}
    for source, target in (('paperId', 'paper'), ('versionId', 'version')):
        if position.get(source):
            route[target] = position[source]
    route['mode'] = 'tree'
    return '#' + urlencode(route)


def _walk(model, roots, tree, paper=None, version=None):
    found, active = [], set()
    def visit(pid, parent):
        if pid in active or any(p['id'] == pid for p in found):
            raise ValueError('Native tree must have unique acyclic positions')
        p = model['positions'][pid]
        if p['tree'] != tree or p.get('parentId') != parent:
            raise ValueError('Native tree parent or perspective mismatch')
        if tree in ('l', 'c') and p.get('scopeId') != DEFAULT_SCOPE:
            raise ValueError('Native default tree cannot borrow another scope')
        if paper and (p.get('paperId') != paper or p.get('versionId') != version):
            raise ValueError('Native analysis cannot borrow another paper or version')
        if p['entityId'] not in model['entities']:
            raise ValueError('Native node has no content entity')
        active.add(pid); found.append(p)
        for child in p.get('childIds', []):
            visit(child, pid)
        active.remove(pid)
    for root in roots:
        visit(root, None)
    return found


def render_native_trees(model):
    """Return complete native HTML for ObjectNav l/c and explicitly selected PONI a.

    Inputs are already authenticated by navigation_product.payloads. This pure
    projection validates identity/topology again and emits only allowlisted text.
    Native details work without any script; enhanced links never choose a version.
    """
    if model.get('schemaVersion') != 'navigation-product/1':
        raise ValueError('Unsupported native tree model')
    roots = model['forests'][DEFAULT_SCOPE]
    positions = model['positions']
    literature = _walk(model, roots['l'], 'l')
    challenges = _walk(model, roots['c'], 'c')
    analysis = model['analyses']['poni'][PONI_VERSION]
    a_nodes = _walk(model, analysis['roots'], 'a', 'poni', PONI_VERSION)
    if len(a_nodes) != 59 or {p.get('originalNodeId') for p in a_nodes} != set(model['template']['nodeIds']):
        raise ValueError('Native PONI must retain all original 59 nodes')
    answered = sum(p['kind'] == 'analysis_answer' for p in a_nodes)
    if answered != analysis['answeredOriginalCount']:
        raise ValueError('Native answer coverage must match the fixed version')
    version = model['versions'][PONI_VERSION]
    if version.get('paperId') != 'poni':
        raise ValueError('Native PONI version identity mismatch')

    def node_body(p):
        entity = model['entities'][p['entityId']]
        detail = entity.get('detail') or {}
        body = []
        if p.get('paperId'):
            paper = model['papers'][p['paperId']]
            body.append(_block('论文', paper.get('label') or paper.get('title') or p['paperId']))
            body.append(_block('来源版本', model['versions'].get(p.get('versionId'), {}).get('label') or '未固定具体版本；不得借用其他版本回答'))
        if p.get('association') in ('context', 'condition'):
            body.append(_block('阅读关系', '跨任务相关阅读' if p['association'] == 'context' else '条件投影；不代表在同一协议评测'))
        if p['tree'] == 'a':
            template = next(n for n in model['template']['nodes'] if n['id'] == p['originalNodeId'])
            if template.get('structural_note') or template.get('note'):
                note = _block('原结构注记', template.get('structural_note')) + _block('原图注记', template.get('note'))
                if template.get('note'):
                    note += '<p>保留原图文字供核对，不是隐瞒真实方法缺陷的建议。应如实呈现限制、任务边界与未验证之处。</p>'
                body.append('<details class="np-native-template-notes"><summary>原图注记与解释</summary>' + note + '</details>')
            answer = detail.get('answer')
            if p['kind'] == 'analysis_answer':
                if entity.get('paperId') != 'poni' or PONI_VERSION not in entity.get('versionIds', []) or not isinstance(answer, dict):
                    raise ValueError('Native answer lacks exact PONI version binding')
                body.append(_block('已填回答（选定章节核读）', answer.get('text') or answer.get('answer')))
                body.append(_block('归属', answer.get('attribution')))
                body.append(_block('范围说明', answer.get('scope_note')))
                body.append(_sources(answer.get('evidence_refs') or answer.get('sourceLocators')))
            else:
                body.append('<p>本节点未填答；结构节点也计入原59节点。未填写不表示原论文没有讨论，不借用其他论文或版本的答案。</p>')
        else:
            for key, label in TEXT_FIELDS:
                body.append(_block(label, detail.get(key)))
            pipeline = detail.get('pipeline')
            if isinstance(pipeline, dict):
                for key, label in PIPELINE_FIELDS:
                    body.append(_block(label, pipeline.get(key)))
            for cid in p.get('claimIds', []):
                claim = model['claims'][cid]
                body.append(_block('有据表述', claim.get('statement') or claim.get('label')))
                body.append(_sources(claim.get('sourceRefs')))
        body.append(_sources(entity.get('sourceRefs')))
        body.append('<p><a data-native-enhanced-link href="' + _esc(canonical_link(p)) + '">在增强三树中打开此精确节点</a></p>')
        return ''.join(body)

    def render_node(pid, depth=0):
        p = positions[pid]
        status = (' · 已填答' if p['kind'] == 'analysis_answer' else ' · 结构／未填答') if p['tree'] == 'a' else ''
        children = p.get('childIds', [])
        opening = ' open' if depth == 0 else ''
        attrs = ' data-native-position="' + _esc(p['id']) + '" data-native-tree="' + _esc(p['tree']) + '"'
        if p['tree'] == 'a':
            attrs += ' data-original-node="' + _esc(p['originalNodeId']) + '" data-native-answer="' + ('answered' if p['kind'] == 'analysis_answer' else 'unanswered') + '"'
        # Put the real child summaries before optional prose, keeping the hierarchy visible.
        child_html = '<ul>' + ''.join('<li>' + render_node(child, depth + 1) + '</li>' for child in children) + '</ul>' if children else ''
        content = node_body(p)
        if children:
            content = '<details class="np-native-content"><summary>本节点内容与来源</summary>' + content + '</details>'
        return '<details class="np-native-node"' + attrs + opening + '><summary>' + _esc(p['label']) + _esc(status) + '</summary>' + child_html + content + '</details>'

    def forest(tree, title, forest_roots, count):
        return '<section class="np-native-forest" data-native-forest="' + tree + '"><h3>' + title + '</h3><p>默认 ObjectNav 范围 · ' + str(count) + ' 个真实树位置；可直接展开节点。</p>' + ''.join(render_node(pid) for pid in forest_roots) + '</section>'

    boundary = ('<p>这是默认 ObjectNav 的原生阅读树，不是全领域目录。文献与挑战层级可直接展开，无需等待 JavaScript；'
                '论文解析单独明确选择下方 PONI 固定版本。增强加载完成后可使用全部研究入口与联动状态；原生内容不代表所有论文已精读。</p>')
    analysis_intro = '<p>明确选择：PONI · ' + _esc(version['label']) + '。原59节点完整保留，' + str(answered) + ' 个节点已填，' + str(59 - answered) + ' 个结构／未填节点；不是59个独立已答问题。</p>'
    analysis_intro += _block('未完成边界', analysis.get('unresolvedQuestions'))
    for record in analysis.get('sourceCoverage', []):
        analysis_intro += _block('已核读范围', record.get('checked')) + _block('未完成', record.get('not_completed')) + _block('抽取限制', record.get('extraction_limit'))
    analysis_intro += _sources([{'url': version.get('sourceURL'), 'descriptor': version['label']}])
    return ('<section id="np-native-reading" class="np-native-reading" aria-labelledby="np-native-heading">'
            '<h2 id="np-native-heading">无需等待即可展开的真实三树</h2><p>默认 ObjectNav 原生树；全部研究入口需增强加载。</p>' +
            '<details class="np-native-boundary"><summary>原生范围与核读边界</summary>' + boundary + '</details>' +
            forest('l', '文献树 · ObjectNav', roots['l'], len(literature)) +
            forest('c', '挑战–思路树 · ObjectNav', roots['c'], len(challenges)) +
            '<details class="np-native-analysis-choice"><summary>论文解析树：选择 PONI · ' + _esc(version['label']) + '（原59节点）</summary>' +
            analysis_intro + '<section data-native-forest="a">' + ''.join(render_node(pid) for pid in analysis['roots']) + '</section></details></section>')
