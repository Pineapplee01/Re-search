# Tests

This repository uses a colocated test strategy for scripted skills.

Default unit-test location:

- `skills/*/scripts/test_*.py`

Current scripted test surfaces:

- `skills/Re-search/scripts/test_preflight_run.py`
- `skills/literature-gap-workflow/scripts/test_literature_run.py`
- `skills/research-hunt/scripts/test_validate_papers_json.py`
- `skills/research-hunt/scripts/test_beast_hunt.py`

Prompt-only skills such as `research-map`, `research-compare`, and `research-report`
currently rely on protocol and artifact discipline rather than scripted validators in this repository.

The root `tests/` directory is reserved for:

- repository-level testing notes
- future cross-skill integration tests if they become necessary

Use:

```powershell
.\scripts\verify.ps1
```

to run the current scripted test suite through one repo-wide entrypoint.
