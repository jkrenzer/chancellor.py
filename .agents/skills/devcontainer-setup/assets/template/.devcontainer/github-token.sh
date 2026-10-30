#!/usr/bin/env bash
# Prints a GitHub token for tools in the container, the first one found of:
#   GITHUB_PERSONAL_ACCESS_TOKEN, GH_TOKEN, `gh auth token`, VS Code's git credential bridge.
# Prints nothing and exits 1 when none is available. Never logs the token.
#
# The bridge is the git credential helper the Dev Containers extension installs. It works in any
# process, SSH sessions included, while a VS Code window is attached to the container; outside a
# VS Code process REMOTE_CONTAINERS_IPC is unset, so the newest IPC socket is used.
set -uo pipefail

for token in "${GITHUB_PERSONAL_ACCESS_TOKEN:-}" "${GH_TOKEN:-}"; do
  if [ -n "$token" ]; then
    printf '%s\n' "$token"
    exit 0
  fi
done

if command -v gh >/dev/null; then
  token="$(gh auth token 2>/dev/null)"
  if [ -n "$token" ]; then
    printf '%s\n' "$token"
    exit 0
  fi
fi

ipc="${REMOTE_CONTAINERS_IPC:-}"
if [ ! -S "$ipc" ]; then
  # shellcheck disable=SC2012  # socket names hold no special characters
  ipc="$(ls -t /tmp/vscode-remote-containers-ipc-*.sock 2>/dev/null | head -n 1)"
fi
if [ -S "$ipc" ]; then
  token="$(printf 'protocol=https\nhost=github.com\n\n' \
    | REMOTE_CONTAINERS_IPC="$ipc" GIT_TERMINAL_PROMPT=0 timeout 10 git credential fill 2>/dev/null \
    | sed -n 's/^password=//p')"
  if [ -n "$token" ]; then
    printf '%s\n' "$token"
    exit 0
  fi
fi

exit 1
