# Architecture: one image, generic scripts, per-environment hooks

Goal: the same image and scripts serve VS Code, SSH clients, Codespaces and CI, for people and
agents. Variation lives in configuration and hooks, not in parallel setups.

## Files in the target repository

| Path                                    | Role                                               |
| --------------------------------------- | -------------------------------------------------- |
| `Dockerfile`, stage `toolchain`         | Language toolchain. Project-specific.              |
| `Dockerfile`, stage `agent`             | Dev image: user `dev`, agent CLIs, helpers.        |
| `Dockerfile`, stage `app`               | Toolchain plus the project; CI, deployment.        |
| `.devcontainer/devcontainer.json`       | Features, user, volumes, ports, lifecycle.         |
| `.devcontainer/config.env`              | The only settings file: setup, auth, firewall.     |
| `.devcontainer/setup.sh`                | Entry point: `create` once, `start` each start.    |
| `.devcontainer/lib.sh`                  | Shared functions; lists the tie-in points on top.  |
| `.devcontainer/environments/<env>.sh`   | Hook per environment: `local`, `codespaces`, `ci`. |
| `.devcontainer/mcp/`, `github-token.sh` | MCP launchers; GitHub token without storing it.    |
| `.devcontainer/root/`                   | Root helpers and allowlist, baked into the image.  |
| `.devcontainer/ssh-*.sh`, `profile.sh`  | `ssh-info`, `ssh-update-keys`, shell defaults.     |
| `.ssh/README.md` (rest gitignored)      | The user's public keys for SSH logins.             |
| `.github/workflows/devcontainer.yml`    | CI in the same image.                              |
| `{{DOCS_PAGE}}`                         | User docs: access, accounts, extending.            |

Every template file and its placeholders: `../assets/INDEX.md`.

## Lifecycle

- `postCreateCommand: bash .devcontainer/setup.sh create`: repair ownership and git links,
  `PROJECT_SETUP`, install `profile.sh` and commands, hook `env_create` (MCP registration).
- `postStartCommand: bash .devcontainer/setup.sh start`: repair again, write `~/.ssh/environment`,
  rebuild `authorized_keys`, check agent logins, hook `env_start`, firewall if `AGENT_FIREWALL=1`.
- Environments without the image (a vendor's cloud agent):
  `bash .devcontainer/setup.sh create start` as their setup script; image-only steps skip
  themselves.

## Environment detection (`dev_env` in `lib.sh`)

`DEVCONTAINER_ENV` forces a name; else `CODESPACES=true` gives `codespaces`, `CI=true` gives `ci`,
the fallback is `local`. A new environment: a detection line plus a hook file with `env_create`,
`env_start`, `env_ssh_info`.

## Design decisions to keep

- Non-root `dev` as `remoteUser`; `containerUser: root` so features' entrypoints (sshd, Docker
  socket proxy) start. `dev`'s sudo allows only the two root helpers.
- Root helpers and the firewall allowlist are copied into the image, not run from the workspace, so
  an agent cannot change what runs as root.
- Logins in named volumes per workspace (`~/.claude`, `~/.codex`, `~/.config/gh`), with
  `CLAUDE_CONFIG_DIR` so `.claude.json` lands in the volume too.
- No secrets in the repo or `devcontainer.json`; `remoteEnv: ${localEnv:X}` would set empty values
  and can shadow Codespaces secrets.
- Scripts are always run as `bash <script>`: Windows checkouts lose executable bits.
- Docker CLI inside (docker-outside-of-docker) in one config for all environments.
- Outbound firewall opt-in; it is not a boundary while the Docker socket is inside.

Sources: `links.md`, sections "Spec", "Features".
