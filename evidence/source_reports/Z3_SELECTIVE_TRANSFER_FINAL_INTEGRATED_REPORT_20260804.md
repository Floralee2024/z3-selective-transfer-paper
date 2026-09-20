# Z3 选择性迁移研究最终统合与收口报告

日期：2026-08-04  
状态：项目级证据收口；不等同于因果、策略或部署闭环

## 0. 执行摘要

本研究回答的是一个预测问题：当某个 state–action 单元样本极少、某个 action cell 未见，甚至整个 state 未见时，模型能否从其他 state 借用跨 state 稳定且可被 action 调制的结构，并在证据不足时安全退化。

最终证据支持以下主线：

1. **固定全量迁移不是合理默认。** 在早期联合稀疏实验中，AR 稳定优于固定 T2、T13、T123；这说明不加选择地迁移全部候选结构容易产生负迁移，不说明高阶真值不存在。
2. **rank-admissible Stage-1 shared transfer 是目前最可靠的正结果。** 在 state-only 场景中，T12356 Stage-1 相对 AR 的 mean-TV 改善在 S2、S3、S23 的 12/12 outer blocks 中方向一致；Stage-2 全部选择 no-op。
3. **action-only 的 Stage-1 机制可运行并有小幅 held-cell 收益，但 Stage-2 correction 没有决策级价值。** shared arm 只有未调整 block-level KL 出现小幅稳定改善，其他指标证据不足；residual-global 没有稳定改善。
4. **正确修复的 action-channel ablation 没有发现应改变模型结构的通道。** deviation/full 的收益低于预冻结门槛且 argmax 下降；residual-global 出现 TV/argmax 与 KL 的稳定冲突。因此停止完整 12-block 扩展是预注册决策，不是计算失败。
5. **joint lowdim 候选没有形成跨场景一致的一步预测优势。** 两个候选总体 mean-TV 均略差于 shared-global control；S3 的 4/4 正向结果不能推广到 S2/S23。
6. **degree1 deviation 的 env_2 四步 occupancy 收益是真实可复现的小效应。** exact distribution propagation 在原 evaluation batch、非重叠 held-out batch 和独立 trajectory generator seed 上均复现约 `+0.0034` 的 t=4 改善，12/12 blocks 为正；但它仍是固定 env_2、固定 action 序列下的 synthetic predictive evidence。
7. **oracle-projected headroom 不支持继续把该小效应做大。** 投影后 degree1 相对同样投影 control 的结构优势只剩 `+0.0000596` / `+0.0000179`，约为当前改善的 1.66% / 0.51%。继续围绕同一 degree1 结构调参不再具有决策价值。
8. **高 N 改善依赖场景和指标。** N=65536 时六个 scenario×condition 组合的平均 TV/KL 方向均偏向 transfer，但多个四-split 区间仍跨 0；argmax 在六个组合中均下降，且没有统一单调趋势。
9. **真实数据只达到锁标签 retrospective pilot。** 五个 held SCOTUS cases 上 shared degree-1 候选得到 `PILOT_SUPPORT`，但 NLL 改善仅 `+0.000830`，精确符号翻转结果不支持稳定确认；selection 的最终保留决策仍为 no-op。

因此，项目的最终模型决策是：

> 保留证据支持的 Stage-1 shared/低维 transfer 作为研究机制；默认删除当前 Stage-2 nullspace correction。任何 action deviation、joint lowdim 或真实数据候选必须经过各自 selection/no-op 守门，不能升级为统一默认模型。

### 0.1 项目状态总表

