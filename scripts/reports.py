#!/usr/bin/env python3
"""Validate and losslessly assemble the reviewed, public HTML report pilot.

No network requests or third-party dependencies. Paths are derived from an exact
identity allowlist; the registry can never supply an input or output directory.
"""
import argparse
import base64
import binascii
from datetime import date
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import re
import stat
import tempfile
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
CHUNK_BYTES = 48000
MAX_PARTS = 999
MAX_REPORT_BYTES = CHUNK_BYTES * MAX_PARTS
STAGE_FILES = {
    'stage1': 'first-pass.html',
    'stage2': 'writing-close-reading.html',
    'stage3': 'method-code-reading.html',
}
RECORD_FIELDS = {
    'paper_id', 'stage', 'version', 'filename', 'sha256', 'bytes',
    'source_sha256', 'source_edition', 'source_url', 'pdf_url', 'created_at',
    'review_status', 'rights_note', 'parts',
}
COMPUTED_FIELDS = {'sha256', 'bytes', 'parts'}
PART_FIELDS = {'file', 'bytes', 'sha256'}
REPORT_PAPERS = {
    'rpa-0052': {
        'title': 'RoboDuet',
        'versions': {'v1': {'stage1', 'stage2'}},
        'review_status': 'content_approved',
        'source_urls': {'https://ieeexplore.ieee.org/document/10925884','https://locomanip-duet.github.io/'},
        'pdf_urls': {'https://locomanip-duet.github.io/RoboDuet.pdf'},
        'arxiv_id': '2403.17367',
    },
    'rpa-0062': {
        'title': 'UMI on Legs',
        'versions': {'v1': set(STAGE_FILES), 'v2': set(STAGE_FILES), 'v3': set(STAGE_FILES), 'v4': {'stage2'}},
        'review_status': 'approved',
        'source_urls': {'https://proceedings.mlr.press/v270/ha25a.html', 'https://umi-on-legs.github.io/'},
        'pdf_urls': {'https://raw.githubusercontent.com/mlresearch/v270/main/assets/ha25a/ha25a.pdf', 'https://proceedings.mlr.press/v270/ha25a/ha25a.pdf'},
        'arxiv_id': '2407.10353',
    },
    'rpa-0012': {
        'title': 'Deep Whole-Body Control',
        'versions': {'v1': {'stage1', 'stage2', 'stage3'}, 'v2': {'stage1'}},
        'review_status': 'content_approved',
        'source_urls': {'https://proceedings.mlr.press/v205/fu23a.html'},
        'pdf_urls': {'https://proceedings.mlr.press/v205/fu23a/fu23a.pdf'},
        'arxiv_id': None,
    },
}
# Backward-compatible test/public API constant; validation uses each paper's path.
SITE_RETURN = '../../../papers/rpa-0062/index.html'


def site_return(paper_id):
    require(paper_id in REPORT_PAPERS, 'Unapproved report paper identity')
    return f'../../../papers/{paper_id}/index.html'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def _keys(value, fields, label):
    require(isinstance(value, dict) and set(value) == fields,
            f'{label}: unexpected or missing fields')


def _text(value, label, limit=4000):
    require(isinstance(value, str) and value.strip() and len(value) <= limit,
            f'{label}: nonempty text required')
    require(not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', value),
            f'{label}: control characters are not permitted')


def _digest(value, label):
    require(isinstance(value, str) and re.fullmatch(r'[0-9a-f]{64}', value),
            f'{label}: lowercase SHA-256 required')


def _public_url(value):
    # validate imports reports for catalog validation; do not create a cycle.
    from validate import check_url
    check_url(value)
    parsed = urlsplit(value)
    try:
        require(parsed.port in (None, 443), 'Only standard HTTPS ports are permitted')
    except ValueError as exc:
        raise ValueError('Invalid HTTPS port') from exc
    return parsed


