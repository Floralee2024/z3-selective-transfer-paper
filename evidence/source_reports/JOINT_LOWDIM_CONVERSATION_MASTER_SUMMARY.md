# Joint lowdim rollout：设计、证据、共识与未完成工作总档案

## 1. 当前结论与决策摘要

本轮工作的成熟结论不是“模型获得了策略能力”或“恢复了真实机制”，而是一条范围严格受限的预测结论：

> 在 synthetic env_2、固定 context mean、固定 behavior-replay 或 uniform action 序列下，`degree1_deviation_stage1` 相对 `shared_global_only` 存在小幅但稳定的 action-conditioned transition/rollout 预测关联。四步 exact occupancy TV 的绝对改善约为 +0.0034～+0.0036，对应约 6%–7% 的相对 TV 下降；该改善跨 transition 精确传播、不重叠 evaluation holdout 和新的 trajectory generator seed 保留。

当前模型决策：

- 保留 `degree1_deviation_stage1` 作为具有稳定窄预测收益的候选结构。
- 暂不保留 Stage-2 selection-resolved correction，因为没有额外实质收益，通常略低于 Stage-1。
- 不把 `action_groups` 视为具有稳定四步 rollout 改善的结构。
- 停止继续追加相同 env_2/context/mechanism 下的 evaluation 或 generator seeds。
- 不把当前证据升级为 policy、reward、regret、因果、真实数据、跨环境或通用 planning 结论。
- 如果要判断当前小幅效应能否通过建模提升，下一项唯一有明确决策价值的工作是 oracle-projected headroom diagnostic；该工作尚未完成。

## 2. 最终冻结的研究设计

### 2.1 真正要回答的问题

在固定 synthetic env_2 action sequences 和固定 env_2 raw context 下，低维 candidate transition models 是否比 `shared_global_only` 更接近 synthetic oracle，并且这种差异能否在四步状态分布传播中保留？

### 2.2 主动改变的变量

核心模型比较中，主动改变的是：

- model representation：`shared_global_only`、`action_groups_degree1`、`degree1_deviation`；
- model stage：Stage-1 与 selection-resolved；
- evaluation action scheme：behavior action replay 与 uniform fixed actions。

后续证伪梯度中，每次只改变一个主要不确定性来源：

1. sampled transition rollout → 完整 64-state exact distribution propagation；
2. reference evaluation rows → 不重叠 held-out rows；
3. 原 trajectory generator seed → 新 generator seed，同时保持 mechanism/residual seeds 与环境数组不变。

### 2.3 主要 estimand

主要差值定义为：

`shared_global_only occupancy TV - candidate occupancy TV`

正值表示 candidate 比 control 更接近 oracle。

统计组织方式：

- 3 scenarios：S2、S3、S23；
- 4 split seeds：20260748–20260751；
- 5 training seeds 在每个 scenario × split 内先求均值；
- 12 个 scenario × split 是 outer descriptive blocks；
- 5 training seeds 不是 5 个独立外部复现；
- 同一 scenario 内的 splits 共享 evaluation batch，因此 12 个正负符号只能作为描述性稳定性，不能当作 12 个独立 evaluation datasets。

### 2.4 冻结环境与传播设置

- evaluation environment：env_2；
- raw context mean：`[0.4, 0.55, 0.3]`；
- horizon：4；
- evaluation episodes：4096；
- states：64；actions：7；transition candidates：7；
- policies：behavior action replay、uniform fixed actions；
- exact occupancy：对每个固定初始状态/action 序列传播完整 64-state probability distribution，不进行 transition categorical sampling。

### 2.5 支持标准

成熟 exact/holdout/new-seed 测试的支持条件包括：

- `degree1_deviation_stage1` 在两种 action schemes 下的 t=4 mean improvement 均大于 0；
- 描述性幅度至少保留 reference exact improvement 的 50%；
- oracle self-TV 必须等于 0；
- candidate 同步置换不得改变 exact occupancy；
- 全部报告、metric keys、模型、配置和数据 provenance 必须完整且一致；
- 所有数值必须有限。