| 工作流 | 流程/合同状态 | 科学证据状态 | 收口决策 |
|---|---|---|---|
| 生成器与表示审计 | 完成 | T12356 可近乎完整表示当前 synthetic truth；T123 不是信息论下限 | 作为机制可表示性依据 |
| State-only rank-admissible | 12/12 PASS | Stage-1 相对 AR 稳定改善；Stage-2 12/12 no-op | 保留 Stage-1，删除 Stage-2 |
| Action-only v1.1 audit package | 12/12 PASS，provenance 完整 | T12356 family 有小幅 held-cell 收益；resolved correction 影响很小 | 保留 Stage-1 研究结果，不保留 Stage-2 |
| Action-channel ablation | 正确修复的单块 pilot PASS | 无 channel 通过预冻结综合门槛；不构成跨 split confirmation | 停止 12-block 扩展 |
| Action-only per-action | 兼容性汇总可运行 | action 0 最难的描述性结果较一致；正式 raw-report 级 CI 未闭环 | 只作描述，不作正式跨 split 结论 |
| λ 审计 | joint 正式完成；action-only Stage-1 trace 缺失 | joint 中 global 通常不弱于 deviation；“正确 degree”未被证明 | 保留操作性审计，不升级为机制选择证明 |
| Joint lowdim | 12/12 PASS，300/300 artifacts | 两候选总体无跨场景一致优势；S3 局部改善 | 不设为统一默认候选 |
| Stable-HO | 未实现真正 group selection | 无科学结果 | 作为新研究阶段，不计入当前闭环 |
| Structured interaction holdout | 未完成 | 无最终 interaction holdout 证据 | 与 trajectory holdout 严格区分 |
| High-N one-step scaling | 72 blocks / 720 runs 完成 | TV/KL 可能受益但依赖场景；argmax 无统一改善 | 拒绝“高 N 普遍改善” |
| High-N rollout package | 工程流程完成 | Monte Carlo、t=0 基线且 `predictive_eligible=false` | 只作描述性 horizon 证据 |
| Joint env_2 exact occupancy | 原 batch、held-out batch、独立 trajectory seed 均完成 | degree1 deviation t=4 约 `+0.0034`，12/12 正向 | 认定为小幅、固定 env_2 synthetic 预测效应 |
| Degree 3/4 稳定性、ICC、recovery | 框架完成，语义系数导出缺失 | 尚无正式 ICC/recovery 结果 | 未闭环；除非机制解释仍是目标，否则停止 |
| Encoder | 无 raw observation 输入 | 未测试 | 未开始 |
| Policy / reward / regret | 无闭环策略评测 | 未测试 | 未开始 |
| 真实数据 | 数据入口与 retrospective pilot 完成 | 五个 SCOTUS test cases 仅微弱方向性证据，selection 保留 no-op | 不称正式外部确认 |
| 因果验证 | 不具备识别设计 | 无因果证据 | 明确排除因果结论 |

## 1. 研究问题、估计量与结论边界

### 1.1 核心问题

```text
action/context baseline
+ 跨-state shared mechanism
+ action-specific deviation
+ 只服务于已见 state 的局部 residual
```

真正关心的是 held-state / held-cell 上的 TV、KL、argmax agreement，以及短 horizon occupancy 是否更接近 synthetic oracle。

### 1.2 主动改变的变量

- 是否启用跨 state Walsh 共享结构；
- 使用哪些 degree；
- global 与 action-deviation 是否独立收缩；
- 是否加入 state-specific residual；
- 是否加入 selection-resolved Stage-2 correction；
- joint 条件中是否使用 action group 或 degree-1 deviation；
- 样本量 N 与 rollout horizon。

### 1.3 外层统计单位

- synthetic one-step：held-state / cell-mask 的 split block；
- joint confirm：scenario × split，共 12 个 outer blocks；
- 同一 block 内五个 training seeds 只反映优化与估计稳定性，不是五个独立实验；
- rollout 中 training seed、trajectory/rollout seed 仍是内层单位；
- 真实数据只有五个 held test cases，且来自同一法院和相邻 Term。

### 1.4 绝对不能推出

- 因果效应；
- certiorari grant 的处理效应；
- policy value、reward 或 regret；
- rollout 结果等同于规划能力；
- encoder 能力；
- 真实世界部署或跨法院普遍泛化；
- 任一 degree/channel 具有普遍语义正确性。

## 2. 证据层级

