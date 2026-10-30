---
title: Expose Only One Hop of References to a Template
id: D0033
addresses:
  - R0008
short_title: One-Hop References
description: >-
  A template sees a referenced record's declared context but not that record's own references;
  reaching further is an error.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:174f9654a0e5aea3c333c76c8f9885f51ce1dddde9a63844ed341f86c2ebbf94
---

## Context

Under D0032 a reference with `depends="data"` exposes the target's data. Whether the target's own
references are exposed in turn decides how far a change can flow.

## Decision

- A data flow reaches one hop; a target's own references are neither exposed nor digested.
- A template that reaches past one hop fails with a clear error.
- Chains of references are deferred; the documentation says so and the code marks where they tie in.

## Alternatives Considered

- Following references transitively, which rebuilds documents that cannot change (D0032).

## Consequences

- A template that needs a second hop must have its record reference that target directly.

## References and Links

None.

## Notes

None.
