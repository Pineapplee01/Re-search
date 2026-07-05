# Preflight JSON Spec

`preflight.json` is the machine-readable contract for the `Re-search` handoff.
`preflight.md` is the human-readable companion artifact.

## Required Top-Level Fields

- `protocol_version`
- `status`
- `run_id`
- `task`
- `task_slug`
- `task_type`
- `project_root`
- `artifact_markdown`
- `problem_boundary`
- `existing_solution_space`
- `selected_reference_patterns`
- `migration_path`
- `boundary_risks`
- `learning_steps`
- `recommended_next_skill`
- `created_at`
- `updated_at`

## Field Rules

### `status`

Allowed values:

- `draft`
- `ready`

Only `ready` artifacts should be handed to downstream scripted workflows.

### `task_type`

Allowed values:

- `research-question`
- `skill-implementation`
- `tool-api`

### `problem_boundary`

Required fields:

- `goal`
- `non_goals`
- `success_signal`
- `boundary_traps`

`non_goals` and `boundary_traps` must be lists of non-empty strings.

### `existing_solution_space`

Each entry must include:

- `ref_id`
- `source_category`
- `title`
- `url`
- `why_it_matters`

Allowed `source_category` values:

- `github-skill`
- `implementation-repo`
- `paper`
- `paper-code`
- `project-page`
- `dataset-page`
- `official-doc`
- `official-example`
- `release-note`
- `issue-discussion`
- `community-repo`

### `selected_reference_patterns`

Each entry must include:

- `ref_id`
- `reusable_pattern`
- `transfer_decision`
- `boundary_limit`

Allowed `transfer_decision` values:

- `keep`
- `adapt`
- `reject`

Each `ref_id` must refer to an entry already present in `existing_solution_space`.

### `migration_path`

Required fields:

- `transfers_directly`
- `needs_adaptation`
- `do_not_copy`

All three fields must be lists of non-empty strings.

### `boundary_risks`

Must be a non-empty list of non-empty strings.

### `learning_steps`

Must be a non-empty list of non-empty strings.

### `recommended_next_skill`

Required fields:

- `skill`
- `why`
- `context_to_inherit`

`context_to_inherit` must be a non-empty list of non-empty strings.

## Markdown Companion

The sibling `preflight.md` should preserve the same semantic sections:

- `task_type`
- `problem_boundary`
- `existing_solution_space`
- `selected_reference_patterns`
- `migration_path`
- `boundary_risks`
- `learning_steps`
- `recommended_next_skill`

The JSON file is the gate artifact.
The Markdown file is the readable handoff for downstream prompt-driven stages.
