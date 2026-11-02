# Serena MCP server

Serena (`serena-agent` on PyPI) gives agents symbol-level code navigation and editing through
language servers. Proven in chancellor.py with Serena 2.1, Poetry 2.5 and Python projects; adapt the
package-manager steps for others.

## Recipe

1. **Never install Serena into the project's environment.** It pins exact versions (`pyyaml==6.0.2`
   in 2.1) that collide with the project's dependencies. Run it with `uvx`, which gives it an
   isolated, cached environment of its own.
2. **Provide uv through the project**, in an optional dependency group, so every developer gets the
   same tool: `agents = ["uv>=0.9,<1"]` under `[dependency-groups]`, plus
   `[tool.poetry.group.agents] optional = true`. Add `agents` to the dev container's install command
   (`PROJECT_SETUP` in `config.env`: `poetry install --with dev,docs,agents ...`).
3. **Wrap the start command in a task**, so agents and humans start Serena the same way. Poe task:
   `uvx --from 'serena-agent>=2.1.0,<3' serena start-mcp-server --context ${context} --project ${POE_ROOT}`,
   with an argument `context` defaulting to `claude-code`.
4. **Point pyright at the project venv.** Serena's pyright runs inside uvx and otherwise sees only
   uvx's Python: every third-party import shows as unresolved. A small idempotent task writes
   `venvPath`/`venv` for `sys.prefix` into a gitignored `pyrightconfig.json`; make it a `deps` of
   the Serena task. Template: chancellor.py's `.agents/scripts/pyright_config.py`.
5. **Register it per agent, with the matching context** (`ide-assistant` is deprecated):
   - Claude Code: `.mcp.json`, `"serena": {"command": "poetry", "args": ["do", "-q", "serena"]}`.
   - VS Code: `.vscode/mcp.json`, `"type": "stdio"`, args plus `--context vscode`,
     `"cwd": "${workspaceFolder}"`.
   - Codex (reads no `.mcp.json`): in `register_image_mcp` in `lib.sh`,
     `codex mcp add serena -- poetry -C "$WORKSPACE_DIR" do -q serena --context codex`.
6. **Image** (`toolchain` stage): install `libatomic1`. Pyright downloads its own Node.js, which
   fails without `libatomic.so.1` on slim Debian images.
7. **Gitignore** `.serena/` (project config and memories) and `pyrightconfig.json`.
8. **Firewall** (`AGENT_FIREWALL=1`): first start downloads from PyPI, `github.com` (uv's Pythons)
   and `nodejs.org`. Propose these allowlist entries to the user; do not edit the allowlist yourself
   without their consent.

## Pitfalls

- **stdout is the MCP protocol.** Run tasks quietly (`poetry do -q`) and send every message of the
  pre-task to stderr, or the client drops the connection.
- **Poetry project plugins** (`requires-plugins`, e.g. poethepoet for `poetry do`) install only
  while the user can write Poetry's own venv. With a root-owned `$POETRY_HOME`, Poetry 2.5.1 falls
  back to a user install with a garbled path and `poetry do` does not exist. Fix in the `agent`
  stage: `chown -R dev:dev "$VIRTUAL_ENV" "$POETRY_HOME"`.
- **First start is slow**: uv fetches Serena, a Python for pyright, pyright and Node.js. A client
  timeout on first connect usually just needs a reconnect.
- A failing `PROJECT_SETUP` (e.g. stale `poetry.lock`) leaves the venv without uv; Serena then fails
  with "Could not find 'uvx' or 'uv' in PATH".

## Verify

After the user rebuilds and reconnects the MCP server:

- Serena's tool list loads; call its initial instructions.
- A symbol overview of one source file returns its classes and functions.
- References of a widely used symbol span several files.
- Diagnostics of a file importing third-party packages are empty.
- Serena's log shows no deprecated-context warning and pyright started via the venv's `uvx`.

Sources: `links.md`, section "Serena".
