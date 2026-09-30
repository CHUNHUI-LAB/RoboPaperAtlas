"""Audited primary-question display adapter; canonical bibliographic data stays intact.

Direction, method and resource kind are different axes. There is no legacy
category fallback: every paper requires an explicit reviewed placement.
"""
import json,re,hashlib
from pathlib import Path
from atlas_taxonomy import atlas_projection
from validate import check_url
ROOT=Path(__file__).resolve().parents[1]
EXPECTED_DIRECTIONS=('navigation','mobile-manipulation','wbc','locomotion','policy-learning','spatial-representations','general-ml')
RESOURCE_LABELS={'benchmark':'Benchmark','data-collection':'Data Collection','data-generator':'Data Generator','dataset':'Dataset','model':'Model','simulator':'Simulator','software':'Software'}
CHINESE={'navigation':'具身导航','mobile-manipulation':'移动操作','wbc':'全身运动规划与控制','locomotion':'运动与步态','policy-learning':'策略学习','spatial-representations':'空间表征','general-ml':'通用机器学习','resources':'跨领域资源','cross-domain':'跨领域研究'}

def validate_projection(data):
    if [d['id'] for d in data['directions']][:7]!=list(EXPECTED_DIRECTIONS):raise ValueError('Explicit reviewed direction order required')
    for d in data['directions']:
        if not re.fullmatch('[a-z][a-z-]*',d['id']):raise ValueError('Invalid direction id')
    for pid,p in data['placements'].items():
        if not re.fullmatch('[a-z0-9][a-z0-9-]*',pid):raise ValueError('Invalid paper id')
        for url in p['sources']:check_url(url)
        for tag in p['methodTags']:
            if not isinstance(tag['label'],str) or not tag['label'] or '|' in tag['label']:raise ValueError('Invalid method label')
            check_url(tag['source'])
        if any(x not in RESOURCE_LABELS for x in p['resourceKinds']):raise ValueError('Unknown resource kind')
    return data

def validate_overlay(overlay,papers):
    envelope={'schema_version','status','catalog_sha256','scope','primary_axis','directions','null_direction_display','records','counts','direction_full_names','revision','evidence_counts','pending_ids'}
    record_fields={'additional_review','canonical_category_preserved','classification_confidence','classification_status','evidence_note','evidence_scope','full_paper_read','id','method_evidence_note','method_tags','needs_review','placement_state','primary_direction','rationale','resource_kind_evidence_scope','resource_kinds','review_note','secondary_directions','source_catalog_record','source_checked_at','source_identity_note','source_urls','subdirection','title'}
    if set(overlay)-envelope or overlay.get('schema_version')!=1:raise ValueError('Unknown classification schema')
    if tuple(overlay['directions'])!=EXPECTED_DIRECTIONS:raise ValueError('Unknown direction set/order')
    if overlay['catalog_sha256']!=hashlib.sha256((ROOT/'data/catalog.json').read_bytes()).hexdigest():raise ValueError('Classification must be reviewed against current catalog bytes')
    for row in overlay['records']:
        if set(row)-record_fields:raise ValueError('Unknown classification record field')
        if not isinstance(row['needs_review'],bool) or not isinstance(row['full_paper_read'],bool):raise ValueError('Classification boolean expected')
        if row['subdirection'] and (set(row['subdirection'])!={'id','label','status'} or not re.fullmatch('[a-z0-9][a-z0-9-]*',row['subdirection']['id'])):raise ValueError('Invalid problem identifier')
        if any(d not in EXPECTED_DIRECTIONS for d in row['secondary_directions']):raise ValueError('Unknown secondary direction')
        for tag in row['method_tags']:
            if set(tag)!={'label','evidence_scope','confidence','source'}:raise ValueError('Unknown method evidence field')
    return validate_projection(atlas_projection(papers,overlay))

PAPERS=json.loads((ROOT/'data/catalog.json').read_text())['papers']
OVERLAY=json.loads((ROOT/'data/classification.json').read_text())
TAXONOMY=validate_overlay(OVERLAY,PAPERS)
ORIGINAL_CATEGORIES={p['id']:p['category'] for p in PAPERS}
TOPIC_LABELS={d['id']:d['label'] for d in TAXONOMY['directions']}
TOPIC_FULL_NAMES={d['id']:d['english'] for d in TAXONOMY['directions']}
TOPIC_CHINESE=CHINESE
TOPIC_HINTS={k:TOPIC_FULL_NAMES[k]+' · '+CHINESE[k] for k in TOPIC_LABELS}
RESEARCH_TOPICS=EXPECTED_DIRECTIONS

def classification(paper):
    pid=paper['id']
    if pid not in TAXONOMY['placements'] or ORIGINAL_CATEGORIES[pid]!=paper['category']:
        raise ValueError('An explicit reviewed classification is required: '+pid)
    return TAXONOMY['placements'][pid]
def primary_topic(paper):return classification(paper)['direction']
def paper_topics(paper):return (primary_topic(paper),)
def method_tags(paper):return tuple(t['label'] for t in classification(paper)['methodTags'])
def resource_kinds(paper):return tuple(classification(paper)['resourceKinds'])
def topic_counts(papers):return {key:sum(primary_topic(p)==key for p in papers) for key in TOPIC_LABELS}
def taxonomy_search(paper):
    c=classification(paper)
    return ' '.join([TOPIC_LABELS[c['direction']],TOPIC_HINTS[c['direction']],c['problemLabel'],*method_tags(paper),*(RESOURCE_LABELS[x] for x in resource_kinds(paper))])
