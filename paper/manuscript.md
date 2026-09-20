# Selection-Gated Transfer Under Sparse State–Action Support

## A synthetic study of low-dimensional mechanisms, selection, exact rollout, and high-N scaling

**Status:** preprint manuscript draft; synthetic predictive study; not a causal or deployment evaluation.

## Abstract

When a model must predict transitions for rarely observed states and state–action cells, sharing structure across states can reduce variance but can also create negative transfer. We study this trade-off in a controlled synthetic benchmark with held-out state and action cells, explicit train/selection/test separation, rank-admissible model families, and an autoregressive (AR) or no-transfer fallback. The study evaluates unselected shared mechanisms, selection-gated Stage-1 mechanisms, low-dimensional action-conditioned candidates, Stage-2 nullspace corrections, exact multi-step distribution propagation, and three sequence-count levels.

The evidence supports a conditional rather than universal conclusion. In the joint low-dimensional confirmatory panel, all 12 formal blocks and 300 model artifacts passed computational checks, but selection-resolved pooled contrasts were close to zero and varied by scenario. A subsequent exact-occupancy analysis found a small Stage-1 degree-1 deviation improvement of approximately 0.0034–0.0036 in four-step TV relative to a shared-global control in a fixed synthetic environment. The improvement remained positive in all 12 outer blocks under the original evaluation batch, a non-overlapping held-out batch, and a trajectory-generator seed perturbation. These are robustness checks on a shared fixed environment, context, and fitted models, not independent outer replications. Selection-resolved Stage-2 corrections did not add stable improvement. In the high-N experiment, 72/72 blocks passed and all 18 N-by-scenario-by-condition cells had positive mean endpoint changes, but universal accumulation and universal endpoint retention were not supported; effects depended on scenario, condition, metric, and horizon.

The resulting claim is deliberately narrow: a rank-admissible low-dimensional Stage-1 representation can yield a small and reproducible fixed-action predictive association in a controlled synthetic environment, while selection and support coverage remain material bottlenecks. The study does not establish causality, policy value, reward or regret improvement, real-data validity, encoder performance, or deployment benefit.

## 1. Introduction

Distribution shift is often discussed as a single change from training to test data. In structured transition problems, however, several kinds of scarcity can occur simultaneously: a state may be absent, an action-conditioned cell may be absent, or a state may be observed only under a subset of actions. These forms of support loss need not be repaired by the same inductive bias. A shared mechanism can borrow statistical strength, but an incorrectly shared mechanism can transfer error into cells where the model has no direct evidence.

This paper studies selective transfer under sparse state–action support. The benchmark is synthetic by design. That choice makes it possible to freeze the transition truth, define held-out cells, separate fitting from selection and testing, propagate predicted distributions exactly, and test whether more data or a more elaborate correction actually changes a model decision. The goal is not to claim that a particular symbolic representation is universally correct. The goal is to identify which claims survive support-aware evaluation.

The study makes four contributions.

1. It separates pipeline completion, contract-valid implementation, held-cell predictive association, and practical or mechanistic improvement.
2. It compares shared Stage-1 transfer with selection-resolved Stage-2 corrections under joint state–action sparsity.
3. It uses exact distribution propagation, held-out evaluation rows, and a trajectory-generator seed perturbation to test a small multi-step effect without introducing transition Monte Carlo noise; these variants are not independent outer replications.
4. It treats high-N scaling as a heterogeneous response surface rather than assuming that more data must monotonically improve every metric.

The central result is a boundary, not a universal success claim. A low-dimensional Stage-1 mechanism can show a small local predictive effect, but the current evidence does not justify making it the default transition mechanism under joint sparsity.

## 2. Related work and positioning

The problem is related to distribution shift and domain generalization, where performance can change when the test distribution differs from the training distribution [1]. It is also related to predictive-state modeling, which represents a state through predictions of future observations or outcomes rather than through an assumed semantic interpretation [2,3]. Our setting is narrower and more controlled: the state space and transition truth are synthetic, actions are explicit, and support masks define which state–action cells are available for fitting, selection, and evaluation.

