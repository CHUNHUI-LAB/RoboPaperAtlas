# Relationship design preview

`/atlas-preview/` is a separately labeled design prototype. It does not replace the live Atlas or modify the paper catalog. The default UMI neighborhood contains 11 source-checked typed records over eight paper pairs: citation and explicit adoption are separate records. Optional same-classification-problem-group links are stated inferences; missing citation indexing is unknown, not evidence of zero citations.

The prototype's single self-contained HTML is transported in ordered UTF-8 chunks under `data/atlas-preview-parts`. `scripts/preview_artifacts.py` verifies every part and the final payload hash and writes only `dist/atlas-preview/index.html`. The assembled bytes match the independently reviewed standalone artifact exactly. Its behavior tests extract and execute the actual embedded production script.

Publication of this route permits design review, not an assertion that its appearance or interaction design has been accepted. All 95 papers remain searchable with independent task and method filters. Existing report/resource links retain their actual destinations. No new relation is inferred from graph distance or layout.
