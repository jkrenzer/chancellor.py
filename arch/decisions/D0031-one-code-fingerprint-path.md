---
title: Fingerprint Code by Where It Comes From, Along One Path
id: D0031
addresses:
  - R0006
  - R0009
short_title: One Code Fingerprint Path
description: >-
  Every piece of Python code chancellor loads is fingerprinted by one function, by its distribution
  version, its source digest or its static import closure.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:519e41afeff0860cd5b57956fb9a6d8a6cab9524b04070394dea1a92feba51a2
---

## Context

Models, providers, overrides, loaders and root models arrive as installed distributions, editable
installs, files in the project or helper modules those files import. Fingerprinting only some of
them lets code change output unnoticed.

## Decision

- A module of an installed distribution is fingerprinted by the distribution's exact version string.
- In an editable install, the fingerprint is the version plus a source digest of the top-level
  package, and the build records an `editable-install` degradation.
- Any other module is fingerprinted by the digest of its own source and every module it imports,
  found statically without executing anything; the walk stops at the standard library, at installed
  distributions and at chancellor itself.
- An import that cannot be resolved, or whose name is computed, records an `unfingerprinted-code`
  degradation; an optional import guarded by `except ImportError` that does not resolve is recorded
  as absent.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- The Python version and files a module reads at runtime stay outside every digest.
- Model overrides in both forms and their helper modules are fingerprinted (D0025).
- The user documentation explains how chancellor fingerprints code.

## References and Links

None.

## Notes

None.