The contribution is therefore methodological rather than a new claim about real-world domain generalization. The benchmark is designed to expose three distinctions that are easy to collapse: representation capacity versus finite-sample identifiability; shared transfer versus selection-resolved intervention; and one-step predictive association versus multi-step or policy value. The benchmark should be read as a stress test for those distinctions, not as a replacement for real distribution-shift benchmarks.

The study is also adjacent to model-based reinforcement learning, where learned-model bias and rollout horizon affect whether model-generated data should be trusted [4], to offline-RL theory, where coverage and representation conditions constrain generalization [5], and to low-dimensional multi-task transfer [6]. Unlike those lines of work, this paper stops at fixed-action transition prediction and occupancy; it does not evaluate a learned policy, reward, or regret.

## 3. Research question and estimands

### 3.1 Research question

Under frozen synthetic transition truth and sparse support, does a low-dimensional action-conditioned shared mechanism improve held-cell transition prediction relative to a shared-global or zero-transfer control, and does that improvement survive exact multi-step propagation, held-out evaluation data, a trajectory-generator perturbation, and changes in sequence count?

### 3.2 Experimental variables

The primary variables are:

- representation: `shared_global_only`, `action_groups_degree1`, and `degree1_deviation`;
- stage: Stage-1 fit versus selection-resolved Stage-2 correction;
- scenario: S2, S3, and S23;
- condition: `state_only` and `state_action` in the high-N study;
- sequence count: 4,096, 16,384, and 65,536;
- evaluation horizon: one-step through four-step exact occupancy.

The AR or no-transfer baseline is retained as a fallback and as a separate comparison. Results with different controls are not pooled into one effect estimate.

### 3.3 Metrics and sign convention

The primary transition metrics are total variation (TV), excess KL, and candidate argmax agreement. A positive paired improvement means lower TV or KL, or higher agreement, for the candidate relative to its declared control. The exact-rollout analysis reports absolute TV improvement at horizon four.

The outer experimental units are scenario-by-split blocks. Five training seeds inside a block are averaged and are not treated as independent outer experiments. In the high-N experiment, the three N levels are nested prefixes and therefore are not independent samples of a population of datasets.

### 3.4 Evidence ceiling

The experiments can establish predictive association under the declared synthetic data-generating process. They cannot establish causal effects, policy value, reward or regret improvement, real-data validity, encoder recovery, or deployment benefit. Exact rollout evaluates fixed action sequences; it is not a learned-policy evaluation.

## 4. Benchmark and protocol

### 4.1 Support-aware splits

The benchmark constructs fit, selection, and test units separately. The held evaluation units include unseen states and/or unseen action-conditioned cells depending on the scenario. The selector is allowed to use selection units but not held test units. The study reports both observation-weighted and equal-cell sensitivity where available.

### 4.2 Model families

The shared mechanism uses a frozen low-dimensional basis with separate global and action-conditioned coordinates. Stage-1 estimates the declared mechanism from fit units. Stage-2 adds a nullspace correction only when the rank and contract gates admit the requested channel. Structural no-ops are recorded rather than silently treated as successful interventions.

The benchmark also includes an AR/no-transfer fallback. This fallback is important because the scientific question is not whether any structured model can fit the data, but whether sharing improves prediction on held units enough to justify retaining the mechanism.

### 4.3 Exact occupancy evaluation

The exact-rollout package removes transition Monte Carlo noise by propagating the full state distribution through the fitted transition tables for four steps. The same candidate and shared-global control are evaluated under fixed behavior-replay and uniform fixed-action sequences. The protocol is repeated on the original evaluation batch, a non-overlapping held-out batch, and a trajectory-generator seed perturbation. The fitted models, synthetic environment, raw context, and outer split structure remain fixed across these variants; they are robustness checks rather than independent outer replications.

### 4.4 High-N scaling

The high-N design contains 3 sequence counts × 3 scenarios × 2 conditions × 4 fresh split seeds = 72 blocks, with five training seeds per block. The primary readout is the paired `CHANNEL - AR` contrast across N, condition, and scenario. The design is intended to test finite-sample predictive scaling; it is not a causal or policy experiment. We distinguish four audit quantities: positive endpoint means, positive directional `t=4 - t=1` cells, strong accumulation cells exceeding the frozen practical threshold, and universal retention/accumulation requiring the corresponding condition in all 18 cells. The aggregate JSON packages explicitly mark `formal_confirmatory=false` and `causal_eligible=false`.

