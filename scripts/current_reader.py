"""Deterministic live navigation views derived from validated immutable reports."""
import hashlib
from html import escape

CURRENT_READER_PAPERS = frozenset({'rpa-0012', 'rpa-0062'})
STAGES = (('stage1', '初读'), ('stage2', '写作精读'), ('stage3', '方法与代码'))
OPEN = '<nav class="reader-stages" aria-label="阅读阶段">'
NOTE = '<p class="reader-document-note">正文、嵌入图、代码和已排版公式可离线阅读；站点导航、外部原文与源码链接需联网。阅读覆盖范围以本页声明为准。</p>'
SITE = 'https://chunhui-lab.github.io/RoboPaperAtlas/'
FROZEN_NAV = {
    'stage1': OPEN + '<span aria-current="page"><small>01</small>初读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>02</small>写作精读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>03</small>方法与代码</span></nav>',
    'stage2': OPEN + '<a href="' + SITE + 'artifacts/rpa-0012/v2/first-pass.html"><small>01</small>初读</a><span aria-current="page"><small>02</small>写作精读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>03</small>方法与代码</span></nav>',
    'stage3': OPEN + '<a href="' + SITE + 'artifacts/rpa-0012/v2/first-pass.html"><small>01</small>初读</a><a href="' + SITE + 'artifacts/rpa-0012/v1/writing-close-reading.html"><small>02</small>写作精读</a><span aria-current="page"><small>03</small>方法与代码</span></nav>',
}
FROZEN_RETURN = {
    'stage1': '<a class="atlas-return" href="../../../papers/rpa-0012/index.html">回到论文详情</a>',
    'stage2': '<a class="atlas-return" href="' + SITE + 'index.html#catalog">回到论文目录</a>',
    'stage3': '<a class="atlas-return" href="' + SITE + 'index.html#catalog">回到论文目录</a>',
}

# One exact registered source per UMI current stage; unknown revisions fail closed.
UMI_FROZEN = {'stage1': {'version': 'v3',
            'sha256': '207e383ba08f684b4272dcee766fe2ab5db2613261430b88c28af27018143d2b',
            'nav': '<nav class="reader-stages" aria-label="阅读阶段"><a href="#main" '
                   'aria-current="page"><small>01</small>初读</a><a '
                   'href="writing-close-reading.html"><small>02</small>写作精读</a><a '
                   'href="method-code-reading.html"><small>03</small>方法与代码</a></nav>',
            'note': '<p class="reader-document-note">报告版本 v3 · 正文、图表和公式可离线阅读；原文、源码与站内搜索需联网。</p>',
            'return_link': '<a class="reader-paper-link" '
                           'href="https://chunhui-lab.github.io/RoboPaperAtlas/papers/rpa-0062/index.html">UMI-on-Legs '
                           '<span> / Reading</span></a>',
            'current_return': '<a class="reader-paper-link" '
                              'href="../index.html#reading">UMI-on-Legs <span> / '
                              'Reading</span></a>'},
 'stage2': {'version': 'v4',
            'sha256': 'f5dc2cb12b37a45d0cc1b36e0cbcfd52cfc49264f2beb9786be8def75de5749b',
            'nav': '<nav class="reader-stages" aria-label="阅读阶段"><a '
                   'href="https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0062/v3/first-pass.html"><small>01</small>初读</a><a '
                   'href="writing-close-reading.html" '
                   'aria-current="page"><small>02</small>写作精读</a><a '
                   'href="https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0062/v3/method-code-reading.html"><small>03</small>方法与代码</a></nav>',
            'note': '<p class="reader-document-note">报告版本 v4 · '
                    '2026-10-02。原文、中文释义与分析直接并排展示；正文可离线阅读，站点导航与正式 PDF '
                    '链接需联网。原文链接定位到页，不提供句级自动高亮；浏览器可能下载 PDF。历史报告：<a '
                    'href="https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0062/v3/writing-close-reading.html">v3</a> '
                    '· <a '
                    'href="https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0062/v2/writing-close-reading.html">v2</a> '
                    '· <a '
                    'href="https://chunhui-lab.github.io/RoboPaperAtlas/artifacts/rpa-0062/v1/writing-close-reading.html">v1</a>。阅读覆盖范围以本页声明为准。</p>',
            'return_link': '<a class="atlas-return" '
                           'href="../../../papers/rpa-0062/index.html">回到论文详情</a>',
            'current_return': '<a class="atlas-return" href="../index.html#reading">回到论文详情</a>'},
 'stage3': {'version': 'v3',
            'sha256': '2fa0b3f3a65fab738837d2c8a30c43a02473b5bf71ac61cbc5a670b3496e23e9',
            'nav': '<nav class="reader-stages" aria-label="阅读阶段"><a '
                   'href="first-pass.html"><small>01</small>初读</a><a '
                   'href="writing-close-reading.html"><small>02</small>写作精读</a><a href="#main" '
                   'aria-current="page"><small>03</small>方法与代码</a></nav>',
            'note': '<p class="reader-document-note">报告版本 v3 · 正文、图表和公式可离线阅读；原文、源码与站内搜索需联网。</p>',
            'return_link': '<a class="reader-paper-link" '
                           'href="https://chunhui-lab.github.io/RoboPaperAtlas/papers/rpa-0062/index.html">UMI-on-Legs '
                           '<span> / Reading</span></a>',
            'current_return': '<a class="reader-paper-link" '
                              'href="../index.html#reading">UMI-on-Legs <span> / '
                              'Reading</span></a>'}}


