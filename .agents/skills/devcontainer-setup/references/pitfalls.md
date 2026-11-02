# Pitfalls found in practice

Each was hit while building chancellor.py's container. Check the target repo against all of them.

## Image and features

- **Floating base tags move**: `python:3.x-slim` became Debian trixie, where the
  docker-outside-of-docker feature's default Moby packages do not exist. Pin the release
  (`-slim-trixie`) and set `"moby": false` (Docker CE CLI).
- **`USER <non-root>` at the end of the image** makes the entrypoint run as that user; the sshd and
  Docker features then fail silently. Set `"containerUser": "root"` next to `remoteUser`. Plain
  `docker exec` is then root: document `-u dev`.
- **Image `ENV` does not reach login or SSH shells** (Debian's `/etc/profile` resets PATH): write
  `/etc/profile.d/00-image-env.sh` and `~/.ssh/environment`, allow the variables in sshd.
- **A window reload is not a rebuild**: the same hostname means the old container. Changes to the
  Dockerfile, features, `containerEnv` or `runArgs` need "Dev Containers: Rebuild Container".
- **Volumes for logins** must exist as directories in the image first, or they belong to root.

## Windows hosts

- **Bind mount over 9p/drvfs**: files show as root-owned or not writable for `dev`, git reports
  "dubious ownership". `root/fix-workspace` (via sudo) chowns them on every start.
- **Symlinks**: with `core.symlinks=false`, git links become plain files (Claude Code then sees no
  `.claude/skills`). `repair_links` in `lib.sh` recreates them on every start. How Git for Windows
  on the host treats links created from the container is untested.
- **No executable bits** (`core.filemode=false`): run scripts as `bash <script>`; the Dockerfile
  sets modes for root helpers; commands on PATH are wrapper scripts.
- **`localhost` resolves to `::1`** in Windows' ssh: connect to `127.0.0.1`.
- **Line endings**: suggest `.gitattributes` with `*.sh text eol=lf` if scripts fail with `\r`.

## Repository tooling

- `check-json` pre-commit hook rejects `devcontainer.json` (JSON with comments): exclude it.
- `.gitignore` patterns like `env/` hide folders; check `git check-ignore -v <path>` for every new
  path.
- Uncommitted config changes (e.g. to `.pre-commit-config.yaml`) can block other sessions' hooks;
  tell the user instead of leaving them lying around.

## Auth and access

- A set `ANTHROPIC_API_KEY` silently beats a Claude subscription login.
- Processes started over SSH get neither `~/.bashrc` nor `REMOTE_CONTAINERS_IPC`.
- Keys pasted as fingerprints into `authorized_keys` do not work; `ssh-info` warns.
- Auto-mode safety checks may block running scripts against real credentials; hand that test to the
  user instead of routing it through another session.

## Not pursued, possible later

- `.dockerignore` (the build context includes `.git`, build output).
- Remote GitHub MCP over HTTP for cloud environments instead of the Docker image.
