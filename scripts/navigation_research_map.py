"""Evidence-preserving global display projection; frozen science is never mutated."""
from collections import defaultdict
import hashlib
import html
import json
import os
import stat
import tempfile
from pathlib import Path
from urllib.parse import urlencode

SOURCE_SHA = '1229372f697316dc5c0627995fce7de18496160d85f4a1acb4ffc2a6faf1d708'
GOAL = 'legacy:nav:goal'
DOC = 'legacy:nav:root'
LITERATURE = 'legacy:nav:l'
CHALLENGE = 'legacy:nav:c'


def _esc(x):
    return html.escape(str(x), quote=True)


def _relations(model):
    result = {}
    for row in list(model['relations'].values()) + list(model.get('relatedRelations', [])):
        rid = row['id']
        if rid in result and result[rid] != row:
            raise ValueError('Conflicting relation identity: ' + rid)
        result[rid] = row
    return result


def build_research_map(model):
    """Project original global containment plus explicitly identified CI refinements.

    This is a display descriptor, not a merged scientific model. Legacy work nodes
    retain their labels and priority annotations. Scope bridges remain typed links.
    """
    entities = model['entities']
    for key in (GOAL, DOC, LITERATURE, CHALLENGE):
        if key not in entities:
            raise ValueError('Missing reviewed global entity ' + key)
    relations = _relations(model)
    canonical = {}
    alias_rows = []
    for eid, e in entities.items():
        if not eid.startswith('legacy:ci_'):
            continue
        matches = [mid for mid, other in entities.items()
                   if mid.startswith('methods:') and other.get('originalId') == e.get('originalId')
                   and other.get('kind') in ('challenge', 'subchallenge')]
        if len(matches) > 1:
            raise ValueError('Ambiguous challenge display alias')
        if matches:
            canonical[matches[0]] = eid
            alias_rows.append({'canonicalEntityId': eid, 'aliasEntityIds': matches,
                               'basis': 'exact_public_originalId', 'originalId': e['originalId'],
                               'displayKind': e['kind'], 'scientificRecordsMerged': False})
    def canon(eid):
        return canonical.get(eid, eid)
    aliases_by_target = defaultdict(list)
    for alias, target in canonical.items():
        aliases_by_target[target].append(alias)

    # Original legacy containment is the faithful core. Do not blindly append the
    # parallel methods literature projection with duplicate pipeline/work layers.
    selected = [r for r in relations.values() if r.get('renderAsTree')
                and r.get('from', '').startswith('legacy:')
                and r.get('to', '').startswith('legacy:')
                and r.get('from') in entities and r.get('to') in entities
                and r['from'] != DOC]
    # Preserve newer CI descendants and the four extra reviewed CI roots. Shared
    # problems use the original legacy role, including prompt_uncertainty's parent.
    ci_frontier = {CHALLENGE} | set(aliases_by_target)
    progressed = True
    while progressed:
        progressed = False
        for r in relations.values():
            if not r.get('renderAsTree') or not r.get('to', '').startswith('methods:'):
                continue
            src, dst = canon(r.get('from')), canon(r.get('to'))
            if src not in ci_frontier or dst not in entities:
                continue
            if r not in selected:
                selected.append(r)
            if dst not in ci_frontier:
                ci_frontier.add(dst); progressed = True
    # No context work becomes a containment child. Equivalent witnessed edges
    # share one visible occurrence but keep every contributing relation ID.
    children = defaultdict(dict)
    for r in selected:
        src, dst = canon(r['from']), canon(r['to'])
        if dst.startswith('legacy:challenge:context:') or src == dst:
            continue
        row = children[src].setdefault(dst, [])
        if r['id'] not in row:
            row.append(r['id'])
    # Preserve the original prompt refinement placement even if a parallel record
    # also declared it at root; its role must not become a new top-level challenge.
    prompt = 'legacy:ci_prompt_uncertainty'
    if prompt in children.get(CHALLENGE, {}):
        children[CHALLENGE].pop(prompt)

    bindings = []
    for eid, e in entities.items():
        if not eid.startswith('legacy:method:work:'):
            continue
        variant = e.get('detail', {}).get('method_variant_id')
        matches = [mid for mid, other in entities.items()
                   if other.get('kind') == 'pipeline_recipe'
                   and other.get('detail', {}).get('id') == variant
                   and other.get('paperId') == e.get('paperId')
                   and set(other.get('versionIds', [])) == set(e.get('versionIds', []))]
        if len(matches) == 1:
            versions = e.get('versionIds', [])
            bindings.append({'workEntityId': eid, 'recipeEntityId': matches[0],
                             'paperId': e.get('paperId'),
                             'versionId': versions[0] if len(versions) == 1 else None,
                             'versionIds': list(versions)})
    recipe_by_work = {r['workEntityId']: r['recipeEntityId'] for r in bindings}
    annotation_edges = defaultdict(list)
    for r in relations.values():
        if r.get('renderAsTree'):
            continue
        src, dst = canon(r.get('from')), r.get('to')
        rt = r.get('relationType', '')
        if dst in entities and (dst.startswith('legacy:challenge:context:') or
                rt in ('supported_by', 'supported_by_claim', 'described_by', 'described_in') or
                any(part in rt for part in ('context', 'diagnostic', 'comparator', 'adjacent'))):
            annotation_edges[src].append((dst, r['id']))

    positions = {}
    by_entity = defaultdict(list)
    def visit(eid, parent=None, ancestors=(), depth=0, witness=()):
        if eid in ancestors:
            raise ValueError('Global containment cycle')
        e = entities[eid]
        pid = 'pos:g:' + hashlib.sha256(('\x1f'.join(ancestors + (eid,))).encode()).hexdigest()[:22]
        versions = e.get('versionIds', [])
        annotations = list(aliases_by_target[eid])
        if eid in recipe_by_work:
            annotations.append(recipe_by_work[eid])
        annotations += [a for a, _ in annotation_edges[eid]]
        p = {'id': pid, 'tree': 'g', 'scopeId': 'scope:all', 'entityId': eid,
             'paperId': e.get('paperId'), 'versionId': versions[0] if len(versions) == 1 and e.get('paperId') and model['versions'].get(versions[0], {}).get('paperId') == e['paperId'] else None,
             'versionIds': list(versions), 'claimIds': list(e.get('claimIds', [])),
             'parentId': parent, 'childIds': [], 'label': e['label'], 'kind': e['kind'],
             'depth': depth, 'order': 0, 'status': e.get('status'), 'association': 'direct',
             'sourceRelationIds': list(witness),
             'relationType': relations[witness[0]]['relationType'] if witness else 'global_goal',
             'annotationEntityIds': list(dict.fromkeys(annotations)),
             'annotationRelationIds': [rid for _, rid in annotation_edges[eid]]}
        positions[pid] = p; by_entity[eid].append(pid)
        for order, (child, relation_ids) in enumerate(children.get(eid, {}).items()):
            child_id = visit(child, pid, ancestors + (eid,), depth + 1, relation_ids)
            positions[child_id]['order'] = order; p['childIds'].append(child_id)
        return pid
    root = visit(GOAL)
    scope_entries = []
    for scope in model['scopes']:
        bridges, target_positions = [], []
        for b in scope.get('bindings', []):
            if not b.get('legacyId'):
                continue
            target = 'legacy:' + b['legacyId']
            bridge = {'targetEntityId': target, 'association': b.get('association'),
                      'relationType': b.get('relationType'),
                      'positionIds': list(by_entity.get(canon(target), []))}
            bridges.append(bridge); target_positions += bridge['positionIds']
        scope_entries.append({'scopeId': scope['id'], 'positionIds': list(dict.fromkeys(target_positions)),
                              'mappingStatus': ('typed_bridge_available' if target_positions else 'typed_bridge_target_not_visible') if bridges else 'global_placement_pending',
                              'bridges': bridges, 'label': scope['label'],
                              'displayRole': scope.get('displayRole') or scope['kind'],
                              'readingTarget': {'nav': '1', 'scope': scope['id'], 'tree': 'l', 'mode': 'tree'}})
    descriptor = {'schemaVersion': 'research-map/1', 'sourceModelSha256': SOURCE_SHA,
            'documentEntityId': DOC, 'positions': positions, 'roots': [root],
            'initialExpandedIds': [root] + positions[root]['childIds'],
            'aliases': alias_rows, 'workRecipeBindings': bindings, 'scopeEntries': scope_entries,
            'coverage': {'displayPositions': len(positions), 'displayEntities': len(by_entity),
                         'scopeEntries': len(scope_entries),
                         'scopesWithTypedBridges': sum(bool(x['bridges']) for x in scope_entries),
                         'scopesWithoutTypedBridges': sum(not x['bridges'] for x in scope_entries),
                         'scopesWithVisibleGlobalPosition': sum(bool(x['positionIds']) for x in scope_entries),
                         'scopesPendingGlobalPlacement': sum(not x['positionIds'] for x in scope_entries),
                         'scopesBridgedButTargetNotVisible': sum(bool(x['bridges']) and not x['positionIds'] for x in scope_entries),
                         'scientificModelUnchanged': True,
                         'noveltyPolicy': 'evidence_scoped_annotations_only_no_automatic_seminal_labels'}}
    return _extend_canonical_scopes(model, descriptor)


