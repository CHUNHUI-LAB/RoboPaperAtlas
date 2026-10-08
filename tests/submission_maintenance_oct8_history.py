"""Strict inverse of the reviewed October 8 T-RO presentation note.

Only the known reviewed append is accepted. Unknown future snapshots fail closed;
new batches must supply their own reviewed inverse, never replace old digests.
"""
import copy
import hashlib
import json

BASELINE_SHA256 = 'f9232d3eb1e521cfbd30a703357ec7971d3e30706f8c0033945c6736d01dfcb5'
CANDIDATE_SHA256 = 'b646147f7b7fa42eb72bb79cf6a404c44a4358d41c22adcb8e372987a744d9ee'


def canonical_sha256(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':')).encode()).hexdigest()


def project_before_oct8_maintenance(data):
    restored = copy.deepcopy(data)
    if restored['checked_at'] == '2026-10-06':
        assert canonical_sha256(restored) == BASELINE_SHA256
        return restored
    assert restored['checked_at'] == '2026-10-08'
    assert canonical_sha256(restored) == CANDIDATE_SHA256
    update = restored['maintenance_history'].pop()
    assert update['checked_at'] == '2026-10-08'
    assert update['previous_snapshot'] == '2026-10-06'
    assert set(update['prior_records']) == {'tro-policy-20261001'}
    assert restored['sources'][-1]['id'] == 'maintenance-tro-presentation-20261008'
    restored['sources'].pop()
    index = next(i for i, e in enumerate(restored['editions'])
                 if e['id'] == 'tro-policy-20261001')
    restored['editions'][index] = update['prior_records']['tro-policy-20261001']
    restored['checked_at'] = update['previous_snapshot']
    assert canonical_sha256(restored) == BASELINE_SHA256
    return restored