本项目统一采用五层证据：

1. 代码能够执行；
2. 数据、split、manifest、hash 与流程合格；
3. 预定干预对象和几何实现正确；
4. held-unit 上出现预测差异；
5. 差异足够稳定和重要，能够改变模型或实践决策。

PASS、SHA 匹配、优化器收敛和 rank contract 只支持前 1–3 层。只有 outer-block held-unit 指标才能支持第 4 层；本项目没有证据支持实际部署层面的第 5 层。

## 3. 生成器、表示能力与固定模型基线

### 3.1 生成器审计

- `degree4_energy = 0`；
- degree 5–6 残余跨环境稳定，不是每个环境重新抽取的噪声；
- T12356 在 full-state oracle 条件下可近乎完整表示当前真值。

因此，T123 的约 `TV≈0.077` 只是 T123 表示类诊断参考，不是信息论下限。必须区分表示能力不足与有限 fit 支持下不可识别。

### 3.2 固定 AR/T 比较

在联合 state/action 稀疏和固定模型族下，AR 稳定优于固定 T2、T13、T123。该结果闭合了一个决策：**固定全量迁移不再作为最终机制方向。**

## 4. State-only：最成熟的 Stage-1 正证据

rank-admissible T12356 state-only confirmation 完成 12/12 reports，Stage-2 fit-logit change 为 0。

| 场景 | Stage-1/Resolved − AR mean ΔTV | 范围 | 优于 AR 的 split |
|---|---:|---:|---:|
| S2 | -0.024758 | [-0.028530, -0.019414] | 4/4 |
| S3 | -0.017666 | [-0.019779, -0.013551] | 4/4 |
| S23 | -0.009412 | [-0.015426, -0.005252] | 4/4 |

Stage-2 在 12/12 blocks 选择 explicit no-op，resolved 与 Stage-1 完全相同。

结论：

> 在几何条件化的完全未见 state 场景中，T12356 Stage-1 shared mechanism 稳定优于 AR；当前 selection 没有证据支持额外 nullspace correction。

## 5. Action-only audit package 与正式 v1.1

### 5.1 几何与执行完整性

- 12/12 blocks PASS；
- 0 Stage-2 convergence failures；
- 360 model NPZ、约 3600 Stage-2 folds；
- shared-only fit nullity 27–33，fit+selection 343/343；
- residual-global-only fit nullity 38，fit+selection 358/358；
- 完整 residual-deviation 最多 384/448，结构性不可辨识并排除；
- fit logits 最大变化约 `1e-14`，低于 `1e-8` 守门阈值。

初版 NumPy L-BFGS 失败只属于 implementation history；它已被使用冻结 SciPy L-BFGS-B 的 v1.1 正式结果替代，不能继续写成 action-only 未完成。

### 5.2 Stage-2 resolved-minus-base

| Arm | Metric | Mean delta | 95% CI | 结论 |
|---|---|---:|---:|---|
| shared | TV | -0.0015 | [-0.0031, +0.0002] | 接近 0，未稳定确认 |
| shared | KL | -0.0010 | [-0.0018, -0.0003] | 小幅未调整 paired 改善 |
| shared | argmax | -0.0003 | [-0.0032, +0.0025] | 证据不足 |
| shared | p95-TV | -0.0019 | [-0.0059, +0.0021] | 证据不足 |
| residual-global | TV | +0.0002 | [-0.0018, +0.0021] | 无稳定改善 |
| residual-global | KL | +0.0001 | [-0.0009, +0.0011] | 无稳定改善 |

T12356 family 在 held action cells 上总体优于 AR / T123_R，但 Stage-2 增量很小。最终决策仍是保留 Stage-1，不保留当前 Stage-2。

## 6. Action-channel ablation

### 6.1 旧结果为何无效

旧 runner 存在三项关键问题：

- tall matrix 使用 `full_matrices=True` 造成巨大内存需求；
- 使用 `A.T @ A` 的 Gram-eigh 推断奇异值，平方 condition number 并改变 nullity 判定；
- correction 使用完整 `selection_m`，而非 channel-restricted selection operator。

