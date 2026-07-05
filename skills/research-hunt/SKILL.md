---
name: research-hunt
description: Use when a mapped research question needs a high-quality paper set, with venue-first screening, article links, and reusable paper/code/dataset metadata written into the active literature run artifacts.
---

# Research Hunt

This stage finds and filters papers. It must run after `research-map` and before `research-compare`.

## Execution Shape

This is a `scripted` stage.
Its script-backed surfaces are `scripts/validate_papers_json.py` and `scripts/beast_hunt.py`.

## Inputs

Required:

- `state.json` path
- `problem-map.md`
- `baseline-snapshot.md`
- preferred handoff: relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Read `effort` from `state.json`.
Treat any stored `mode` only as derived internal depth.
Use the bundled schema guide at `references/papers-json-spec.md`.
If `effort: beast`, also use `references/beast-hunt-protocol.md`.

## Gate

Before doing any search, verify:

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" assert-stage --state-path "<state.json>" --stage hunt
```

If this fails, stop and fix the earlier stage.
If this stage is invoked directly, first run `Re-search` or reuse a relevant preflight artifact.

## Work

Default search policy:

- English high-level literature first
- top conference / top journal first
- arXiv only as a supplement

Preferred reuse:

- `research-writing:literature-review` discipline
- `research-lit` multi-source logic
- `semantic-scholar`
- `openalex`

Search source priority:

1. official publisher / DOI / arXiv page for the paper itself
2. official project page linked by the paper or authors
3. official code repository
4. official dataset page or benchmark page
5. only then secondary aggregators such as Papers with Code

If a preflight artifact exists, use it to keep:

- source layering
- reference directions
- migration hypotheses
- boundary risks

stable across the search pass.

Effort-sensitive behavior:

- `lite`: small, fast venue-first set
- `balanced`: default single-agent venue-first set
- `max`: deeper single-agent search and stronger filtering
- `beast`: deep search plus multi-agent cross-search and result cross-check

Beast invariant:

- fan out for breadth
- merge mechanically
- do not let search lanes judge acceptance

1. Read `problem-map.md`.
2. Search for venue papers matching the mapped problem.
3. Filter for quality and relevance.
4. For every selected paper, find a direct article link.
5. Check whether official open-source code and public dataset links exist.
6. Write `papers.json`.
7. Validate `papers.json` with the bundled validator before completion.
8. Optionally summarize a short human-readable search note into `problem-map.md` or a sidecar note, but `papers.json` is the primary artifact.
9. Mark the `hunt` stage complete.

If `effort != beast`, the normal path above is enough.

If `effort == beast`, replace Steps 2-9 with this executor:

1. Initialize beast hunt artifacts:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" init --state-path "<state.json>" --problem-map "<problem-map.md>"
```

2. Fan out across these lanes:
   - `venue-first`
   - `citation-expansion`
   - `boundary-challenger`
   - `artifact-verifier`
3. Each lane writes only its own file under `beast-hunt/lanes/<lane-id>.json`.
4. Lane outputs are candidate-generation artifacts, not verdicts.
5. Merge and mechanically dedup:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" merge --state-path "<state.json>"
```

6. Check jury readiness:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" jury-ready --state-path "<state.json>"
```

7. Send the merged set to an independent reviewer:
   - preferred: a genuinely different model family
   - fallback: a fresh independent reviewer thread or subagent
8. Record the reviewer verdict:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" record-verdict --state-path "<state.json>" --reviewer-type "<model-family-or-fresh-thread>" --verdict accepted --reason "<reason-1>" --reason "<reason-2>"
```

9. Assert the verdict before completion:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" assert-verdict --state-path "<state.json>"
```

10. Only after the reviewer verdict and validator both pass, run `complete-stage`.

Paper-set size guidance:

- `lite`: 3-5 papers
- `balanced`: 5-10 papers
- `max`: 10-20 papers, usually clustered by subtopic
- `beast`: 10-20 papers with 4 search lanes preferred over one oversized pass

## Artifacts

Each selected paper should include at least:

- `paper_id`
- `title`
- `authors`
- `year`
- `venue`
- `venue_type`
- `article_url`
- `code_url`
- `dataset_urls`
- `source`
- `why_relevant`
- `is_primary_evidence`
- `artifact_search_notes`

Rules:

- `article_url` is mandatory for every paper.
- `code_url` must exist as a field even when no repo is found; use `null` in that case.
- `dataset_urls` must exist as a field even when no dataset is found; use `[]` in that case.
- `artifact_search_notes` must say where code and dataset links were checked.
- Never return search-result pages as `article_url`, `code_url`, or `dataset_urls`.
- In beast mode, add:
  - `supporting_lanes`
  - `crosscheck_status`

If `effort == beast`, the stage also owns these artifacts under `beast-hunt/`:

- `lane-plan.json`
- `lanes/<lane-id>.json`
- `merge-report.json`
- `jury-input.json`
- `jury-verdict.json`

## Completion

First validate:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\validate_papers_json.py" "<papers.json>"
```

If `effort == beast`, also assert the verdict:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" assert-verdict --state-path "<state.json>"
```

Then complete:

```bash
python "%USERPROFILE%\.agents\skills\literature-gap-workflow\scripts\literature_run.py" complete-stage --state-path "<state.json>" --stage hunt --artifact "<papers.json>"
```

## Common Mistakes

- Skipping `Re-search` and then searching with no explicit boundary.
- Ranking only by citation count and ignoring venue quality.
- Filling the set with preprints when published papers exist.
- Returning links without a relevance judgment.
- Omitting article links, or failing to record whether code / dataset links were checked.
- Letting multiple same-family search lanes vote on acceptance. Lanes search; they do not acquit.
- Starting gap analysis in this stage. This stage curates papers, not differences.
