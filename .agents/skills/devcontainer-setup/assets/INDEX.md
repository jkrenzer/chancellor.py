# Template index

Files under `template/` keep their target paths. Copy, then replace every `{{PLACEHOLDER}}`
(`rg -n '\{\{[A-Z_]+\}\}'` finds them; `{{.Name}}`-style Docker formats in `local.sh` are code, not
placeholders). Merge with existing files; do not overwrite them unasked.

## Placeholders

| Placeholder               | Where                      | Fill with                             |
| ------------------------- | -------------------------- | ------------------------------------- |
| `{{PROJECT_NAME}}`        | `devcontainer.json`        | Container display name.               |
| `{{EXTENSIONS}}`          | `devcontainer.json`        | Language extensions; drop comment.    |
| `{{DOCS_PAGE}}`           | `devcontainer.json`, `lib` | Path of the docs page below.          |
| `{{PROJECT_SETUP}}`       | `config.env`               | Install command run on creation.      |
| `{{TOOLCHAIN}}`           | `Dockerfile`               | Base image and toolchain.             |
| `{{TOOLCHAIN_OWNERSHIP}}` | `Dockerfile`               | chown of shared tool dirs, or delete. |
| `{{AGENT_VERSIONS}}`      | `Dockerfile`               | Current Claude Code, Codex versions.  |
| `{{APP}}`                 | `Dockerfile`               | Project install for the `app` stage.  |
| `{{PACKAGE_INDEXES}}`     | `firewall-allow.txt`       | The language's registry domains.      |
| `{{CI_ACTION_VERSION}}`   | `devcontainer.yml`         | Current `devcontainers/ci` tag.       |
| `{{CI_COMMAND}}`          | `devcontainer.yml`         | The project's checks.                 |

## Files

| Template path                              | Kind    | Notes                                    |
| ------------------------------------------ | ------- | ---------------------------------------- |
| `Dockerfile`                               | adapt   | Stage names are a contract.              |
| `.devcontainer/devcontainer.json`          | adapt   | JSON with comments.                      |
| `.devcontainer/config.env`                 | adapt   | The only settings file; no secrets.      |
| `.devcontainer/lib.sh`                     | generic | Tie-in points listed at the top.         |
| `.devcontainer/setup.sh`                   | generic | `create` / `start` phases.               |
| `.devcontainer/profile.sh`                 | generic | Sourced from `~/.bashrc`.                |
| `.devcontainer/ssh-info.sh`                | generic | Command `ssh-info`.                      |
| `.devcontainer/ssh-update-keys.sh`         | generic | Command `ssh-update-keys`.               |
| `.devcontainer/github-token.sh`            | generic | Never stores or prints tokens.           |
| `.devcontainer/environments/local.sh`      | generic | MCP registration via Docker.             |
| `.devcontainer/environments/codespaces.sh` | generic | `gh codespace ssh` hints.                |
| `.devcontainer/environments/ci.sh`         | generic | New, untested in a real CI run.          |
| `.devcontainer/mcp/github.sh`              | generic | Stdio GitHub MCP in Docker.              |
| `.devcontainer/mcp/github-headers.sh`      | generic | `headersHelper` for `github-remote`.     |
| `.devcontainer/root/agent-firewall`        | generic | Root; baked into the image.              |
| `.devcontainer/root/fix-workspace`         | generic | Root; only below `/workspaces`.          |
| `.devcontainer/root/firewall-allow.txt`    | adapt   | Add registries and project domains.      |
| `.ssh/README.md`                           | generic | Folder is gitignored except this file.   |
| `.github/workflows/devcontainer.yml`       | adapt   | CI in the same image.                    |
| `docs/environments.md`                     | adapt   | Place at `{{DOCS_PAGE}}`; MyST/Markdown. |

Also needed, not as files: the `.gitignore` lines in `../references/safety.md`, and, if the repo
uses pre-commit's `check-json`, an exclude for `devcontainer.json`.

`devcontainer-lock.json` is not a template. If the Dev Containers tooling writes one on the first
build, propose committing it, so feature versions stay pinned.