因此旧 Gram-based correction 与相关 paired delta 不进入最终科学证据。

### 6.2 修复后的 v4 pilot

direct SVD、完整 cell-level nullspace、restricted selection operator、SVD whitening、basis rotation invariance 和 fit-logit invariance 均通过。正式 pilot 为 S2 / split 20260748，属于 retrospective corrected decision pilot，不是新 confirmatory aggregation。

| Channel | 选择 | mean ΔTV | mean ΔKL | mean Δargmax | 决策 |
|---|---|---:|---:|---:|---|
| shared-global | structural no-op | 0 | 0 | 0 | 无干预空间 |
| shared-deviation | ridge 100 | +0.000460 | +0.000344 | -0.000264 | 低于 SESOI，argmax 下降 |
| shared-full | ridge 100 | +0.000298 | +0.000194 | -0.000415 | 低于 SESOI，argmax 下降 |
| residual-global | ridge 10 | +0.001356 | -0.002139 | +0.007788 | TV/argmax 与 KL 冲突 |

冻结的 source-specific SESOI 约为 TV `0.00128`、KL `0.000815`，且要求五 seeds TV/KL 均为正、argmax 不下降。没有 channel 通过。

正式决策：

```text
STOP_AFTER_RETROSPECTIVE_PILOT_NO_DECISION_CHANGING_CHANNEL
```

因此不运行 corrected 12-block 扩展，不把“未发现决策级收益”升级成“action channel 普遍无用”。

## 7. Per-action 汇总与 λ 审计

### 7.1 Action-only per-action

统一脚本已经实现逐 action 均值、SD、SE、区间、最差 action、action 方差与 resolved-minus-base delta。但 action-only dry-run 使用的是 final-audit compatibility package，其中部分值已经先按 block 聚合，不能恢复真正的跨 split 方差和 CI。

可保留的描述性结论：

- action 0 在 mean-TV、KL 和 argmax 上通常最困难；
- AR 的 action-0 mean-TV 约 0.1836；T12356 family 约 0.169–0.171；
- action 间 argmax SD 约 0.16–0.17，明显高于 TV 的 action 间 SD；
- action 6 在若干 action-only结果中相对容易。

不能声称 action-only 的正式 per-action 跨 split CI 已闭环。joint lowdim 的 per-action 表则是正式 12-block 汇总。

### 7.2 λ 审计

Action-only final-audit compatibility package 不包含完整 Stage-1 selector trace，因此 degree/global/deviation retention 的正式结论仍缺失。Stage-2 ridge/no-op 分布可以描述，但不能替代 Stage-1 λ 审计。

joint lowdim 的正式 λ 审计显示：

- global 更活跃 5/12；
- deviation 更活跃 1/12；
- 6/12 持平；
- 两类 deviation 的低惩罚保留率均只有 1/12。

这里“更积极”只表示 λ 更小，不证明某个 degree 在科学意义上正确。

## 8. Joint lowdim confirm

12/12 reports PASS，300/300 artifacts 完整；外层单位为 S2/S3/S23 × 四 splits。

### 8.1 总体结果

| 候选 | 总体 mean-TV improvement | 结论 |
|---|---:|---|
| action_groups_degree1 | -0.001270 | 不支持总体优势 |
| degree1_deviation | -0.001297 | 不支持总体优势 |

正值表示优于 shared-global control。其他 TV/KL/argmax 描述性区间也均跨 0。

### 8.2 场景异质性

| 候选 | S2 | S3 | S23 |
|---|---:|---:|---:|
| action_groups_degree1 | -0.01162 | +0.00644，4/4 wins | +0.00137 |
| degree1_deviation | -0.00462 | +0.00518，4/4 wins | -0.00445 |

S3 的正结果不能推广为 joint 条件下的普遍机制结论。

### 8.3 Stage-2 与最差 action

