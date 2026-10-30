---
title: A Record's Data Hash Covers Its Own Data Only
id: R0007
addressed_by:
  - D0006
  - S0003
  - S0006
short_title: Data Hash Scope
description: >-
  `data_hash` is the digest of the record's own canonical data, the same standalone and in the
  project, and never includes the schema that validated it.
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
data_hash: c1:sha256:ae2fd13b85c15478686a594fa03f1dc51c22811db79ed39ff8270b86d2340e2e
---

## Context

A hash over the whole data tree in every document would make any edit rewrite every document. A
per-record hash keeps edits local.

## Requirement

- `data_hash` is identical whether the record is hashed standalone or from the complete data tree.
- A change to a kind definition does not change the `data_hash` of records of that kind.

## Goals

- Editing one record changes only that record's hash.

## Stakeholders

- Reviewers, who see one changed hash per changed record.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
