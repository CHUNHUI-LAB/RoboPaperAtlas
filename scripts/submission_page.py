"""Integrate the public submission module without promoting other design previews.

The reviewed four-file source remains the single source of data and behavior.
Only its page furniture and CSS scope are adapted for the common site shell.
"""
import re
from pathlib import Path


def scoped_styles(css):
    """Scope the module's deliberately simple CSS, including media-query rules.

    Fail closed if the source introduces unsupported at-rules. This is not a
    general CSS parser; the accepted source uses ordinary rules and @media only.
    """
    if re.search(r'@(?!media\b)[\w-]+', css):
        raise ValueError('Submission CSS supports @media only')

    def qualify(match):
        selectors = match.group(1).strip()
        if selectors.startswith('@media'):
            return selectors + '{'
        scoped = []
        for selector in selectors.split(','):
            selector = selector.strip()
            if selector in (':root', 'body', 'main'):
                scoped.append('.submission-module')
            else:
                scoped.append('.submission-module ' + selector)
        return ','.join(scoped) + '{'

    return re.sub(r'([^{}]+)\{', qualify, css)


def write_submission(root, target, shell):
    from build_previews import write_submit_preview
    root, target = Path(root), Path(target)
    # This retains the strict four-file allowlist and symlink checks unchanged.
    versions = write_submit_preview(root, target)
    source = root / 'submit-preview'
    import json
    from submission_profiles import validate_submission_profiles, validate_experience_overview
    data = json.loads((source / 'data/venues.json').read_text(encoding='utf8'))
    validate_submission_profiles(data)
    validate_experience_overview(data)
    html = (source / 'index.html').read_text(encoding='utf8')
    main = re.search(r'<main>(.*?)</main>', html, re.S)
    nav = re.search(r'<nav class="submission-tabs" aria-label="模块">(.*?)</nav>', html, re.S)
    footer = re.search(r'<footer>(.*?)</footer>', html, re.S)
    if not all((main, nav, footer)):
        raise ValueError('Submission source page structure changed; review integration')
    body = ('<main id="main" class="submission-module">'
            + main.group(1).replace('aria-label="模块"', 'aria-label="投稿模块"')
            + '<footer>' + footer.group(1) + '</footer></main>')
    page = shell('投稿与期刊', body, prefix='../', page='submit',
                 description='机器人研究投稿渠道、期刊政策与公开来源。')
    page = page.replace('<title>RoboPaperAtlas</title>',
                        '<title>投稿与期刊 · RoboPaperAtlas</title>')
    css = scoped_styles((source / 'style.css').read_text(encoding='utf8'))
    css += '\n.submission-module{--shell-height:70px}'
    css += '\n.submission-module{width:100%;font-family:inherit}'
    import hashlib
    version = hashlib.sha256(css.encode()).hexdigest()[:12]
    page = page.replace('</head>', f'<link rel="stylesheet" href="style.css?v={version}"></head>')
    page = page.replace('</body>', f'<script src="../submit-preview/app.js?v={versions["script"]}&amp;data={versions["data"]}"></script></body>')
    folder = target / 'submit'
    folder.mkdir(exist_ok=True)
    (folder / 'index.html').write_text(page, encoding='utf8')
    (folder / 'style.css').write_text(css, encoding='utf8')
