---
title: Load Configuration Through a Loader Interface Built on pydantic-settings
id: D0004
addresses:
  - R0012
short_title: Config Loader Interface
description: >-
  Configuration comes from a loader interface whose sources follow pydantic-settings; the first
  release has one loader reading the data file.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:02387c4219c362a1da7065e7a868250058a5f324bc0d950805ed0d79156230d1
---

## Context

Pydantic validates objects; it does not read files. pydantic-settings already provides an ordered
source stack for JSON, YAML, TOML and `pyproject.toml`.

## Decision

- Build the loader interface on the pydantic-settings source protocol.
- Ship one loader in v1, reading `config/chancellor` from the data tree.
- A standalone file and `[tool.chancellor]` are later loaders against the same interface.
- Use a source built on ruamel.yaml rather than the `pydantic-settings[yaml]` extra (D0011).

## Alternatives Considered

- A hard-wired read of the data file: rejected, because it would have to be torn up for the second
  source.

## Consequences

- Source order is defined once and dumped at DEBUG.

## References and Links

None.

## Notes

None.
