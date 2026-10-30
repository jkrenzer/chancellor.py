#!/usr/bin/env bash
# Starts GitHub's MCP server as a container on stdio, with a token from github-token.sh.
# Registered by environments/local.sh; needs Docker and one of: GITHUB_PERSONAL_ACCESS_TOKEN,
# GH_TOKEN, `gh auth login`, or a VS Code window attached to the container.
set -euo pipefail
if ! token="$(bash "$(dirname "${BASH_SOURCE[0]}")/../github-token.sh")"; then
  echo "github MCP: no token; attach VS Code to the container, run 'gh auth login'," \
    "or set GH_TOKEN" >&2
  exit 1
fi
export GITHUB_PERSONAL_ACCESS_TOKEN="$token"
exec docker run -i --rm -e GITHUB_PERSONAL_ACCESS_TOKEN \
  "ghcr.io/github/github-mcp-server:${GITHUB_MCP_SERVER_VERSION:-2.0.3}"
