# High-N held-unit exact occupancy aggregate

Status: `PASS`

- Blocks: 72 / 72
- Frozen horizon comparison: t=1 to t=4
- Strong accumulation cells: 6 / 18
- Directional positive t4-t1 cells: 18 / 18
- Positive t4 mean cells: 18 / 18
- Universal accumulation supported: false
- Universal t4 retention supported: false

The first transition is exactly a held test cell. Later transitions use the exact uniform action mixture and may visit non-held cells.
The practical threshold was informed by the prior sampled rollout and frozen before this exact held-unit run.
Training seeds are averaged within split; the four splits are the outer units. N levels are nested.
This is predictive synthetic evidence, not policy, reward/regret, causal, real-data, cross-context, or long-horizon evidence.
