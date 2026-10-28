FROM python:3.11-slim

# Poetry lives in its own venv so that project dependencies (dulwich among them, which Poetry
# also depends on) cannot break it. The project installs into /opt/venv, which Poetry uses
# because VIRTUAL_ENV points at it.
ENV POETRY_HOME=/opt/poetry
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="$VIRTUAL_ENV/bin:$POETRY_HOME/bin:$PATH"
ENV POETRY_NO_INTERACTION=1
ENV POETRY_VIRTUALENVS_CREATE=false

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    gh \
    && rm -rf /var/lib/apt/lists/*

RUN python -m venv "$POETRY_HOME" \
    && "$POETRY_HOME/bin/pip" install --upgrade pip \
    && "$POETRY_HOME/bin/pip" install "poetry>=2.3,<3" \
    && python -m venv "$VIRTUAL_ENV"

WORKDIR /workspace

COPY pyproject.toml poetry.lock README.md LICENSE ./
COPY src ./src
COPY docs ./docs

RUN poetry install --all-extras

CMD ["bash"]
