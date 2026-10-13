"""Shared, progressively enhanced navigation for the live Atlas surfaces."""
from html import escape

REPOSITORY = 'https://github.com/CHUNHUI-LAB/RoboPaperAtlas'


def render_header(prefix='', page='catalog', compact=False):
    def item(path, label, active=False):
        current = ' aria-current="page"' if active else ''
        return f'<a href="{escape(prefix + path, quote=True)}"{current}>{label}</a>'

    compact_class = ' site-header--compact' if compact else ''
    group_class = ' is-current' if page in ('map', 'navigation') else ''
    return f'''<header class="site-header{compact_class}"><div class="header-inner">
<a class="brand" href="{prefix}index.html" aria-label="RoboPaperAtlas 首页"><svg class="brand-symbol" width="26" height="26" viewBox="0 0 26 26" aria-hidden="true"><path d="M4 19 11 5l11 12-18 2Z" fill="none" stroke="currentColor" stroke-width="1.2"/><circle cx="11" cy="5" r="2.5" fill="currentColor"/><circle cx="4" cy="19" r="2.5" fill="currentColor"/><circle cx="22" cy="17" r="2.5" fill="currentColor"/></svg><span>RoboPaper<span class="brand-light">Atlas</span></span></a>
<nav id="main-nav" aria-label="主导航">
{item('index.html#catalog', '论文库', page == 'catalog')}
<details class="nav-group{group_class}"><summary>研究地图 <span aria-hidden="true">⌄</span></summary><div class="nav-dropdown">{item('map/index.html', '研究星图', page == 'map')}{item('research/navigation/index.html', '导航研究地图', page == 'navigation')}</div></details>
{item('frontier/index.html', '前沿动态', page == 'frontier')}{item('reading/index.html', '阅读档案', page == 'reading')}
<details class="nav-group nav-more"><summary>更多 <span aria-hidden="true">⌄</span></summary><div class="nav-dropdown">{item('submit/index.html', '投稿指南', page == 'submit')}{item('about/index.html', '关于与贡献', page == 'about')}<a href="{REPOSITORY}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></details>
</nav><div class="header-actions"><button type="button" class="global-search-trigger" aria-label="搜索论文（Control 或 Command K）" aria-haspopup="dialog"><svg width="18" height="18" viewBox="0 0 20 20" fill="none" aria-hidden="true"><circle cx="8.5" cy="8.5" r="5.75" stroke="currentColor" stroke-width="1.5"/><path d="m13 13 4 4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg><span class="search-trigger-label">搜索</span><kbd>⌘ K</kbd></button><button type="button" class="mobile-menu" aria-expanded="false" aria-controls="main-nav">菜单 <span aria-hidden="true">☰</span></button></div></div></header>'''


def render_footer(prefix=''):
    return f'''<footer class="site-footer"><div><a class="footer-brand" href="{prefix}index.html">RoboPaperAtlas<span>机器人研究的开放地图</span></a><p>从原始论文出发，让每一次理解都有据可查。</p><div class="library-footer-links"><a href="{prefix}reading/index.html">阅读档案</a><a href="{prefix}submit/index.html">投稿指南</a><a href="{prefix}about/index.html">关于与贡献</a><a href="{REPOSITORY}" target="_blank" rel="noopener noreferrer">GitHub ↗</a></div></div><div class="footer-right"><span>编目核验 ≠ 阅读完成 ≠ 独立复现</span><span>© 2026 · 第三方论文与代码遵循各自许可</span></div></footer>'''


def render_dialogs(prefix=''):
    return f'''<dialog id="search-dialog" aria-labelledby="search-title"><div class="dialog-heading"><div><p class="eyebrow">EXPLORE THE LIBRARY</p><h2 id="search-title">寻找下一篇论文</h2></div><button class="dialog-close" type="button" aria-label="关闭搜索">✕</button></div><form id="global-search-form" role="search"><label class="global-input-label"><span class="sr-only">论文标题、作者或关键词</span><input id="global-search-input" type="search" placeholder="标题、作者或关键词…" autocomplete="off" maxlength="512"></label></form><p class="global-search-scope">检索公开书目与编目备注，不检索阅读报告正文</p><p id="global-search-status" role="status" aria-live="polite">输入关键词开始搜索</p><button type="button" id="global-search-retry" class="secondary-button" hidden>重新载入目录</button><ul id="global-search-results"></ul><div class="dialog-footer"><span>↑ ↓ 选择 · Enter 打开 · Esc 关闭</span><a id="global-all-results" href="{prefix}index.html#catalog">进入完整目录 ↗</a></div></dialog><dialog class="paper-drawer" id="paper-drawer" aria-labelledby="drawer-title"><div class="drawer-top"><span>论文速览</span><button type="button" class="drawer-close" aria-label="关闭论文速览">✕</button></div><div id="drawer-body"><h2 id="drawer-title">正在载入</h2></div><div id="drawer-footer" class="drawer-actions" hidden></div></dialog><div class="toast" role="status" aria-live="polite" hidden></div>'''
