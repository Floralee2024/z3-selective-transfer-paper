# Z3 选择性迁移研究阶段性总结

日期：2026-08-04  
阶段：从固定高阶迁移失败，推进到可选择、可退化的迁移机制

## 0. 本阶段真正回答的问题

本研究最初比较的是 AR 与固定阶数的共享 Walsh 模型，但最终问题已经被收敛为：

> 当某个 state–action 单元数据稀少，甚至整个 state 完全未见时，模型能否从其他 state 借用跨 state 稳定、并允许 action 调制的规律；同时在证据不足时，能否自动减少借用或退化到 no-op/AR？

主动改变的变量包括：

- 是否启用跨 state 的共享机制；
- 启用哪些 degree；
- global 与 action-specific deviation 是否独立收缩；
- 是否加入只服务于已见 state 的 residual；
- 是否由真正未见的 selection units 选择 λ；
- 是否加入 selection-resolved Stage-2 nullspace correction；
- holdout 是 state-only、action-only，还是 state+action joint。

真正关心的结果是：

- held-state / held-cell TV、KL、argmax agreement；
- 不同 action 的最差表现与异质性；
- fixed-action short-horizon occupancy 是否更接近 synthetic oracle；
- 选择机制能否在没有可靠收益时退化为 no-op。

支持目标所需的证据不是 runner PASS，而是：

1. 干预对象与冻结 contract 等价；
2. 以 split/held-unit 为外层独立单位；
3. held-unit 指标相对基线有稳定、足够大的改善；
4. 改善能够跨 split、evaluation batch 或环境条件复现；
5. 结果足以改变模型保留决策。

即使全部成功，也不能直接推出因果效应、policy value、reward/regret、规划能力、真实世界普遍泛化或部署有效性。

## 1. 起点：固定高阶共享模型为什么在联合稀疏下失败

早期 runner：

- `run_z3_minimal_a2_strict_stateholdout_cpu.ps1`
- `d5_y1_z3_minimal_interaction_ablation.py`

比较了 AR 与固定的 T1、T2、T13、T123。Z3 oracle matrix 明确构造了可表示的共享真值：

| 场景 | 稳定共享机制 | 正确的固定候选 |
|---|---|---|
| S2 | degree 1 + 2 | T2 / T123 |
| S3 | degree 1 + 3 | T13 / T123 |
| S23 | degree 1 + 2 + 3 | T123 |

oracle projection、residual 正交和 T64 positive control 均通过。因此，后续失败不能解释为“生成器里根本没有对应高阶结构”。

### 1.1 IID 与 held-state 不是同一个问题

在 IID finite-sample 条件下：

- S2 中 T2 优于 T13；
- S3 中 T13 优于 T2；
- S23 中 T123 优于 T2/T13；
- 正确阶模型在数据覆盖充分时可以优于 AR。

这证明高阶真值有预测价值，并且模型能在已覆盖的 state/action 支持上学习它。但它没有证明完全未见 state 的迁移。

### 1.2 两种 holdout 给出了不同答案

只有 state holdout、没有额外 action 缺失时：

- S2 的 T2 在完整数据量下可以优于 AR；
- S3 的 T13 大致与 AR 持平；
- S23 的 T123 仍弱于 AR。

在更严格的“8 个 state 完全未见 + 每个已见 state 再缺失 2 个 action”的联合稀疏条件下：

- S2、S3、S23 均由 AR 胜出；
- 4 个 split-seed × 每 split 5 个 training seeds 的方向一致；
- 在四个 split-block 内，AR 对固定正确阶候选方向一致胜出；具体 block-level TV 差值需由权威 raw reports 重新聚合后报告。早期报告中出现的具体效应量（约 0.040、0.125、0.267）未能从原始实验产物中追溯，已撤回，待重新聚合后补报；
- 外层独立单位应是 4 个 split-block，而不是 20 个 training fits。

因此，早期成熟结论是：

> 高阶真值存在、并且能够在 IID 支持内被学习，不等于固定全量高阶机制能在有限样本和联合 state/action 稀疏下安全迁移。当前条件下，AR 的强收缩更稳健。

