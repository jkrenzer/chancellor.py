# .agents

Shared, vendor-neutral agent assets live in this folder.

## Layout

- `AGENTS.md`: rules and index for this folder.
- `context/`: reusable context snippets.
- `scripts/`: helper scripts that are safe to share between tools.
- `agents/`: agent definitions, one folder per agent with an `agent.md`: the coworking roles
  (coordinator, implementer, reviewer, arch-recorder) and the `sweeper` and `planner` helpers;
  protocol in `context/coworking.md`.
- `skills/`: reusable skills, one folder each.

## Running a role

The coordinator is the parent: start it as the main agent of a session
(`claude --agent coordinator`, or the agent picker of your client). It starts the other roles as
subagents by default, as agent-team teammates when two roles must talk mid-task, or asks you to
start a separate session for long work you want to steer yourself. `context/coworking.md` describes
the three modes and when to choose which.

The coordinator watches Claude usage with `caut` and asks you for a cap per usage window (5-hour and
weekly; it proposes 75%). You can change the caps at any time. It aims for a usable milestone before
a cap is reached, and spends budget that would otherwise expire at a reset. You can ask it to pause
at any time: now, after the next minor milestone, or after the next major one. All roles then save
their state for a later resume.

## Claude symlinks

This repository uses symbolic links:

- `.claude/skills -> ../.agents/skills`
- `.claude/agents -> ../.agents/agents`

If symlinks are lost on Windows (they show up as plain files containing the target path), restore
them from PowerShell 7 in the repository root. Windows PowerShell 5.1 resolves the relative target
against the current directory and creates a wrong link.

```powershell
Remove-Item .claude\skills -Force -ErrorAction SilentlyContinue
Remove-Item .claude\agents -Force -ErrorAction SilentlyContinue
New-Item -ItemType SymbolicLink -Path .claude\skills -Target ..\.agents\skills
New-Item -ItemType SymbolicLink -Path .claude\agents -Target ..\.agents\agents
```

Alternatively let git recreate them:

```powershell
git config core.symlinks true
git checkout -- .claude/skills .claude/agents
```

Creating symbolic links on Windows needs Developer Mode or an elevated shell. Without
`core.symlinks true`, git writes plain files again on the next checkout.