def _identity(record):
    require(isinstance(record, dict), 'Report record must be an object')
    require(isinstance(record.get('paper_id'), str), 'Report paper ID must be text')
    policy = REPORT_PAPERS.get(record.get('paper_id'))
    require(policy is not None, 'Only explicitly reviewed report papers are allowed')
    version = record.get('version')
    require(isinstance(version, str) and version in policy['versions'], 'Unapproved report version')
    require(isinstance(record.get('stage'), str) and record.get('stage') in policy['versions'][version], 'Unapproved paper/version/stage identity')
    stage = record.get('stage')
    require(isinstance(stage, str) and stage in STAGE_FILES, 'Unknown report stage')
    require(record.get('filename') == STAGE_FILES[stage], 'Filename must match its stage')


def _validate_record(record):
    _keys(record, RECORD_FIELDS, 'Report')
    _identity(record)
    require(record['review_status'] == REPORT_PAPERS[record['paper_id']]['review_status'], 'Report must have its explicitly approved review state')
    for key in ('source_edition', 'rights_note'):
        _text(record[key], key)
    for key in ('sha256', 'source_sha256'):
        _digest(record[key], key)
    created = record['created_at']
    require(isinstance(created, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', created),
            'created_at must be an ISO YYYY-MM-DD date')
    try:
        date.fromisoformat(created)
    except ValueError as exc:
        raise ValueError('Invalid created_at calendar date') from exc
    for key in ('source_url', 'pdf_url'):
        _public_url(record[key])
    policy = REPORT_PAPERS[record['paper_id']]
    arxiv_id = policy['arxiv_id']
    require(record['source_url'] in policy['source_urls'] or arxiv_id is not None and re.fullmatch(
        r'https://arxiv\.org/abs/' + re.escape(arxiv_id) + r'(?:v[1-9]\d*)?', record['source_url']),
        'source_url must identify this paper’s approved official source')
    require(record['pdf_url'] in policy['pdf_urls'] or arxiv_id is not None and re.fullmatch(
        r'https://arxiv\.org/pdf/' + re.escape(arxiv_id) + r'(?:v[1-9]\d*)?(?:\.pdf)?', record['pdf_url']),
        'pdf_url must identify this paper’s approved official PDF')
    require(type(record['bytes']) is int and 0 < record['bytes'] <= MAX_REPORT_BYTES,
            'Invalid report byte count')
    parts = record['parts']
    require(isinstance(parts, list) and 0 < len(parts) <= MAX_PARTS, 'Invalid report part count')
    for index, part in enumerate(parts, 1):
        _keys(part, PART_FIELDS, 'Report part')
        require(part['file'] == f'part-{index:03d}.txt',
                'Report parts must have consecutive, ordered, unique derived filenames')
        require(type(part['bytes']) is int and 0 < part['bytes'] <= CHUNK_BYTES,
                'Each report part must contain 1 to 48000 bytes')
        _digest(part['sha256'], 'Part sha256')
    require(sum(part['bytes'] for part in parts) == record['bytes'],
            'Report/part byte counts do not agree')


def report_path(record):
    """Return the derived public artifact path, after validating the record."""
    _validate_record(record)
    return f"artifacts/{record['paper_id']}/{record['version']}/{record['filename']}"


def _parts_path(record):
    return f"data/report-parts/{record['paper_id']}/{record['version']}/{record['stage']}"


def _root(root):
    root = Path(os.path.abspath(root))
    for component in [*reversed(root.parents), root]:
        require(not component.is_symlink(), 'Symlinked root or ancestor is not permitted')
    require(root.is_dir(), 'Report root must be an existing directory')
    return root


def _safe_path(root, relative, *, required=False):
    relative = Path(relative)
    require(not relative.is_absolute() and relative.parts and
            all(piece not in ('.', '..') for piece in relative.parts), 'Unsafe derived path')
    path = root
    for index, piece in enumerate(relative.parts):
        path = path / piece
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            require(not required, f'Missing report file or directory: {relative}')
            continue
        require(not stat.S_ISLNK(mode), f'Symlinked report path is not permitted: {relative}')
        if index < len(relative.parts) - 1:
            require(stat.S_ISDIR(mode), f'Report path ancestor must be a directory: {relative}')
        else:
            require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), f'Unsafe report path type: {relative}')
    return path