- action-group：6 次 no-op、6 次 ridge，1 次 structural no-op；
- degree1 deviation：9 次 no-op、3 次 ridge，3 次 structural no-op；
- 最差 argmax action 主要由 action 0 主导：action-group 9/12，degree1 deviation 10/12。

结论：低维 deviation/action-group 是场景依赖候选，不是统一 joint 默认机制；Stage-2 仍不应默认保留。

### 8.4 Joint shared Stage-1 vs zero-transfer AR

此前 joint lowdim 只比较了 transfer 候选与 shared-global control，不能回答“选择性共享机制与零迁移 AR 谁更好”。该缺口现已由 fresh panel 20260772–20260775 的 12-block prospective confirm 闭合。

| Arm | overall ΔTV | ΔKL | Δargmax | 正向 TV blocks | 决策 |
|---|---:|---:|---:|---:|---|
| T12356 shared Stage-1 | -0.001897 | -0.005654 | -0.021760 | 5/12 | FAIL |
| LOSO selection gate | -0.002937 | -0.005418 | -0.010145 | 3/12 | FAIL |

正值表示优于 zero-transfer AR。gate 选择 shared 8/12 次，但其中 7 块 test ΔTV 为负；selection regret 为 0.01167，retention ratio 为 -0.336。真正 held-cell 等权的无重训敏感性复算也没有翻转结果：shared ΔTV -0.002215，gate -0.003094。

正式决定：**joint transfer 不进入 Y1 主干，当前 joint fallback 为 zero-transfer AR/no-op。** 该负结果限于当前 synthetic panel、表示、λ 网格和 selector，不否定 state-only/action-only 的局部 Stage-1 结果。

## 9. Stable-HO 与 holdout

### 9.1 Stable-HO

项目中出现过 `Stable_HO_orthogonal_residual` positive-control/smoke 名称，也完成过 minimal interaction ablation，但这些报告都明确标注：

```text
not a final Stable-HO interaction-set selection experiment
```

真正的 interaction-group discovery/selection 尚未实现。因此 Stable-HO 不能写成已完成、负结果或已验证机制。

### 9.2 Holdout

早期 strict state-holdout 和 holdout decomposition 已用于比较固定 T1/T2/T13/T123，并帮助确认固定全量迁移不稳健；但它们不是最终 structured holdout，也没有完成真正 Stable-HO group selection。

另一个不同概念的 holdout 已完成：env_2 exact occupancy 使用 trajectory IDs 4096–8191 的非重叠 evaluation batch，验证 degree1 deviation 的 t=4 小幅收益。这是 evaluation-sample holdout，不等同于结构化 interaction holdout。

## 10. 高 N one-step scaling

正式设计包含 N=4096/16384/65536、S2/S3/S23、state-only/state-action、四 fresh splits、五 training seeds，共 72 outer blocks / 720 model-seed runs。

N=65536 时，六个 scenario×condition 组合的平均 TV 与 KL 方向均偏向 `T123_R_degree_global_deviation`；但多个四-split 区间仍跨 0。六个组合的 argmax improvement 均为负。

趋势审计：

- TV 单调方向通过 4/6；
- KL 单调方向通过 4/6；
- argmax 单调方向通过 0/6；
- state_action / S23 的 TV、KL 均不单调。

结论：

> 高 N 可能改善概率预测的 TV/KL，但效果依赖 scenario、condition 和 metric；不存在“样本越多，所有指标越稳定改善”的证据。

## 11. Rollout 与 exact occupancy

### 11.1 Joint lowdim exact distribution propagation

转移采样被移除，每条固定 action 序列传播完整 64-state distribution。degree1_deviation Stage-1 相对 shared-global 的 t=4 occupancy 改善为：

| Evaluation | behavior replay | uniform fixed | 正 blocks |
|---|---:|---:|---:|
| 原 env_2 batch | +0.003406 | +0.003386 | 12/12 |
| 非重叠 held-out batch | +0.003477 | +0.003329 | 12/12 |
| 独立 trajectory seed | +0.003583 | +0.003495 | 12/12 |

