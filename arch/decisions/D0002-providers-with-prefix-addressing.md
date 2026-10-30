---
title: Contribute Kinds and Templates Through Providers Addressed by Prefix
id: D0002
addresses:
  - R0004
  - R0005
short_title: Providers With Prefix Addressing
description: >-
  One mechanism, the provider, carries every contribution, and each contribution is addressed as
  `<provider>/<name>` so nothing shadows anything silently.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:433daf0c6ad3e62d9570fef91b303c8757c5f5812e93078706ba27798d4788ba
---

## Context

Projects need local templates and model definitions. Templates were already loaded through a Jinja2
`PrefixLoader`; models had no comparable mechanism.

## Decision

- A provider is a named, versioned bundle declared in one manifest file; built-in, plugin and local
  providers load through the same code path.
- Every contribution is addressed as `<provider>/<name>`, extending the template prefix rule to
  models.
- Load order is fixed: built-in, entry points by distribution name, local providers in declared
  order. Redefinition is an error; an override is written out in configuration.
- One registry is the only lookup from a kind to everything it needs.

## Alternatives Considered

- Search paths where a later folder shadows an earlier one were not adopted, because shadowing is
  silent.

## Consequences

- The built-in kinds get no privileged path, so local providers stay covered by the same tests.
- A provider cannot redefine a kind; a project extends one by a model override in configuration
  (D0025).

## References and Links

- **Specification**:
  - [S0001: Provider Manifest](../specifications/S0001-provider-manifest.md)

## Notes

None.
