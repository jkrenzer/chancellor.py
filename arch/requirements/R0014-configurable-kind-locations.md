---
title: Every Kind's Location Is Configurable With Provider Defaults
id: R0014
addressed_by:
  - D0019
  - D0035
  - S0002
short_title: Configurable Kind Locations
description: >-
  Each kind maps to exactly one configurable folder, falling back to its provider's default, and
  provider folders are never read as record data.
tags:
  - area: paths
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:e3b98cd475e240946102f236745421515ccb1cdb60db43c310a40310e4ca4b62
---

## Context

Projects lay out their documents differently; this repository uses `arch/specifications` where the
built-in default is singular. Output-path injectivity and orphan detection rest on one folder per
kind.

## Requirement

- The location of every kind is configurable; an omitted key falls back to the provider default.
- A kind maps to exactly one directory in this version; a list of folders is a later extension, not
  improvised with globs.
- Provider directories are never scanned as record data; the duplicate-ID pass and ref resolution
  run over the configured data only.

## Goals

- An empty configuration reproduces the built-in layout.

## Stakeholders

- Consuming projects with their own folder conventions.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

Record data is read from per-kind data files or the data tree; the folder is where documents go
(D0019).
