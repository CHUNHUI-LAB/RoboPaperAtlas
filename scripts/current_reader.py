"""Deterministic live navigation views derived from validated immutable reports."""
import hashlib
from html import escape

CURRENT_READER_PAPERS = frozenset({'rpa-0012'})
STAGES = (('stage1', '初读'), ('stage2', '写作精读'), ('stage3', '方法与代码'))
OPEN = '<nav class="reader-stages" aria-label="阅读阶段">'
NOTE = '<p class="reader-document-note">正文、嵌入图、代码和已排版公式可离线阅读；站点导航、外部原文与源码链接需联网。阅读覆盖范围以本页声明为准。</p>'
SITE = 'https://chunhui-lab.github.io/RoboPaperAtlas/'
FROZEN_NAV = {
    'stage1': OPEN + '<span aria-current="page"><small>01</small>初读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>02</small>写作精读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>03</small>方法与代码</span></nav>',
    'stage2': OPEN + '<a href="' + SITE + 'artifacts/rpa-0012/v2/first-pass.html"><small>01</small>初读</a><span aria-current="page"><small>02</small>写作精读</span><span aria-disabled="true" title="此阶段报告尚未提供"><small>03</small>方法与代码</span></nav>',
    'stage3': OPEN + '<a href="' + SITE + 'artifacts/rpa-0012/v2/first-pass.html"><small>01</small>初读</a><a href="' + SITE + 'artifacts/rpa-0012/v1/writing-close-reading.html"><small>02</small>写作精读</a><span aria-current="page"><small>03</small>方法与代码</span></nav>',
}


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
    frozen = FROZEN_NAV[stage]
    if page.count(OPEN) != 1 or page.count(frozen) != 1 or page.count(NOTE) != 1:
        raise ValueError('Unexpected current reader navigation signature')
    nav = []
    for index, (key, label) in enumerate(STAGES, 1):
        target = paper['stages'][key]
        if target['status'] == 'imported' and target['artifacts']:
            current = ' aria-current="page"' if key == stage else ''
            nav.append(f'<a href="{key}.html"{current}><small>{index:02}</small>{label}</a>')
        else:
            nav.append(f'<span aria-disabled="true"><small>{index:02}</small>{label} · 尚未导入</span>')
    provenance = (f'当前导航视图 · 基于固定报告 {escape(record["version"])} 生成，仅更新阶段导航与本说明；'
                  f'正文、脚本与样式保持原样。<a href="../../../{escape(report_path(record), quote=True)}">打开固定版本报告 ↗</a> ')
    return page.replace(frozen, OPEN + ''.join(nav) + '</nav>', 1).replace(
        NOTE, NOTE.replace('>', '>' + provenance, 1), 1)


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
