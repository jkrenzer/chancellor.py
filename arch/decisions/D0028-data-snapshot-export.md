---
title: Export a Snapshot of the Validated Data on Request
id: D0028
addresses:
  - R0010
short_title: Data Snapshot Export
description: >-
  On request, chancellor writes the validated data tree as JSON to a configured path; the snapshot
  is output, never input.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:0d2fe8009ff3fe00e44a05e2263998f2107398467b3e00d38be59c5add788110
---

## Context

Other tools may want the validated data with every default filled rather than the raw YAML, for
example to index records or to check them in CI.

## Decision

- `config/chancellor/snapshot` names a path; when it is set, `build` writes the validated data tree
  there as JSON.
- The snapshot is opt-in and is excluded from every document's inputs.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Writing a snapshot never causes a rebuild.

## References and Links

None.

## Notes

None.
