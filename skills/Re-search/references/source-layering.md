# Source Layering

Use source layers deliberately. Do not mix them into one bucket.

## `research-question`

Preferred order:

1. high-level papers
2. paper-linked code or project pages
3. benchmark or dataset pages
4. implementation repos only when they clarify deployment reality

Use this lane when the task is mainly:

- framing a research problem
- finding prior work
- judging novelty or gap
- transferring method ideas into a new research setting

## `skill-implementation`

Preferred order:

1. GitHub skills repositories
2. authoritative implementation repos
3. official docs for the specific runtime or tool
4. papers only when the skill encodes a research workflow

Use this lane when the task is mainly:

- creating a new skill
- refactoring a skill
- adding a validator or executor
- learning how a strong skill repo structures prompts, scripts, and references

## `tool-api`

Preferred order:

1. official docs
2. official examples
3. authoritative issue discussions or release notes
4. community repos only as secondary confirmation

Use this lane when the task is mainly:

- learning a library or API
- checking parameter behavior
- understanding a runtime surface
- resolving version-specific tool behavior

## Required Record Discipline

For every selected reference, record:

- source category
- source URL
- why it matters
- what transfers
- what does not transfer
