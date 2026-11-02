---
title: Unreliable Fingerprints Are Recorded as Degradations
id: R0009
addressed_by:
  - D0017
  - D0021
  - D0031
  - S0006
short_title: Degradations
description: >-
  An input chancellor cannot fingerprint reliably is recorded per build in the lock and fails
  `--strict`; an outdated lock is rebuilt, never an error.
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
data_hash: c1:sha256:7c60aa750b326735603397b2179c172d0300f3110cac9d523dfa10c36f182096
---

## Context

Code that can change without its version changing, such as a loose module or a provider without a
version, makes a build irreproducible unless chancellor hashes it completely.

## Requirement

- A provider with no reliable version that cannot be hashed completely is a degradation, recorded
  per build in the lock, counted by one handler and failing the build under `--strict`. One that is
  hashed completely raises an INFO message instead.
- A lock written by a version that knew nothing of providers, or with another `_api` version, is
  ignored and rebuilt.

## Goals

- CI from a built wheel can prove a build reproducible with `--strict`.

## Stakeholders

- CI pipelines of consuming projects.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
