#!/usr/bin/env bash
# headersHelper for GitHub's remote MCP server (registered by the environment hooks): prints
# {"Authorization": "Bearer <token>"} with a token from github-token.sh. Prints nothing and exits
# 1 without a token. Never logs the token.
set -euo pipefail
token="$(bash "$(dirname "${BASH_SOURCE[0]}")/../github-token.sh")" || exit 1
# GitHub tokens are letters, digits and underscores; anything else would need JSON escaping.
[[ "$token" =~ ^[A-Za-z0-9_]+$ ]] || exit 1
printf '{"Authorization": "Bearer %s"}\n' "$token"
