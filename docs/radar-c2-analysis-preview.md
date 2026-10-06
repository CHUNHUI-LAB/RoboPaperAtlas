# C2 isolated review candidate

Status: local candidate pending real-browser acceptance. Not published. Model, in-memory DOM and static layout checks are not browser, touch or visual acceptance.

## Build and scope

The opt-in CI wrapper `python3 scripts/build_previews.py` appends `review/radar-c2-analysis/`. In this C2 integration, `scripts/build.py` and `scripts/validate.py` remain byte-identical to the rebased main; running `build.py` alone does not add C2. There is no formal home navigation link or new formal reading Stage.

The existing `review/radar-trees-c/` route, its exact nine-file manifest and weekly archive remain intact. This candidate is a separately namespaced data-model and interaction experiment, not only a CSS skin of the old C view.

First integration history: the initial integration used main `880d4fa46d01a5288515062a4cf1d6f34de65903`, tree `69d3b2098220db004cbeb4bacb9200c7bfdc948e`, including the submission-maintenance changes in PR #24. That historical source identity was independently reconstructed from 1,063 Git blobs; it is not the current rebased baseline. The sealed integration proofs preserve all 105 PR #18 added/modified source paths for this release; 105 is not a paper count or a permanent freeze on their evolving builders and tests.

Current rebased integration baseline: main `352b424965f685359a56e5c3b2c104fb7dab3c6b`, tree `941c810b152e54afed8464149be2d272b5401fd1`, with all 1,068 tracked source paths independently verified. This main includes the five-file reader TOC-focus repair merged in PR #27 and the three-file inset focus-ring repair merged in PR #28. The PR #28 repair changes only the reader preview builder, its Python test and the reader UI document; it leaves JavaScript unchanged. All these reader paths already belong to the baseline and are not C2 additions. All 18 daily changed source paths from PR #25 and all eight submission-maintenance paths from PR #24 are preserved byte-for-byte; these are path counts, not paper counts. Relative to this main, the candidate scope remains the same three appended lines in `scripts/build_previews.py` plus 34 added paths, with no deletions. Any later main must be reconciled before publication.

Historical reader-rebase baseline: main `122a7daa35e61b20b04c827f7b579981800c01a6`, tree `c718c4f923ac4eaae5eec6c99e24946fa2e095ba`, had 1,068 tracked paths and included PR #27. Its sealed C2 candidate tree `b0c990b3d631a72b9fd64e0cf09c42f2aba2dc88` and verification are historical evidence, not this PR #28-rebased candidate.

Historical daily-rebase baseline: main `1a27cc16d5acb2e8df54ddde880016aa134b352c`, tree `6ed865ef741692c40282a2d67f5b45a382488054`, had 1,065 tracked paths. Its separately sealed C2 CI-contract revision is preserved as historical evidence and is not the current baseline.

## Coverage and scientific boundaries

Canonical sets in the unchanged old graph independently give:

- baseline: 39 papers; the new typed literature/Challenge trees cover exactly these 39
- old weekly: 6 candidates, overlapping baseline by 2
- total unique across these ranges: 43
- four weekly-only candidates are outside the rebuilt trees and analysis: `arxiv:2609.37187`, `arxiv:2609.37353`, `arxiv:2609.39166`, `arxiv:2609.39579`

The four records are retained in the old weekly route with explicit links and coverage notices from every new HTML entry, including the no-JavaScript alternative. No mappings were invented to extend the new tree's denominator to 43.

At this release baseline, the formal catalog has 95 records, the reports registry has 21 records, and there are 12 imported Stage slots. Their source bytes remain unchanged by this C2 integration. These are dated release measurements, not permanent current-catalog limits. Baseline records and all their existing state are copied without scientific reinterpretation. Typed seed additions are editorial comparison structures supported by source fields; shared concepts do not imply shared code, a common implementation or academic inheritance.

Only HarnessVLN has the filled analysis sample: 59 original template nodes, 13 explicitly marked repeated template instances, 47 answers and 6 unresolved questions. The 47 comprise 40 evidence-linked answers and 7 author-claim-only answers. The unresolved set retains 5 not-reported items plus 1 source-missing item, including its empty code locator array. Other 38 papers retain honest pending templates, without copied sample answers. Evidence-linked does not mean independently reproduced. No existing Stage state is promoted.

