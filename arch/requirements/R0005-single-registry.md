---
title: One Registry Resolves Every Kind and Reports What Was Loaded
id: R0005
addressed_by:
  - D0002
  - S0001
short_title: Single Registry
description: >-
  One registry is the only lookup from a kind to its provider, model, templates, defaults and
  folders, and `chancellor providers` shows what it holds.
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
data_hash: c1:sha256:45b6713f1e9cefc457572170c848974ee09acfcfd9e69ab4d1a42acb9de09de5
---

## Context

When several places resolve kinds, folders and paths, they drift apart, and a wrong resolution is
invisible unless it can be listed.

## Requirement

- Nothing outside the registry resolves a kind.
- `chancellor providers` lists every loaded provider with name, origin, fingerprint and contributed
  kinds.
- `doctor` reports a provider declared in configuration but absent on disk.

## Goals

- A wrong provider resolution is visible from one command.

## Stakeholders

- Maintainers debugging a project's provider set.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
