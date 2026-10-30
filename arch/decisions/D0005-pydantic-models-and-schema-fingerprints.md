---
title: Define Kinds by Imported Pydantic Models Fingerprinted by Their Schema
id: D0005
addresses:
  - R0004
  - R0006
short_title: Pydantic Models and Schema Fingerprints
description: >-
  A kind's model is an imported Pydantic v2 class by default, schema-first input sits behind a
  `[schema]` extra, and a model is fingerprinted by the JSON Schema it emits.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:128a14610444af25f0fdc7e51d53f64a7cfa97717df1814d32a9fb8d7a5bc001
---

## Context

Some projects write models by hand, others generate them from a schema in CI or at load. All three
must fingerprint alike, and generator formatting changes should rebuild nothing.

## Decision

- Import Pydantic v2 modules by default.
- Accept schema input through a `[schema]` extra; a consumer committing generated models keeps the
  generator in its dev group.
- Fingerprint a model by its emitted JSON Schema, canonicalized, plus its distribution version or
  the source bytes of a loose module, since validators never appear in a schema.

## Alternatives Considered

- Fingerprinting the generator that wrote a model: rejected, because a generator upgrade would
  rebuild everything.

## Consequences

- Generated files must be written without a timestamp header.
- Record refs and digest exclusions must be visible in the emitted schema (S0004).

## References and Links

None.

## Notes

None.
