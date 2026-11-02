# Stages:
# - toolchain: the project's language toolchain. Project-specific; a project derived from this
#   setup replaces this stage and keeps the stage names.
# - agent: the dev container image (.devcontainer/devcontainer.json builds this target). Adds a
#   non-root user, coding-agent CLIs and the tools the .devcontainer scripts use. Project-agnostic.
# - app (default target): the toolchain with the project installed.

FROM rust:slim-trixie AS rust-builder

# Install any native build dependencies here, if needed.
# For example: pkg-config, git and libssl-dev
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        pkg-config \
        git \
        libssl-dev \
        dpkg-dev \
        libsqlite3-dev \
    && rm -rf /var/lib/apt/lists/*
RUN cargo install cargo-deb --locked

WORKDIR /build
# Pull in Cargo.toml for settings
# COPY .docker/Cargo.toml ./

# Build the projects in subdirs and create a .deb package in /tmp
## Common Agent Usage Tracker (CAUT) for tracking agent usage and resource consumption
## Pinned to a commit so that image builds are reproducible; bump it to update CAUT.
ARG CAUT_COMMIT=39a0ddcb2a0032462610073512e422f3d33068f8
RUN git init coding_agent_usage_tracker \
    && cd coding_agent_usage_tracker \
    && git fetch --depth 1 \
        https://github.com/Dicklesworthstone/coding_agent_usage_tracker "$CAUT_COMMIT" \
    && git checkout --quiet FETCH_HEAD \
    && cargo deb --output /tmp/caut.deb \
    && cd .. \
    && rm -rf coding_agent_usage_tracker

FROM python:3.14-slim-trixie AS toolchain

# Poetry lives in its own venv so that project dependencies (dulwich among them, which Poetry
# also depends on) cannot break it. The project installs into /opt/venv, which Poetry uses
# because VIRTUAL_ENV points at it.
ENV POETRY_HOME=/opt/poetry
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$POETRY_HOME/bin:$PATH"
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false

# libatomic1: the Node.js that pyright downloads for Serena (`poe serena`) needs it.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    gh \
    libatomic1 \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$POETRY_HOME" \
    && "$POETRY_HOME/bin/pip" install --upgrade pip \
    && "$POETRY_HOME/bin/pip" install "poetry>=2.3,<3" \
    && python -m venv "$VIRTUAL_ENV"


FROM toolchain AS builder

# Add any build-requirement installation steps here.
## None yet
# Add any build steps here
## None yet

# Copy Install .debs from other builder images
## Common Agent Usage Tracker (CAUT) for tracking agent usage and resource consumption
COPY --from=rust-builder /tmp/caut.deb /tmp/caut.deb
RUN dpkg -i /tmp/caut.deb && rm /tmp/caut.deb

# Add any clean-up steps here to keep the image size down.
## None yet

FROM builder AS agent

# USERNAME must match "remoteUser" and the volume targets in devcontainer.json.
ARG USERNAME=dev
ARG USER_UID=1000
# Versions a fresh container starts with. Claude Code updates itself at runtime; Codex does not.
ARG CLAUDE_CODE_VERSION=2.1.308
ARG CODEX_VERSION=0.165.0

# aggregate, dnsutils, iproute2, ipset, iptables, jq: .devcontainer/root/agent-firewall.
# sudo: lets the dev user run the two root helpers below, nothing else.
RUN apt-get update && apt-get install -y --no-install-recommends \
    aggregate \
    dnsutils \
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
# /etc/profile resets PATH; profile.d restores both.
RUN printf 'export PATH="%s"\nexport CLAUDE_CONFIG_DIR="%s"\n' "$PATH" "$CLAUDE_CONFIG_DIR" \
    > /etc/profile.d/00-image-env.sh
# sshd starts sessions with an empty environment; it takes these variables from the user's
# ~/.ssh/environment, which .devcontainer/setup.sh writes from 00-image-env.sh and the
# workspace path, so `ssh host <command>` finds the tools too. The sshd feature installs later
# and includes this directory.
RUN mkdir -p /etc/ssh/sshd_config.d \
    && echo 'PermitUserEnvironment DEVCONTAINER_WORKSPACE,PATH,CLAUDE_CONFIG_DIR' \
    > /etc/ssh/sshd_config.d/devcontainer.conf
# The dev user owns Poetry's venv too: Poetry installs the project's plugins (requires-plugins)
# into .poetry/plugins only while it can write to its own bin/. Otherwise it falls back to a user
# install and garbles the target path (Poetry 2.5.1).
RUN chmod 0755 /usr/local/sbin/agent-firewall /usr/local/sbin/fix-workspace \
    && useradd --create-home --shell /bin/bash --uid "$USER_UID" "$USERNAME" \
    && echo "$USERNAME ALL=(root) NOPASSWD: /usr/local/sbin/agent-firewall, /usr/local/sbin/fix-workspace" \
    > /etc/sudoers.d/agent \
    && chmod 0440 /etc/sudoers.d/agent \
    && chown -R "$USERNAME:$USERNAME" "$VIRTUAL_ENV" "$POETRY_HOME"

USER $USERNAME
# The directories devcontainer.json mounts volumes on exist first, so the volumes belong to
# the dev user.
RUN mkdir -p ~/.claude ~/.codex ~/.config/gh ~/.ssh/ \
    && curl -fsSL https://claude.ai/install.sh | bash -s "$CLAUDE_CODE_VERSION"


FROM toolchain AS app

WORKDIR /workspace

COPY pyproject.toml poetry.lock README.md LICENSE ./
COPY src ./src
COPY docs ./docs

RUN poetry install --all-extras

CMD ["bash"]
