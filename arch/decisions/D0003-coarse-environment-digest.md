---
title: Use One Coarse Digest for All of config/chancellor
id: D0003
addresses:
  - R0008
short_title: Coarse Environment Digest
description: >-
  One fingerprint covers the resolved provider set and one digest the whole of `config/chancellor`;
  any change in either rebuilds every document chancellor owns.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:cb711f5ca79c539d0fa81c99e018b20e4eceb6d7fac02982740c7f7dbbd9b1e2
---

## Context

A finer digest would rebuild only documents affected by a configuration key, but which key affects
which file depends on templates and providers and cannot be known reliably.

## Decision

- The configuration part of every document's `input_hash` is one digest over the whole validated
  `config/chancellor`.
- The provider part is one fingerprint over the whole resolved provider set; any change in it, too,
  rebuilds every document chancellor owns.

## Alternatives Considered

- Per-document configuration slices: rejected, because a wrong slice yields a stale document, and a
  needless rebuild is cheaper than a stale one.

## Consequences

- Changing the wrap width or any kind setting rebuilds everything.
- `explain` can always name `config` or the provider set as the moved part.

## References and Links

None.

## Notes

None.
