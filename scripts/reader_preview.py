"""One complete shared-shell reader preview, rendered from approved Stage3 HTML.

Code is token-colored at build time, never executed. Source links and line ranges
remain pinned to the approved upstream commit; v1 artifacts are left intact.
"""
from pathlib import Path
import html,re,io,tokenize,token,keyword

SOURCE_FILE='artifacts/rpa-0062/v1/method-code-reading.html'
COMMIT='d75c9c182d8044dadf53043612da2ffbf1936a97'
KEY_NEEDLES={
 'code-pose_sequence-76':('episode_idx =','self.ee_pos[episode_idx','self.ee_rot_mat[episode_idx'),
 'code-task-845':('torch.linalg.inv','global_target_pose'),
 'code-task-874':('matrix_to_rotation_6d','torch.cat'),
 'code-realtime_traj-202':('searchsorted','alpha =','translation =','rotation ='),
 'code-wbc_node-967':('float(t) * 0.0','target_obs_index'),
 'code-task-716':('.sqrt()',),
 'code-task-768':('self.get_pos_err','self.get_orn_err','pos_reward * orn_reward'),
 'code-control-130':('assert normalized_action','self.kp','self.kd'),
 'code-wbc_node-1089':('forward_kinematics','affines.compose'),
}
def esc(value):return html.escape(str(value),quote=True)
def text(value):return html.unescape(re.sub('<[^>]+>','',value))
def colored_lines(source):
 lines=source.splitlines();spans=[[] for _ in lines]
 try:tokens=list(tokenize.generate_tokens(io.StringIO(source+'\n').readline))
 except (tokenize.TokenError,IndentationError):tokens=[]
 for i,tok in enumerate(tokens):
  kind=None
  if tok.type==token.NAME:
   if keyword.iskeyword(tok.string) or tok.string in {'True','False','None'}:kind='keyword'
   elif i+1<len(tokens) and tokens[i+1].string=='(':kind='call'
   else:kind='name'
  elif tok.type==token.STRING:kind='string'
  elif tok.type==token.NUMBER:kind='number'
  elif tok.type==token.COMMENT:kind='comment'
  elif tok.type==token.OP:kind='operator'
  if not kind:continue
  for row in range(tok.start[0],tok.end[0]+1):
   if row<1 or row>len(lines):continue
   start=tok.start[1] if row==tok.start[0] else 0;end=tok.end[1] if row==tok.end[0] else len(lines[row-1]);spans[row-1].append((start,end,kind))
 out=[]
 for line,marks in zip(lines,spans):
  result='';pos=0
  for start,end,kind in sorted(marks):
   if end<=pos:continue
   start=max(start,pos);result+=esc(line[pos:start])+f'<span class="tok-{kind}">'+esc(line[start:end])+'</span>';pos=end
  out.append(result+esc(line[pos:]))
 return out

def code_blocks(article):
 pattern=re.compile(r'<div id="(code-[^"]+)"><p class="source">(.*?)</p>\s*<pre><code>(.*?)</code></pre></div>',re.S)
 def render(match):
  ident,caption,encoded=match.groups();source=html.unescape(encoded)
  refs=re.findall(r'<a href="([^"]+)">([^<]*)</a>',caption);assert len(refs)==1
  url,label=refs[0];assert '/blob/'+COMMIT+'/' in url
  numbers=re.search(r'#L(\d+)-L(\d+)$',url);assert numbers
  first,last=map(int,numbers.groups());raw=source.splitlines();assert len(raw)==last-first+1,(ident,len(raw),first,last)
  description=text(caption.split(' · ')[0]).removeprefix('[代码] ').strip();filename=url.split('#')[0].rsplit('/',1)[-1]
  rows=[];needles=KEY_NEEDLES.get(ident,())
  for offset,(plain,colored)in enumerate(zip(raw,colored_lines(source))):
   line=first+offset;key=any(needle in plain for needle in needles)
   rows.append(f'<span class="code-line'+(' is-key' if key else '')+f'" id="{ident}-L{line}"><span class="code-number" aria-hidden="true">{line}</span><span class="code-text">{colored}</span></span>')
  return f'''<div class="code-reader" id="{ident}"><div class="code-toolbar"><div><span class="code-language">PYTHON</span><a href="{esc(url)}" target="_blank" rel="noopener noreferrer" title="{esc(label)} · commit {COMMIT}">{esc(filename)} · L{first}–{last} ↗</a></div><div class="code-actions"><button type="button" data-code-focus aria-pressed="false">关键行</button><button type="button" data-copy-code>复制</button></div></div><p class="code-intro"><strong>阅读此段</strong> · {esc(description)}</p><pre tabindex="0" aria-label="{esc(filename)} 第{first}至{last}行，代码可横向滚动"><code>{''.join(rows)}</code></pre><p class="code-foot"><span>原文件行号 · 静态摘录，未执行</span><a href="https://github.com/real-stanford/umi-on-legs/commit/{COMMIT}" target="_blank" rel="noopener noreferrer">commit {COMMIT[:10]} ↗</a></p></div>'''
 result,count=pattern.subn(render,article);assert count==9,count
 return result

