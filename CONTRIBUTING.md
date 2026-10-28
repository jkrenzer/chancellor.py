# Contributing

## Commit messages

This repository enforces Conventional Commits (`conventional-pre-commit --strict`). Use these types:

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
- `deps`
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

## Licensing of contributions

Chancellor is licensed under the AGPL-3.0-only. By submitting a contribution you agree that it is
made under the same license.

A contributor license agreement is in preparation. Until it is in place, contributions from outside
the project cannot be merged; feel free to open an issue to discuss a change meanwhile.
