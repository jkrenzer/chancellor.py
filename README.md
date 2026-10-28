# chancellor

Chancellor keeps structured records — decisions, requirements, specifications — in one validated
data model and renders them into per-record files plus the core documents that index them. Builds
are incremental and content-hash based, so only what actually changed is re-rendered, and repeated
runs on unchanged input produce byte-identical output. Templates are Jinja2 and can be overridden
per repository. It runs as a CLI and as an MCP server, so an agent can co-maintain the records
alongside you.

> [!IMPORTANT]
> Status: this repository currently contains only the package skeleton, tooling, and CI. The
> renderer implementation is migrated in a follow-up pull request.

## Install

```bash
pip install chancellor
```

Git support is optional. The `git` extra adds [dulwich](https://www.dulwich.io/) so chancellor can
tell whether a file is tracked or ignored; without it chancellor runs in its no-git configuration,
which is supported and tested:

```bash
pip install 'chancellor[git]'
```

## Developer setup

```bash
git clone https://github.com/jkrenzer/chancellor.py.git
cd chancellor.py
pip install poetry
poetry install --all-extras
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

The package exposes the `chancellor` CLI. At this stage it only supports `--version`. Planned
subcommands (not implemented yet): `build`, `hash`, `schema`, `explain`, `impact`, `doctor`,
`recover`, `normalize-eol`.

The MCP server name is `chancellor-records`; its implementation arrives with the renderer migration.

Full documentation lives in [`docs/`](docs/index.md) and builds with `poetry run poe docs`.

## License

Copyright (C) 2026 Jörn Krenzer.

Chancellor is licensed under the [GNU Affero General Public License v3.0](LICENSE) only. You are
free to use and run it; if you pass on a modified version, you must pass on its source under the
same license.

As provided in section 14 of the license, Jörn Krenzer is designated as proxy to decide whether
future versions of the GNU Affero General Public License can be used for chancellor.