### 2.6 永久 non-claims

当前任何 PASS 都不能推出：

- policy 已学到或改善；
- reward、policy regret 或决策质量改善；
- action intervention 对真实 outcome 有因果效应；
- candidate features 就是真实生成机制；
- synthetic env_2 结果适用于真实数据；
- 跨 env/context 或更长 horizon 泛化；
- 通用 planning、encoder utility 或实际模型能力获得实质改进。

## 3. 关键代码问题、修正和最终规范

### 3.1 Context contract

发现的问题：旧 `model_probability` 读取模型的 `context_mean/context_scale` 后却传入全零 context。零值代表模型训练 context mean 的标准化位置，不是 frozen config 声明的 env_2 context mean。与此同时 oracle 在 env_2 context mean 下计算，导致 model 与 oracle 在不同 context 上比较。

最终共识和实现：

- evaluation 应使用环境的 raw context mean，而不是模型训练均值；
- 每个模型内部接收 `(raw_env_context - training_context_mean) / training_context_scale`；
- oracle 与 model 必须绑定到同一个 raw context；
- env spec 必须显式存储 `environment_id` 和 `context_mean`。

### 3.2 Categorical sampling 边界

发现的问题：浮点概率行和略小于 1 时，`(cumsum(prob) < u).sum()` 可能返回 candidate=7，引发越界状态并导致后续索引崩溃。

最终修正：

- categorical rows 先以 float64 归一；
- 最后一个 CDF 元素强制设为 1；
- exact occupancy 主结论进一步完全移除了 transition categorical sampling。

### 3.3 env spec

最终 env spec v2：

- 明确 env_2 context mean；
- oracle probabilities 使用 float64 并严格归一；
- probability row-sum 最大误差 `4.44e-16`；
- reward expectation 的 candidate-axis 计算已修正，重算最大误差为 0；
- schema、environment、context 和 source provenance 均被冻结。

### 3.4 t=0 和时间语义

最终规则：

- t=0 occupancy TV=0、initial agreement=1，作为强制 sanity assertion；
- t=0 occupancy 行保留在 raw output，但从 paired/block/final aggregation 排除；
- `mean_one_step_transition_tv` 的 t=0 表示 0→1 transition，应保留；
- intermediate agreement 命名为 `state_agreement_at_t`；
- `final_state_agreement_vs_oracle` 只在 t=horizon=4 输出；
- 不允许用平凡 t=0 值稀释非平凡 rollout 指标。

### 3.5 Launcher、恢复与 provenance

最终规范：

- 正式矩阵必须由 launcher 明确覆盖 3×4×5=60 model blocks；
- exact evaluation 用 12 个 outer blocks，每块内部复用 5 training seeds；
- 独占锁防止重复 launcher；
- 已有 PASS 只有在 config/env/runner/dependency/model/data hashes 全部一致时才可跳过；
- partial output 不自动覆盖；
- 完成后自动 aggregate；
- smoke test 必须走与正式运行相同的生产路径；
- 先完成一个正式 block，再扩展至完整矩阵。

## 4. 证据递进与成熟实验结论

### 4.1 Corrected sampled rollout v2

完整性：

- 300/300 模型 artifacts 有效；
- 60/60 formal blocks PASS；
- 7800 raw metric rows；
- 5760 nontrivial paired rows；
- 60/60 resume 验证通过。

单步 transition TV，0→1：

| model | behavior replay | uniform fixed | outer-block stability |
|---|---:|---:|---:|
| degree1-deviation Stage-1 | +0.005913 | +0.005793 | 两者均 12/12 正 |
| action-groups Stage-1 | +0.002029 | +0.001973 | 两者均 12/12 正 |

