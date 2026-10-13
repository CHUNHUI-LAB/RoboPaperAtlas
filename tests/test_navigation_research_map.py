"""Global display projection: source identity, actual topology and native paths."""
import copy
import gzip
import hashlib
from html.parser import HTMLParser
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from navigation_research_map import (build_research_map, render_global_native, write_scope_pages,
    _build_scope_outputs, _relations, _scope_name, _analysis_name, SOURCE_SHA, GOAL, LITERATURE, CHALLENGE)


class DOM(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.nodes = []; self.text = []; self.feed(text)
    def handle_starttag(self, tag, attrs): self.nodes.append((tag, dict(attrs)))
    def handle_data(self, data): self.text.append(data)


class ResearchMapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = gzip.decompress((ROOT / 'data/navigation-product/model.json.gz').read_bytes())
        cls.model = json.loads(cls.raw)
        cls.map = build_research_map(cls.model)
        cls.outputs = _build_scope_outputs(cls.model, cls.map)

    def test_frozen_science_and_deterministic_pure_descriptor(self):
        self.assertEqual(hashlib.sha256(self.raw).hexdigest(), SOURCE_SHA)
        before = json.dumps(self.model, sort_keys=True)
        self.assertEqual(build_research_map(self.model), self.map)
        self.assertEqual(json.dumps(self.model, sort_keys=True), before)
        self.assertEqual(self.map['schemaVersion'], 'research-map/1')
        self.assertEqual(self.map['sourceModelSha256'], SOURCE_SHA)

    def test_display_metadata_omits_redundant_status_and_order(self):
        for p in self.map['positions'].values():
            self.assertNotIn('status', p)
            self.assertNotIn('order', p)
            self.assertIsInstance(p['childIds'], list)
        # The original frozen records, including source status and ordering,
        # remain available. The purity test also verifies exact non-mutation.
        self.assertTrue(any('status' in p for p in self.model['positions'].values()))
        self.assertTrue(any('order' in p for p in self.model['positions'].values()))

    def test_recipe_display_title_uses_exact_langmap_v3_source(self):
        p = self.map['positions']['pos:g:18a33fba17e8e92ee1ed5d']
        title = 'LangMap: A Human-Verified Benchmark for Hierarchical Open-Vocabulary Goal Navigation'
        self.assertEqual(p['sourcePositionId'], 'pos:l:a786031a24f0627d36943d')
        self.assertEqual(p['versionId'], 'arxiv:2602.02220v3')
        self.assertEqual(p['label'], title)
        self.assertEqual(self.map['positions'][p['childIds'][0]]['label'], title)
        self.assertEqual(p['sourceLabel'], 'planavid：输入到执行反馈')
        self.assertNotEqual(p['label'], self.model['papers']['langmap26']['title'])
        self.assertIn('>' + title + '<span', render_global_native(self.model, self.map))

    def test_recipe_display_title_preserves_cow_publication_binding(self):
        rows = [p for p in self.map['positions'].values()
                if p.get('labelSourcePaperId') == 'cow']
        self.assertEqual(len(rows), 3)
        for p in rows:
            self.assertEqual(p['versionId'], 'publication:cow:a7abf1e326e6')
            self.assertEqual(p['label'], 'CoWs on PASTURE: Baselines and Benchmarks for Language-Driven Zero-Shot Object Navigation')
            self.assertEqual(p['sourceLabel'], self.model['positions'][p['sourcePositionId']]['label'])
        self.assertEqual(self.model['papers']['cow']['title'],
                         'CLIP on Wheels: Zero-Shot Object Navigation as Object Localization and Exploration')

    def test_recipe_display_title_uses_selected_older_version_not_latest(self):
        model = copy.deepcopy(self.model)
        source = model['positions']['pos:l:a786031a24f0627d36943d']
        paper = model['papers']['langmap26']
        older_id = 'arxiv:2602.02220v1'
        model['versions'][older_id] = dict(model['versions'][source['versionId']],
            id=older_id, sourceVersionIds=['test:langmap-v1'])
        paper['versionIds'].append(older_id)
        older_title = 'Earlier LangMap title for the v1 regression fixture'
        paper['provenance'].append({'title': older_title, 'sourceVersionIds': ['test:langmap-v1']})
        model['entities']['paper:test:langmap-v1'] = dict(model['entities']['methods:paper:langmap26'],
            id='paper:test:langmap-v1', label=older_title, versionIds=[older_id])
        source['versionId'] = older_id
        source['versionIds'] = [older_id]
        before = json.dumps(model, sort_keys=True)
        p = build_research_map(model)['positions']['pos:g:18a33fba17e8e92ee1ed5d']
        self.assertEqual(p['label'], older_title)
        self.assertEqual(p['versionId'], older_id)
        self.assertEqual(json.dumps(model, sort_keys=True), before)

    def test_recipe_display_title_falls_back_without_unambiguous_version_provenance(self):
        for case in ('historical-snapshot', 'missing-version', 'unknown-version',
                     'other-paper', 'unregistered-version', 'no-source-ids',
                     'unbound-provenance', 'ambiguous-title', 'blank-title',
                     'missing-entity', 'other-entity-version', 'other-entity-paper', 'other-entity-kind'):
            with self.subTest(case=case):
                model = copy.deepcopy(self.model)
                source = model['positions']['pos:l:a786031a24f0627d36943d']
                paper = model['papers']['langmap26']
                version = model['versions'][source['versionId']]
                bound = next(r for r in paper['provenance'] if r.get('sourceVersionIds'))
                if case == 'historical-snapshot': source['versionId'] = 'source:legacy:langmap26:0'
                elif case == 'missing-version': source['versionId'] = None
                elif case == 'unknown-version': source['versionId'] = 'not-imported'
                elif case == 'other-paper': version['paperId'] = 'cow'
                elif case == 'unregistered-version': paper['versionIds'].remove(source['versionId'])
                elif case == 'no-source-ids': version['sourceVersionIds'] = []
                elif case == 'unbound-provenance': bound['sourceVersionIds'] = ['test:other-version']
                elif case == 'ambiguous-title': paper['provenance'].append(dict(bound, title='Conflicting title'))
                elif case == 'blank-title': bound['title'] = ' '
                elif case == 'missing-entity': del model['entities']['methods:paper:langmap26']
                elif case == 'other-entity-version': model['entities']['methods:paper:langmap26']['versionIds'] = []
                elif case == 'other-entity-paper': model['entities']['methods:paper:langmap26']['paperId'] = 'cow'
                elif case == 'other-entity-kind': model['entities']['methods:paper:langmap26']['kind'] = 'pipeline_recipe'
                before = json.dumps(model, sort_keys=True)
                p = build_research_map(model)['positions']['pos:g:18a33fba17e8e92ee1ed5d']
                self.assertEqual(p['label'], paper['title'])
                self.assertEqual(p['versionId'], source['versionId'])
                self.assertEqual(json.dumps(model, sort_keys=True), before)

    def test_recipe_display_title_does_not_parse_descriptors_or_source_ref_text(self):
        model = copy.deepcopy(self.model)
        source = model['positions']['pos:l:a786031a24f0627d36943d']
        paper = model['papers']['langmap26']
        version = model['versions'][source['versionId']]
        paper['provenance'] = []
        version['label'] = 'arXiv v3 — Descriptor text is not title provenance'
        version['sourceRefs'][0]['detail']['title'] = 'Unbound source-ref title'
        p = build_research_map(model)['positions']['pos:g:18a33fba17e8e92ee1ed5d']
        self.assertEqual(p['label'], paper['title'])

    def test_recipe_version_title_is_escaped_and_duplicate_evidence_is_unambiguous(self):
        model = copy.deepcopy(self.model)
        paper = model['papers']['langmap26']
        bound = next(r for r in paper['provenance'] if r.get('sourceVersionIds'))
        bound['title'] = '<script>version title</script> & "quoted"'
        model['entities']['methods:paper:langmap26']['label'] = bound['title']
        paper['provenance'].append(copy.deepcopy(bound))
        descriptor = build_research_map(model)
        self.assertEqual(descriptor['positions']['pos:g:18a33fba17e8e92ee1ed5d']['label'], bound['title'])
        rendered = render_global_native(model, descriptor)
        self.assertIn('&lt;script&gt;version title&lt;/script&gt; &amp; &quot;quoted&quot;', rendered)
        self.assertNotIn('<script>version title', rendered)

    def test_recipe_version_title_keeps_unmatched_igibson_title_unchanged(self):
        p = self.map['positions']['pos:g:24ecb6d36c4e5d1798cf90']
        self.assertEqual(p['versionId'], 'arxiv:1910.14442v2')
        self.assertEqual(p['label'], self.model['papers']['igibson19']['title'])

    def test_root_is_goal_and_two_real_branches_are_initially_expanded(self):
        p = self.map['positions']; self.assertEqual(len(self.map['roots']), 1)
        root = p[self.map['roots'][0]]
        self.assertEqual(root['entityId'], GOAL)
        self.assertEqual({p[c]['entityId'] for c in root['childIds']}, {LITERATURE, CHALLENGE})
        self.assertTrue(({root['id']} | set(root['childIds'])) <= set(self.map['initialExpandedIds']))
        for branch in root['childIds']: self.assertGreater(len(p[branch]['childIds']), 1)
        self.assertEqual(self.map['documentEntityId'], 'legacy:nav:root')

    def test_every_occurrence_has_real_containment_witness_and_exact_closure(self):
        p = self.map['positions']; rels = _relations(self.model)
        aliases = {a: row['canonicalEntityId'] for row in self.map['aliases'] for a in row['aliasEntityIds']}
        seen = set()
        def walk(pid, parent=None):
            self.assertNotIn(pid, seen); seen.add(pid); node = p[pid]
            self.assertEqual(node['parentId'], parent); self.assertEqual(node['id'], pid)
            self.assertTrue(pid.startswith('pos:g:')); self.assertEqual(node['tree'], 'g')
            self.assertEqual(node['scopeId'], 'scope:all')
            self.assertIn(node['entityId'], {**self.model['entities'], **self.map['presentationEntities']})
            self.assertTrue(set(node['annotationEntityIds']) <= set(self.model['entities']))
            if parent and node.get('edgeSemantics') == 'source_position_projection':
                old = self.model['positions'][node['sourcePositionId']]
                self.assertEqual(p[parent]['sourcePositionId'], old['parentId'])
                self.assertEqual(node['sourceParentPositionId'], old['parentId'])
                for key in ('entityId', 'paperId', 'versionId', 'claimIds', 'association', 'relationType'):
                    self.assertEqual(node.get(key), old.get(key))
            elif parent and node.get('edgeSemantics') == 'editorial_navigation':
                self.assertFalse(node['sourceRelationIds'])
                self.assertEqual(node['relationType'], 'editorial_navigation_not_scientific_containment')
            elif parent:
                self.assertTrue(node['sourceRelationIds'])
                for rid in node['sourceRelationIds']:
                    r = rels[rid]; self.assertTrue(r['renderAsTree'])
                    self.assertEqual(aliases.get(r['from'], r['from']), node.get('sourceParentEntityId', p[parent]['entityId']))
                    self.assertEqual(aliases.get(r['to'], r['to']), node['entityId'])
            for child in node['childIds']: walk(child, pid)
        for root in self.map['roots']: walk(root)
        self.assertEqual(seen, set(p))

    def test_thirteen_display_aliases_do_not_merge_science_or_promote_subchallenge(self):
        self.assertEqual(len(self.map['aliases']), 13)
        for row in self.map['aliases']:
            e = self.model['entities'][row['canonicalEntityId']]
            self.assertFalse(row['scientificRecordsMerged'])
            for eid in row['aliasEntityIds']:
                self.assertEqual(self.model['entities'][eid]['originalId'], e['originalId'])
                occurrences = [p for p in self.map['positions'].values() if p['entityId'] == row['canonicalEntityId']]
                for p in occurrences: self.assertIn(eid, p['annotationEntityIds'])
        prompt = [p for p in self.map['positions'].values() if p['entityId'] == 'legacy:ci_prompt_uncertainty']
        self.assertTrue(prompt)
        for p in prompt:
            self.assertEqual(p['kind'], 'subchallenge')
            self.assertEqual(self.map['positions'][p['parentId']]['entityId'], 'legacy:ci_search_unknown_target')

    def test_seventeen_works_are_contained_six_context_works_only_annotations(self):
        visible = {p['entityId'] for p in self.map['positions'].values()}
        notes = {eid for p in self.map['positions'].values() for eid in p['annotationEntityIds']}
        works = {eid for eid in self.model['entities'] if eid.startswith('legacy:method:work:')}
        contexts = {eid for eid in self.model['entities'] if eid.startswith('legacy:challenge:context:')}
        self.assertEqual(len(works), 17); self.assertTrue(works <= visible)
        self.assertEqual(len(contexts), 6); self.assertFalse(contexts & visible); self.assertTrue(contexts <= notes)

    def test_ten_work_recipe_bindings_keep_paper_and_version_exact(self):
        self.assertEqual(len(self.map['workRecipeBindings']), 10)
        for row in self.map['workRecipeBindings']:
            work = self.model['entities'][row['workEntityId']]; recipe = self.model['entities'][row['recipeEntityId']]
            self.assertEqual(work['paperId'], recipe['paperId'])
            self.assertEqual(set(work['versionIds']), set(recipe['versionIds']))
            self.assertEqual(work['detail']['method_variant_id'], recipe['detail']['id'])
        for p in self.map['positions'].values():
            if p['versionId']:
                self.assertTrue(p['paperId'])
                self.assertEqual(self.model['versions'][p['versionId']]['paperId'], p['paperId'])
            self.assertNotEqual(p['kind'], 'milestone_task')
            self.assertNotIn('noveltyClass', p)

    def test_sixty_four_roles_and_thirty_bridges_never_become_twenty_identity_merges(self):
        self.assertEqual(len(self.map['scopeEntries']), 64)
        scopes = {s['id']: s for s in self.model['scopes']}
        self.assertEqual({r['scopeId'] for r in self.map['scopeEntries']}, set(scopes))
        self.assertEqual(sum(bool(r['bridges']) for r in self.map['scopeEntries']), 20)
        self.assertEqual(sum(len(r['bridges']) for r in self.map['scopeEntries']), 30)
        same = [(r['scopeId'], b) for r in self.map['scopeEntries'] for b in r['bridges'] if b['relationType'] == 'same_bounded_task_identity']
        self.assertEqual(len(same), 2); self.assertEqual({s for s, _ in same}, {'task:category-objectnav'})
        self.assertEqual(sum(bool(r['positionIds']) for r in self.map['scopeEntries']), 64)
        self.assertEqual(sum(bool(r['legacyPositionIds']) for r in self.map['scopeEntries']), 13)
        for row in self.map['scopeEntries']: self.assertIn(row['canonicalPositionId'], row['positionIds'])
        self.assertEqual(self.map['coverage']['scopesPendingGlobalPlacement'], 0)
        self.assertEqual(self.map['coverage']['legacyAudit']['scopesPendingGlobalPlacement'], 51)
        self.assertEqual(self.map['coverage']['scopesWithoutTypedBridges'], 44)
        self.assertEqual(self.map['coverage']['scopesBridgedButTargetNotVisible'], 7)
        for row in self.map['scopeEntries']:
            self.assertEqual(row['displayRole'], scopes[row['scopeId']]['displayRole'])
            original = [b for b in scopes[row['scopeId']].get('bindings', []) if b.get('legacyId')]
            self.assertEqual([(b['targetEntityId'], b['association'], b['relationType']) for b in row['bridges']],
                             [('legacy:' + b['legacyId'], b['association'], b['relationType']) for b in original])

    def test_all_220_original_scope_positions_and_editorial_groups_are_explicit(self):
        expected = {pid for pid, p in self.model['positions'].items() if p['tree'] == 'l' and p['scopeId'] != 'scope:all'}
        projected = [p['sourcePositionId'] for p in self.map['positions'].values() if p.get('sourceTree') == 'l']
        self.assertEqual(len(expected), 228); self.assertEqual(len(projected), 228)
        self.assertEqual(set(projected), expected)
        groups = {g['id']: g for g in self.model['directoryGroups']}
        for eid, entity in self.map['presentationEntities'].items():
            self.assertTrue(eid.startswith('display:research-map:'))
            self.assertIsNone(entity['paperId'])
            for key in ('versionIds', 'claimIds', 'sourceRefs'): self.assertEqual(entity[key], [])
            if entity['kind'] == 'editorial_directory_group':
                self.assertEqual(entity['label'], groups[entity['detail']['sourceDirectoryGroupId']]['label'])
        for sid, pid in self.map['canonicalScopePositionIds'].items():
            scope = next(s for s in self.model['scopes'] if s['id'] == sid)
            p = self.map['positions'][pid]
            self.assertEqual(p['displayRole'], scope['displayRole'])
            self.assertEqual(p['entityId'], scope['entityId'])
            if scope.get('parentScopeId'):
                self.assertEqual(p['parentId'], self.map['canonicalScopePositionIds'][scope['parentScopeId']])
        relevant = [p for p in self.map['positions'].values() if p.get('sourceTree') == 'l' and p.get('relationType') == 'mechanism_relevance_projection']
        self.assertEqual(len(relevant), 7)
        self.assertTrue(all(p['association'] == 'condition' for p in relevant))

    def test_real_model_installer_accepts_and_global_routes_preserve_identity(self):
        code = "const fs=require('fs'),z=require('zlib'),M=require('./assets/navigation-product-model.js');const b=JSON.parse(z.gunzipSync(fs.readFileSync('data/navigation-product/model.json.gz'))),d=JSON.parse(fs.readFileSync(0,'utf8'));b.delivery={researchMap:d,sourceModelSha256:d.sourceModelSha256};M.installResearchMap(b);M.validateBundle(b);for(const p of Object.values(d.positions)){const r=M.routeForPosition(b,{scope:'scope:all',tree:'g'},p.id);M.validateRoute(b,r);}"
        subprocess.run(['node', '-e', code], cwd=ROOT, input=json.dumps(self.map), text=True, check=True)

    def test_native_home_is_true_global_structure_without_all_scope_bodies(self):
        text = render_global_native(self.model, self.map); dom = DOM(text)
        self.assertNotIn('np-static-reading', text)
        positions = [a for t, a in dom.nodes if a.get('data-native-global-position')]
        self.assertEqual(len(positions), len(self.map['positions']))
        for attrs in positions:
            p = self.map['positions'][attrs['data-native-global-position']]
            self.assertEqual(attrs['data-native-entity'], p['entityId'])
            self.assertEqual(attrs['data-native-directory-group'], p.get('sourceDirectoryGroupId') or '')
        self.assertEqual(sum('open' in a for a in positions), len(self.map['initialExpandedIds']))
        self.assertIn('General goal', text)
        self.assertNotIn('6 个常用入口', text)
        self.assertFalse(any(t in ('script', 'iframe') for t, _ in dom.nodes))
        self.assertLess(len(text.encode()), 350000)
        self.assertTrue(any(a.get('href') == 'branches/index.html' for _, a in dom.nodes))

    def test_native_all_scope_links_including_hidden_directory_roles(self):
        html = self.outputs['directory.html'].decode(); dom = DOM(html)
        entries = [a['data-scope-id'] for _, a in dom.nodes if 'data-scope-id' in a]
        self.assertEqual(len(entries), 64); self.assertEqual(len(set(entries)), 64)
        self.assertIn('protocol:sequential-eqa', entries); self.assertIn('task:av-question-answering', entries)
        for scope in self.model['scopes']:
            page = self.outputs[_scope_name(scope['id'])].decode()
            self.assertIn(scope['displayRole'], page)
            for tree in ('l', 'c'):
                for pid in self.model['forests'][scope['id']][tree]: self.assertIn(pid, page)

    def test_analysis_pages_keep_explicit_versions_and_no_borrowing(self):
        from navigation_research_map import _native_forest
        for paper, versions in self.model['analyses'].items():
            for version, entry in versions.items():
                page = self.outputs[_analysis_name(paper, version)].decode()
                self.assertIn(str(entry['answeredOriginalCount']) + '个原节点已填', page)
                self.assertEqual(page.count('data-native-position='), entry['originalNodeCount'] + entry['instanceCount'])
        pid = 'harnessvln'; version = next(v for v in self.model['papers'][pid]['versionIds'] if v not in self.model['analyses'][pid])
        page = self.outputs[_analysis_name(pid, version)].decode()
        self.assertIn('0已答', page); self.assertEqual(page.count('data-native-position='), 59)
        self.assertNotIn('<strong>已填回答', page)
        self.assertIn('template=1', page)

    def test_native_types_are_readable_and_answer_counts_are_version_bound(self):
        from navigation_research_map import NATIVE_RELATION_LABELS
        for p in list(self.model['positions'].values()) + list(self.map['positions'].values()):
            if p.get('relationType'): self.assertIn(p['relationType'], NATIVE_RELATION_LABELS)
        for paper, versions in self.model['analyses'].items():
            for version, entry in versions.items():
                dom = DOM(self.outputs[_analysis_name(paper, version)].decode())
                answers = [a for _, a in dom.nodes if a.get('data-native-answer') == 'true']
                self.assertEqual(len(answers), entry['answeredOriginalCount'])
        home = render_global_native(self.model, self.map)
        self.assertIn('条件关联', home)
        self.assertIn('定义、评测条件与来源', home)
        self.assertNotIn('全图位置待组织', self.outputs['directory.html'].decode())
        for p in self.map['positions'].values():
            if p.get('sourceTree') == 'l':
                old = self.model['positions'][p['sourcePositionId']]
                for key in ('entityId', 'paperId', 'versionId', 'claimIds', 'association'):
                    self.assertEqual(p.get(key), old.get(key))

    def test_all_native_links_resolve_and_only_optional_shared_scripts(self):
        for name, raw in self.outputs.items():
            if not name.endswith('.html'): continue
            dom = DOM(raw.decode())
            self.assertFalse(any(t == 'iframe' for t, _ in dom.nodes), name)
            allowed_scripts = {'../../../assets/' + x for x in ('catalog-navigation.js', 'presentation.js', 'interface.js', 'chrome.js')}
            self.assertEqual({a.get('src') for t, a in dom.nodes if t == 'script'}, allowed_scripts, name)
            self.assertIn('class="native-main"', raw.decode())
            for tag, attrs in dom.nodes:
                self.assertFalse(any(k.startswith('on') for k in attrs), name)
                href = attrs.get('href')
                if not href: continue
                parts = urlsplit(href)
                if parts.scheme:
                    self.assertIn(parts.scheme, ('https', 'http')); continue
                if not parts.path or parts.path == '../index.html': continue
                if parts.path.startswith('../../../'):
                    self.assertIn(parts.path[9:], {'index.html', 'map/index.html', 'research/navigation/index.html', 'frontier/index.html', 'reading/index.html', 'submit/index.html', 'about/index.html', 'assets/site.css'}, name)
                    continue
                self.assertIn(parts.path, self.outputs, name + ' -> ' + href)

    def test_writer_is_deterministic_rejects_extra_or_symlink_before_writing(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            target = Path(tmp) / 'out'
            first = write_scope_pages(ROOT, target, self.model, self.map)
            second = write_scope_pages(ROOT, target, self.model, self.map)
            self.assertEqual(first, second)
            self.assertEqual(first['pageCount'], sum(x.endswith('.html') for x in self.outputs))
            folder = target / 'research/navigation/branches'
            extra = folder / 'unexpected.txt'; extra.write_text('keep')
            with self.assertRaises(ValueError): write_scope_pages(ROOT, target, self.model, self.map)
            extra.unlink()
            index = folder / 'index.html'; original = index.read_bytes(); index.unlink(); index.symlink_to(folder / 'directory.html')
            with self.assertRaises(ValueError): write_scope_pages(ROOT, target, self.model, self.map)
            self.assertTrue(index.is_symlink())

    def test_content_escaping_and_unknown_private_fields_are_not_serialized(self):
        model = copy.deepcopy(self.model)
        model['entities'][GOAL]['label'] = '<script>bad</script>" onfocus="bad'
        model['entities'][GOAL]['detail']['private_debug'] = 'PRIVATE-SENTINEL'
        descriptor = build_research_map(model); page = render_global_native(model, descriptor)
        self.assertIn('&lt;script&gt;', page); self.assertNotIn('<script>', page)
        self.assertNotIn('PRIVATE-SENTINEL', page)
        body = _build_scope_outputs(model, descriptor)['index.html'].decode()
        self.assertNotIn('PRIVATE-SENTINEL', body); self.assertNotIn('<script>', body)


if __name__ == '__main__': unittest.main()
