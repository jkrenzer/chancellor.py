---
title: Accept an Editable Install Whose Changes Chancellor Detects
id: D0017
addresses:
  - R0009
  - R0023
short_title: Editable Install Detected
description: >-
  An editable install of chancellor is no degradation when its code changes are caught by the source
  digest; `--strict` means fully reproducible.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:bf6a1e53bd67256be86c814691c2154a088b5773ba742ec4e5c32d3fc87d95e6
---

## Context

An editable install reports the version of its last installation, so after more commits the version
names the wrong code. Chancellor now adds a digest of the package source to the fingerprint of an
editable install, so a code change is detected and rebuilds what it feeds.

## Decision

- An editable install whose code changes are caught by the source digest is no degradation;
  chancellor logs it at INFO level.
- `--strict` means fully reproducible: equal digests yield equal output.

## Alternatives Considered

- Treat every editable install as a degradation, so `--strict` fails in every development checkout.
- Probe git at runtime when running from a checkout; it would have to degrade silently where git is
  missing.
- Refuse or warn when the checkout's HEAD differs from the installed version's commit.

## Consequences

- The `api` digest part covers the Python implementation and its major.minor version and the
  installed versions of the libraries that shape output, so equal digests mean equal output.
- An editable install whose source digest is incomplete, for example because of compiled extensions
  or unreadable files, records `editable-install` with the reason.
- A development checkout passes `--strict`.

## References and Links

None.

## Notes

None.