## 5. Results

### 5.1 Joint low-dimensional confirmatory panel

The formal joint panel completed 12/12 blocks with 300/300 model artifacts verified. This establishes pipeline and predictive eligibility for the declared synthetic estimand; it does not establish a generally improved model.

The selection-resolved pooled mean-TV improvements were:

| Candidate | Mean TV improvement | Descriptive interval | Wins/ties/losses |
|---|---:|---:|---:|
| action-groups degree 1 | -0.001270 | [-0.006913, 0.004373] | 7/0/5 |
| degree-1 deviation | -0.001297 | [-0.006666, 0.004071] | 7/0/5 |

Positive values favor the candidate. Thus neither candidate showed a stable pooled advantage. The scenario profile was heterogeneous. For `degree1_deviation`, the mean TV improvements were -0.00462 in S2, +0.00518 in S3, and -0.00445 in S23. For action-groups degree 1, the corresponding values were -0.01162, +0.00644, and +0.00137. The S3 4/4 positive pattern therefore cannot be generalized to the joint panel.

Stage-2 selection also frequently chose no-op: 9/12 blocks for degree-1 deviation and 6/12 for action-groups degree 1. This is evidence that the correction channel often had no selected support or no decision-changing value under the frozen protocol.

### 5.2 Exact four-step occupancy

The exact occupancy analysis focused on the degree-1 deviation Stage-1 model relative to the shared-global control. The primary endpoint was four-step TV improvement under fixed action sequences.

| Evaluation set | Behavior replay | Uniform fixed actions | Positive blocks |
|---|---:|---:|---:|
| Original evaluation batch | +0.003406 | +0.003386 | 12/12 |
| Non-overlapping held-out batch | +0.003477 | +0.003329 | 12/12 |
| Generator-seed perturbation | +0.003583 | +0.003495 | 12/12 |

This is the strongest positive result in the joint low-dimensional branch, but its scope is narrow: fixed synthetic environment, fixed context, fixed action rules, and a comparison against shared-global rather than AR. Selection-resolved correction was not better than Stage-1, and action-groups showed only small and unstable multi-step improvement.

The exact propagation is useful because the sampled rollout showed weaker uniform-action stability. Replacing sampled transitions with full distribution propagation removed that source of noise while retaining the same direction across outer blocks. This is a different estimand from the joint one-step held-cell comparison: it changes the horizon, propagated quantity, fixed action rule, initial distribution, and shared-global control. The positive four-step result is therefore not a replication of the pooled one-step effect.

### 5.3 High-N scaling

Both high-N packages completed all 72 blocks. Each package had 18 N-by-scenario-by-condition endpoint cells with positive mean four-step change. However, the aggregate audits did not support universal accumulation or universal endpoint retention.

| High-N package | Strong accumulation | Positive directional endpoint cells | Positive endpoint means | Universal accumulation | Universal t=4 retention |
|---|---:|---:|---:|---|---|
| Uniform post-first-step actions | 6/18 | 18/18 | 18/18 | No | No |
| Repeat each held unit's first action | 7/18 | 18/18 | 18/18 | No | No |

The repeat-action package is a sensitivity analysis, not a policy evaluation: after the first held transition, it applies a deterministic fixed action rule rather than a learned controller. Neither high-N package is formal confirmatory evidence; their role is to characterize heterogeneous predictive scaling and falsify a universal accumulation claim.

The pattern was heterogeneous. At N=4,096, several S2 state-action contrasts were near zero or negative while S3 was more favorable. At N=65,536, many TV/KL means moved toward transfer, but argmax did not show a uniform improvement and several four-split intervals still crossed zero. Repeat-action evaluation showed a similar qualitative pattern.

The correct conclusion is not that high N solves transfer. It is that more data can improve some continuous probability metrics under some support conditions while leaving scenario dependence, metric disagreement, and structural selection unresolved.

