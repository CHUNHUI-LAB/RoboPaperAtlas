# Two-paper local analysis candidate

This local candidate extends the existing isolated `review/radar-c2-analysis/`
route. It is not published. Real browser rendering, keyboard behavior in an
actual browser, font metrics, touch, screenshots and publication are NOT_RUN.
Model, in-memory DOM and script-free checks are separate from browser acceptance.
The prior sealed label-bounds candidate remains untouched.

## Contract

The original 59-node schema, complete 39-paper snapshot, literature/Challenge
source taxonomies, formal catalog/report registry and all reading Stage values
remain unchanged. HarnessVLN retains its exact legacy `mapping` and `compat`
fields. `mappingsByPaperId`, `ledgersByPaperId` and `unknownsByPaperId` add explicit
paper-scoped data. Local evidence IDs such as E01 are resolved within each paper.
No cross-paper evidence inference is performed.

- HarnessVLN: 59 original nodes + 13 instances; 47 answers; 6 unresolved questions
- NavHarness (`navharness`, fixed `2609.34276v1`): 59 + 18 = 77 nodes;
  51 content records (43 evidence-linked, 6 author claims, 2 partially reported);
  12 unresolved questions; 31 evidence records; 724 answer source-locator occurrences
- 20 NavHarness module answers explicitly retain
  `not_reviewed_implementation_unknown`; zero are implementation-verified
- `arxiv:2609.39915` (Adaptive Goals) is distinct and remains pending
- Two content views, 37 pending; baseline39/weekly6/unique43/four weekly-only
  coverage remains unchanged

Counts are derived from each mapping. Fixed review-boundary checks independently
reject loss, status changes and identity changes. Evidence-linked means source
location is available, never independent verification or reproduction.

Each answer shows its exact status, `sourceKind`, every `codeEvidence` field and
real `sourceGapIds` links. Unknowns use their original id/topic/detail/status,
source URLs and evidence IDs without fabricating semantic nodes. They can be
searched independently. U12 remains a whole-paper issue, preserving the PDF
Figure18/page39 bar/text disagreement and its exact link.

The script-free page includes both complete trees and all original source
locators. Harness legacy anchors remain valid. New Nav DOM anchors have a paper
namespace; semantic schema/instance IDs are unchanged. Local history includes
the chosen paper and per-gap drawer scroll, and return context retains the prior
tree, facet, query, page, paper and scroll.

## Bounded public payload

The fixed public allowlist remains exactly 14 files. Additional concise analyzed
data lives inside the existing bundle. PDF/full-paper text/images, review tools,
fixtures, private paths and logs are excluded. Separate exact scientific input
pins and the new source seal cover both papers; the original Harness seal stays
unchanged. Manifest v2 seals the full reviewed runtime and fixture input set.
Existing historical preservation, source mutation, symlink/FIFO, extra-file,
hardlink and safe-output checks remain in place.

`analysis/build_bundle.py` deterministically reproduces the runtime bundle from
reviewed fixtures. `analysis/build_reading.py` generates all four HTML entries
from those reviewed data and explicit public templates. Both are fixture-only,
not published. New model/DOM and script-free suites run through Python discovery,
as do the original portable regression suites.

## Verification gates

Independent schema/content/render/security review precedes the full regression,
build and validate run. Results and final hashes are recorded in separate local
validation evidence. A passed local suite does not promote any reading Stage or
approve publication. Real-browser acceptance remains a separate unresolved gate;
no localhost, alternate-port, DevTools or headless bypass is used.
