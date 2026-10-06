# C2 isolated review candidate

Status: local candidate pending real-browser acceptance. Not published. Model, in-memory DOM and static layout checks are not browser, touch or visual acceptance.

## Build and scope

The opt-in CI wrapper `python3 scripts/build_previews.py` appends `review/radar-c2-analysis/`. The protected `scripts/build.py` and `scripts/validate.py` remain byte-identical; running `build.py` alone does not add C2. There is no formal home navigation link or new formal reading Stage.

The existing `review/radar-trees-c/` route, its exact nine-file manifest and weekly archive remain intact. This candidate is a separately namespaced data-model and interaction experiment, not only a CSS skin of the old C view.

First integration history: the initial integration used main `880d4fa46d01a5288515062a4cf1d6f34de65903`, tree `69d3b2098220db004cbeb4bacb9200c7bfdc948e`, including the submission-maintenance changes in PR #24. That historical source identity was independently reconstructed from 1,063 Git blobs; it is not the current rebased baseline. PR #18 protects 105 added/modified source paths; 105 is not a paper count.

Current rebased integration baseline: main `1a27cc16d5acb2e8df54ddde880016aa134b352c`, tree `6ed865ef741692c40282a2d67f5b45a382488054`, with all 1,065 tracked source paths independently verified. All 18 daily changed source paths from PR #25 are preserved byte-for-byte; 18 is a path count, not a paper count. Relative to this main, the candidate scope remains the same three appended lines in `scripts/build_previews.py` plus 34 added paths, with no deletions. Any later main must be reconciled before publication.

## Coverage and scientific boundaries

Canonical sets in the unchanged old graph independently give:

- baseline: 39 papers; the new typed literature/Challenge trees cover exactly these 39
- old weekly: 6 candidates, overlapping baseline by 2
- total unique across these ranges: 43
- four weekly-only candidates are outside the rebuilt trees and analysis: `arxiv:2609.37187`, `arxiv:2609.37353`, `arxiv:2609.39166`, `arxiv:2609.39579`

The four records are retained in the old weekly route with explicit links and coverage notices from every new HTML entry, including the no-JavaScript alternative. No mappings were invented to extend the new tree's denominator to 43.

Formal catalog 95 records, reports registry 21 records, and 12 imported Stage slots remain byte-identical. Baseline records and all their existing state are copied without scientific reinterpretation. Typed seed additions are editorial comparison structures supported by source fields; shared concepts do not imply shared code, a common implementation or academic inheritance.

Only HarnessVLN has the filled analysis sample: 59 original template nodes, 13 explicitly marked repeated template instances, 47 answers and 6 unresolved questions. The 47 comprise 40 evidence-linked answers and 7 author-claim-only answers. The unresolved set retains 5 not-reported items plus 1 source-missing item, including its empty code locator array. Other 38 papers retain honest pending templates, without copied sample answers. Evidence-linked does not mean independently reproduced. No existing Stage state is promoted.

## Publication boundary and reproducibility

`radar_c2_preview.py` defines a code-fixed public allowlist of 14 files. The manifest cannot expand it. Only runtime HTML, CSS, JavaScript and their bundled data enter the route. Tests, frozen source JSON, provenance seals, helper scripts, source snapshots, review reports, logs and reference images are not publicly copied. Review fixtures live under `tests/fixtures/radar-c2-analysis/`, outside the public route.

The manifest seals exact runtime and review-input SHA-256 values. Preflight validates the sources and destination before `build.py` can clear output. It rejects changed bytes, missing/extra files, symlinks, FIFOs, source-directory output overlap, and manifest allowlist expansion. The writer atomically replaces each file, so an existing hardlink is not truncated, then verifies the exact output file/directory set and bytes. The manifest preserves the real-browser `NOT_RUN` state.

Local script and stylesheet URL versions in the new root entry are derived from their actual file hashes, preventing a new entry from requesting stale resources under the same URL. No remote library, build-time scientific inference or network execution is introduced.

The unchanged 31-check typed-tree suite and 38-check C2 suite are invoked from Python test discovery in temporary copies. They do not generate reports in frozen source directories. Two new-copy-only integration regressions check explicit C2 entry at scroll zero and restoration of the prior tree scroll, while history-based entry does not force zero. The new root coverage notice stays outside the main/header elements hidden during C2, so the old-weekly link remains accessible. Additional tests cover the integration, archived coverage, protected paths, safe publication and output equivalence. Existing CI workflow discovery already runs them; workflows and package dependencies are unchanged.

The current implementation also checks that the normal old build plus its existing previews and the new wrapper differ only by the new 14-file route. This protects all existing generated reader/Atlas/Radar/report outputs, beyond a mere page-count comparison.

Measured output for the rebased candidate before this documentation-only correction: two fresh wrapper builds each produced 278 files, with identical path/SHA-256 maps. An independent original build of the new main produced 264 files; all 264 paths and hashes are preserved, with exactly 14 C2 files added. These are the completed rebased build measurements, not a claim that the full validation was rerun after this documentation edit. Code, UI, data, scientific evidence and tests are unchanged; the earlier 610 Python / 306 static Node passes are inherited code-identical validation, and post-edit targeted checks are recorded separately in this revision's release evidence. Publication and real-browser acceptance remain NOT_RUN.

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
