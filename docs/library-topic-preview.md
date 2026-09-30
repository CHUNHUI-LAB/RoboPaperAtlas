# Isolated topic-browser source review

This proposal adds one opt-in route without changing the catalog's classification, the homepage, reports, Atlas, or Radar. No publication is requested by this patch.

## Reproducible build

Run `python3 scripts/build_topic_preview.py --output dist-topic` from this repository. The command validates the four public source files, runs the unchanged existing full-site builder, and adds only `library-topic-preview/`. It works after deleting generated output; it does not depend on any older `dist` directory.

The normal `scripts/build.py` is deliberately unchanged, preserving the existing build-script fingerprint and every original generated page. For a later reviewed combined preview build, call `write_preview(ROOT, target)` from `scripts/build_topic_preview.py` after the existing site build and alongside the other isolated-route writers. Never copy this whole snapshot over concurrent work.

Source files live in `previews/library-topic-preview/`: HTML, CSS, JS and the explicit public JSON allowlist. The build does not read private audits or any external local path. JSON is the small reviewable browsing overlay, not a replacement scientific classification. Exact schema keys, approved source hosts and record IDs are checked before copying. Extra fields, unsafe URLs, unexpected files and invalid membership values fail the build.

## Reader contract

All 95 papers appear and are searchable by default. Exactly 13 boundary examples are arranged into the proposed research themes; the other 82 are explicitly still awaiting theme organization. Counts are example counts, not a claim of complete library classification. Research themes can overlap; methods, robot type and resource roles remain independent. Related resources can be hidden without treating them as research papers.

Search uses multiword AND matching independent of query order, whitespace normalization, original UMI aliases and π/pi normalization. Main controls use 16–18px text, main explanatory text is 18px and supporting text 14–15px. Methods and evidence are collapsed for quieter scanning.

## Verification

- `python3 -m unittest discover -s tests -p test_library_topic_preview.py -v`
- `node tests/test_library_topic_preview.cjs`
- `python3 scripts/build_topic_preview.py --output dist-topic`
- Compare `dist-topic` against a clean `scripts/build.py --output dist-baseline` build. Only the four new route files should be additional.

Automated checks cover field allowlists, HTTPS source-host restrictions, injection escaping, sample status counts, 95 default results, aliases, multiword ordering and whitespace, no-result handling, resource/topic boundaries and detail-page destinations.

Visual acceptance is still pending. Earlier local browser startup failed because of sandbox socket restrictions; no browser screenshot or passing visual check is claimed. Review at phone and desktop widths before public integration.

## Revision after source review

RoboDuet and UMI on Legs remain related entries under the manipulation theme only as an editorial reading-path choice. Their notes explicitly retain cooperative manipulation-policy, demonstration-trained visual-policy and policy/control-interface contributions. Related-entry placement is not a negative scientific classification, and UMI on Legs is not reduced to moving an already-existing policy.

UMI's project evidence is labeled as an official project page and points to the opening abstract, Policy Robustness and Capability Experiments. The public locator contains no uncheckable earlier-review claim. Repeated Chinese wording is corrected.

Source/output paths must stay normalized inside the repository, with no symlink in their path or output tree. Only four allowlisted regular source files are copied, with final-file `O_NOFOLLOW`; an existing route with extra files fails closed instead of being recursively copied or replaced. Nine Python tests cover these additional cases. For integration, transfer only the eight manifest-listed added files into the newest reviewed A/B source, never this older full snapshot.
