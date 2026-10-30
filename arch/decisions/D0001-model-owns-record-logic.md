---
title: Keep Validation, Derived Values and Front Matter in the Model
id: D0001
addresses:
  - R0001
  - R0019
short_title: Model Owns Record Logic
description: >-
  Record models validate, default and serialize; templates render the body only and never repair,
  default or re-check data.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:c3e7048fd5abb064c3bda467e4e5921c772d467a35c978a5fd2a12e583fc5bac
---

## Context

When templates compute defaults, write front matter field by field, re-check what the model already
checked, and are split apart again after rendering, documents and data drift apart. A template that
forgets a field then produces a document that still looks valid.

## Decision

- Validation lives in the model: unknown inputs are refused (`extra="forbid"`) with a readable error
  that lists every violation.
- Derived values, such as the short title, the creation date and the version, are computed on the
  model in one place; templates do no defaulting.
- Chancellor serializes the front matter from the model; templates render the body only, and front
  matter and body are produced separately, never split back apart.
- Templates run with `StrictUndefined`; the `required_text` and `required_list` filters stay
  available, but the built-in templates do not rely on them for correctness.
- Each kind's model declares its ID pattern and its core document's ID.
- Chancellor orders records by ID and generates each core document's index; the index is excluded
  from the digest and refused as input.

## Alternatives Considered

- Defaults and front matter written by templates: rejected, because a forgotten or misquoted field
  goes unnoticed.

## Consequences

- A template cannot drop or misquote a front-matter field.
- A provider's templates only lay content out, which keeps them short.

## References and Links

- **Specification**:
  - [S0007: Built-In Record Kinds](../specifications/S0007-built-in-record-kinds.md)

## Notes

None.
