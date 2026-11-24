param(
    [switch]$SkipE2E,
    [string]$TestProjectsDir = 'data/tests',
    [switch]$ShowOutput
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location (Split-Path -Parent $PSScriptRoot)

Write-Host "==> ruff check"
python -m ruff check app celery_app fastapi_scaff tests
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

Write-Host "==> pytest (test projects dir: $TestProjectsDir)"
$pytestArgs = @('tests', "--test-projects-dir=$TestProjectsDir", '-v', '--tb=short', '-ra', '--durations=5')
if ($ShowOutput) {
    $pytestArgs += '-s'
}
if ($SkipE2E) {
    $pytestArgs += '--ignore=tests/test_e2e_generated_project.py'
}
Write-Host "python -m pytest $($pytestArgs -join ' ')"
python -m pytest @pytestArgs
exit $LASTEXITCODE
