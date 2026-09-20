# Formal joint low-dimensional confirm aggregation

## Scope and evidence boundary

- Research question: whether the two pre-registered compact joint mechanisms improve held joint state-action-cell prediction over the shared-global control.
- Estimand: test-cell TV/KL/argmax agreement, with five training seeds averaged within each scenario x split block.
- Outer evidence units: 12 blocks (S2/S3/S23 x four confirmatory splits); training seeds are not independent outer experiments.
- Eligibility: pipeline and predictive eligible for this synthetic predictive estimand; not causal eligible. No policy, rollout, encoder, real-data, or causal claim follows.

## Integrity

- Reports: 12/12 PASS; artifacts verified: 300/300.
- Runner SHA256: `5101b81d674c5952c5858b5cb6037b0f4a0b425b0396aca8581f7a19d0e53101`.
- Geometry audit: `PASS_WITH_REJECTIONS` (outcome blind: `True`).

## Primary selection-resolved comparisons: all scenarios

Positive improvement means lower TV/KL or higher agreement than `shared_global_only`; the interval is descriptive mean +/- 1.96 SE across outer blocks, not a causal or pseudo-replicated test.

| candidate | metric | mean improvement | descriptive interval | wins/ties/losses |
|---|---|---:|---|---:|
| action_groups_degree1 | mean_candidate_tv | -0.00126987 | [-0.00691312, 0.00437338] | 7/0/5 |
| action_groups_degree1 | p95_candidate_tv | -0.00666935 | [-0.0237869, 0.0104483] | 4/0/8 |
| action_groups_degree1 | mean_excess_kl | -0.0024691 | [-0.00819474, 0.00325653] | 7/0/5 |
| action_groups_degree1 | candidate_argmax_agreement | -0.00627326 | [-0.0347552, 0.0222086] | 8/0/4 |
| degree1_deviation | mean_candidate_tv | -0.00129738 | [-0.0066658, 0.00407104] | 7/0/5 |
| degree1_deviation | p95_candidate_tv | -0.00243665 | [-0.013625, 0.00875166] | 6/0/6 |
| degree1_deviation | mean_excess_kl | -0.00301995 | [-0.0072792, 0.0012393] | 5/0/7 |
| degree1_deviation | candidate_argmax_agreement | 0.0092626 | [-0.00665628, 0.0251815] | 8/0/4 |

## Mean TV by scenario: selection-resolved versus control

| candidate | scenario | mean improvement | wins/ties/losses |
|---|---|---:|---:|
| action_groups_degree1 | S2 | -0.0116242 | 1/0/3 |
| action_groups_degree1 | S3 | 0.00644353 | 4/0/0 |
| action_groups_degree1 | S23 | 0.00137104 | 2/0/2 |
| degree1_deviation | S2 | -0.00461855 | 1/0/3 |
| degree1_deviation | S3 | 0.00517983 | 4/0/0 |
| degree1_deviation | S23 | -0.00445342 | 2/0/2 |

## Stage-2 selection audit

| candidate | selected candidates across 12 blocks | structural no-op |
|---|---|---:|
| action_groups_degree1 | `{'no_op': 6, 'ridge_0.01': 2, 'ridge_1': 4}` | 1 |
| degree1_deviation | `{'no_op': 9, 'ridge_1': 2, 'ridge_10': 1}` | 3 |

## Lambda audit: degree-1 global versus declared deviation coordinate

A smaller lambda is operationally treated as a more active coordinate. This is a selector description, not proof that a degree is scientifically correct.

| candidate | global more active | deviation more active | tie |
|---|---:|---:|---:|
| action_groups_degree1 | 0.417 | 0.083 | 0.500 |
| degree1_deviation | 0.417 | 0.083 | 0.500 |

## Worst held action: selection-resolved models

| model | metric | mean block-wise worst value | worst-action counts |
|---|---|---:|---|
| action_groups_degree1_selection_resolved | candidate_argmax_agreement | 0.430869 | `{'0': 9, '4': 3}` |
| action_groups_degree1_selection_resolved | mean_candidate_tv | 0.197678 | `{'0': 3, '2': 5, '4': 2, '5': 2}` |
| action_groups_degree1_selection_resolved | mean_excess_kl | 0.119048 | `{'0': 5, '2': 3, '4': 2, '5': 1, '6': 1}` |
| action_groups_degree1_selection_resolved | p95_candidate_tv | 0.239303 | `{'0': 5, '2': 5, '3': 1, '5': 1}` |
| degree1_deviation_selection_resolved | candidate_argmax_agreement | 0.507842 | `{'0': 10, '4': 2}` |
| degree1_deviation_selection_resolved | mean_candidate_tv | 0.202221 | `{'0': 4, '1': 1, '2': 5, '5': 2}` |
| degree1_deviation_selection_resolved | mean_excess_kl | 0.116097 | `{'0': 6, '1': 1, '2': 3, '5': 2}` |
| degree1_deviation_selection_resolved | p95_candidate_tv | 0.233761 | `{'0': 6, '2': 4, '3': 1, '4': 1}` |

## Files

- `joint_lowdim_confirm_aggregate.json`: complete machine-readable audit and all block values.
- `joint_lowdim_paired_deltas.csv`: primary and stage-1 paired comparisons at the outer-block level.
- `joint_lowdim_per_action.csv`: per-action summaries with held-cell coverage.
- `joint_lowdim_lambda_audit.csv`: coordinate lambda summaries.

## Next falsification test

The present result can establish only whether these frozen mechanisms transfer in this synthetic joint protocol. A high-N scaling or structured-holdout replication remains necessary to test robustness beyond these four outer splits.
