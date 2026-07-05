$ErrorActionPreference = 'Stop'

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$testPaths = @(
    (Join-Path $repoRoot 'skills\Re-search\scripts\test_preflight_run.py'),
    (Join-Path $repoRoot 'skills\literature-gap-workflow\scripts\test_literature_run.py'),
    (Join-Path $repoRoot 'skills\research-hunt\scripts\test_validate_papers_json.py'),
    (Join-Path $repoRoot 'skills\research-hunt\scripts\test_beast_hunt.py')
)

# Scripted skill tests stay next to the scripts that own the behavior.
foreach ($testPath in $testPaths) {
    if (-not (Test-Path -LiteralPath $testPath)) {
        throw "Missing scripted test: $testPath"
    }

    python $testPath
    if ($LASTEXITCODE -ne 0) {
        throw "Test failed: $testPath"
    }
}
