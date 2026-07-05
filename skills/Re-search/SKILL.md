---
name: Re-search
description: Use when starting most Re-search tasks to classify the task, inspect the problem boundary, look up strong external solutions, judge migration paths, record boundary risks, and hand off a reusable preflight artifact to the next skill.
---

# Research Preflight

This is the default first station for most Re-search tasks.
It is a thin preflight meta-skill, not the downstream executor.

## Execution Shape

This is a `scripted` meta-skill.
Its artifact manager and validator live in `scripts/preflight_run.py`.

## Inputs

Expected inputs:

- user task or problem statement
- current project root if a target project exists
- any baseline file, code snippet, or design note already provided
- any existing relevant `research-wiki/preflight_runs/<run-id>/preflight.json`

Use the bundled references:

- `references/preflight-template.md`
- `references/source-layering.md`
- `references/preflight-json-spec.md`

## Gate

Run this skill before most downstream tasks in Re-search.

- If a relevant preflight artifact already exists, reuse or refresh it instead of starting from scratch.
- Do not jump straight into a literature workflow, skill refactor, or API implementation task without first making the boundary explicit.
- This skill remains document-first, but its handoff artifact is now script-validated and can be registered into downstream workflow state.

## Work

1. Classify the task into one of these simple types:
   - `research-question`
   - `skill-implementation`
   - `tool-api`
2. Define the problem boundary:
   - what is being solved
   - what is not being solved
   - what counts as success
   - what boundary mistakes are likely
3. Choose the source layer by task type:
   - `research-question` -> high-level papers and paper-linked code first
   - `skill-implementation` -> GitHub skills and authoritative implementation repos first
   - `tool-api` -> official documentation first
4. Look up strong existing solutions instead of immediately designing from scratch.
5. Select only the reference patterns that actually transfer to the current problem.
6. Explain the migration path from the reference pattern to the current task.
7. Record the boundary risks and the things that must not be silently widened.
8. Initialize a preflight run:

```bash
python "scripts/preflight_run.py" init --project-root "<project-root>" --task "<task>" --task-type "<research-question|skill-implementation|tool-api>"
```

9. Fill both artifacts:
   - `preflight.json`
   - `preflight.md`
10. Validate the artifact before handoff:

```bash
python "scripts/preflight_run.py" validate "<research-wiki/preflight_runs/<run-id>>"
```

11. Recommend the next skill explicitly.

Downstream defaults:

- `research-question` -> usually `literature-gap-workflow`
- `skill-implementation` -> usually `writing-skills`, `request-refactor-plan`, or `skill`
- `tool-api` -> whichever downstream skill actually performs the tool-specific work after the docs pass

## Artifacts

Write a paired handoff artifact at:

- `research-wiki/preflight_runs/<YYYYMMDDTHHMMSSZ>-<task-slug>/preflight.json`
- `research-wiki/preflight_runs/<YYYYMMDDTHHMMSSZ>-<task-slug>/preflight.md`

The JSON artifact must include these top-level fields:

- `protocol_version`
- `status`
- `run_id`
- `task`
- `task_slug`
- `task_type`
- `project_root`
- `artifact_markdown`
- `source_layer`
- `problem_boundary`
- `existing_solution_space`
- `selected_reference_patterns`
- `migration_path`
- `boundary_risks`
- `learning_steps`
- `recommended_next_skill`

The Markdown artifact must preserve these semantic sections:

- `task_type`
- `problem_boundary`
- `existing_solution_space`
- `selected_reference_patterns`
- `migration_path`
- `boundary_risks`
- `learning_steps`
- `recommended_next_skill`

Reference records inside the artifact must label:

- source category
- source URL
- why the source matters
- how the pattern transfers
- what boundary limit still applies

The artifact should let a downstream skill continue with less re-reading and less drift.

## Completion

This skill is complete when:

- a validated `preflight.json` and paired `preflight.md` exist in the target project's `research-wiki/`
- the task type is explicit
- the source layer is explicit
- a next skill is explicitly recommended

If the next lane is the literature lane, the artifact should be sufficient for `literature-gap-workflow` to preserve boundary and search direction.
If the next lane is the skill-development lane, the artifact should be sufficient for skill design or refactor work to preserve reference patterns and risk constraints.

## Common Mistakes

- Treating preflight as a vague brainstorming step instead of a boundary-setting step.
- Leaving `preflight.json` in `draft` and handing it to a downstream scripted workflow anyway.
- Mixing GitHub skills, papers, and official docs into one undifferentiated source list.
- Copying a reference pattern without explaining how it transfers.
- Forgetting to mark what is out of boundary.
- Recommending a next skill without leaving a reusable artifact.
