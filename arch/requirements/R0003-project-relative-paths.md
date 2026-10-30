---
title: Paths Resolve Against the Consuming Project and Never Into Another Repository
id: R0003
addressed_by:
  - S0002
short_title: Project-Relative Paths
description: >-
  Chancellor finds the project root from the data file, keeps every configured path inside it, and
  publishes nothing that points into another repository.
tags:
  - area: paths
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:adc5c4a41dd449df2dc961001984424c28fe8823d348665d8d3ac24a7dd7d157
---

## Context

A tool installed as a package must not resolve paths against its own location, and guidance it
publishes must not point into a repository the reader does not have.

## Requirement

- The project root is found by walking up from the data file. Chancellor's own location and its own
  `pyproject.toml` never take part in path resolution.
- Where no `pyproject.toml` is found above the data file, the root of the git checkout is the
  fallback; that fallback has a test of its own.
- Configured paths resolve against the project root, are stored repo-relative in POSIX form and must
  stay inside the root; a path or symlink escaping it is an error with a clear message.
- The published JSON schemas and built-in templates contain no path into another repository.

## Goals

- Running chancellor from any folder of a project gives the same result.

## Stakeholders

- Consuming projects, whose locks and documents must not depend on where chancellor is installed.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
