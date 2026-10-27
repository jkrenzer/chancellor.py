# Contributing

## Commit messages

This repository enforces Conventional Commits (`conventional-pre-commit --strict`).
Use these types:

- `feat`
- `fix`
- `docs`
- `refactor`
- `test`
- `build`
- `ci`
- `chore`

Recommended scopes in this repository include:

- `packaging`
- `cli`
- `templates`
- `tests`
- `docs`
- `ci`
- `agents`

## Branch naming

Use:

```text
<user>-<yyyy-mm-dd>-<topic>-v<nn>
```

Example:

```text
jkrenzer-2026-10-27-bootstrap-repo-v01
```

## Pull requests

- Keep PRs focused and small.
- Ensure `poetry run poe lint` and `poetry run poe test` pass.
- For releases, configure Trusted Publishing on PyPI before pushing the first `v*` tag.
