---
name: research-report
description: Use when a literature workflow already has a problem map, curated paper set, and difference matrix and needs a fixed-structure Chinese report with Motivation, Method, and Result sections.
---

# Research Report

This stage writes the final user-facing report. It must run after `research-compare`.

## Execution Shape

This is a `prompt-only` stage.
It does not provide a stage executor script in this repository.

## Inputs

Required:

- `state.json`
- `problem-map.md`
- `papers.json`
- `difference-matrix.md`
- preferred handoff: relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Read `effort` from `state.json`.
Treat any stored `mode` only as derived internal depth.
Use the bundled template at `references/report-template.md`.

## Gate

Before writing, verify:

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" assert-stage --state-path "<state.json>" --stage report
```

If this stage is invoked directly, first run `Re-search` or reuse a relevant preflight artifact.

## Work

Write `report.md` with these sections in this order:

1. `Problem Mapping`
2. `Literature Search`
3. `Difference Analysis`
4. `Motivation`
5. `Method`
6. `Result`

The report language should be Chinese by default.
Paper titles, venue names, and method names may remain in English.
Default audience is an internal research memo unless the user explicitly asks for a different audience.

If the run uses `effort: beast`, the report should explicitly surface any disagreements resolved during cross-check.
If a preflight artifact exists, use it to preserve the original problem boundary, migration path, and risk framing.

## Artifacts

Section rules:

- `Problem Mapping`: summarize the mapped research problem and field.
- `Literature Search`: summarize the high-level paper set, search scope, and why those papers were selected.
- `Difference Analysis`: synthesize the main differences from the matrix with explicit `paper_id` references.
- `Motivation`: explain why the user's research direction matters given the literature gaps.
- `Method`: explain what the user's research is trying to do differently.
- `Result`: close the loop between method and evidence, including what still must be validated if results are not yet established.

Reporting rules:

- Every section except `Method` should cite supporting `paper_id` values where applicable.
- `Literature Search` should state coverage limits and inclusion logic, not only list papers.
- `Result` must clearly label statements as `validated`, `proposed`, or `pending validation`.

## Completion

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" complete-stage --state-path "<state.json>" --stage report --artifact "<report.md>"
```

## Common Mistakes

- Skipping `Re-search` and reframing the problem while reporting.
- Skipping the fixed section order.
- Turning the report into only a paper list.
- Treating planned results as already validated results without marking the evidence boundary.
- Reopening earlier evidence decisions in the reporting stage.
- Writing uncited claims that cannot be traced back to `papers.json` or `difference-matrix.md`.