成熟解释：degree1-deviation 具有最强的一步 action-conditioned predictive association。action-groups 在一步上有小幅关联，但该优势没有稳定传播至 t=4。

sampled t=4 occupancy：

- degree1-deviation Stage-1：behavior +0.003687，9/12 正；uniform +0.002091，6/12 正；
- action-groups Stage-1：behavior -0.000354；uniform -0.001335。

sampled rollout 表明 mean 可能为正，但 uniform block stability 不足，因此触发 exact propagation 测试。

sampled final-state agreement：

- behavior：+0.012223；
- uniform：+0.015466；
- 两者均 12/12 正。

该指标依赖 frozen inverse-CDF common-random-number coupling 与 candidate order。它是有效的耦合诊断，但不是 permutation-invariant distribution distance，因此被降为辅助证据，不作为核心成熟结论。

### 4.2 Reference exact occupancy

改变：只把 sampled transitions 替换为完整 distribution propagation。

| action scheme | control TV | candidate TV | improvement | positive blocks |
|---|---:|---:|---:|---:|
| behavior replay | 0.054116 | 0.050711 | +0.003406 | 12/12 |
| uniform fixed | 0.054516 | 0.051131 | +0.003386 | 12/12 |

验证：

- oracle self-TV=0；
- candidate permutation max error=`6.94e-18`；
- 12/12 reports PASS；
- 2400 raw rows、1920 paired rows；
- 全部有限、唯一；resume PASS。

成熟解释：sampled uniform sign instability 主要包含 transition Monte Carlo noise；移除该噪声后，t=4 degree1-deviation 改善在所有 outer blocks 为正。

### 4.3 Disjoint held-out evaluation batch

改变：reference trajectory IDs 0–4095 → held-out IDs 4096–8191；uniform seed 20260803 → 20260804。

| action scheme | holdout improvement | reference improvement | retained magnitude | positive blocks |
|---|---:|---:|---:|---:|
| behavior replay | +0.003477 | +0.003406 | 102.1% | 12/12 |
| uniform fixed | +0.003329 | +0.003386 | 98.3% | 12/12 |

held-out 与 reference trajectory IDs 无交集；初始状态和 action arrays 明确改变。

成熟解释：+0.0034 不是原始 4096-row evaluation sample 的偶然结果。

### 4.4 Independent trajectory generator seed

改变：trajectory generator seed 20261300 → 20261301。

保持：mechanism seed=20261200、residual seed=20261300、env_2、context、模型和 oracle。

三种 scenario 均重新生成 65536×4 trajectories；生成环境数组及 environment NPZ hashes 与参考逐 scenario 完全相同，只有 trajectory generation 改变。

| action scheme | new-seed improvement | reference improvement | retained magnitude | positive blocks |
|---|---:|---:|---:|---:|
| behavior replay | +0.003583 | +0.003406 | 105.2% | 12/12 |
| uniform fixed | +0.003495 | +0.003386 | 103.2% | 12/12 |

成熟解释：当前窄预测关联不仅跨 evaluation rows，也跨一个独立 trajectory generator seed 保留。

### 4.5 Stage-2 与 action-groups 决策

跨 reference exact、held-out 和 independent generator-seed tests：

- degree1 selection-resolved 通常比对应 Stage-1 低约几万分之几；
- 没有额外实质收益支持 Stage-2 correction；
- action-groups Stage-1 的 t=4 exact improvement 通常仅约 +0.0001～+0.0002，正块约 6/12～7/12；
- action-groups selection-resolved 的 t=4 mean 通常为负。

成熟模型决策：保留 degree1-deviation Stage-1 的窄预测结论；暂不保留 Stage-2 correction；不升级 action-groups。

## 5. 被修正、取代或降级的早期结果

### 5.1 原始 context-mismatched rollout

