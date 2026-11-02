---
title: Use SemVer 2.0.0 for Record Revisions and the Record Set
id: D0037
addresses:
  - R0024
short_title: SemVer for Records
description: >-
  This project versions every record revision and the record set with SemVer 2.0.0, writes absolute
  IDs as `<version>:<id>`, and starts the record set at `0.1.0`.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:7293234beef071078fabfbec36f8719be9046434980eb6eb8a2d17d2f63cc016
---

## Context

R0024 asks for a decided versioning scheme. The records already write their revision versions as
MAJOR.MINOR.PATCH, and chancellor's own releases follow PEP 440 numbers of the same shape.

## Decision

- Every record revision and the record set use Semantic Versioning 2.0.0.
- The absolute ID format is `<version>:<id>`, for example `0.1.0:D0017`.
- The record set starts at version `0.1.0`.
- The repository configures the scheme `semver` once chancellor supports it.

## Alternatives Considered

- PEP 440 versions, as for chancellor's distribution: not chosen, because SemVer states what each
  component means for a reader.

## Consequences

- Commit messages, code comments, tests and documentation refer to records as `<version>:<id>`.

## References and Links

- **Specification**:
  - [S0010: SemVer Versions and Absolute IDs](../specifications/S0010-semver-versions-and-absolute-ids.md)
- **Semantic Versioning 2.0.0**:
  - [semver.org/spec/v2.0.0](https://semver.org/spec/v2.0.0.html)

## Notes

None.
