"""Strict, test-only inverse of the October 6 NeurIPS data supplement."""
import copy
import hashlib
import json

BASELINE_SHA256 = 'fc06a018d980fe2474a8018c6b93e4860a2e5fb4c51e0978ed5f6715f005c03c'
EDITION_SHA256 = '216982e61a5775adbf74d22c6f9460935897f4ed0c32ac5d606802dfdc926657'
SOURCES_SHA256 = 'b2c9406e861cd5034973e6cbd3a09ac86fcf2ed1f89efb8ac86a10008c38ec3f'
HISTORY_SHA256 = '3ca3470a63e0d7f8530ee482814ec02c0bc65a1aaa30977751c576ca990400b3'


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def project_before_oct6_maintenance(data):
    restored = copy.deepcopy(data)
    assert restored['checked_at'] == '2026-10-06'
    update = restored['maintenance_history'].pop()
    assert canonical_sha256(update) == HISTORY_SHA256
    assert update['checked_at'] == '2026-10-06'
    assert update['previous_snapshot'] == restored['maintenance_history'][-1]['checked_at']
    assert set(update['prior_records']) == {'neurips-2026'}
    index = next(i for i, e in enumerate(restored['editions']) if e['id'] == 'neurips-2026')
    assert canonical_sha256(restored['editions'][index]) == EDITION_SHA256
    assert canonical_sha256(restored['sources'][-2:]) == SOURCES_SHA256
    restored['editions'][index] = update['prior_records']['neurips-2026']
    restored['sources'] = restored['sources'][:-2]
    restored['checked_at'] = update['previous_snapshot']
    assert canonical_sha256(restored) == BASELINE_SHA256
    return restored
