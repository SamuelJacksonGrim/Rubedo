# Start the live runner and the board. Repo root is the working directory.
# The page is http://127.0.0.1:8780/ (8740 and 8770 are already taken).
#
#   powershell -File tools/board/start-board.ps1
#   powershell -File tools/board/start-board.ps1 -SkipPretrain -NoDreamChannel -Steps 40
#
# -Threads is the pin. The digest moves if a replay uses a different count.
# Pretrain is on unless -SkipPretrain. That boot is the long one.

param(
    [int]$Port = 8780,
    [int]$Seed = 42,
    [string]$Workload = "canonical",
    [int]$Steps = 0,
    [int]$Every = 20,
    [int]$Window = 256,
    [int]$Threads = 1,
    [double]$StepDelay = 0,
    [switch]$SkipPretrain,
    [switch]$NoDreamChannel,
    [switch]$NoRhythmReader
)

$ErrorActionPreference = "Stop"
$repo = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
Set-Location $repo

$stamp = Get-Date -Format "yyyyMMddTHHmmss"
$runs = Join-Path $repo "tools\board\runs"
$run = Join-Path $runs "$stamp-seed$Seed-$Workload"
New-Item -ItemType Directory -Force -Path $run | Out-Null

$runnerArgs = @(
    "-3", "-m", "tools.board.run_live",
    "--run-dir", $run,
    "--seed", "$Seed",
    "--workload", $Workload,
    "--steps", "$Steps",
    "--every", "$Every",
    "--window", "$Window",
    "--threads", "$Threads"
)
if ($SkipPretrain) { $runnerArgs += "--skip-pretrain" }
if ($NoDreamChannel) { $runnerArgs += "--no-dream-channel" }
if ($NoRhythmReader) { $runnerArgs += "--no-rhythm-reader" }
if ($StepDelay -gt 0) { $runnerArgs += @("--step-delay", "$StepDelay") }

$boardArgs = @(
    "-3", "-m", "tools.board.server",
    "--port", "$Port",
    "--runs", $runs
)

Start-Process -FilePath "py" -ArgumentList $runnerArgs -WorkingDirectory $repo
Start-Process -FilePath "py" -ArgumentList $boardArgs -WorkingDirectory $repo

Write-Host "runner  $run"
Write-Host "board   http://127.0.0.1:$Port/"
Write-Host "threads $Threads"
if ($SkipPretrain) { Write-Host "pretrain off" } else { Write-Host "pretrain on (the long boot)" }
