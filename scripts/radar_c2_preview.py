"""Copy a frozen C2 experiment to a sibling review route, never formal stages.

Only PUBLIC_FILES can be published. Inputs and tests remain outside the route.
No retrieval, scientific inference, source regeneration or browser claim occurs.
"""
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from build_topic_preview import require, safe_path, safe_target

ROUTE = 'review/radar-c2-analysis'
SOURCE = 'previews/radar-c2-analysis'
INPUT_SOURCE = 'tests/fixtures/radar-c2-analysis'
MANIFEST = 'scripts/radar_c2_preview_manifest.json'
PUBLIC_FILES = frozenset((
    'index.html', 'harnessvln.html', 'all-papers.html', 'model.js', 'app.js',
    'style.css', 'data/catalog.js', 'data/literature.js', 'data/challenge.js',
    'analysis/model.js', 'analysis/c2.js', 'analysis/c2.css',
    'analysis/reading.html', 'analysis/data/bundle.js',
))
REVIEW_INPUTS = frozenset((
    'data/catalog.json', 'data/catalog-SHA256.txt', 'data/literature-seed.json',
    'data/challenge-seed.json', 'analysis/data/method.json',
    'analysis/data/mapping.json', 'analysis/data/analysis.compat.json',
    'analysis/data/ledger.json', 'analysis/data/UPSTREAM-VERIFICATION.json',
    'analysis/build_bundle.py', 'tests/navigation.test.cjs',
    'tests/dom_fixture.cjs', 'tests/integration.test.cjs', 'analysis/tests/c2.test.cjs',
    'analysis/tests/dom_fixture.cjs', 'analysis/tests/global-first.test.cjs',
    'tests/global-dual.test.cjs',
))
# Source namespaces are never valid clean-build output destinations.
SOURCE_DIRS = frozenset(('.git', '.github', 'assets', 'artifacts', 'candidates',
    'data', 'docs', 'previews', 'release_checks', 'scripts', 'submit-preview', 'tests', 'node_modules'))


def sha256(content):
    return hashlib.sha256(content).hexdigest()


def read_regular(root, path):
    path = safe_path(root, path)
    require(path.exists() and stat.S_ISREG(path.stat().st_mode),
            'C2 input must be a regular file: ' + str(path))
    # Nonblocking prevents a replaced FIFO from blocking between lstat and open.
    flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    with os.fdopen(os.open(path, flags), 'rb') as stream:
        require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode),
                'C2 input must remain regular')
        return stream.read()


def directories(names):
    return {parent.as_posix() for name in names for parent in Path(name).parents
            if parent != Path('.')}


def validate_tree(root, folder, names):
    folder = safe_path(root, folder)
    require(folder.is_dir(), 'C2 tree must be a directory')
    entries = list(folder.rglob('*'))
    dirs = directories(names)
    require({p.relative_to(folder).as_posix() for p in entries} == set(names) | dirs,
            'C2 tree must exactly match its fixed allowlist')
    for path in entries:
        safe_path(root, path)
        name = path.relative_to(folder).as_posix()
        require(path.is_dir() if name in dirs else stat.S_ISREG(path.stat().st_mode),
                'C2 tree must contain only regular files and allowlisted directories')
    return folder


def assigned_json(content, global_name):
    text = content.decode('utf8').strip()
    prefix = 'window.' + global_name + ' = '
    require(text.startswith(prefix) and text.endswith(';'), 'Unexpected C2 data wrapper')
    return json.loads(text[len(prefix):-1])


def range_stats(graph):
    baseline = {p['canonical_id'] for p in graph['papers']}
    weekly = {p['canonical_id'] for p in graph['candidates']}
    require(len(baseline) == len(graph['papers']) and len(weekly) == len(graph['candidates']),
            'Repeated C canonical identity')
    return {'baseline_count': len(baseline), 'weekly_count': len(weekly),
            'unique_count': len(baseline | weekly), 'overlap_count': len(baseline & weekly),
            'weekly_only_count': len(weekly - baseline), 'baseline_ids': sorted(baseline),
            'weekly_ids': sorted(weekly), 'overlap_ids': sorted(baseline & weekly),
            'weekly_only_ids': sorted(weekly - baseline)}