### 5.4 Stage-2 and implementation boundary

The action-channel branch exposed a material implementation hazard: Gram-matrix eigenvalue substitution changed near-zero singular-value decisions relative to the frozen cell-level contract. Direct SVD reproduced the contract geometry, while the mismatched runtime geometry could not support the intended confirmatory intervention.

The corrected pilot was therefore treated as a retrospective implementation-corrected decision pilot, not as a fresh confirmation. No channel passed the pre-frozen combined TV/KL/argmax decision gate. This result supports stopping the current Stage-2 expansion; it does not prove that every possible action-channel correction is useless.

## 6. Discussion

### 6.1 What the study establishes

The study establishes a conditional evidence boundary. Unselected or overly broad transfer can be harmful under joint sparsity. A rank-admissible Stage-1 low-dimensional mechanism can produce a small fixed-action predictive association that survives exact propagation, held-out evaluation rows, and a trajectory-generator perturbation. The effect is not large enough, in the current environment, to justify a universal default or further same-environment tuning. Stage-2 corrections are not automatically valuable; selection frequently chooses no-op and the evaluated corrections do not pass a decision-level gate.

### 6.2 Representation, support, and selection are separate bottlenecks

The high-N results show why “more data” is not a sufficient explanation. N changes cell coverage, but it does not guarantee that the selected mechanism matches the target estimand. The joint panel shows why “a positive scenario” is not a sufficient explanation. Scenario-specific gains can coexist with negative transfer elsewhere. The exact rollout shows why one-step and horizon results must use the same candidate, control, action rule, initial distribution, and baseline if they are to affect the same model decision.

### 6.3 Practical model implication

The evidence supports a hybrid design principle rather than one universal model:

```text
action/context baseline
  + selection-gated Stage-1 shared mechanism
  + optional low-dimensional deviation
  + seen-state residual
  + AR/no-op fallback
```

The optional deviation should not be enabled by default without an untouched environment/context test. The current evidence supports retaining the fallback and rejecting automatic Stage-2 correction.

## 7. Limitations

1. The exact positive effect is concentrated in a fixed synthetic environment and context.
2. The joint confirmatory candidate comparisons are heterogeneous and do not establish a pooled positive effect.
3. High-N levels are nested prefixes rather than independent dataset draws.
4. Four split clusters are sufficient for a descriptive evidence boundary but not a precise estimate of a small universal effect.
5. The study uses fixed-action rollout, not learned policy evaluation.
6. No observation encoder is evaluated; the state is supplied in the controlled transition study.
7. No real-data or causal identification claim is supported.
8. Large fixtures and NPZ artifacts are not bundled in this repository; the artifact release must be linked before submission.
9. The three exact-occupancy variants reuse the same fitted models, environment, context, and outer blocks; they are not independent outer replications.
10. The reported intervals are descriptive summaries across four split clusters, not family-wise-confirmatory hypothesis tests; the high-N N levels are nested prefixes.
11. The compact repository is not a self-contained rerun environment until the fixtures, manifests, dependencies, and immutable artifact archive are released.

## 8. Reproducibility and artifact status

The result packages contain frozen configurations, split manifests, runner and aggregator hashes, block reports, model artifacts, and exact-rollout reviews. The repository includes a compact evidence snapshot and provenance copies of the aggregation scripts. The copied scripts are not self-contained rerun commands: they still require the original fixtures, manifests, dependencies, and runtime layout. Large fixtures are intentionally kept outside the Git repository and should be released as a versioned archive with a DOI or immutable release URL.

The primary source packages are:

- joint confirm aggregation: `joint_lowdim_confirm_aggregate_20260801_final`;
- exact rollout and held-out evaluation: `joint-lowdim-rollout-60-60-block`;
- high-N protocol and aggregates: `action-only-runner-16-cpu-32gb`;
- project-level synthesis: `Z3_SELECTIVE_TRANSFER_FINAL_INTEGRATED_REPORT_20260804.md`.

## 9. Conclusion