## 2. 旧设计暴露出的真正缺陷

旧 runner 没有明显的功能性 bug；主要问题是实验对象和研究意图没有完全对齐。

### 2.1 比较的是“零迁移 vs 全量迁移”

AR 对 held state 基本退化到 action/context baseline，相当于不借用 state 结构。固定 T123 则把所有注册的 global 和 action-deviation 高阶方向一起外推。

因此它回答的是：

> 全部借用是否优于完全不借用？

而不是最终真正关心的：

> 哪些 degree、哪些 channel 应该借用，借用多少，何时应该不借？

### 2.2 validation 不能为 unseen-unit transfer 选择强度

held states 被正确排除在 validation 之外，避免了 test 泄漏；但旧 validation 主要由已见 state 构成，因此 λ 和 early stopping 仍主要优化 seen-state fit，无法直接选择 held-state 外推强度。

这不是数据泄漏，而是 selection target 与科学目标错位。

### 2.3 global 与 action deviation 被捆绑

旧模型把 action-invariant shared structure 和每个 action 的 deviation 一起放入固定候选。action deviation 每个方向获得的数据更少，估计噪声更大，可能把 global channel 的收益抵消。

### 2.4 residual 与共享空间在受限支持上产生混叠

degree 5/6 residual 虽然在完整 64-state 空间中与低阶共享空间正交，但删除 held states 后，受限设计上的正交性不再自动成立。固定 T 模型可能在 seen states 上吸收 residual 投影，并把该误差外推到 held states。

### 2.5 主要读出曾被全状态池化

旧 `paired_against_ar` 使用 `uniform_state_all_action`，可能被 56 个已见 states 主导。研究意图要求的决定性比较应位于 held-state / held-cell，并进一步按 action 分解。

### 2.6 随机 state holdout 主要是精确模型类内的组合插值

随机保留 8/64 states 能严格测试“零训练样本 state”，但在其余 56 states 已充分覆盖时，并不等同于更强的结构化组合外推。它的结论范围应限定为当前模型类和 split 几何。

## 3. 从固定 T 模型到选择性迁移机制

上述缺陷推动了模型和实验协议的根本调整。

### 3.1 从二元比较改为可退化迁移

研究不再被简化成：

```text
AR = 不迁移
T123/T12356 = 全量迁移
```

而是允许：

```text
不借
只借低阶
只借 global
谨慎借 action deviation
证据足够时再借完整结构
```

### 3.2 模型分解

当前目标分解为：

```text
action/context baseline
+ 跨-state shared global mechanism
+ action-specific shared deviation
+ 只服务于已见 state 的 local residual
```

并要求：

- degree、global、deviation 尽量独立收缩；
- residual 相对共享空间正交；
- residual 不外推到完全未见 state；
- 不可辨识的 residual-deviation 结构直接排除；
- selection 证据不足时退化为 no-op。

### 3.3 fit / selection / test 三分

新的选择顺序是：

```text
fit units       估计共享机制
selection units 选择 λ 与 correction
test units      只做最终报告
```

这解决了旧 validation 只代表 seen-state fit、不能选择 transfer strength 的问题。

### 3.4 factorial 拆分

原先混在一起的困难条件被拆成：

- state-only；
- action-only；
- state + action joint。

这样可以判断失败主要来自 state 外推、action 稀疏还是二者交互，而不是只得到“联合困难条件失败”的总结果。

### 3.5 几何先于拟合

对 T12356，fit rank、fit nullity、fit+selection rank、selection resolution 和 channel positions 均在拟合前冻结。Stage-2 只允许在完整 action-conditioned fit nullspace 中校正，并要求 fit logits 保持不变。

这一阶段还纠正了 action-channel runner 中 Gram-eigh 改写导致的数值秩漂移，以及错误 selection operator 问题。旧的错误 channel correction 不再进入科学结果。

## 4. 当前选择性迁移机制取得的结果

