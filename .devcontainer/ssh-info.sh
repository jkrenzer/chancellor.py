#!/usr/bin/env bash
# Prints how to reach this container over SSH (and without it), as far as the container can tell.
# Installed as the command `ssh-info` by setup.sh; the environment hook's env_ssh_info adds the
# part that depends on where the container runs. Prints no secrets.
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

env_name="$(dev_env)"
hook="$DEVCONTAINER_DIR/environments/$env_name.sh"
# shellcheck source=/dev/null
[ -f "$hook" ] && . "$hook"

user="$(id -un)"
port="$(sed -n 's/^[[:space:]]*Port[[:space:]]\+\([0-9]\+\).*/\1/p' \
  /etc/ssh/sshd_config /etc/ssh/sshd_config.d/*.conf 2>/dev/null | tail -n 1 || true)"
port="${port:-22}"
keys=0 other=0
if [ -f ~/.ssh/authorized_keys ]; then
  keys="$(grep -cE '^(ssh-|ecdsa-|sk-)' ~/.ssh/authorized_keys || true)"
  other="$(grep -vE '^(ssh-|ecdsa-|sk-|#|[[:space:]]*$)' ~/.ssh/authorized_keys | grep -c . || true)"
fi

echo "Environment:     $env_name"
echo "User:            $user"
echo "Workspace:       $WORKSPACE_DIR (DEVCONTAINER_WORKSPACE in every session)"
if ! command -v sshd >/dev/null; then
  echo "sshd:            not installed in this image"
elif pgrep -x sshd >/dev/null; then
  echo "sshd:            running, port $port in the container"
else
  echo "sshd:            not running (the container's entrypoint starts it as root)"
fi
echo "Authorized keys: $keys in ~/.ssh/authorized_keys (login is by key only)"
if [ "$other" -gt 0 ]; then
  echo "                 $other other line(s) there are not public keys; sshd needs the whole"
  echo "                 line of your *.pub file (ssh-ed25519 AAAA... you@host), not a fingerprint"
fi
echo

if declare -F env_ssh_info >/dev/null; then
  env_ssh_info "$user" "$port" "$keys"
else
  echo "The hook for '$env_name' has no env_ssh_info; add one to $hook."
fi
