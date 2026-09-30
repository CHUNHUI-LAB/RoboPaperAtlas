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