## Publication boundary and reproducibility

`radar_c2_preview.py` defines a code-fixed public allowlist of 14 files. The manifest cannot expand it. Only runtime HTML, CSS, JavaScript and their bundled data enter the route. Tests, frozen source JSON, provenance seals, helper scripts, source snapshots, review reports, logs and reference images are not publicly copied. Review fixtures live under `tests/fixtures/radar-c2-analysis/`, outside the public route.

The manifest seals exact runtime and review-input SHA-256 values. Preflight validates the sources and destination before `build.py` can clear output. It rejects changed bytes, missing/extra files, symlinks, FIFOs, source-directory output overlap, and manifest allowlist expansion. The writer atomically replaces each file, so an existing hardlink is not truncated, then verifies the exact output file/directory set and bytes. The manifest preserves the real-browser `NOT_RUN` state.

Local script and stylesheet URL versions in the new root entry are derived from their actual file hashes, preventing a new entry from requesting stale resources under the same URL. No remote library, build-time scientific inference or network execution is introduced.

The unchanged 31-check typed-tree suite and 38-check C2 suite are invoked from Python test discovery in temporary copies. They do not generate reports in frozen source directories. Two new-copy-only integration regressions check explicit C2 entry at scroll zero and restoration of the prior tree scroll, while history-based entry does not force zero. The new root coverage notice stays outside the main/header elements hidden during C2, so the old-weekly link remains accessible. Additional tests cover the integration, archived coverage, immutable history, dynamic source/state preservation, safe publication and output equivalence. Existing CI workflow discovery already runs them; workflows and package dependencies are unchanged.

The current implementation also checks that the normal old build plus its existing previews and the new wrapper differ only by the new 14-file route. This protects all existing generated reader/Atlas/Radar/report outputs, beyond a mere page-count comparison.

The prior sealed daily-rebased release measured 278 wrapper-output files and 264 original-build files, preserving all original paths and hashes with exactly 14 C2 files added. Its 610 Python / 306 static Node passes, and the later sealed CI-contract revision's 625 Python / 40 C2 / 306 static Node passes, remain historical evidence for those earlier trees. The sealed PR #27 reader-rebased C2 tree `b0c990b3d631a72b9fd64e0cf09c42f2aba2dc88` subsequently measured 626 Python / 40 C2 / 318 static Node passes and 265 original-build / 279 wrapper-output files. None of those results is claimed as full-suite verification for this PR #28-rebased candidate. The current candidate preserves the corrected C2 test contract and updates this document; the three inset focus-ring repair paths come only from the new main. Fresh full-suite results, independently derived output counts, repeated-build hashes and exact source identities are recorded in this candidate's separate release evidence after these document bytes are fixed. Formal data, scientific evidence, the original protection fixture and all frozen C2 inputs remain unchanged.

PR #26's earlier head `52277197d4a992c995d0f634335f159084d101b8` had a successful remote CI run `37450596309` for the earlier reader-rebased tree. That historical success does not validate this new candidate. Publication, remote CI for this exact candidate and real-browser acceptance remain NOT_RUN.

## Permanent CI versus release provenance

`tests/fixtures/radar-c2-protection.json` retains its original bytes and historical
base identity. The sealed per-release proofs still compare all 105 PR #18 paths,
all rebased-main sources and the formal state against that release's inputs. A
later reader fix, catalog addition or reviewed import does not invalidate that
historical proof and must not be blocked solely by an earlier builder hash or
an old current-state total.

Permanent C2 CI applies distinct scopes:

- Exact historical hashes still protect the fixture itself, the PR #18 reviewed
  v2 raw chunks, policies and historical facts/presentation evidence, plus the old-C graph-data
  JSON/JavaScript and dated weekly archive. Old-C presentation files and their
  manifest may receive separately reviewed UI repairs under the existing exact
  nine-file payload validator and the dynamic no-side-effect guard; C2 does not
  permanently freeze their earlier hashes. Existing independent v1/v2
  report-security and immutable-history tests remain unchanged. Current pending
  gate evidence, migration plans and print-verification metadata remain dynamic;
  their report identities/bytes and print content retain the existing v2
  validators/tests, rather than a blanket C2 workflow-metadata freeze
