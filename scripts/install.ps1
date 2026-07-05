param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path,
    [string]$SkillsRoot = "$env:USERPROFILE\.agents\skills"
)

$ErrorActionPreference = 'Stop'

# This repository installs standalone skill directories rather than a repo-level package.
$skillNames = @(
    'Re-search',
    'literature-gap-workflow',
    'research-map',
    'research-hunt',
    'research-compare',
    'research-report'
)

function Assert-SkillBoundary {
    param(
        [string]$SkillDir
    )

    if (-not (Test-Path -LiteralPath $SkillDir)) {
        throw "Missing source skill directory: $SkillDir"
    }

    $skillFile = Join-Path $SkillDir 'SKILL.md'
    if (-not (Test-Path -LiteralPath $skillFile)) {
        throw "Skill boundary is missing SKILL.md: $SkillDir"
    }
}

New-Item -ItemType Directory -Force -Path $SkillsRoot | Out-Null

foreach ($name in $skillNames) {
    $source = Join-Path $RepoRoot "skills\$name"
    $target = Join-Path $SkillsRoot $name

    Assert-SkillBoundary -SkillDir $source

    if (Test-Path $target) {
        $item = Get-Item -LiteralPath $target -Force
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            Remove-Item -LiteralPath $target -Force
        } else {
            Remove-Item -LiteralPath $target -Recurse -Force
        }
    }

    cmd /c mklink /J "$target" "$source" | Out-Null
    Write-Host "Linked $name -> $source"
}
