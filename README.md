# Selection-Gated Transfer Under Sparse State–Action Support

This public repository contains the manuscript and reproducibility materials for a synthetic study of selective transfer when state and state–action cells are sparse or held out.

## Main result

The study does not support a universal transfer claim. It supports a narrower boundary:

1. unselected high-order transfer can create negative transfer under joint sparsity;
2. a rank-admissible Stage-1 low-dimensional mechanism can produce a small, reproducible fixed-action predictive association in one controlled environment;
3. selection-resolved Stage-2 corrections do not add stable decision-level value in the evaluated panels;
4. increasing sequence count improves some TV/KL contrasts but does not produce universal or metric-wide monotonic improvement.

The result is predictive synthetic evidence. It is not causal, policy, reward, regret, real-data, encoder, or deployment evidence.

## Repository layout

- paper/manuscript.md — complete manuscript draft.
- paper/claims.md — claim-to-evidence ledger and non-claims.
- vidence/ — compact evidence snapshots and provenance notes.
- eproducibility/ — commands, environment notes, and artifact mapping.
- CITATION.cff — citation metadata for the repository.

## Reproducibility status

The repository is the compact manuscript and provenance layer. Large fixtures, model artifacts, and NPZ bundles are distributed in the companion immutable artifact release rather than committed into Git history.

The public artifact release is [v0.1.0](https://github.com/Floralee2024/z3-selective-transfer-paper/releases/tag/v0.1.0). Its direct archive URL, SHA256, and version are recorded in [eproducibility/ARTIFACT_RELEASE.md](reproducibility/ARTIFACT_RELEASE.md).

## Status

Public manuscript repository with a versioned reproducibility artifact release. The archive supports synthetic fixed-action predictive claims only; it does not establish causal effects, policy improvement, reward improvement, planning ability, real-data validity, or deployment safety.

The compact evidence package includes the primary exact held-unit high-N aggregate and its repeat-action sensitivity aggregate. Both preserve the same negative conclusion about universal accumulation and endpoint retention.