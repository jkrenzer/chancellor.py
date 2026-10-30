---
title: Every Extension Point Is a Documented Abstract Class in chancellor.api
id: R0019
addressed_by:
  - D0001
  - D0009
  - D0024
  - D0025
  - D0032
  - S0004
short_title: Public Extension Interfaces
description: >-
  Formatter, linter, model, provider and config loader each have an abstract base class in
  `chancellor.api`, implemented by the built-ins too and documented as the public surface.
tags:
  - area: extension
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:aebb78b75c0c927a26b5c6524bf49ad2f3e360ba4af83e46bc3071f2b0cc182f
---

## Context

Configuration covers the common cases. Everything past them is a class the consumer writes, which is
cheaper to support than an option for every edge case.

## Requirement

- Every extension point has an abstract base class in `chancellor.api`, and the built-in types
  implement those same classes on no privileged path.
- Every point accepts a consumer's subclass named by import path and class; interfaces carry hook
  methods rather than switches.
- `chancellor.api` is documented as the public surface: every class with its contract, hooks and a
  minimal working subclass.
- The model interface has six hooks: loading, validation, canonicalization, indexing, serialization
  and saving.

## Goals

- Consumers extend chancellor without forking it.

## Stakeholders

- Plugin and provider authors.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

The `chancellor.api` reference documentation is not complete yet.
