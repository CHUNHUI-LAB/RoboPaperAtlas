#!/usr/bin/env python3
"""Build the unchanged public site, then append the allowlisted previews.

The normal scripts/build.py output stays unchanged. CI opts into this wrapper.
"""
import argparse
import hashlib
import os
import stat
from pathlib import Path
import subprocess
import sys

from build_topic_preview import ROOT, require, safe_path, safe_target, validate_source, write_preview
from radar_c2_preview import validate_preview as validate_c2_preview, write_preview as write_c2_preview


SUBMIT_ROUTE = 'submit-preview'
SUBMIT_FILES = ('index.html', 'style.css', 'app.js', 'data/venues.json')
SUBMIT_ENTRIES = set(SUBMIT_FILES) | {'data'}


def validate_submit_tree(root, folder):
    """Accept exactly four regular files and their one data directory."""
    folder = safe_path(root, folder)
    require(folder.is_dir(), 'Submission preview must be a directory')
    entries = list(folder.rglob('*'))
    require({p.relative_to(folder).as_posix() for p in entries} == SUBMIT_ENTRIES,
            'Submission preview must contain exactly the public allowlist')
    for path in entries:
        safe_path(root, path)
        if path.relative_to(folder).as_posix() == 'data':
            require(path.is_dir(), 'Submission data must be a directory')
        else:
            require(stat.S_ISREG(path.stat().st_mode), 'Submission files must be regular files')
    return folder


def validate_submit_source(root, target):
    root = Path(root).absolute()
    target = safe_target(root, target)
    source = validate_submit_tree(root, root / SUBMIT_ROUTE)
    require(target != source and source not in target.parents and target not in source.parents,
            'Build output must not overlap submission source')
    destination = safe_path(root, target / SUBMIT_ROUTE)
    if destination.exists():
        validate_submit_tree(root, destination)
    return source


def write_submit_preview(root, target):
    """Copy allowlisted bytes and version the entry page's script/data pair."""
    root = Path(root).absolute()
    source = validate_submit_source(root, target)
    payloads = {}
    for name in SUBMIT_FILES:
        src = safe_path(root, source / name)
        with os.fdopen(os.open(src, os.O_RDONLY | os.O_NOFOLLOW), 'rb') as inp:
            require(stat.S_ISREG(os.fstat(inp.fileno()).st_mode), 'Source must remain regular')
            payloads[name] = inp.read()
    versions = {key: hashlib.sha256(payloads[name]).hexdigest()[:12]
                for key, name in (('script', 'app.js'), ('data', 'data/venues.json'))}
    html = payloads['index.html'].decode('utf8')
    require(html.count('src="app.js"') == 1, 'Submission entry script must occur exactly once')
    payloads['index.html'] = html.replace('src="app.js"',
        f'src="app.js?v={versions["script"]}&amp;data={versions["data"]}"').encode('utf8')
    destination = safe_path(root, Path(target) / SUBMIT_ROUTE)
    destination.mkdir(parents=True, exist_ok=True)
    safe_path(root, destination / 'data').mkdir(exist_ok=True)
    for name in SUBMIT_FILES:
        dst = safe_path(root, destination / name)
        with os.fdopen(os.open(dst, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o644), 'wb') as out:
            require(stat.S_ISREG(os.fstat(out.fileno()).st_mode), 'Output must remain regular')
            out.write(payloads[name])
    return versions


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='dist')
    args = parser.parse_args(argv)
    target = safe_target(ROOT, ROOT / args.output)
    validate_source(ROOT)
    validate_submit_source(ROOT, target)
    validate_c2_preview(ROOT, target)
    from objectnav_reading_preview import validate_preview as validate_objectnav_preview, write_preview as write_objectnav_preview
    validate_objectnav_preview(ROOT, target)
    from navigation_product import validate_preview as validate_navigation_product
    validate_navigation_product(ROOT, target)
    subprocess.run(
        [sys.executable, str(ROOT / 'scripts/build.py'), '--output', args.output],
        check=True,
    )
    write_preview(ROOT, target)
    write_submit_preview(ROOT, target)
    write_c2_preview(ROOT, target)
    write_objectnav_preview(ROOT, target)


if __name__ == '__main__':
    main()
