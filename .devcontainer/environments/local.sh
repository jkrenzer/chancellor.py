# shellcheck shell=bash
# Hook for a dev container on a workstation (VS Code, or the devcontainer CLI).
# Sourced by setup.sh and ssh-info.sh after lib.sh; defines env_create, env_start and
# env_ssh_info.

# Interactive work by default; set AGENT_FIREWALL=1 for unattended runs.
: "${AGENT_FIREWALL:=0}"

env_create() {
  # The host's Docker is reachable here (feature docker-outside-of-docker), so MCP servers that
  # ship as container images run locally. Register further ones the same way.
  if docker info >/dev/null 2>&1; then
    register_mcp github bash "$DEVCONTAINER_DIR/mcp/github.sh"
  else
    log "Docker not reachable; container-based MCP servers not registered"
  fi
  # GitHub's remote server for Claude Code, with the token from github-token.sh; it covers
  # sessions started over SSH too, as long as a VS Code window is attached for the token.
  register_mcp_http github-remote https://api.githubcopilot.com/mcp/ \
    "bash $DEVCONTAINER_DIR/mcp/github-headers.sh"
}

env_start() { :; }

# Usage: env_ssh_info <user> <sshd port> <number of authorized keys>
# Asks the host's Docker about this container; Docker names it after its ID, the hostname.
env_ssh_info() {
  local user=$1 port=$2 keys=$3 name="" folder="" published=""
  if docker info >/dev/null 2>&1; then
    name="$(docker inspect --format '{{.Name}}' "$(hostname)" 2>/dev/null | sed 's#^/##')"
    folder="$(docker inspect --format '{{index .Config.Labels "devcontainer.local_folder"}}' \
      "$(hostname)" 2>/dev/null)"
    # docker port fails when the port is not published.
    published="$(docker port "$(hostname)" "$port/tcp" 2>/dev/null | head -n 1 || true)"
  else
    echo "Docker not reachable: container name, host folder and published ports unknown."
    echo
  fi
  echo "From the host, without SSH:"
  echo "  docker exec -it -u $user -w $WORKSPACE_DIR ${name:-$(hostname)} bash -l"
  echo "  devcontainer exec --workspace-folder ${folder:-<folder on the host>} bash -l"
  echo
  local host_port
  if [ -n "$published" ]; then
    host_port="${published##*:}"
    echo "SSH: port $port is published on the host as $published."
  else
    host_port="<forwarded port>"
    echo "SSH: port $port is not published by Docker. To use it while VS Code is connected,"
    echo "forward it in VS Code's Ports panel (Forward a Port, $port; labelled \"SSH: user $user"
    echo "...\") and use the local port from its Forwarded Address column. VS Code forwarding is"
    echo "not visible to Docker, so this script cannot see that port."
  fi
  [ "$keys" -gt 0 ] || echo "First add your public key to ~/.ssh/authorized_keys in the container."
  # 127.0.0.1, not localhost: Windows' ssh may try ::1, where VS Code does not forward.
  echo
  echo "On the host:"
  echo "  ssh -p $host_port $user@127.0.0.1"
  echo "  ssh -p $host_port $user@127.0.0.1 'echo \$DEVCONTAINER_WORKSPACE'"
  echo "  ssh -t -p $host_port $user@127.0.0.1 'cd \"\$DEVCONTAINER_WORKSPACE\" && claude'"
}
