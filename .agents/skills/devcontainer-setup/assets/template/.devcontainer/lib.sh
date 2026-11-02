# shellcheck shell=bash
# Helpers shared by the dev container scripts. Source it; do not run it.
#
# Tie-in points, also listed in the developer docs ({{DOCS_PAGE}}):
# - New environment (cloud VM, CI runner, another hosted IDE): detect it in dev_env below and
#   add .devcontainer/environments/<name>.sh with env_create, env_start and env_ssh_info.
# - New agent CLI: install it in the Dockerfile's agent stage, persist its config directory in
#   devcontainer.json "mounts", and add it to register_mcp and configure_auth below, with an
#   <AGENT>_AUTH setting in config.env that defaults to subscription.
# - New MCP server: register it with register_mcp in the hook of each environment that wants it;
#   servers every environment can run go into the committed .mcp.json instead.
# - Project settings: .devcontainer/config.env.

DEVCONTAINER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_DIR="$(dirname "$DEVCONTAINER_DIR")"
# shellcheck source=config.env
. "$DEVCONTAINER_DIR/config.env"

log() { printf '[devcontainer] %s\n' "$*" >&2; }

# Prints the name of the environment we run in; it selects .devcontainer/environments/<name>.sh.
# DEVCONTAINER_ENV forces a name, for environments without a reliable marker.
dev_env() {
  if [ -n "${DEVCONTAINER_ENV:-}" ]; then
    echo "$DEVCONTAINER_ENV"
  elif [ "${CODESPACES:-}" = true ]; then
    echo codespaces
  elif [ "${CI:-}" = true ]; then
    echo ci
  # New environments: detect them here, above the local fallback.
  else
    echo local
  fi
}

# Gives the dev user ownership of workspace files it cannot write. Bind mounts from Windows and
# macOS hosts, and files a root process wrote, leave such files behind. No-op outside our image.
repair_ownership() {
  [ -x /usr/local/sbin/fix-workspace ] || return 0
  sudo -n /usr/local/sbin/fix-workspace "$WORKSPACE_DIR"
  git -C "$WORKSPACE_DIR" rev-parse --git-dir >/dev/null 2>&1 \
    || git config --global --add safe.directory "$WORKSPACE_DIR"
}

# Recreates symbolic links that git tracks but the filesystem lost: a checkout with
# core.symlinks=false, or a copy across filesystems, turns them into plain files holding the
# target path. Directories in a link's place are reported, not deleted.
repair_links() {
  git -C "$WORKSPACE_DIR" rev-parse --git-dir >/dev/null 2>&1 || return 0
  local rel path target
  while IFS= read -r rel; do
    path="$WORKSPACE_DIR/$rel"
    target="$(git -C "$WORKSPACE_DIR" cat-file blob ":$rel")"
    if [ -L "$path" ] && [ "$(readlink "$path")" = "$target" ]; then
      continue
    elif [ -d "$path" ] && [ ! -L "$path" ]; then
      log "not repaired, a directory stands where git has a link: $rel"
      continue
    fi
    rm -f -- "$path"
    ln -s -- "$target" "$path"
    log "restored link $rel -> $target"
  done < <(git -C "$WORKSPACE_DIR" ls-files -s | sed -n 's/^120000 [0-9a-f]* [0-9]\t//p')
}

# Registers a stdio MCP server, for the dev user, with every agent CLI installed here.
# Usage: register_mcp <name> <command> [args...]
register_mcp() {
  local name=$1
  shift
  if command -v claude >/dev/null; then
    claude mcp remove --scope user "$name" >/dev/null 2>&1 || true
    claude mcp add --scope user "$name" -- "$@" >/dev/null && log "MCP $name: registered for claude"
  fi
  if command -v codex >/dev/null; then
    codex mcp remove "$name" >/dev/null 2>&1 || true
    codex mcp add "$name" -- "$@" >/dev/null && log "MCP $name: registered for codex"
  fi
}

# Registers a remote HTTP MCP server, for the dev user, whose request headers come from a helper
# command run before connecting (Claude Code's headersHelper). Codex has no such hook and keeps
# the stdio servers. Usage: register_mcp_http <name> <url> <helper command>
register_mcp_http() {
  local name=$1 url=$2 helper=$3
  command -v claude >/dev/null || return 0
  claude mcp remove --scope user "$name" >/dev/null 2>&1 || true
  claude mcp add-json --scope user "$name" \
    "$(printf '{"type":"http","url":"%s","headersHelper":"%s"}' "$url" "$helper")" >/dev/null \
    && log "MCP $name: registered for claude (HTTP)"
}

