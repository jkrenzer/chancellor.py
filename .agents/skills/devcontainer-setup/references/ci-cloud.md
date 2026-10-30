# CI and cloud environments

The same `devcontainer.json` and image run everywhere; the hook in `environments/<env>.sh` adapts.
Steps needed per environment should be zero or one.

## CI (GitHub Actions)

- Template: `assets/template/.github/workflows/devcontainer.yml`, using `devcontainers/ci`. It
  builds the `agent` target and runs `runCmd` inside, after the lifecycle commands.
- The action's `env` input passes `CI=true` and `DEVCONTAINER_ENV=ci` into the container, which
  selects `environments/ci.sh`: no MCP servers, no logins, firewall off.
- Image cache: set `imageName` (with registry, e.g. `ghcr.io/<owner>/<repo>/devcontainer`),
  `cacheFrom`, `push: filter`, a `docker/login-action` step and `permissions: packages: write`. PR
  builds do not push by default.
- Other CI systems: `npm i -g @devcontainers/cli`, then
  `devcontainer up --workspace-folder . --remote-env CI=true` and
  `devcontainer exec --workspace-folder . <checks>`.
- Status: the `ci` hook and workflow are new in this skill and were not run in chancellor.py. Tell
  the user and verify on the first CI run.

## GitHub Codespaces

- Uses `devcontainer.json` and the Dockerfile directly. Detected by `CODESPACES=true`.
- Secrets: repository Codespaces secrets become environment variables (`ANTHROPIC_API_KEY`,
  `OPENAI_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `GH_TOKEN`). User secrets are not visible to
  `onCreateCommand`; this setup reads them in `postCreateCommand`/`postStartCommand` only.
- SSH: `gh codespace ssh` (needs the sshd feature). Docker works on the codespace's own VM; the hook
  registers no container-based MCP servers by default.
- Unverified in chancellor.py: sshd with non-root `remoteUser` in Codespaces, and whether the
  connection survives `AGENT_FIREWALL=1`.

## Vendor clouds and other hosts

- Claude Code on the web, Codex cloud and similar run their own base images: use
  `bash .devcontainer/setup.sh create start` as their setup script; image-only steps skip
  themselves.
- Own VMs: add an environment (detection line in `dev_env`, a hook file). Idea not yet built: a
  Tailscale feature for inbound-free SSH.

## Unattended agent runs

```bash
devcontainer up --workspace-folder . --remote-env AGENT_FIREWALL=1
devcontainer exec --workspace-folder . claude -p "<task>" --dangerously-skip-permissions
```

The firewall allows DNS, the Docker host network, GitHub's ranges and `root/firewall-allow.txt`;
`dev` can switch it on, not off. It is not a security boundary while the Docker socket is in the
container. Tell the user that API keys bill per token: separate key, spending limit, rotation.

Sources: `links.md`, sections "CI", "Codespaces", "Claude Code".
