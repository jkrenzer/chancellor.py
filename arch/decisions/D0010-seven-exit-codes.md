---
title: Use a Fixed Seven-Value Exit-Code Table
id: D0010
addresses:
  - R0020
short_title: Seven Exit Codes
description: Chancellor returns one of seven exit codes with fixed meanings from every command.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:004a6e95a94921185a61b9bcff7b828f7ea73b4ac9f30121ef45735ea4ae073e
---

## Context

A script has to tell a misconfiguration from a finding, so every kind of result gets its own code
instead of a habit of returning 1.

## Decision

- Codes 0 to 6 mean success, configuration error, invalid input, drift, degradations, lint findings
  and internal error.
- Exit code 2 is for record data errors, including one-sided links that `doctor` finds and record
  data defined twice across files.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Hooks and CI can react to drift, degradation and lint findings separately.

## References and Links

- **Specification**:
  - [S0005: Exit Codes](../specifications/S0005-exit-codes.md)

## Notes

Command-line misuse exits 1, as a configuration error (D0029).
