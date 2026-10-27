# chancellor

Chancellor keeps structured records — decisions, requirements, specifications — in one
validated data model and renders them into per-record files plus the core documents
that index them. Builds are incremental and content-hash based, so only what actually
changed is re-rendered, and repeated runs on unchanged input produce byte-identical
output. Templates are Jinja2 and can be overridden per repository. It runs as a CLI and
as an MCP server, so an agent can co-maintain the records alongside you.

> [!IMPORTANT]
> Status: this repository currently contains only the package skeleton, tooling, and CI.
> The renderer implementation is migrated in a follow-up pull request.

## Install

```bash
pip install chancellor
```

Optional extras:

```bash
pip install 'chancellor[git]'
pip install 'chancellor[mcp]'
```

## Developer setup

```bash
git clone https://github.com/jkrenzer/chancellor.py.git
cd chancellor.py
pip install poetry
poetry install --all-extras --with docs
poetry run pre-commit install
```

Common commands:

```bash
poetry run poe format
poetry run poe lint
poetry run poe test
poetry run poe docs
```

## CLI and MCP server

The package exposes the `chancellor` CLI. At this stage it only supports `--version`.
Planned subcommands (not implemented yet): `build`, `hash`, `schema`, `explain`,
`impact`, `doctor`, `recover`, `normalize-eol`.

The MCP server name is `chancellor-records`; its implementation arrives with the
renderer migration.
