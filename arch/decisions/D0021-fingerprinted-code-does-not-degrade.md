---
title: Treat Completely Hashed Code as No Degradation
id: D0021
addresses:
  - R0009
  - R0006
short_title: Fingerprinted Code Does Not Degrade
description: >-
  Code and resources chancellor can hash completely are no degradation; an unversioned provider
  hashed completely raises only an INFO message.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:5ba4fc72eebd7caf84c818f1923f6105ee5062993798703b893d61aeab1ca906
---

## Context

A loose module can be fingerprinted reliably by its source bytes, yet unversioned providers and
loose modules were treated as degradations, while supplied root models and model overrides in
configuration were not.

## Decision

- A reliably fingerprintable module or other resource is no degradation.
- A provider without a version whose manifest, templates and full code closure are digested
  completely raises an INFO message instead of a degradation: "Drop the level to an info message as
  long as we can safely hash it."
- If anything in it cannot be hashed safely, `unversioned-provider` stays a degradation next to
  `unfingerprinted-code`, and `--strict` fails.

## Alternatives Considered

- Degrade every loose module even when its bytes are fingerprinted, as first implemented.

## Consequences

- A project with a local Python model passes `--strict` when its code closure is complete.
- An unversioned provider no longer fails `--strict` by itself.

## References and Links

None.

## Notes

None.
