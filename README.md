# Re-search

[中文说明](README_CN.md) | [Contributing](CONTRIBUTING.md) | [Agent Guide](AGENT_GUIDE.md)

Re-search is a Codex-oriented skill pack and research/implementation methodology repository.
It is designed for two recurring job families:

- research and literature analysis
- skill and workflow design grounded in strong external solutions

This repository is `skill-pack first`.
Its public interface is the set of directories under `skills/`, not a repo-level Python package or a monolithic automation framework.

## Methodology First

Re-search follows a simple discipline before doing work:

1. define the problem boundary
2. inspect strong existing solutions
3. judge what can migrate into the current task
4. mark boundary risks explicitly
5. learn before implementing

This applies to both research tasks and skill-development tasks.
The goal is to reduce drift, overclaiming, and noisy ad hoc execution.

## Default Path

The default path through this repository is:

1. `Re-search`
2. `literature-gap-workflow`
3. `research-map`
4. `research-hunt`
5. `research-compare`
6. `research-report`

`Re-search` is the preflight entry.
It classifies the task, defines the boundary, records reusable external reference patterns, and hands off a validated preflight artifact.

## Included Skills

| Skill | Shape | Role |
| --- | --- | --- |
| `Re-search` | scripted | Preflight meta-skill and handoff contract |
| `literature-gap-workflow` | scripted | Thin staged workflow entry |
| `research-map` | prompt-only | Problem mapping and baseline snapshot |
| `research-hunt` | scripted | Paper curation, validation, beast-mode merge/jury gates |
| `research-compare` | prompt-only | Difference analysis against baseline |
| `research-report` | prompt-only | Fixed-structure final report |

## Script-Backed Surfaces

Current deterministic surfaces include:

- `skills/Re-search/scripts/preflight_run.py`
- `skills/literature-gap-workflow/scripts/literature_run.py`
- `skills/research-hunt/scripts/validate_papers_json.py`
- `skills/research-hunt/scripts/beast_hunt.py`

They provide artifact initialization, validation, gating, and merge/jury control.
Prompt-only stages remain intentionally thin and consume structured artifacts instead of hidden chat memory.

## Artifact Model

Re-search uses explicit artifacts rather than relying on thread memory alone.

- preflight artifacts live under `research-wiki/preflight_runs/<run-id>/`
- literature workflow artifacts live under `research-wiki/literature_runs/<run-id>/`

Important artifacts include:

- `preflight.json`
- `preflight.md`
- `problem-map.md`
- `baseline-snapshot.md`
- `papers.json`
- `difference-matrix.md`
- `report.md`
- `state.json`

## Install

PowerShell:

```powershell
.\scripts\install.ps1
```

This links each public skill directory into `$env:USERPROFILE\.agents\skills`.

## Verify

PowerShell:

```powershell
.\scripts\verify.ps1
```

This runs the current script-backed test surfaces through one repository-level entrypoint.

## Repository Layout

```text
skills/
  <skill-name>/
    SKILL.md
    references/
    scripts/
scripts/
  install.ps1
  verify.ps1
tests/
  README.md
```

## What This Repository Is Not

Re-search is not presented as:

- a complete autonomous research platform
- a generic Python framework
- a sleep/replay/log-harvesting system

The public release style aligns with repositories such as ARIS in readability and publishing hygiene, but the implementation scope remains limited to what is actually present here.

## Notes

- Public user control for the literature workflow is `effort: lite | balanced | max | beast`
- Legacy `mode` input is intentionally unsupported
- Shared runtime extraction is intentionally deferred until multiple scripted skills truly need it
