"""Hydrate reviewed graph previews with the current, registry-backed reading state.

Call only after the preview transport has authenticated its immutable source bytes.
This is a derived-output transform: only the JSON values at papers[].stages change.
It does not regenerate the graph, its relationships, or its classification evidence.
"""
import json
import re
from pathlib import Path

from reports import load_reports
from validate import validate_catalog

SITE_ROOT = 'https://chunhui-lab.github.io/RoboPaperAtlas/'
DATA_IDS = {'atlas-data', 'prototype-data'}


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'Duplicate preview reading JSON field: {key}')
        result[key] = value
    return result


def _constant(value):
    raise ValueError(f'Invalid preview reading JSON constant: {value}')


DECODER = json.JSONDecoder(object_pairs_hook=_object, parse_constant=_constant)


def _read_json(root, name):
    directory = Path(root) / 'data'
    path = directory / name
    if directory.is_symlink() or path.is_symlink() or not path.is_file():
        raise ValueError(f'Unsafe or missing preview reading source: {name}')
    if path.stat().st_size > 2_000_000:
        raise ValueError(f'Preview reading source is too large: {name}')
    return DECODER.decode(path.read_text(encoding='utf-8'))


def reading_stages(root):
    """Project all artifact versions in validated canonical newest-first order.

    Validate the full registry, immutable chunks, HTML, and cross-report links
    without generating output or requiring the math-rendering toolchain.
    """
    catalog = _read_json(root, 'catalog.json')
    records = load_reports(root)
    validate_catalog(catalog, records)
    return {
        paper['id']: [
            {'number': number, 'status': paper['stages'][key]['status'],
             'links': [SITE_ROOT + artifact['path']
                       for artifact in paper['stages'][key]['artifacts']]}
            for number, key in enumerate(('stage1', 'stage2', 'stage3'), 1)
        ]
        for paper in catalog['papers']
    }


def _space(text, offset):
    while offset < len(text) and text[offset] in ' \t\r\n':
        offset += 1
    return offset


def _members(text, start):
    """Locate member value spans in an already strictly decoded JSON object."""
    offset = _space(text, start + 1)
    while text[offset] != '}':
        key, offset = DECODER.raw_decode(text, offset)
        offset = _space(text, offset)
        start = _space(text, offset + 1)  # Skip the validated colon.
        _, end = DECODER.raw_decode(text, start)
        yield key, start, end
        offset = _space(text, end)
        if text[offset] == ',':
            offset = _space(text, offset + 1)


def hydrate_reading_stages(payload, root, data_id):
    """Return derived bytes; never modify the authenticated transport inputs.

    The preview must contain every canonical paper exactly once. Missing,
    duplicate, malformed, and unknown IDs fail closed instead of silently leaving
    a mixed old/new reading state. Only stages spans are replaced, so all other
    source bytes, including graph evidence and source links, remain unchanged.
    """
    if data_id not in DATA_IDS:
        raise ValueError('Unsupported preview reading data ID')
    text = payload.decode('utf-8')
    pattern = re.compile(
        r'<script id="' + re.escape(data_id)
        + r'" type="application/json">(.*?)</script>', re.S)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError('Expected exactly one preview reading data block')
    match = matches[0]
    source = match.group(1)
    data = DECODER.decode(source)
    if not isinstance(data, dict) or not isinstance(data.get('papers'), list):
        raise ValueError('Preview reading papers must be an array')
    stages = reading_stages(root)
    ids = set()
    for paper in data['papers']:
        if not isinstance(paper, dict):
            raise ValueError('Preview reading paper must be an object')
        paper_id = paper.get('id')
        if (not isinstance(paper_id, str)
                or not re.fullmatch(r'[a-z0-9][a-z0-9-]*', paper_id)
                or paper_id not in stages or paper_id in ids):
            raise ValueError('Invalid, unknown, or duplicate preview reading paper ID')
        if not isinstance(paper.get('stages'), list):
            raise ValueError('Missing preview reading stages array')
        ids.add(paper_id)
    if ids != set(stages):
        raise ValueError('Preview reading paper IDs must match the full catalog')

    _, papers_start, _ = next(member for member in _members(source, _space(source, 0))
                              if member[0] == 'papers')
    offset = _space(source, papers_start + 1)
    replacements = []
    for paper in data['papers']:
        _, start, end = next(member for member in _members(source, offset)
                             if member[0] == 'stages')
        value = json.dumps(stages[paper['id']], ensure_ascii=False, separators=(',', ':'))
        value = value.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
        replacements.append((match.start(1) + start, match.start(1) + end, value))
        _, offset = DECODER.raw_decode(source, offset)
        offset = _space(source, offset)
        if source[offset] == ',':
            offset = _space(source, offset + 1)
    for start, end, value in reversed(replacements):
        text = text[:start] + value + text[end:]
    return text.encode('utf-8')
