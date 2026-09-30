# Reader preview

`reader-preview/umi-on-legs/` is one complete Stage3 interface sample. It uses the same site shell, navigation, global search and base design tokens as the catalog and Atlas. Published v1 artifacts and Library files are not replaced by this preview.

- Audited Stage3 body, six embedded figure images and nine Python excerpts are retained
- Python tokens are colored during the static build using the standard-library tokenizer; no snippet is executed
- Each source line range is parsed from its fixed-commit reference and checked against the exact excerpt line count
- Key-line controls emphasize specific operations in the existing excerpts; copying excludes rendered line numbers
- Long source-path labels become compact file/line links with the original path in their title; destination URLs remain unchanged
- Active section navigation, a keyboard-usable narrow TOC and reduced-motion behavior are implemented
- The original PDF is linked externally. This preview does not embed, mirror or claim sentence-level highlighting of it
- Stage1 and Stage2 links lead to the published v1 readers. Later content/UI revisions require their own review

The navigation labels are Library / Atlas / Radar. The reading surface is deliberately quiet: no animated galaxy behind long text or code.
