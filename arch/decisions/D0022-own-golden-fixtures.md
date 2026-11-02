---
title: Guard Output With Chancellor's Own Golden Fixtures
id: D0022
addresses:
  - R0016
short_title: Own Golden Fixtures
description: >-
  Synthetic sample records and their committed renders guard chancellor's output between versions.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:2db9b7fdad5b28e619c34f11fd9a9fa4db8322e5438b3570b641cca06f41852f
---

## Context

Consuming projects rely on chancellor's version to know when their documents may change. Output that
changes without a version bump breaks that silently.

## Decision

- A synthetic sample project under `tests/fixtures/sample/` covers every built-in kind and template.
- Its renders are committed under `tests/golden/` and compared byte for byte.
- `poe golden` regenerates them deliberately.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- A CI check against unbumped versions is still to be built.

## References and Links

None.

## Notes

None.