def validate_semantics(root, public, inputs, manifest):
    load = lambda name: json.loads(inputs[name])
    graph_bytes = read_regular(root, root / 'previews/radar-trees-c/data/graph-data.json')
    graph = json.loads(graph_bytes)
    expected = dict(range_stats(graph), source_sha256=sha256(graph_bytes))
    require(manifest['range'] == expected, 'C2 range must derive from complete old C records')
    require([expected[k] for k in ('baseline_count', 'weekly_count', 'unique_count',
            'overlap_count', 'weekly_only_count')] == [39, 6, 43, 2, 4],
            'C2 covers baseline39; retain weekly6, unique43 and four weekly-only records')
    catalog = load('data/catalog.json')
    require(catalog['papers'] == graph['papers'], 'C2 must preserve all baseline records and raw stages')
    for script, source, global_name in (
        ('data/catalog.js', 'data/catalog.json', 'PAPER_CATALOG'),
        ('data/literature.js', 'data/literature-seed.json', 'LITERATURE_TREE'),
        ('data/challenge.js', 'data/challenge-seed.json', 'CHALLENGE_TREE')):
        require(assigned_json(public[script], global_name) == load(source),
                'Runtime and reviewed input disagree: ' + script)
    bundle = assigned_json(public['analysis/data/bundle.js'], 'C2_DATA')
    require(bundle == {'schema': load('analysis/data/method.json'),
            'mapping': load('analysis/data/mapping.json'),
            'compat': load('analysis/data/analysis.compat.json')},
            'Analysis bundle must remain source-identical')
    schema, mapping = bundle['schema'], bundle['mapping']
    require(manifest['scientific_state'] == {'original_nodes': 59, 'instances': 13,
            'answers': 47, 'unresolved': 6, 'pending_papers': 38,
            'existing_stage_state_mutation': False}, 'Scientific manifest boundary changed')
    require(len(schema['nodes']) == 59 and len(mapping['expandedNodes']) == 13
            and len(mapping['answers']) == 47 and len(mapping['unresolvedQuestions']) == 6
            and mapping['existingStageStateMutation'] is False,
            'C2 scientific counts or raw Stage boundary changed')
    seal = load('analysis/data/UPSTREAM-VERIFICATION.json')
    for name in ('method.json', 'mapping.json', 'analysis.compat.json', 'ledger.json'):
        require(sha256(inputs['analysis/data/' + name]) == seal[name], 'Scientific seal mismatch')
    for name in ('index.html', 'all-papers.html', 'harnessvln.html', 'analysis/reading.html'):
        text = public[name].decode('utf8')
        prefix = '../../' if name.startswith('analysis/') else '../'
        require(f'href="{prefix}radar-trees-c/weekly-2026-10-04.html"' in text
                and 'data-c2-range="baseline-weekly"' in text
                and '4 篇 weekly 独有候选未进入本次重构双树或论文解析' in text,
                'C2 must expose the preserved weekly-only boundary and old archive')


def payloads(root):
    root = Path(root).absolute()
    manifest = json.loads(read_regular(root, root / MANIFEST))
    require(manifest['schema'] == 'radar-c2-isolated-release/1', 'Unknown C2 manifest')
    require(manifest['status'] == 'local_candidate_pending_real_browser_acceptance'
            and manifest['real_browser'] == 'NOT_RUN' and manifest['screenshots'] == 'NOT_RUN'
            and manifest['publication'] == 'NOT_RUN',
            'C2 acceptance must not be silently promoted')
    require(manifest['route'] == ROUTE, 'C2 route must remain isolated')
    result = []
    for source, names, key in ((SOURCE, PUBLIC_FILES, 'public_files'),
                              (INPUT_SOURCE, REVIEW_INPUTS, 'review_inputs')):
        require(set(manifest[key]) == names, 'C2 manifest cannot expand the code allowlist')
        folder = validate_tree(root, root / source, names)
        data = {name: read_regular(root, folder / name) for name in sorted(names)}
        for name, content in data.items():
            require(sha256(content) == manifest[key][name], 'C2 reviewed hash mismatch: ' + name)
        result.append(data)
    public, inputs = result
    validate_semantics(root, public, inputs, manifest)
    return public


def validate_preview(root, target):
    """Fail before build.py is allowed to clean its target, including stale output."""
    root = Path(root).absolute()
    target = safe_target(root, target)
    require(target.relative_to(root).parts[0] not in SOURCE_DIRS,
            'Build output must not overlap C2 or repository source namespaces')
    public = payloads(root)
    destination = safe_path(root, target / ROUTE)
    if destination.exists():
        validate_tree(root, destination, PUBLIC_FILES)
    return root, target, public


def validate_output(root, target, public=None):
    root = Path(root).absolute()
    target = safe_target(root, target)
    public = payloads(root) if public is None else public
    destination = validate_tree(root, target / ROUTE, PUBLIC_FILES)
    for name, content in public.items():
        require(read_regular(root, destination / name) == content,
                'C2 output hash mismatch: ' + name)
    return sorted(public)


def write_preview(root, target):
    root, target, public = validate_preview(root, target)
    destination = safe_path(root, target / ROUTE)
    destination.mkdir(parents=True, exist_ok=True)
    for name in sorted(directories(PUBLIC_FILES), key=lambda value: (value.count('/'), value)):
        safe_path(root, destination / name).mkdir(exist_ok=True)
    for name, content in public.items():
        path = safe_path(root, destination / name)
        # Atomic replacement never truncates pre-existing hard-linked source bytes.
        fd, temporary = tempfile.mkstemp(prefix='.radar-c2-', dir=path.parent)
        try:
            with os.fdopen(fd, 'wb') as stream:
                stream.write(content)
            safe_path(root, path)
            os.replace(temporary, path)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return validate_output(root, target, public)
