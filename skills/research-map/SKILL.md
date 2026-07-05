---
name: research-map
description: Use when a literature workflow needs to convert a research question and user baseline into a scoped problem map, search vocabulary, venue targets, and a reusable baseline snapshot before searching papers.
---

# Research Map

This stage defines the search problem. It must run before `research-hunt`.

## Execution Shape

This is a `prompt-only` stage.
It does not provide a stage executor script in this repository.

## Inputs

Required:

- question
- `state.json` path for the active literature run
- baseline source:
  - local document path, or
  - pasted baseline text
- preferred handoff: relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Read `effort` from `state.json`.
Do not ask the user for a separate `mode` value.
Use the bundled templates:

- `references/problem-map-template.md`
- `references/baseline-snapshot-template.md`

## Gate

Do not proceed if no baseline is available.
Do not ask the user for a separate `mode` value.
If this stage is invoked directly, first run `Re-search` or reuse a relevant preflight artifact.

## Work

1. Read the question.
2. Read the baseline document or baseline text.
3. Produce two artifacts:
   - `problem-map.md`
   - `baseline-snapshot.md`
4. Mark the `map` stage complete in `state.json`.

Keep these artifacts structurally close to the bundled templates so later stages can consume them reliably.
If a preflight artifact exists, preserve its problem boundary and source directions rather than re-inventing them from scratch.

The mapping must be specific enough to drive paper search.
If the baseline is too vague to compare against papers, ask for clarification instead of inventing details.

## Artifacts

`problem-map.md` must include:

- problem statement
- related research fields
- English search keywords
- synonyms / alternate phrasings
- exclusion keywords
- target venue families with short rationale
- grouped search queries:
  - core queries
  - expansion queries
  - exclusion-enforced queries
- recommended effort profile with derived runtime depth:
  - `lite` -> internal `quick`
  - `balanced` -> internal `standard`
  - `max` -> internal `deep`
  - `beast` -> internal `deep`

`baseline-snapshot.md` must include:

- current research goal
- target scenario
- core method assumption
- expected evidence/result shape
- explicit boundaries and non-goals

The map should yield at least 3 usable English query groups, not only keyword fragments.

## Completion

After writing the map artifact:

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" complete-stage --state-path "<state.json>" --stage map --artifact "<problem-map.md>"
```

## Common Mistakes

- Skipping the baseline snapshot and jumping to search keywords only.
- Producing only Chinese keywords for an English-paper workflow.
- Mixing search planning with paper analysis. This stage does not evaluate papers.
