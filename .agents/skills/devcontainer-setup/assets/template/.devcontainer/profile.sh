# shellcheck shell=bash
# Sourced by the dev user's ~/.bashrc (installed by setup.sh). Applies the auth choice from
# config.env to interactive shells, so a key meant for another repository does not bill here,
# and starts them in the workspace.
# Editor extensions do not read ~/.bashrc; setup.sh warns about a mismatch for them.

# shellcheck source=config.env
. "$(dirname "${BASH_SOURCE[0]}")/config.env"
if [ "$CLAUDE_AUTH" = subscription ]; then unset ANTHROPIC_API_KEY; fi
if [ "$CODEX_AUTH" = subscription ]; then unset OPENAI_API_KEY CODEX_API_KEY; fi

# Shells that start in the home directory, SSH logins among them, move to the workspace. Where
# the variable did not arrive, this file's location gives the path.
: "${DEVCONTAINER_WORKSPACE:=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export DEVCONTAINER_WORKSPACE
if [ "$PWD" = "$HOME" ]; then cd "$DEVCONTAINER_WORKSPACE" || true; fi
