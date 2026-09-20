param(
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$FixtureRoot,
  [Parameter(Mandatory=$true)][string]$ContractsRoot,
  [Parameter(Mandatory=$true)][string]$OutputRoot,
  [string]$FrozenConfig = "",
  [string]$Scenarios = "S2,S3,S23",
  [string]$Conditions = "state_only,state_action",
  [string]$NGrid = "4096,16384,65536",
  [string]$SplitSeeds = "20260748,20260749,20260750,20260751",
  [int]$NSeeds = 5,
  [int]$Epochs = 120,
  [int]$Patience = 18,
  [int]$BatchSize = 1024,
  [double]$LearningRate = 0.003
)

$ErrorActionPreference = "Stop"
$python = (Resolve-Path $PythonExe).Path
$fixture = (Resolve-Path $FixtureRoot).Path
$contracts = (Resolve-Path $ContractsRoot).Path
$output = [IO.Path]::GetFullPath($OutputRoot)
$runner = Join-Path $PSScriptRoot "d5_y1_z3_high_n_scaling_v1.py"
if ([string]::IsNullOrWhiteSpace($FrozenConfig)) { $FrozenConfig = Join-Path $PSScriptRoot "FROZEN_CONFIG_high_n_scaling_v1.json" }
$frozen = (Resolve-Path $FrozenConfig).Path
foreach ($path in @($python,$fixture,$contracts,$runner,$frozen)) { if (-not (Test-Path -LiteralPath $path)) { throw "Required input missing: $path" } }
New-Item -ItemType Directory -Force -Path $output | Out-Null
$lock = Join-Path $output ".high_n_scaling_serial.lock"
try { New-Item -ItemType File -Path $lock -ErrorAction Stop | Out-Null } catch { throw "Another high-N serial launcher appears active or left a lock: $lock" }

function Test-CompleteHighNReport([string]$ReportPath, [int]$N, [string]$Scenario, [string]$Condition, [int]$Split, [string]$Block) {
  if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) { return $false }
  try { $report = Get-Content -LiteralPath $ReportPath -Raw | ConvertFrom-Json } catch { return $false }
  if ($report.status -ne "PASS" -or $report.runner_version -ne "z3_high_n_scaling_v1" -or [int]$report.n_sequences -ne $N -or $report.scenario -ne $Scenario -or $report.condition -ne $Condition -or [int]$report.split_seed -ne $Split -or @($report.per_run).Count -ne 10) { return $false }
  $models = @($report.per_run | ForEach-Object { $_.model } | Sort-Object -Unique)
  if (($models -join ',') -ne 'AR,T123_R_degree_global_deviation') { return $false }
  foreach ($entry in @($report.per_run)) { if (-not (Test-Path -LiteralPath (Join-Path $Block $entry.artifact.path) -PathType Leaf)) { return $false } }
  return $true
}

& $python -m py_compile $runner
if ($LASTEXITCODE -ne 0) { Remove-Item -LiteralPath $lock -Force; throw "high-N runner compilation failed" }

$scenarioList = $Scenarios.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$conditionList = $Conditions.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
$nList = $NGrid.Split(',') | ForEach-Object { [int]$_.Trim() }
$splitList = $SplitSeeds.Split(',') | ForEach-Object { [int]$_.Trim() }
$log = Join-Path $output "high_n_scaling_serial.log"
$env:OMP_NUM_THREADS = "1"; $env:OPENBLAS_NUM_THREADS = "1"; $env:MKL_NUM_THREADS = "1"
Start-Transcript -Path $log -Append | Out-Null
try {
  foreach ($n in $nList) {
    foreach ($scenario in $scenarioList) {
      foreach ($condition in $conditionList) {
        foreach ($split in $splitList) {
          $block = Join-Path $output ("N_{0}\{1}\{2}\split_{3}" -f $n,$scenario,$condition,$split)
          $report = Join-Path $block "z3_high_n_scaling_block_report.json"
          if (Test-CompleteHighNReport $report $n $scenario $condition $split $block) { Write-Host "SKIP PASS $n/$scenario/$condition/$split"; continue }
          if (Test-Path -LiteralPath $block) { throw "Refusing incomplete or invalid output reuse: $block" }
          Write-Host "RUN  $n/$scenario/$condition/$split"
          & $python $runner `
            --fixture-root $fixture `
            --contracts-root $contracts `
            --frozen-config $frozen `
            --output-dir $block `
            --scenario $scenario `
            --condition $condition `
            --split-seed $split `
            --n-sequences $n `
            --n-seeds $NSeeds `
            --epochs $Epochs `
            --patience $Patience `
            --batch-size $BatchSize `
            --lr $LearningRate
          if ($LASTEXITCODE -ne 0) {
            if (Test-CompleteHighNReport $report $n $scenario $condition $split $block) { Write-Warning "Runner returned $LASTEXITCODE after a complete PASS report; accepting $n/$scenario/$condition/$split" } else { throw "high-N scaling block failed: $n/$scenario/$condition/$split" }
          }
          if (-not (Test-CompleteHighNReport $report $n $scenario $condition $split $block)) { throw "Runner exited but report/artifacts failed validation: $n/$scenario/$condition/$split" }
          Write-Host "PASS $n/$scenario/$condition/$split"
        }
      }
    }
  }
  Write-Host "HIGH-N SCALING COMPLETE: $output"
}
finally {
  Stop-Transcript | Out-Null
  if (Test-Path -LiteralPath $lock) { Remove-Item -LiteralPath $lock -Force }
}
