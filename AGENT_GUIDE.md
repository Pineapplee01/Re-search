# Re-search Agent Guide

This guide is for agents and automation surfaces working inside the Re-search repository.

## Core Positioning

Re-search is a `skill-pack first` repository.
The public boundary is each directory under `skills/`.
Do not treat this repository as a repo-level Python package unless a later explicit refactor changes that rule.

## Default Entry

For most tasks, start with:

1. `Re-search`
2. the recommended downstream skill from the preflight artifact

For literature work, the normal lane is:

1. `Re-search`
2. `literature-gap-workflow`
3. `research-map`
4. `research-hunt`
5. `research-compare`
6. `research-report`

## Artifact Discipline

Prefer explicit artifacts over hidden chat memory.

Important artifact families:

- `research-wiki/preflight_runs/<run-id>/`
- `research-wiki/literature_runs/<run-id>/`

Important files include:

- `preflight.json`
- `preflight.md`
- `problem-map.md`
- `baseline-snapshot.md`
- `papers.json`
- `difference-matrix.md`
- `report.md`
- `state.json`

## Skill Directory Contract

Each skill directory may contain only:

- `SKILL.md`
- optional `references/`
- optional `scripts/`

Use these roles consistently:

- `SKILL.md`: public workflow contract
- `references/`: templates, protocols, schema notes
- `scripts/`: deterministic validators, gates, and executors

Do not write runtime outputs into skill directories.

## Scripted vs Prompt-Only

`prompt-only` skills:

- define protocol
- define required artifacts
- do not provide a runtime executor in this repository

`scripted` skills:

- provide validators, gates, or executors
- should have colocated tests under `scripts/test_*.py`

## Verification

Repository-level verification entrypoint:

```powershell
.\scripts\verify.ps1
```

If you change a scripted surface, run the relevant local tests and then the repository verify script.

## Design Guardrails

- Keep the repository `skill-pack first`
- Do not invent capabilities not implemented here
- Do not add a repo-level shared runtime casually
- Keep public docs aligned with actual implementation
- Prefer artifact-based handoff over thread-memory handoff
