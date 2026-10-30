---
title: Command-Line Changes Taken While Coding
id: D0026
addresses:
  - R0002
short_title: CLI Changes While Coding
description: >-
  `hash [IDS]` and `schema data` replace the old forms `hash INPUT` and `schema architecture`,
  without aliases.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:3d31f8ae687b9c5f9a06b49effa2fdb44bad8ac7f58306dcf4fe5534f2078806
---

## Context

R0002 keeps the verbs available but does not fix their arguments. `hash` works on the project's
records, and the data-tree schema is named after the data tree.

## Decision

- `hash [IDS]` prints the data hash of records of the project, replacing `hash INPUT`.
- `schema data` prints the data-tree schema, replacing `schema architecture`.
- No aliases for the old forms.

## Alternatives Considered

- Keeping the old forms as aliases, rejected by the maintainer.

## Consequences

- Scripts that call the earlier forms must change.

## References and Links

None.

## Notes

None.