def _scope_name(scope_id):
    return 'scope-' + hashlib.sha256(scope_id.encode()).hexdigest()[:20] + '.html'


def render_global_native(model, descriptor):
    """Actual global hierarchy in script-free details, not a summary-card fallback."""
    pos = descriptor['positions']; expanded = set(descriptor['initialExpandedIds'])
    def render(pid):
        p = pos[pid]
        q = {'nav': '1', 'scope': 'scope:all', 'tree': 'g', 'node': pid, 'mode': 'tree'}
        if p['paperId']: q['paper'] = p['paperId']
        if p['versionId']: q['version'] = p['versionId']
        child = '<ul>' + ''.join('<li>' + render(cid) + '</li>' for cid in p['childIds']) + '</ul>' if p['childIds'] else ''
        return '<details class="np-native-node" data-native-global-position="' + pid + '" data-native-entity="' + _esc(p['entityId']) + '" data-native-directory-group="' + _esc(p.get('sourceDirectoryGroupId') or '') + '"' + (' open' if pid in expanded else '') + '><summary>' + _esc(p['label']) + _native_role(p) + '</summary>' + _native_scope_note(p, 'branches/') + child + '<p><a href="branches/' + _node_name(pid) + '">阅读此节点与来源（无需脚本）</a> · <a href="' + _esc('#' + urlencode(q)) + '">在联动全图聚焦此节点</a></p></details>'
    return '<section class="np-native-reading" id="np-native-global"><h2>全局研究图</h2><p>从共同研究目标逐步展开文献与挑战；各范围角色、来源与待组织部分分别保留。</p><p><a href="branches/index.html">全部研究范围与无脚本阅读</a></p>' + ''.join(render(x) for x in descriptor['roots']) + '</section>'


