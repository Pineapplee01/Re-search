---
name: literature-gap-workflow
description: Use when repeatedly doing literature analysis on a research question and wanting a thin workflow entry that orchestrates staged mapping, paper hunting, comparison, and reporting with reusable project artifacts.
---

# Literature Gap Workflow

Use this as the thin entrypoint. It does not do every step itself.

## Execution Shape

This is a `scripted` orchestration skill.
Its runtime gate lives in `scripts/literature_run.py`.

## Inputs

Expect the user input to contain:

- `question: ...`
- `baseline: <document path or pasted text>`
- `effort: lite | balanced | max | beast`
- preferred handoff: latest relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Defaults:

- `effort` defaults to `balanced`
- `balanced` maps to `standard`
- report language defaults to Chinese
- paper titles, venue names, method names stay in English

Legacy `mode` input is not compatible.
If the user provides legacy `mode`, normalize it manually:

- `quick` -> `lite`
- `standard` -> `balanced`
- `deep` -> `max` or `beast`

Then continue with `effort` as the only accepted control field.

`mode` is derived runtime state, not a user-facing argument.

## Gate

The workflow does not bypass baseline gating.

- Before entering this workflow, first run `Re-search` or reuse a relevant preflight artifact.
- If `baseline` is missing, stop and ask for either a document path or 5-8 lines of baseline text.
- Do not continue directly to paper search without baseline context.
- Later stages must rely on `state.json` rather than ad hoc memory.

## Work

Run this stage order:

1. `research-map`
2. `research-hunt`
3. `research-compare`
4. `research-report`

Use this orchestration sequence:

1. Resolve project root from the current workspace.
2. Run `Re-search` first, or load the latest relevant preflight artifact from `research-wiki/preflight_runs/`.
3. Use the preflight artifact to preserve:
   - problem boundary
   - selected source directions
   - migration judgment
   - boundary risks
4. Run:

```bash
python "scripts/literature_run.py" init-run --project-root "<project-root>" --question "<question>" --effort "<effort>"
```

If a validated preflight artifact already exists, attach it during init:

```bash
python "scripts/literature_run.py" init-run --project-root "<project-root>" --question "<question>" --effort "<effort>" --preflight "<research-wiki/preflight_runs/<run-id>>"
```

5. If a baseline was provided, register it:

```bash
python "scripts/literature_run.py" set-baseline --state-path "<state.json>" --source-type path --source-value "<baseline-path>"
```

or:

```bash
python "scripts/literature_run.py" set-baseline --state-path "<state.json>" --source-type text --source-value "<baseline-text>"
```

6. Then invoke the stage skills in order:

- `research-map`
- `research-hunt`
- `research-compare`
- `research-report`

7. Between stages, rely on `state.json` for gate checks.
8. If a preflight artifact was created after run init, register it:

```bash
python "scripts/literature_run.py" set-preflight --state-path "<state.json>" --preflight "<research-wiki/preflight_runs/<run-id>>"
```

9. Re-run only the stage that needs to change:
   - `research-hunt` without redoing `research-map`
   - `research-compare` without re-pulling papers
   - `research-report` without changing prior evidence

`beast` is not only a deeper search budget.
It means:

- deep search scope
- multi-agent cross-search during `research-hunt`
- cross-check verification during `research-compare`
- stricter evidence reconciliation before `research-report`

Operationally, `research-hunt` should use its beast executor with:

- lane fan-out
- mechanical merge
- jury-ready gate
- recorded independent verdict before stage completion
- completion blocked unless the verdict artifact is accepted

## Artifacts

Each run owns these files:

- `problem-map.md`
- `baseline-snapshot.md`
- `papers.json`
- `difference-matrix.md`
- `report.md`
- `state.json`

Never invent alternative file names for the primary artifacts.

## Completion

The workflow is complete only after `report` is completed and prior stage artifacts remain consistent with `state.json`.
This entrypoint owns orchestration and gate state; it is not the analysis engine itself.

## Common Mistakes

- Skipping `Re-search` and starting from an unbounded question.
- Treating this workflow as the analysis engine. It is only the orchestrator.
- Running `research-hunt` before baseline and mapping are recorded.
- Writing results outside `research-wiki/literature_runs/<run-id>/`.
- Letting later stages silently change evidence from earlier stages.