selection-resolved 始终略低于 Stage-1；action_groups 只有约 `+0.0001` 且方向不稳。

可支持的结论：

> 在固定 env_2 truth、固定初始状态分布和固定 action-conditioned 四步传播下，degree1_deviation Stage-1 的 occupancy 预测比 shared-global 更接近 synthetic oracle；该小效应跨非重叠 evaluation rows 和独立 trajectory generator seed 复现。

不能支持 policy、reward、regret、因果、真实数据或跨环境结论。

### 11.2 Oracle-projected headroom

| Action rule | 当前 t=4 改善 | 投影后 degree1 特有结构优势 | 占当前改善 |
|---|---:|---:|---:|
| behavior replay | +0.003583 | +0.0000596 | 1.66% |
| uniform fixed | +0.003495 | +0.0000179 | 0.51% |

约 `+0.0515` 的总 oracle headroom 主要属于 control 与 candidate 共有的估计/训练差距，不能归因于 degree1。停止围绕同一结构继续调参是合理收口决策。

### 11.3 High-N rollout package

该包包含 360 个 PASS seed-run reports、72 outer blocks、H=4、uniform fixed actions 和 common random numbers，工程完整性通过。结果显示 occupancy 的 t=1→t=4 endpoint 在 18 个 N×scenario×condition 组合中 17 个增加、1 个近似 flat；但许多中间 horizon 路径非单调。

它仍不能作为最终 high-N exact-distribution 判别实验，原因是：

- runner 使用 `n_episodes=256` 的 Monte Carlo rollout，而非完整 distribution propagation；
- aggregate 对 occupancy 的正式 `delta_0` 使用 t=0，天然为 0，而不是预先要求的 t=1 horizon baseline；
- aggregate JSON 明确标记 `predictive_eligible=false`。

因此它回答了“差异在短 horizon 中可能累积且经常非单调”的相关问题，不足以闭合预定的 held-unit exact-distribution、t=1-baseline 判别问题。

## 12. Degree 3/4 稳定性、ICC 与 recovery

框架、冻结配置、preflight、aggregator 和测试脚本均已完成。固定统计定义包括：

- coefficient-level seed stability；
- environment|split coefficient vector 的 cosine、Pearson、NRMSE、sign agreement；
- `ICC(A,1)`；
- 相对 generator truth 的 cosine、Pearson、normalized L2、support precision/recall/F1 和 active sign accuracy。

但现有 high-N NPZ 只有数值权重数组，没有冻结的 `row → degree/channel/term_key` 语义映射，也没有与 truth 对齐的 coefficient export。缺少：

```text
coefficient_estimates.csv
coefficient_truth.csv
coefficient_manifest.json
```

因此这一流目前只达到分析框架与 pipeline-ready，不能报告 degree 3/4 ICC 或 recovery 科学结论。

## 13. Encoder、policy、rollout、真实数据与因果

### 13.1 Encoder

未开始。SCOTUS 数据没有 `raw_observation_x_t`，只有人工冻结的 11 维部分可观测特征，不能据此声称 encoder 能力。

### 13.2 Policy / regret

未开始。当前所有 rollout action 都是 behavior replay 或 frozen uniform action sequence，不是由模型选择的 policy；没有 reward、value 或 regret。

### 13.3 Rollout

synthetic fixed-action rollout 已完成并得到 env_2 小幅 occupancy 证据；规划、闭环控制和策略 rollout 未开始。

### 13.4 真实数据

15 条 SCOTUS cases 被转换为 partial-observation、locked-label retrospective evaluation。模型只读取判断时点的冻结特征；未知、争议和不可观测信息不使用事后材料填补。

五个 held test cases 的结果：

| 指标 | held-state baseline | shared degree-1 | 改善 |
|---|---:|---:|---:|
| mean NLL | 0.957958 | 0.957128 | +0.000830 |
| one-hot TV | 0.584615 | 0.559989 | +0.024626 |
| Brier | 0.565680 | 0.563266 | +0.002415 |
| accuracy | 0.600 | 0.600 | 0 |

