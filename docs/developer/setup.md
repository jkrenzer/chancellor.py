# Development setup

Chancellor uses [Poetry](https://python-poetry.org/) 2.3 or later for dependencies and virtual
environments, and [Poe the Poet](https://poethepoet.natn.io/) tasks for routine work.

## Dev container

The repository includes a `Dockerfile` and `.devcontainer/devcontainer.json`. Opening the repository
in a dev container or a codespace gives Python 3.14, git, the GitHub CLI, Poetry, Claude Code and
Codex, with all dependency groups and extras installed. You work as the non-root user `dev`.
{doc}`environments` describes agent access, accounts, unattended runs and how to extend the setup.

Chancellor itself is installed in editable mode, so the `chancellor` command always runs the code in
your working tree; chancellor manages its own design records in `arch/`. `poetry install` does this
by default, in the dev container (re-run after creation, so it points at the mounted repository),
locally and in CI.

The container uses the Docker daemon of the host (dev container feature `docker-outside-of-docker`)
so that MCP servers shipped as images, like GitHub's, can run as containers: for VS Code from
`.vscode/mcp.json`, for Claude Code and Codex from `.devcontainer/environments/local.sh`. Access to
the Docker socket amounts to root access on the host's Docker.

## Local setup

```bash
git clone https://github.com/jkrenzer/chancellor.py.git
cd chancellor.py
poetry install --all-extras
poetry run pre-commit install
```

`poetry install` installs the `dev` and `docs` dependency groups. `--all-extras` adds the `git`
extra; leave it out to work in the no-git configuration.

## Routine tasks

| Task                     | Purpose                                                           |
| ------------------------ | ----------------------------------------------------------------- |
| `poetry run poe format`  | Format Python and Markdown files.                                 |
| `poetry run poe lint`    | Check formatting, run pylint, and lint Markdown.                  |
| `poetry run poe test`    | Run the test suite.                                               |
| `poetry run poe docs`    | Build this documentation as HTML into `docs/_build/html`.         |
| `poetry run poe docs-md` | Build this documentation as Markdown into `docs/_build/markdown`. |
| `poetry run poe prek`    | Run all pre-commit hooks on the whole tree.                       |
