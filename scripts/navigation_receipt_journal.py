"""Lossless screenshot checkpoints: immutable JSON base and atomic delta journal.

This is an evidence format, not a browser-session resume mechanism. Every
successful save is committed by head.json; uncommitted files are never replayed.
Only JSON is read from artifacts. marshal is confined to fresh process-owned
snapshots to detect nested/aliased mutations without re-encoding old evidence.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import marshal
import os
from pathlib import Path
import re
import tempfile
import time

FORMAT = 'navigation-receipt-journal-v1'
# Evidence limits, not screenshot acceptance thresholds. The observed 700 MB
# receipt fits the base bound; ordinary per-operation deltas are much smaller.
MAX_BASE_BYTES = 2 * 1024 ** 3
MAX_CHECKPOINT_BYTES = 1024 ** 3
MAX_HISTORY_BYTES = 8 * 1024 ** 3
MAX_CHECKPOINTS = 100000
RECOVERY_README = '''# Recover screenshot evidence offline

Keep this entire directory together. No package installation is needed.
Use Python 3.9+ on Linux from a trusted source. From the containing artifact directory:

    python3 receipt-journal/recover.py --journal receipt-journal --output receipt.json

Add --checkpoint N to reconstruct an earlier save. All committed checkpoints
are still verified. The derived output must be outside this journal directory.
The command checks the bundled recovery script/README version hashes, JSON
base, checkpoint sequence/hash chain and head before publishing a receipt.
The original source script hash is also checked when present in captureSources.
Do not run scripts from untrusted artifacts: hashes detect damage, not publisher
identity. Obtain this bundle from the expected exact-head workflow artifact.

base.json and every numbered JSON record up to head.json's sequence are required.
Later records and temporary files are uncommitted and are not replayed. Failure
or a missing head is not success; no incomplete receipt is silently repaired.
Keep the original capture status and human-review requirement. This tool
recovers evidence; it cannot resume the browser or complete unexecuted scenes.
Hard runner termination may prevent upload itself. Locally committed bytes
cannot guarantee a remote artifact exists after the runner is gone.

Format: navigation-receipt-journal-v1. Limits: head 16 KiB, base 2 GiB, each
checkpoint 1 GiB, committed base+records 8 GiB, 100000 checkpoints. These bound
artifact parsing; they do not relax or replace any screenshot acceptance gate.
'''


def encode(value):
    return (json.dumps(value, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def decode(data):
    def object_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError('Duplicate receipt JSON object key')
            value[key] = item
        return value
    return json.loads(data, object_pairs_hook=object_pairs)


def sync_directory(path):
    descriptor = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def size_limit(path):
    if path.name == 'head.json':
        return 16384
    if path.name == 'base.json':
        return MAX_BASE_BYTES
    if path.name == 'recover.py':
        return 1024 ** 2
    if path.name == 'README.md':
        return 65536
    if re.fullmatch(r'[0-9]{8,}\.json', path.name):
        return MAX_CHECKPOINT_BYTES
    return MAX_BASE_BYTES


def atomic_write(path, chunks, limit=None):
    """Commit only fully written, flushed bytes; return their SHA256 and length."""
    temporary = None
    checksum, size = hashlib.sha256(), 0
    if limit is None:
        limit = size_limit(path)
    try:
        with tempfile.NamedTemporaryFile(mode='wb', dir=path.parent,
                                         prefix='.' + path.name + '.', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            for data in chunks:
                if size + len(data) > limit:
                    raise ValueError('Receipt evidence exceeds explicit byte limit: ' + path.name)
                if stream.write(data) != len(data):
                    raise OSError('Incomplete receipt journal write')
                checksum.update(data)
                size += len(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        sync_directory(path.parent)
        return checksum.hexdigest(), size
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def report_chunks(report):
    """Bound JSON encoding memory by one top-level list item, as in the old cache."""
    yield b'{'
    for number, (key, value) in enumerate(report.items()):
        if number:
            yield b','
        yield encode(key).rstrip(b'\n') + b':'
        if type(value) is list:
            yield b'['
            for index, item in enumerate(value):
                if index:
                    yield b','
                yield encode(item).rstrip(b'\n')
            yield b']'
        else:
            yield encode(value).rstrip(b'\n')
    yield b'}\n'


def changes(old, new, path, operations):
    """JSON-model diff; preserve key order and scalar types, including signed zero."""
    if type(old) is dict and type(new) is dict:
        for key in new:
            if key in old:
                changes(old[key], new[key], path + [key], operations)
            else:
                operations.append(['set', path + [key], new[key]])
        if list(old) != list(new):
            operations.append(['keys', path, list(new)])
    elif type(old) is list and type(new) is list:
        for index in range(min(len(old), len(new))):
            changes(old[index], new[index], path + [index], operations)
        if len(new) != len(old):
            operations.append(['tail', path, min(len(old), len(new)), new[len(old):]])
    elif type(old) is not type(new) or (repr(old) != repr(new) if type(old) is float else old != new):
        operations.append(['set', path, new])


def slots(report):
    for key, value in report.items():
        if type(value) is list:
            for index, item in enumerate(value):
                yield (key, index), item
        else:
            yield (key,), value


class ReceiptJournal:
    """Single-writer journal. Every call commits, even when the report is unchanged.

    Snapshots are immutable process-owned bytes. No object identity, append-only
    assumption or skipped save is used. On any I/O failure this instance is
    poisoned: the committed prefix can be recovered but no uncertain write is
    retried. Artifacts and their committed history are never removed by close.
    """
    def __init__(self, path, progress_every=50):
        self.path = Path(path)
        self.root = self.path.parent / 'receipt-journal'
        self.root.mkdir()  # Never append to an unrelated or prior run.
        sync_directory(self.root.parent)
        self.recovery_hash, _ = atomic_write(self.root / 'recover.py', [Path(__file__).read_bytes()])
        self.readme_hash, _ = atomic_write(self.root / 'README.md', [RECOVERY_README.encode('utf-8')])
        self.previous, self.layout = {}, {}
        self.history_bytes = 0
        self.sequence, self.last_hash, self.base_hash = 0, None, None
        self.closed, self.failed = False, False
        self.progress_every = progress_every
        self.stats = dict(writes=0, bytes=0, totalSeconds=0.0, diffSeconds=0.0, publishSeconds=0.0)

    def __call__(self, path, report):
        if self.closed or self.failed or Path(path) != self.path:
            raise ValueError('Receipt journal is closed, failed or changed target')
        if type(report) is not dict or any(type(key) is not str for key in report):
            raise TypeError('Receipt journal requires original named report fields')
        started = time.perf_counter()
        try:
            if self.sequence >= MAX_CHECKPOINTS:
                raise ValueError('Receipt checkpoint count exceeds explicit limit')
            staged, operations = {}, []
            layout = {key: len(value) if type(value) is list else None for key, value in report.items()}
            # Prepare top-level containers before item-level deltas.
            if self.base_hash is not None:
                for key, length in layout.items():
                    if key not in self.layout or (length is None) != (self.layout[key] is None):
                        operations.append(['set', [key], [] if length is not None else None])
                    if length is not None and (key not in self.layout or self.layout[key] is None or length != self.layout[key]):
                        old_length = self.layout.get(key) or 0
                        operations.append(['tail', [key], min(old_length, length), [None] * max(0, length - old_length)])
            for slot, value in slots(report):
                frozen = marshal.dumps(value, 4)
                prior = self.previous.get(slot)
                if prior is not None and prior == frozen:
                    staged[slot] = prior
                    continue
                staged[slot] = frozen
                # JSON normalization preserves the original encoder's tuples,
                # numeric object keys, non-finite floats, and insertion order.
                new = decode(encode(marshal.loads(frozen)))
                if self.base_hash is not None:
                    if prior is None:
                        operations.append(['set', list(slot), new])
                    else:
                        changes(decode(encode(marshal.loads(prior))), new, list(slot), operations)
            if self.base_hash is not None and list(layout) != list(self.layout):
                operations.append(['keys', [], list(layout)])
            self.stats['diffSeconds'] += time.perf_counter() - started
            publish = time.perf_counter()
            if self.base_hash is None:
                self.base_hash, size = atomic_write(self.root / 'base.json', report_chunks(report))
                self.stats['bytes'] += size
                self.history_bytes += size
            sequence = self.sequence + 1
            entry = encode(dict(format=FORMAT, sequence=sequence, baseSha256=self.base_hash,
                                previousSha256=self.last_hash, operations=operations))
            if self.history_bytes + len(entry) > MAX_HISTORY_BYTES:
                raise ValueError('Receipt history exceeds explicit byte limit')
            entry_hash, size = atomic_write(self.root / ('%08d.json' % sequence), [entry])
            self.stats['bytes'] += size
            head = dict(format=FORMAT, baseSha256=self.base_hash, sequence=sequence, lastSha256=entry_hash,
                        recoverySha256=self.recovery_hash, readmeSha256=self.readme_hash)
            _, size = atomic_write(self.root / 'head.json', [encode(head)])
            self.stats['bytes'] += size
            self.previous, self.layout = staged, layout
            self.sequence, self.last_hash = sequence, entry_hash
            self.history_bytes += len(entry)
            self.stats['writes'] += 1
            self.stats['publishSeconds'] += time.perf_counter() - publish
        except BaseException:
            self.failed = True
            raise
        finally:
            self.stats['totalSeconds'] += time.perf_counter() - started
        if self.progress_every and self.sequence % self.progress_every == 0:
            print('receipt_checkpoint ' + json.dumps(dict(self.stats, format=FORMAT), separators=(',', ':')), flush=True)

    def close(self):
        self.previous.clear()
        self.closed = True


def resolve(document, path):
    value = document
    if type(path) is not list:
        raise ValueError('Invalid receipt operation path')
    for part in path:
        if type(value) is dict and type(part) is str and part in value:
            value = value[part]
        elif type(value) is list and type(part) is int and 0 <= part < len(value):
            value = value[part]
        else:
            raise ValueError('Receipt operation path does not exist')
    return value


def apply_operations(document, operations):
    if type(operations) is not list:
        raise ValueError('Invalid receipt operations')
    for operation in operations:
        if type(operation) is not list or not operation:
            raise ValueError('Invalid receipt operation')
        kind = operation[0]
        if kind == 'set' and len(operation) == 3:
            _, path, value = operation
            if not path:
                raise ValueError('Receipt root cannot be replaced')
            parent = resolve(document, path[:-1]); key = path[-1]
            if not ((type(parent) is dict and type(key) is str) or
                    (type(parent) is list and type(key) is int and 0 <= key < len(parent))):
                raise ValueError('Invalid receipt set target')
            parent[key] = value
        elif kind == 'keys' and len(operation) == 3:
            _, path, keys = operation; target = resolve(document, path)
            if (type(target) is not dict or type(keys) is not list or
                    any(type(key) is not str or key not in target for key in keys) or len(set(keys)) != len(keys)):
                raise ValueError('Invalid receipt object keys')
            ordered = {key: target[key] for key in keys}
            target.clear(); target.update(ordered)
        elif kind == 'tail' and len(operation) == 4:
            _, path, start, values = operation; target = resolve(document, path)
            if type(target) is not list or type(start) is not int or not 0 <= start <= len(target) or type(values) is not list:
                raise ValueError('Invalid receipt list tail')
            target[start:] = values
        else:
            raise ValueError('Unknown receipt operation')


def read_regular(path):
    if path.is_symlink() or not path.is_file():
        raise ValueError('Missing or non-regular receipt journal file: ' + path.name)
    limit = size_limit(path)
    size = path.stat().st_size
    if size > limit:
        raise ValueError('Receipt evidence exceeds explicit byte limit: ' + path.name)
    with path.open('rb') as stream:
        data = stream.read(size + 1)
    if len(data) != size:
        raise ValueError('Receipt file size changed during read: ' + path.name)
    return data


def recover(root, checkpoint=None):
    """Validate the entire committed chain, returning the selected full checkpoint.

    An explicit earlier checkpoint never hides a corrupt later committed entry.
    Files beyond the head are uncommitted orphans, not evidence of a passed save.
    """
    root = Path(root)
    if root.is_symlink() or not root.is_dir():
        raise ValueError('Invalid receipt journal directory')
    head_bytes = read_regular(root / 'head.json')
    head = decode(head_bytes)
    if (type(head) is not dict or head.get('format') != FORMAT or type(head.get('sequence')) is not int or not 1 <= head['sequence'] <= MAX_CHECKPOINTS
            or set(head) != {'format', 'baseSha256', 'sequence', 'lastSha256', 'recoverySha256', 'readmeSha256'}
            or any(type(head.get(key)) is not str or not re.fullmatch('[0-9a-f]{64}', head[key]) for key in ('baseSha256', 'lastSha256', 'recoverySha256', 'readmeSha256'))):
        raise ValueError('Invalid receipt journal head')
    if (digest(read_regular(root / 'recover.py')) != head['recoverySha256']
            or digest(Path(__file__).read_bytes()) != head['recoverySha256']
            or digest(read_regular(root / 'README.md')) != head['readmeSha256']):
        raise ValueError('Receipt recovery tool version integrity check failed; use the bundled recover.py')
    # Bound a corrupt sequence by actual directory entries before iterating.
    available = sum(1 for path in root.iterdir() if re.fullmatch(r'[0-9]{8,}\.json', path.name))
    if head['sequence'] > available:
        raise ValueError('Missing committed receipt checkpoints')
    committed = [root / 'base.json'] + [root / ('%08d.json' % number) for number in range(1, head['sequence'] + 1)]
    history_bytes = 0
    for path in committed:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > size_limit(path):
            raise ValueError('Missing, non-regular or oversized committed receipt file: ' + path.name)
        history_bytes += path.stat().st_size
    if history_bytes > MAX_HISTORY_BYTES:
        raise ValueError('Receipt history exceeds explicit byte limit')
    if checkpoint is None:
        checkpoint = head['sequence']
    if type(checkpoint) is not int or not 1 <= checkpoint <= head['sequence']:
        raise ValueError('Checkpoint outside committed receipt history')
    base = read_regular(root / 'base.json')
    if digest(base) != head['baseSha256']:
        raise ValueError('Receipt base integrity check failed')
    document = decode(base)
    if type(document) is not dict:
        raise ValueError('Receipt base must be an object')
    sources = document.get('captureSources', {})
    if type(sources) is not dict:
        raise ValueError('Invalid receipt capture source metadata')
    source_hash = sources.get('scripts/navigation_receipt_journal.py')
    if source_hash is not None and source_hash != head['recoverySha256']:
        raise ValueError('Receipt recovery tool differs from original capture source')
    del base
    previous, selected = None, None
    for number in range(1, head['sequence'] + 1):
        payload = read_regular(root / ('%08d.json' % number))
        entry = decode(payload)
        if (type(entry) is not dict or entry.get('format') != FORMAT or type(entry.get('sequence')) is not int or entry['sequence'] != number
                or set(entry) != {'format', 'sequence', 'baseSha256', 'previousSha256', 'operations'}
                or entry.get('baseSha256') != head['baseSha256'] or entry.get('previousSha256') != previous):
            raise ValueError('Receipt checkpoint chain integrity check failed')
        previous = digest(payload)
        apply_operations(document, entry.get('operations'))
        if number == checkpoint and number != head['sequence']:
            selected = encode(document)
    if previous != head['lastSha256']:
        raise ValueError('Receipt checkpoint digest integrity check failed')
    return (decode(selected) if selected is not None else document), head


def materialize(root, output, checkpoint=None):
    document, head = recover(root, checkpoint)
    output = Path(output)
    # Do not let a typo overwrite any part of the authoritative journal.
    if output.resolve().is_relative_to(Path(root).resolve()):
        raise ValueError('Reconstructed receipt must be outside the journal')
    # A small base can grow through many valid deltas. Its derived full output
    # is bounded by the complete evidence history, not the initial-base limit.
    checksum, size = atomic_write(output, report_chunks(document), limit=MAX_HISTORY_BYTES)
    return dict(format=FORMAT, committedCheckpoints=head['sequence'], checkpoint=checkpoint or head['sequence'],
                receiptSha256=checksum, receiptBytes=size)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--journal', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--checkpoint', type=int)
    args = parser.parse_args()
    print(json.dumps(materialize(args.journal, args.output, args.checkpoint), sort_keys=True))


if __name__ == '__main__':
    main()
