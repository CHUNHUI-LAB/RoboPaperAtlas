"""Lossless delivery projection of the frozen navigation model, not new science."""
import copy
import hashlib
import json
from navigation_research_map import build_research_map

OMIT = {
    'entities': ('detail', 'sourceRefs', 'directoryProjection'),
    'claims': ('detail', 'sourceRefs', 'statement', 'label', 'history', 'evidenceCorrection'),
    'papers': ('sourceRefs', 'provenance'),
    'versions': ('sourceRefs',),
}
ARCHIVE_TABLES = ('relations', 'relatedRelations', 'sources', 'sourceProvenance')

def encode(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

def inline_json(value):
    return encode(value).decode().replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def project_record(table, value):
    return {k: copy.deepcopy(v) for k, v in value.items() if k not in OMIT.get(table, ())}

def relation_claims(relation):
    d = relation.get('detail') or {}
    return relation.get('claimIds') or relation.get('evidence_refs') or d.get('claimIds') or d.get('evidence_refs') or []

def compact_research_map(model, descriptor):
    compact = copy.deepcopy(descriptor)
    compact['labelEncoding'] = 'source-reference/1'
    entities = {**model['entities'], **descriptor.get('presentationEntities', {})}
    for p in compact['positions'].values():
        if p['label'] == entities[p['entityId']]['label']:
            p['labelRef'] = 'entityId.label'
        elif p.get('labelSourcePaperId') == p.get('paperId') and p.get('paperId') in model['papers'] and p['label'] == model['papers'][p['paperId']]['title']:
            p['labelRef'] = 'labelSourcePaperId.title'
        else:
            raise ValueError('Global title has no exact source reference')
        del p['label']
    restored = restore_research_map(model, compact)
    if restored != descriptor: raise ValueError('Global label reference projection is lossy')
    return compact


def restore_research_map(model, compact):
    result = copy.deepcopy(compact)
    if result.pop('labelEncoding', None) != 'source-reference/1': raise ValueError('Unknown global label encoding')
    entities = {**model['entities'], **result.get('presentationEntities', {})}
    for p in result['positions'].values():
        ref = p.pop('labelRef', None)
        if 'label' in p: raise ValueError('Conflicting inline label and reference')
        if ref == 'entityId.label': p['label'] = entities[p['entityId']]['label']
        elif ref == 'labelSourcePaperId.title' and p.get('labelSourcePaperId') == p.get('paperId'):
            p['label'] = model['papers'][p['labelSourcePaperId']]['title']
        else: raise ValueError('Unknown or mismatched global title reference')
    return result

def compact_scope_coverage(index):
    refs=[]
    for scope in index['scopes']:
        sid=scope['id']
        if sid not in index['coverage']:continue
        canonical=index['coverage'][sid]
        if scope.get('coverage')!=canonical or scope.get('coveragePolicy')!=canonical.get('coveragePolicy'):
            raise ValueError('Scope coverage is not an exact duplicate: '+sid)
        del scope['coverage'];del scope['coveragePolicy'];refs.append(sid)
    if set(refs)!=set(index['coverage']):raise ValueError('Coverage references must match the scope inventory')
    index['delivery']['scopeCoverageEncoding']='coverage-and-policy-by-scope-id-v1'
    index['delivery']['scopeCoverageIds']=refs
    directory_refs=[]
    for entry in index['directory']:
        sid=entry['id']
        if sid not in index['coverage'] or entry.get('coverage')!=index['coverage'][sid]:
            raise ValueError('Directory coverage is not an exact duplicate: '+sid)
        del entry['coverage'];directory_refs.append(sid)
    index['delivery']['directoryCoverageIds']=directory_refs

def restore_scope_coverage(index):
    result=copy.deepcopy(index);delivery=result.get('delivery',{})
    encoding=delivery.get('scopeCoverageEncoding');refs=delivery.get('scopeCoverageIds')
    directory_refs=delivery.get('directoryCoverageIds')
    scopes={s['id']:s for s in result['scopes']}
    if encoding is None:
        if refs is not None or directory_refs is not None:raise ValueError('Coverage references have no encoding')
        if any('coverage' not in scopes[sid] or 'coveragePolicy' not in scopes[sid] for sid in result['coverage']):
            raise ValueError('Missing unencoded scope coverage')
        if any('coverage' not in entry for entry in result['directory']):raise ValueError('Missing unencoded directory coverage')
        return result
    if encoding!='coverage-and-policy-by-scope-id-v1':raise ValueError('Unknown scope coverage encoding')
    if not isinstance(refs,list) or any(not isinstance(x,str) for x in refs) or len(set(refs))!=len(refs) or set(refs)!=set(result['coverage']):
        raise ValueError('Invalid scope coverage reference inventory')
    for sid,scope in scopes.items():
        if sid not in refs and ('coverage' not in scope or not scope.get('isVirtual') and 'coveragePolicy' not in scope):
            raise ValueError('Scope coverage is missing from both inline and referenced records')
    for sid in refs:
        if sid not in scopes or 'coverage' in scopes[sid] or 'coveragePolicy' in scopes[sid]:
            raise ValueError('Unknown or conflicting scope coverage reference')
        coverage=result['coverage'][sid]
        if coverage.get('scopeId')!=sid or not isinstance(coverage.get('coveragePolicy'),dict):raise ValueError('Coverage identity mismatch')
        scopes[sid]['coverage']=copy.deepcopy(coverage)
        scopes[sid]['coveragePolicy']=copy.deepcopy(coverage['coveragePolicy'])
    directory={row['id']:row for row in result['directory']}
    if len(directory)!=len(result['directory']):raise ValueError('Duplicate directory identity')
    if directory_refs is None:
        if any('coverage' not in row for row in directory.values()):raise ValueError('Missing unencoded directory coverage')
    else:
        if not isinstance(directory_refs,list) or any(not isinstance(x,str) for x in directory_refs) or len(set(directory_refs))!=len(directory_refs) or set(directory_refs)!=set(directory):raise ValueError('Invalid directory coverage references')
        for sid in directory_refs:
            if sid not in result['coverage'] or 'coverage' in directory[sid]:raise ValueError('Unknown or conflicting directory coverage')
            directory[sid]['coverage']=copy.deepcopy(result['coverage'][sid])
        del delivery['directoryCoverageIds']
    del delivery['scopeCoverageEncoding'];del delivery['scopeCoverageIds']
    return result

def project(model, model_sha):
    index = copy.deepcopy(model)
    for table in OMIT:
        index[table] = {key: project_record(table, row) for key, row in model[table].items()}
    archive = {key: index.pop(key) for key in ARCHIVE_TABLES if key in index}
    # These rows preserve all non-rendered provenance and any otherwise unbound claims.
    archive.update(papers=model['papers'], versions=model['versions'], claims=model['claims'])
    archive.update(schemaVersion='navigation-content-archive/1', sourceModelSha256=model_sha)
    files = {}
    archive_raw = encode(archive)
    archive_sha = digest(archive_raw)
    files[archive_sha+'.json'] = archive_raw
    all_relations = list(model.get('relations', {}).values()) + model.get('relatedRelations', [])
    papers = {}
    detail_ids = {}
    position_claims = {}
    for e in model['entities'].values():
        if e.get('kind') == 'paper' and e.get('paperId'):
            papers.setdefault(e['paperId'], set()).add(e['id'])
        ref = (e.get('detail') or {}).get('id')
        if isinstance(ref, str): detail_ids.setdefault(ref, set()).add(e['id'])
    for p in model['positions'].values():
        position_claims.setdefault(p['entityId'], set()).update(p.get('claimIds') or [])
    manifest = {}
    packets = {}
    for owner_id, entity in model['entities'].items():
        own = {owner_id} | papers.get(entity.get('paperId'), set())
        relations = []
        seen = set()
        for rel in all_relations:
            start = rel.get('from') or rel.get('fromId')
            end = rel.get('to') or rel.get('toId')
            key = rel.get('id') or start+'|'+end+'|'+str(rel.get('relationType'))
            if key in seen or (start not in own and end not in own): continue
            seen.add(key); relations.append(rel)
        entity_ids = {owner_id}
        design = (entity.get('detail') or {}).get('design')
        if isinstance(design, str):
            candidates = set(detail_ids.get(design, set()))
            if design in model['entities']: candidates.add(design)
            # Keep exact original candidates. Rendering still enforces paper AND version.
            entity_ids.update(candidates)
        claim_ids = set()
        for eid in entity_ids:
            claim_ids.update(model['entities'][eid].get('claimIds') or [])
            claim_ids.update(position_claims.get(eid, set()))
        for rel in relations: claim_ids.update(cid for cid in relation_claims(rel) if cid in model['claims'])
        if not claim_ids <= model['claims'].keys(): raise ValueError('Unknown packet claim')
        packet = {'schemaVersion':'navigation-content-packet/1', 'sourceModelSha256':model_sha,
                  'ownerId':owner_id,
                  'entities':{eid:model['entities'][eid] for eid in sorted(entity_ids)},
                  'claims':{cid:model['claims'][cid] for cid in sorted(claim_ids)},
                  'relations':relations}
        raw = encode(packet); sha = digest(raw)
        files[sha+'.json'] = raw
        manifest[owner_id] = {'sha256':sha, 'bytes':len(raw),
                              'entityIds':sorted(entity_ids), 'claimIds':sorted(claim_ids)}
        packets[owner_id] = packet
    # Full original rows can be recovered, including unused source/history fields.
    reconstructed = copy.deepcopy(index)
    reconstructed.update({k:copy.deepcopy(v) for k,v in archive.items()
                          if k not in ('schemaVersion','sourceModelSha256')})
    reconstructed['entities'] = {eid:copy.deepcopy(packets[eid]['entities'][eid]) for eid in model['entities']}
    if reconstructed != model: raise ValueError('Delivery projection lost frozen model content')
    research_map=build_research_map(model)
    if research_map['sourceModelSha256']!=model_sha: raise ValueError('Research map source mismatch')
    default_scope = model['recommendedScopeIds'][0]
    roots = model['forests'][default_scope]['l']
    seed_ids = {model['positions'][pid]['entityId'] for pid in roots}
    seed_ids.update(research_map['positions'][pid]['entityId'] for pid in research_map['roots'])
    index['delivery'] = {'schemaVersion':'navigation-delivery/1', 'sourceModelSha256':model_sha,
                         'researchMap':compact_research_map(model,research_map), 'recordOmissions':{k:list(v) for k,v in OMIT.items()},
                         'referenceIds':{key:sorted(ids) for key,ids in sorted(detail_ids.items())},
                         'packets':manifest, 'initialPackets':{eid:packets[eid] for eid in sorted(seed_ids)},
                         'archive':{'sha256':archive_sha,'bytes':len(archive_raw)}}
    before_coverage_compaction=copy.deepcopy(index)
    compact_scope_coverage(index)
    if restore_scope_coverage(index)!=before_coverage_compaction:raise ValueError('Scope coverage projection lost information')
    embedded = inline_json(index).encode()
    return {'index':index, 'inline':embedded, 'indexSha256':digest(embedded), 'files':files,
            'reconstructed':reconstructed, 'researchMap':research_map}
