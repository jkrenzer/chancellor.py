---
name: devcontainer-setup
description: 'Create or adapt an agent-ready dev container: VS Code, SSH, Codespaces, CI.'
---

# Dev container setup

Use when asked to create, add, adapt or repair a dev container or `devcontainer.json`, SSH access
into a container, or a container for agents, Codespaces or CI, with or without an existing
`.devcontainer/`.

Sets up the dev container proven in chancellor.py: a Dockerfile with stages `toolchain`, `agent` and
`app`; generic scripts in `.devcontainer/`; per-environment hooks (local, Codespaces, CI); SSH
access; agent logins that survive rebuilds; GitHub token without stored secrets.

## Hard rules

1. **Never stage, commit or push** without the user's clear, specific consent for exactly that step.
   Show `git status` and the file list first. Consent for one commit is not consent for the next,
   nor for a push.
2. **Secrets stop the work.** If a key, token, password or private key could reach git (a file, a
   diff, a commit message, a log), stop, tell the user what and where, and fix it together.
   Publishing it needs the user's explicit order after you told them exactly what goes out.
   Procedure: `references/safety.md`.
3. **Ask, do not guess**, where the answer changes the result: language, base image, agents, auth
   mode, what to keep of an existing setup. Questions: `references/interview.md`.
4. **Do not overwrite** existing files (Dockerfile, devcontainer.json, .gitignore, workflows)
   without showing the user the change. Merge instead.
5. Software on the user's computer is theirs to install. Tell them how, per OS, when they are
   unsure: `references/host-prereqs.md`. Never run installers on their host yourself.

## Workflow

1. **Survey** the repo: language and package manager, existing `.devcontainer/`, `Dockerfile`,
   `.gitignore`, `.github/workflows/`, `AGENTS.md`/`CLAUDE.md`, `git status`. Note untracked or
   changed files that are not yours and leave them alone.
2. **Interview** the user: `references/interview.md`. Record the answers in the session notes.
3. **Host check**: what the user's computer needs, `references/host-prereqs.md`.
4. **Plan** the files: `references/architecture.md` and the template index `assets/INDEX.md`. Show
   the user the list of files you will create or change before writing.
5. **Write** from `assets/template/`. Replace every `{{PLACEHOLDER}}` (list in `assets/INDEX.md`).
   Adapt, do not copy blindly:
   - SSH: `references/ssh.md`
   - agents, logins, MCP, GitHub token: `references/agents-mcp.md`
   - Serena MCP server (semantic code tools): `references/serena.md`
   - CI and cloud: `references/ci-cloud.md`
6. **Check before anyone builds**: `references/pitfalls.md` against the repo (Windows host,
   symlinks, .gitignore patterns, base image tags), and the secret scan in `references/safety.md`.
7. **Verify** with the user: `references/verify.md`. The user rebuilds the container; you check
   inside. Report what was verified and what was not.
8. **Hand over**: tell the user what changed, what is unverified, and propose a commit message
   (Conventional Commits). Commit only on their explicit yes (rule 1).

## Where things are

- `references/`: one short guide per topic; each ends with links to the sources.
- `references/links.md`: external documentation by topic.
- `assets/INDEX.md`: every template file, its role and its placeholders.
- `assets/template/`: the files to copy into the repository, paths as in the target.

Origin: chancellor.py's `.devcontainer/` and `docs/developer/environments.md` (2026-10). Its history
of findings is summarised in `references/pitfalls.md`.
