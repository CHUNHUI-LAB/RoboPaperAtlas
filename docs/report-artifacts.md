# Reviewed HTML report artifacts

This pilot imports three separately reviewed reading stages for `rpa-0062`
(UMI-on-Legs). Current Stage 2 is `v4`; Stage 1 and Stage 3 remain `v3`. All historical files remain available. A report means that the named reading artifact was
imported; it does not mean that its claims or experiments were independently
reproduced. Metadata verification, reading, code inspection, and reproduction
remain distinct.

## Public registry contract

`data/reports.json` has exactly two keys:

```json
{"schema_version": 1, "reports": []}
```

An empty registry is valid. Every included report must have exactly these fields:

| Field | Contract |
| --- | --- |
| `paper_id` | `rpa-0062` in this pilot |
| `stage` | `stage1`, `stage2`, or `stage3` |
| `version` | `v1`, `v2`, or `v3`; `v4` is restricted to UMI Stage 2 |
| `filename` | The exact stage-specific filename below |
| `sha256` | Lowercase 64-character SHA-256 of the delivered HTML bytes |
| `bytes` | Positive integer, exactly the delivered HTML byte count |
| `source_sha256` | Lowercase SHA-256 identifying the reviewed source artifact |
| `source_edition` | Nonempty public source/edition description |
| `source_url` | Approved official paper, project, or arXiv source |
| `pdf_url` | Approved official publisher or arXiv PDF URL |
| `created_at` | Real calendar date in exact `YYYY-MM-DD` form |
| `review_status` | `approved` |
| `rights_note` | Nonempty public statement of the publication/quotation rights basis |
| `parts` | Ordered nonempty list of exact `{file, bytes, sha256}` objects |

Unknown fields, duplicate JSON keys, duplicate reports, invalid dates, booleans
masquerading as byte counts, and unapproved report identities are rejected.
The two source URLs are checked through the shared public-HTTPS URL validator
and the pilot's official UMI-on-Legs source allowlist. They do not trigger network
requests. A rights statement and an `approved` value record a content
review; a hash or schema check cannot establish rights or factual correctness.

Do not add Library identifiers, private file locations, credentials, research
workspace paths, or internal instructions to the registry or report content.
Only public provenance belongs in these fields. Private originals are not build
inputs and must not be copied into this repository.

## Derived paths and exact transport

| Stage | Filename |
| --- | --- |
| `stage1` | `first-pass.html` |
| `stage2` | `writing-close-reading.html` |
| `stage3` | `method-code-reading.html` |

Generated paths are always:

```text
artifacts/rpa-0062/<approved-version>/<stage-specific-filename>
```

Input chunks are always:

```text
data/report-parts/rpa-0062/v1/stage1/part-001.txt
data/report-parts/rpa-0062/v1/stage2/part-001.txt
data/report-parts/rpa-0062/v1/stage3/part-001.txt
```

Each stage's list starts at `part-001.txt`, increments consecutively, and ends no
later than `part-999.txt`. Each part contains at most **48,000 bytes**, is
independently valid UTF-8, and carries its exact byte count and SHA-256. Assembly
concatenates those original bytes without newline, Unicode, whitespace, or HTML
normalization. The final byte count and SHA-256 must also match. This bounds a
single report at 47,952,000 bytes. The whole registry is limited to 2 MB and the exact
reviewed paper/stage/version identities in `REPORT_PAPERS` (currently fifteen
records, including ten UMI versions across its three stages).

No registry value is accepted as a directory or arbitrary input/output path.
Symlinks in the root, its ancestors, the registry, chunk ancestry, chunks, or
generated destinations are rejected. Inputs must be regular files. Chunk names
cannot contain traversal or alternate path syntax. Missing, reordered,
duplicated, oversized, invalid-UTF-8, or tampered chunks fail closed.

Unlisted files are never read as report content, copied, or published. The
assembler does not recursively copy the artifact tree, discover reports by glob,
or remove unrelated files. The static builder must copy only the validated
manifest-listed paths returned by `report_path(record)`; stale generated files
must not become publication inputs.

