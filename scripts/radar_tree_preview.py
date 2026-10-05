"""Publish only the frozen, reviewed C candidate at an isolated review route.

No literature/data inference happens during normal site builds. Updating this
snapshot requires rerunning the separate evidence pipeline and reviewing hashes.
"""
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from build_topic_preview import require, safe_path, safe_target

ROUTE = 'review/radar-trees-c'
SOURCE = 'previews/radar-trees-c'
FILES = frozenset(('index.html', 'literature.html', 'challenge.html',
    'weekly-2026-10-04.html', 'reading-overview.html', 'graph.css', 'graph.js',
    'data/graph-data.js', 'data/graph-data.json'))
MANIFEST = 'scripts/radar_tree_preview_manifest.json'


def payloads(root):
    root = Path(root).absolute()
    source = safe_path(root, root / SOURCE)
    require(source.is_dir(), 'Missing Radar C preview source')
    entries = list(source.rglob('*'))
    require({p.relative_to(source).as_posix() for p in entries} == FILES | {'data'},
            'Radar C source must exactly match the nine-file public allowlist')
    for p in entries:
        safe_path(root, p)
        require(p.is_dir() if p == source / 'data' else stat.S_ISREG(p.stat().st_mode),
                'Radar C source must contain regular files and its data directory')
    manifest_path = safe_path(root, root / MANIFEST)
    manifest = json.loads(manifest_path.read_text())
    require(set(manifest['files']) == FILES, 'Invalid Radar C manifest allowlist')
    require(manifest['status'] == 'local_candidate_pending_real_browser_acceptance',
            'Preview acceptance must not be silently promoted')
    result = {}
    for name in sorted(FILES):
        p = safe_path(root, source / name)
        with os.fdopen(os.open(p, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as f:
            require(stat.S_ISREG(os.fstat(f.fileno()).st_mode), 'Source must remain regular')
            result[name] = f.read()
        require(hashlib.sha256(result[name]).hexdigest() == manifest['files'][name],
                'Radar C reviewed source hash mismatch: ' + name)
    return result


def validate_preview(root, target):
    root = Path(root).absolute()
    target = safe_target(root, target)
    source = safe_path(root, root / SOURCE)
    require(target != source and target not in source.parents and source not in target.parents,
            'Output must not overlap Radar C source')
    data = payloads(root)
    return root, target, data


def write_preview(root, target):
    root, target, data = validate_preview(root, target)
    dest = safe_path(root, target / ROUTE)
    if dest.exists():
        require(dest.is_dir(), 'Radar C output must be a directory')
        require({p.relative_to(dest).as_posix() for p in dest.rglob('*')} == FILES | {'data'},
                'Unexpected file in Radar C output')
        for item in dest.rglob('*'):
            safe_path(root, item)
            require(item.is_dir() if item == dest / 'data' else stat.S_ISREG(item.stat().st_mode),
                    'Radar C output must contain only regular files')
    dest.mkdir(parents=True, exist_ok=True)
    safe_path(root, dest / 'data').mkdir(exist_ok=True)
    for name, content in data.items():
        p = safe_path(root, dest / name)
        # Atomic replacement does not truncate hard-linked inodes or open FIFOs.
        fd, temporary = tempfile.mkstemp(prefix='.radar-c-', dir=p.parent)
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(content)
            os.replace(temporary, p)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    return sorted(data)
