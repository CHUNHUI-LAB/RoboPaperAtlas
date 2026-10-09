"""Copy a frozen C2 experiment to a sibling review route, never formal stages.

Only PUBLIC_FILES can be published. Inputs and tests remain outside the route.
No retrieval, scientific inference, source regeneration or browser claim occurs.
"""
from collections import Counter
from copy import deepcopy
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlsplit
from build_topic_preview import require, safe_path, safe_target

ROUTE = 'review/radar-c2-analysis'
SOURCE = 'previews/radar-c2-analysis'
INPUT_SOURCE = 'tests/fixtures/radar-c2-analysis'
RESEARCH_INPUT_SOURCE = 'tests/fixtures/research-navigation'
MANIFEST = 'scripts/radar_c2_preview_manifest.json'
PUBLIC_FILES = frozenset((
    'index.html', 'harnessvln.html', 'all-papers.html', 'model.js', 'app.js',
    'style.css', 'data/catalog.js', 'data/literature.js', 'data/challenge.js',
    'analysis/model.js', 'analysis/c2.js', 'analysis/c2.css',
    'analysis/reading.html', 'analysis/data/bundle.js',
    'research.js', 'data/research-graph.js', 'data/reference-complete.js', 'data/scoped-analysis.js',
    'reference/figure-1.jpg', 'reference/figure-2.jpg', 'reference/figure-3.jpg', 'reference/figure-4.jpg',
))
REVIEW_INPUTS = frozenset((
    'data/task-contract-corrections-20261007.json',
    'data/catalog.json', 'data/catalog-SHA256.txt', 'data/literature-seed.json',
    'data/challenge-seed.json', 'analysis/data/method.json',
    'analysis/data/mapping.json', 'analysis/data/analysis.compat.json',
    'analysis/data/ledger.json', 'analysis/data/UPSTREAM-VERIFICATION.json',
    'analysis/data/navharness.mapping.json', 'analysis/data/navharness.ledger.json',
    'analysis/data/navharness.unknowns.json', 'analysis/data/MULTI-PAPER-VERIFICATION.json',
    'analysis/build_reading.py', 'analysis/tests/static-multi-paper.test.cjs',
    'analysis/tests/multi-paper.test.cjs',
    'tests/historical-single-paper/analysis/data/bundle.js',
    'tests/historical-single-paper/all-papers.html',
    'tests/historical-single-paper/analysis/reading.html',
    'analysis/build_bundle.py', 'tests/navigation.test.cjs',
    'tests/dom_fixture.cjs', 'tests/integration.test.cjs', 'analysis/tests/c2.test.cjs',
    'analysis/tests/dom_fixture.cjs', 'analysis/tests/global-first.test.cjs',
    'tests/global-dual.test.cjs', 'tests/entry_dom_fixture.cjs', 'tests/three-entry.test.cjs', 'tests/analysis-independent.test.cjs', 'tests/entry-baseline.json',
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


# These pins cover unchanged historical sources and the three approved NavHarness
# derivatives. The release manifest can seal reviewed UI evolution; it cannot
# silently relabel new science as an already reviewed source by changing hashes.
SCIENTIFIC_SOURCE_SHA256 = {
    'data/catalog.json': 'bf1ba3b0887334803f08a11e80dd8bb0db0f2d3427f8d3787f1e5cc704f37bf4',
    'data/literature-seed.json': '4e3cd8b898acf82a1dcfbcd78a8903dc5a79ecd98bad06b1178fb88841da7bad',
    'data/challenge-seed.json': '857e0d0f719ea651ede20f49384ae8fcdba878a58b3821e186b7e4115e8d417d',
    'analysis/data/method.json': '3680f02c8d06f266c9975c7d1ea677e031ed15f6ede1cd18cedca63682f29c53',
    'analysis/data/mapping.json': '2bb837879bf6e4ad4d44cb83ee7203428169a6ef9219e193bdf30ce27f932d20',
    'analysis/data/analysis.compat.json': 'e665093f8001af87d7f46882fd68dbd00e3fa236b6c4efeb9cf8bca181baff15',
    'analysis/data/ledger.json': 'b0aa5113e36eb34f4fa7fc8b2d71460678baa6c54de1e038802937a6fe9effac',
    'analysis/data/UPSTREAM-VERIFICATION.json': 'bf846ca9b440ebde6333dff6104ca6a1d7ff60a246bb6634be969fc60f518589',
    'analysis/data/navharness.mapping.json': '23e0eb70374965f85184b36ba3c33e91732477d8aeee2c047e583e08c29ca7ec',
    'analysis/data/navharness.ledger.json': 'e81ef8f9aa101301f3feb310ebfcc406ddd92885c192bad6586560cd1814b7ee',
    'analysis/data/navharness.unknowns.json': '10803d91f96ae6d85770769dfd3405af68e6f069de60ccf93b1df0e1d15106b8',
}
HISTORICAL_ENTRY_SHA256 = {'tests/historical-single-paper/analysis/data/bundle.js': '84c278efcc809bc8f382ee1b19cc57a57089034edb6e58e5c643f8918a3eb353', 'tests/historical-single-paper/all-papers.html': '0b7faf72081bb841ceda6a1347821e4f8720d6dcabc5af57846b9db86ebb018d', 'tests/historical-single-paper/analysis/reading.html': '81ad4382c202c2d4baf0177b68a473373d46fb25e2f4017c61e465c1905e360b'}
ENTRY_BASELINE_SHA256 = 'd3edd07e8eff1fb0e85e3b24537e8b1f3000c1563c0ceaadf3a7667234208807'
FIXED_VERSIONS = {'harnessvln': '2609.15195v3', 'navharness': '2609.34276v1'}
NAVHARNESS_SOURCE_MANIFEST_SHA256 = '23e97231441c71e64b6a0e3e5b526b8954d47fdc87133a664fbf25b4eb5fbb9f'


def expected_analysis_bundle(inputs):
    """No projection or inferred fields: retain the reviewed values completely."""
    load = lambda name: json.loads(inputs['analysis/data/' + name])
    mapping = load('mapping.json')
    return {
        'schema': load('method.json'), 'mapping': mapping,
        'compat': load('analysis.compat.json'),
        'mappingsByPaperId': {
            'harnessvln': mapping, 'navharness': load('navharness.mapping.json')},
        'ledgersByPaperId': {
            'harnessvln': load('ledger.json'), 'navharness': load('navharness.ledger.json')},
        'unknownsByPaperId': {
            'harnessvln': mapping['unresolvedQuestions'], 'navharness': load('navharness.unknowns.json')},
    }


def scientific_state(bundle, catalog):
    """Counts derive from mappings; fixed reviewed boundaries are checked below."""
    papers = {}
    original_nodes = len(bundle['schema']['nodes'])
    for paper_id, mapping in bundle['mappingsByPaperId'].items():
        answers = mapping['answers']
        code_states = Counter(a.get('codeEvidence', {}).get('status', 'not_recorded') for a in answers)
        papers[paper_id] = {
            'source_version': mapping['sourceVersion'],
            'original_nodes': original_nodes,
            'instances': len(mapping['expandedNodes']),
            'total_nodes': original_nodes + len(mapping['expandedNodes']),
            'answers': len(answers),
            'unresolved': len(bundle['unknownsByPaperId'][paper_id]),
            'answer_statuses': dict(sorted(Counter(a['status'] for a in answers).items())),
            'code_evidence_statuses': dict(sorted(code_states.items())),
            'implementation_unknown': code_states['not_reviewed_implementation_unknown'],
            'evidence_records': len(bundle['ledgersByPaperId'][paper_id]['records']),
            'source_locator_occurrences': sum(len(a['sourceLocators']) for a in answers),
        }
    harness = papers['harnessvln']
    return {
        # Backwards-compatible aliases are always the HarnessVLN values.
        'original_nodes': original_nodes, 'instances': harness['instances'],
        'answers': harness['answers'], 'unresolved': harness['unresolved'],
        'supported_papers': len(papers),
        'pending_papers': len(catalog['papers']) - len(papers),
        'existing_stage_state_mutation': False, 'papers': papers,
    }


def validate_analysis_bundle(bundle, inputs):
    require(bundle == expected_analysis_bundle(inputs),
            'Analysis bundle must remain source-identical for both papers and aliases')
    for name, expected in SCIENTIFIC_SOURCE_SHA256.items():
        require(sha256(inputs[name]) == expected, 'Scientific approved-source hash mismatch: ' + name)
    for name, expected in HISTORICAL_ENTRY_SHA256.items():
        require(sha256(inputs[name]) == expected, 'Historical entry source hash mismatch: ' + name)
    require(sha256(inputs['tests/entry-baseline.json']) == ENTRY_BASELINE_SHA256,
            'Original entry baseline provenance changed')
    old_seal = json.loads(inputs['analysis/data/UPSTREAM-VERIFICATION.json'])
    for name in ('method.json', 'mapping.json', 'analysis.compat.json', 'ledger.json'):
        require(sha256(inputs['analysis/data/' + name]) == old_seal[name], 'Scientific seal mismatch')
    seal = json.loads(inputs['analysis/data/MULTI-PAPER-VERIFICATION.json'])
    require(seal['schema'] == 'radar-c2-paper-sources/1'
            and seal['fixedVersions'] == FIXED_VERSIONS
            and seal['navharnessSourceManifestSha256'] == NAVHARNESS_SOURCE_MANIFEST_SHA256
            and seal['inputs'] == SCIENTIFIC_SOURCE_SHA256
            and seal['historicalEntryFiles'] == HISTORICAL_ENTRY_SHA256
            and seal['entryBaselineSha256'] == ENTRY_BASELINE_SHA256, 'Multi-paper scientific seal mismatch')
    schema = bundle['schema']
    nodes = schema['nodes']
    original_ids = {node['id'] for node in nodes}
    require(len(nodes) == len(original_ids) == 59, 'Original 59-node schema changed')
    template = [{'templateNodeId': node['id'], 'labelOriginal': node['labelOriginal'],
                 'parentTemplateNodeId': node['parentId'], 'order': node['order']} for node in nodes]
    require(bundle['compat']['existingStageStateMutation'] is False,
            'Legacy compatibility must not change Stage state')
    require([(a['nodeId'], a['state'], a['answer']) for a in bundle['mapping']['answers']] ==
            [(a['nodeId'], a['state'], a['answer']) for a in bundle['compat']['answers']],
            'HarnessVLN compatibility alias changed')
    for key in ('mappingsByPaperId', 'ledgersByPaperId', 'unknownsByPaperId'):
        require(set(bundle[key]) == set(FIXED_VERSIONS), 'Paper indexes must contain only approved identities')
    for paper_id, version in FIXED_VERSIONS.items():
        mapping = bundle['mappingsByPaperId'][paper_id]
        ledger = bundle['ledgersByPaperId'][paper_id]
        unknowns = bundle['unknownsByPaperId'][paper_id]
        require(mapping['paperId'] == ledger['paperId'] == paper_id and mapping['sourceVersion'] == version,
                'Analysis identity or fixed source version changed')
        require(mapping['methodSchemaId'] == schema['schemaId']
                and mapping['originalSchemaUnmodified'] is True and mapping['originalNodeCount'] == 59
                and mapping['templateNodes'] == template and mapping['existingStageStateMutation'] is False,
                'Original schema metadata, node order or Stage boundary changed')
        instances = mapping['expandedNodes']
        instance_ids = {node['nodeId'] for node in instances}
        require(len(instances) == len(instance_ids) and original_ids.isdisjoint(instance_ids),
                'Paper instances must not replace or repeat original schema IDs')
        all_ids = original_ids | instance_ids
        for node in instances:
            require(node['repeatOfSchemaNode'] in original_ids and node['expansionSlot'] in original_ids
                    and node['parentId'] in all_ids and node['isPaperSpecificInstantiation'] is True,
                    'Invalid paper-specific expansion contract')
        evidence_ids = [record.get('id', record.get('evidenceRecordId')) for record in ledger['records']]
        require(None not in evidence_ids and len(evidence_ids) == len(set(evidence_ids)),
                'Evidence IDs must be unique within their paper')
        evidence_ids = set(evidence_ids)
        answer_ids = [answer['nodeId'] for answer in mapping['answers']]
        require(len(answer_ids) == len(set(answer_ids)) and set(answer_ids) <= all_ids,
                'Answers must target unique real paper nodes')
        require(unknowns == mapping['unresolvedQuestions'], 'Unknown items must remain lossless')
        for entry in mapping['answers'] + unknowns:
            require(set(entry.get('evidenceRecordIds', [])) <= evidence_ids,
                    'Evidence IDs must resolve within the same paper ledger')
            for locator in entry.get('sourceLocators', []):
                source = urlsplit(locator['sourceUrl'])
                require(source.scheme == 'https' and source.netloc == 'arxiv.org'
                        and source.path in ('/pdf/' + version, '/html/' + version, '/abs/' + version)
                        and locator['sourceVersion'] == version,
                        'Answer locator must retain its fixed paper version')
        for answer in mapping['answers']:
            require(answer['state'] == answer['status'], 'Original answer state and status must agree')
        counts = tuple(len(mapping[name]) for name in ('expandedNodes', 'answers', 'unresolvedQuestions'))
        expected_counts = (13, 47, 6) if paper_id == 'harnessvln' else (18, 51, 12)
        require(counts == expected_counts, 'Reviewed per-paper scientific counts changed')
        expected_statuses = ({'evidence_linked': 40, 'author_claim_only': 7} if paper_id == 'harnessvln' else
                             {'evidence_linked': 43, 'author_claim_only': 6, 'partially_reported': 2})
        require(dict(Counter(a['status'] for a in mapping['answers'])) == expected_statuses,
                'Reviewed answer status distribution changed')
        require(len(ledger['records']) == (27 if paper_id == 'harnessvln' else 31),
                'Reviewed paper evidence ledger count changed')
        require(sum(len(a['sourceLocators']) for a in mapping['answers']) ==
                (182 if paper_id == 'harnessvln' else 724), 'Reviewed source locator occurrences changed')
    nav = bundle['mappingsByPaperId']['navharness']
    unknowns = bundle['unknownsByPaperId']['navharness']
    require(nav['canonicalId'] == 'navharness', 'NavHarness must not merge with Adaptive Goals')
    require([item['id'] for item in unknowns] == ['U%02d' % i for i in range(1, 13)]
            and all('nodeId' not in item and 'question' not in item for item in unknowns),
            'NavHarness unknown taxonomy must not be fabricated or truncated')
    unknown_ids = {item['id'] for item in unknowns}
    for answer in nav['answers']:
        require(answer['sourceKind'] == 'primary_paper'
                and set(answer['sourceGapIds']) <= unknown_ids,
                'NavHarness answer source kind or unknown backlink changed')
        code = answer['codeEvidence']
        expected_code = ('not_reviewed_implementation_unknown' if answer['nodeId'].startswith('method.module')
                         else 'not_applicable_to_this_answer')
        require(code['status'] == expected_code, 'Implementation evidence cannot be promoted')
        if expected_code == 'not_reviewed_implementation_unknown':
            require(code['remainingQuestionId'] == 'U02' and 'U02' in answer['sourceGapIds']
                    and code['sourceKind'] == 'none', 'Implementation unknown must retain its real U02 gap')
    require(sum(a['codeEvidence']['status'] == 'not_reviewed_implementation_unknown'
                for a in nav['answers']) == 20, 'All 20 implementation-unknown answers must remain')
    require(all(record['independentlyReproduced'] is False
                for record in bundle['ledgersByPaperId']['navharness']['records']),
            'NavHarness evidence must not imply independent reproduction')
    require(unknowns[-1]['id'] == 'U12' and unknowns[-1]['status'] == 'figure_text_inconsistency'
            and unknowns[-1]['sourceUrls'] == ['https://arxiv.org/pdf/2609.34276v1#page=39']
            and all('U12' not in a['sourceGapIds'] for a in nav['answers']),
            'Figure18 conflict remains a whole-paper unresolved issue without invented answer backlinks')


# A separately reviewed additive correction record, not a replacement history seed.
PROTOCOL_DELTA_SHA256 = 'dd9f1990f1f68b04b37183231b9a362938ee4596543d0957eed5e86529163748'
CORRECTED_LITERATURE_SHA256 = '44a1645269740d0f1bda0cbaddc6097d915f43171b6c4739fde7a745b80efc66'


def expected_corrected_literature(inputs):
    raw = inputs['data/task-contract-corrections-20261007.json']
    require(sha256(raw) == PROTOCOL_DELTA_SHA256, 'Protocol correction delta changed')
    delta = json.loads(raw)
    original = json.loads(inputs['data/literature-seed.json'])
    require(sha256(inputs['data/literature-seed.json']) == SCIENTIFIC_SOURCE_SHA256['data/literature-seed.json'], 'Original literature seed changed')
    result = deepcopy(original)
    by = {n['node_id']: n for n in result['nodes']}
    for record in delta['nodes']:
        node = by[record['node_id']]
        for field in record['fields']:
            name = field['field']
            require((name in node) == field['before_present'] and node.get(name) == field['before'], 'Protocol correction before-value mismatch')
            node[name] = deepcopy(field['after'])
    for record in delta['implementation_variants']:
        node = result['implementation_variants'][record['selector']['variant_id']]
        for field in record['fields']:
            name = field['field']
            require((name in node) == field['before_present'] and node.get(name) == field['before'], 'Implementation correction before-value mismatch')
            node[name] = deepcopy(field['after'])
    for key, extra in delta['append_only_additions'].items():
        result.setdefault(key, []).extend(deepcopy(extra))
    result.update(deepcopy(delta['top_level_additions']))
    require(result['paths'] == original['paths'] and result['edges'] == original['edges'], 'Protocol correction cannot migrate paths or edges')
    require([n['node_id'] for n in result['nodes']] == [n['node_id'] for n in original['nodes']], 'Protocol correction cannot replace node IDs')
    return result


# New research content has independent pins. Historical scientific seals above are untouched.
RESEARCH_GRAPH_SHA256 = "c8ecb785113a921af21c63fd649e695cd6f9150525242b8ad359917ba822c5d7"
RESEARCH_REVIEWED_SHA256 = "e58b93113b8f8112b2680c01856ae6966d287393d8e4ab945106001894cb9d84"
RESEARCH_RECEIPT_SHA256 = "808b02bd1193636c536a10cbe8e718248d215aa1ab19f38818c3ff4cc7a6ea8f"
SCOPED_ANALYSIS_SHA256 = "229012daa98d77d2ac07295a72c10b200c4d8e7234e8e945102132372b4b3f5e"


def validate_research_semantics(root, public):
    reviewed = read_regular(root, root / 'tests/fixtures/research-navigation/reviewed-graph.json')
    receipt = read_regular(root, root / 'tests/fixtures/research-navigation/review-receipt.json')
    require(sha256(reviewed) == RESEARCH_REVIEWED_SHA256, 'Separate reviewed research content changed')
    require(sha256(receipt) == RESEARCH_RECEIPT_SHA256, 'Separate scientific review receipt changed')
    require(sha256(public['data/research-graph.js']) == RESEARCH_GRAPH_SHA256, 'Reviewed research graph changed')
    require(assigned_json(public['data/research-graph.js'], 'RESEARCH_NAVIGATION') == json.loads(reviewed),
            'Runtime research graph differs from reviewed content')
    require(sha256(public['data/scoped-analysis.js']) == SCOPED_ANALYSIS_SHA256, 'Scoped paper analysis changed')
    graph = json.loads(reviewed)
    require(graph['schema_version'] == 'research-navigation/1', 'Unknown research graph version')
    require(graph['root_id'] == 'nav:root' and graph['goal_id'] == 'nav:goal'
            and graph['tree_roots'] == {'l': 'nav:l', 'c': 'nav:c'}, 'Original sibling-root grammar changed')
    require(len(graph['overview']['sentences']) in range(3, 6), 'Research overview must explain the field before expansion')
    scoped = assigned_json(public['data/scoped-analysis.js'], 'SCOPED_RESEARCH_ANALYSES')
    require(set(scoped) == {'poni'} and len(scoped['poni']['answers']) == 22,
            'PONI selected-section answer scope changed')
    require(scoped['poni']['status'] == 'partial_selected_section_analysis', 'Partial analysis cannot become complete')
    return graph


def validate_semantics(root, public, inputs, manifest):
    validate_research_semantics(root, public)
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
        expected_source = expected_corrected_literature(inputs) if script == 'data/literature.js' else load(source)
        require(assigned_json(public[script], global_name) == expected_source,
                'Runtime and reviewed input disagree: ' + script)
        if script == 'data/literature.js':
            require(sha256(public[script]) == CORRECTED_LITERATURE_SHA256, 'Corrected literature source changed')
    bundle = assigned_json(public['analysis/data/bundle.js'], 'C2_DATA')
    validate_analysis_bundle(bundle, inputs)
    require(manifest['scientific_state'] == scientific_state(bundle, catalog),
            'Scientific manifest must derive from both reviewed mappings')
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
    require(manifest['schema'] == 'radar-c2-isolated-release/2', 'Unknown C2 manifest')
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
    # Add navigation only after the sealed historical inputs have been verified.
    # Keep source bytes and science intact; only generated entry UI is extended.
    anchor = ('<a href="../../research/navigation/index.html" '
              'data-navigation-entry="formal" title="导航研究地图 · 正式三树">正式三树 →</a>')
    script = public['analysis/c2.js'].decode('utf8')
    marker = '<header class="ft-top"><a href="index.html">RoboPaperAtlas</a>'
    require(script.count(marker) == 1, 'C2 navigation needs one faithful header')
    old_version = sha256(public['analysis/c2.js'])[:12]
    public['analysis/c2.js'] = script.replace(marker, marker + anchor, 1).encode('utf8')
    new_version = sha256(public['analysis/c2.js'])[:12]
    entry = public['index.html'].decode('utf8')
    marker = '<span class="local-badge">隔离预览</span>'
    require(entry.count(marker) == 1, 'C2 navigation needs one legacy header')
    script_url = 'analysis/c2.js?v=' + old_version
    require(entry.count(script_url) == 1, 'C2 navigation needs one pinned script URL')
    entry = entry.replace(marker, marker + anchor, 1)
    public['index.html'] = entry.replace(script_url, 'analysis/c2.js?v=' + new_version, 1).encode('utf8')
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
