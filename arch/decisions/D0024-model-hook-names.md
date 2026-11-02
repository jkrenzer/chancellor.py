---
title: Name the Model Hooks After Pydantic's Conventions
id: D0024
addresses:
  - R0019
short_title: Model Hook Names
description: >-
  The six model hooks are named `model_load`, `model_validate`, `model_canonicalize`, `model_index`,
  `model_serialize` and `model_save`.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:3a13de259b80979bbefd837d05afc4371cd6a5611117e9edff7ad6b5b2dbf4fa
---

## Context

The hook names are public API in `chancellor.api`, so they are chosen once and reviewed before
consumers depend on them.

## Decision

- The hooks are named as Pydantic names things: `model_load`, `model_validate`,
  `model_canonicalize`, `model_index`, `model_serialize`, `model_save`.
- `front_matter` is a class variable on the model, not a seventh hook.

## Alternatives Considered

- Shorter names: load, validate, canonical, index, dump and save.
- `model_canonical` for the canonicalization hook.

## Consequences

- Renaming a hook after the release is a breaking change of `chancellor.api` (D0009).

## References and Links

None.

## Notes

None.
