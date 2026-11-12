"""Lossless checkpoint, crash recovery and artifact transport contracts."""
import ast
import copy
import importlib.util
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location('receipt_journal', ROOT / 'scripts/navigation_receipt_journal.py')
J = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(J)


def fixture():
    observation = {'route': {'node': '原始方法', 'claim': '完整原文'}, 'events': [],
                   'scroll': {'tree': 0, 'reader': 160}, 'trusted': True}
    audit = {'before': observation, 'actions': [{'before': observation, 'after': copy.deepcopy(observation)}]}
    return {'head': 'exact-source', 'status': 'starting', 'captures': [{'audit': audit}],
            'audits': [audit], 'scalars': [0, False, 0.0, -0.0, None, float('inf'), float('nan')],
            'keys': {1: 'integer', None: 'null', 'true': 'string'}, 'tuple': (1, '二')}


class JournalTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name)
        self.target = self.output / 'receipt.json'
        self.writer = J.ReceiptJournal(self.target, progress_every=0)
        self.addCleanup(self.writer.close)

    def save(self, report):
        self.writer(self.target, report)
        recovered, head = J.recover(self.writer.root)
        self.assertEqual(J.encode(recovered), J.encode(report))
        self.assertEqual(head['sequence'], self.writer.stats['writes'])
        self.assertEqual(list(self.writer.root.glob('.*.tmp')), [])
        return head

    def test_every_save_and_prior_checkpoint_is_losslessly_reconstructable(self):
        report = fixture(); snapshots = []
        for number in range(5):
            report['checkpoint'] = number
            self.save(report); snapshots.append(J.encode(report))
        for number, snapshot in enumerate(snapshots, 1):
            self.assertEqual(J.encode(J.recover(self.writer.root, number)[0]), snapshot)
        self.assertEqual(self.writer.sequence, 5)

    def test_nested_alias_in_place_and_late_events_remain_visible_everywhere(self):
        report = fixture(); self.save(report)
        shared = report['audits'][0]
        changes = [lambda: shared['before']['events'].append({'type': 'keydown', 'trusted': True}),
                   lambda: shared['actions'][0]['after']['route'].update(claim='晚到完整证据'),
                   lambda: shared.update(status='verified', cleanup={'removed': True}),
                   lambda: shared['actions'].append({'before': shared['before'], 'result': 'next action'}),
                   lambda: report.update(status='failed', error='真实失败证据')]
        for change in changes:
            change(); self.save(report)

    def test_scalar_types_signed_zero_and_nonfinite_values_do_not_false_hit(self):
        report = {'value': [0]}
        for value in [0, False, 0.0, -0.0, 1, True, 1.0, None, '1', [], {}, float('nan'), float('inf'), -float('inf')]:
            report['value'][0] = value; self.save(report)

    def test_key_reorder_add_delete_list_reorder_shrink_and_container_type_changes(self):
        report = fixture(); self.save(report)
        report['audits'][0]['actions'].reverse(); self.save(report)
        report['audits'][0]['before'] = dict(reversed(list(report['audits'][0]['before'].items()))); self.save(report)
        del report['audits'][0]['before']['scroll']; self.save(report)
        report['scalars'].reverse(); self.save(report)
        report['scalars'] = report['scalars'][2:]; self.save(report)
        report['scalars'] = {'new': 'shape'}; self.save(report)
        report['scalars'] = [1, 2, 3]; self.save(report)
        report['scalars'] = []; self.save(report)
        del report['keys']; self.save(report)
        report = dict(reversed(list(report.items()))); self.save(report)

    def test_randomized_nested_mutations_match_full_json_at_each_checkpoint(self):
        rng = random.Random(6021)
        report = {'items': [{'list': [0], 'value': 'original'}], 'status': 'starting'}
        for step in range(120):
            choice = rng.randrange(7)
            if choice == 0:
                report['items'].append({'list': [step], 'value': step})
            elif choice == 1 and report['items']:
                report['items'].pop(rng.randrange(len(report['items'])))
            elif choice == 2:
                report['items'].reverse()
            elif choice == 3 and report['items']:
                report['items'][0]['list'].append(step)
            elif choice == 4 and report['items']:
                report['items'][0]['value'] = rng.choice([False, 0, -0.0, None, '文字', {'key': step}])
            elif choice == 5:
                report = dict(reversed(list(report.items())))
            else:
                report['status'] = str(step)
            self.save(report)

    def test_unchanged_checkpoint_does_not_rewrite_base_or_copy_prior_proof(self):
        report = {'proof': [{'text': '完整证据' * 20000}], 'status': 'starting'}
        self.save(report)
        base = self.writer.root / 'base.json'; original = base.read_bytes(); stat = base.stat()
        self.save(report)
        report['status'] = 'next'; self.save(report)
        self.assertEqual(base.read_bytes(), original)
        self.assertEqual(base.stat().st_mtime_ns, stat.st_mtime_ns)
        self.assertLess((self.writer.root / '00000002.json').stat().st_size, 512)
        self.assertLess((self.writer.root / '00000003.json').stat().st_size, 512)
        self.assertGreater(base.stat().st_size, 200000)

    def test_small_nested_delta_does_not_copy_unchanged_snapshot_body(self):
        report = {'audits': [{'evidence': ['完整证据' * 5000], 'actions': [{'trusted': True}]}]}
        self.save(report)
        report['audits'][0]['actions'].append({'kind': 'release', 'trusted': True})
        self.save(report)
        self.assertLess((self.writer.root / '00000002.json').stat().st_size, 600)

    def test_materialization_matches_ordinary_receipt_bytes_and_close_preserves_history(self):
        report = fixture(); self.save(report); report['status'] = 'done'; self.save(report)
        expected = J.encode(report); self.writer.close()
        result = J.materialize(self.writer.root, self.target)
        self.assertEqual(self.target.read_bytes(), expected)
        self.assertEqual(result['receiptSha256'], J.digest(expected))
        with self.assertRaises(ValueError):
            self.writer(self.target, report)
        with self.assertRaises(ValueError):
            J.materialize(self.writer.root, self.writer.root / 'base.json')
        self.assertEqual(J.encode(J.recover(self.writer.root)[0]), expected)

    def test_failures_poison_writer_and_preserve_last_committed_prefix(self):
        report = fixture(); self.save(report); prior = J.encode(report)
        report['status'] = 'new'
        with patch.object(J.os, 'replace', side_effect=OSError('replace stopped')):
            with self.assertRaisesRegex(OSError, 'replace stopped'):
                self.writer(self.target, report)
        self.assertEqual(J.encode(J.recover(self.writer.root)[0]), prior)
        with self.assertRaises(ValueError):
            self.writer(self.target, report)

    def test_partial_write_file_sync_and_postcommit_sync_failures_have_exact_prefix(self):
        from contextlib import contextmanager
        for fault in ('partial', 'short', 'close', 'file-sync', 'head-directory-sync'):
            with self.subTest(fault=fault), tempfile.TemporaryDirectory() as directory:
                target = Path(directory) / 'receipt.json'; writer = J.ReceiptJournal(target, progress_every=0)
                self.addCleanup(writer.close)
                writer(target, {'status': 'prior'}); real_factory = J.tempfile.NamedTemporaryFile
                @contextmanager
                def broken_stream(*args, **kwargs):
                    with real_factory(*args, **kwargs) as stream:
                        class Stream:
                            name = stream.name
                            def write(self, data):
                                if fault in ('partial', 'short'):
                                    stream.write(data[:max(1, len(data)//2)])
                                    if fault == 'partial':
                                        raise OSError('partial write')
                                    return len(data) - 1
                                return stream.write(data)
                            def flush(self):
                                return stream.flush()
                            def fileno(self):
                                return stream.fileno()
                        yield Stream()
                    if fault == 'close':
                        raise OSError('close stopped')
                original_sync = J.sync_directory
                def directory_sync(path):
                    if fault == 'head-directory-sync' and json.loads((path / 'head.json').read_bytes())['sequence'] == 2:
                        raise OSError('postcommit directory sync stopped')
                    return original_sync(path)
                original_fsync = J.os.fsync
                def file_sync(fd):
                    if fault == 'file-sync':
                        raise OSError('file sync stopped')
                    return original_fsync(fd)
                with patch.object(J.tempfile, 'NamedTemporaryFile', broken_stream), patch.object(J, 'sync_directory', directory_sync), patch.object(J.os, 'fsync', file_sync):
                    with self.assertRaises(OSError):
                        writer(target, {'status': 'new'})
                recovered, head = J.recover(writer.root)
                committed = fault == 'head-directory-sync'
                self.assertEqual(recovered, {'status': 'new' if committed else 'prior'})
                self.assertEqual(head['sequence'], 2 if committed else 1)
                self.assertTrue(writer.failed)
                self.assertEqual(list(writer.root.glob('.*.tmp')), [])

    def test_corrupt_missing_truncated_reordered_committed_files_fail_closed(self):
        report = fixture(); self.save(report); report['status'] = 'new'; self.save(report)
        root = self.writer.root
        for name in ['base.json', 'head.json', '00000001.json', '00000002.json']:
            path = root / name; data = path.read_bytes()
            for mutation in ('missing', 'truncated', 'altered'):
                with self.subTest(name=name, mutation=mutation):
                    if mutation == 'missing':
                        path.unlink()
                    elif mutation == 'truncated':
                        path.write_bytes(data[:len(data)//2])
                    else:
                        path.write_bytes(data.replace(b'new', b'bad') if b'new' in data else b'{}')
                    with self.assertRaises((ValueError, KeyError)):
                        J.recover(root)
                    path.write_bytes(data)
        first, second = (root / name for name in ('00000001.json', '00000002.json'))
        one, two = first.read_bytes(), second.read_bytes(); first.write_bytes(two); second.write_bytes(one)
        with self.assertRaises(ValueError):
            J.recover(root)

    def test_earlier_checkpoint_cannot_hide_corrupt_later_committed_entry(self):
        self.save(fixture()); self.save(fixture())
        (self.writer.root / '00000002.json').write_text('{}')
        with self.assertRaises(ValueError):
            J.recover(self.writer.root, checkpoint=1)

    def test_uncommitted_orphan_does_not_advance_or_corrupt_recovery(self):
        report = fixture(); self.save(report)
        (self.writer.root / '00000002.json').write_text('torn uncommitted checkpoint')
        (self.writer.root / '.head.json.crash.tmp').write_text('torn head temporary')
        recovered, head = J.recover(self.writer.root)
        self.assertEqual(J.encode(recovered), J.encode(report)); self.assertEqual(head['sequence'], 1)

    def test_wrong_target_existing_journal_and_invalid_json_fail_without_false_commit(self):
        with self.assertRaises(FileExistsError):
            J.ReceiptJournal(self.target)
        with self.assertRaises(ValueError):
            self.writer(self.output / 'other.json', {})
        self.save(fixture())
        with self.assertRaises(TypeError):
            self.writer(self.target, {'invalid': {1, 2}})
        self.assertEqual(J.recover(self.writer.root)[1]['sequence'], 1)

    def test_duplicate_keys_invalid_head_sequence_and_unknown_schema_fail_closed(self):
        self.save(fixture()); head_path = self.writer.root / 'head.json'; raw = head_path.read_bytes()
        for mutation in ('duplicate', 'huge-sequence', 'bool-sequence', 'extra-field', 'oversized'):
            with self.subTest(mutation=mutation):
                head = json.loads(raw)
                if mutation == 'duplicate':
                    payload = raw.replace(b'{', b'{"sequence":1,', 1)
                elif mutation == 'huge-sequence':
                    head['sequence'] = 10**100; payload = J.encode(head)
                elif mutation == 'bool-sequence':
                    head['sequence'] = True; payload = J.encode(head)
                elif mutation == 'oversized':
                    payload = b' ' * 16385 + raw
                else:
                    head['unknown'] = 1; payload = J.encode(head)
                head_path.write_bytes(payload)
                with self.assertRaises(ValueError):
                    J.recover(self.writer.root)
                head_path.write_bytes(raw)

    def test_bundled_recovery_tool_readme_and_source_binding_are_verified(self):
        report = fixture()
        report['captureSources'] = {'scripts/navigation_receipt_journal.py': J.digest(Path(J.__file__).read_bytes())}
        self.save(report)
        for name in ('recover.py', 'README.md'):
            path = self.writer.root / name; raw = path.read_bytes()
            path.write_bytes(raw + b'\nchanged')
            with self.assertRaisesRegex(ValueError, 'version integrity'):
                J.recover(self.writer.root)
            path.write_bytes(raw)
        # A coherent head cannot rebind the base's recorded source version.
        root = self.writer.root; base = json.loads((root / 'base.json').read_bytes())
        base['captureSources']['scripts/navigation_receipt_journal.py'] = '0' * 64
        payload = J.encode(base); (root / 'base.json').write_bytes(payload)
        head = json.loads((root / 'head.json').read_bytes()); head['baseSha256'] = J.digest(payload)
        (root / 'head.json').write_bytes(J.encode(head))
        with self.assertRaisesRegex(ValueError, 'original capture source'):
            J.recover(root)

    def test_explicit_size_limits_reject_before_reading_or_committing_large_evidence(self):
        self.save(fixture()); root = self.writer.root
        for name, constant in [('base.json', 'MAX_BASE_BYTES'), ('00000001.json', 'MAX_CHECKPOINT_BYTES')]:
            with self.subTest(name=name), patch.object(J, constant, 10):
                with self.assertRaisesRegex(ValueError, 'oversized'):
                    J.recover(root)
        with patch.object(J, 'MAX_HISTORY_BYTES', 10):
            with self.assertRaisesRegex(ValueError, 'history exceeds'):
                J.recover(root)
        # A sparse oversized head is rejected by stat, not read into memory.
        head = root / 'head.json'; prior = head.read_bytes()
        with head.open('wb') as stream:
            stream.truncate(2**30)
        with patch.object(Path, 'open', side_effect=AssertionError('must reject before opening')):
            with self.assertRaisesRegex(ValueError, 'byte limit'):
                J.read_regular(head)
        head.write_bytes(prior)
        with patch.object(J, 'MAX_CHECKPOINT_BYTES', 10):
            with self.assertRaisesRegex(ValueError, 'byte limit'):
                self.writer(self.target, {'status': 'new'})
        self.assertEqual(J.recover(root)[1]['sequence'], 1)

    def test_derived_receipt_can_grow_beyond_initial_base_limit(self):
        report = {'proof': []}; self.save(report)
        with patch.object(J, 'MAX_BASE_BYTES', 100), patch.object(J, 'MAX_CHECKPOINT_BYTES', 4096), patch.object(J, 'MAX_HISTORY_BYTES', 8192):
            report['proof'].append('new complete evidence' * 30)
            self.save(report)
            J.materialize(self.writer.root, self.target)
            self.assertGreater(self.target.stat().st_size, J.MAX_BASE_BYTES)
            self.assertEqual(self.target.read_bytes(), J.encode(report))

    def test_symlink_artifact_and_invalid_operation_paths_are_rejected(self):
        self.save(fixture()); base = self.writer.root / 'base.json'
        copy_path = self.output / 'copy.json'; copy_path.write_bytes(base.read_bytes()); base.unlink(); base.symlink_to(copy_path)
        with self.assertRaises(ValueError):
            J.recover(self.writer.root)
        for operation in [['set', ['items', -1], 1], ['tail', ['items'], True, []],
                          ['keys', [], ['missing']], ['set', [], {}], ['set', ['items', True], 1],
                          ['unknown', [], None]]:
            with self.subTest(operation=operation), self.assertRaises(ValueError):
                J.apply_operations({'items': [0]}, [operation])

    def test_workflow_uploaded_globs_round_trip_all_committed_evidence(self):
        report = fixture(); self.save(report); report['audits'][0]['actions'].append({'trusted': True}); self.save(report)
        J.materialize(self.writer.root, self.target)
        (self.output / 'scene.png').write_bytes(b'PNG-test-fixture')
        (self.writer.root / '.head.json.incomplete.tmp').write_text('not committed')
        workflow = (ROOT / '.github/workflows/navigation-screenshots.yml').read_text()
        globs = [line.strip().replace('navigation-screenshots/', '') for line in workflow.splitlines()
                 if line.strip().startswith('navigation-screenshots/')]
        files = sorted(set(path for pattern in globs for path in self.output.glob(pattern)))
        self.assertIn(self.writer.root / 'base.json', files)
        self.assertIn(self.writer.root / 'head.json', files)
        self.assertIn(self.writer.root / '00000002.json', files)
        self.assertIn(self.writer.root / 'recover.py', files)
        self.assertIn(self.writer.root / 'README.md', files)
        self.assertFalse(any(path.name.startswith('.') for path in files))
        archive = self.output / 'upload.zip'
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
            for path in files:
                zipped.write(path, path.relative_to(self.output))
        extracted = self.output / 'download'
        with zipfile.ZipFile(archive) as zipped:
            zipped.extractall(extracted)
        rebuilt = extracted / 'reconstructed.json'
        result = subprocess.run([sys.executable, str(extracted / 'receipt-journal/recover.py'),
                                 '--journal', str(extracted / 'receipt-journal'), '--output', str(rebuilt)],
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(rebuilt.read_bytes(), self.target.read_bytes())
        self.assertIn('if: always()\n        run: python3 scripts/navigation_receipt_journal.py', workflow)
        self.assertIn('timeout-minutes: 120', workflow)

    def test_capture_keeps_all_existing_save_sites_and_binds_journal_source(self):
        source = (ROOT / 'scripts/navigation_screenshots.py').read_text(); tree = ast.parse(source)
        calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'save']
        self.assertEqual(len(calls), 113)  # 103 original + 1 paint + 9 disclosure checkpoints
        self.assertIn("receipt_cache = ReceiptJournal(out / 'receipt.json')", source)
        self.assertIn("report['captureSources']['scripts/navigation_receipt_journal.py'] = sha('scripts/navigation_receipt_journal.py')", source)


class ProcessCrashTests(unittest.TestCase):
    def test_initial_base_and_first_commit_interruption_never_looks_like_complete_receipt(self):
        code = r'''
import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import navigation_receipt_journal as j
root=Path(sys.argv[2]);writer=j.ReceiptJournal(root/'receipt.json',progress_every=0)
target,stage=sys.argv[3:];original=j.atomic_write
def stop(path,chunks):
    if path.name!=target:return original(path,chunks)
    replace=j.os.replace
    def replace_stop(source,destination):
        if stage=='before-replace':os._exit(73)
        replace(source,destination)
        if stage=='after-replace':os._exit(73)
    j.os.replace=replace_stop
    return original(path,chunks)
j.atomic_write=stop
writer(root/'receipt.json',{'status':'starting','proof':['complete']})
'''
        for target in ('base.json', '00000001.json', 'head.json'):
            for stage in ('before-replace', 'after-replace'):
                with self.subTest(target=target, stage=stage), tempfile.TemporaryDirectory() as directory:
                    result = subprocess.run([sys.executable, '-c', code, str(ROOT / 'scripts'), directory, target, stage], timeout=15)
                    self.assertEqual(result.returncode, 73)
                    root = Path(directory) / 'receipt-journal'
                    if target == 'head.json' and stage == 'after-replace':
                        recovered, head = J.recover(root)
                        self.assertEqual(recovered, {'status': 'starting', 'proof': ['complete']})
                        self.assertEqual(head['sequence'], 1)
                    else:
                        with self.assertRaises(ValueError):
                            J.recover(root)

    def test_real_process_exit_at_write_fsync_replace_and_directory_sync_boundaries(self):
        code = r'''
import os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1]);import navigation_receipt_journal as j
root=Path(sys.argv[2]); writer=j.ReceiptJournal(root/'receipt.json',progress_every=0)
writer(root/'receipt.json',{'status':'prior','proof':['complete']})
target,stage=sys.argv[3:]
original=j.atomic_write
def stop(path,chunks):
    if path.name!=target:return original(path,chunks)
    if stage=='before-write':os._exit(73)
    replace=j.os.replace;sync=j.sync_directory;fsync=j.os.fsync
    def replace_stop(source,destination):
        if stage=='before-replace':os._exit(73)
        replace(source,destination)
        if stage=='after-replace':os._exit(73)
    def sync_stop(directory):
        if stage=='before-directory-sync':os._exit(73)
        sync(directory)
        if stage=='after-directory-sync':os._exit(73)
    def fsync_stop(fd):
        if stage=='before-file-sync':os._exit(73)
        fsync(fd)
        if stage=='after-file-sync':os._exit(73)
    j.os.replace=replace_stop;j.sync_directory=sync_stop;j.os.fsync=fsync_stop
    return original(path,chunks)
j.atomic_write=stop
writer(root/'receipt.json',{'status':'new','proof':['complete','new operation']})
'''
        for target in ('00000002.json', 'head.json'):
            for stage in ('before-write', 'before-file-sync', 'after-file-sync', 'before-replace', 'after-replace',
                          'before-directory-sync', 'after-directory-sync'):
                with self.subTest(target=target, stage=stage), tempfile.TemporaryDirectory() as directory:
                    result = subprocess.run([sys.executable, '-c', code, str(ROOT / 'scripts'), directory, target, stage], timeout=15)
                    self.assertEqual(result.returncode, 73)
                    recovered, head = J.recover(Path(directory) / 'receipt-journal')
                    committed = target == 'head.json' and stage in ('after-replace', 'before-directory-sync', 'after-directory-sync')
                    self.assertEqual(head['sequence'], 2 if committed else 1)
                    self.assertEqual(recovered, {'status': 'new', 'proof': ['complete', 'new operation']} if committed
                                     else {'status': 'prior', 'proof': ['complete']})


if __name__ == '__main__':
    unittest.main()
