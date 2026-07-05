# Beast Hunt Protocol

Use this protocol only when `effort: beast`.

## Goal

Convert `research-hunt` from a single-pass retrieval stage into:

1. same-family breadth fan-out
2. mechanical merge and dedup
3. explicit jury-ready gate
4. independent verdict before stage completion

## Lane Roles

### `venue-first`

- Search top venues and publisher pages with the strongest core queries.
- Return papers that clearly fit the mapped problem.

### `citation-expansion`

- Start from strong seed papers and expand across references, citations, and related-work neighborhoods.
- Return papers that the venue-first lane may miss.

### `boundary-challenger`

- Use exclusion-enforced queries and adjacent terminology to challenge the current scope boundary.
- Return near-miss papers that sharpen what should stay in or out.

### `artifact-verifier`

- For candidate papers, verify article links, official code repositories, and dataset pages.
- This lane does not decide relevance alone; it hardens metadata and reproducibility.

## Execution Rule

- Lanes generate candidates; they do not decide acceptance.
- Merge, dedup, and field completion are mechanical executor work.
- Final acceptance of the merged set is a separate step.

## Beast Commands

Initialize:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" init --state-path "<state.json>" --problem-map "<problem-map.md>"
```

Merge:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" merge --state-path "<state.json>"
```

Jury readiness:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" jury-ready --state-path "<state.json>"
```

Record verdict:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" record-verdict --state-path "<state.json>" --reviewer-type "<model-family-or-fresh-thread>" --verdict accepted --reason "<reason-1>"
```

Assert verdict:

```bash
python "%USERPROFILE%\.agents\skills\research-hunt\scripts\beast_hunt.py" assert-verdict --state-path "<state.json>"
```

## Lane Output Rules

Each lane file in `beast-hunt/lanes/` must:

- stay read-only on shared artifacts
- write only its own lane JSON file
- include `status: completed`
- include a non-empty `papers` array
- include direct article links
- explicitly record whether code and dataset links were found

## Completion Rule

Do not mark `hunt` complete in beast mode until all hold:

1. `papers.json` passes the normal validator
2. `jury-ready` returns `ready: true`
3. an independent reviewer has checked the merged set and written a verdict artifact
4. `assert-verdict` returns accepted

If a genuinely different model family is available, prefer it for the verdict.
If not, use a fresh independent reviewer lane or fresh thread and record that limitation.
