# shellcheck shell=bash
# Hook for GitHub Codespaces. Sourced by setup.sh and ssh-info.sh after lib.sh; defines
# env_create, env_start and env_ssh_info.
#
# Secrets (ANTHROPIC_API_KEY, OPENAI_API_KEY, CLAUDE_CODE_OAUTH_TOKEN, GH_TOKEN) come from the
# repository's Codespaces secrets. Connect from outside with `gh codespace ssh`.

# Interactive codespaces stay open; unattended runs set AGENT_FIREWALL=1 (Codespaces variable or
# the run's environment).
: "${AGENT_FIREWALL:=0}"

env_create() {
  # Docker works here too (on the codespace's own VM), but container-based MCP servers are not
  # registered by default: cloud runs use the gh CLI. To add one, copy the register_mcp call
  # from environments/local.sh.
  :
}

env_start() { :; }

# Usage: env_ssh_info <user> <sshd port> <number of authorized keys>
# gh brings its own key and tunnel; it needs sshd in the container, but no published port.
env_ssh_info() {
  local name="${CODESPACE_NAME:-<codespace>}"
  echo "SSH, from any machine with the gh CLI logged in as the codespace's owner:"
  echo "  gh codespace ssh -c $name"
  echo "Host entry for other SSH clients (VS Code Remote-SSH, JetBrains Gateway, Zed):"
  echo "  gh codespace ssh -c $name --config >> ~/.ssh/config"
  echo "Run a command, e.g. a stdio MCP server or an agent in the workspace:"
  echo "  gh codespace ssh -c $name -- 'echo \$DEVCONTAINER_WORKSPACE'"
  echo "  gh codespace ssh -c $name -- -t 'cd \"\$DEVCONTAINER_WORKSPACE\" && claude'"
}