## Legacy v1 static HTML security boundary

The validator checks exact UTF-8 bytes and a strict readable-HTML tag/attribute
allowlist. It allows semantic text, headings, navigation, tables, figures,
`details`/`summary`, labels, and checkbox-only inputs for CSS image zoom. It rejects
scripts, frames, objects, embeds, forms, base tags, refresh/other `http-equiv`
metadata, external stylesheets/resources, event handlers, SVG/MathML, unknown
attributes, duplicate attributes/IDs, processing instructions, and non-UTF-8
charset declarations.

Images must be `data:image/png;base64,...` or
`data:image/jpeg;base64,...`, with strict canonical base64 and matching binary
signatures (including the PNG header/trailer or JPEG trailer). Remote image
sources, SVG, other MIME types, `srcset`, and data-URL hyperlinks are disallowed.
This is a resource/security boundary, not a full image decoder or image-quality
check.

Inline styles and CSS style blocks are permitted. CSS escapes, imports, resource
functions such as `url()`/`image-set()`, JavaScript expressions, legacy behavior
bindings, URL-bearing values, and unapproved at-rules are rejected. Ordinary
`scroll-behavior` is allowed. Safe media queries and layout/typographic CSS work
without an external stylesheet or font.

Links may be:

- Public HTTPS citations passing the shared URL check, using the standard HTTPS
  port
- Same-document fragments resolving to an actual unique ID
- One of the three exact sibling report filenames, optionally with an existing
  fragment in the approved target report
- The exact site-return path `../../../papers/rpa-0062/index.html`

Other relative paths, root-relative URLs, protocol-relative URLs, local query
strings, empty links, and unknown/missing sibling targets are rejected. Sibling
links are resolved against the complete approved registry, not the filesystem.

## Python and CLI integration

No third-party dependency or network connection is needed:

```sh
python3 scripts/reports.py --check
python3 scripts/reports.py
python3 -m unittest discover -s tests -p test_reports.py -v
```

The default root is the script's repository. `--root <repository>` supports
isolated validation and assembly. A failure raises an error and exits nonzero.

- `report_path(record)` validates a complete record and returns its derived
  artifact-relative path
- `load_reports(root)` is read-only. It validates all metadata, chunks, assembled
  HTML, and inter-report links, then returns the public record list unchanged,
  with no private cached fields or embedded payloads
- `assemble_reports(root)` performs all input validation before writing any
  report. It preflights all destinations, then atomically replaces each listed
  generated HTML file and returns the public records. The group of writes is
  not a cross-file filesystem transaction
- `split_report(root, record, raw_bytes)` requires every noncomputed metadata
  field. It computes/replaces `sha256`, `bytes`, and `parts`; validates the HTML;
  writes UTF-8-safe chunks; and returns a new complete record without changing
  the input record or registry. Caller-provided computed fields are optional.
  Same-document links are checked immediately; sibling existence/fragments are
  checked when the complete registry is loaded

Publish only after the complete registry passes validation. Splitting individual
stages is a packaging operation, not approval to publish them. Updating existing
chunks can temporarily make an old registry invalid until its corresponding
metadata is updated, so build only from a coherent reviewed revision.

Tests use tiny synthetic reports and generated temporary directories. They do
not include original research reports, private notes, credentials, or source
Library files.

## Narrow-screen presentation correction

The Stage3 v1 delivery includes a CSS-only correction for long inline identifiers in prose/list items at widths up to860px: `overflow-wrap:anywhere`. Preformatted code blocks retain their existing local horizontal scrolling. No report text, citations, image bytes or stage interlinks changed. The corrected offline source and the public copy each retain their own SHA; the public copy still differs from that offline source only by its return-to-paper brand link.

## Immutable v2 readers

Each v2 HTML is the exact same self-contained file for website and offline use. It embeds the shared reader CSS, reviewed interaction scripts, original figure bytes, and, in Stage 3, all 20 unmodified KaTeX WOFF2 fonts. Math is static HTML plus accessible MathML and TeX annotations; no remote formula renderer runs. Software and font license notices are included in the document. Original PDF/code links and site search need a network connection.