NATIVE_RELATION_LABELS = {'selected_fixed_version_condition': '已核固定版本·条件关联', 'selected_fixed_version_task': '已核固定版本·任务关联', 'scope_reading_entry': '阅读入口', 'editorial_index': '资料索引', 'editorial_projection': '按接口组织的阅读路线', 'recipe_member': '路线中的具体方法', 'described_by': '论文描述', 'explains_design': '思路落实为设计', 'supported_by': '来源证据', 'selected_challenge': '有据的困难', 'insight_with_reference_annotations': '回应困难的思路', 'scoped_challenge_projection': '限定范围的困难', 'scoped_challenge_refinement': '限定条件下细化', 'original_template_parent': '原模板结构', 'paper_specific_instantiation': '本篇特定展开', 'explicit_component_reuse_and_policy_replacement': '复用组件并替换策略', 'explicit_mapping_reuse_with_alternative_search_scorer': '复用建图，替换搜索评分', 'documented_method_reuse': '原文明确复用', 'component_reused_and_policy_replaced_by': '组件承接与策略替换', 'mapping_component_reused_by': '建图组件复用', 'explicit_method_adaptation': '明确的方法改造', 'explicit_design_revision': '明确的设计修订', 'cited_architectural_lineage_with_ablated_changes': '有消融支持的结构发展', 'cited_architectural_response': '被引用的结构回应', 'cited_architectural_development': '原文支持的结构发展', 'cited_baseline_and_problem_response': '引用基线并回应问题', 'cited_baseline_problem_response': '基线与问题回应', 'explicit_framework_extension': '明确框架扩展', 'versioned_refinement': '指定版本的细化', 'editorial_route_comparison_only': '编辑对照，不是继承', 'cited_method_comparison': '原文方法对照', 'editorial_method_comparison': '阅读对照，不是继承', 'evaluated_on': '原文评测关联', 'evaluated_on_restricted_protocol': '受限协议下评测', 'evaluated_on_and_protocol_extension': '评测与协议扩展', 'addresses_task': '原文任务关联', 'addresses_task_or_setting': '原文任务/条件关联', 'method_relevance_not_task_membership': '相关方法，不是任务归属', 'evidence_interface_relevance_not_task_membership': '证据接口相关，不是任务解法归属', 'comparator_reference_not_solution_child': '对照阅读，不是解法子节点', 'context_or_diagnostic_reference_on_challenge': '背景/诊断证据', 'context_or_diagnostic_evidence': '背景/诊断证据', 'adjacent_route_crosslink_not_solution_child': '相邻路线，不是解法子节点', 'adjacent_question_evidence': '相邻问题证据', 'conditional_subchallenge': '条件化子困难', 'refines_estimation_target': '细化估计目标', 'related_reading': '同论文相关阅读', 'paper_specific_instance': '本篇具体展开', 'method_card': '已核方法卡', 'versioned_evidence_supplement': '指定版本证据补充', 'supported_by_claim': '原文主张支持', 'implemented_by': '落实为方法实现', 'problem_projection': '研究问题的阅读投影', 'proposed_insight': '提出关键思路', 'design_in_pipeline': '路线中的技术设计', 'mechanism_relevance_projection': '机制相关的阅读投影', 'addressed_by': '对应的方法回应', 'addresses_challenge': '回应此困难', 'described_in': '论文中的描述', 'method_for_condition': '此条件下的相关方法', 'has_recipe': '具体运行方法', 'task_has_challenge': '任务下的有据困难', 'has_insight': '对应关键思路', 'direct_method_for_task': '明确针对本任务的方法', 'method_for_learning_protocol': '学习协议下的方法', 'has_system_pipeline': '系统运行路线', 'bibliographic_index_not_method_membership': '文献索引，不代表任务方法归属', 'adds_information_channel': '增加信息通道', 'adds_sensor_when_coordinates_known': '已知坐标条件下增加传感信息', 'adds_social_costs_constraints': '增加社会交互代价或约束', 'alternative_pipeline': '另一条实现路线', 'author_rationale_for': '作者给出的设计依据', 'benchmark_extension': '评测基准扩展', 'benchmark_instantiation': '评测基准的具体实例', 'bounded_composition_instantiation': '限定条件的组合实例', 'broad_condition_covers': '宽条件关联，非具体任务等同', 'changes_prior_knowledge': '改变先验知识条件', 'changes_success_semantics': '改变成功判据', 'cited_limitation_response_and_training_component_lineage': '引用局限并承接训练组件', 'cited_modular_transfer': '原文引用的模块迁移', 'cited_prior_and_shared_component_family': '引用前作并共享组件族', 'cited_prior_shared_component_family': '引用前作并共享组件族', 'complementary_stages': '互补阶段', 'composed_goal_type_in': '组合中的目标类型', 'concrete_instance': '具体实例', 'contributes_goal_variant': '提供目标变体', 'cross_problem_dependency': '跨问题依赖', 'cross_problem_overlap_not_containment': '跨问题重叠，不是包含', 'cross_task_mechanism_relevance_not_solution': '跨任务机制相关，不是本任务解法', 'cross_task_overlap': '跨任务重叠', 'design_revised_by': '设计被后续工作修订', 'different_success_semantics': '成功判据不同', 'documented_problem_extension': '原文支持的问题扩展', 'editorial_entry': '编辑组织的阅读入口', 'evaluated_in_or_related_benchmark': '评测或基准关联，按原文区分', 'evaluated_in_paper_local_protocol': '作者局部协议下评估', 'evaluation_uses_benchmark': '评估使用此基准', 'execution_condition_restriction': '执行条件限定', 'explicit_baseline_adaptation': '原文明确的基线改造', 'explicit_model_reuse': '原文明确的模型复用', 'extends_temporal_assumption': '扩展时间假设', 'generalizes_goal_predicate': '推广目标判定条件', 'goal_predicate_restriction': '限定目标判定条件', 'goal_specification_restriction': '限定目标描述', 'informs_search_prior': '提供搜索先验', 'instantiated_by': '具体实现为', 'instantiated_in': '在此场景具体实现', 'instantiated_or_supported_by': '具体实例或支持证据', 'language_mode_restriction': '语言输入方式限定', 'map_prior_cross_cutting_condition': '跨任务地图先验条件', 'may_reduce_to_after_grounding': '目标落地后可能归约', 'modular_approach_adapted_by': '模块式方法被改造', 'organized_under': '阅读组织归属', 'problem_decomposition': '问题分解', 'problem_restriction': '限定研究问题', 'related_challenge_not_inheritance': '相关困难，不是继承', 'related_goal_predicate': '相关目标判定条件', 'related_hidden_goal_localization': '相关隐式目标定位', 'related_language_grounding': '相关语言落地', 'relaxes_static_obstacle_assumption': '放宽静态障碍假设', 'relaxes_vocabulary_assumption': '放宽词表假设', 'restricts_prior_knowledge_condition': '限制先验知识', 'sequential_composition': '按序组合', 'specializes_execution_condition': '细化执行条件', 'specific_method_dependency': '具体方法依赖', 'supports': '支持关联', 'supports_continuous_setting_of': '支持连续环境条件', 'systematizes_semantic_constraints': '系统化语义约束', 'task_application': '任务应用', 'task_setting_instantiated_by_benchmark': '任务或设置的基准实例', 'challenge_refinement': '困难进一步细化', 'editorial_navigation_not_scientific_containment': '编辑阅读导航', 'renderAsTree': '原有层级'}
NATIVE_KIND_LABELS = {'goal': '共同研究目标', 'tree': '研究视角', 'root': '研究图', 'problem_setting': '问题条件', 'problem_condition': '限定问题', 'task_instantiation': '具体任务', 'pipeline_or_representation': '路线 / 表示', 'improvement_idea': '技术变化', 'subchallenge': '子困难', 'task': '任务', 'setting': '条件', 'family': '任务族', 'protocol': '学习/评估协议', 'reading_index': '来源索引', 'pipeline': '路线', 'pipeline_family': '路线族', 'pipeline_recipe': '具体方法', 'technical_improvement': '技术改进', 'concrete_work': '论文', 'paper': '论文', 'challenge': '困难', 'insight': '关键思路', 'design': '技术设计', 'technical_design': '技术设计', 'evidence': '证据', 'analysis_answer': '已核回答', 'analysis_template': '原模板节点', 'versioned_method_card': '有来源的方法卡', 'diagnostic_or_comparison': '诊断/对照', 'representation_with_downstream_pipeline': '表示与下游路线', 'benchmark': 'Benchmark', 'evaluation_setting': '作者评估设置', 'local_evaluation': '局部评估', 'development_group': '原有发展线索', 'editorial_directory_group': '编辑阅读分组', 'analysis_instance': '本篇具体展开'}

