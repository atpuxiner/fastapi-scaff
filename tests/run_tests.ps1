param(
    [switch]$SkipE2E,
    [string]$TestProjectsDir = 'data/tests'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "==> ruff check"
python -m ruff check tests
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "==> pytest (test projects dir: $TestProjectsDir)"
$pytestArgs = @('tests', '-q', "--test-projects-dir=$TestProjectsDir")
if ($SkipE2E) {
    $pytestArgs += '--ignore=tests/test_e2e_generated_project.py'
}
python -m pytest @pytestArgs
exit $LASTEXITCODE
