# Development environments

One image and one set of scripts serve every place chancellor is developed in: a dev container on a
workstation, GitHub Codespaces, and later other hosts. People and coding agents (Claude Code, Codex,
others) use the same environment, interactively or unattended.

## Parts

| Path                                   | Role                                             |
| -------------------------------------- | ------------------------------------------------ |
| `Dockerfile`, stage `toolchain`        | Language toolchain; the project-specific part.   |
| `Dockerfile`, stage `agent`            | Dev image: user `dev`, agent CLIs, helper tools. |
| `.devcontainer/devcontainer.json`      | Features, volumes, lifecycle commands.           |
| `.devcontainer/config.env`             | Project settings: setup, agent auth, firewall.   |
| `.devcontainer/setup.sh`               | Entry point: `create` once, `start` each start.  |
| `.devcontainer/lib.sh`                 | Shared functions; lists the tie-in points.       |
| `.devcontainer/environments/<name>.sh` | Per-environment hook: MCP servers, firewall.     |
| `.devcontainer/mcp/`                   | Launchers for MCP servers the hooks register.    |
| `.devcontainer/github-token.sh`        | Finds a GitHub token, also via VS Code's bridge. |
| `.devcontainer/root/`                  | Root helpers and allowlist, baked into image.    |
| `.devcontainer/profile.sh`             | Interactive shells: auth choice, start folder.   |
| `.devcontainer/ssh-info.sh`            | The `ssh-info` command: how to reach the box.    |

`setup.sh create` repairs file ownership and git symbolic links, runs `PROJECT_SETUP` and the
environment hook's `env_create`. `setup.sh start` repairs again, checks the agent logins, runs
`env_start` and switches the firewall on if `AGENT_FIREWALL=1`.

## Access

SSH is the vendor-agnostic way in. Any editor or agent that works over SSH can use the container,
without either side knowing about the other.

- Codespaces: `gh codespace ssh`, or `gh codespace ssh --config >> ~/.ssh/config` for a host entry
  that VS Code Remote-SSH, JetBrains Gateway, Zed or a terminal can use.
- Local: VS Code attaches to the dev container directly; other tools use `docker exec -u dev` or
  `devcontainer exec`. The `sshd` feature runs in the container, but its port is not published. The
  container's main process runs as root, so `docker exec` without `-u dev` gives a root shell.
- Local SSH, optional: forward port 2222 in VS Code's Ports panel (it is labelled "SSH: user dev, …"
  and never forwarded automatically), add your public key to `~/.ssh/authorized_keys` in the
  container, and connect to the local port the panel shows. The forward lasts while VS Code is
  connected.
- MCP from outside: an agent on another machine can start a server inside the container as a stdio
  server, e.g. `ssh <host> chancellor serve`.

