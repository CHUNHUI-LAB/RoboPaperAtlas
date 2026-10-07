"""Deterministically expose corrected protocol cards in the script-free alternative.
Original task blocks remain verbatim under labelled historical disclosures.
"""
from pathlib import Path
import argparse, html, json, re
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'previews/radar-c2-analysis'
esc=lambda x:html.escape(str(x),quote=True)
FIELDS=[('目标如何给定','goal_spec'),('目标发放与顺序','goal_delivery'),('怎样移动','action_regime'),('是否预先有地图','environment_prior'),('记忆何时重置','memory_regime'),('怎样判成功','success_contract'),('评测范围','evaluation_scope'),('oracle 转场','oracle_phase'),('tour 排序','tour_ordering'),('适用范围','scope_note'),('边界','boundary')]
def payload():
 s=(SOURCE/'data/literature.js').read_text();return json.loads(s[s.index('{'):].strip().removesuffix(';'))
def fields(n):return '<dl>'+''.join('<dt>'+esc(label)+'</dt><dd>'+esc(n[key])+'</dd>' for label,key in FIELDS if n.get(key))+'</dl>'
def render(text,data):
 old=json.loads((ROOT/'tests/fixtures/radar-c2-analysis/data/literature-seed.json').read_text());before={n['node_id']:n for n in old['nodes']}
 for n in data['nodes']:
  if not n.get('protocol_variants'):continue
  ident=n['node_id'];start='<!-- task-map-'+ident+':start -->';end='<!-- task-map-'+ident+':end -->'
  marker=re.search(re.escape(start)+r'(.*?)'+re.escape(end),text,re.S)
  if marker:
   match=re.search(r'<details class="historical-task-contract"><summary>历史记录：已被本轮定点纠错替代，不作为当前协议</summary>(.*?)</details>\s*$',marker[1],re.S)
   if not match:raise ValueError('Missing original historical task block '+ident)
   original=match[1];target=marker[0]
  else:
   match=re.search(r'<details><summary>'+re.escape(esc(before[ident]['label']))+r'.*?</details>',text,re.S)
   if not match:raise ValueError('Missing historical task block '+ident)
   original=target=match[0]
  fresh='<section data-current-contract="'+esc(ident)+'"><h3>'+esc(n['label'])+'</h3>'+fields(n)
  for v in n['protocol_variants']:
   fresh+='<article class="current-protocol-version" data-protocol-variant="'+esc(v['id'])+'"><h4>'+esc(v['title'])+'</h4>'+fields(v)+'<p>仅适用于：'+esc('、'.join(v['paper_ids']))+'</p><p>'+esc(v.get('locator',''))+'</p><a href="'+esc(v['source_url'])+'">固定版本协议来源 ↗</a>'
   for src in v.get('supporting_sources',[]):fresh+='<p><a href="'+esc(src['source_url'])+'">版本边界对照 ↗</a> '+esc(src.get('locator',''))+'</p>'
   fresh+='</article>'
  fresh+='</section><details class="historical-task-contract"><summary>历史记录：已被本轮定点纠错替代，不作为当前协议</summary>'+original+'</details>'
  text=text.replace(target,start+fresh+end)
 return text
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();p=SOURCE/'all-papers.html';old=p.read_text();new=render(old,payload())
 if args.check:
  if new!=old:raise SystemExit('Stale script-free protocol cards')
  print('PASS deterministic current protocol cards and retained historical blocks')
 else:p.write_text(new)
