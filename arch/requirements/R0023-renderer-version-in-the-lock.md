---
title: The Lock Records the Exact Renderer Version
id: R0023
addressed_by:
  - D0017
  - S0006
short_title: Renderer Version in the Lock
description: >-
  The lock records which chancellor version produced the documents, including the commit for
  unreleased builds, and the documents never contain it.
tags:
  - area: hashing
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:f609f62c983b7a8ae7eb61632a56939d8413e644916c260ab37fe235d67c9110
---

## Context

poetry-dynamic-versioning gives every build a PEP 440 version, such as `0.1.1.dev3+g9f2c1ab` between
releases. A lock should trace back to the renderer source.

## Requirement

- The lock records `chancellor.__version__` unchanged, PEP 440 dev and local parts included.
- The version enters only the lock and other metadata, never a rendered document.
- An editable install, whose version may be stale, is handled by a documented rule.

## Goals

- A lock can be traced to the exact renderer source that wrote it.

## Stakeholders

- Maintainers auditing generated documents.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
