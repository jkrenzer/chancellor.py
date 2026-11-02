---
title: Keep the Runtime Dependencies Small and Free of PyYAML
id: D0011
addresses:
  - R0018
  - R0021
short_title: Runtime Dependencies
description: >-
  mdformat and `rfc8785` are required, pymarkdownlnt and application-properties are dropped, and
  YAML is read and written with ruamel.yaml only.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:45f19e9e299505a006189b18ce100f73bd7b3a4bb52cb860200180c9f38085be
---

## Context

Once the linter is the consumer's own command, chancellor no longer needs pymarkdown. mdformat
shapes the bytes chancellor writes and must stay.

## Decision

- Runtime dependencies include mdformat, mdformat-gfm, `rfc8785` and pydantic-settings.
- pymarkdownlnt and application-properties leave the runtime dependencies; pymarkdownlnt stays a dev
  dependency.
- YAML is read and written with ruamel.yaml only; chancellor's code never imports PyYAML, even where
  an optional extra pulls it in, and a test checks that.
- `packaging` is a runtime dependency, for the built-in `pep440` version scheme.

## Alternatives Considered

- The `pydantic-settings[yaml]` extra: rejected, because it brings PyYAML.

## Consequences

- Chancellor needs its own pydantic-settings source on ruamel.yaml.
- If mdformat ever moves to an extra, the default formatter becomes `builtin.none`.

## References and Links

None.

## Notes

None.
