---
title: Configure Formatter and Linter by Type With No Default Linter
id: D0008
addresses:
  - R0018
short_title: Formatter and Linter by Type
description: >-
  Formatter and linter are configured as types resolved through the registry; mdformat is the
  default formatter and the default linter is none, which makes `lint` fail.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:9da4d2ed2dc87a0d298715505e274bfbd438bb33fd94b24a000ac0bdc0552105
---

## Context

Wrapping and linting Markdown is one project's workflow, not chancellor's: another consumer may emit
HTML, pipe the output through pandoc or check it with something else.

## Decision

- Types `builtin.mdformat`, `builtin.shell`, `builtin.python` and `builtin.none` ship; plugins may
  add more.
- `builtin.mdformat` is the default formatter, because the built-in kinds must render correctly from
  an empty configuration.
- `builtin.none` is the default linter, and `lint` under it exits 1 with "No linter set".
- The wrap width becomes `config/chancellor/wrap_width`; `doctor` compares it with
  `[tool.pymarkdown]`.

## Alternatives Considered

- A built-in pymarkdown linter: rejected, because chancellor would hard-wire one consumer's
  workflow.

## Consequences

- A project points `builtin.shell` at its own lint task, such as `poe lint`.
- A script calling `lint` without a linter fails loudly instead of passing silently.

## References and Links

None.

## Notes

None.
