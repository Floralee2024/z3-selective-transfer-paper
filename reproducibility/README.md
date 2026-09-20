# Reproducibility

## Source artifact map

The manuscript was assembled from frozen result packages in the source workspace. The large binary inputs and model artifacts are published in the companion immutable artifact release below.

## Published artifact release

- Release page: https://github.com/Floralee2024/z3-selective-transfer-paper/releases/tag/v0.1.0
- Archive: https://github.com/Floralee2024/z3-selective-transfer-paper/releases/download/v0.1.0/z3_selective_transfer_artifact_v0.1.0_20260920.zip
- SHA256: $hash
- Version: 0.1.0
- SHA256 sidecar: https://github.com/Floralee2024/z3-selective-transfer-paper/releases/download/v0.1.0/z3_selective_transfer_artifact_v0.1.0_20260920.zip.sha256

The release contains the low-dimensional confirm package, canonical fixtures, exact-rollout packages, High-N scaling and exact-held packages, model artifacts, contracts, frozen configurations, work code, and runbooks.

## Aggregation entry points

The source workspace contains these aggregation and execution entry points. Provenance copies are included under eproducibility/source/; the companion artifact release supplies the large fixtures, manifests, contracts, model artifacts, and original runtime inputs needed for reruns:

`	ext
original source entry points:
work\aggregate_joint_lowdim_confirm_v1.py
work\run_joint_lowdim_v1_serial.ps1
work\aggregate_high_n_scaling_v1.py
work\run_high_n_scaling_v1_serial.ps1

repository provenance copies:
reproducibility/source/aggregate_joint_lowdim_confirm_v1.py
reproducibility/source/run_joint_lowdim_v1_serial.ps1
reproducibility/source/aggregate_high_n_scaling_v1.py
reproducibility/source/run_high_n_scaling_v1_serial.ps1
`

The high-N formal design is 3 N levels × 3 scenarios × 2 conditions × 4 split seeds = 72 blocks, with five training seeds per block.

The compact evidence package includes both exact held-unit high-N aggregates: the uniform post-first-step action mixture and the repeat-action sensitivity package. The latter repeats each held unit's first action after the first transition; it is a fixed evaluation rule, not a learned policy.

## Reproduction contract

Any reproduction must preserve:

- fit/selection/test separation;
- the declared outer split units;
- nested training seeds rather than pseudo-replicating them;
- the exact candidate/control contrast;
- the fixed action rule and initial distribution for horizon evaluation;
- the frozen configuration and contract hashes;
- the distinction between predictive eligibility and causal eligibility.