旧结果中 model 实际在训练 context mean 的标准化位置预测，oracle 在 env_2 context mean 下预测。该比较不公平，因此旧 aggregate 数字不能作为最终科学结论。后续 env_2 v2 全量重跑取代了它。

### 5.2 t=0 聚合结果

旧聚合若把 occupancy TV=0 或 agreement=1 的 t=0 平凡值纳入，会稀释指标。最终 aggregate 已排除这些值；旧的混合均值不再使用。

### 5.3 “t=4 全部候选转负”

这一判断来自较早版本/抽样设置，不是最终 corrected exact 结果。最终 exact tests 明确显示 degree1-deviation Stage-1 在两种 action schemes 下均约 +0.0034～+0.0036、12/12 正。action-groups 则仍弱或不稳定。

### 5.4 Final-state agreement 的地位

约 +0.012～+0.015 的 agreement improvement 在 corrected sampled coupling 下有效，但依赖共同随机数和 candidate order。它不能替代 permutation-invariant occupancy TV，因而不再承担核心结论。

## 6. 已达成共识的设计理念

### 6.1 证据层级必须分开

必须明确区分：

1. 代码跑通；
2. 数据结构、coverage 和 provenance 合格；
3. 模型能够预测某种关联；
4. 干预确实改变 outcome；
5. 对 policy、模型能力或实际机制有实质改善。

当前只达到第 3 层的 synthetic predictive evidence；没有达到第 4–5 层。

### 6.2 每个实验先冻结四件事

- 真正问题；
- intervention 与 estimand；
- 什么结果算支持；
- 即使 PASS 也绝不能声称什么。

### 6.3 一个测试必须改变决策

如果无论测试结果如何，下一步决策都不变，该测试属于研究装饰，应删除。这个原则最终导出了明确停止规则：不再追加相同 env_2 的 evaluation/generator seeds。

### 6.4 不通过重新评测“放大”效应

更多评测可以提高稳定性证据，但不能把小效应变成中效应或大效应。效应增大必须来自模型、数据或训练目标改变，并构成新的实验。

### 6.5 分布指标优先使用 exact propagation

当 state space 足够小且目标是 occupancy distribution 时，应使用完整概率传播，避免 transition Monte Carlo noise 和耦合顺序伪影。

### 6.6 Context 是实验变量，不是实现细节

环境 raw context 决定 oracle；模型训练 mean/scale 只是标准化参数。两者不可混淆，且 model/oracle 必须在同一 raw context 比较。

### 6.7 小而稳定优于被包装成“大效果”

当前 absolute improvement 约 +0.0035、relative TV reduction 约 6%–7%。应如实称为小幅稳定预测改善，而不是通过选择 metric、baseline、horizon 或 coupling 将其包装成中大效应。

### 6.8 负结果也应直接影响设计

Stage-2 没有额外收益、action-groups rollout 不稳定，都是有效结果。它们支持删减设计，而不是触发无限补测。

## 7. 明确尚未完成的工作

### 7.1 Oracle-projected headroom diagnostic：未完成

目的：判断 degree1-deviation Stage-1 当前约 +0.0035 是否接近该表示结构的上限。

推荐设计：

1. 保持 degree1-deviation Stage-1 feature class 不变；
2. 直接使用 synthetic oracle 的完整 64×7 transition cells 拟合，不受有限训练样本影响；
3. 在 independent generator-seed trajectories 上 exact rollout；
4. 比较 oracle-projected ceiling 与当前实际模型 improvement。

可能决策：

- 若 ceiling 也只有约 +0.004～+0.005：当前接近结构上限，应停止优化；
- 若 ceiling 明显高于当前，例如超过当前两倍且跨过预先定义的实用阈值：才有理由研究数据覆盖、正则化或训练目标；
- 若 ceiling 高、实际模型低：问题更可能在有限样本估计或优化，而不是表示能力。

尚未冻结的部分：什么数值算“中幅/大幅”以及最低实用阈值，尚未定义。没有该阈值之前，不应启动调参。

