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

## Coding agents

The optional `agents` group adds [uv](https://docs.astral.sh/uv/), which runs
[Serena](https://github.com/oraios/serena) (semantic code navigation and editing for agents) in an
environment of its own: Serena pins exact versions that cannot share chancellor's environment.

```bash
poetry install --with agents
```

`.mcp.json` registers Serena for Claude Code as `poetry do -q serena`, `.vscode/mcp.json` for VS
Code with `--context vscode`; the dev container registers it for Codex as well. `poetry do serena`
writes the gitignored `pyrightconfig.json` first (`poetry do pyright-config`), so that Serena's
pyright finds the project's dependencies. Serena keeps its project memories in the gitignored
`.serena/` folder. On first start, uv downloads Serena, a Python for pyright, pyright and Node.js,
which takes a while. Pyright's Node.js needs `libatomic.so.1`, which slim Linux images may lack.

## Routine tasks

| Task                | Purpose                                                            |
| ------------------- | ------------------------------------------------------------------ |
| `poetry do format`  | Format Python and Markdown files.                                  |
| `poetry do lint`    | Check formatting, run pylint, and lint Markdown.                   |
| `poetry do test`    | Run the test suite.                                                |
| `poetry do docs`    | Build this documentation as HTML into `docs/_build/html`.          |
| `poetry do docs-md` | Build this documentation as Markdown into `docs/_build/markdown`.  |
| `poetry do prek`    | Run all pre-commit hooks on the whole tree.                        |
| `poetry do serena`  | Start the Serena MCP server on stdio; `--context` picks the agent. |