def _read(root, relative, max_bytes):
    path = _safe_path(root, relative, required=True)
    require(path.is_file(), f'Report input is not a regular file: {relative}')
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, 'rb') as handle:
            info = os.fstat(handle.fileno())
            require(stat.S_ISREG(info.st_mode) and info.st_size <= max_bytes,
                    f'Report input is nonregular or too large: {relative}')
            payload = handle.read(max_bytes + 1)
            require(len(payload) <= max_bytes, f'Report input is too large: {relative}')
            return payload
    except OSError as exc:
        raise ValueError(f'Cannot safely read report input: {relative}') from exc


def _atomic_write(root, relative, payload):
    path = _safe_path(root, relative)
    # Check each ancestor before and after making it. Never mkdir through a symlink.
    parent = root
    for piece in Path(relative).parts[:-1]:
        parent = parent / piece
        _safe_path(root, parent.relative_to(root))
        parent.mkdir(exist_ok=True)
        _safe_path(root, parent.relative_to(root), required=True)
    _safe_path(root, relative)
    require(not path.exists() or path.is_file(), 'Generated target must be a regular file')
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix='.report-', delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        _safe_path(root, relative)
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


# An allowlist is intentionally stricter than a script-tag blacklist. In
# particular no SVG, MathML, resource-loading link, frame, media, or form tags.
ALLOWED_TAGS = set(('html head title meta style body main header footer nav section article aside '
                    'h1 h2 h3 h4 h5 h6 p div span a img figure figcaption br hr '
                    'ul ol li dl dt dd table caption colgroup col thead tbody tfoot tr th td '
                    'strong em b i u s del ins small sub sup mark abbr q blockquote pre code '
                    'kbd samp var time details summary input label').split())
GLOBAL_ATTRS = {'id', 'class', 'title', 'style', 'lang', 'dir', 'role', 'hidden', 'tabindex'}
TAG_ATTRS = {
    'a': {'href', 'target', 'rel'}, 'img': {'src', 'alt', 'width', 'height', 'loading', 'decoding'},
    'meta': {'charset', 'name', 'content'}, 'style': {'type', 'media'},
    'html': set(), 'input': {'type', 'checked', 'disabled', 'name', 'value'},
    'label': {'for'}, 'details': {'open', 'name'},
    'th': {'colspan', 'rowspan', 'scope', 'headers'}, 'td': {'colspan', 'rowspan', 'headers'},
    'col': {'span'}, 'colgroup': {'span'}, 'ol': {'start', 'reversed', 'type'},
    'li': {'value'}, 'time': {'datetime'}, 'del': {'datetime'}, 'ins': {'datetime'},
}
ARIA_ATTRS = {'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-hidden',
              'aria-expanded', 'aria-controls', 'aria-current', 'aria-live',
              'aria-checked', 'aria-disabled', 'aria-modal', 'aria-roledescription'}


def _safe_css(css):
    require(not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f\\]', css),
            'CSS escapes and control characters are not permitted')
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    require('/*' not in css and '*/' not in css, 'Unterminated CSS comment')
    require(not re.search(r'(?:url|expression|image-set|-webkit-image-set|image|src|paint|element)\s*\(|(?<![-\w])(?:behavior|-moz-binding)\s*:', css, re.I),
            'Active or resource-loading CSS is not permitted')
    require(not re.search(r'@(?!(?:media|supports|container|layer|keyframes|-webkit-keyframes|page)\b)', css, re.I),
            'CSS import, font sources, and unknown at-rules are not permitted')
    require(not re.search(r'(?:https?:|data:|javascript:|vbscript:|file:)', css, re.I),
            'URL-bearing CSS is not permitted')


