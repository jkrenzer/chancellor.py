---
title: Log Every Top-Level Section at INFO Level
id: D0027
addresses:
  - R0010
short_title: Log Top-Level Sections
description: >-
  Chancellor logs every top-level section of the data tree it encounters at INFO level, and the user
  documentation explains raising the log level to investigate the YAML.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:6117ba5ab034da265bed5e7c3be950e8179a7272835e756fe2a3c20c176e2a71
---

## Context

Other modules may keep their own sections in the shared data tree (R0010), so chancellor cannot
reject a section it does not know, and a misspelt kind section would be ignored silently.

## Decision

- Every top-level section encountered is logged at INFO level, for debugging.
- The user documentation tells users to raise the log level to look into problems with the YAML.

## Alternatives Considered

- An `unknown-section` degradation that fails `--strict`: not chosen.

## Consequences

- An unknown section is neither an error nor a degradation.

## References and Links

None.

## Notes

None.
