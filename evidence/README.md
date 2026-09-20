# Evidence snapshot

This directory is intentionally compact. It records the numbers used in the manuscript without copying the large source workspace.

## Primary numeric snapshot

```text
Joint confirm: 12/12 blocks, 300/300 artifacts.
Joint pooled mean-TV improvement:
  action_groups_degree1 = -0.00126987
  degree1_deviation     = -0.00129738

Exact degree1-deviation Stage-1 t=4 improvement:
  original batch      = +0.003406 / +0.003386
  held-out batch      = +0.003477 / +0.003329
  independent seed    = +0.003583 / +0.003495
  positive blocks     = 12/12 in each evaluation.

High-N exact held-unit:
  blocks              = 72/72
  directional cells   = 18/18
  positive t4 cells   = 18/18
  universal accumulation = false
  universal t4 retention = false
  formal_confirmatory   = false
  causal_eligible       = false

High-N exact held-unit, repeat-action sensitivity:
  blocks              = 72/72
  strong accumulation cells = 7/18
  directional t4-t1 cells   = 18/18
  positive t4 cells         = 18/18
  universal accumulation    = false
  universal t4 retention    = false
```

## Interpretation rule

The PASS counts certify the declared pipeline and artifact checks. They do not certify a universal performance improvement. The manuscript reports the held-unit effect sizes and scenario dependence separately.
