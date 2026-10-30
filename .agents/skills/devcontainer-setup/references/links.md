# External documentation

Collected 2026-10-30. "(unchecked)" means the link was not opened when this list was made.

## Spec

- [devcontainer.json reference](https://containers.dev/implementors/json_reference/): properties,
  `containerUser`/`remoteUser`, `containerEnv`/`remoteEnv`, `${localEnv:...}`, lifecycle order,
  `portsAttributes`, `updateRemoteUserUID`.
- [Features spec](https://containers.dev/implementors/features/) (unchecked).
- [devcontainers/spec](https://github.com/devcontainers/spec): spec repo, lockfile (unchecked).

## Features

- [devcontainers/features](https://github.com/devcontainers/features): read
  `src/<name>/devcontainer-feature.json` for exact options (sshd, docker-outside-of-docker,
  common-utils, github-cli).
- [docker-outside-of-docker README](https://github.com/devcontainers/features/blob/main/src/docker-outside-of-docker/README.md):
  socket path, `moby` option.

## CI

- [devcontainers/ci action docs](https://github.com/devcontainers/ci/blob/main/docs/github-action.md):
  `runCmd`, `env`, `imageName`, `cacheFrom`, `push`.
- [devcontainers/cli](https://github.com/devcontainers/cli): `build`, `up`, `exec` (unchecked).

## Codespaces

- [Codespaces with GitHub CLI](https://docs.github.com/en/codespaces/developing-in-a-codespace/using-github-codespaces-with-github-cli):
  `gh codespace ssh` needs an SSH server in the image.
- [gh codespace ssh](https://cli.github.com/manual/gh_codespace_ssh): flags incl. `--config`
  (unchecked).
- [Account secrets for Codespaces](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-your-account-specific-secrets-for-github-codespaces).

## VS Code

- [Dev Containers overview and requirements](https://code.visualstudio.com/docs/devcontainers/containers).
- [Sharing git credentials](https://code.visualstudio.com/remote/advancedcontainers/sharing-git-credentials):
  credential helper, SSH agent forwarding per OS.
- [Improve performance](https://code.visualstudio.com/remote/advancedcontainers/improve-performance):
  WSL2 filesystem, named volumes.

## Claude Code

- [Development containers](https://code.claude.com/docs/en/devcontainer): volumes plus
  `CLAUDE_CONFIG_DIR`, non-root user, firewall capabilities, headless auth.
- [MCP](https://code.claude.com/docs/en/mcp): `claude mcp add`/`add-json`, scopes, `headersHelper`,
  `.mcp.json` variable expansion.
- [Reference .devcontainer](https://github.com/anthropics/claude-code/tree/main/.devcontainer):
  `init-firewall.sh`, the origin of `root/agent-firewall`.
- [claude-code feature](https://github.com/anthropics/devcontainer-features/tree/main/src/claude-code).

## Codex

- [Codex authentication](https://learn.chatgpt.com/docs/auth): `--device-auth`, `--with-api-key`,
  `CODEX_HOME`, credential store.
- [Codex MCP](https://learn.chatgpt.com/docs/extend/mcp?surface=cli) (unchecked).
- [openai/codex](https://github.com/openai/codex): releases (binary asset names).

## GitHub MCP

- [github/github-mcp-server](https://github.com/github/github-mcp-server): remote endpoint, PAT
  header, Docker image, toolsets.

## Secrets

- [gitleaks](https://github.com/gitleaks/gitleaks): pre-commit hook `id: gitleaks`; modes `git`,
  `dir`, `stdin` since v8.19.
- [Push protection](https://docs.github.com/en/code-security/secret-scanning/introduction/about-push-protection):
  repository-level push protection is off by default.
- [detect-secrets](https://github.com/Yelp/detect-secrets): alternative (unchecked).

## Host

- [VS Code Dev Containers install](https://code.visualstudio.com/docs/devcontainers/containers#_installation).
- [Docker Desktop](https://docs.docker.com/desktop/) (unchecked).
- [Docker Engine](https://docs.docker.com/engine/install/) (unchecked).
- [WSL install](https://learn.microsoft.com/windows/wsl/install) (unchecked).
- [GitHub CLI](https://cli.github.com/) (unchecked).