def _image_source(value):
    require(isinstance(value, str), 'Image source required')
    match = re.fullmatch(r'data:image/(png|jpeg);base64,([A-Za-z0-9+/]*={0,2})', value)
    require(match is not None, 'Only embedded PNG/JPEG base64 image sources are permitted')
    try:
        data = base64.b64decode(match[2], validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError('Invalid image base64') from exc
    require(base64.b64encode(data).decode('ascii') == match[2], 'Noncanonical image base64')
    if match[1] == 'png':
        require(data.startswith(b'\x89PNG\r\n\x1a\n') and len(data) >= 33 and
                data[8:16] == b'\x00\x00\x00\rIHDR' and data.endswith(b'IEND\xaeB`\x82'),
                'Image does not have a PNG signature/header/trailer')
    else:
        require(len(data) >= 4 and data.startswith(b'\xff\xd8\xff') and data.endswith(b'\xff\xd9'),
                'Image does not have a JPEG signature/trailer')


def _fragment(value):
    require(not re.search(r'%(?![0-9a-fA-F]{2})', value), 'Malformed URL fragment escape')
    try:
        result = unquote(value, encoding='utf-8', errors='strict')
    except UnicodeError as exc:
        raise ValueError('Invalid UTF-8 URL fragment') from exc
    require(result and not re.search(r'[\x00-\x20\x7f]', result), 'Invalid report fragment')
    return result


class ReportHTML(HTMLParser):
    allowed_tags=ALLOWED_TAGS
    global_attrs=GLOBAL_ATTRS
    tag_attrs=TAG_ATTRS
    aria_attrs=ARIA_ATTRS
    meta_names={'viewport','description','author','robots','color-scheme'}
    input_types={'checkbox'}
    def __init__(self, filename, paper_id='rpa-0062'):
        self.site_return = site_return(paper_id)
        super().__init__(convert_charrefs=True)
        self.filename = filename
        self.ids = set()
        self.links = []
        self.style = False
        self.style_text = []
        self.tags = set()

    def handle_decl(self, decl):
        require(decl.lower() == 'doctype html', 'Only the HTML5 doctype is permitted')

    def unknown_decl(self, data):
        raise ValueError('Unknown HTML declaration')

    def handle_pi(self, data):
        raise ValueError('HTML processing instructions are not permitted')

    def handle_starttag(self, tag, attrs):
        require(tag in self.allowed_tags, f'HTML tag is not permitted: {tag}')
        self.tags.add(tag)
        values = {}
        for key, value in attrs:
            require(key not in values, f'Duplicate HTML attribute: {key}')
            require(not key.startswith('on') and key in self.global_attrs | self.tag_attrs.get(tag, set()) | self.aria_attrs,
                    f'HTML attribute is not permitted: {tag}.{key}')
            require(value is None or not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', value),
                    'Control character in HTML attribute')
            values[key] = value
        if 'id' in values:
            ident = values['id']
            require(isinstance(ident, str) and ident and not re.search(r'[\s\x7f]', ident), 'Invalid HTML id')
            require(ident not in self.ids, 'Duplicate HTML id')
            self.ids.add(ident)
        if 'style' in values:
            require(isinstance(values['style'], str), 'CSS value required')
            _safe_css(values['style'])
        if tag == 'style':
            require(isinstance(values.get('type', 'text/css'), str) and
                    values.get('type', 'text/css').lower() == 'text/css', 'Only CSS style blocks are allowed')
            self.style = True
            self.style_text = []
        if tag == 'meta':
            if 'charset' in values:
                require(set(values) == {'charset'} and isinstance(values['charset'], str) and
                        values['charset'].lower() == 'utf-8', 'Only UTF-8 charset metadata is permitted')
            else:
                require(set(values) <= {'name', 'content'} and values.get('name') in
                        self.meta_names and
                        isinstance(values.get('content'), str), 'Unsupported report metadata')
        if tag == 'input':
            require(isinstance(values.get('type'), str) and values['type'].lower() in self.input_types,
                    'Only checkbox inputs are permitted')
        if tag == 'img':
            _image_source(values.get('src'))
        if tag == 'a':
            require(values.get('target', '_self') in ('_self', '_blank'), 'Unsupported link target')
            if 'href' in values:
                self._link(values['href'])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        require(tag in self.allowed_tags, f'HTML end tag is not permitted: {tag}')
        if tag == 'style':
            _safe_css(''.join(self.style_text))
            self.style = False
            self.style_text = []

    def handle_data(self, data):
        if self.style:
            self.style_text.append(data)

    def _link(self, value):
        require(isinstance(value, str) and value and not re.search(r'[\x00-\x20\x7f\\]', value),
                'Invalid HTML link characters')
        parsed = urlsplit(value)
        if parsed.scheme:
            _public_url(value)
            return
        require(not parsed.netloc and not parsed.query, 'Network-relative links and local queries are forbidden')
        if value == self.site_return:
            return
        require(parsed.path in ('', *STAGE_FILES.values()), 'Unapproved relative report link')
        require(parsed.path or parsed.fragment, 'Empty report link')
        fragment = _fragment(parsed.fragment) if parsed.fragment else None
        self.links.append((parsed.path or self.filename, fragment))


def _parse_html(record, payload, root=ROOT):
    try:
        text = payload.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Report must contain exact UTF-8 bytes') from exc
    require(not re.search(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', text), 'HTML contains control characters')
    if record['paper_id'] == 'rpa-0052' and record['stage'] == 'stage2':
        from report_roboduet_stage2 import prepare
        text,parser=prepare(root,record,payload)
    elif record['paper_id'] == 'rpa-0052':
        from report_roboduet import prepare
        text,parser=prepare(root,record,payload)
    elif record['paper_id'] == 'rpa-0012':
        from report_deep_wbc import prepare
        text,parser=prepare(root,record,payload)
    elif record['paper_id'] == 'rpa-0062' and record['version'] == 'v4':
        from report_umi_stage2 import prepare
        text,parser=prepare(root,record,payload)
    elif record['version']in {'v2','v3'}:
        from report_v2 import prepare
        text,parser=prepare(root,record,payload)
    else:parser = ReportHTML(record['filename'], record['paper_id'])
    try:
        parser.feed(text)
        parser.close()
    except (TypeError, AssertionError) as exc:
        raise ValueError('Malformed report HTML') from exc
    require(not parser.style, 'Unclosed CSS style block')
    require({'html', 'head', 'body'} <= parser.tags, 'A standalone HTML document is required')
    for target, fragment in parser.links:
        if target == record['filename'] and fragment:
            require(fragment in parser.ids, f'Unresolved report fragment: {fragment}')
    return parser


def _json_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, f'Duplicate JSON field: {key}')
        result[key] = value
    return result


def _load(root):
    root = _root(root)
    try:
        registry = json.loads(_read(root, 'data/reports.json', 2_000_000).decode('utf-8'),
                              object_pairs_hook=_json_object)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError('Report registry must be UTF-8 JSON') from exc
    _keys(registry, {'schema_version', 'reports'}, 'Report registry')
    require(type(registry['schema_version']) is int and registry['schema_version'] == 1,
            'Unsupported report schema')
    records = registry['reports']
    require(isinstance(records, list) and len(records) <= sum(len(stages) for p in REPORT_PAPERS.values() for stages in p['versions'].values()), 'Invalid report registry list')
    payloads = {}
    parsers = {}
    for record in records:
        _validate_record(record)
        filename = (record['paper_id'],record['version'],record['filename'])
        require(filename not in payloads, 'Duplicate paper/stage/version report')
        directory = _parts_path(record)
        chunks = []
        for part in record['parts']:
            raw = _read(root, directory + '/' + part['file'], CHUNK_BYTES)
            require(len(raw) == part['bytes'] and sha(raw) == part['sha256'],
                    'Report part byte count or SHA-256 mismatch')
            try:
                raw.decode('utf-8')
            except UnicodeDecodeError as exc:
                raise ValueError('Each report part must be independently valid UTF-8') from exc
            chunks.append(raw)
        payload = b''.join(chunks)
        require(len(payload) == record['bytes'] and sha(payload) == record['sha256'],
                'Assembled report byte count or SHA-256 mismatch')
        parsers[filename] = _parse_html(record, payload, root)
        payloads[filename] = payload
    for (paper_id, version, filename),parser in parsers.items():
        for target, fragment in parser.links:
            target=(paper_id,version,target)
            require(target in parsers, f'Report link is absent from the approved registry: {target}')
            require(not fragment or fragment in parsers[target].ids,
                    f'Unresolved sibling report fragment: {target}#{fragment}')
    return records, payloads


def load_reports(root=ROOT):
    """Read-only validation of registry, all chunks, HTML, and cross-report links.

    Returns only the public records, without cached bytes or private fields.
    An empty, otherwise valid registry is supported.
    """
    return _load(root)[0]


def assemble_reports(root=ROOT):
    """Validate every input first, then write only manifest-listed artifacts."""
    root = _root(root)
    records, payloads = _load(root)
    for record in records:
        target = _safe_path(root, report_path(record))
        require(not target.exists() or target.is_file(), 'Generated target must be a regular file')
    for record in records:
        _atomic_write(root, report_path(record), payloads[(record['paper_id'],record['version'],record['filename'])])
    return records


def split_report(root, record, raw_bytes):
    """Write exact UTF-8 parts and return updated metadata; never edit registry.

    Caller supplies all noncomputed metadata. sha256, bytes, and parts may be
    omitted or supplied; they are replaced by values calculated from raw_bytes.
    Sibling links are checked fully when the complete registry is loaded.
    """
    root = _root(root)
    require(isinstance(record, dict) and RECORD_FIELDS - COMPUTED_FIELDS <= set(record)
            and set(record) <= RECORD_FIELDS, 'Report metadata has unknown or missing fields')
    _identity(record)
    require(isinstance(raw_bytes, bytes) and 0 < len(raw_bytes) <= MAX_REPORT_BYTES,
            'Report input must be a nonempty bounded byte string')
    try:
        raw_bytes.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise ValueError('Report input must be UTF-8') from exc
    updated = dict(record, bytes=len(raw_bytes), sha256=sha(raw_bytes), parts=[])
    chunks = []
    start = 0
    while start < len(raw_bytes):
        end = min(start + CHUNK_BYTES, len(raw_bytes))
        # The complete input is valid; only a split continuation needs retreating.
        while end < len(raw_bytes) and raw_bytes[end] & 0xC0 == 0x80:
            end -= 1
        chunk = raw_bytes[start:end]
        name = f'part-{len(chunks) + 1:03d}.txt'
        chunks.append(chunk)
        updated['parts'].append({'file': name, 'bytes': len(chunk), 'sha256': sha(chunk)})
        start = end
    _validate_record(updated)
    _parse_html(updated, raw_bytes, root)
    directory = _parts_path(updated)
    for part in updated['parts']:
        target = _safe_path(root, directory + '/' + part['file'])
        require(not target.exists() or target.is_file(), 'Chunk target must be a regular file')
    for part, chunk in zip(updated['parts'], chunks):
        _atomic_write(root, directory + '/' + part['file'], chunk)
    return updated


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT, help='Repository root (defaults to script checkout)')
    parser.add_argument('--check', action='store_true', help='Validate without writing generated artifacts')
    args = parser.parse_args()
    records = load_reports(args.root) if args.check else assemble_reports(args.root)
    print(json.dumps({'reports': len(records), 'bytes': sum(record['bytes'] for record in records),
                      'mode': 'check' if args.check else 'assemble'}, sort_keys=True))


if __name__ == '__main__':
    main()
