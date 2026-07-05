---
name: research-compare
description: Use when a literature workflow already has a baseline snapshot and curated paper set and now needs a structured difference analysis between the user's research and prior work.
---

# Research Compare

This stage converts papers into a difference matrix. It must run after `research-hunt`.

## Execution Shape

This is a `prompt-only` stage.
It does not provide a stage executor script in this repository.

## Inputs

Required:

- `state.json`
- `baseline-snapshot.md`
- `papers.json`
- preferred handoff: relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Read `effort` from `state.json`.
Treat any stored `mode` only as derived internal depth.
Use the bundled template at `references/difference-matrix-template.md`.

## Gate

Before analysis, verify:

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" assert-stage --state-path "<state.json>" --stage compare
```

If this stage is invoked directly, first run `Re-search` or reuse a relevant preflight artifact.

## Work

1. Read the baseline snapshot.
2. Read the curated papers metadata.
3. Compare prior work against the user's research on fixed dimensions.
4. Write `difference-matrix.md`.
5. Mark the `compare` stage complete.

If the run uses `effort: beast`, this stage should perform cross-check verification rather than a single comparison pass.

For every major comparison claim, cite the contributing `paper_id` values from `papers.json`.
Do not write unsupported synthesis with no paper back-reference.
If a preflight artifact exists, keep its migration judgment and boundary risks visible while comparing.

## Artifacts

At minimum compare:

- problem definition
- task/scenario
- core method
- evidence and evaluation
- limitations
- remaining innovation space

`difference-matrix.md` should contain:

- a short synthesis paragraph
- a table or structured matrix
- a final section:
  - `Most Relevant Gaps To Exploit`

Each row in the matrix should include:

- `paper_id`
- problem / scenario fit
- method overlap or difference
- evidence strength
- limitation relevant to the user's work
- actionable gap note

The matrix should clearly distinguish:

- same problem, different method
- similar method, different scenario
- same scenario, insufficient evidence

## Completion

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" complete-stage --state-path "<state.json>" --stage compare --artifact "<difference-matrix.md>"
```

## Common Mistakes

- Skipping `Re-search` and losing the original migration question.
- Writing generic "our work is novel" claims without evidence.
- Comparing only topics, not methods and evidence.
- Treating missing information as proof of novelty.
- Rewriting the baseline instead of comparing against it.
- Losing traceability by omitting `paper_id` references.
