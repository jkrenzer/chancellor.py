# shellcheck shell=bash
# Hook for CI runs of the dev container (devcontainers/ci GitHub Action, or `devcontainer up` in
# any CI). Sourced by setup.sh and ssh-info.sh after lib.sh; defines env_create, env_start and
# env_ssh_info. Detected by CI=true, which CI systems set on the runner; pass it into the
# container (the workflow template does), or set DEVCONTAINER_ENV=ci.

# CI jobs run tests, not agents; an unattended agent job sets AGENT_FIREWALL=1 itself.
: "${AGENT_FIREWALL:=0}"

env_create() {
  # No MCP servers and no logins: CI only needs the toolchain and PROJECT_SETUP.
  :
}

env_start() { :; }

# Usage: env_ssh_info <user> <sshd port> <number of authorized keys>
env_ssh_info() {
  echo "CI run: no interactive access. Reproduce locally with:"
  echo "  devcontainer up --workspace-folder . && devcontainer exec --workspace-folder . bash -l"
}
