---
title: Ship Only the jkrenzer Flavour in the First Release
id: D0013
addresses:
  - R0001
  - R0004
short_title: Built-In Flavours
description: >-
  The first release ships the `builtin.jkrenzer` flavour only; Nygard joins the built-ins later and
  ECSS comes as a plugin module.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:c4fe25d8a1d167d846a7ae7add163270d2e693a1e4a3c0cb559514833e160a45
---

## Context

Flavours are sub-namespaces of the built-in provider. The common shape of record kinds across
flavours is not settled yet.

## Decision

- The decision, requirement and specification kinds of the first release ship as `builtin.jkrenzer`.
- A Nygard flavour joins the built-ins once the common shape is settled.
- A standard as particular as ECSS ships as a plugin module, not in the distribution.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Template addresses carry the flavour, e.g. `builtin.jkrenzer/decision.md.j2`.

## References and Links

None.

## Notes

None.
