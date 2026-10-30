---
title: Configuration Loads in Two Phases Through a Loader Interface
id: R0012
addressed_by:
  - D0004
  - D0020
  - D0034
  - S0002
short_title: Configuration Loading
description: >-
  Configuration arrives through a loader interface, is validated against one merged model built from
  the provider set, and rejects unknown keys with suggestions.
tags:
  - area: config
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:bff8e9c79e66b5e7e931f83ce2aed37ebe8e519d90ac85c6e31c6cc50f8d756e
---

## Context

Configuration may later come from a standalone file or `[tool.chancellor]`. Its schema depends on
the providers, but the provider list cannot depend on a provider.

## Requirement

- Configuration arrives through a loader interface, never a hard-wired file read. The first release
  ships one loader reading the data file. Sources are ordered once: CLI, environment, loaders in
  declared order, provider defaults, built-in defaults.
- Phase one reads `_api/chancellor` and the provider list against a fixed bootstrap schema; phase
  two validates all of `config/chancellor` against the merged model.
- The merged model is the only configuration schema; `chancellor schema config` prints it for the
  resolved provider set, and an unknown key is an error naming the loaded providers and the nearest
  valid keys.

## Goals

- New configuration sources are added without changing the loading code.

## Stakeholders

- Consuming projects choosing where their configuration lives.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
