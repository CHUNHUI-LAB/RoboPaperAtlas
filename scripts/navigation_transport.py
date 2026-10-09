"""Lossless delivery projection of the frozen navigation model, not new science."""
import copy
import hashlib
import json

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
    default_scope = model['recommendedScopeIds'][0]
    roots = model['forests'][default_scope]['l']
    seed_ids = {model['positions'][pid]['entityId'] for pid in roots}
    index['delivery'] = {'schemaVersion':'navigation-delivery/1', 'sourceModelSha256':model_sha,
                         'recordOmissions':{k:list(v) for k,v in OMIT.items()},
                         'referenceIds':{key:sorted(ids) for key,ids in sorted(detail_ids.items())},
                         'packets':manifest, 'initialPackets':{eid:packets[eid] for eid in sorted(seed_ids)},
                         'archive':{'sha256':archive_sha,'bytes':len(archive_raw)}}
    embedded = inline_json(index).encode()
    return {'index':index, 'inline':embedded, 'indexSha256':digest(embedded), 'files':files,
            'reconstructed':reconstructed}
