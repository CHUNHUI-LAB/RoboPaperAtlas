"""Metadata-based presentation facets, separate from canonical catalog categories.

These are provisional navigation aids, not verified scientific classifications.
Cross-facet membership is intentional. No paper IDs, original records, or tags change.
"""
TOPIC_LABELS = {
    'navigation': 'Embodied Nav',
    'wbc': 'WBC',
    'vla': 'VLA',
    'methods': 'Methods',
    'sim-tools': 'Sim & Tools',
    'data-benchmarks': 'Data & Benchmarks',
}
TOPIC_FULL_NAMES = {
    'navigation': 'Embodied Navigation',
    'wbc': 'Whole-body Control & Loco-manipulation',
    'vla': 'Vision-Language-Action',
    'methods': 'Learning, Modeling & Representation Methods',
    'sim-tools': 'Simulation, Software & Data-collection Tools',
    'data-benchmarks': 'Datasets, Benchmarks & Evaluation Protocols',
}
TOPIC_CHINESE = {
    'navigation': '具身导航',
    'wbc': '全身控制与移动操作',
    'vla': '视觉语言动作',
    'methods': '学习、建模与表征方法',
    'sim-tools': '仿真、软件与数据采集工具',
    'data-benchmarks': '数据集、基准与评测协议',
}
TOPIC_HINTS = {key: f'{TOPIC_FULL_NAMES[key]} · {TOPIC_CHINESE[key]}' for key in TOPIC_LABELS}
# First entry gives the stable primary star region; all entries are filter facets.
# Membership uses the existing title/tags/curated note, never fabricated citation or method-inheritance links.
FOUNDATION_FACETS = {
    'rpa-0004': ('methods',),
    'rpa-0008': ('methods',),
    'rpa-0013': ('methods',),
    'rpa-0014': ('methods',),
    'rpa-0017': ('sim-tools', 'data-benchmarks'),
    'rpa-0018': ('methods',),
    'rpa-0021': ('methods',),
    'rpa-0022': ('sim-tools',),
    'rpa-0032': ('sim-tools',),
    'rpa-0033': ('data-benchmarks',),
    'rpa-0039': ('sim-tools',),
    'rpa-0044': ('data-benchmarks', 'methods'),
    'rpa-0045': ('sim-tools',),
    'rpa-0046': ('methods',),
    'rpa-0047': ('methods',),
    'rpa-0053': ('data-benchmarks', 'sim-tools'),
    'rpa-0058': ('methods',),
    'rpa-0060': ('data-benchmarks',),
    'rpa-0063': ('methods',),
    'rpa-0064': ('sim-tools', 'methods'),
    'rpa-0071': ('methods',),
    'anderson2018r2r': ('data-benchmarks', 'navigation'),
    'ku2020rxr': ('data-benchmarks', 'navigation'),
    'krantz2020vlnce': ('data-benchmarks', 'navigation', 'methods'),
    'savva2019habitat': ('sim-tools', 'navigation', 'data-benchmarks'),
    'ramakrishnan2021hm3d': ('data-benchmarks', 'navigation'),
    'yadav2023hm3dsem': ('data-benchmarks', 'navigation'),
    'batra2020objectnav': ('data-benchmarks', 'navigation'),
    'huang2023vlmaps': ('methods', 'navigation'),
    'gu2024conceptgraphs': ('methods', 'navigation'),
    'krantz2023ivln': ('data-benchmarks', 'navigation', 'methods'),
}

def paper_topics(paper):
    if paper['category'] != 'foundations':
        return (paper['category'],)
    if paper['id'] not in FOUNDATION_FACETS:
        raise ValueError('Foundation record needs explicit metadata-based presentation facet review: '+paper['id'])
    return FOUNDATION_FACETS[paper['id']]

def primary_topic(paper):
    return paper_topics(paper)[0]

def topic_counts(papers):
    return {key: sum(key in paper_topics(p) for p in papers) for key in TOPIC_LABELS}
