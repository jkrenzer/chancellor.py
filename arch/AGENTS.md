# arch folder guide

## Purpose

Chancellor's own architecture records, managed with chancellor itself (dogfooding). See `README.md`.

## Index

- `README.md`: human-facing overview.
- `decisions/`: decision records.
- `requirements/`: requirements.
- `specifications/`: specifications.

The three record folders count as tool-prescribed (see "Folder documentation rules" in
`/AGENTS.md`): chancellor will define their file layout, and it may read every file in them. They
get no `README.md` or `AGENTS.md` of their own. Until records exist they hold only `.gitkeep`.

## Rules

- Do not add records by hand before the record format is settled. The design is handed off through
  `.agents/tmp/`. Ask the maintainer which hand-off applies.
- Once chancellor can manage records, create and change them with the `chancellor` command (or its
  MCP server), not by editing generated output.
- Do not duplicate rules from `/AGENTS.md` here.
