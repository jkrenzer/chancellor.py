---
title: Ship Model Generation as a Plugin of the schema Extra With Hooks
id: D0007
addresses:
  - R0017
short_title: Generation Tooling in the schema Extra
description: >-
  Model generation is chancellor's own plugin module inside the `[schema]` extra, with its settings
  documented flag by flag and pre-commit hooks for it and the check commands.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:f1ec120f1a6bd2bbc734721bb3e8c483ec4227dcf5dbf4b1f84c69bf58638a32
---

## Context

Every consumer generating models would otherwise repeat the same generator settings in its own CI
scripts, and drift between them changes fingerprints.

## Decision

- `chancellor model generate` lives in a plugin module inside the `[schema]` extra and owns the
  generator settings.
- Every setting is documented with its upstream CLI flag.
- Chancellor ships `.pre-commit-hooks.yaml` entries for generation and the check commands.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- The `[schema]` extra pulls in datamodel-code-generator, and with it PyYAML transitively (D0011).

## References and Links

None.

## Notes

Not built yet.