def compact_citations(article):
 def shorten(m):
  url,label=m.groups();plain=text(label)
  if '/blob/'+COMMIT+'/' not in url:return m.group(0)
  name=url.split('#')[0].rsplit('/',1)[-1];lines=url.split('#')[1] if '#'in url else''
  return f'<a class="code-cite" href="{esc(url)}" title="{esc(plain)} · commit {COMMIT}">{esc(name)}'+(f' · {esc(lines.replace("-","–"))}' if lines else '')+' ↗</a>'
 # Existing file references become compact citations; their exact URLs remain unchanged.
 return re.sub(r'<a href="([^"]+)">([^<]*)</a>',shorten,article)

def render(root,shell,asset_url):
 root=Path(root);source=(root/SOURCE_FILE).read_text();article=re.search(r'<main class="article">(.*?)</main>',source,re.S).group(1)
 toc=re.search(r'<nav class="toc"[^>]*>(.*?)</nav>',source,re.S).group(1)
 title=re.search(r'<title>(.*?)</title>',source,re.S).group(1);subtitle=re.search(r'<p class="subtitle">(.*?)</p>',source,re.S).group(1)
 metadata=re.findall(r'<p class="meta">(.*?)</p>',source,re.S)
 article=compact_citations(code_blocks(article));article=re.sub(r'<section id="([^"]+)">',r'<section id="\1" tabindex="-1">',article);article=article.replace('<table','<div class="reader-table"><table').replace('</table>','</table></div>')
 toc=toc.replace('ON THIS PAGE','本页章节')
 stages=''.join(f'<a href="{href}"'+(' aria-current="page"'if stage==3 else'')+f'><small>0{stage}</small>{label}</a>'for stage,label,href in [(1,'初读','../../artifacts/rpa-0062/v1/first-pass.html'),(2,'写作精读','../../artifacts/rpa-0062/v1/writing-close-reading.html'),(3,'方法与代码','#main')])
 body=f'''<link rel="stylesheet" href="{asset_url('../../','reader-v2.css')}"><script src="{asset_url('../../','reader-v2.js')}" defer></script><main id="main" class="reader-page reader-stage3"><div class="reader-breadcrumb"><a href="../../index.html#catalog">Library</a><span> / </span><a href="../../papers/rpa-0062/index.html">UMI-on-Legs</a><span> / </span><span>Reader preview</span></div><header class="reader-title"><p class="reader-kicker">METHODS & CODE · STAGE 03</p><h1>UMI-on-Legs</h1><p class="subtitle">{subtitle}</p><div class="reader-meta"><p>{metadata[0]}</p><details><summary>阅读范围、来源版本与限制</summary><div class="reader-context">{metadata[1]}</div></details><p class="reader-context">新版阅读器设计预览：内容沿用已审核报告，代码仅做静态展示。Stage1与Stage2链接仍指向已发布v1；本页不会替换已发布报告。</p></div></header><div class="reader-stagebar"><nav class="reader-stages" aria-label="阅读阶段">{stages}</nav><div class="reader-controls"><a class="reader-control" href="../../artifacts/rpa-0062/v1/method-code-reading.html">已发布 v1 ↗</a><button type="button" class="reader-control reader-toc-toggle" aria-expanded="false" aria-controls="reader-toc">本页目录</button></div></div><div class="reader-grid"><nav class="reader-toc" id="reader-toc" aria-label="本页目录">{toc}</nav><article class="reader-article">{article}</article></div></main><p class="reader-footer">RoboPaperAtlas · 独立中文阅读分析，不代表作者背书 · 保留正式论文来源与固定源码版本</p><div class="reader-toast" role="status" aria-live="polite" hidden></div>'''
 return shell('RoboPaperAtlas',body,prefix='../../',page='reader-preview')
