"""Additive Atlas display taxonomy. Never mutates bibliographic records.

Classification is editorial navigation; evidence scope is separate from reading
or citation verification. Exactly one primary placement per canonical paper.
"""
import json
from pathlib import Path

COLORS = ['#65e0c2', '#ffbb68', '#bb9cff', '#fb799b', '#7eb9ff', '#f0dc77', '#d5a8ee']
SPECIAL = {
    'resources': ('Resources', 'Cross-domain resources', '#a9bacb', 'Resources belt · 跨领域工具、数据与基础设施'),
    'cross-domain': ('Cross-domain', 'Cross-domain research', '#f5e7c8', 'Cross-domain research · 主方向尚无唯一归属'),
}

def atlas_projection(papers, overlay=None):
    if overlay is None:
        overlay = json.loads((Path(__file__).resolve().parents[1] / 'data/classification.json').read_text())
    records = overlay.get('records', [])
    by_id = {p['id']: p for p in records}
    if len(by_id) != len(records) or set(by_id) != {p['id'] for p in papers}:
        raise ValueError('Atlas classification must explicitly cover each canonical paper exactly once')
    directions = []
    for i, (key, label) in enumerate(overlay['directions'].items()):
        label = 'Motion & Control' if key == 'wbc' else label
        directions.append({'id': key, 'label': label, 'english': 'Policy Learning · robot and simulated-character policies' if key == 'policy-learning' else overlay.get('direction_full_names', {}).get(key, label),
                           'chinese': '', 'color': COLORS[i % len(COLORS)], 'kind': 'research-direction'})
    for key, (label, full, color, hint) in SPECIAL.items():
        directions.append({'id': key, 'label': label, 'english': full, 'chinese': hint, 'color': color, 'kind': key})
    valid = {d['id'] for d in directions}; result = {}; problems = {}
    for paper in papers:
        rec = by_id[paper['id']]
        if rec['canonical_category_preserved'] != paper['category']:
            raise ValueError('Canonical category mismatch in Atlas overlay: ' + paper['id'])
        direction = rec.get('primary_direction')
        if direction is None:
            placement = rec.get('placement_state')
            if placement == 'cross-domain-resource': direction = 'resources'
            elif placement == 'cross-domain-research': direction = 'cross-domain'
            else: raise ValueError('Unresolved Atlas placement must be explicit: ' + paper['id'])
        if direction not in valid: raise ValueError('Unknown Atlas direction: ' + str(direction))
        sub = rec.get('subdirection')
        if sub:
            problem = {'id': direction + '/' + sub['id'], 'label': sub['label'], 'direction': direction, 'status': sub['status']}
        else:
            # An explicit unresolved/research-resource grouping, not a guessed problem.
            problem = {'id': direction + '/overview', 'label': 'Shared infrastructure' if direction == 'resources' else 'Cross-domain research', 'direction': direction, 'status': 'editorial-navigation'}
        existing = problems.setdefault(problem['id'], problem)
        if existing['label'] != problem['label']: raise ValueError('Inconsistent subsystem label')
        result[paper['id']] = {'direction': direction, 'problem': problem['id'], 'problemLabel': problem['label'],
            'placementState': rec['placement_state'], 'secondaryDirections': rec.get('secondary_directions', []),
            'methodTags': [{key: ('formal paper sections 3.1–3.2' if key == 'evidence_scope' and str(tag.get(key, '')).startswith('formal_pdf_sections_3.1_3.2') else tag.get(key)) for key in ('label', 'evidence_scope', 'confidence', 'source')} for tag in rec.get('method_tags', [])], 'resourceKinds': rec.get('resource_kinds', []),
            'confidence': rec['classification_confidence'], 'evidenceScope': rec['evidence_scope'],
            'evidenceNote': rec.get('evidence_note', ''), 'rationale': rec['rationale'],
            'sources': rec.get('source_urls', []), 'needsReview': rec['needs_review'], 'reviewNote': rec.get('review_note', '')}
    return {'directions': directions, 'problems': list(problems.values()), 'placements': result,
            'scope': overlay.get('scope', ''), 'status': overlay.get('status', '')}
