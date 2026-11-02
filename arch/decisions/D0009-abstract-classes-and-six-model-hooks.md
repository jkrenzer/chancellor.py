---
title: Give Every Extension Point an Abstract Class and the Model Six Hooks
id: D0009
addresses:
  - R0019
short_title: Abstract Classes and Six Model Hooks
description: >-
  Every extension point is an abstract base class in `chancellor.api`, implemented by the built-ins
  too, and the model interface has six hooks for loading, validation, canonicalization, indexing,
  serialization and saving.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:77d59187fcf3eef59e51e809945578fd5313267b4a7c6ad64714ba760d3dca32
---

## Context

Options for every edge case are expensive to support. A class the consumer writes is cheap, provided
the interface is stable; the model is where a later addition hurts most.

## Decision

- One abstract base class per extension point in `chancellor.api`: model, provider, formatter,
  linter, config loader, version scheme.
- Built-ins implement the same classes on no privileged path.
- Interfaces carry hooks rather than switches; a consumer's subclass is accepted wherever a type is
  named.
- The model interface has six hooks: loading, validation, canonicalization, indexing, serialization
  and saving, fixed before the classes are written.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- A change to one of these signatures is a breaking change of the distribution.
- The hook names are recorded in D0024.

## References and Links

- **Specification**:
  - [S0004: Extension Interfaces](../specifications/S0004-extension-interfaces.md)
  - [D0024: Model Hook Names](D0024-model-hook-names.md)

## Notes

None.