### 4.1 State-only：固定模型负结果被部分改写

在 rank-admissible 的 state-only split 上，T12356 Stage-1 相对 AR 得到稳定改善：

| 场景 | Stage-1 相对 AR 的 mean ΔTV | 正向 blocks |
|---|---:|---:|
| S2 | -0.024758 | 4/4 |
| S3 | -0.017666 | 4/4 |
| S23 | -0.009412 | 4/4 |

这里负值表示 T12356 TV 更低。Stage-2 在 12/12 blocks 中均选择 no-op。

这说明：

> 早期“固定 T123 在 strict holdout 中失败”不是共享迁移本身的上限。经过 rank-admissible split、selection-unit 选择和更完整的 T12356 表示后，Stage-1 shared transfer 可以在完全未见 state 上稳定优于 AR。

但它同时说明当前 nullspace correction 没有额外价值。

### 4.2 Action-only：机制可运行，但收益很小

正式 v1.1 完成 12/12 blocks、360 个模型产物和约 3600 个 Stage-2 folds。T12356 family 整体优于 AR/T123_R，但 resolved-minus-base 的效果很小：

- shared KL 有小幅 block-level paired 改善；
- shared TV、argmax、p95-TV 的证据不足；
- residual-global 没有稳定改善；
- action 0 通常是最难 action。

因此 action-only 支持的是小幅 synthetic held-cell predictive benefit，而不是普遍性能提升。

### 4.3 Action-channel ablation：没有值得保留的 Stage-2 channel

正确修复后的 retrospective pilot 显示：

- shared-global 为结构性 no-op；
- shared-deviation 和 shared-full 的 TV/KL 改善低于冻结门槛，并伴随 argmax 下降；
- residual-global 改善 TV/argmax，但 KL 稳定恶化；
- 没有 channel 同时通过 TV、KL、argmax 守门。

正式决策是停止完整 12-block 扩展，并在最终模型中不保留当前 Stage-2 correction。

### 4.4 Joint lowdim：局部有效，不构成统一机制

12/12 blocks、300/300 artifacts 完整。相对 shared-global：

- action-groups degree1 总体 mean-TV 改善为 -0.00127；
- degree1 deviation 总体 mean-TV 改善为 -0.00130；
- 正值才表示候选更好，因此总体均不支持稳定优势；
- 两者在 S3 均出现 4/4 正向，但不能推广到 S2/S23。

λ 审计中，global 更积极 5/12、deviation 更积极 1/12、持平 6/12；两类 deviation 的低惩罚保留率均只有 1/12。

这表明 action-specific 低维结构可能在特定 truth 场景中有用，但不应成为跨场景默认机制。

### 4.5 Joint selective transfer vs AR：正式缺口已闭合

fresh action-coverage panel（20260772–75）上的 12-block prospective confirm 已完成。相对 zero-transfer AR，改善符号为正才代表 transfer 更好：

| Arm | overall ΔTV | ΔKL | Δargmax | 正向 TV blocks | 决策 |
|---|---:|---:|---:|---:|---|
| T12356 shared Stage-1 | -0.001897 | -0.005654 | -0.021760 | 5/12 | FAIL |
| LOSO selection gate | -0.002937 | -0.005418 | -0.010145 | 3/12 | FAIL |

gate 选择 shared 8/12 次，但其中 7 块的 test ΔTV 为负；selection regret 为 0.01167，retention ratio 为 -0.336。独立 held-cell 等权复算仍为 shared ΔTV -0.002215、gate -0.003094，决策不变。

因此，此前“选择性共享机制 vs zero-transfer AR 在 joint 稀疏下从未正式比较”的缺口已经闭合：**当前 shared 机制与 selector 均未达到冻结门槛，joint transfer 不进入 Y1 主干。** 这不影响 state-only/action-only 的局部正结果。

### 4.6 High-N：样本量不是唯一瓶颈

N=4096/16384/65536 的正式 scaling 显示：

