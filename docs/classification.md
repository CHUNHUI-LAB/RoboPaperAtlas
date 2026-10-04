# Research classification

The additive `data/classification.json` overlay organizes all 95 catalog entries by their primary research problem. It does not change their original IDs, titles, bibliographic fields, original categories or reading status.

## Three separate axes

- Primary direction: Embodied Nav, Mobile Manip., Motion & Control, Locomotion, Policy Learning, Spatial Repr., General ML
- Method tags: explicitly sourced components such as WBC, VLA, MPC, RL or Memory. Using a component does not make it the paper's primary contribution
- Resource kind: dataset, benchmark, software, simulator, model, data collection or data generator. These may coexist with a research direction

Cross-domain Resources and Cross-domain research are separate visible collections. Every paper has one primary placement; Library, Atlas, homepage controls and detail pages use the same projection. Method/resource filters intersect that placement.

The initial source review used primary abstracts, contribution statements or official project descriptions, with stated section-level evidence for the UMI pilot. Four editorial boundary cases remain explicitly pending. This review does not certify all bibliography fields, imply a full reading of all papers, or establish reproducibility.

The immutable canonical catalog and reviewed overlay remain separate. New records fail closed without an explicit overlay entry. The overlay is bound to the catalog byte hash; after an intentional catalog update, review the overlay and update that binding. Unknown IDs, extra fields, invalid method/resource labels and unsafe source URLs fail validation.

Original catalog tags remain available as historical search keywords. Atlas's original-tag links are transparent similarity suggestions, not reviewed citation, method-inheritance or scientific influence edges.

## Targeted method-discovery correction (2026-10-04)

RMA (rpa-0050) adds RL from [arXiv v1, III-A Base Policy](https://arxiv.org/html/2107.04034v1#S3.SS1); RoboDuet (rpa-0052) adds RL from [arXiv v5, IV-C Training Details](https://arxiv.org/html/2403.17367v5#S4.SS3). These author-manuscript component checks preserve their primary directions and all reading states. The overlapping robot-learning browse lens consequently contains 50 entries, not 48.

Library and the map share the reviewed classification search projection. Method labels reuse the same Chinese display adapter while canonical method values remain unchanged. The direction filter is explicitly primary-only; secondary directions are displayed in the classification details.

The global preview's immutable transport remains unchanged. After authentication and reading-state hydration, `preview_discovery.py` derives updated methods, method evidence, search aliases and overlapping navigation only for records with changed reviewed method evidence. It preserves primary placement/navigation, relations, layout and reading states; tests constrain the current correction to the two records above.
