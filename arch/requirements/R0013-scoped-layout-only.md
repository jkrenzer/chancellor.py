---
title: The Unscoped Data Layout Is Refused Without a Compatibility Shim
id: R0013
addressed_by:
  - D0012
  - S0002
short_title: Scoped Layout Only
description: >-
  Only the scoped layout with `_api/chancellor.kind: project_records` is accepted; the old unscoped
  layout is refused with a message naming the new shape.
tags:
  - area: data-tree
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:d3bdf525f19270a6d382d600167750360c97288978ee544e41b5292e2dbfecc0
---

## Context

No released data uses the unscoped layout, so a shim would carry cost and no benefit.

## Requirement

- The data tree declares `_api.chancellor.kind` as `project_records`.
- The old unscoped layout fails to load with a message showing the new shape.

## Goals

- One layout to document, validate and test.

## Stakeholders

- Projects with data in the unscoped layout, which rewrite it once.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
