# Contributing to Re-search

Thanks for contributing to Re-search.

This repository is a `skill-pack first` collection of skills and methodology, not a repo-level Python framework.
Changes should preserve that boundary unless a separate refactor explicitly decides otherwise.

## Repository Contract

Each public skill lives under:

```text
skills/<skill-name>/
```

A skill may contain:

- `SKILL.md`
- optional `references/`
- optional `scripts/`

Do not place runtime outputs, caches, or generated run artifacts inside a skill directory.

## Skill Shapes

Re-search currently uses two execution shapes:

- `prompt-only`
- `scripted`

`prompt-only` skills define protocol and artifact expectations.
`scripted` skills provide deterministic validators, gates, or executors.

## Testing Strategy

Script-backed behavior is verified with colocated tests:

- `skills/*/scripts/test_*.py`

Repository-level verification entrypoint:

```powershell
.\scripts\verify.ps1
```

If you change a script-backed surface, run the relevant colocated tests and then run `scripts/verify.ps1`.

## Modification Principles

- Keep the repository `skill-pack first`
- Prefer small, reversible diffs
- Reuse current patterns before adding new abstractions
- Do not introduce a repo-level shared runtime without a separate, explicit refactor decision
- Keep `SKILL.md` concise and move detailed protocol material into `references/`
- Keep deterministic logic in `scripts/`

## Documentation Expectations

Public-facing changes should keep these documents coherent:

- `README.md`
- `README_CN.md`
- `CONTRIBUTING.md`
- `CONTRIBUTING_CN.md`
- `AGENT_GUIDE.md`

Do not claim capabilities the repository does not actually implement.
