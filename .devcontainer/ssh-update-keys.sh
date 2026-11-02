#!/usr/bin/env bash
# Rebuilds ~/.ssh/authorized_keys from the container's own keys and the workspace's gitignored
# .ssh/authorized_keys; run it after editing the latter. Installed as the command
# `ssh-update-keys` by setup.sh, which also runs it on every start. Prints no keys.
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

install_authorized_keys
