# Interview: what to ask the user

Ask only what the survey did not answer. Offer the default; group questions, at most four at a time.
Record answers in the session notes (e.g. `.agents/tmp/devcontainer-setup/notes.md`).

## Always

| Question                               | Default / why it matters                      |
| -------------------------------------- | --------------------------------------------- |
| Host OS: Windows (WSL2?), macOS, Linux | Windows needs the fixes in `pitfalls.md`.     |
| Container engine installed? Which one? | Missing: point to `host-prereqs.md`.          |
| Language toolchain and versions        | From the survey; fills the `toolchain` stage. |
| Package manager and install command    | Fills `PROJECT_SETUP` in `config.env`.        |
| Which agents in the container?         | Claude Code and Codex; others need tie-ins.   |
| Auth per agent: subscription or API?   | `subscription`, login via VS Code extension.  |
| Where else: Codespaces, CI, cloud?     | Local, Codespaces and CI hooks ship.          |

## When it applies

- **Existing `.devcontainer/` or `Dockerfile`**: keep, merge or replace? Show the differences; never
  replace silently. An existing Dockerfile used for production stays the `app` stage.
- **SSH from outside VS Code wanted?** (other editors, agents on another machine). Local SSH is
  optional, needs a forwarded port and the user's public key.
- **Unattended agent runs?** Then the outbound firewall (`AGENT_FIREWALL=1`) and API keys with
  spending limits matter.
- **Docker inside the container** (docker-outside-of-docker)? Needed for container-based MCP
  servers; it amounts to root on the host's Docker. Default: yes locally.
- **GitHub MCP servers?** Default: yes, token from VS Code's bridge, never stored.
- **Extra package registries or domains** for the firewall allowlist?
- **Docs location** for the environment page (`{{DOCS_PAGE}}`), e.g. `docs/developer/`.

## Do not ask

- Things the repo shows (language, existing hooks). State what you found instead.
- For secrets. If a step needs a token, tell the user where to put it (Codespaces secret, their
  shell, a login command); never take it into the chat or a file.
