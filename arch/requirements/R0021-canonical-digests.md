---
title: Every Digest Is Made From One Specified Canonical Form
id: R0021
addressed_by:
  - D0006
  - D0011
  - D0020
  - S0003
  - S0004
short_title: Canonical Digests
description: >-
  Record data, the config subtree, model schemas and provider manifests are digested from one
  canonical byte form, with exclusions declared on the model and a tagged digest format.
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
data_hash: c1:sha256:211cf56f1c7c573a334d84b55dc62d0019996ad8d8938c68a83ee45f8dd65816
---

## Context

Hand-rolled canonicalizers break at key sorting and number formatting, and a CRLF checkout must not
move a digest.

## Requirement

- Canonical bytes are produced by one function from the validated dump with defaults filled, never
  the raw parsed input.
- Fields kept out of a digest are declared on the model with a marker from `chancellor.api`.
- A digest names the canonicalization spec that produced it, and one with an unknown tag rebuilds
  instead of being compared.

## Goals

- Equal content hashes equal on every platform and from every input form.

## Stakeholders

- Every consumer relying on incremental builds and reviewable hashes.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
