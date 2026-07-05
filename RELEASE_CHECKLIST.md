# Release Checklist

Use this checklist before the first public push and before any later public-facing release refresh.

## 1. Repository Truthfulness

- Confirm `README.md` and `README_CN.md` describe the repository as a `skill-pack first` skills + methodology repository.
- Confirm `scripted` vs `prompt-only` claims still match the real implementation.
- Confirm no document claims sleep/replay/log harvesting, autonomous multi-agent orchestration, or other capabilities that are not actually implemented here.
- Confirm the default workflow path is still accurate:
  - `Re-search`
  - `literature-gap-workflow`
  - `research-map`
  - `research-hunt`
  - `research-compare`
  - `research-report`

## 2. Public Repository Hygiene

- Confirm `LICENSE` exists and matches the intended release license.
- Confirm `CONTRIBUTING.md`, `CONTRIBUTING_CN.md`, and `AGENT_GUIDE.md` are present and still accurate.
- Confirm `.github/ISSUE_TEMPLATE/`, `.github/pull_request_template.md`, and `.github/workflows/verify.yml` exist.
- Confirm `.gitignore` excludes caches, bytecode, editor files, logs, and local temporary output.
- Confirm no secrets, tokens, or local machine paths are committed.
- Confirm no runtime outputs, caches, or generated artifacts were written into any `skills/<skill>/` directory.

## 3. Verification

- Run:

```powershell
.\scripts\verify.ps1
```

- Confirm the GitHub Actions workflow runs the same repository verification entrypoint.
- If install behavior changed, run a local install smoke test:

```powershell
.\scripts\install.ps1
```

## 4. Git State

- Confirm the working tree is clean:

```powershell
git status --short --branch
```

- Confirm the current branch is `main`.
- Confirm the latest commit message follows the Lore commit protocol.

## 5. GitHub Publication

- Confirm the target repository is `https://github.com/Pineapplee01/Re-search`.
- Confirm repository visibility is `Public`.
- Confirm the default branch is `main`.
- If `origin` is missing, add it:

```powershell
git remote add origin https://github.com/Pineapplee01/Re-search.git
```

- Push the initial public branch:

```powershell
git push -u origin main
```

## 6. Post-Publish Sanity Check

- Open the GitHub repository homepage and confirm the README renders correctly.
- Confirm links to `README_CN.md`, `CONTRIBUTING.md`, `CONTRIBUTING_CN.md`, `AGENT_GUIDE.md`, and this checklist all work.
- Confirm the `Verify` workflow appears and is green after the first push.
- Confirm repository description and topics reflect the actual scope of Re-search.
- Confirm the repo still reads like a focused skills collection, not an overclaimed automation platform.
