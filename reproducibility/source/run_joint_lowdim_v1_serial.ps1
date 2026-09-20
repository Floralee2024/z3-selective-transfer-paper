param(
  [Parameter(Mandatory=$true)][string]$PythonExe,
  [Parameter(Mandatory=$true)][string]$FixtureRoot,
  [Parameter(Mandatory=$true)][string]$ContractsRoot,
  [Parameter(Mandatory=$true)][string]$OutputRoot,
  [string]$FrozenConfig = "$PSScriptRoot\FROZEN_CONFIG_joint_lowdim_v1.json",
  [string]$Scenarios = "S2,S3,S23",
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
$config = (Resolve-Path $FrozenConfig).Path
$output = [System.IO.Path]::GetFullPath($OutputRoot)
New-Item -ItemType Directory -Force -Path $output | Out-Null
$lockPath = Join-Path $output ".joint_lowdim_serial.lock"
$lockHandle = $null
$lockOwned = $false

function Test-CompleteJointReport([string]$ReportPath) {
  if (-not (Test-Path -LiteralPath $ReportPath -PathType Leaf)) { return $false }
  try {
    $report = Get-Content -Raw -LiteralPath $ReportPath | ConvertFrom-Json
    if ($report.status -ne "PASS") { return $false }
    if ($report.runner_version -ne "z3_joint_lowdim_v1") { return $false }
    if ($report.condition -ne "joint") { return $false }
    if (@($report.per_run).Count -ne 25) { return $false }
    if (@($report.candidate_order).Count -ne 3) { return $false }
    $seeds = @($report.per_run | ForEach-Object { [int]$_.seed } | Sort-Object -Unique)
    if ($seeds.Count -ne 5) { return $false }
    $models = @($report.per_run | ForEach-Object { [string]$_.model } | Sort-Object -Unique)
    if ($models.Count -ne 5) { return $false }
    $reportRoot = Split-Path -Parent $ReportPath
    foreach ($entry in @($report.per_run)) {
      if ($null -eq $entry.artifact -or [string]::IsNullOrWhiteSpace([string]$entry.artifact.path)) { return $false }
      $artifactPath = Join-Path $reportRoot ([string]$entry.artifact.path)
      if (-not (Test-Path -LiteralPath $artifactPath -PathType Leaf)) { return $false }
    }
    return $true
  } catch {
    return $false
  }
}

try {
  try {
    $lockHandle = [System.IO.File]::Open($lockPath, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    $lockOwned = $true
    $lockBytes = [Text.Encoding]::UTF8.GetBytes(("pid={0}; started={1:o}; host={2}" -f $PID, (Get-Date), $env:COMPUTERNAME))
    $lockHandle.Write($lockBytes, 0, $lockBytes.Length)
    $lockHandle.Flush()
  } catch {
    throw "Another joint launcher appears to be using this OutputRoot, or a stale lock exists: $lockPath. Verify processes before removing the lock."
  }

  Write-Host "Preflight: Python/SciPy"
  & $python -c "import numpy,pandas,scipy; print('numpy',numpy.__version__,'pandas',pandas.__version__,'scipy',scipy.__version__)"
  if ($LASTEXITCODE -ne 0) { throw "SciPy preflight failed; install requirements or switch machine." }

  Write-Host "Preflight: compile joint runner"
  & $python -m py_compile "$PSScriptRoot\d5_y1_z3_joint_lowdim_v1.py"
  if ($LASTEXITCODE -ne 0) { throw "joint runner compilation failed" }

  $scenarioList = $Scenarios.Split(',') | ForEach-Object { $_.Trim() } | Where-Object { $_ }
  $splitList = $SplitSeeds.Split(',') | ForEach-Object { [int]$_.Trim() }
  $runner = Join-Path $PSScriptRoot "d5_y1_z3_joint_lowdim_v1.py"
  $log = Join-Path $output "joint_lowdim_serial.log"
  Start-Transcript -Path $log -Append | Out-Null
  try {
  foreach ($scenario in $scenarioList) {
    foreach ($split in $splitList) {
      $block = Join-Path $output ("{0}\split_{1}" -f $scenario, $split)
      $report = Join-Path $block "z3_joint_lowdim_transfer_report.json"
      if (Test-Path -LiteralPath $report -PathType Leaf) {
        if (Test-CompleteJointReport $report) {
          Write-Host "SKIP PASS $scenario split $split -> $report"
          continue
        }
        throw "Existing joint report is missing or incomplete; inspect before continuing: $report"
      }
      if (Test-Path -LiteralPath $block -PathType Container) {
        $partial = @(Get-ChildItem -LiteralPath $block -Force)
        if ($partial.Count -gt 0) {
          throw "Partial block directory exists without a PASS report; use a new OutputRoot or inspect manually: $block"
        }
      }
      Write-Host "RUN $scenario split $split -> $block"
      & $python $runner `
        --train-env-dir (Join-Path $fixture "$scenario\env_0") `
        --selection-env-dir (Join-Path $fixture "$scenario\env_1") `
        --test-env-dir (Join-Path $fixture "$scenario\env_2") `
        --contracts-root $contracts `
        --frozen-config $config `
        --output-dir $block `
        --split-seed $split `
        --n-seeds $NSeeds `
        --epochs $Epochs `
        --patience $Patience `
        --batch-size $BatchSize `
        --lr $LearningRate
      $runnerExitCode = $LASTEXITCODE
      Write-Host "RUNNER_EXIT_CODE $scenario split $split = $runnerExitCode"
      if ($runnerExitCode -ne 0) {
        if (Test-CompleteJointReport $report) {
          Write-Warning "Runner returned non-zero after a complete PASS report was written; accepting report and continuing: $report"
        } else {
          throw "formal joint block failed without a complete PASS report: $scenario split $split; exit=$runnerExitCode"
        }
      } elseif (-not (Test-CompleteJointReport $report)) {
        throw "runner returned zero but did not produce a complete PASS report: $scenario split $split"
      }
    }
  }
  Write-Host "FORMAL JOINT COMPLETE: $output"
  }
  finally {
    Stop-Transcript | Out-Null
  }
}
finally {
  if ($null -ne $lockHandle) { $lockHandle.Dispose() }
  if ($lockOwned -and (Test-Path -LiteralPath $lockPath -PathType Leaf)) { Remove-Item -LiteralPath $lockPath -Force }
}