# Checks each agent CLI's login against CLAUDE_AUTH / CODEX_AUTH from config.env, and logs Codex
# in with its API key in api mode. Never prints secrets.
configure_auth() {
  case "$CLAUDE_AUTH" in
    api)
      [ -n "${ANTHROPIC_API_KEY:-}" ] \
        || log "claude: CLAUDE_AUTH=api, but ANTHROPIC_API_KEY is not set" ;;
    subscription)
      [ -z "${ANTHROPIC_API_KEY:-}" ] \
        || log "claude: CLAUDE_AUTH=subscription, but ANTHROPIC_API_KEY is set and bills instead" ;;
    *) log "claude: unknown CLAUDE_AUTH '$CLAUDE_AUTH'" ;;
  esac
  command -v codex >/dev/null || return 0
  case "$CODEX_AUTH" in
    api)
      if [ -n "${OPENAI_API_KEY:-}" ]; then
        printenv OPENAI_API_KEY | codex login --with-api-key >/dev/null \
          && log "codex: logged in with API key"
      else
        log "codex: CODEX_AUTH=api, but OPENAI_API_KEY is not set"
      fi ;;
    subscription)
      codex login status >/dev/null 2>&1 \
        || log "codex: not logged in; run 'codex login --device-auth' once" ;;
    *) log "codex: unknown CODEX_AUTH '$CODEX_AUTH'" ;;
  esac
}

# Puts the user-facing scripts on PATH. Wrappers instead of links: a Windows checkout does not
# keep executable bits.
install_commands() {
  mkdir -p ~/.local/bin
  printf '#!/bin/sh\nexec bash "%s" "$@"\n' "$DEVCONTAINER_DIR/ssh-info.sh" >~/.local/bin/ssh-info
  chmod 0755 ~/.local/bin/ssh-info
  printf '#!/bin/sh\nexec bash "%s" "$@"\n' "$DEVCONTAINER_DIR/ssh-update-keys.sh" \
    >~/.local/bin/ssh-update-keys
  chmod 0755 ~/.local/bin/ssh-update-keys
}

# SSH sessions get no container environment; sshd reads ~/.ssh/environment instead (allowed
# variables: /etc/ssh/sshd_config.d/devcontainer.conf in the image). It gets the image's PATH
# and other variables from /etc/profile.d/00-image-env.sh, so commands run over SSH find the
# tools. Not in a volume, so it is rewritten on every start.
install_ssh_env() {
  mkdir -p ~/.ssh
  {
    [ -f /etc/profile.d/00-image-env.sh ] \
      && sed -n 's/^export \([A-Za-z_][A-Za-z0-9_]*\)="\(.*\)"$/\1=\2/p' /etc/profile.d/00-image-env.sh
    printf 'DEVCONTAINER_WORKSPACE=%s\n' "${DEVCONTAINER_WORKSPACE:-$WORKSPACE_DIR}"
  } >~/.ssh/environment
  chmod 0600 ~/.ssh/environment
}

# Rebuilds ~/.ssh/authorized_keys from the keys the container came with and the workspace's
# gitignored .ssh/authorized_keys, so a key deleted there is gone after the next run. The first
# run keeps the container's own file as authorized_keys.image (empty if there was none). Keys are
# copied, not linked: sshd's StrictModes rejects a key file below the world-writable workspace
# mount. sshd reads the file on every login, so changes need no restart. Also the command
# `ssh-update-keys`.
install_authorized_keys() {
  local keys="$HOME/.ssh/authorized_keys" src="$WORKSPACE_DIR/.ssh/authorized_keys"
  local image="$HOME/.ssh/authorized_keys.image" tmp file line
  mkdir -p ~/.ssh
  if [ ! -f "$image" ]; then
    if [ -f "$keys" ] && [ ! -L "$keys" ]; then cp "$keys" "$image"; else : >"$image"; fi
    chmod 0600 "$image"
  fi
  # A temporary file in the same folder and a rename, so a login never sees a partial file.
  tmp="$(mktemp "$keys.XXXXXX")"
  for file in "$image" "$src"; do
    [ -f "$file" ] || continue
    while IFS= read -r line || [ -n "$line" ]; do
      line="${line%$'\r'}"
      [ -n "${line//[[:space:]]/}" ] || continue
      grep -qxF -- "$line" "$tmp" || printf '%s\n' "$line" >>"$tmp"
    done <"$file"
  done
  mv -f "$tmp" "$keys"
  log "ssh: $(grep -cvE '^[[:space:]]*#' "$keys" || true) key(s) in $keys"
}

# Interactive shells source profile.sh, which applies the auth choice to the shell environment.
install_profile() {
  local line=". \"$DEVCONTAINER_DIR/profile.sh\""
  grep -qxF "$line" ~/.bashrc 2>/dev/null || printf '%s\n' "$line" >>~/.bashrc
}

enable_firewall() {
  if [ -x /usr/local/sbin/agent-firewall ]; then
    sudo -n /usr/local/sbin/agent-firewall
  else
    log "AGENT_FIREWALL=1, but this environment has no agent-firewall; traffic stays open"
  fi
}
