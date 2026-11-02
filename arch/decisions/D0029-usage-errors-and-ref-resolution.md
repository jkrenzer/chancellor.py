---
title: Usage Errors and Ref Resolution Taken While Coding
id: D0029
addresses:
  - R0020
  - R0024
short_title: Usage Errors and Ref Resolution
description: >-
  Command-line misuse exits 1, and a reference shaped like a registered kind's ID must resolve;
  external references are written so they cannot be mistaken for one.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:8f6d28e3a928a62c065656a01cdf271b3b8c4a0ce51c646d9492f1328cd75ec7
---

## Context

The exit-code table does not say which code command-line misuse returns, nor how chancellor tells a
record ID from an external identifier.

## Decision

- Command-line misuse exits 1, as a configuration error.
- A ref shaped like an ID of a registered kind must resolve to a record, else the input is invalid;
  any other value is an external identifier.
- A dangling reference shaped like an ID fails with a hint to write an external reference as
  `<project>:<version>:<id>` or as a URL; a local absolute ID's first part parses as a version
  (S0008).

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- A typo in an ID of a known kind fails the build instead of passing as external.

## References and Links

None.

## Notes

None.
