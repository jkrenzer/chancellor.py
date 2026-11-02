---
title: Rebuild Every Document After a Provider Change
id: D0018
addresses:
  - R0008
  - R0006
short_title: Whole-Set Provider Part
description: >-
  The providers part is one digest per build over the provider set and every fingerprint, so any
  provider change rebuilds every document.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:e2308a461b7a89119883c6d6a17179d426bcfcb67c6dcd51e45340921454eb9c
---

## Context

Rebuilding only the documents a changed provider feeds needs a per-document map of which provider
fed what, and that map is easy to get wrong. A needless rebuild is cheaper than a stale document
(D0003).

## Decision

- The `providers` part is one digest per build over the provider set and every fingerprint:
  providers, `data_model`, `model:<kind>`, `code:<address>` and `schema:<kind>`.
- The lock stores the whole fingerprint map, and `explain` names the entries that differ.

## Alternatives Considered

- A per-document provider part that rebuilds only the documents a changed provider feeds: first
  implemented, then reversed for simplicity.

## Consequences

- Any change of a provider or model rebuilds every document chancellor owns; the loaders proposed in
  D0034 would join the providers part.
- Lock entries carry no per-document list of feeding providers; the lock format version is 2.

## References and Links

None.

## Notes

None.
