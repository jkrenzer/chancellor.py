---
title: Render Documents Without Network Access
id: D0002
addresses: []
short_title: Render Documents Without Network Access
description: >-
  Rendering works offline, from local data and templates only, so that a CI runner without network
  access produces the same documents as a developer's machine does.
tags: []
author: sample-team
date: '2026-10-06'
state: drafted
version: 0.1.0
revisions:
  - version: 0.1.0
    date: '2026-10-06'
    description: >-
      Draft written to try the approach before the CI runners were configured for offline builds.
data_hash: c1:sha256:d4046cb0155bab1b05b541bf7624cc5785aa7858c66a01d25f5043eeeec4b692
---

## Context

Rendering runs in CI without network access.

## Decision

- Render from local data and templates only.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- No remote includes.

## References and Links

None.

## Notes

Open question whether caching is needed.
