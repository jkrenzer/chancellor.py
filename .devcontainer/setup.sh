#!/usr/bin/env bash
# Prepares the workspace. Usage: setup.sh <phase>...
#   create  once per container (devcontainer.json postCreateCommand)
#   start   on every container start (postStartCommand)
# Environments that do not build our image (e.g. a vendor's cloud agent with its own base image)
# run `bash .devcontainer/setup.sh create start` as their setup script; steps that need our
# image are skipped there.
set -euo pipefail
# shellcheck source=lib.sh
. "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

env_name="$(dev_env)"
hook="$DEVCONTAINER_DIR/environments/$env_name.sh"
if [ ! -f "$hook" ]; then
  log "no hook for environment '$env_name'; add $hook (see lib.sh)"
  exit 1
fi
# shellcheck source=/dev/null
. "$hook"
log "environment: $env_name"

[ $# -gt 0 ] || set -- create start
for phase in "$@"; do
  case "$phase" in
    create)
      repair_ownership
      repair_links
      (cd "$WORKSPACE_DIR" && eval "$PROJECT_SETUP")
      install_profile
      install_commands
      register_image_mcp
      env_create
      ;;
    start)
      # Again on every start: the host may have rewritten files since the last one.
      repair_ownership
      repair_links
      install_ssh_env
      install_authorized_keys
      configure_auth
      env_start
      if [ "$AGENT_FIREWALL" = 1 ]; then enable_firewall; fi
      ;;
    *)
      log "unknown phase '$phase'"
      exit 1
      ;;
  esac
done
