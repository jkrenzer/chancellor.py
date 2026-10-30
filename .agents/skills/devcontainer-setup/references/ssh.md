# SSH access

SSH is the vendor-agnostic way in: any editor (VS Code Remote-SSH, JetBrains Gateway, Zed) or agent
on another machine can use the container, and an agent can start stdio MCP servers in it
(`ssh <host> <command>`).

## How it works

- Feature `ghcr.io/devcontainers/features/sshd:1`: sshd on port 2222, key login. Codespaces'
  `gh codespace ssh` needs it too.
- `containerUser: root` in `devcontainer.json`: the feature starts sshd from the entrypoint, which
  fails silently under a non-root image user with narrow sudo.
- Port 2222 is **not** published. `portsAttributes` labels it and sets `onAutoForward: ignore`; the
  user forwards it by hand in VS Code's Ports panel. The forward lives while VS Code is connected.
- Keys: the user puts public keys (whole `*.pub` lines, not fingerprints) in the workspace's
  `.ssh/authorized_keys`, which is gitignored. `setup.sh start` and the command `ssh-update-keys`
  rebuild `~/.ssh/authorized_keys` from it plus the image's own keys; deleted keys go away. Copied,
  not linked: sshd `StrictModes` rejects files on the workspace mount.
- Environment: sshd sessions get no image `ENV`, and Debian's `/etc/profile` resets PATH. The image
  writes `/etc/profile.d/00-image-env.sh`; `setup.sh` writes `~/.ssh/environment`; an sshd drop-in
  allows exactly `DEVCONTAINER_WORKSPACE,PATH,CLAUDE_CONFIG_DIR`. Add new variables in all three
  places.
- `profile.sh` moves shells that start in `$HOME` into the workspace.
- `ssh-info` prints environment, user, sshd state, key count and the commands to connect, filled in
  from the host's Docker where reachable.

## Connecting

- Local: `ssh -p <forwarded port> dev@127.0.0.1`. Use `127.0.0.1`, not `localhost`: Windows' ssh may
  try `::1`, which VS Code does not forward.
- Local without SSH: `docker exec -it -u dev <container> bash -l` (without `-u dev` you are root) or
  `devcontainer exec --workspace-folder <folder> bash -l`.
- Codespaces: `gh codespace ssh -c <name>`; `--config >> ~/.ssh/config` for a host entry.
- Agent in the workspace: `ssh -t -p <port> dev@127.0.0.1 'cd "$DEVCONTAINER_WORKSPACE" && claude'`.

## Never

- Commit `.ssh/` contents other than its README; never put private keys anywhere in the repo.
- Mount the host's `~/.ssh` into the container (Claude Code's docs advise against it); use the SSH
  agent forwarding of the Dev Containers extension instead.
- Publish 2222 with `forwardPorts`/`-p` on a shared network without telling the user.

Sources: `links.md`, sections "Features", "Codespaces", "VS Code".
