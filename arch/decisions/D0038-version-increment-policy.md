---
title: Increment Versions by Their Impact on Absolute References
id: D0038
addresses:
  - R0024
short_title: Version Increment Policy
description: >-
  A version increments by the highest impact of the changes since the last version: MAJOR when an
  absolute ID would mislead, MINOR when content is added or firmed up, PATCH for corrections.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:01138fe560ba59101ecac98b78e7ccb248f5059aa76da8b6ad5f9fc659a04028
---

## Context

A version is only useful to a reader if its increments say how far the content may have moved. An
absolute ID such as `0.1.0:D0017` should keep meaning what it meant.

## Decision

- Increments mark published states, committed to the shared history or released; all changes between
  two published states fold into one increment by their highest category (S0009).
- MAJOR when an absolute ID would now lead a reader astray, MINOR when content is added or firmed up
  without invalidating what an absolute ID said, PATCH for corrections that do not change meaning.
- Rendering, layout, configuration, lock and provider changes do not increment.
- Each record's revision version follows the same rules; the record set moves by the highest
  category among the record changes since its last version, once per batch.
- While the major version is 0, MAJOR-category changes increment MINOR and all others PATCH; the
  record set goes to `1.0.0` with chancellor's first final release.

## Alternatives Considered

- One increment per edit: rejected, because versions mark published states, and per-edit increments
  show as jumps in git.

## Consequences

- A version never goes back, and a released `<version>:<id>` stays valid in history.

## References and Links

- **Specification**:
  - [S0009: Version Increment Policy](../specifications/S0009-version-increment-policy.md)

## Notes

None.