NATIVE_RELATION_LABELS['global_goal'] = '共同研究目标'

def _relation_label(value):
    return NATIVE_RELATION_LABELS.get(value, '原文记录的关联')


def _native_role(p):
    role = p.get('displayRole') or NATIVE_KIND_LABELS.get(p.get('kind'), '原有研究节点')
    text = role + (' · 条件关联' if p.get('association') == 'condition' else '')
    return '<span class="native-depth">' + _esc(text) + '</span>'


def _native_scope_note(p, prefix=''):
    if not p.get('scopeDefinition'): return ''
    note = '<p class="native-note">' + _esc(p['scopeDefinition']) + '</p>'
    if p.get('coverageCategory') == 'no_reviewed_method':
        note += '<p class="native-note">此入口暂无已核直接或条件方法；角色、已有证据与适用边界以阅读范围说明为准。</p>'
    return note + '<p><a href="' + prefix + _scope_name(p['sourceScopeId']) + '#conditions">定义、评测条件与来源</a></p>'


def _node_name(pid):
    return 'node-' + hashlib.sha256(pid.encode()).hexdigest()[:20] + '.html'


def _analysis_name(paper, version):
    return 'analysis-' + hashlib.sha256((paper + '\x1f' + version).encode()).hexdigest()[:20] + '.html'


NATIVE_CSS = '''*{box-sizing:border-box}body{margin:0;background:#fbfcf9;color:#18313d;font:16px/1.65 system-ui,sans-serif}main{max-width:1200px;margin:auto;padding:12px 18px 36px}h1{font-size:1.35rem;line-height:1.4;margin:8px 0}h2{font-size:1.1rem;margin:10px 0}h3{font-size:1rem}p{margin:6px 0 12px}a{color:#155b4e;overflow-wrap:anywhere}nav{display:flex;gap:12px;flex-wrap:wrap;font-size:.85rem}summary{cursor:pointer;overflow-wrap:anywhere;min-height:30px;line-height:1.5;padding:4px 0}a:focus-visible,summary:focus-visible{outline:3px solid #ab5013;outline-offset:2px}.native-tree ul{list-style:none;padding-left:12px;margin:2px 0}.native-tree ul ul ul{padding-left:0}.native-tree details{min-width:0;margin:2px 0;border-left:1px solid #b6cec4}.native-tree summary{padding-left:5px}.native-depth{display:block;font-size:.7rem;color:#456170}.native-columns{display:grid;grid-template-columns:1fr 1fr;gap:18px}.native-columns>*{min-width:0}.native-content{overflow-wrap:anywhere}.native-note{font-size:.85rem;color:#456170}.native-boundary{padding:8px;border-left:3px solid #ab772e;background:#faf3e4}.native-directory{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:16px}.native-directory ul{padding-left:18px}li{overflow-wrap:anywhere}.native-identity{font-size:.85rem;color:#155b4e}.native-body{padding:5px 10px}details.native-evidence{margin:12px 0;border-top:1px solid #b6cec4}@media(max-width:600px){main{padding:8px}.native-columns,.native-directory{grid-template-columns:1fr;gap:10px}.native-tree summary{font-size:.9rem}.native-tree ul ul ul{padding-left:0}}'''


def _page(title, body):
    return ('<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + _esc(title) + ' · 导航研究图</title><link rel="stylesheet" href="native.css"></head><body><main>'
            '<nav aria-label="原生阅读来路"><a href="index.html">全局研究图</a><a href="directory.html">全部阅读范围与角色</a>'
            '<a href="../index.html">返回联动研究图</a></nav><h1>' + _esc(title) + '</h1>' + body + '</main></body></html>').encode()


def _enhanced(p, scope=None, paper=None, version=None, template=False):
    q = {'nav': '1', 'scope': scope or p.get('scopeId') or 'scope:all', 'tree': p['tree'], 'node': p['id'], 'mode': 'tree'}
    if paper or p.get('paperId'): q['paper'] = paper or p['paperId']
    if version or p.get('versionId'): q['version'] = version or p['versionId']
    if template: q['template'] = '1'
    return '../index.html#' + urlencode(q)


