# .agents folder guide

## Purpose

This folder contains cross-tool agent metadata, context, scripts, and skills.

## Index

- `README.md`: human-facing overview, including the Claude symlink restore procedure.
- `context/`: reusable context snippets; see `context/AGENTS.md`.
- `scripts/`: shared helper scripts; see `scripts/AGENTS.md`.
- `agents/`: tool-prescribed. Subagent definitions, one Markdown file each; every Markdown file here
  is loaded as a subagent, so no index files. Empty apart from `.gitkeep`.
- `skills/`: tool-prescribed. One folder per skill, each with a `SKILL.md`; no index files.
  - `setup-session/`: session start-up procedure.
- `tmp/`: gitignored. Session-bound context (hand-offs, work boards, plans, notes), one subfolder
  per task; see "Working alongside other sessions" in `/AGENTS.md`.

## Rules

- Keep files vendor-neutral and reusable across coding assistants.
- Store process guidance in `context/` and `skills/`.
- Do not duplicate repository-wide rules here; link back to `/AGENTS.md`.