Selective transfer under sparse state–action support is not a binary choice between sharing and no sharing. The useful boundary is conditional: a low-dimensional Stage-1 mechanism can yield a small, reproducible predictive association in a controlled synthetic environment, but selection, support coverage, scenario, metric, and horizon determine whether that association is decision-relevant. The present evidence supports a selection-gated hybrid with an AR/no-op fallback and argues against treating Stage-2 corrections or high-N scaling as universal remedies.

## Appendix A. Audit contract and evidence ceiling

The reported PASS counts are contract-level results. They verify that the declared blocks, artifacts, hashes, and aggregate schemas were present and internally admissible for the synthetic predictive estimands. They do not convert the experiments into formal causal tests, independent population replications, or learned-policy evaluations.

The strongest positive result is the degree-1 deviation Stage-1 exact-occupancy contrast in one fixed synthetic environment and context. Its four-step improvement is positive in all 12 outer blocks under three evaluation variants, but the estimand is fixed-action occupancy relative to a shared-global control. It is therefore reported as a conditional predictive association. The joint one-step panel, Stage-2 correction panel, and high-N scaling panel are retained because they delimit when that local association fails to become a universal transfer rule.

The repository's `paper/claims.md` is the operational claim ledger. The source report snapshots under `evidence/source_reports/` are the compact provenance layer; the large fixtures and model arrays remain pending an immutable artifact release.
Both aggregate JSON records mark the packages as pipeline-eligible and predictive-eligible, but `formal_confirmatory=false` and `causal_eligible=false`. Those flags are part of the reported result, not an implementation footnote.

## Appendix B. Estimands and audit definitions

For candidate model `c` and declared control `b`, one-step cell-level improvements are defined as `ΔTV = TV(b) - TV(c)`, `ΔKL = KL(b) - KL(c)`, and `ΔA = A(c) - A(b)`, so positive values favor the candidate. The joint panel aggregates these improvements over held cells and scenario-by-split outer units; its intervals are descriptive mean plus or minus 1.96 standard errors across the four split clusters within each scenario.

The exact-rollout estimand is the absolute horizon-four TV difference between the shared-global control and the degree-1 deviation Stage-1 candidate after exact propagation under a fixed action rule and initial distribution. It is not the same estimand as the joint one-step cell average.

For high-N, the primary accumulation contrast is the paired improvement at `t=4` minus the paired improvement at `t=1`. A positive endpoint mean is an average direction within one N-by-scenario-by-condition cell; directional positivity requires that contrast to be positive, while strong accumulation additionally requires the frozen practical threshold of 0.005. Universal claims require the corresponding condition in all 18 cells and are rejected by either aggregate JSON package.

## References

[1] Koh, P. W., Sagawa, S., Marklund, H., et al. “WILDS: A Benchmark of in-the-Wild Distribution Shifts.” *Proceedings of ICML*, 2021. https://proceedings.mlr.press/v139/koh21a.html

[2] Siddiqi, S. M., Boots, B., and Gordon, G. J. “Reduced-Rank Hidden Markov Models.” *Proceedings of AISTATS*, 2010. https://proceedings.mlr.press/v9/siddiqi10a.html

[3] Sun, W., Venkatraman, A., Boots, B., and Bagnell, J. A. “Learning to Filter with Predictive State Inference Machines.” *Proceedings of ICML*, 2016. https://proceedings.mlr.press/v48/sun16.html

[4] Janner, M., Fu, J., Zhang, M., and Levine, S. “When to Trust Your Model: Model-Based Policy Optimization.” *Advances in Neural Information Processing Systems*, 2019. https://proceedings.neurips.cc/paper/2019/hash/5faf461eff3099671ad63c6f3f094f7f-Abstract.html

[5] Foster, D. J., Krishnamurthy, A., Simchi-Levi, D., and Xu, Y. “Offline Reinforcement Learning: Fundamental Barriers for Value Function Approximation.” *Proceedings of COLT*, 2022. https://proceedings.mlr.press/v178/foster22a.html

[6] Cella, L., Lounici, K., Pacreau, G., and Pontil, M. “Multi-task Representation Learning with Stochastic Linear Bandits.” *Proceedings of AISTATS*, 2023. https://proceedings.mlr.press/v206/cella23a.html
