# Navigation Stage 1 integrated-reader preview

This change adds an isolated, noindex review surface for three specified preprints:

- HarnessVLN, arXiv:2609.15195v3
- NavHarness: Towards Lifelong Embodied Navigation, arXiv:2609.34276v1
- HoloAgent-0, arXiv:2606.23565v1

The public review entry is `reader-integration-preview/navigation-stage1-20261004/index.html`.
Each paper has a `stage1.html` current-reader presentation and a self-contained
`first-pass.html` source in its own subdirectory. The former uses the same F2
presentation and reviewed reading controls intended for canonical integration.
Stage 2 and Stage 3 are unavailable. The preview is explicitly pending visual
acceptance and final content review; it is neither a reproduction claim nor a
promotion of the formal catalog's reading status.

## Isolation

`data/catalog.json`, `data/reports.json`, classification evidence, Radar data,
assets, historical report policies/chunks and workflows are unchanged. The
formal registry remains at 21 versioned reports; the three papers' canonical
stage states remain `not_imported`.

Only four existing runtime files receive additive integration hooks:
`reports.py`, `current_reader.py`, `build.py`, and `validate.py`. The exact three
Stage 1 identities are permitted only with `review_status: preview_pending`.
They do not enter the formal registry. The preview manifest is separate at
`data/navigation-stage1-preview.json`, and its UTF-8 chunks live only under
`data/navigation-stage1-preview-parts/`, not the formal report-parts tree.
Both canonical registry loading and artifact assembly explicitly reject
`preview_pending`, even if valid preview records and chunks are copied there.

No preview step changes repository permissions, authentication, the Pages
workflow, or the configured publishing branch. Publishing still follows the
repository's ordinary reviewed main-branch deployment.

## Safety and provenance

The exact source PDF, complete HTML, stylesheet, existing reader-controls
script, all 12 scientific sections, passive MathML and image bytes are pinned.
The script is the unmodified, already reviewed VBC controls script. No inline
event attributes are allowed. The inherited resource-free CSS, HTTPS URL,
HTML-attribute and PNG/JPEG checks remain active. Unknown identities, stages,
versions, source editions, scripts, formulas, images or chunk changes fail closed.

HarnessVLN and NavHarness retain CC BY 4.0 source/crop attribution, complete
authors, versioned paper and license links, alteration notes and non-endorsement.
HoloAgent-0 contains no original figure reproduction: eight independently
worded Chinese explanatory cards point to the original figure locations.
Its arXiv non-exclusive distribution license is not treated as a grant to
republish figures. No full PDF, original page scan, private source file, account
identifier or authoring instruction is distributed.

## Validation boundary

`tests/test_navigation_stage1.py` exercises exact source/identity boundaries,
independently pinned resources and sections, active-content attacks after
policy rehash, malformed preview manifests, derived preview bytes and restricted
in-memory rendering. `release_checks/navigation_stage1_isolation.py` additionally
checks every prior tracked source and generated route, allowing only the four
specified runtime edits and the declared generated cache marker change.

The added output is exactly seven HTML pages. The 237 pre-existing output files
remain byte-identical after normalizing only their generated `data-data-version`
cache marker. No formal artifact or PDF is added to the public output.

Static content review and test results are not browser visual acceptance.
Desktop, narrow-screen, keyboard, image enlargement, chapter navigation and
print checks must be recorded against the actual HTTPS preview before canonical
Stage 1 entries are promoted. This document does not assert those checks passed.

The whole-baseline comparison is a release-specific check, run with
`python3 release_checks/navigation_stage1_isolation.py -v`. It is intentionally
outside default test discovery so a later legitimate Radar, catalog or UI update
is not forced to preserve this release snapshot forever. The generic security
regressions remain in the normal test suite.