def _entity_body(model, eid, paper=None, version=None):
    from navigation_native_trees import _block, _sources, _text, TEXT_FIELDS, PIPELINE_FIELDS
    e = model['entities'][eid]; d = e.get('detail') or {}; out = []
    if paper:
        pe = model['papers'].get(paper, {})
        out.append(_block('论文', pe.get('label') or pe.get('title') or paper))
    if version:
        v = model['versions'].get(version, {})
        out.append(_block('来源版本', v.get('label') or version))
        if v.get('status') == 'snapshot_not_version_pinned':
            out.append('<p class="native-boundary">此来源为未固定版本快照，不作为固定版本已答依据。</p>')
    for key, label in [('plain_language_question', '研究问题')] + list(TEXT_FIELDS):
        out.append(_block(label, d.get(key)))
    pipeline = d.get('pipeline_contract') or d.get('pipeline')
    if isinstance(pipeline, dict):
        for key, label in PIPELINE_FIELDS: out.append(_block(label, pipeline.get(key)))
    for note in d.get('annotations', []):
        out.append('<div class="native-boundary">' + _block('原有注记', note.get('label')) +
                   _block('确切贡献范围', note.get('exact_contribution_scope')) +
                   _block('优先权核查范围', note.get('prior_art_search_scope')) +
                   _block('排除与边界', note.get('counterexamples_or_exclusions')) +
                   _block('验证状态', note.get('verification_status')) + '</div>')
    for key, label in [('version', '协议版本'), ('readScope', '核读范围'), ('readingDepth', '核读深度'),
                       ('unverified', '待核'), ('implementationStatus', '实现核验边界'),
                       ('protocolLinkSemantics', '协议关联边界')]:
        out.append(_block(label, d.get(key)))
    for key, label in [('successPredicates', '成功判据'), ('environmentActionsPrivileges', '环境、动作与特权'),
                       ('memoryReset', '记忆与重置'), ('details', '协议细节')]:
        rows = d.get(key)
        if isinstance(rows, list):
            for row in rows:
                if isinstance(row, dict): out.append(_block(row.get('label') or label, row.get('value')))
    answer = d.get('answer')
    if e['kind'] == 'analysis_answer' and isinstance(answer, dict):
        if paper != e.get('paperId') or version not in e.get('versionIds', []):
            raise ValueError('Analysis body cannot borrow another paper/version')
        out.append(_block('已填回答', answer.get('text') or answer.get('answer')))
        out.append(_block('归属', answer.get('attribution')) + _block('范围', answer.get('scope_note')))
        out.append(_sources(answer.get('evidence_refs') or answer.get('sourceLocators')))
    for cid in e.get('claimIds', []):
        claim = model['claims'].get(cid)
        if claim:
            out.append(_block('有据表述', claim.get('statement') or claim.get('label')))
            out.append(_sources(claim.get('sourceRefs')))
    out.append(_sources(e.get('sourceRefs')))
    return ''.join(out)


def _native_forest(model, positions, roots, scope, paper=None, version=None, template=False, global_map=False, expanded_ids=None):
    def render(pid, depth, path):
        if pid in path: raise ValueError('Native output cycle')
        p = positions[pid]
        branch = '<ul>' + ''.join('<li>' + render(child, depth + 1, path + (pid,)) + '</li>' for child in p.get('childIds', [])) + '</ul>' if p.get('childIds') else ''
        if global_map:
            content = _native_scope_note(p) + '<p><a href="' + _node_name(pid) + '">具体内容、注记与来源</a></p>'
        else:
            selected_paper, selected_version = paper or p.get('paperId'), version or p.get('versionId')
            content = _entity_body(model, p['entityId'], selected_paper, selected_version)
            if p['tree'] == 'a' and (template or p['kind'] != 'analysis_answer'):
                content = '<p>原结构／未填答；不是论文没有讨论，也不借用其他版本答案。</p>' + content
            if p['tree'] == 'a':
                original = next((x for x in model['template']['nodes'] if x['id'] == p.get('originalNodeId')), {})
                from navigation_native_trees import _block
                content += _block('原结构注记', original.get('structural_note'))
                if original.get('note'):
                    content += '<details><summary>原图注记与解释</summary>' + _block('原图文字', original['note']) + '<p>保留原图供核对，不是隐瞒真实方法缺陷的建议。</p></details>'
            content += '<p><a href="' + _esc(_enhanced(p, scope, paper, version, template)) + '">在联动图打开同一身份</a></p>'
            if branch: content = '<details class="native-evidence"><summary>本节点正文与来源</summary>' + content + '</details>'
        edge = ''
        if depth:
            edge = '<span class="native-depth">第' + str(depth + 1) + '层 · ' + _esc(_relation_label(p.get('relationType'))) + (' · 条件关联' if p.get('association') == 'condition' else ' · 跨任务相关' if p.get('association') == 'context' else '') + '</span>'
        return '<details data-native-position="' + _esc(pid) + '" data-original-node="' + _esc(p.get('originalNodeId') or '') + '" data-native-answer="' + ('true' if p['kind'] == 'analysis_answer' and not template else 'false') + '"' + (' open' if (pid in expanded_ids if expanded_ids is not None else depth <= (1 if global_map else 0)) else '') + '><summary>' + _esc(p['label']) + _native_role(p) + edge + '</summary>' + branch + '<div class="native-body">' + content + '</div></details>'
    return '<div class="native-tree">' + ''.join(render(pid, 0, ()) for pid in roots) + '</div>'


