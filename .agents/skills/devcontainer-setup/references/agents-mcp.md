# Agents, logins, MCP servers and the GitHub token

## Agent CLIs

- Installed in the `agent` stage: Claude Code via its install script with a pinned start version (it
  self-updates), Codex as a release binary (pinned, no self-update). Look up current versions.
- Non-root user: Claude Code refuses `--dangerously-skip-permissions` as root.
- A new agent: install it in `agent`, a volume for its config directory in `devcontainer.json`,
  create that directory in the image (so the volume belongs to `dev`), extend `register_mcp` and
  `configure_auth` in `lib.sh`, add `<AGENT>_AUTH` to `config.env` defaulting to `subscription`.

## Accounts (`config.env`)

- `CLAUDE_AUTH`, `CODEX_AUTH`: `subscription` (default; log in once via the VS Code extension or
  `claude` → `/login`, `codex login --device-auth`) or `api` (keys from the environment or
  Codespaces secrets; setup logs Codex in with
  `printenv OPENAI_API_KEY | codex login --with-api-key`).
- A set `ANTHROPIC_API_KEY` beats a subscription login, also in the extension. Setup warns;
  `profile.sh` unsets it in interactive shells in subscription mode.
- Headless Claude on a subscription: `CLAUDE_CODE_OAUTH_TOKEN` from `claude setup-token`, as a
  secret, never in a file.
- Logins persist in per-workspace volumes; they survive rebuilds, not volume deletion.

## MCP servers

- Servers that run anywhere: the repo's `.mcp.json` (project scope).
- Servers needing Docker or host capabilities: a launcher in `.devcontainer/mcp/` and a
  `register_mcp` call (stdio, Claude Code and Codex, user scope) in the hooks that want them.
- Remote HTTP servers with a dynamic token: `register_mcp_http` (Claude Code `headersHelper`; a
  command printing a JSON object of headers, run on each connect, 10 s timeout). Codex has no
  equivalent. An `Authorization` header from the helper disables Claude Code's OAuth fallback.

## GitHub token without storing it

`github-token.sh` prints the first of `GITHUB_PERSONAL_ACCESS_TOKEN`, `GH_TOKEN`, `gh auth token`,
then VS Code's git credential bridge. The bridge is the credential helper the Dev Containers
extension installs; it works in any process, SSH sessions included, once `REMOTE_CONTAINERS_IPC`
points at the newest `/tmp/vscode-remote-containers-ipc-*.sock`, and only while a VS Code window is
attached. Setup never writes the token anywhere.

- `github` (stdio, Docker image `ghcr.io/github/github-mcp-server`) via `mcp/github.sh`: Claude Code
  and Codex, local only.
- `github-remote` (HTTP, `https://api.githubcopilot.com/mcp/`) via `mcp/github-headers.sh`.
- A plugin's MCP server with a static `${VAR}` header cannot be fed this way; register an own server
  instead and suggest disabling the plugin's server for the repo.
- Never print, log or echo the token; mask it in diagnostics (`gho_…`).

Sources: `links.md`, sections "Claude Code", "Codex", "GitHub MCP".