- C2's 14 public files, 15 review inputs, science seals and snapshot-scoped
  39/6/43 coverage remain exact. Evolving the live catalog does not expand that
  reviewed snapshot or manufacture new scientific mappings
- Current builders, shared code, tests, formal catalog, registry and Stage
  state may evolve through independent reviewed work. CI hashes all current
  input files and derives paper/report/imported-Stage counts before C2
  generation, then requires identical sources and counts afterward. Added and
  deleted source inputs, future namespaces and directory-to-symlink replacements
  are checked too. Only exact generated output destinations, Git/dependency
  directories and Python bytecode are excluded. No historical builder SHA or dated
  catalog/report/Stage total is imposed on the current repository
- The real baseline build and integrated wrapper are enclosed by the same
  pre/post guard, captured before either build starts. Their output comparison
  still permits exactly the isolated C2 route. It does not reuse a snapshot
  taken after generation has already changed a source

Temporary-copy mutation controls run the actual C2 writer with mutations during
its output-validation step. They prove rejection of source edits, source
addition/deletion (including new namespaces), source-directory symlink replacement,
Stage promotion, and artifact metadata rewrites that leave
counts unchanged. Separate preflight controls corrupt raw history and the old
weekly archive before generation; exact reviewed hashes reject both before the
writer runs. Positive controls validate an independent synthetic catalog
addition and a synthetic separately approved formal import with the normal
catalog/report validators, and allow a changed preview builder before generation.
The import control reuses exact pinned report bytes solely in a temporary
repository; it does not approve the real pending candidate or alter its provenance. They preserve the frozen C2 payload exactly.
A gate-evidence control updates temporary workflow metadata without promoting
pending status or claiming browser/print acceptance, and revalidates all exact
v2 sources. An additional positive control changes old-C CSS/JavaScript with synchronized
entry cache hashes and a reviewed manifest, while preserving its graph-data and
weekly snapshot. The stale-manifest form still fails the actual guard.
The earlier sealed release evidence exercised the real independent five-file
reader TOC-focus repair in a temporary combined repository. That repair is now
merged in PR #27, and the subsequent three-file inset focus-ring repair is
merged in PR #28. Both belong to the current main baseline. Fresh validation
runs on this exact combined source tree; the C2 patch does not repeat either
reader repair. The 105-path PR #18 release comparison is against the current
base, with PR #27 and PR #28 reader builder/test evolution separately
attributed; only the 90 historical raw/policy/evidence paths remain
permanently pinned by C2.
Other repository tests still contain their own dated
catalog/report totals and import boundaries; this correction removes the C2
universal freeze only, and does not claim future imports pass those separate
contracts without their own review.

## Validation commands

Use the repository's existing Node 24 and lockfile dependency preparation. After the existing math preparation step:

```sh
python3 scripts/assemble_frontier.py
python3 scripts/reports.py
python3 -m unittest discover -s tests -v
python3 scripts/build_previews.py
python3 scripts/validate.py
```

Run every existing static Node command in `.github/workflows/validate.yml` as well. To focus the new integration contract:

```sh
python3 -m unittest discover -s tests -p test_radar_c2_preview.py -v
```

Repeat the wrapper and validator into a second safe output folder and compare full path/SHA-256 maps. A failed check is not equivalent to an unsupported or never-run check.

## Pending visual acceptance

After separate publication/preview authorization, use the normal isolated HTTPS review route. Do not work around a restricted cloud localhost route using another port, headless browser or DevTools.

- Check the chosen C2 composition at 1448×1088, wide 2048px, and 390×844 mobile
- Inspect actual fonts, connections, 40/44px hit areas, clipping, keyboard focus and scroll
- Check complete directories, every pagination boundary, long-label expansion, search and empty results
- Check evidence drawer open/close, tabs, unresolved questions, source links and return focus
- Check deep links and real Back/Forward, including drawer scroll restoration
- Enter from each base tree, then return with original filters, page, selected paper and scroll
- Verify mobile structure/focus switching, touch behavior and the no-JavaScript alternative
- Open the old weekly archive from new entrypoints and confirm all six records remain available

Publication, remote CI, actual-browser rendering, font measurement, touch and screenshots remain separate gates. None is implied by model or deterministic geometry success.
