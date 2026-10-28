# .agents

Shared, vendor-neutral agent assets live in this folder.

## Layout

- `AGENTS.md`: rules and index for this folder.
- `context/`: reusable context snippets.
- `scripts/`: helper scripts that are safe to share between tools.
- `agents/`: subagent definitions; currently empty.
- `skills/`: reusable skills, one folder each; currently `setup-session`.

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
