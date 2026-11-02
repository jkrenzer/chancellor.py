---
title: Defer Reports and Prose Documents but Keep Room for Them
id: D0014
addresses:
  - R0022
short_title: Defer Prose Documents
description: >-
  The first release builds records only and keeps rendering open for template-to-template rendering
  and document-walking functions.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:786e7fe9879ff10746832b8be8196d0faf5d2716047814720e8f1bdcea4652bc
---

## Context

Records come first; reports and prose documents follow in a later release.

## Decision

- Reports and prose documents are deferred to a later release.
- The rendering design must not assume a record-shaped model and a single rendering pass.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- The build pipeline keeps the template environment open to registered functions.

## References and Links

None.

## Notes

None.
