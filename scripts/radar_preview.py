"""An isolated 1.1 overview pilot. The current brief archive remains untouched."""
import json,hashlib,shutil
from pathlib import Path
from briefs import validate_brief,load_archive
from radar_overview import validate_snapshot,render
DATE='2026-09-30'
def load(root):
 root=Path(root);folder=root/'data/radar-preview';path=folder/(DATE+'.json')
 if folder.is_symlink() or path.is_symlink() or not path.is_file():raise ValueError('Unsafe Radar preview input')
 if {p.name for p in folder.iterdir()}!={DATE+'.json'}:raise ValueError('Unlisted Radar preview input')
 data=validate_brief(json.loads(path.read_text()));raw=(root/'data/frontier.json').read_bytes();current_hash=hashlib.sha256(raw).hexdigest()
 if data['source_snapshot']['sha256']==current_hash:validate_snapshot(data,json.loads(raw),current_hash)
 return data
def build_preview(root,output,shell):
 root=Path(root);output=Path(output);data=load(root);index,_=load_archive(root)
 page=output/'radar-preview';page.mkdir()
 body='<main id="main" class="radar-overview-main">'+render(data,index,prefix='../',preview=True)+'</main>'
 (page/'index.html').write_text(shell('Radar 设计预览',body,prefix='../',page='frontier'))
 dest=output/'data/radar-preview';dest.mkdir();shutil.copyfile(root/'data/radar-preview'/(DATE+'.json'),dest/(DATE+'.json'))
