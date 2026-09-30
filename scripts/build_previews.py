#!/usr/bin/env python3
"""Build the unchanged public site, then append the opt-in topic preview.

The normal scripts/build.py output stays unchanged. CI opts into this wrapper.
"""
import argparse
import subprocess
import sys

from build_topic_preview import ROOT, safe_target, validate_source, write_preview


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', default='dist')
    args = parser.parse_args(argv)
    target = safe_target(ROOT, ROOT / args.output)
    validate_source(ROOT)
    subprocess.run(
        [sys.executable, str(ROOT / 'scripts/build.py'), '--output', args.output],
        check=True,
    )
    write_preview(ROOT, target)


if __name__ == '__main__':
    main()