- N=65536 时，多数或全部场景组合的平均 TV/KL 方向偏向 transfer；
- 多个四-split 区间仍跨 0；
- argmax 在多个组合随 N 下降；
- 18 个 trend audits 没有形成统一单调改善；
- state_action/S23 的 TV/KL 也不单调。

因此，更多数据可能改善连续概率指标，但不能消除场景、指标和结构选择问题。

### 4.6 Exact occupancy：发现可复现但很小的下游效应

degree1-deviation Stage-1 在固定 env_2、固定 action-conditioned 四步传播中取得约 `+0.0034` 的 t=4 occupancy TV 改善：

- 原 evaluation batch：behavior `+0.003406`，uniform `+0.003386`；
- 非重叠 held-out batch：`+0.003477` / `+0.003329`；
- 独立 trajectory generator seed：`+0.003583` / `+0.003495`；
- 三轮均为 12/12 blocks 正向。

但 oracle-projected diagnostic 显示，degree1 相对同样投影 control 的结构特有优势只剩约 `+0.0000596` / `+0.0000179`，即当前改善的 1.66% / 0.51%。

因此该效应可以被认定为可复现的小型 synthetic predictive effect，但不支持继续围绕相同 degree1 结构反复调参以寻求中型或大型收益。

### 4.7 真实数据：仅达到 retrospective pilot

15 条 SCOTUS cases 的数据入口和 split 流程合格，但 test 只有 5 条，来自同一法院和相邻 Term，且标签曾被 retrospective 审计查看。

候选相对 baseline：

- NLL 改善约 `+0.000830`；
- one-hot TV 改善约 `+0.024626`；
- accuracy 均为 0.6；
- selection 最终保留 no-op。

这只能称为微弱方向性的 retrospective temporal pilot，不能称为正式真实数据确认。

## 5. 旧结论现在应如何改写

旧结论：

> 在联合 state/action 稀疏条件下，AR 稳定优于固定 T2、T13、T123。

该结论仍然成立，但适用对象必须保留“固定候选阶数、全量 action-conditioned 迁移、旧选择管道”的限定。

当前更完整的结论是：

> 固定全量高阶迁移在联合稀疏下容易发生负迁移；但这不是选择性共享机制的上限。在 rank-admissible state-only 和 action-only 条件下，由未见 selection units 守门的 T12356 Stage-1 可以获得相对 AR 的预测收益。fresh joint confirm 进一步显示，当前 T12356 shared Stage-1 与 LOSO gate 相对 zero-transfer AR 均未达到冻结门槛；Stage-2 nullspace correction、完整 action-channel 和 joint lowdim 扩展也没有形成跨场景的决策级收益，因此 joint 条件应退化到 AR/no-op。

换句话说，研究已经从：

```text
高阶共享机制有没有用？
```

推进到：

```text
哪些共享方向在什么几何和数据条件下值得借用，
以及如何在证据不足时拒绝借用？
```

## 6. 昨日未完成事项的当前状态

| 昨日问题 | 当前状态 | 判断 |
|---|---|---|
| degree-specific / global-deviation 收缩 | 已在选择性模型和 joint λ 审计中部分实现 | 操作机制完成，但不能宣称选中了科学意义上“正确 degree” |
| fit/selection/test 分离 | 已实现 | 成为当前最重要的选择守门机制 |
| factorial holdout | state-only、action-only、joint 均已有正式结果 | 三者不能再混写为一个结论 |
| split-block 统计 | 已采用 | training seeds 不作为外层独立重复 |
| per-action 汇总 | joint 正式完成；action-only 仍主要是兼容性/描述性汇总 | action 0 难度信号稳定，但 action-only raw-report 级 CI 未完全闭环 |
| action-channel ablation | 正确修复的 pilot 完成 | 无 decision-changing channel，停止扩展 |
| Stage-2 selection-resolved | state-only/action-only/joint 均已测试 | 总体不支持保留 |
| Stable-HO interaction selection | 尚未实现 | 不能写成完成或负结果 |
| structured interaction holdout | 尚未完成 | trajectory held-out evaluation 不能替代它 |
| 高 N scaling | 已完成 | TV/KL 可能受益，但无统一单调改善 |
| degree 3/4 stability、ICC、recovery | 框架完成，缺语义系数导出和 truth alignment | 尚无正式科学结果 |
| rollout | fixed-action exact occupancy 已完成 | 不等于 policy 或 planning |
| encoder | 未开始，无 raw observation 输入 | 属于新阶段 |
| policy / reward / regret | 未开始 | 属于新阶段 |
| 真实数据 | retrospective pilot 完成 | 不是盲测确认 |
| 因果验证 | 未开始且当前设计不具备识别条件 | 明确排除因果结论 |

