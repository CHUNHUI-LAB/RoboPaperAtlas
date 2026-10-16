# Screenshot receipt checkpoints

The screenshot capture keeps every existing save point and observation. It does
not change screenshot scenes, browser actions, budgets or visual acceptance.
The evidence storage format is `navigation-receipt-journal-v1`:

- `receipt-journal/base.json`: the complete ordinary JSON receipt at the first
  save, including the exact source head and source hashes. It is never rewritten.
- `receipt-journal/00000001.json`, `00000002.json`, etc.: immutable ordered
  checkpoint records containing JSON structural changes, the base SHA256 and
  the preceding record SHA256. The first record has no changes. An unchanged
  save still gets its own record.
- `receipt-journal/head.json`: the authoritative atomic commit pointer, with the
  base SHA256, last committed sequence, last record SHA256 and recovery tool/
  README SHA256 values.
- `receipt-journal/recover.py` and `README.md`: self-contained recovery code and
  instructions, included in every artifact and bound to their exact hashes.
- `receipt.json`: a derived ordinary JSON receipt reconstructed after capture.
  During capture, the journal is authoritative; a missing derived file does not
  mean that earlier successful saves were lost.

Each record is fully written and fsynced before its atomic rename and directory
fsync. Only then is the small head pointer written, fsynced, atomically replaced
and directory-fsynced. A successful save therefore includes all of its evidence.
An interrupted save may leave a record or temporary file beyond the head; those
files were not committed and are not replayed. A failure after replacing the head
may already have committed that checkpoint. Any writer error stops further
writing with that instance rather than guessing whether a retry is safe.

This relies on the Ubuntu runner's normal local filesystem atomic rename/fsync
contract. It does not claim to withstand malicious artifact replacement or a
filesystem that violates that contract. Hashes detect damaged or inconsistent
bytes; they do not authenticate an artifact's publisher. Preserve the workflow's
exact-head binding when deciding which artifact to review.

## Validate and reconstruct offline

Keep the whole `receipt-journal` directory together. Use its bundled
reconstruction script on Linux, with Python's standard library only:

```sh
python3 navigation-screenshots/receipt-journal/recover.py \
  --journal navigation-screenshots/receipt-journal \
  --output navigation-screenshots/receipt.json
```

The command first checks the bundled recovery script and README hashes, and the
script hash in the base's capture source metadata. It then checks the base,
every committed sequence and its linked SHA256,
operation schema and paths, and the terminal head digest before atomically
publishing any reconstructed receipt. Missing, reordered, truncated, corrupt,
duplicate-key or symlinked committed inputs fail closed. It does not repair bad
evidence, silently roll back to an earlier prefix, or mark a capture successful.
The reconstructed `status`, failures and pending human-review state come from
the original report. The command prints the receipt SHA256, byte length and
committed checkpoint count.

Resource guards reject inputs before unbounded reads: 16 KiB for the head,
2 GiB for the base, 1 GiB per checkpoint, 8 GiB for the committed base and records
combined, and 100000 checkpoints. The script and README are capped at 1 MiB and
64 KiB. The reconstructed ordinary receipt may grow beyond its initial base;
its output bound is the complete 8 GiB history budget. The writer enforces the
same evidence bounds before committing. These explicit
format limits accommodate the observed roughly 700 MB receipt and do not change
any browser acceptance threshold.

To inspect an earlier checkpoint, add `--checkpoint 123`. The entire committed
chain is still checked, including entries after checkpoint 123; a damaged later
entry cannot be hidden by selecting an earlier one. The output must be outside
the authoritative journal directory.

The workflow attempts reconstruction with `always()` after capture, and uploads
both the ordinary receipt and the journal JSON/recovery files alongside screenshots. If
capture is terminated before reconstruction, the already-uploaded journal can
be reconstructed with the same command. A hard runner termination can also stop
artifact upload itself; no local file format can guarantee an upload after the
runner is gone. This is evidence recovery, not resuming a browser session or
claiming that unexecuted scenes passed.

## Performance and invariants

The writer still snapshots every live report item on every save, including
nested aliases and in-place mutations. Immutable, process-owned marshal bytes
are used only for change detection; artifact recovery never loads marshal.
Previously committed unchanged JSON is neither rewritten nor recopied. Changed
items are compared in the JSON model, and only their changes enter the journal.
No observation is summarized, no save is deferred, and no assertion is skipped.

Memory usage includes immutable snapshots of the current report in addition to
the live report. A large newly added observation necessarily creates a large
delta. The first full base and final ordinary reconstruction still require full
I/O; performance gains concern repeated checkpoints, not eliminating all work
proportional to report size. The original complete-file writer and cache remain
available with their regression tests.

```sh
python3 -m unittest discover -s tests -p 'test_navigation_receipt*.py' -v
```

Tests cover exact reconstruction, checkpoint history, nested aliases and late
events, scalar types/order/deletion, random mutations, failures, process-exit
boundaries, committed-input corruption, and a ZIP round trip using the actual
workflow upload globs, executing only the downloaded bundle's recovery script.
The regular full validation suite also discovers them.
