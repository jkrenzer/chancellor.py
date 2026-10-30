---
title: Scope the Data Tree by Facet and Rename Its Kind to project_records
id: D0012
addresses:
  - R0010
  - R0013
short_title: Facet-Scoped Data Tree
description: >-
  The data tree is scoped by facet with chancellor's keys under `_api/chancellor` and
  `config/chancellor`, its kind is `project_records`, and the old layout gets no shim.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:ef90c780af60fe491f23ccb5eb95f4d25bb3c952d462a936c103db917990f553
---

## Context

Other tools, such as field-marshall, read the same requirements chancellor renders. An unscoped
layout, or a data-tree kind named after architecture records only, would tie the shared data to
chancellor and to its first document type.

## Decision

- Top-level keys are `_api/<module>`, `config/<module>` and one section per record kind.
- `_api/chancellor.kind` is renamed to `project_records` now.
- Data in an unscoped layout gets no compatibility path; it is refused.
- The module key is a module-level default plus a mapping of per-facet overrides.

## Alternatives Considered

- A compatibility shim for the unscoped layout: rejected, because no released data uses it.

## Consequences

- The unscoped layout is refused with a message naming the new shape.

## References and Links

- **Specification**:
  - [S0002: Project Data Tree](../specifications/S0002-project-data-tree.md)

## Notes

None.
