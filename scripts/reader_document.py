"""Format approved UMI report content with the accepted reader design.

This module contains presentation and local packaging only, no reading prompts.
It preserves the supplied article and provides a self-contained HTML document.
"""
from pathlib import Path
import base64,hashlib,html,json,re
from reader_preview import code_blocks,compact_citations,text,esc
from reader_math import apply_math
SITE='https://chunhui-lab.github.io/RoboPaperAtlas/'
FILES={1:'first-pass.html',2:'writing-close-reading.html',3:'method-code-reading.html'}
LABELS={1:'初读',2:'写作精读',3:'方法与代码'}
STAGE3_TOC={'overview':'总体框架','mapping':'图与代码','visual-policy':'视觉策略','trajectory-data':'示范轨迹','frames':'坐标变换','preview':'轨迹预览','reward':'奖励与课程','actor-control':'观测与动作','deployment':'部署与状态估计','chains':'训练与推理','conditions':'条件与限制','summary':'理解小结'}

def source_panel(units):
 payload=json.dumps(units,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
 return '''<aside class="reader-source-panel" aria-labelledby="source-panel-title"><div class="source-panel-top"><strong id="source-panel-title">原文定位</strong><span>正式 PDF · 17 页</span></div><div class="source-panel-body"><p class="source-unit-id" data-source-id></p><p class="source-location" data-source-location></p><blockquote class="source-quote" data-source-quote hidden></blockquote><p class="source-paraphrase" data-source-paraphrase></p><a class="source-open" data-source-open href="https://proceedings.mlr.press/v270/ha25a.html" target="_blank" rel="noopener noreferrer">打开正式原文 ↗</a><p class="source-caveat">原句完整上下文请对照正式 PDF。只按页、段落与分析单位定位，不提供句级自动高亮。原文链接需要联网；浏览器可能下载 PDF，请按标注页码打开。</p><div class="source-stepper"><button type="button" data-source-previous>← 上一个单位</button><button type="button" data-source-next>下一个单位 →</button></div></div></aside><script type="application/json" data-source-units id="reader-source-units">'''+payload+'</script>'

def align_tables(article,units):
 byid={u['id']:u for u in units};seen=set()
 def table(m):
  raw=m[0];heads=[text(x)for x in re.findall(r'<th[^>]*>(.*?)</th>',raw,re.S)]
  def row(match):
   body=match[1];ids=set(re.findall(r'id="([^"]+)"',body))&set(byid)
   if not ids:return match[0]
   if len(ids)!=1:raise ValueError('Ambiguous source analysis row')
   ident=next(iter(ids));seen.add(ident);unit=byid[ident];n=0
   def cell(c):
    nonlocal n
    content=c[1];label=heads[n]if n<len(heads)else'';n+=1
    if n==1:content+=f'<div class="source-row-actions"><button type="button" class="source-row-button" data-source-unit="{esc(ident)}" aria-pressed="false">对照原文位置 · {esc(ident)}</button><a class="reader-source-mobile" href="{esc(unit["url"])}" target="_blank" rel="noopener noreferrer">正式 PDF · 第{unit["page"]}页 ↗</a></div>'
    return '<td data-label="'+esc(label)+'">'+content+'</td>'
   body=re.sub(r'<td>(.*?)</td>',cell,body,flags=re.S)
   return '<tr class="source-row" data-source-row="'+esc(ident)+'">'+body+'</tr>'
  raw=re.sub(r'<tr>(.*?)</tr>',row,raw,flags=re.S)
  return '<div class="reader-table'+(' reader-unit-table'if 'data-source-row='in raw else'')+'">'+raw+'</div>'
 article=re.sub(r'<table>.*?</table>',table,article,flags=re.S)
 if seen!=set(byid):raise ValueError('All37 source rows must be aligned exactly')
 return article

def render(root,stage,source,units,site_shell,asset_url):
 root=Path(root)
 if stage not in FILES:raise ValueError('Unknown stage')
 if stage==3:source=apply_math(source,root)
 article=re.search(r'<main class="article">(.*?)</main>',source,re.S).group(1)
 toc=re.search(r'<nav class="toc"[^>]*>(.*?)</nav>',source,re.S).group(1).replace('ON THIS PAGE','本页章节')
 subtitle=re.search(r'<p class="subtitle">(.*?)</p>',source,re.S).group(1)
 metadata=re.findall(r'<p class="meta">(.*?)</p>',source,re.S)
 if stage==3:
  article=compact_citations(code_blocks(article))
  toc=re.sub(r'<a href="#([^"]+)">(.*?)</a>',lambda m:f'<a href="#{m[1]}" title="{esc(text(m[2]))}">{esc(STAGE3_TOC.get(m[1],text(m[2])))}</a>',toc)
 article=re.sub(r'<section id="([^"]+)">',r'<section id="\1" tabindex="-1">',article)
 if stage==2:article=align_tables(article,units)
 else:article=article.replace('<table','<div class="reader-table"><table').replace('</table>','</table></div>')
 count=len(re.findall(r'<section id=',article))
 stages=''.join(f'<a href="{FILES[k]if k!=stage else"#main"}"'+(' aria-current="page"'if k==stage else'')+f'><small>0{k}</small>{LABELS[k]}</a>'for k in FILES)
 toggler='<button type="button" class="reader-control" data-source-toggle aria-pressed="true">原文定位</button>'if stage==2 else''
 panel=source_panel(units)if stage==2 else''
 styles=(f'<link rel="stylesheet" href="{asset_url(SITE,"vendor/katex/katex.min.css")}">'if stage==3 else'')+f'<link rel="stylesheet" href="{asset_url(SITE,"reader-v2.css")}"><link rel="stylesheet" href="{asset_url(SITE,"reader-document.css")}">'
 body=f'''{styles}<script src="{asset_url(SITE,'reader-v2.js')}" defer></script><main id="main" class="reader-page reader-stage{stage}"><div class="reader-stagebar"><a class="reader-paper-link" href="{SITE}papers/rpa-0062/index.html">UMI-on-Legs <span> / Reading</span></a><nav class="reader-stages" aria-label="阅读阶段">{stages}</nav><div class="reader-controls">{toggler}<nav class="reader-section-stepper" aria-label="章节导航"><button type="button" data-reader-previous aria-label="上一节" title="上一节" disabled>←</button><span class="reader-position" aria-label="当前章节位置">01 / {count:02d}</span><span class="sr-only" data-reader-section-label></span><button type="button" data-reader-next aria-label="下一节" title="下一节">→</button></nav><button type="button" class="reader-control reader-toc-toggle" aria-expanded="false" aria-controls="reader-toc">本页目录</button></div></div><div class="reader-grid"><nav class="reader-toc" id="reader-toc" aria-label="本页目录">{toc}</nav><div class="reader-body"><header class="reader-title"><div class="reader-breadcrumb"><a href="{SITE}index.html#catalog">Library</a><span> / </span><span>Stage {stage} · {LABELS[stage]} · v2</span></div><h1>UMI-on-Legs</h1><p class="subtitle">{subtitle}</p><div class="reader-meta"><p class="reader-byline">Huy Ha · Yihuai Gao · Zipeng Fu · Jie Tan · Shuran Song</p><details><summary>CoRL 2024 / PMLR 2025 · 原文、来源与阅读范围</summary><div class="reader-context"><p>{metadata[0]}</p><p>{metadata[1]}</p><a href="{SITE}artifacts/rpa-0062/v1/{FILES[stage]}">历史报告 v1 ↗</a></div></details><p class="reader-document-note">报告版本 v2 · 正文、图表和公式可离线阅读；原文、源码与站内搜索需联网。</p></div></header><article class="reader-article">{article}</article></div>{panel}</div></main><p class="reader-footer">RoboPaperAtlas · 独立中文阅读分析，不代表作者背书 · 保留正式论文来源与固定源码版本</p><div class="reader-toast" role="status" aria-live="polite" hidden></div>'''
 return site_shell('RoboPaperAtlas',body,prefix=SITE,page='reader')

def self_contained(document,root,stage):
 root=Path(root);policies={'styles':{},'scripts':{}};scripts=[]
 document=re.sub(r'data-data-version="[^"]+"','data-data-version="reader-v2"',document)
 def asset_path(url):
  if not url.startswith(SITE+'assets/'):raise ValueError('Unexpected reader asset')
  path=(root/url.split('?',1)[0][len(SITE):]).resolve()
  if root.resolve()not in path.parents or not path.is_file():raise ValueError('Asset escapes source tree')
  return path
 def css_inline(css,path):
  def resource(m):
   value=m[1].strip().strip('\"\\\'')
   if value.startswith('data:'):return m[0]
   target=(path.parent/value).resolve()
   if root.resolve()not in target.parents or target.suffix not in {'.svg','.woff2'}:raise ValueError('Unexpected CSS asset')
   mime='font/woff2'if target.suffix=='.woff2'else'image/svg+xml'
   return 'url(data:'+mime+';base64,'+base64.b64encode(target.read_bytes()).decode()+')'
  return re.sub(r'url\(([^)]+)\)',resource,css)
 def style(m):
  path=asset_path(m[1]);name=str(path.relative_to(root/'assets'));css=css_inline(path.read_text(),path);policies['styles'][name]=hashlib.sha256(css.encode()).hexdigest()
  return '<style data-report-style="'+name+'">'+css+'</style>'
 document=re.sub(r'<link rel="stylesheet" href="([^"]+)">',style,document)
 document=re.sub(r'<link rel="icon"[^>]+>','',document)
 def script(m):
  path=asset_path(m[1]);name=str(path.relative_to(root/'assets'));code=path.read_text()
  if '</script' in code.lower():raise ValueError('Unsafe embedded script delimiter')
  policies['scripts'][name]=hashlib.sha256(code.encode()).hexdigest();scripts.append('<script data-report-script="'+name+'">'+code+'</script>');return''
 document=re.sub(r'<script src="([^"]+)" defer></script>',script,document)
 if stage==3:
  notices='\n\n'.join((root/p).read_text()for p in ['assets/vendor/katex/LICENSE.txt','docs/katex-font-notices.txt','docs/katex-font-license.txt'])
  legal='<details class="reader-licenses"><summary>公式软件与字体许可</summary><pre>'+html.escape(notices)+'</pre></details>'
  document=document.replace('<div class="reader-toast"',legal+'<div class="reader-toast"',1)
 document=document.replace('</body>',''.join(scripts)+'</body>')
 return document,policies