def _build_scope_outputs(model, descriptor):
    model = dict(model, entities={**model['entities'], **descriptor.get('presentationEntities', {})})
    scopes = {s['id']: s for s in model['scopes']}; scope_rows = {r['scopeId']: r for r in descriptor['scopeEntries']}
    outputs = {'native.css': NATIVE_CSS.encode()}
    global_body = '<p class="native-note">这是已有共同目标下的全局文献／挑战结构；不是64个任务，也不把编辑阅读条件提升为milestone。</p>'
    global_body += _native_forest(model, descriptor['positions'], descriptor['roots'], 'scope:all', global_map=True, expanded_ids=set(descriptor['initialExpandedIds']))
    outputs['index.html'] = _page('全局研究图 · 原生阅读', global_body)
    directory, seen = [], set()
    groups = list(model.get('directoryGroups', [])) + [{'label': '其他保留入口与来源索引', 'scopeIds': list(scopes)}]
    for group in groups:
        rows = []
        for sid in list(group.get('scopeIds', [])) + list(group.get('nestedScopeIds', [])):
            if sid not in scopes or sid in seen: continue
            seen.add(sid); s = scopes[sid]; mapped = bool(scope_rows[sid]['bridges'])
            rows.append('<li data-scope-id="' + _esc(sid) + '"><a href="' + _scope_name(sid) + '">' + _esc(s['label']) + '</a> · ' + _esc(s.get('displayRole') or s['kind']) + (' · 已有类型化关联' if mapped else ' · 编辑阅读挂点；无旧发展图类型桥') + '</li>')
        if rows: directory.append('<section><h2>' + _esc(group.get('label') or group['id']) + '</h2><ul>' + ''.join(rows) + '</ul></section>')
    outputs['directory.html'] = _page('全部研究范围与角色', '<p>以下是已存在的阅读目录分组，不是互斥科学分类；任务、条件、协议、邻接问题与来源索引分开标注。</p><div class="native-directory">' + ''.join(directory) + '</div>')

    for pid, p in descriptor['positions'].items():
        trail, cursor = [], p
        while cursor:
            trail.append('<a href="' + _node_name(cursor['id']) + '">' + _esc(cursor['label']) + '</a>')
            cursor = descriptor['positions'].get(cursor['parentId'])
        body = '<nav aria-label="全局到局部">' + ' → '.join(reversed(trail)) + '</nav>'
        body += _entity_body(model, p['entityId'], p.get('paperId'), p.get('versionId'))
        if p['childIds']:
            body += '<h2>继续展开</h2><ul>' + ''.join('<li><a href="' + _node_name(cid) + '">' + _esc(descriptor['positions'][cid]['label']) + '</a></li>' for cid in p['childIds']) + '</ul>'
        for eid in p['annotationEntityIds']:
            e = model['entities'][eid]; versions = e.get('versionIds', [])
            body += '<details class="native-evidence"><summary>来源注记：' + _esc(e['label']) + '</summary><p>并行来源或相关证据，不因此改变科学包含或合并不同版本答案。</p>' + _entity_body(model, eid, e.get('paperId'), versions[0] if len(versions) == 1 else None) + '</details>'
        rows = [r for r in descriptor['scopeEntries'] if pid in r['positionIds']]
        if rows:
            body += '<h2>相关阅读范围（关联不等于包含）</h2><ul>' + ''.join('<li><a href="' + _scope_name(r['scopeId']) + '">' + _esc(scopes[r['scopeId']]['label']) + '</a> · ' + _esc('；'.join(_relation_label(b['relationType']) for b in r['bridges'])) + '</li>' for r in rows) + '</ul>'
        if p.get('paperId'):
            body += '<h2>明确选择论文来源版本后进入原解析结构</h2><ul>' + ''.join('<li><a href="' + _analysis_name(p['paperId'], vid) + '">' + _esc(model['versions'][vid]['label']) + '</a></li>' for vid in model['papers'][p['paperId']].get('versionIds', [])) + '</ul>'
        body += '<p><a href="' + _esc(_enhanced(p)) + '">在联动全图打开此精确位置</a></p>'
        outputs[_node_name(pid)] = _page(p['label'], body)

    for sid, s in scopes.items():
        row = scope_rows[sid]
        body = '<p class="native-identity">' + _esc(s.get('displayRole') or s['kind']) + ' · ' + ('存在已审类型化关联；不等于同身份或包含' if row['bridges'] else '编辑阅读挂点；无旧发展图类型桥，已有材料按原关联阅读') + '</p>'
        body += '<nav><a href="#literature">文献视角</a><a href="#challenge">挑战视角</a><a href="#analysis">论文与明确版本</a><a href="#conditions">任务与评测条件</a></nav>'
        if row['positionIds']:
            body += '<p>全局来路：' + ' · '.join('<a href="' + _node_name(pid) + '">' + _esc(descriptor['positions'][pid]['label']) + '</a>' for pid in row['positionIds']) + '</p>'
        for tree, section, label in [('l', 'literature', '文献视角'), ('c', 'challenge', '挑战–思路视角')]:
            forest = model['forests'].get(sid, {}).get(tree, [])
            coverage = model['coverage'].get(sid, {}); direct = coverage.get('direct', {})
            count = direct.get('methodCount' if tree == 'l' else 'challengeCount', 0)
            body += '<section id="' + section + '"><h2>' + label + '</h2>'
            if not count:
                body += '<p class="native-note">此范围暂无直接适用的已核' + ('方法' if tree == 'l' else '困难') + '覆盖；原有条件投影、相关材料或来源仍按各自类型保留，不补造结论。</p>'
            body += _native_forest(model, model['positions'], forest, sid) if forest else '<p>暂无已核树分支，保留待核状态。</p>'
            body += '</section>'
        body += '<details id="conditions"><summary>任务与评测条件、原文与边界</summary>' + _entity_body(model, s['entityId'])
        for eid in list(s.get('benchmarkIds', [])) + list(s.get('protocolVariantIds', [])):
            if eid in model['entities']:
                e = model['entities'][eid]; body += '<details><summary>' + _esc(e['label']) + '</summary>' + _entity_body(model, eid) + '</details>'
        body += '</details><section id="analysis"><h2>论文解析：明确选择论文与版本</h2><p>只有已导入的同版本包含回答；其他来源保留原59节点未答结构。快照不冒充固定版本。</p><ul>'
        for paper_id in s.get('paperIds', []):
            paper = model['papers'][paper_id]
            for vid in paper.get('versionIds', []):
                v = model['versions'][vid]; available = vid in model['analyses'].get(paper_id, {})
                body += '<li><a href="' + _analysis_name(paper_id, vid) + '">' + _esc(paper.get('label') or paper.get('title') or paper_id) + ' · ' + _esc(v['label']) + '</a> · ' + ('同版本部分回答' if available else '原59结构／0已答') + '</li>'
        body += '</ul></section>'
        outputs[_scope_name(sid)] = _page(s['label'], body)

    for paper_id, paper in model['papers'].items():
        for vid in paper.get('versionIds', []):
            version = model['versions'][vid]
            if version.get('paperId') != paper_id: raise ValueError('Analysis source version mismatch')
            a = model['analyses'].get(paper_id, {}).get(vid)
            roots = a['roots'] if a else model['template']['roots']
            title = (paper.get('label') or paper.get('title') or paper_id) + ' · ' + version['label']
            body = '<p class="native-identity">已明确选择以上论文／来源版本；' + ('此来源是未固定快照。' if version.get('status') == 'snapshot_not_version_pinned' else '来源身份按该记录单独保留。') + '</p>'
            if a:
                body += '<p>原59节点保留；' + str(a['answeredOriginalCount']) + '个原节点已填，' + str(a.get('instanceCount', 0)) + '个本篇实例展开；不表示全文或独立复现完成。</p>'
            else:
                body += '<p class="native-boundary">此版本未导入逐节点解析：原59结构全部保留，0已答。不借用另一版本或另一论文答案。</p>'
            body += _native_forest(model, model['positions'], roots, 'scope:all', paper_id, vid, not bool(a))
            outputs[_analysis_name(paper_id, vid)] = _page(title, body)
    return outputs


