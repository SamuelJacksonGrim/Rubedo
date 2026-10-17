# run_all_tests.ps1 - Windows runner for the pass/fail suite.
#
# Runs every `run_test "..."` module listed in run_all_tests.sh (the single list of
# what CI gates), one Python process each, and prints PASS/FAIL plus a total.
# Rubedo has no venv of its own on this box; it uses RFE-Core2's (torch cu128).
#
#   powershell -File run_all_tests.ps1
#   powershell -File run_all_tests.ps1 -Python C:\path\to\python.exe
param(
  [string]$Python = "C:\Users\spamw\rfe\RFE-Core2\.venv\Scripts\python.exe"
)
$env:PYTHONUTF8 = "1"   # without it, cp1252 printing makes ~15 tests fail falsely
Set-Location $PSScriptRoot
$tests = Select-String -Path run_all_tests.sh -Pattern '^run_test "([^"]+)"' |
  ForEach-Object { $_.Matches[0].Groups[1].Value }
$pass = 0; $fail = @()
foreach ($t in $tests) {
  & $Python -m $t *> $null
  if ($LASTEXITCODE -eq 0) { $pass++; "PASS $t" } else { $fail += $t; "FAIL $t (exit $LASTEXITCODE)" }
}
"passed $pass / $($tests.Count)"
if ($fail) { "FAILED: $($fail -join ', ')"; exit 1 }
