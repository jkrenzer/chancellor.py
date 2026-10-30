---
title: Formatter and Linter Are Configured by Type
id: R0018
addressed_by:
  - D0008
  - D0011
  - S0002
  - S0005
short_title: Formatter and Linter Types
description: >-
  The formatter and the linter are configuration resolved as types through the registry; chancellor
  hard-wires neither and records what the linter reports.
tags:
  - area: formatting
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:94c8acd52a1c62c04c5da99d484929c50c2f4ccd04f054d41540c0a4a7e9fce0
---

## Context

Markdown that lints clean is one project's workflow, not chancellor's business: another consumer may
emit HTML or use another checker.

## Requirement

- `config/chancellor/linter` names a type and its arguments: `builtin.shell`, `builtin.python` and
  `builtin.none` ship, and plugins may contribute more.
- `builtin.shell` runs an argv list without a shell and without record content in the command;
  `builtin.python` takes an import path, a callable and parameters.
- `builtin.none` is the default, and under it `lint` fails with "No linter set" and a code distinct
  from "the linter found problems".
- The linter is run, not trusted: its exit status and output are recorded and neither is part of
  what chancellor wrote. Under MCP the shell type runs only in a tier that permits execution.
- The wrap width is a key in `config/chancellor`; `doctor` compares it with `[tool.pymarkdown]`
  where that exists.
- `config/chancellor/formatter` selects `builtin.mdformat` (the default), `builtin.none` or a plugin
  type.
- `render --lint` runs the configured linter on the rendered document; its findings exit 5.

## Goals

- pymarkdownlnt and application-properties leave chancellor's runtime dependencies.

## Stakeholders

- Consuming projects with their own lint workflow.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

Only `builtin.none` exists among the linter types so far.