def write_scope_pages(root, target, model, descriptor):
    """Write only a deterministic flat branches directory after full preflight."""
    from build_topic_preview import require, safe_path, safe_target
    root = Path(root).absolute(); target = safe_target(root, target)
    require(target.relative_to(root).parts[0] not in {'assets', 'data', 'scripts', 'tests', 'previews', 'docs'}, 'Native output cannot overlap source')
    dest = safe_path(root, target / 'research/navigation/branches')
    outputs = _build_scope_outputs(model, descriptor)
    if dest.exists():
        require(dest.is_dir(), 'Native output must be a directory')
        require({p.name for p in dest.iterdir()} == set(outputs), 'Unexpected native output files')
        for path in dest.iterdir():
            safe_path(root, path); require(stat.S_ISREG(path.stat().st_mode), 'Native output must be regular files')
    manifest = [{'path': 'research/navigation/branches/' + name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()} for name, data in sorted(outputs.items())]
    dest.mkdir(parents=True, exist_ok=True)
    for name, data in outputs.items():
        path = safe_path(root, dest / name); fd, tmp = tempfile.mkstemp(prefix='.native-', dir=dest)
        try:
            with os.fdopen(fd, 'wb') as out: out.write(data)
            os.replace(tmp, path)
        finally:
            if os.path.exists(tmp): os.unlink(tmp)
    return {'schemaVersion': 'research-map-native-output/1', 'sourceModelSha256': SOURCE_SHA, 'files': manifest,
            'totalBytes': sum(x['bytes'] for x in manifest), 'pageCount': sum(x['path'].endswith('.html') for x in manifest)}


