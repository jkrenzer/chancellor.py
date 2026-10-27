# .agents

Shared, vendor-neutral agent assets live in this folder.

## Layout

- `AGENTS.md`: rules and index for this folder.
- `context/`: reusable context snippets.
- `scripts/`: helper scripts that are safe to share between tools.
- `agents/`: reserved for agent-specific definitions.
- `skills/`: reusable skills; currently includes `setup-session`.

## Claude symlinks

This repository uses symbolic links:

- `.claude/skills -> ../.agents/skills`
- `.claude/agents -> ../.agents/agents`

If symlinks are lost on Windows, restore them from PowerShell in repository root:

```powershell
Remove-Item .claude\skills -Force -ErrorAction SilentlyContinue
Remove-Item .claude\agents -Force -ErrorAction SilentlyContinue
New-Item -ItemType SymbolicLink -Path .claude\skills -Target ..\.agents\skills
New-Item -ItemType SymbolicLink -Path .claude\agents -Target ..\.agents\agents
```