Run `ssh-info` in the container to see how to reach it: the environment, user, sshd state and port,
authorized keys, and the commands for this environment, filled in as far as the container can tell
(locally the container name and host folder come from the host's Docker).

`DEVCONTAINER_WORKSPACE` holds the workspace path everywhere in the container, SSH sessions
included, e.g. for an agent that needs a working directory: `cd "$DEVCONTAINER_WORKSPACE"`.
Interactive shells that start in the home directory, SSH logins among them, change into it. SSH
sessions get it from `~/.ssh/environment`, which `setup.sh start` writes; sshd accepts only the
variables named in `/etc/ssh/sshd_config.d/devcontainer.conf` in the image.

GitHub access for tools in the container comes from `.devcontainer/github-token.sh`. It takes the
first of `GITHUB_PERSONAL_ACCESS_TOKEN`, `GH_TOKEN`, `gh auth token` and VS Code's git credential
bridge. The bridge also serves SSH sessions, but only while a VS Code window is attached to the
container. Setup never stores the token it finds, so without an attached window, a `gh` login or a
token variable, GitHub tools have no token.

Locally two GitHub MCP servers use it: `github`, GitHub's server in Docker on stdio, for Claude Code
and Codex; and `github-remote`, GitHub's hosted server over HTTP, for Claude Code, whose
`headersHelper` (`.devcontainer/mcp/github-headers.sh`) fetches the token on each connect.

## Agent accounts

`CLAUDE_AUTH` and `CODEX_AUTH` in `config.env` choose, per repository, whether each agent bills to
an API key (`api`) or a subscription (`subscription`). The default is `subscription` for every
agent, including agents added later: in VS Code people log in through the agents' extensions. Like
every value in `config.env`, the setting can be overridden from the environment, e.g.
`CLAUDE_AUTH=api` for an unattended run that bills to a key.

- API keys: set `ANTHROPIC_API_KEY` and `OPENAI_API_KEY` as Codespaces secrets of the repository, or
  in the environment of an unattended run. Setup logs Codex in with its key.
- Subscriptions: log in once inside the container, through the agent's VS Code extension or its CLI
  (`claude`, then `/login`; `codex login --device-auth`), or provide `CLAUDE_CODE_OAUTH_TOKEN` from
  `claude setup-token`.
- Logins persist in per-workspace volumes for `~/.claude`, `~/.codex` and `~/.config/gh`.

```{warning}
API keys bill per token. An unattended run that loops costs money until it is stopped. Give each
key its own Anthropic workspace or OpenAI project with a spending limit, scope Codespaces secrets
to this repository, and rotate keys.
```

A set `ANTHROPIC_API_KEY` takes precedence over a Claude subscription login, also in the VS Code
extension. In subscription mode setup warns about a set key, and `profile.sh` unsets it in
interactive shells.

## Unattended runs

Unattended agents run in the same image with the outbound firewall on:

```bash
devcontainer up --workspace-folder . --remote-env AGENT_FIREWALL=1
devcontainer exec --workspace-folder . claude -p "<task>" --dangerously-skip-permissions
devcontainer exec --workspace-folder . \
  codex exec --dangerously-bypass-approvals-and-sandbox "<task>"
```

The firewall allows DNS, the Docker host network, GitHub's address ranges and the domains in
`.devcontainer/root/firewall-allow.txt`. The dev user can switch it on through `sudo` but not off.
Codex's own sandbox does not work reliably inside a container, so the container and its firewall are
the sandbox.

```{warning}
The firewall guards against accidental or injected data exfiltration; it is not a security
boundary while the Docker socket is in the container (feature `docker-outside-of-docker`), since
a container started through it is not subject to the firewall.
```

## Environments

| Environment  | Detected by       | Container-based MCP servers | Firewall default |
| ------------ | ----------------- | --------------------------- | ---------------- |
| `local`      | fallback          | registered (Docker on host) | off              |
| `codespaces` | `CODESPACES=true` | not registered              | off              |

`DEVCONTAINER_ENV=<name>` forces an environment where detection is not possible.

## Extending the setup

The top of `.devcontainer/lib.sh` lists every tie-in point; in short:

- New environment: detect it in `dev_env` in `lib.sh`, add `.devcontainer/environments/<name>.sh`
  with `env_create`, `env_start` and `env_ssh_info` (what `ssh-info` prints there), and add a row to
  the table above.
- Environment without our image (a vendor's cloud agent with its own base image): use
  `bash .devcontainer/setup.sh create start` as its setup script; steps that need the image are
  skipped.
- New agent CLI: install it in the Dockerfile's `agent` stage, add a volume for its config directory
  in `devcontainer.json`, and extend `register_mcp` and `configure_auth` in `lib.sh`.
- New MCP server: servers that run anywhere go into `.mcp.json`; servers that need Docker or other
  host capabilities get a launcher in `.devcontainer/mcp/` and a `register_mcp` call in the hooks of
  the environments that want them.
- New allowed domain: add it to `.devcontainer/root/firewall-allow.txt` and rebuild.

## File ownership and links

The dev user does not own files that a Windows or macOS bind mount or a root process created. On
every start, `fix-workspace` (root, through `sudo`) gives the dev user ownership of such files in
the workspace. Git symbolic links that a checkout or copy turned into plain files, like
`.claude/agents`, are recreated at the same time.
