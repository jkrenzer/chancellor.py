# Verify the setup

Static checks you run; container checks after the user rebuilds. Report each as passed, failed or
not run. Never claim a check you did not run.

## Before the build (you)

```bash
bash -n .devcontainer/*.sh .devcontainer/environments/*.sh .devcontainer/mcp/*.sh
shellcheck .devcontainer/*.sh .devcontainer/environments/*.sh .devcontainer/mcp/*.sh
rg -n '\{\{[A-Z_]+\}\}' Dockerfile .devcontainer .github <docs page>  # must print nothing
git check-ignore -v .devcontainer/environments/local.sh   # must print nothing
```

Plus the secret scan in `safety.md`. If Docker works where you run:
`devcontainer build --workspace-folder .` (VS Code bundles the CLI; `npm i -g @devcontainers/cli`
otherwise).

## After the rebuild (in the container)

1. New container: hostname changed; `ps -o user= -p 1` prints `root`; `id -un` prints `dev`.
2. Setup ran: no errors in the creation log; `ls -l .claude/skills` (if the repo has links) shows
   links; `git status` is clean apart from intended changes.
3. Toolchain: the project's checks run (the command the CI workflow runs).
4. Agents: `claude --version`, `codex --version`; logins per `CLAUDE_AUTH`/`CODEX_AUTH`.
5. Docker: `docker ps` works (if the feature is on).
6. SSH: `pgrep -x sshd`; `ssh-info` shows the user, port 2222, key count.
7. MCP: `claude mcp list` shows `github` and `github-remote` (local); connecting `github-remote`
   needs a VS Code window attached.

## From the host (the user)

- Forward 2222 in the Ports panel, put their `*.pub` line in `.ssh/authorized_keys`, run
  `ssh-update-keys` in the container, then:
  `ssh -p <port> dev@127.0.0.1 'echo $DEVCONTAINER_WORKSPACE; claude --version'`.
- Optional: `git status` on the host after the first start (links created in the container).

## Later environments

- Codespaces: create one, `gh codespace ssh -c <name>`, `ssh-info` prints `codespaces`.
- CI: the first run of `.github/workflows/devcontainer.yml` passes and `setup.sh` logs
  `environment: ci`.

Record results in the session notes and, when done, tell the user which items remain unverified.