Version 2 uses a separate strict boundary in `scripts/report_v2.py`. `data/report-v2-policy.json` pins all three complete document hashes and the exact named inline CSS/script hashes. The parser then checks permitted semantic HTML and MathML, IDs, safe inline styles, figures, HTTPS links and version-local sibling links. Unknown scripts, styles, events, frames, remote fonts/images and resource tags are rejected. An arbitrary script cannot be enabled by changing only the report registry or its document hash. Policy changes require reviewing the embedded code and delivered documents. Version 1 retains its original script-free policy.

Only `rpa-0062` receives v2 entries. Artifact arrays are newest-first; stage counts count three imported stages, not six independent readings. The detail page links both current and historical versions. Original bibliographic fields and classification records are unchanged.

Stage 1 expands the approved figure/table discussion while preserving the twelve-section structure. The Figure 4 description uses upper/lower rows rather than ambiguous panel letters. Stage 2 keeps all 37 Chinese analysis units and adds exact PDF page/paragraph locations, with six short openings totaling 16 quoted words. The official PDF may download rather than embed, and no sentence-level highlighting is claimed. Stage 3 retains the approved 54 rendered math occurrences, nine exact source-code snippets, fixed-commit citations and six figure images.

Public CI assembles already reviewed, hash-pinned HTML parts. It does not regenerate reading content from any private input. `scripts/reader_document.py` is a generic presentation/packaging utility; its source inputs are not required by the public build.

## Typography revision v3

Version3 changes only reader presentation and current/history links. Main body text increases from16 to17px (15 to16px on narrow screens), code from12 to13px (11 to12px narrow), and captions from11 to12px (10 to12px narrow). Selected analysis/table/source-note text increases by1px. Title sizes, section order, paper content, images, equations and code snippets remain unchanged. The Stage2 official-PDF button explicitly uses light text in normal, hover and keyboard-focus states, fixing a more-specific inherited link color.

`data/report-v3-policy.json` pins the new self-contained files and their embedded assets. Public v1/v2 bytes and policies remain immutable. The current arrays are newest-first v3/v2/v1; the three stages still belong to one paper.

## Current stage navigation without changing frozen reports

Deep WBC (`rpa-0012`) has live entry pages at
`papers/rpa-0012/reading/stage1.html` through `stage3.html`. These standalone
views derive from the exact registry-validated report bytes. The generator
requires the reviewed document hash and exact known navigation, return-link, and note
signatures. It only replaces that stage navigation and the exact known header return link,
then adds explicit generated
view provenance with a direct fixed-version link in the existing document note.
Report content, embedded scripts and styles remain byte-identical. Unknown
signatures fail closed instead of falling back to a broad HTML rewrite.

Only imported stages get links and generated views. Detail pages, Library quick
views and Atlas use these current entries; UMI-on-Legs now has a bounded
v4 current-entry extension described below. The shared browser routing adapter checks the exact paper ID, version
and stage filename before constructing a local entry URL. Historical links,
report HTML, report parts, manifests, security policies and approved hashes are
unchanged. Output validation reconstructs each view and compares its entire
bytes before allowing embedded report resources; the report security parsers
are not relaxed. There is no iframe or additional runtime code.


## RoboDuet reviewed first reading

`rpa-0052/v1/first-pass.html` adds one content-reviewed Stage 1, with all twelve sections and explanations of seven figures and six tables. It reads the author-hosted eight-page manuscript; its extracted text matches arXiv v5 apart from the margin stamp. The formal RA-L identity is retained, while publisher-PDF equivalence remains unverified. No source PDF, extracted figure, page screenshot, copied original table or video is redistributed.

`report_roboduet.py` permits only this exact paper/stage/version/file identity and pins both document and inline navigation-script hashes. The source-manuscript hash is independent of the report hash. Existing HTML/CSS/URL/attribute, path, sibling-link and resource guards remain unchanged. Later stages are not enabled. The content review does not assert browser visual QA or experiment reproduction. All existing UMI and Deep WBC report bytes are preserved.

