"""Deterministic paper-indexed bundle of sealed, concise local analysis inputs.

No retrieval, inference, Stage mutation, PDF/image redistribution or publication.
The original HarnessVLN mapping and compatibility fields remain exact aliases.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent / 'data'
SEALED_INPUTS = frozenset((
    'data/catalog.json', 'data/literature-seed.json', 'data/challenge-seed.json',
    'analysis/data/method.json', 'analysis/data/mapping.json',
    'analysis/data/analysis.compat.json', 'analysis/data/ledger.json',
    'analysis/data/UPSTREAM-VERIFICATION.json', 'analysis/data/navharness.mapping.json',
    'analysis/data/navharness.ledger.json', 'analysis/data/navharness.unknowns.json',
))


def build_bundle(data_dir=ROOT):
    data_dir = Path(data_dir)
    load = lambda name: json.loads((data_dir / name).read_text(encoding='utf-8'))
    seal = load('MULTI-PAPER-VERIFICATION.json')
    if set(seal['inputs']) != SEALED_INPUTS:
        raise ValueError('Source seal cannot expand the bounded input set')
    for name, digest in seal['inputs'].items():
        source = data_dir.parent.parent / name
        if not source.is_file() or source.is_symlink():
            raise ValueError('Reviewed source must be a regular file: ' + name)
        if hashlib.sha256(source.read_bytes()).hexdigest() != digest:
            raise ValueError('Reviewed source hash mismatch: ' + name)
    mapping = load('mapping.json')
    compat = load('analysis.compat.json')
    navharness = load('navharness.mapping.json')
    data = {
        'schema': load('method.json'),
        'mapping': mapping,
        'compat': compat,
        'mappingsByPaperId': {'harnessvln': mapping, 'navharness': navharness},
        'ledgersByPaperId': {
            'harnessvln': load('ledger.json'),
            'navharness': load('navharness.ledger.json'),
        },
        'unknownsByPaperId': {
            'harnessvln': mapping['unresolvedQuestions'],
            'navharness': load('navharness.unknowns.json'),
        },
    }
    assert compat['existingStageStateMutation'] is False
    assert [(a['nodeId'], a['state'], a['answer']) for a in mapping['answers']] == [
        (a['nodeId'], a['state'], a['answer']) for a in compat['answers']]
    assert len(data['schema']['nodes']) == 59
    for paper_id, counts in (('harnessvln', (13, 47, 6)), ('navharness', (18, 51, 12))):
        paper = data['mappingsByPaperId'][paper_id]
        assert paper['paperId'] == paper_id and paper['existingStageStateMutation'] is False
        assert tuple(len(paper[key]) for key in ('expandedNodes', 'answers', 'unresolvedQuestions')) == counts
        assert data['unknownsByPaperId'][paper_id] == paper['unresolvedQuestions']
        assert data['ledgersByPaperId'][paper_id]['paperId'] == paper_id
    assert navharness['canonicalId'] == 'navharness'
    assert navharness['sourceVersion'] == '2609.34276v1'
    return data


def bundle_bytes(data):
    return ('window.C2_DATA = ' + json.dumps(data, ensure_ascii=False) + ';\n').encode('utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'bundle.js')
    args = parser.parse_args()
    args.output.write_bytes(bundle_bytes(build_bundle()))
    print('Deterministic C2 paper-indexed bundle rebuilt from sealed local inputs')


if __name__ == '__main__':
    main()
