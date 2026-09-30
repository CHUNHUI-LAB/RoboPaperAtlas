"""Exact, section-hash-bound substitutions for an approved reader only."""
import json,hashlib,html,re
from pathlib import Path

def apply_math(source,root):
 root=Path(root);raw=(root/'data/reader-math.json').read_bytes();mapping=json.loads(raw);rendered=json.loads((root/'data/reader-math-rendered.json').read_text())
 if rendered['input_sha256']!=hashlib.sha256(raw).hexdigest() or rendered['katex_version']!='0.18.9':raise ValueError('Run npm run prepare:math to refresh pinned math output')
 by_section={}
 for e in mapping['entries']:
  if hashlib.sha256(e['original_html'].encode()).hexdigest()!=e['original_html_sha256']:raise ValueError('Math original hash mismatch')
  by_section.setdefault(e['section_id'],[]).append(e)
 labels={'eq-relative':'坐标变换 · 阅读解释','eq-paper':'论文指数表达式 · 左侧 r_pose 为本文记号','eq-code':'代码等价式 · 默认配置权重 4'}
 def section(m):
  sid,content=m.groups()
  if sid not in by_section:return m[0]
  if hashlib.sha256(content.encode()).hexdigest()!=mapping['section_sha256'][sid]:raise ValueError('Math section changed: '+sid)
  replacements=[]
  for e in by_section[sid]:
   output=rendered['rendered'][e['id']]
   if e['display_mode']:
    replacement='<span class="math-label">'+html.escape(labels[e['id']])+'</span>'+output+'<details class="math-source"><summary>查看 LaTeX 源码</summary><pre>'+html.escape(e['latex'])+'</pre></details>'
   else:replacement='<span class="math-inline" data-math-id="'+e['id']+'">'+output+'</span>'
   for o in e['occurrences']:
    if content[o['start']:o['end']]!=e['original_html']:raise ValueError('Exact math span mismatch: '+e['id'])
    replacements.append((o['start'],o['end'],replacement))
  last=len(content)
  for start,end,replacement in sorted(replacements,reverse=True):
   if end>last:raise ValueError('Overlapping math spans')
   content=content[:start]+replacement+content[end:];last=start
  return '<section id="'+sid+'">'+content+'</section>'
 source=re.sub(r'<section id="([^"]+)">(.*?)</section>',section,source,flags=re.S)
 source=source.replace('class="formula"','class="reader-equation"')
 update=mapping['renderer_description']
 if source.count(update['original_html'])!=1:raise ValueError('Renderer description changed')
 return source.replace(update['original_html'],html.escape(update['replacement_html']))
