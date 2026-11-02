# Host prerequisites: what the user installs

The user installs these on their computer; you explain and check, you never run installers on their
host. Ask which OS first. Links: `links.md`, section "Host".

## Needed

1. **Container engine**, one of:
   - Windows: Docker Desktop with the WSL2 backend (install WSL first: `wsl --install` in an
     administrator PowerShell, then reboot). In Docker Desktop: Settings > Resources > WSL
     integration, enable the distro. Windows containers and Docker Toolbox do not work.
   - macOS: Docker Desktop (Apple silicon or Intel build).
   - Linux: Docker Engine (CE) from Docker's apt/dnf repository, not the Ubuntu snap. Then
     `sudo usermod -aG docker $USER` and log out and in.
   - Podman may work but is not supported by VS Code; mention it only if the user asks.
2. **VS Code** and the **Dev Containers** extension (`ms-vscode-remote.remote-containers`).
3. **Git**, configured with `user.name` and `user.email`; the extension copies `.gitconfig` in.

## Optional

- **OpenSSH client**, for SSH into the container: built into macOS and Linux; on Windows an optional
  feature (Settings > System > Optional features > OpenSSH Client), usually present.
- **SSH agent**, if git over SSH should work in the container: Windows: start the `ssh-agent`
  service (administrator PowerShell:
  `Set-Service ssh-agent -StartupType Automatic; Start-Service ssh-agent`), then `ssh-add`. Linux:
  `eval "$(ssh-agent -s)"; ssh-add`.
- **GitHub CLI** (`gh`) on the host, for `gh codespace ssh`.
- **devcontainer CLI** (`npm i -g @devcontainers/cli`, needs Node), for builds outside VS Code.

## Checks the user can run

```bash
docker version
docker run --rm hello-world
git config --get user.email
ssh -V
```

On Windows run them in PowerShell; `docker version` must show a server, not only a client.

## Windows: where the checkout lives

A checkout on the Windows drive (`C:\...`) works but is slow and brings the ownership and symlink
problems in `pitfalls.md`. Faster: clone inside WSL (`\\wsl$\<distro>\home\...`) and open it from
there. Ask the user which they use; do not move their checkout.
