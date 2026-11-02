---
title: Exit Codes of Every Chancellor Command
id: S0005
addresses:
  - R0018
  - R0020
short_title: Exit Codes
description: The seven exit codes every chancellor command returns and what each means.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:665e029aca99d09d875b87675f3ca2a145e4bd1fe924feaf7ce64ab56ec4090d
---

## Context

Scripts, hooks and CI react to chancellor by its exit code.

## Subject

- The process exit code of the `chancellor` console script.
- Excluded: messages on stderr, which may change.

## Terms

- Drift: a document whose bytes or inputs differ from what the data and the lock say it should be.
- Degradation: a build input chancellor cannot fingerprint reliably.

## Specification

### Codes

- 0: success.
- 1: configuration error, including `builtin.none` under `lint`, command-line misuse (D0029) and
  problems `doctor` finds outside the record data, such as untracked documents (D0035).
- 2: record data invalid: duplicate IDs, also across files, dangling refs, one-sided links found by
  `doctor`, a record failing its model.
- 3: `--check` found drift.
- 4: `--strict` found degradations.
- 5: the linter reported problems.
- 6: internal error.

### Documentation

- The table appears in the CLI help, and each command's help names the codes it can return.

## Conformance

- `tests/test_cli.py` asserts each code.
- `chancellor --help` shows the table.

## References and Links

- **Governing decision**:
  - [D0010: Seven Exit Codes](../decisions/D0010-seven-exit-codes.md)
  - [D0029: Usage Errors and Ref Resolution](../decisions/D0029-usage-errors-and-ref-resolution.md)

## Notes

None.
