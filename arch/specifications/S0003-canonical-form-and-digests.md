---
title: Canonical Form and Digest Format
id: S0003
addresses:
  - R0007
  - R0021
short_title: Canonical Form and Digests
description: The canonical bytes behind every chancellor digest and the written form of a digest.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:54f771162dc3243dfb6176c31b86e9e0f9ba5f4a37817d9c027204c6b5f0491f
---

## Context

Four callers depend on one canonical form: record data, the configuration subtree, a model's emitted
JSON Schema and a provider manifest.

## Subject

- The function from JSON data to canonical bytes, and the digest written from those bytes.
- Excluded: which fields a caller passes in; the models define that.

## Terms

- Validated dump: a model's JSON-mode dump after validation, with defaults filled.
- Spec tag: the leading name of the canonicalization rules, currently `c1`.

## Specification

### Input

- The input is the validated dump with defaults filled, never raw parsed YAML.
- Fields marked `DigestExclude` or `Generated` in `chancellor.api` are left out of a record's data.
- A key absent with a null default and an explicit null are both serialized as null.

### Normalization

- Strings are normalized to Unicode NFC.
- Line breaks inside strings are normalized to LF.
- Trailing whitespace is kept.
- Floats are refused; `Decimal` values arrive as strings.
- Mapping keys must be strings.

### Bytes and digest

- Canonical bytes are JCS, RFC 8785, as produced by the `rfc8785` package.
- A digest is written `c1:sha256:<hex>` with the full lowercase SHA-256 hex digest.
- A stored digest with another tag is never compared; the document is rebuilt.

## Conformance

- Test vectors in `tests/test_canonical.py` cover NFC, LF, floats, nulls and the digest form.

## References and Links

- **Governing decision**:
  - [D0006: JCS Canonical Form](../decisions/D0006-jcs-canonical-form.md)
- **RFC 8785**: JSON Canonicalization Scheme (JCS).

## Notes

None.
