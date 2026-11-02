# .agents folder guide

## Purpose

This folder contains cross-tool agent metadata, context, scripts, and skills.

## Index

- `README.md`: human-facing overview, including the Claude symlink restore procedure.
- `context/`: reusable context snippets; see `context/AGENTS.md`.
- `scripts/`: shared helper scripts; see `scripts/AGENTS.md`.
- `agents/`: tool-prescribed. Agent definitions in the layout of the `.agents` protocol
  (dotagentsprotocol.com, draft): one folder per agent with an `agent.md` (simple `key: value`
  frontmatter, system prompt as body) and optionally a `config.json`. Claude Code loads every
  Markdown file below `agents/` as a subagent, subfolders included, so each folder holds exactly one
  Markdown file and the folders get no index files. The coworking roles, all following
  `context/coworking.md`, each runnable as a subagent, a teammate or a session:
  - `coordinator/`: monitor and coordinator; the parent that starts the others (opus, medium).
  - `implementer/`: the only role that changes chancellor's code (opus, high).
  - `reviewer/`: read-only review against requirements, with repros (opus, high).
  - `arch-recorder/`: keeps `arch/` with chancellor itself (opus, medium).
  - `sweeper/`: read-only helper for mechanical sweeps, called by the roles (sonnet, low).
  - `planner/`: schedules tasks against the usage caps for the coordinator (sonnet, high).
- `skills/`: tool-prescribed. One folder per skill, each with a `SKILL.md`; no index files.
  - `setup-session/`: session start-up procedure.
  - `devcontainer-setup/`: set up an agent-ready dev container (VS Code, SSH, Codespaces, CI) in a
    repository; generic templates in its `assets/template/`.
- `tmp/`: gitignored. Session-bound context (hand-offs, work boards, plans, notes), one subfolder
  per task; see "Working alongside other sessions" in `/AGENTS.md`.

## Rules

- Keep files vendor-neutral and reusable across coding assistants.
- Store process guidance in `context/` and `skills/`.
- Do not duplicate repository-wide rules here; link back to `/AGENTS.md`.
