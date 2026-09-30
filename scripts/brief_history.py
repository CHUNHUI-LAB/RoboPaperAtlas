"""Preserve the already published initial1.0 snapshot without changing task paths."""
import hashlib,json,shutil,re
from pathlib import Path
from briefs import validate_brief,section
RELATIVE='data/brief-history/2026-09-30-v1.0.json'
DIGEST='f4051befc11c31856ac8d397f8efe39fb9a0a8f1927ba5710dd98f3f78ae9fc7'
def load(root):
 root=Path(root);path=root/RELATIVE
 if any(p.is_symlink() for p in [path,path.parent]):raise ValueError('Unsafe historical brief')
 raw=path.read_bytes()
 if hashlib.sha256(raw).hexdigest()!=DIGEST:raise ValueError('Historical brief bytes changed')
 data=validate_brief(json.loads(raw))
 if data['schema_version']!='1.0' or data['date']!='2026-09-30':raise ValueError('Unexpected historical brief identity')
 return data

def build(root,output,shell,index):
 root=Path(root);output=Path(output);data=load(root);folder=output/'frontier/briefs/2026-09-30/v1';folder.mkdir(parents=True)
 content=section(data,index,prefix='../../../../',archive=False)
 content=re.sub(r'<p class="brief-automation">.*?</p>','<p class="brief-automation">此为最初发布的历史摘要快照，不代表当前版本。<a href="../index.html">查看本日研究概览 ↗</a> · <a href="../../../../data/brief-history/2026-09-30-v1.0.json">查看原始1.0数据 ↗</a></p>',content)
 content=content.replace('独立阅读本期 ↗','查看本日研究概览 ↗')
 body='<main id="main" class="brief-archive-page"><p class="brief-state">历史快照 · 最初发布的五篇摘要。<a href="../index.html">查看本日研究概览 ↗</a></p>'+content+'</main>'
 (folder/'index.html').write_text(shell(data['title'],body,prefix='../../../../',page='frontier'))
 target=output/RELATIVE;target.parent.mkdir(parents=True);shutil.copyfile(root/RELATIVE,target)
