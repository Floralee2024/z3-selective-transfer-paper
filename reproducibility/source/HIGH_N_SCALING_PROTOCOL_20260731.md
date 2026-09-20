# High-N scaling final discriminating experiment

## What this experiment decides

The primary question is whether the predictive advantage of the declared
`T123_R_degree_global_deviation` mechanism over `AR` improves, stabilizes, or
disappears as the amount of sequence data increases.

The estimand is the paired test-cell contrast

```text
CHANNEL - AR
```

for candidate TV, excess KL, and candidate-argmax agreement, summarized across
the four fresh split seeds. The intervention is sequence count `N`; all other
fixture, environment, contract, model, selector, and test definitions remain
fixed.

This is pipeline-eligible and predictive-eligible evidence only. It is not a
causal test, semantic-recovery test, policy/regret test, rollout test, encoder
test, or real-data validation.

## Frozen design

| Item | Frozen value |
|---|---|
| Fixture | current `fixtures_high_n_matrix`, 65,536 sequences available |
| N levels | 4,096; 16,384; 65,536 |
| N construction | nested prefix sequence IDs `0 ... N-1` |
| Scenarios | S2, S3, S23 |
| Conditions | state_only, state_action |
| Split seeds | 20260748, 20260749, 20260750, 20260751 |
| Models | AR; T123_R_degree_global_deviation |
| Training seeds | 5 per block |
| Epochs / patience | 120 / 18 |
| Batch / learning rate | 1024 / 0.003 |
| Lambda grid | 0.0001, 0.01, 1.0 |
| Selector | fixed_coordinate_lambda_v1, tie tolerance 1e-5 |
| Oracle policy | evaluation only; never fit or select |

The full run is 3 N levels × 3 scenarios × 2 conditions × 4 splits = 72
blocks, or 720 model-seed fits. The primary block cell counts are:

- `state_only`: 336 fit, 56 selection, 56 test cells;
- `state_action`: 240 fit, 16 selection, 16 test cells.

## Resource estimate

The current high-N sequence file contains about 122 MB uncompressed arrays per
environment. Loading env_0/env_1/env_2 for one scenario is therefore roughly
367 MB before design matrices. The largest CHANNEL design in the historical
high-N run had 339 columns and about 141k fit rows; one float64 design is about
380 MB. A single process should fit comfortably within 8 GB RAM, while four
concurrent processes should be planned within 16 GB. The existing 16 CPU / 32
GB machine is adequate for memory; CPU time is the limiting resource.

Historical reference: the previous 24-block N=65,536 run used 5 seeds and 120
epochs and took about 13 hours 46 minutes on its machine. A conservative
serial estimate for this 72-block scaling run is about 17–20 hours:

```text
N=65,536: ~13.8 h historical reference
N=16,384: ~3.5 h, approximately one quarter of high-N work
N=4,096:  ~0.9 h, approximately one sixteenth of high-N work
total:    ~18.2 h plus I/O and machine variation
```

Use the serial launcher for the most reproducible run. Four-way concurrency
should reduce wall time but increases memory and thermal contention; do not
start more than four workers on the 32 GB machine without measuring.

## Smoke evidence

Completed smoke block:

```text
N=4096 / S2 / state_action / split=20260748
5 seeds × 2 models = 10 runs
epochs=2, patience=1
status=PASS
fit/selection/test cells=240/16/16
oracle_used_for_training_or_selection=False
```

The smoke output is intentionally separate from the formal output and must
not be aggregated with it:

`outputs/high_n_scaling_smoke_20260731_run1/`

## Formal commands

```powershell
$Python = (Resolve-Path .\.venv\Scripts\python.exe).Path

powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\work\run_high_n_scaling_v1_serial.ps1 `
  -PythonExe $Python `
  -FixtureRoot C:\data\fixtures_high_n_matrix `
  -ContractsRoot C:\data\built_contracts_20260748_51 `
  -OutputRoot C:\data\high_n_scaling_confirm_20260731
```

Before the long run, execute the outcome-blind preflight:

```powershell
& $Python .\work\preflight_high_n_scaling_v1.py `
  --fixture-root C:\data\fixtures_high_n_matrix `
  --contracts-root C:\data\built_contracts_20260748_51 `
  --frozen-config .\work\FROZEN_CONFIG_high_n_scaling_v1.json `
  --output-dir C:\data\high_n_scaling_confirm_20260731_preflight
```

For a memory-gated single-concurrency run, use the wrapper below. It creates
or verifies the same preflight, requires 10 GB available memory, and resumes
only from complete PASS blocks with their model artifacts:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File .\work\run_high_n_scaling_v1_single.ps1 `
  -PythonExe $Python `
  -FixtureRoot C:\data\fixtures_high_n_matrix `
  -ContractsRoot C:\data\built_contracts_20260748_51 `
  -OutputRoot C:\data\high_n_scaling_confirm_20260801 `
  -MinimumAvailableMemoryMB 10240
```

After all 72 blocks pass:

```powershell
& $Python .\work\aggregate_high_n_scaling_v1.py `
  --input C:\data\high_n_scaling_confirm_20260731 `
  --frozen-config .\work\FROZEN_CONFIG_high_n_scaling_v1.json `
  --verify-artifacts `
  --output-dir C:\data\high_n_scaling_confirm_20260731\aggregate
```

The decisive readout is the N-by-condition-by-scenario table of paired
`CHANNEL - AR` deltas. A monotone move toward zero or a stable sign is
evidence about finite-sample predictive scaling; it is not proof of causal or
semantic meaning.

## Relation to the supplied historical summary

The supplied low/high/oracle and per-action summaries are useful as a
compatibility reference: they used the same broad AR-vs-CHANNEL question and
showed the old N=4,096 versus N=65,536 comparison. They used older contracts and
split seeds, so they are not pooled with this fresh-split experiment. The
current runner records fixture and contract hashes so the new result remains
auditable independently.
