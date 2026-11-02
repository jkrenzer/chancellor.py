---
title: Model Generation and Check Commands Run From Chancellor and in Hooks
id: R0017
addressed_by:
  - D0007
short_title: Generator and Hooks
description: >-
  Schema-to-model generation runs through chancellor with documented settings, and the check forms
  of its commands ship as pre-commit hooks.
tags:
  - area: tooling
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:3c5dd36044164943f3def9b08a2d962e9fb64fc150b1ea18d69d5f48bae17731
---

## Context

Settings that make generated models reproducible should live in one place, and a project should keep
its documents in step with the data before a commit lands.

## Requirement

- The `[schema]` extra ships a plugin module exposing `chancellor model generate`, which owns the
  generator settings, `disable_timestamp` first.
- Every setting the plugin applies is documented in one table with the equivalent upstream CLI flag;
  a setting changed in the plugin and not in the table is a defect.
- `model generate` and the check forms of `build` and `lint` take staged files, exit non-zero on a
  difference and write nothing unexpected; chancellor ships the `.pre-commit-hooks.yaml` entries.

## Goals

- A consumer adds a `repo:` line instead of writing hook scripts.

## Stakeholders

- Schema-first projects and their CI.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

Not built yet.
