# Agent instructions

This repository is maintained with multiple AI coding tools. `AGENTS.md` is the
single source of truth; vendor-specific files should only point here.

## Folder documentation rules

- Each root-level folder should include a `README.md` and an `AGENTS.md`.
- A folder's `AGENTS.md` indexes the folder and states folder-specific rules.
- Use progressive context loading: read parent instructions first, then descend.
- A child rule can override a parent rule only when it names the overridden rule and
  explains why the override is required.

## Git and commit rules

- Never commit, push, rebase, or create branches unless explicitly requested.
- Propose commits only after requested work is complete and verified.
- Use Conventional Commits and validate with `conventional-pre-commit --strict`.

## Markdown rules

- Keep lines at 100 characters unless a longer line is unavoidable.
- Use consistent heading levels and fenced code blocks with language hints.

## Tooling notes

- Use Poetry for dependency management and virtual environments.
- Use `poe` tasks for routine formatting, linting, testing, docs, and release actions.
- Run pre-commit hooks before proposing commits.
