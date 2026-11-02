---
title: A Consumer May Supply Its Own Root Model
id: R0015
addressed_by:
  - D0030
  - S0002
  - S0004
short_title: Supplied Root Model
description: >-
  A project may validate its data with its own Pydantic root model under a documented protocol,
  inheriting chancellor's fields and defaults.
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
data_hash: c1:sha256:388cce6b9944fe0874d446a5891e9a3330925c8a81cbc4ee5a765df69b3f2c95
---

## Context

Some projects already have a data model for their records and should not have to duplicate it in
provider declarations.

## Requirement

- The root-model contract is a documented Protocol in `chancellor.api`: it exposes sections, the
  records in each, and per record its ID, kind, data and refs; chancellor supplies canonicalization,
  hashing, ref extraction and rendering.
- A supplied root model inherits from chancellor's base classes, which bring every field and its
  default, configuration included; output folders stay configurable alongside it.

## Goals

- A supplied root model renders a fixture to the same bytes as the generated model.

## Stakeholders

- Projects with an existing data model.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
