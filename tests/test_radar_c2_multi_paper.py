"""Focused paper-indexed C2 contracts; no real browser or scientific reproduction.

Historical C2 security and immutable-history tests remain unchanged and run in
addition to these tests. Controls use copies or in-memory bytes, never originals.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import radar_c2_preview as c2


def encode(value):
    return json.dumps(value, ensure_ascii=False).encode('utf-8')


def reviewed_inputs():
    # Source-science tests do not depend on in-progress UI or a release reseal.
    names = (set(c2.SCIENTIFIC_SOURCE_SHA256) | set(c2.HISTORICAL_ENTRY_SHA256)
             | {'analysis/data/MULTI-PAPER-VERIFICATION.json', 'tests/entry-baseline.json'})
    return {name: (ROOT / c2.INPUT_SOURCE / name).read_bytes() for name in names}


class RadarC2MultiPaperContractTests(unittest.TestCase):
    def setUp(self):
        self.inputs = reviewed_inputs()
        self.bundle = c2.assigned_json(
            (ROOT / c2.SOURCE / 'analysis/data/bundle.js').read_bytes(), 'C2_DATA')

    def test_both_sources_and_legacy_aliases_are_exact(self):
        c2.validate_analysis_bundle(self.bundle, self.inputs)
        self.assertEqual(set(self.bundle), {'schema', 'mapping', 'compat', 'mappingsByPaperId',
                                          'ledgersByPaperId', 'unknownsByPaperId'})
        self.assertEqual(self.bundle['mapping'], self.bundle['mappingsByPaperId']['harnessvln'])
        for name, value in (('method.json', self.bundle['schema']),
                            ('mapping.json', self.bundle['mapping']),
                            ('analysis.compat.json', self.bundle['compat']),
                            ('navharness.mapping.json', self.bundle['mappingsByPaperId']['navharness']),
                            ('navharness.ledger.json', self.bundle['ledgersByPaperId']['navharness']),
                            ('navharness.unknowns.json', self.bundle['unknownsByPaperId']['navharness'])):
            self.assertEqual(value, json.loads(self.inputs['analysis/data/' + name]))
        for name, digest in c2.SCIENTIFIC_SOURCE_SHA256.items():
            self.assertEqual(hashlib.sha256(self.inputs[name]).hexdigest(), digest, name)

    def test_schema_and_instance_topology_are_paper_local(self):
        schema = self.bundle['schema']['nodes']
        ids = {node['id'] for node in schema}
        self.assertEqual(len(ids), 59)
        for paper_id, expected in [('harnessvln', 72), ('navharness', 77)]:
            mapping = self.bundle['mappingsByPaperId'][paper_id]
            extra = mapping['expandedNodes']
            extra_ids = {node['nodeId'] for node in extra}
            self.assertEqual(len(ids | extra_ids), expected)
            self.assertFalse(ids & extra_ids)
            for node in extra:
                self.assertIn(node['repeatOfSchemaNode'], ids)
                self.assertIn(node['expansionSlot'], ids)
                self.assertIn(node['parentId'], ids | extra_ids)
                self.assertTrue(node['isPaperSpecificInstantiation'])
            self.assertEqual([node['templateNodeId'] for node in mapping['templateNodes']],
                             [node['id'] for node in schema])

    def test_counts_derive_from_indexes_with_explicit_reviewed_boundaries(self):
        catalog = json.loads(self.inputs['data/catalog.json'])
        state = c2.scientific_state(self.bundle, catalog)
        self.assertEqual((state['supported_papers'], state['pending_papers']), (2, 37))
        for paper_id, expected in [('harnessvln', (72, 47, 6, 27, 182)),
                                   ('navharness', (77, 51, 12, 31, 724))]:
            paper = state['papers'][paper_id]
            self.assertEqual(tuple(paper[key] for key in ('total_nodes', 'answers', 'unresolved',
                                                          'evidence_records', 'source_locator_occurrences')),
                             expected)
        self.assertEqual(state['papers']['navharness']['answer_statuses'],
                         {'evidence_linked': 43, 'author_claim_only': 6, 'partially_reported': 2})
        # A derivation control is intentionally not a valid releasable bundle.
        reduced = copy.deepcopy(self.bundle)
        for key in ('mappingsByPaperId', 'ledgersByPaperId', 'unknownsByPaperId'):
            del reduced[key]['navharness']
        derived = c2.scientific_state(reduced, catalog)
        self.assertEqual((derived['supported_papers'], derived['pending_papers']), (1, 38))
        with self.assertRaises(ValueError):
            c2.validate_analysis_bundle(reduced, self.inputs)

    def test_identity_and_all_other_papers_remain_pending(self):
        catalog = json.loads(self.inputs['data/catalog.json'])
        ids = {paper['canonical_id'] for paper in catalog['papers']}
        self.assertEqual(len(ids), 39)
        supported = set(self.bundle['mappingsByPaperId'])
        self.assertEqual(supported, {'harnessvln', 'navharness'})
        self.assertTrue(supported <= ids)
        self.assertEqual(len(ids - supported), 37)
        self.assertIn('arxiv:2609.39915', ids - supported)
        self.assertEqual(self.bundle['mappingsByPaperId']['navharness']['sourceVersion'], '2609.34276v1')
        self.assertFalse(self.bundle['compat']['existingStageStateMutation'])
        self.assertTrue(all(not m['existingStageStateMutation']
                            for m in self.bundle['mappingsByPaperId'].values()))

    def test_evidence_ids_are_paper_scoped_and_all_backlinks_resolve(self):
        by_paper = {}
        for paper_id, ledger in self.bundle['ledgersByPaperId'].items():
            by_paper[paper_id] = {record.get('id', record.get('evidenceRecordId')): record
                                  for record in ledger['records']}
            self.assertEqual(len(by_paper[paper_id]), len(ledger['records']))
            mapping = self.bundle['mappingsByPaperId'][paper_id]
            for entry in mapping['answers'] + self.bundle['unknownsByPaperId'][paper_id]:
                for evidence_id in entry.get('evidenceRecordIds', []):
                    self.assertIn(evidence_id, by_paper[paper_id])
        self.assertNotEqual(by_paper['harnessvln']['E01'], by_paper['navharness']['E01'])
        self.assertNotIn('E31', by_paper['harnessvln'])
        self.assertIn('E31', by_paper['navharness'])
        self.assertTrue(all(record['independentlyReproduced'] is False
                            for record in by_paper['navharness'].values()))

    def test_twelve_unknowns_and_figure18_conflict_remain_lossless(self):
        unknowns = self.bundle['unknownsByPaperId']['navharness']
        self.assertEqual(unknowns, self.bundle['mappingsByPaperId']['navharness']['unresolvedQuestions'])
        self.assertEqual([item['id'] for item in unknowns], ['U%02d' % i for i in range(1, 13)])
        for item in unknowns:
            self.assertTrue(item['topic'] and item['detail'] and item['status'])
            self.assertNotIn('nodeId', item)
            self.assertNotIn('question', item)
        u12 = unknowns[-1]
        self.assertEqual(u12['status'], 'figure_text_inconsistency')
        self.assertEqual(u12['sourceUrls'], ['https://arxiv.org/pdf/2609.34276v1#page=39'])
        self.assertIn('Figure18(p39)', u12['detail'])
        self.assertIn('task34', u12['detail'])
        self.assertTrue(all('U12' not in answer['sourceGapIds']
                            for answer in self.bundle['mappingsByPaperId']['navharness']['answers']))

    def test_twenty_implementation_unknowns_are_not_verified(self):
        answers = self.bundle['mappingsByPaperId']['navharness']['answers']
        unknowns = [a for a in answers if a['codeEvidence']['status'] == 'not_reviewed_implementation_unknown']
        self.assertEqual(len(unknowns), 20)
        self.assertEqual({a['nodeId'] for a in unknowns},
                         {'method.module%d.%s' % (i, suffix) for i in range(1, 6)
                          for suffix in ('motivation', 'how', 'why', 'advantage')})
        for answer in unknowns:
            self.assertEqual(answer['sourceKind'], 'primary_paper')
            self.assertEqual(answer['codeEvidence'], {'status': 'not_reviewed_implementation_unknown',
                             'sourceKind': 'none', 'remainingQuestionId': 'U02'})
            self.assertIn('U02', answer['sourceGapIds'])
        self.assertEqual({a['codeEvidence']['status'] for a in answers},
                         {'not_applicable_to_this_answer', 'not_reviewed_implementation_unknown'})

    def test_runtime_rejects_extra_sources_wrong_aliases_and_cross_paper_replacement(self):
        controls = []
        changed = copy.deepcopy(self.bundle); changed['privateSources'] = {}; controls.append(changed)
        changed = copy.deepcopy(self.bundle); changed['mapping'] = changed['mappingsByPaperId']['navharness']; controls.append(changed)
        changed = copy.deepcopy(self.bundle); changed['ledgersByPaperId']['navharness'] = changed['ledgersByPaperId']['harnessvln']; controls.append(changed)
        changed = copy.deepcopy(self.bundle); changed['unknownsByPaperId']['navharness'] = changed['unknownsByPaperId']['navharness'][:6]; controls.append(changed)
        for changed in controls:
            with self.subTest(keys=list(changed)), self.assertRaisesRegex(ValueError, 'source-identical'):
                c2.validate_analysis_bundle(changed, self.inputs)

    def test_coherent_source_and_seal_rewrite_cannot_promote_science(self):
        for filename, mutate in (
            ('navharness.mapping.json', lambda m: m.update(sourceVersion='2609.39915v1')),
            ('navharness.mapping.json', lambda m: m['answers'][0].update(status='implementation_verified')),
            ('navharness.ledger.json', lambda m: m['records'][0].update(independentlyReproduced=True)),
            ('navharness.unknowns.json', lambda m: m.pop()),
            ('mapping.json', lambda m: m.update(existingStageStateMutation=True)),
        ):
            with self.subTest(filename=filename):
                inputs = dict(self.inputs)
                name = 'analysis/data/' + filename
                source = json.loads(inputs[name]); mutate(source); inputs[name] = encode(source)
                seal_name = 'analysis/data/MULTI-PAPER-VERIFICATION.json'
                seal = json.loads(inputs[seal_name])
                seal['inputs'][name] = hashlib.sha256(inputs[name]).hexdigest()
                inputs[seal_name] = encode(seal)
                # Even a matching runtime wrapper and rewritten seal cannot bless
                # changed approved source bytes without an explicit code review.
                with self.assertRaisesRegex(ValueError, 'approved-source hash mismatch'):
                    c2.validate_analysis_bundle(c2.expected_analysis_bundle(inputs), inputs)

    def test_new_seal_is_separate_and_cannot_change_versions_or_input_set(self):
        for mutate in (lambda s: s['fixedVersions'].update(navharness='2609.39915v1'),
                       lambda s: s['inputs'].update({'private.json': '0' * 64}),
                       lambda s: s.update(navharnessSourceManifestSha256='0' * 64)):
            inputs = dict(self.inputs)
            name = 'analysis/data/MULTI-PAPER-VERIFICATION.json'
            seal = json.loads(inputs[name]); mutate(seal); inputs[name] = encode(seal)
            with self.assertRaisesRegex(ValueError, 'Multi-paper scientific seal mismatch'):
                c2.validate_analysis_bundle(self.bundle, inputs)
        old = self.inputs['analysis/data/UPSTREAM-VERIFICATION.json']
        self.assertEqual(hashlib.sha256(old).hexdigest(),
                         'bf846ca9b440ebde6333dff6104ca6a1d7ff60a246bb6634be969fc60f518589')

    def test_public_allowlist_stays_fourteen_with_only_embedded_derivatives(self):
        self.assertEqual(len(c2.PUBLIC_FILES), 14)
        self.assertFalse(any(name.endswith(('.json', '.pdf', '.png', '.jpg', '.svg')) for name in c2.PUBLIC_FILES))
        self.assertIn('analysis/data/bundle.js', c2.PUBLIC_FILES)
        self.assertTrue(all(name not in c2.PUBLIC_FILES for name in (
            'analysis/data/navharness.mapping.json', 'analysis/data/navharness.ledger.json',
            'analysis/data/navharness.unknowns.json', 'analysis/data/MULTI-PAPER-VERIFICATION.json')))
        self.assertTrue(all(name in c2.REVIEW_INPUTS for name in (
            'analysis/data/navharness.mapping.json', 'analysis/data/navharness.ledger.json',
            'analysis/data/navharness.unknowns.json', 'analysis/data/MULTI-PAPER-VERIFICATION.json')))

    def test_deterministic_bundle_generator_and_changed_source_rejection(self):
        generator = ROOT / c2.INPUT_SOURCE / 'analysis/build_bundle.py'
        api = runpy.run_path(str(generator))
        expected = (ROOT / c2.SOURCE / 'analysis/data/bundle.js').read_bytes()
        self.assertEqual(api['bundle_bytes'](api['build_bundle']()), expected)
        with tempfile.TemporaryDirectory(prefix='c2-multi-bundle-') as temp:
            site = Path(temp) / 'site'
            shutil.copytree(ROOT / c2.INPUT_SOURCE, site)
            args = [sys.executable, str(site / 'analysis/build_bundle.py')]
            for _ in range(2):
                subprocess.run(args, check=True, capture_output=True, timeout=20)
                self.assertEqual((site / 'analysis/data/bundle.js').read_bytes(), expected)
            source = site / 'analysis/data/navharness.mapping.json'
            source.write_bytes(source.read_bytes() + b'\n')
            run = subprocess.run(args, capture_output=True, text=True, timeout=20)
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Reviewed source hash mismatch', run.stderr)

    def test_new_review_sources_reject_symlinks_and_fifo(self):
        # Exercise the existing nonblocking O_NOFOLLOW guard for every new source.
        for name in ('navharness.mapping.json', 'navharness.ledger.json',
                     'navharness.unknowns.json', 'MULTI-PAPER-VERIFICATION.json'):
            with self.subTest(name=name), tempfile.TemporaryDirectory(prefix='c2-new-source-') as temp:
                root = Path(temp)
                target = root / name
                target.symlink_to(ROOT / c2.INPUT_SOURCE / 'analysis/data' / name)
                with self.assertRaises(ValueError):
                    c2.read_regular(root, target)
                target.unlink(); os.mkfifo(target)
                with self.assertRaises(ValueError):
                    c2.read_regular(root, target)


class RadarC2MultiPaperJavaScriptTests(unittest.TestCase):
    """Permanent discovery entrypoint for new focused model and static suites."""
    def run_suite(self, name):
        with tempfile.TemporaryDirectory(prefix='c2-multi-js-') as temp:
            site = Path(temp) / 'site'
            shutil.copytree(ROOT / c2.SOURCE, site)
            shutil.copytree(ROOT / c2.INPUT_SOURCE, site, dirs_exist_ok=True)
            run = subprocess.run(['node', str(site / 'analysis/tests' / name)],
                                 capture_output=True, text=True, timeout=60)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('PASS ', run.stdout)

    def test_multi_paper_model_and_memory_dom_contracts(self):
        self.run_suite('multi-paper.test.cjs')

    def test_multi_paper_script_free_contracts(self):
        self.run_suite('static-multi-paper.test.cjs')


class RadarC2HistoricalPreservationControls(unittest.TestCase):
    """Each corruption calls the exact positive invariant used by the portable suite."""
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='c2-historical-controls-')
        self.addCleanup(self.temp.cleanup)
        self.site = Path(self.temp.name) / 'site'
        shutil.copytree(ROOT / c2.SOURCE, self.site)
        shutil.copytree(ROOT / c2.INPUT_SOURCE, self.site, dirs_exist_ok=True)

    def invariant(self, overrides):
        return subprocess.run(['node', str(self.site / 'tests/three-entry.test.cjs'),
                               '--check-preservation'], input=json.dumps(overrides, ensure_ascii=False),
                              capture_output=True, text=True, timeout=60)

    def test_exact_positive_and_changed_or_dropped_legacy_answers(self):
        positive = self.invariant({})
        self.assertEqual(positive.returncode, 0, positive.stdout + positive.stderr)
        original = c2.assigned_json((self.site / 'analysis/data/bundle.js').read_bytes(), 'C2_DATA')
        for mode in ('change', 'drop'):
            changed = copy.deepcopy(original)
            for mapping in (changed['mapping'], changed['compat'], changed['mappingsByPaperId']['harnessvln']):
                if mode == 'change':
                    mapping['answers'][0]['answer'] = 'CORRUPTION CONTROL'
                else:
                    mapping['answers'].pop(0)
            run = self.invariant({'analysis/data/bundle.js': 'window.C2_DATA = ' + json.dumps(changed, ensure_ascii=False) + ';\n'})
            self.assertNotEqual(run.returncode, 0, mode)
            self.assertIn('Current complete bundle differs from approved source values', run.stderr)

    def test_rendered_science_corruptions_fail_the_same_typed_invariant(self):
        from html import escape
        import re
        original = (self.site / 'analysis/reading.html').read_text()
        mapping = json.loads((self.site / 'analysis/data/mapping.json').read_text())
        answer = mapping['answers'][0]
        controls = {}
        needle = '<div class="answer">' + escape(answer['answer'], quote=True) + '</div>'
        self.assertEqual(original.count(needle), 1)
        controls['changed Harness answer'] = original.replace(needle, '<div class="answer">CORRUPTION CONTROL</div>', 1)
        for label, pattern in (
            ('dropped Harness answer', r'<section class="answer-record" data-answer-node="abstract.task">.*?</section>'),
            ('missing Nav unknown', r'<article id="unknown-navharness-U12".*?</article>'),
        ):
            changed, count = re.subn(pattern, '', original, count=1, flags=re.S)
            self.assertEqual(count, 1, label)
            controls[label] = changed
        nav_article = re.search(r'<article id="node-navharness-method.module1.motivation".*?</article>', original, re.S)
        self.assertIsNotNone(nav_article)
        altered_article, count = re.subn(r'<dt>codeEvidence</dt><dd data-field="codeEvidence">.*?</dl></dd>', '', nav_article.group(), count=1, flags=re.S)
        self.assertEqual(count, 1)
        controls['missing Nav implementation-unknown flag'] = original[:nav_article.start()] + altered_article + original[nav_article.end():]
        for label, changed in controls.items():
            with self.subTest(label=label):
                run = self.invariant({'analysis/reading.html': changed})
                self.assertNotEqual(run.returncode, 0, label)
                self.assertIn('AssertionError', run.stderr)

    def test_all_papers_body_corruption_and_coordinated_source_rewrite_fail(self):
        from html import escape
        import re
        page = (self.site / 'all-papers.html').read_text()
        match = re.search(r'<article id="paper-harnessvln">.*?</article>', page, re.S)
        self.assertIsNotNone(match)
        article = match.group()
        needle = '<p>跨论文结果受backbone和子集影响；未独立复现实验。</p>'
        self.assertEqual(article.count(needle), 1)
        for replacement in ('', '<p>COORDINATED CORRUPTION CONTROL</p>'):
            altered = page[:match.start()] + article.replace(needle, replacement) + page[match.end():]
            run = self.invariant({'all-papers.html': altered})
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('original catalog body changed', run.stderr)
        source = self.site / 'analysis/data/navharness.mapping.json'
        original_source = source.read_bytes()
        mapping = json.loads(original_source)
        old_answer = mapping['answers'][0]['answer']
        mapping['answers'][0]['answer'] = 'COORDINATED CORRUPTION CONTROL'
        source.write_bytes(encode(mapping))
        seal_path = self.site / 'analysis/data/MULTI-PAPER-VERIFICATION.json'
        original_seal = seal_path.read_bytes()
        seal = json.loads(original_seal)
        seal['inputs']['analysis/data/navharness.mapping.json'] = hashlib.sha256(source.read_bytes()).hexdigest()
        seal_path.write_bytes(encode(seal))
        bundle = c2.assigned_json((self.site / 'analysis/data/bundle.js').read_bytes(), 'C2_DATA')
        bundle['mappingsByPaperId']['navharness'] = mapping
        reading = (self.site / 'analysis/reading.html').read_text().replace(escape(old_answer, quote=True), 'COORDINATED CORRUPTION CONTROL')
        try:
            run = self.invariant({'analysis/data/bundle.js': 'window.C2_DATA = ' + json.dumps(bundle, ensure_ascii=False) + ';\n',
                                  'analysis/reading.html': reading})
            self.assertNotEqual(run.returncode, 0)
            self.assertIn('Approved input source hash mismatch', run.stderr)
        finally:
            source.write_bytes(original_source)
            seal_path.write_bytes(original_seal)

    def test_false_verified_or_reproduced_summary_claims_are_rejected(self):
        import re
        page = (self.site / 'all-papers.html').read_text()
        for pid in ('harnessvln', 'navharness'):
            pattern = r'<!-- c2-paper-summary-' + pid + r':start -->(.*?)<!-- c2-paper-summary-' + pid + r':end -->'
            match = re.search(pattern, page, re.S)
            self.assertIsNotNone(match)
            for old, false_claim in (('未独立复现实验', '已独立复现实验'), ('既有 Stage 未改', '实现已验证')):
                with self.subTest(paper=pid, false_claim=false_claim):
                    self.assertEqual(match[1].count(old), 1)
                    changed = page[:match.start(1)] + match[1].replace(old, false_claim) + page[match.end(1):]
                    run = self.invariant({'all-papers.html': changed})
                    self.assertNotEqual(run.returncode, 0)
                    self.assertIn('approved exact analysis summary changed', run.stderr)

    def test_unchanged_fixed_public_validator_rejects_unexpected_output(self):
        root = Path(self.temp.name) / 'guarded'
        for name in (c2.SOURCE, c2.INPUT_SOURCE):
            shutil.copytree(ROOT / name, root / name)
        for name in (c2.MANIFEST, 'previews/radar-trees-c/data/graph-data.json'):
            dest = root / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, dest)
        c2.write_preview(root, root / 'dist')
        unexpected = root / 'dist' / c2.ROUTE / 'unapproved-private.json'
        unexpected.write_text('{"synthetic_control":true}')
        with self.assertRaisesRegex(ValueError, 'fixed allowlist'):
            c2.validate_output(root, root / 'dist')


if __name__ == '__main__':
    unittest.main()
