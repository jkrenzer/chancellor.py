---
title: Keep the Version at 0.1.0 for the First Internal Release
id: D0015
addresses: []
short_title: Version 0.1.0
description: >-
  The first release is an internal test and stays at version `0.1.0`, which leaves room to change
  the documented public surface.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:071b699dabd9595f960e127362e7e78117a4314ca0dc1e828b4d3c1ee2473bff
---

## Context

`chancellor.api` is documented as the public surface, so a change to it is breaking. The first
release is an internal test for now.

## Decision

- The version stays `0.1.0`.
- `chancellor.api` is still documented as the public surface.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Under 0.x, breaking changes to `chancellor.api` remain possible before 1.0.

## References and Links

None.

## Notes

None.
