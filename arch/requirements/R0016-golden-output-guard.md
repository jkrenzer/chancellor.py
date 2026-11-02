---
title: Golden Fixtures Guard Rendered Output Between Versions
id: R0016
addressed_by:
  - D0022
short_title: Golden Output Guard
description: >-
  Chancellor's own synthetic records over every built-in kind and template are rendered and compared
  byte for byte with committed golden files.
tags:
  - area: testing
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:6ce9586d642ce67345d119b4e548377e83a7f4a344f6a0c90df59b5c1134b582
---

## Context

Consuming projects rely on the version to know when their documents may change. A change to
templates or rendering that alters output without a version bump breaks that silently.

## Requirement

- Fixture records in `tests/` cover every built-in kind and template; their committed renders are
  compared byte for byte.
- A documented task regenerates the golden files deliberately.
- On pull requests, CI fails when a golden file differs from the base branch and the package version
  was not bumped.
- The renderer version never appears in rendered documents.
- Rendered output does not depend on whether git is available.

## Goals

- No unintended output change reaches a release.

## Stakeholders

- Consuming projects upgrading chancellor.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

The CI version-bump check is not built yet.
