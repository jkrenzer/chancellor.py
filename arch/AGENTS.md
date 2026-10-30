# arch folder guide

## Purpose

Chancellor's own architecture records, managed with chancellor itself (dogfooding). See `README.md`.

## Index

- `README.md`: human-facing overview.
- `data/`: record data, one YAML file per kind, named in `/chancellor.yaml` under
  `kinds.<kind>.data`. The source of truth for every record.
- `chancellor.lock`: chancellor's lock file; written by `chancellor build` only.
- `decisions/`: decision records.
- `requirements/`: requirements.
- `specifications/`: specifications.

The three record folders count as tool-prescribed (see "Folder documentation rules" in
`/AGENTS.md`): chancellor writes every file in them. They get no `README.md` or `AGENTS.md` of their
own.

## Rules

- Create and change records in `data/` and render them with `poetry run chancellor build` (or the
  MCP server, once it exists). Never edit a rendered document or the lock.
- Keep `addresses` and `addressed_by` consistent in both directions; `doctor` reports one-sided
  links.
- A decision taken during implementation and not yet confirmed by the maintainer has the state
  `proposed`.
- Do not duplicate rules from `/AGENTS.md` here.