按冻结规则得到 `PILOT_SUPPORT`，但 NLL exact sign-flip p=1.0，TV p=0.375；selection 本身没有支持保留 transfer，最终 retained model 为 no-op。

正确表述：

> shared held-state transfer 在五个已查看标签的 retrospective held cases 上出现小幅方向性预测收益，但尚未形成盲测确认或稳定真实数据能力证据。

### 13.5 因果

未开始，也不由当前设计支持。所有真实样本的 action 都是 certiorari grant，不能估计 action effect；不完整信息可以用于预测，但不能自动识别因果链。

## 14. 跨实验综合判断

### 14.1 一致出现的事实

- 固定全量迁移容易负迁移；
- rank/selection 几何是进入实验的必要条件；
- 可测收益主要来自 Stage-1 representation，而不是 Stage-2 correction；
- no-op 是有效科学结果和模型安全机制；
- action 0 是反复出现的困难 action；
- low-dimensional deviation 的收益高度依赖场景与指标；
- 概率指标 TV/KL 与 argmax 可能分离；
- rollout endpoint 收益可能大于 one-step，但不保证中间 horizon 单调。

### 14.2 看似冲突但可以共存的结果

joint one-step 中 degree1_deviation 总体不优于 control；env_2 t=4 occupancy 却稳定为正。这不构成矛盾，因为估计量不同：前者平均 held cells 的一步 TV/KL/argmax，后者在固定 action sequence 下传播 occupancy，并可能放大特定方向的小误差差异。

oracle projection 又表明该 t=4 优势不是一个可继续放大的巨大 degree1 结构上限。因此最稳妥的解释是：**存在可复现的小型、环境与 action-sequence 条件化的 rollout 关联，而不是普遍的 degree1 机制优势。**

## 15. 最终模型与停止决策

### 15.1 保留

- rank-admissible Stage-1 shared transfer；
- 场景明确时的低维 degree1 deviation 研究候选；
- explicit no-op 与 held-unit selection；
- shared mechanism / local residual 分离；
- geometry、hash、fit-logit invariance 与 outer-block aggregation 守门。

### 15.2 默认删除或停止

- 当前 action-channel Stage-2 correction；
- corrected channel ablation 的完整 12-block 扩展；
- 围绕同一 env_2 degree1 结构追加更多 trajectory seeds；
- 把固定 T123/T12356 全量迁移作为默认；
- 把 residual-deviation 塞入不可辨识的 action-only 完整模型；
- 根据单一 TV/argmax 改善事后接受 KL 恶化。

### 15.3 尚未关闭但不应伪装为完成

- 真正 Stable-HO interaction-group selection；
- structured interaction holdout；
- action-only Stage-1 的正式 degree/global/deviation λ retention 审计；
- action-only 真正 raw-report 级 per-action 跨 split CI；
- high-N exact-distribution、t=1-baseline rollout；
- degree 3/4 coefficient export、ICC 与 recovery；
- 新 env/context rollout；
- 新的未查看真实 test cases；
- encoder、policy、regret、causal validation。

## 16. 项目级结论表述

推荐最终摘要：

> 本研究表明，跨 state 迁移不应在 AR 与固定全量高阶模型之间二选一，而应被建模为由 held selection units 控制的分阶数、分通道、可退化机制。rank-admissible T12356 Stage-1 在完全未见 state 和 action-only held-cell synthetic 场景中获得相对 AR 的预测收益；但 fresh joint confirm 中 shared 与 LOSO gate 均未胜过 zero-transfer AR，因此 joint 默认应退化到 AR/no-op。selection-resolved Stage-2 correction 的增量很小，未形成保留证据。低维 degree1 deviation 在 joint one-step 上不具备跨场景一致优势，却在固定 env_2、固定 action sequence 的四步 exact occupancy 中产生约 0.0034、可跨 evaluation batch 与 trajectory seed 复现的小幅收益。高 N 对 TV/KL 有场景依赖帮助，但不改善所有指标。真实 SCOTUS pilot 只提供微弱的 retrospective shared-transfer 方向性证据。所有结果均限于预测关联，不支持因果、policy、regret、规划能力或部署结论。

