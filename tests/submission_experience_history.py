"""Strict inverse of the reviewed October 4 experience-only append.

Frozen source-reviewed append. This projection is for tests, never publication.
Verify additions before removing them, then verify the complete old envelope.
"""
import copy
import hashlib
import json

OCT4_IDS = (
    'tokekar-robotics-writing-2019',
    'milford-iros-writing-anticipation-2024',
    'zhang-robotics-metrics-2023',
    'reddit-ral-baseline-gap-2022',
    'ye-cooperative-perception-reflection-2023',
)
OCT4_SYNTHESIS_IDS = (
    'match-baselines-and-essential-metrics',
    'test-assumptions-before-polishing-story',
)
PRE_APPEND_DATA_SHA256 = '5338c46d7d04e66087b2df9ca4d97c5cab630002d097fb88abfb2dab4cad6381'
PRE_APPEND_EXPERIENCES_SHA256 = '718874f4706078d43a36394aae6c24d24c9d5e835914fc19c3cb3df9307f2b16'
# Fingerprints of the reviewed additions, fixed independently of test inputs.
OCT4_RECORDS_SHA256 = '9769bd658b6602dc57108f2bdefea451ce838888e0fef8947ad860e2b06a7cbf'
OCT4_SYNOPSES_SHA256 = '32102a8c4abf4c9e3b407f4c61fdc77af80a1e1da138d45a4114c724a956aab3'
OCT4_SYNTHESES_SHA256 = '933f185851387b8919fa53b9071225fc6681b9e16aff21120caf5928338a49a1'
OCT4_OVERVIEW_FIELDS_SHA256 = '6105d589e7925ae647bea695ba388a000b50534d7c2337f57e185f9b92e93e4c'
PRIOR_OVERVIEW_FIELDS = {'schema_version': 1,
 'updated_at': '2026-10-02',
 'summary': '这组资料适合用来检查贡献与验证、组织逐条回复，并把投稿阶段与结果分清。长等待可能接着短返修窗口；同帖不同人的经历不能混接；认真补证据、获得回复机会或转投都不保证接收。转投去向还要分清主会与工作坊。',
 'evidence_note': '共 14 条来源记录，包含个人投稿经历、作者建议、审稿者自述和论坛讨论。条数不等于独立作者、论文或成功样本数；多个帖子出现同一账号，JFR '
                  '三份匿名评价的作者独立性无法确认。年份未知与工作坊个案均单独注明，不据此计算录用概率或平均周期。'}


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def project_before_oct4_experience_append(data):
    frozen = (OCT4_RECORDS_SHA256, OCT4_SYNOPSES_SHA256,
              OCT4_SYNTHESES_SHA256, OCT4_OVERVIEW_FIELDS_SHA256)
    assert all(isinstance(h, str) and len(h) == 64 and
               all(c in '0123456789abcdef' for c in h) for h in frozen), 'Append not frozen'
    from submission_maintenance_oct6_history import project_before_oct6_maintenance
    restored = project_before_oct6_maintenance(data)
    pack = restored['experiences']
    records, overview, synthesis = pack['records'], pack['overview'], pack['editorial_synthesis']
    assert len(records) == 19, 'Expected exactly 14 old and 5 appended records'
    assert len(overview['records']) == 19, 'Expected exactly 19 source synopses'
    assert len(synthesis) == 8, 'Expected exactly 6 old and 2 appended syntheses'
    assert tuple(r['id'] for r in records[14:]) == OCT4_IDS
    assert tuple(r['record_id'] for r in overview['records'][14:]) == OCT4_IDS
    assert tuple(s['id'] for s in synthesis[6:]) == OCT4_SYNTHESIS_IDS
    assert canonical_sha256(records[14:]) == OCT4_RECORDS_SHA256
    assert canonical_sha256(overview['records'][14:]) == OCT4_SYNOPSES_SHA256
    assert canonical_sha256(synthesis[6:]) == OCT4_SYNTHESES_SHA256
    assert canonical_sha256({k: v for k, v in overview.items() if k != 'records'}) == OCT4_OVERVIEW_FIELDS_SHA256
    pack['records'] = records[:14]
    pack['editorial_synthesis'] = synthesis[:6]
    overview['records'] = overview['records'][:14]
    overview.update(PRIOR_OVERVIEW_FIELDS)
    assert canonical_sha256(pack) == PRE_APPEND_EXPERIENCES_SHA256
    return restored