## 7. 本阶段最重要的科学判断

### 已被证据支持

1. 受控 Z3 truth 中确实存在可表示的二阶、三阶和更高阶共享结构。
2. 正确阶模型在 IID 支持内能够学习这些结构。
3. 固定全量 T 模型在联合 state/action 稀疏下明显不如 AR。
4. 经过 rank-admissible split 和 held-unit selection 的 Stage-1 shared transfer，在 state-only 上可以稳定优于 AR，在 action-only 上有小幅收益。
5. 当前 Stage-2 correction 和多数 action-specific 扩展没有足够收益，应退化为 no-op。
6. degree1 deviation 在固定 env_2 的四步 occupancy 上存在可复现的小效应。

### 做过但没有证明目标

- contract、SHA、artifact 和 optimizer PASS 证明流程可信，不证明模型能力改善；
- high-N Monte Carlo rollout 描述了 horizon 变化，但没有完成预定的 exact-distribution、t=1-baseline 判别；
- SCOTUS preflight 和 retrospective pilot 没有证明真实泛化；
- coefficient stability 框架没有产生 degree 3/4 recovery 结论。

### 仍未测试的关键假设

- env_2 的 occupancy 小效应能否跨 env/context truth 复现；
- 新的、标签未查看的真实数据 batch 是否保留方向；
- 真正 Stable-HO interaction-group selection 是否优于当前 degree/channel 守门；
- degree 3/4 系数是否具有跨环境稳定、可解释的 recovery；
- 原始 observation 能否被编码成任务充分的 state；
- 预测改善是否能转化为 policy/reward/regret 改善。

## 8. 下一阶段的最小推进路线

如果目标是继续检验当前判断，而不是扩大实验清单，优先级应为：

1. **新 env/context exact-occupancy replication**  
   这是最可能推翻“degree1 deviation 只在 env_2 有小效应”的实验。若失败，应把 rollout 结论限定在 env_2；若复现，才能开始讨论跨 context 稳定性。

2. **新的未查看标签真实数据 batch**  
   先冻结 representation、模型、λ、no-op 门槛和指标，再打开标签。它决定真实数据工作是否值得继续。

3. **按研究目标决定是否完成 degree ICC/recovery**  
   只有在论文需要“恢复了稳定机制系数”时才补 semantic coefficient export 和 truth alignment；若目标只是 held-unit prediction，这项不会改变模型保留决策，应停止。

Stable-HO、encoder、policy 和因果验证均属于新的研究阶段，不应作为当前分支“差一点完成”的尾项无限追加。

## 9. 阶段性结论

> Z3 的早期固定模型实验成功识别了一个真实失败模式：高阶真值存在，不代表固定高阶机制在联合稀疏和有限样本下可迁移。后续选择性迁移设计找到了它的适用边界：在 rank-admissible、selection-unit 守门的 state-only/action-only 条件下，Stage-1 shared transfer 可以产生预测收益；但 fresh joint confirm 中 shared 与 gate 都未胜过 zero-transfer AR，复杂 Stage-2、完整 action-channel 和 joint 扩展也没有决策级价值。当前最合理的模型是条件化的简化 Stage-1 shared/低维 transfer，并在 joint 或证据不足时退化到 AR/no-op。现有证据属于 synthetic predictive association；真实数据仅有弱 retrospective pilot，尚不支持因果、policy、规划或部署结论。
