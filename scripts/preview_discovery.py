"""Refresh method discovery in authenticated global-preview output only.

The immutable transport, graph geometry, relations, primary placement and reading
state are preserved. Only papers whose reviewed method evidence changed receive
new method/search/navigation projections.
"""
import json
import re
from catalog_search import BROWSE, BROWSE_LABELS, classification_search
from topic_labels import PAPERS, classification
from preview_reading import DECODER, _members, _space


def hydrate_discovery(payload):
    text=payload.decode('utf-8')
    matches=list(re.finditer(r'<script id="atlas-data" type="application/json">(.*?)</script>',text,re.S))
    if len(matches)!=1:raise ValueError('Expected one global discovery data block')
    match=matches[0];source=match.group(1);data=DECODER.decode(source)
    papers=data.get('papers')
    if not isinstance(papers,list):raise ValueError('Expected global discovery papers')
    canonical={p['id']:p for p in PAPERS}
    ids=[p.get('id') for p in papers if isinstance(p,dict)]
    if len(ids)!=len(papers) or len(set(ids))!=len(ids) or set(ids)!=set(canonical):
        raise ValueError('Global discovery IDs must match the full catalog exactly once')
    _,start,_=next(m for m in _members(source,_space(source,0)) if m[0]=='papers')
    offset=_space(source,start+1);replacements=[]
    for paper in papers:
        pid=paper['id'];reviewed=classification(canonical[pid])
        current=paper.get('classification')
        direction=current.get('direction') if isinstance(current,dict) else None
        if isinstance(current,dict) and direction is None:
            direction={'cross-domain-resource':'resources','cross-domain-research':'cross-domain'}.get(current.get('placementState'))
        if not isinstance(current,dict) or direction!=reviewed['direction']:
            raise ValueError('Global discovery must preserve reviewed primary placement')
        if current.get('methodTags')!=reviewed['methodTags']:
            navigation=paper.get('navigation')
            if not isinstance(navigation,dict) or navigation.get('primary') not in BROWSE[pid]['groups']:
                raise ValueError('Global discovery must preserve primary navigation')
            updates={
                'methods':[t['label'] for t in reviewed['methodTags']],
                'classification':dict(current,methodTags=reviewed['methodTags']),
                'searchAliases':list(dict.fromkeys([*paper['searchAliases'],classification_search(canonical[pid])])),
                'navigation':dict(navigation,groups=BROWSE[pid]['groups'],reasons=BROWSE[pid]['reasons'],
                                  labels=[BROWSE_LABELS[g] for g in BROWSE[pid]['groups']]),
            }
            spans={k:(a,b) for k,a,b in _members(source,offset)}
            if set(updates)-set(spans):raise ValueError('Missing global discovery fields')
            for key,value in updates.items():
                a,b=spans[key];encoded=json.dumps(value,ensure_ascii=False,separators=(',',':'))
                encoded=encoded.replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
                replacements.append((match.start(1)+a,match.start(1)+b,encoded))
        _,offset=DECODER.raw_decode(source,offset);offset=_space(source,offset)
        if source[offset]==',':offset=_space(source,offset+1)
    for a,b,value in sorted(replacements,reverse=True):text=text[:a]+value+text[b:]
    return text.encode('utf-8')
