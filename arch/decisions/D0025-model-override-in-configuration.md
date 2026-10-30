---
title: Let a Project Subclass a Provider's Kind Model in Configuration
id: D0025
addresses:
  - R0004
  - R0019
short_title: Model Override in Configuration
description: >-
  A project replaces a kind's record or core model with a subclass of the provider's model, named in
  `config/chancellor` as `kinds.<kind>.model` or `kinds.<kind>.core_model`.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:875310c15349b0e25787840bdd954ae3626bcf5232bdbd16e43eaa4a3f8df820
---

## Context

A project may need a field the built-in record kinds lack. The built-in models refuse unknown
fields, and a later provider may not redefine a kind (R0004).

## Decision

- `config/chancellor` accepts `kinds.<kind>.model` and `kinds.<kind>.core_model`, each a subclass of
  the provider's model for that kind; anything else is refused.
- A model is named as `path/to/file.py:Class`, relative to the project root, or as `module:Class`.
- `chancellor providers` lists each override as `model:<kind>`.
- An override is fingerprinted by its code and the JSON Schema it emits and is no degradation when
  its code can be hashed completely.

## Alternatives Considered

- A field added to `builtin.jkrenzer` for one project's needs.
- Tags as a stand-in for a missing field: rejected, because they crowd every core index entry.
- Letting a provider extend an existing kind, which R0004 rules out.

## Consequences

- Both reference forms, code from installed or editable distributions and helper modules a file
  override imports are fingerprinted along the one code path (D0031).
- Like a file override, a provider's loose module degrades only when it cannot be hashed completely
  (D0021).

## References and Links

- **Specification**:
  - [S0004: Extension Interfaces](../specifications/S0004-extension-interfaces.md)
  - [S0002: Project Data Tree](../specifications/S0002-project-data-tree.md)

## Notes

None.
