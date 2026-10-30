---
title: Read Each Kind's Records From Its Own Data File
id: D0019
addresses:
  - R0014
  - R0011
short_title: Per-Kind Data Files
description: >-
  `kinds.<kind>.data` names the file that holds a kind's records; `kinds.<kind>.folder` is where the
  kind's documents go.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:51ee5230f60e2e198e2ce6297b98aaa0d8815def7eaadcf9c693563970655392
---

## Context

A setting called a kind's location could mean where its records are read or where its documents are
written. Both need to be configurable, and a project should be able to keep each kind's records in a
file of its own.

## Decision

- `kinds.<kind>.data` names a file, relative to the project root and confined to it, holding the
  kind's section (`core`, `records`).
- A missing data file means the kind has no data yet; chancellor logs it at INFO level.
- A file used as a kind's data and as a whole data tree, or by two kinds, is a configuration error.
- `kinds.<kind>.folder` is the kind's output folder.
- Whole data-tree files can still be merged through `include`; `providers` and `include` are
  honoured only in the main data file.
- Provider folders are never read as data.

## Alternatives Considered

- One shared file for every kind, addressed by the path to its top-level key: planned for later, and
  the code marks where it ties in.

## Consequences

- Data file paths are layout, not content, and stay out of the configuration digest (D0020).

## References and Links

None.

## Notes

None.
