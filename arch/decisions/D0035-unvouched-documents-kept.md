---
title: Keep and Report Documents Chancellor Cannot Vouch For
id: D0035
addresses:
  - R0014
short_title: Unvouched Documents Kept
description: >-
  Proposed: documents an unusable lock still names are reported as orphans and kept, and unknown
  files in a kind's output folder are warned about and kept; `doctor` flags them.
tags: []
author: jkrenzer
date: '2026-10-30'
state: proposed
version: 0.1.0
revisions:
  - version: 0.1.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:24866866a335de17fa4e79196513cb49e738a9b3eded8f45e077ebf51f93b5f0
---

## Context

An outdated lock is ignored and everything is rebuilt (R0009). A cold build knows nothing of the
documents the old lock tracked, so a renamed document stays behind and looks current.

## Decision

- The document paths of an unusable lock are read best effort; those still on disk are reported as
  orphans and never deleted, because their hashes cannot be trusted.
- A file in a kind's output folder named `<ID>…<suffix>`, with an ID matching the kind's pattern and
  unknown to the plan and every lock, is listed as untracked with a warning, kept, and not counted
  as drift.
- `doctor` reports untracked documents as problems and exits 1.

## Alternatives Considered

- Delete such files: rejected, because chancellor cannot tell whether someone edited them.

## Consequences

- A stale document after a lock-format change is visible instead of silent; removing it stays a
  person's decision.

## References and Links

None.

## Notes

The maintainer confirmed that `doctor` exits 1 for untracked documents; the rest of the record is
still proposed.
