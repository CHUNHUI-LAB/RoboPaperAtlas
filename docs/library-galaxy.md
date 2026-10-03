# Library galaxy presentation

The Library home uses an original decorative galaxy illustration and a dark,
readable interface. The galaxy is not a diagram of citations, similarity, or
verified relationships. Topic labels and counts are derived from the existing
catalogue grouping rules. Pointer and keyboard focus identify a topic; choosing
it invokes the unchanged catalogue filtering controller.

The illustration is a 1440 × 720 WebP (under 70 KB). It is static: there is no
animation loop, pointer-tracking sensor, external font, image CDN, or background
network request. Local focus transitions respect `prefers-reduced-motion`.
Search submission scrolls to the actual results; live typing and history/scroll
restoration remain owned by the existing catalogue controller.

Featured entries use real catalogue IDs. Existing summaries are reused; the VBC
presentation summary is based on the [official PMLR abstract](https://proceedings.mlr.press/v270/liu25b.html)
and the published Stage 1 reading. It describes the visual high-level goals and
low-level whole-body tracking, without claiming a new reading stage or independent
reproduction. No paper photograph, citation edge, report status or history is
created by the decorative interface.

Styles are loaded only for the Library. Detail, map, submission, frontier,
reading and immutable report pages keep their own presentation.

## Checks

- `python -m unittest discover -s tests -p test_experience.py`
- `python -m unittest discover -s tests -p test_readable_navigation.py`
- `node --test tests/test_library_galaxy.cjs`
- `node --test tests/test_catalog_navigation.cjs tests/test_filter_feedback.cjs`
- The complete repository test/build/validation workflow remains required

Static contrast and controller checks do not establish browser layout, native
dialog focus, image-background contrast, or real history behavior. Review those
on desktop and mobile, including search, empty results, filters, preview dismissal,
Back/Forward, returning from a report, and loading the complete catalogue.
