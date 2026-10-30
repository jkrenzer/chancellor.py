---
title: Write Every File Through One Propose-and-Apply Path
id: D0023
addresses: []
short_title: One Write Path
description: >-
  Nothing is written outside a staging tree except by `apply`, and `output_path_for` is the only
  place output paths are built.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:5e641f8a53a4b961eb7859fd6692721a2da2775df20e5c1bff74dfeb52930d38
---

## Context

When commands write files on their own and tools build paths on their own, partial writes and
divergent path rules follow.

## Decision

- One write path; nothing is written outside the staging tree except by `apply`.
- `output_path_for` is the only place an output path is constructed; paths are never parsed back
  into records.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- The MCP server's authority tiers default to `propose`.

## References and Links

None.

## Notes

Staging inside the repository, backups during the write phase, an NDJSON journal and `recover` are
pending a pipeline specification for the maintainer's review. Today `write.apply` is the single
write function.