def _extend_canonical_scopes(model, descriptor):
    """Expose the already reviewed scope forests through explicit editorial edges.

    Directory groups are UI organization copied from the existing model, not new
    scientific taxonomies. All scientific child edges retain their old position
    witnesses and association. Legacy development branches remain independently
    inspectable, rather than being mistaken for the only permissible task space.
    """
    descriptor['presentationEntities'] = {}
    positions = descriptor['positions']; scopes = {s['id']: s for s in model['scopes']}
    l_id = next(pid for pid, p in positions.items() if p['entityId'] == LITERATURE)
    legacy_children = list(positions[l_id]['childIds']); positions[l_id]['childIds'] = []
    def new_id(key):
        return 'pos:g:' + hashlib.sha256(('canonical-editorial-v1\x1f' + key).encode()).hexdigest()[:22]
    def editorial(key, parent, label, kind, eid=None, **proof):
        pid = new_id(key)
        if eid is None:
            eid = 'display:research-map:' + hashlib.sha256(key.encode()).hexdigest()[:22]
            detail = {'description': proof.get('displayRole', '编辑阅读导航，不构成科学分类或包含断言')}
            if proof.get('sourceDirectoryGroupId'): detail['sourceDirectoryGroupId'] = proof['sourceDirectoryGroupId']
            descriptor['presentationEntities'][eid] = {'id': eid, 'kind': kind, 'label': label, 'paperId': None, 'versionIds': [], 'claimIds': [], 'sourceRefs': [], 'detail': detail}
        if pid in positions: raise ValueError('Global editorial position collision')
        p = {'id': pid, 'tree': 'g', 'scopeId': 'scope:all', 'entityId': eid,
             'paperId': None, 'versionId': None, 'versionIds': [], 'claimIds': [],
             'parentId': parent, 'childIds': [], 'label': label, 'kind': kind,
             'depth': positions[parent]['depth'] + 1, 'order': len(positions[parent]['childIds']),
             'status': 'editorial_navigation_not_scientific_assertion', 'association': 'direct',
             'sourceRelationIds': [], 'relationType': 'editorial_navigation_not_scientific_containment',
             'edgeSemantics': 'editorial_navigation', 'annotationEntityIds': [],
             'annotationRelationIds': [], **proof}
        positions[pid] = p; positions[parent]['childIds'].append(pid)
        return pid
    scope_positions = {}
    groups = list(model.get('directoryGroups', []))
    group_by_scope = {}
    for g in groups:
        for sid in g.get('scopeIds', []) + g.get('nestedScopeIds', []):
            if sid not in group_by_scope: group_by_scope[sid] = g['id']
    children_scopes = defaultdict(list)
    for s in scopes.values():
        if s.get('parentScopeId') in scopes: children_scopes[s['parentScopeId']].append(s['id'])
    groups_by_id = {g['id']: g for g in groups}
    group_positions = {}
    for g in groups:
        group_positions[g['id']] = editorial('directory:' + g['id'], l_id, g['label'],
            'editorial_directory_group', sourceDirectoryGroupId=g['id'],
            displayRole='编辑阅读分组；不是科学分类或milestone')
    work_for_recipe = {r['recipeEntityId']: r['workEntityId'] for r in descriptor['workRecipeBindings']}

    def clone_old(pid, parent, sid):
        old = model['positions'][pid]
        if old.get('association') == 'context':
            positions[parent].setdefault('relatedReadingPositionIds', []).append(pid)
            return None
        nid = new_id('source-position:' + sid + ':' + pid)
        p = {k: (list(v) if isinstance(v, list) else v) for k, v in old.items()}
        p.update({'id': nid, 'tree': 'g', 'scopeId': 'scope:all', 'parentId': parent,
                  'childIds': [], 'depth': positions[parent]['depth'] + 1,
                  'order': len(positions[parent]['childIds']), 'sourcePositionId': pid,
                  'sourceParentPositionId': old['parentId'], 'sourceScopeId': sid,
                  'sourceTree': 'l', 'edgeSemantics': 'source_position_projection',
                  'sourceRelationIds': [], 'annotationEntityIds': [], 'annotationRelationIds': [],
                  'sourceLabel': old['label']})
        if old['kind'] == 'pipeline_recipe' and old.get('paperId'):
            p['labelSourcePaperId'] = old['paperId']
            p['label'] = model['papers'][old['paperId']]['title']
            if old['entityId'] in work_for_recipe:
                p['annotationEntityIds'].append(work_for_recipe[old['entityId']])
        positions[nid] = p; positions[parent]['childIds'].append(nid)
        for child in old.get('childIds', []): clone_old(child, nid, sid)
        return nid

    def add_scope(sid, parent):
        if sid in scope_positions: return scope_positions[sid]
        s = scopes[sid]
        pid = editorial('scope:' + sid, parent, s['label'], s['kind'], eid=s['entityId'],
                         sourceScopeId=sid, sourceParentScopeId=s.get('parentScopeId'),
                         sourceDirectoryGroupId=group_by_scope.get(sid),
                         displayRole=s.get('displayRole') or s['kind'],
                         scopeDefinition=s.get('definition') or '',
                         coverageCategory='uncomputed')
        scope_positions[sid] = pid
        for child in children_scopes[sid]: add_scope(child, pid)
        roots = model['forests'].get(sid, {}).get('l', [])
        positions[pid]['sourceRootPositionIds'] = list(roots)
        if len(roots) != 1: raise ValueError('Expected one canonical literature scope root')
        old_root = model['positions'][roots[0]]
        positions[pid].update({'sourcePositionId': roots[0], 'sourceParentPositionId': old_root['parentId'], 'sourceTree': 'l', 'sourceLabel': old_root['label']})
        for old_root in roots:
            for child in model['positions'][old_root].get('childIds', []): clone_old(child, pid, sid)
        c = model.get('coverage', {}).get(sid, {})
        direct = c.get('direct', {}).get('methodCount', 0)
        condition = c.get('condition', {}).get('methodCount', 0)
        positions[pid]['coverageCategory'] = 'direct_methods' if direct else 'condition_methods_only' if condition else 'no_reviewed_method'
        positions[pid]['directMethodCount'] = direct; positions[pid]['conditionMethodCount'] = condition
        positions[pid]['relatedReadingPositionIds'] = [p['id'] for p in model['positions'].values()
            if p.get('scopeId') == sid and p.get('association') == 'context']
        return pid
    for g in groups:
        for sid in g.get('scopeIds', []) + g.get('nestedScopeIds', []):
            if sid == 'scope:all' or sid not in scopes or scopes[sid].get('parentScopeId') in scopes: continue
            add_scope(sid, group_positions[g['id']])
    remaining = [sid for sid in scopes if sid != 'scope:all' and sid not in scope_positions]
    for sid in remaining:
        s = scopes[sid]
        group_id = s.get('groupId')
        if group_id not in group_positions: raise ValueError('Scope has no evidenced editorial group')
        parent_scope = s.get('parentScopeId')
        add_scope(sid, scope_positions.get(parent_scope, group_positions[group_id]))
    development = editorial('reviewed-development', l_id, '已有证据支持的发展与问题条件分支',
        'development_group', displayRole='原有发展线索；不是任务总量或新milestone分类')
    positions[development]['childIds'] = legacy_children
    for child in legacy_children:
        positions[child]['parentId'] = development
        positions[child]['sourceParentEntityId'] = LITERATURE
        positions[child]['edgeSemantics'] = 'editorial_reparent_preserving_source_relation'
    # The display wrapper is explicitly not the original scientific relation parent.
    def redepth(pid, depth):
        positions[pid]['depth'] = depth
        for order, child in enumerate(positions[pid]['childIds']):
            positions[child]['order'] = order; redepth(child, depth + 1)
    redepth(descriptor['roots'][0], 0)
    for row in descriptor['scopeEntries']:
        row['legacyPositionIds'] = list(row['positionIds'])
        row['legacyMappingStatus'] = row['mappingStatus']
        row['positionIds'] = [descriptor['roots'][0]] if row['scopeId'] == 'scope:all' else [scope_positions[row['scopeId']]]
        row['canonicalPositionId'] = row['positionIds'][0]
        row['mappingStatus'] = 'virtual_source_index' if row['scopeId'] == 'scope:all' else 'canonical_scope_editorial_entry'
        row['placementEvidence'] = 'existing_scope_role_definition_and_literature_forest'
    coverage = descriptor['coverage']
    coverage['legacyAudit'] = {k: coverage[k] for k in ('scopesWithTypedBridges', 'scopesWithoutTypedBridges',
        'scopesWithVisibleGlobalPosition', 'scopesPendingGlobalPlacement', 'scopesBridgedButTargetNotVisible')}
    coverage.update({'displayPositions': len(positions), 'displayEntities': len({p['entityId'] for p in positions.values()}),
        'scopesWithVisibleGlobalPosition': len(descriptor['scopeEntries']), 'scopesPendingGlobalPlacement': 0,
        'canonicalScopeEntries': len(scope_positions), 'virtualSourceIndexEntries': 1,
        'originalLiteraturePositionsProjected': sum(p.get('sourceTree') == 'l' for p in positions.values()),
        'scopeRolePolicy': 'existing_displayRole_not_all_contexts_are_tasks_or_milestones'})
    descriptor['canonicalScopePositionIds'] = scope_positions
    descriptor['initialExpandedIds'] = [descriptor['roots'][0], l_id,
        next(pid for pid, p in positions.items() if p['entityId'] == CHALLENGE)] + [group_positions['task']]
    descriptor['editorialNavigationContract'] = {'version': 'canonical-scope-navigation/1',
        'scientificContainmentUnchanged': True, 'groupBasis': 'existing directoryGroups and explicit parentScopeId',
        'notScientificTaxonomy': True, 'notMilestoneLabels': True,
        'conditionEdgesPreserved': True, 'contextOnlyNeverSolutionChild': True}
    # Display order is the childIds order. Source status remains in frozen entities
    # and original positions (linked by sourcePositionId); do not duplicate it
    # in the inline display-only projection.
    for position in positions.values():
        position.pop('status', None)
        position.pop('order', None)
    return descriptor
