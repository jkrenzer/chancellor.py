---
title: Chancellor Ships Ready-to-Use Kinds for Decision, Requirement and Specification Records
id: R0001
addressed_by:
  - D0001
  - D0013
  - D0016
  - S0007
short_title: Built-In Record Kinds
description: >-
  Chancellor ships decision, requirement and specification kinds with their core documents, strict
  validation and lint-clean rendering, usable from an empty configuration.
tags:
  - area: records
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:99a4bd4f36737f17f9468575c7222afef8b8997701c727c877d58e77fb956a95
---

## Context

Architecture records are useful when they look the same across a project and can be checked by
tools. Chancellor's first purpose is to keep decision, requirement and specification records as
validated data and render them into Markdown documents, without a project writing models or
templates of its own.

## Requirement

- Chancellor ships decision, requirement and specification kinds, each with a core document that
  introduces the kind's folder, states its rules and indexes its records, as the built-in provider
  `builtin.jkrenzer` loaded from package resources.
- An empty configuration renders the three kinds into `arch/decisions`, `arch/requirements` and
  `arch/specification`.
- Validation is strict: missing required values, blank text, wrong types, unknown field names and
  malformed nested entries fail, and every violation is reported in one run.
- Optional values that are omitted, null or blank mean "not given", null lists mean empty, and
  validation never mutates the input.
- Revisions are non-empty, oldest first and unique by version; the last revision gives the record's
  version.
- Every model field carries a description written for human authors and AI agents.
- Rendered documents wrap at the configured width, keep their Markdown structure, keep long
  indivisible content whole and pass a Markdown linter at the default width.
- A record rendered on its own carries its own data hash.
- Guidance the built-in kinds give authors ships with the provider and points into no other
  repository.
- Revision versions follow the project's configured versioning scheme (R0024).

## Goals

- A project documents its architecture with chancellor from an empty configuration.
- Authors and AI agents learn the accepted inputs from the schema alone.

## Stakeholders

- Projects that document their architecture as records.
- Authors and AI agents writing records, who rely on clear validation messages.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
