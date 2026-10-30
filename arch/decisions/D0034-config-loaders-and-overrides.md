---
title: Resolve Configuration Loaders Through the Registry and Accept Command-Line Overrides
id: D0034
addresses:
  - R0012
short_title: Config Loaders and Overrides
description: >-
  Proposed: `config/chancellor/loaders` names the loaders by type, and `--set KEY=VALUE` overrides a
  setting for one run, recorded in the lock.
tags: []
author: jkrenzer
date: '2026-10-30'
state: proposed
version: 0.1.0
revisions:
  - version: 0.1.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:c14b5b9062060b8dbe0638845a19d1e44133d6da5d97eaec5a18f727c39ecc09
---

## Context

Configuration arrives through a loader interface (R0012), but a loader that is hard-wired instead of
resolved like every other type cannot be replaced, and the command-line source of the documented
source order did not exist.

## Decision

- `config/chancellor/loaders` lists loader types, default `["builtin.data_file"]`, resolved through
  the registry or as an import path; it is a layout key and not digested.
- A loader is constructed with a `LoaderContext` and its arguments; a loader that fails exits 1
  naming its entry.
- The global option `--set KEY=VALUE`, repeatable, overrides a setting below `config/chancellor`
  with the highest priority; the value is parsed as YAML without tags, anchors or aliases.
- Overrides are logged at INFO level and recorded in the lock, and `explain` names them under
  `config`.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- A loader's code fingerprint joins the providers part (D0018).
- A build with `--set` moves the configuration digest, so the next build without it rebuilds again.

## References and Links

None.

## Notes

None.
