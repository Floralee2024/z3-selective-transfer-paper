# Selection-Gated Transfer Under Sparse State–Action Support

This repository contains the manuscript and reproducibility materials for a synthetic study of selective transfer when state and state–action cells are sparse or held out.

## Main result

The study does not support a universal transfer claim. It supports a narrower boundary:

1. unselected high-order transfer can create negative transfer under joint sparsity;
2. a rank-admissible Stage-1 low-dimensional mechanism can produce a small, reproducible fixed-action predictive association in one controlled environment;
3. selection-resolved Stage-2 corrections do not add stable decision-level value in the evaluated panels;
4. increasing sequence count improves some TV/KL contrasts but does not produce universal or metric-wide monotonic improvement.

The result is predictive synthetic evidence. It is not causal, policy, reward, regret, real-data, encoder, or deployment evidence.

## Repository layout

- `paper/manuscript.md` — complete manuscript draft.
- `paper/claims.md` — claim-to-evidence ledger and non-claims.
- `evidence/` — compact evidence snapshots and provenance notes.
- `reproducibility/` — commands, environment notes, and artifact mapping.
- `CITATION.cff` — citation metadata for the repository.

## Reproducibility status

The manuscript is based on frozen result packages produced before this repository was assembled. The large fixture, model, and NPZ bundles are not copied into Git because of their size and because the source workspace is not itself a public artifact archive. The exact source paths, hashes, aggregators, and run commands are recorded in `evidence/` and `reproducibility/`.

For a submission-grade release, publish the large immutable artifact bundle separately and add its DOI or release URL to `reproducibility/ARTIFACT_RELEASE.md`.

## Status

Private manuscript repository. The wording intentionally preserves the strongest evidence boundary supported by the experiments; public release still requires author metadata and an immutable artifact archive.

The compact evidence package includes the primary exact held-unit high-N aggregate and its repeat-action sensitivity aggregate. Both preserve the same negative conclusion about universal accumulation and endpoint retention.