## 17. 收口后的最小后续集合

如果项目现在停止，现有主结论已经自洽。若只允许继续三项最可能推翻当前判断的实验，应按以下顺序：

1. **新 env/context 的 exact occupancy replication**：检验 env_2 的 `+0.0034` 是否跨 truth/context 保留；这是当前最关键的 synthetic falsification。
2. **新的未查看真实案件 batch**：先冻结模型和阈值，再打开标签；检验 SCOTUS pilot 的方向是否复现。
3. **只有在系数机制解释仍是核心目标时，补 coefficient semantic export**：否则 degree ICC/recovery 只是研究装饰，不应继续。

Stable-HO、encoder、policy 或 causal 工作都属于新的研究阶段，不应作为本项目“差一点就完成”的尾项继续追加。

## 18. 关键证据路径

- State-only summary: `C:\Users\兜兜\Documents\Codex\2026-07-28\8-state-state-2-action-ar\outputs\z3_selection_resolved_transfer_v11_confirm_20260729_restart1\summary\z3_selection_resolved_transfer_v11_summary.md`
- Action-only final audit: `C:\Users\兜兜\Documents\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\z3_action_only_selection_resolved_v1_1_confirm_20260730_final_audit\z3_action_only_final_audit_package.md`
- Corrected channel pilot: `C:\Users\兜兜\Downloads\action_channel_stage2_only_pilot_S2_20260748\z3_action_channel_stage2_only_decision_pilot.json`
- Joint lowdim: `C:\Users\兜兜\Documents\Codex\2026-07-30\action-only-runner-16-cpu-32gb\outputs\joint_lowdim_confirm_aggregate_20260801_final\joint_lowdim_confirm_aggregate.md`
- High-N one-step: `C:\Users\兜兜\Downloads\z3_high_n_scaling_aggregate.md`
- High-N rollout: `C:\Users\兜兜\Documents\Codex\2026-08-03\c-users-documents-codex-2026-07-2\high_n_rollout_confirm_20260804_package_fixed\03_aggregate\high_n_rollout_aggregate.json`
- Exact occupancy: `C:\Users\兜兜\Documents\Codex\2026-08-03\joint-lowdim-rollout-60-60-block\outputs\joint_lowdim_exact_occupancy_env2_v1_20260803\exact_occupancy_aggregate\joint_lowdim_exact_occupancy_aggregate.md`
- Held-out exact occupancy: `C:\Users\兜兜\Documents\Codex\2026-08-03\joint-lowdim-rollout-60-60-block\outputs\joint_lowdim_exact_occupancy_holdout_env2_v1_20260803\holdout_exact_occupancy_aggregate\joint_lowdim_holdout_exact_occupancy_aggregate.md`
- Independent trajectory seed: `C:\Users\兜兜\Documents\Codex\2026-08-03\joint-lowdim-rollout-60-60-block\outputs\joint_lowdim_independent_generator_seed_20261301_env2_v1_20260803\newseed_vs_reference\newseed_vs_reference_aggregate.md`
- Oracle headroom: `C:\Users\兜兜\Documents\Codex\2026-08-03\joint-lowdim-rollout-60-60-block\outputs\joint_lowdim_oracle_projected_headroom_v1_20260803\oracle_projected_headroom_report.md`
- Degree stability framework: `C:\Users\兜兜\Documents\Codex\2026-07-30\action-only-runner-16-cpu-32gb\work\README_degree_stability_icc_recovery_v1.md`
- Real-data result: `C:\Users\兜兜\Documents\Codex\2026-08-04\c-users-documents-codex-2026-07\outputs\scotus_partial_observation_real_transfer_v1_4_run_20260804\formal_real_transfer_result.json`
