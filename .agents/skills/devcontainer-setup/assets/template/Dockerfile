# Stages, a contract the .devcontainer scripts rely on; keep the names:
# - toolchain: the project's language toolchain. Project-specific: replace the example below.
# - agent: the dev container image (.devcontainer/devcontainer.json builds this target). Adds a
#   non-root user, coding-agent CLIs and the tools the .devcontainer scripts use. Generic.
# - app (default target): the toolchain with the project installed, e.g. for CI or deployment.
#
# Pin the Debian release in base tags (-trixie, -bookworm): floating tags move to a new release
# and break features that only support the old one.

FROM debian:trixie-slim AS toolchain
# {{TOOLCHAIN}}: replace with the project's toolchain, e.g. python:3.14-slim-trixie plus the
# package manager, node:24-trixie-slim, rust:slim-trixie. Put tools on PATH with ENV; the agent
# stage carries ENV PATH over into SSH and login shells (see 00-image-env.sh below).
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

FROM toolchain AS agent

# USERNAME must match "remoteUser" and the volume targets in devcontainer.json.
ARG USERNAME=dev
ARG USER_UID=1000
# Versions a fresh container starts with. Claude Code updates itself at runtime; Codex does not.
# {{AGENT_VERSIONS}}: look up current releases when setting up a project.
ARG CLAUDE_CODE_VERSION=2.1.308
ARG CODEX_VERSION=0.165.0

# aggregate, dnsutils, iproute2, ipset, iptables, jq: .devcontainer/root/agent-firewall.
# gh: GitHub CLI, also a token source for .devcontainer/github-token.sh.
# sudo: lets the dev user run the two root helpers below, nothing else.
RUN apt-get update && apt-get install -y --no-install-recommends \
    aggregate \
    ca-certificates \
    curl \
    dnsutils \
    gh \
    git \
    iproute2 \
    ipset \
    iptables \
    jq \
    less \
    openssh-client \
    procps \
    ripgrep \
    sudo \
    && rm -rf /var/lib/apt/lists/*

RUN arch="$(uname -m)" \
    && curl -fsSL "https://github.com/openai/codex/releases/download/rust-v${CODEX_VERSION}/codex-${arch}-unknown-linux-musl.tar.gz" \
    | tar -xz -C /tmp \
    && install -m 0755 "/tmp/codex-${arch}-unknown-linux-musl" /usr/local/bin/codex \
    && rm "/tmp/codex-${arch}-unknown-linux-musl"

# Root helpers come from the image, not the workspace, so an agent cannot change what runs as
# root. Changing them or the firewall allowlist takes a rebuild.
COPY .devcontainer/root/agent-firewall .devcontainer/root/fix-workspace /usr/local/sbin/
COPY .devcontainer/root/firewall-allow.txt /etc/agent-firewall/allow.txt
# CLAUDE_CONFIG_DIR moves .claude.json into the persisted ~/.claude (see the volumes in
# devcontainer.json).
ENV CLAUDE_CONFIG_DIR=/home/$USERNAME/.claude
ENV PATH="/home/$USERNAME/.local/bin:$PATH"
# Login shells (SSH sessions among them) do not inherit the image's ENV, and Debian's
# /etc/profile resets PATH; profile.d restores both. Further variables agents need go here too.
RUN printf 'export PATH="%s"\nexport CLAUDE_CONFIG_DIR="%s"\n' "$PATH" "$CLAUDE_CONFIG_DIR" \
    > /etc/profile.d/00-image-env.sh
# sshd starts sessions with an empty environment; it takes these variables from the user's
# ~/.ssh/environment, which .devcontainer/setup.sh writes from 00-image-env.sh and the
# workspace path, so `ssh host <command>` finds the tools too. The sshd feature installs later
# and includes this directory.
RUN mkdir -p /etc/ssh/sshd_config.d \
    && echo 'PermitUserEnvironment DEVCONTAINER_WORKSPACE,PATH,CLAUDE_CONFIG_DIR' \
    > /etc/ssh/sshd_config.d/devcontainer.conf
# {{TOOLCHAIN_OWNERSHIP}}: if the toolchain installs into a shared location the dev user must
# write to (e.g. a Python venv in /opt/venv), chown it here: && chown -R "$USERNAME:$USERNAME" ...
RUN chmod 0755 /usr/local/sbin/agent-firewall /usr/local/sbin/fix-workspace \
    && useradd --create-home --shell /bin/bash --uid "$USER_UID" "$USERNAME" \
    && echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/sbin/agent-firewall, /usr/local/sbin/fix-workspace" \
    > /etc/sudoers.d/agent \
    && chmod 0440 /etc/sudoers.d/agent

USER $USERNAME
# The directories devcontainer.json mounts volumes on exist first, so the volumes belong to
# the dev user.
RUN mkdir -p ~/.claude ~/.codex ~/.config/gh ~/.ssh \
    && curl -fsSL https://claude.ai/install.sh | bash -s "$CLAUDE_CODE_VERSION"

FROM toolchain AS app
# {{APP}}: copy the project in and install it, e.g.
#   WORKDIR /workspace
#   COPY . .
#   RUN <install command>
CMD ["bash"]