def entry_path(paper_id, stage):
    if paper_id in CURRENT_READER_PAPERS and stage in dict(STAGES):
        return f'papers/{paper_id}/reading/{stage}.html'
    return None


def render(root, paper, stage, records):
    """Require reviewed source bytes and exact signatures; no script/style edits."""
    from reports import report_path
    state = paper['stages'][stage]
    if not entry_path(paper['id'], stage) or state['status'] != 'imported' or not state['artifacts']:
        raise ValueError('A current reader requires an imported supported report')
    artifact = state['artifacts'][0]
    record = next((r for r in records if report_path(r) == artifact['path']), None)
    if record is None or record['paper_id'] != paper['id'] or record['stage'] != stage:
        raise ValueError('Current reader source is not registered for this stage')
    source = root / report_path(record)
    if source.is_symlink() or any(p.is_symlink() for p in source.parents):
        raise ValueError('Unsafe current reader source')
    raw = source.read_bytes()
    if len(raw) != record['bytes'] or hashlib.sha256(raw).hexdigest() != record['sha256']:
        raise ValueError('Current reader source hash mismatch')
    page = raw.decode('utf-8')
    if paper['id'] == 'rpa-0062':
        spec = UMI_FROZEN[stage]
        if (record['version'], record['sha256']) != (spec['version'], spec['sha256']):
            raise ValueError('Unreviewed UMI current reader source version/hash')
        frozen, frozen_return, note = spec['nav'], spec['return_link'], spec['note']
        current_return = spec['current_return']
    else:
        frozen, frozen_return, note = FROZEN_NAV[stage], FROZEN_RETURN[stage], NOTE
        current_return = '<a class="atlas-return" href="../index.html#reading">回到论文详情</a>'
    if page.count(OPEN) != 1 or page.count(frozen) != 1 or page.count(note) != 1 or page.count(frozen_return) != 1:
        raise ValueError('Unexpected current reader navigation signature')
    nav = []
    for index, (key, label) in enumerate(STAGES, 1):
        target = paper['stages'][key]
        if target['status'] == 'imported' and target['artifacts']:
            current = ' aria-current="page"' if key == stage else ''
            nav.append(f'<a href="{key}.html"{current}><small>{index:02}</small>{label}</a>')
        else:
            nav.append(f'<span aria-disabled="true"><small>{index:02}</small>{label} · 尚未导入</span>')
    provenance = (f'当前导航视图 · 基于固定报告 {escape(record["version"])} 生成，仅更新阶段导航、返回入口与本说明；'
                  f'正文、脚本与样式保持原样。<a href="../../../{escape(report_path(record), quote=True)}">打开固定版本报告 ↗</a> ')
    return (page.replace(frozen, OPEN + ''.join(nav) + '</nav>', 1)
            .replace(frozen_return, current_return, 1)
            .replace(note, note.replace('>', '>' + provenance, 1), 1))


def write_current_readers(root, target, papers, records):
    for paper in papers:
        if paper['id'] not in CURRENT_READER_PAPERS:
            continue
        for stage, _ in STAGES:
            state = paper['stages'][stage]
            if state['status'] == 'imported' and state['artifacts']:
                dest = target / entry_path(paper['id'], stage)
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(render(root, paper, stage, records), encoding='utf-8')


def validate_current_readers(source_root, target, papers, records):
    """Current views get an exact derived-byte boundary, never a relaxed parser."""
    routes = set()
    for paper in papers:
        if paper['id'] not in CURRENT_READER_PAPERS:
            continue
        folder = target / 'papers' / paper['id'] / 'reading'
        if not any(r['paper_id'] == paper['id'] for r in records):
            if folder.exists() or folder.is_symlink():
                raise ValueError('Unregistered current reader output')
            continue  # Supports scoped artifact-only validation fixtures.
        if not folder.is_dir() or folder.is_symlink():
            raise ValueError('Missing or unsafe current reader directory')
        expected = set()
        for stage, _ in STAGES:
            state = paper['stages'][stage]
            if state['status'] == 'imported' and state['artifacts']:
                route = entry_path(paper['id'], stage)
                dest = target / route
                if dest.is_symlink() or any(p.is_symlink() for p in dest.parents):
                    raise ValueError('Unsafe current reader output')
                if not dest.is_file() or dest.read_bytes() != render(source_root, paper, stage, records).encode('utf-8'):
                    raise ValueError('Current reader output mismatch')
                expected.add(route)
        actual = {str(p.relative_to(target)) for p in folder.rglob('*') if p.is_file()}
        if actual != expected:
            raise ValueError('Unexpected current reader output')
        routes.update(expected)
    return routes