## Reading directory

`reading/index.html` derives one entry per imported paper/stage from the public catalog.
It links current readers when available and otherwise the newest frozen report.
Historical versions remain in paper details and are not counted again. The homepage
Reading route opens this directory; all three Deep WBC live reader headers return
to the same paper archive. No immutable report bytes are changed.

## UMI Stage 2 original-sentence revision v4

Only `rpa-0062/stage2/v4/writing-close-reading.html` is added. Stage 1 and Stage 3
remain v3. The current Stage 2 artifact list is v4/v3/v2/v1; the three imported
stages are still three reports, not ten independent readings. All prior registry
records, v1-v3 parts/policies, and the separate reader-theme preview stay immutable.

The new reader carries 37 visible English / Chinese / writing-analysis units from
the previously reviewed preview, with PDF page/paragraph/unit locations. All 37
English excerpts were checked against the publisher-linked formal PDF, including
spelling, punctuation, citations and URLs, after layout-only line-break repairs.
They are unchanged from that preview. The two noun-list fragments remain labelled
as fragments; two bold list lead-in labels are explicitly excluded from the excerpt
units. Source excerpts contain 857 whitespace-delimited items; the language table
uses its separately stated lexical convention and only 35 complete analysis units
(793 lexical words), rather than silently conflating these denominators.

The editorial revision corrects P1-S5's finite-predicate voice classification and
the introduction totals (17 active, 2 passive, 1 mixed, 3 copular/other, N=23).
It distinguishes K2-S2's cross-embodiment deployment claim from P3-S1's nonexpert
usability requirement, moderates overstrong Chinese summaries, and keeps author
claims, translation, and editorial inference separate. English source grammar is
not silently improved. The header bounds this review; it does not claim a new
whole-paper rereading or independent experimental reproduction.

`report_umi_stage2.py` permits this one identity only. The new policy independently
pins the complete HTML, the formal source PDF, one stylesheet, and one interaction
script. The existing resource-free CSS checks remain active; only the exact
hash-pinned script is removed before the unchanged HTML/URL/attribute/path checks.
The 37 source identifiers and English excerpt labels are checked in order.
No legacy policy, general quotation budget, or script/resource allowlist is widened.
Packaging uses the existing `split_report` and complete-registry `load_reports`
checks. The new registry source hash is the formal PDF hash, distinct from the
report hash: `0228e01b083d2fca2cf260115271d0f2c7718844b31799a61ccc34c78762d971`.

Quotation rights are documented from the [formal PMLR record](https://proceedings.mlr.press/v270/ha25a.html),
[CoRL 2024 author requirements](https://2024.corl.org/contributions/instruction-for-authors),
and [PMLR publication agreement](https://proceedings.mlr.press/pmlr-license-agreement.html),
which provides a [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/) basis.
The reader retains full author/title/publication attribution, original-paper and
license links, extraction/translation changes, non-endorsement, and the caveats
that the individual signed agreement was not inspected and the PDF has no printed
CC mark. The source PDF, extracted text, page images and private authoring/review
material are not public build inputs and are not redistributed.

The user-facing UMI entries at `papers/rpa-0062/reading/stage1.html` through
`stage3.html` extend the existing deterministic current-view generator. They use
exact pinned v3 / v4 / v3 source hashes and exact navigation, return-link and note
signatures. Only those three signatures change in a generated view; its article,
embedded styles, scripts, images, formulas and code remain byte-identical to its
registered source. Each view shows its current source version and an explicit
fixed-version link. Current Stage 1 → Stage 2 therefore reaches the v4 comparison.
Historical versioned artifacts retain their original sibling links. The browser
route adapter selects a current view only for the exact supported paper/stage/version
combination; other valid historical artifact identities keep their frozen paths.
Output validation reconstructs all six supported current views (UMI and Deep WBC)
and compares their entire bytes. This is not an HTML-parser or resource-policy
exception.
