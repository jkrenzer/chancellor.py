---
title: Canonicalize With JCS and Tag Every Digest
id: D0006
addresses:
  - R0021
  - R0007
short_title: JCS Canonical Form
description: >-
  Canonical bytes are JCS (RFC 8785) over the validated dump with defaults filled, and digests are
  written `c1:sha256:<hex>`.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:cbb5d0ec40c2a141fb5ef1e6f911a01a0edef8dbcadb0a80fc9d371efbabe02f
---

## Context

Hand-rolled canonicalizers, such as `json.dumps` with sorted keys, break at key sorting and number
formatting, and a digest prefix that names no rules cannot change them safely.

## Decision

- Produce canonical bytes with the `rfc8785` package from the validated dump with defaults filled.
- Normalize strings to NFC and multi-line values to LF; never strip trailing whitespace; refuse
  floats.
- Declare digest exclusions on the model with a marker, never in a list beside it.
- Tag digests with the spec, `c1:sha256:`, and rebuild on an unknown tag.

## Alternatives Considered

- A hand-rolled `json.dumps` with sorted keys: rejected for number formatting and key-order edge
  cases.

## Consequences

- `rfc8785` becomes a runtime dependency (D0011).
- A future change of the canonical form bumps the tag to `c2` and rebuilds everything once.
- Repositories still set `* text=auto eol=lf` in `.gitattributes`, so rendered documents keep LF
  line endings on every platform.

## References and Links

- **Specification**:
  - [S0003: Canonical Form and Digests](../specifications/S0003-canonical-form-and-digests.md)
- **RFC 8785**: JSON Canonicalization Scheme (JCS).

## Notes

None.
