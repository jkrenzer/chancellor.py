---
title: Digest the Validated Configuration in Chancellor, Not in the Loader
id: D0020
addresses:
  - R0008
  - R0011
  - R0012
  - R0021
short_title: Config Digest by Chancellor
description: >-
  Configuration loaders return data only; chancellor digests the validated configuration with
  defaults filled and without layout keys.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:7068bea9b5a5fb808980d35e5b4a2fb5ac8139fe81b8bdc46b20c03ba863dac6
---

## Context

If every loader returned a digest of its own configuration, loaders could disagree on the canonical
form, and an omitted default would digest differently from a written one.

## Decision

- `ConfigLoader.load()` returns the raw mapping and its origin, no digest.
- Chancellor digests the validated configuration with defaults filled.
- Layout keys, `include` and `kinds.<kind>.data`, are excluded from the digest.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Moving configuration between loaders changes no digest.
- A `loaders` key would be a layout key as well; it is proposed in D0034.

## References and Links

None.

## Notes

None.
