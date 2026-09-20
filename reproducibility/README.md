# Reproducibility

## Source artifact map

The manuscript was assembled from the following frozen result packages in the source workspace:

```text
D:\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\joint_lowdim_confirm_aggregate_20260801_final
D:\Codex\2026-08-03\joint-lowdim-rollout-60-60-block\outputs
D:\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\high_n_exact_held_confirm_20260804_aggregate
D:\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\high_n_exact_held_repeat_action_confirm_20260804_aggregate
D:\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\Z3_SELECTIVE_TRANSFER_FINAL_INTEGRATED_REPORT_20260804.md
```

## Aggregation entry points

The source workspace contains these aggregation and execution entry points:

```text
work\aggregate_joint_lowdim_confirm_v1.py
work\run_joint_lowdim_v1_serial.ps1
work\aggregate_high_n_scaling_v1.py
work\run_high_n_scaling_v1_serial.ps1
```

The high-N formal design is 3 N levels × 3 scenarios × 2 conditions × 4 split seeds = 72 blocks, with five training seeds per block.

The compact evidence package includes both exact held-unit high-N aggregates: the uniform post-first-step action mixture and the repeat-action sensitivity package. The latter repeats each held unit's first action after the first transition; it is a fixed evaluation rule, not a learned policy.

## Required artifact release before submission

The large fixture and model bundles should be published as an immutable release or archive. Add its URL and checksum to `ARTIFACT_RELEASE.md` before claiming full public reproducibility. The current GitHub repository is a manuscript and provenance package, not a replacement for the large binary artifact archive.

## Reproduction contract

Any reproduction must preserve:

- fit/selection/test separation;
- the declared outer split units;
- nested training seeds rather than pseudo-replicating them;
- the exact candidate/control contrast;
- the fixed action rule and initial distribution for horizon evaluation;
- the frozen configuration and contract hashes;
- the distinction between predictive eligibility and causal eligibility.
