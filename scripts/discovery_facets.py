"""Broad browse lenses over reviewed evidence; never scientific reclassification.

These optional overlapping lenses are UI shortcuts. The canonical bibliography,
reviewed primary question, detailed methods and resource kinds remain untouched.
"""
GROUPS = (
    ('navigation-space', '导航与空间理解', 'Navigation and Spatial Understanding'),
    ('motion-manipulation', '运动与操作', 'Motion and Manipulation'),
    ('robot-learning', '机器人学习', 'Robot Learning'),
    ('methods-resources', '基础方法与研究资源', 'Foundational Methods and Research Resources'),
)
DIRECTION_GROUPS = {
    'navigation': ('navigation-space',),
    'spatial-representations': ('navigation-space',),
    'mobile-manipulation': ('motion-manipulation',),
    'wbc': ('motion-manipulation',),
    'locomotion': ('motion-manipulation',),
    'policy-learning': ('robot-learning',),
    'general-ml': ('methods-resources',),
}
LEARNING_METHODS = frozenset({
    'RL', 'Imitation Learning', 'Adversarial Imitation', 'Diffusion',
    'Flow Matching', 'VLA', 'World Model', 'Distillation', 'Multitask Learning',
    'Multi-critic Learning', 'Cross-embodiment Training', 'Policy Optimization',
})
RESOURCE_KINDS = frozenset({'benchmark', 'dataset', 'data-collection',
                           'data-generator', 'simulator', 'software'})
METHOD_LABELS = {
    'WBC': '全身控制（WBC）', 'VLA': '视觉—语言—动作模型（VLA）',
    'MPC': '模型预测控制（MPC）', 'RL': '强化学习（RL）',
    'Imitation Learning': '模仿学习', 'Diffusion': '扩散方法',
    'Flow Matching': '流匹配', 'World Model': '世界模型',
    'VLM': '视觉语言模型（VLM）', 'VLM Planning': '视觉语言模型规划',
    'LLM Planning': '大语言模型规划', 'Agent Harness': '智能体执行框架',
    'Memory': '记忆机制', 'Motion Planning': '运动规划',
    'Trajectory Optimization': '轨迹优化', 'Force Control': '力控制',
    'Sim-to-real': '仿真到现实迁移', 'Teleoperation': '遥操作',
}

def project(records):
    result = {}
    for record in records:
        pid = record['id']
        if pid in result:
            raise ValueError('Duplicate ID: ' + pid)
        reasons = {}
        directions = [record.get('primary_direction'), *record.get('secondary_directions', [])]
        for direction in directions:
            if direction is None:
                continue
            if direction not in DIRECTION_GROUPS:
                raise ValueError('Unmapped reviewed direction: ' + direction)
            for group in DIRECTION_GROUPS[direction]:
                reasons.setdefault(group, []).append({'basis': 'reviewed-direction', 'value': direction})
        methods = {tag['label'] for tag in record.get('method_tags', [])}
        for method in sorted(methods & LEARNING_METHODS if record.get('primary_direction')!='general-ml' else set()):
            reasons.setdefault('robot-learning', []).append({'basis': 'reviewed-method', 'value': method})
        resources = set(record.get('resource_kinds', [])) & RESOURCE_KINDS
        if resources or record.get('placement_state') == 'cross-domain-resource':
            reasons.setdefault('methods-resources', []).append({'basis': 'resource-kind', 'value': sorted(resources)})
        if not reasons:
            raise ValueError('No justified browse lens; review manually: ' + pid)
        result[pid] = {'groups': [g[0] for g in GROUPS if g[0] in reasons],
                       'reasons': reasons,
                       'needsReview': record.get('needs_review', False)}
    return result

def counts(placements):
    return {key: sum(key in item['groups'] for item in placements.values())
            for key, _, _ in GROUPS}


def for_catalog(papers,records):
    result=project(records)
    if set(result)!={p['id']for p in papers}:raise ValueError('Browse groups must cover exactly the catalog')
    return result

def method_label(value):return METHOD_LABELS.get(value,value)