### 7.2 提升 effect size 的模型实验：未开始

尚未实施：

- 新的数据覆盖设计；
- partial pooling/regularization 调整；
- multi-step occupancy-aligned objective；
- action×context 扩展；
- 新模型结构或嵌套 model selection。

这些工作只有在 headroom diagnostic 显示存在足够上限时才有必要。

### 7.3 跨环境与跨 context：未测试

尚未在 env_0/env_1 或新的 context mean 上进行同等级 exact propagation。因此不能声称 cross-environment/context generalization。

### 7.4 Policy、reward 和 regret：未测试

当前 actions 均是固定 replay 或 uniform actions，不是 learned policy。没有 policy optimization、reward comparison 或 regret estimand。

### 7.5 因果与真实数据：未测试

没有真实 intervention、外部数据或 real-world outcome validation。synthetic oracle 只支持 synthetic predictive sanity。

### 7.6 完全独立的统计复现：未建立

虽然已经更换一个 generator seed，但同一 scenario 内的 split blocks 仍共享 evaluation batch。当前 block fractions 是描述性稳定性，不是正式独立重复实验的推断统计量。

## 8. 当前停止规则与未来分支

### 8.1 当前应停止的工作

- 不再追加相同 env_2/context/mechanism 的 generator seeds；
- 不再用更多相同 rollout 指标试图“放大”+0.0035；
- 不再为 Stage-2 correction 做同类确认测试；
- 不把 pipeline PASS 当成科学结论升级。

### 8.2 只有以下目标才需要新测试

| 希望改变的决策/声明 | 必要测试 |
|---|---|
| 是否值得继续优化 degree1 Stage-1 | oracle-projected headroom diagnostic |
| 是否跨环境/context 泛化 | env_0/env_1 或新 context mean exact evaluation |
| 是否改善策略 | learned-policy evaluation、reward 与 regret |
| 是否有真实因果或数据价值 | 独立真实数据与明确 intervention design |
| +0.0035 是否具有实际价值 | 先定义最低有用 effect 与部署成本 |

如果暂时不准备提出这些新声明，当前 rollout 研究应在此结束。

## 9. 主要产物索引

- Corrected sampled rollout：[ENV2_V2_REVIEW.md](joint_lowdim_rollout_env2_v2_20260803/ENV2_V2_REVIEW.md)
- Reference exact propagation：[EXACT_OCCUPANCY_REVIEW.md](joint_lowdim_exact_occupancy_env2_v1_20260803/EXACT_OCCUPANCY_REVIEW.md)
- Disjoint holdout：[HOLDOUT_EVALUATION_REVIEW.md](joint_lowdim_exact_occupancy_holdout_env2_v1_20260803/HOLDOUT_EVALUATION_REVIEW.md)
- Independent generator seed：[INDEPENDENT_GENERATOR_SEED_REVIEW.md](joint_lowdim_independent_generator_seed_20261301_env2_v1_20260803/INDEPENDENT_GENERATOR_SEED_REVIEW.md)
- Independent generation audit：[generation_report.json](joint_lowdim_independent_generator_seed_20261301_env2_v1_20260803/generation_report.json)
- New-seed exact comparison：[newseed_vs_reference_aggregate.json](joint_lowdim_independent_generator_seed_20261301_env2_v1_20260803/newseed_vs_reference/newseed_vs_reference_aggregate.json)

## 10. 最终一句话版本

我们已经把一个最初存在 context、sampling 和 metric-semantics 风险的 rollout 流程，修正为 provenance-complete、permutation-invariant、exact-distribution、跨 evaluation sample 与 trajectory generator seed 的验证链；最终只保留“degree1-deviation Stage-1 具有小幅稳定的 synthetic fixed-action predictive association”这一窄结论，同时明确停止继续堆叠同类测试，并把所有更强声明留给尚未完成、且会真正改变决策的新实验。
