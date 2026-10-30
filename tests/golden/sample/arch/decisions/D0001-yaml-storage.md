---
title: Store the Sample Data as YAML
id: D0001
addresses:
  - R0001
short_title: YAML Storage
description: The sample data is kept in YAML files under version control.
tags:
  - storage
  - area: data
author: sample-team
date: '2026-10-02'
state: accepted
version: 1.1.0
revisions:
  - version: 1.0.0
    date: '2026-10-02'
    description: Initial record.
  - version: 1.1.0
    date: '2026-10-05'
    description: Clarify the alternatives.
data_hash: c1:sha256:5293a7a4b6ec0b43328e6e50b517859ecacf080072a16d16930e264dabd44aa6
---

## Context

The sample project needs a storage format that people can review in pull requests and that tools can
validate before anything is rendered. Binary formats and databases make review hard.

## Decision

- Keep all sample data in YAML files.
- Validate every file against the models before rendering.
  - Invalid files fail the build.

## Alternatives Considered

- JSON is equally strict but harder to comment, so it was rejected.

## Consequences

- Reviews show data changes line by line.
- Authors have to quote version strings.

## References and Links

- **Addressed requirements**: The requirement this decision answers.
  - [R0001: Reviewable Data](../requirements/R0001-reviewable-data.md)
- **YAML specification**.

## Notes

None.
