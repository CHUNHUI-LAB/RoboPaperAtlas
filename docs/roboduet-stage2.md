# RoboDuet writing reader

## Scope and source

The Stage 2 report analyzes the eight-page author-hosted manuscript also used for the existing Stage 1. Its source SHA-256 is `5602f56b733bd24328af15646052ebf29a6b9e3414d5aa887e981b3b2f5872a6`. The formal record is [IEEE RA-L 10(5):4564–4571 (2025)](https://doi.org/10.1109/LRA.2025.3551230), but equality with the publisher PDF and accepted-manuscript status have not been established. Both report and catalog retain this distinction prominently.

The analysis covers the abstract (5 sentences), four introduction-prose paragraphs (20 sentences), and the two closing paragraphs (7 sentences). Contribution-list and other-section organization are discussed separately. All 32 counted units have stable anchors, source locations, primary/secondary writing functions, syntax analysis, transitions and limits.

After removing citation markers and punctuation-only remnants, the sample contains 710 whitespace-delimited words: abstract 127, introduction 450, closing 133. Finite-predicate voice categories are reported per sentence, with counts that sum to each sample. The introductory shared-auxiliary coordination is correctly counted as mixed voice; nonfinite passive modifiers and copular predicates are not automatically treated as finite passives.

## Quotation and public boundary

Only two explicitly identified source excerpts, totalling ten English words, appear in the HTML. The remaining analysis uses original commentary, brief summaries and exact sentence locations. This is not a full original-sentence republication. Original PDFs, source-page images and full sentence transcripts are not distributed.

The report preserves the author's reported 23% claim while giving the direct 39/60 versus 32/60 calculation and explaining the unresolved denominator. It distinguishes execution-time perturbation survival from training-process stability, retains the similar-embodiment transfer scope and correctly describes synchronized second-stage training.

## Registration and navigation

Identity: `rpa-0052 / stage2 / v1 / writing-close-reading.html`.

A separate `report_roboduet_stage2.py` validator pins the exact source, document, stylesheet and control-script fingerprints. It also fixes the eight section IDs, 32 ordered unit IDs, two allowed short excerpts and ten-word quotation count. The common resource-free CSS, HTML and URL guards continue to apply. Existing Stage 1 rules are unchanged.

The current navigation views for RoboDuet Stages 1 and 2 are derived from exact registered hashes and fixed navigation signatures. Only navigation, return links and provenance are transformed; article content, script and style are unchanged. Stage 3 remains disabled and no Stage 3 output is written. Fixed historical reports remain byte-identical.

Adding this stage yields 95 catalog papers, 3 papers with at least one report, 8 imported current stages and 2 papers with all three stages. Bibliographic verification is not promoted by report registration.

## Review and checks

Content review and static/DOM-model checks passed. Browser and print visual acceptance is still incomplete, as stated in the report. Visual validation requires checks of the rendered page at desktop and mobile sizes, including its print layout.

Regression coverage includes historical byte immutability; strict identity, source, document, style and script guards; hostile resource and attribute rejection; source-unit/excerpt changes; current navigation and pending-stage output; count invariants; and repeated/interrupted navigation, mobile TOC focus/Escape, reduced motion and terminal section behavior in a DOM model. A DOM model is not a replacement for a real browser render.
