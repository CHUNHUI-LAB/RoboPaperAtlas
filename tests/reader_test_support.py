"""Independent allowlist for live presentation around immutable reader reports."""
import hashlib
import re


def strip_live_presentation_scripts(testcase, page, root, source):
    # Keep this explicit rather than importing the renderer's asset list: a new
    # runtime must be reviewed here before it can pass source-preservation tests.
    assets = ['catalog-navigation.js', 'presentation.js']
    if 'data-report-script="interface.js"' not in source:
        assets.append('interface.js')
    assets += ['chrome.js', 'reader-toc-focus-v1.js', 'reader-current.js']
    stripped = page
    for name in assets:
        digest = hashlib.sha256((root / 'assets' / name).read_bytes()).hexdigest()[:12]
        script = f'<script src="../../../assets/{name}?v={digest}" defer></script>'
        testcase.assertEqual(page.count(script), 1, f'Expected exactly one versioned live runtime: {name}')
        stripped = stripped.replace(script, '', 1)
    # Hash the complete tags to keep failures bounded even for embedded readers.
    # Any additional script or any changed original inline byte fails this test.
    script_hashes = lambda text: [hashlib.sha256(block.encode()).hexdigest()
                                 for block in re.findall(r'<script\b.*?</script>', text, re.S)]
    testcase.assertEqual(script_hashes(stripped), script_hashes(source),
                         'Only the explicit live runtimes may differ from the fixed source scripts')
    return stripped
