---
title: SemVer 2.0.0 for Record Revisions and the Record Set
id: S0010
addresses:
  - R0024
short_title: SemVer Versions and Absolute IDs
description: >-
  This project's versions of records and of the record set, and the form of its absolute IDs.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:8ec383aee5095471da1021320bb2be1ffd35fca0c5b36944cf60018d92427d59
---

## Context

This project uses the `semver` scheme of S0008 with the default absolute-ID format.

## Subject

- Revision versions of this project's records, its record-set version and its absolute IDs.
- Excluded: chancellor's own distribution version.

## Terms

- SemVer: Semantic Versioning 2.0.0.

## Specification

### Versions

- Every revision version and the record-set version is a SemVer 2.0.0 version, written as a quoted
  string in the data.
- The configured scheme is `semver`.
- The initial record-set version is `0.1.0`.

### Absolute IDs

- An absolute ID is written `<version>:<id>`, for example `0.1.0:D0017`.
- Code, tests, documentation, commit messages and other projects refer to records by absolute ID.

## Conformance

- Once the scheme is configured, `chancellor build` validates every version; until then reviewers
  check.

## References and Links

- **Governing decision**:
  - [D0037: SemVer for Records](../decisions/D0037-semver-for-records.md)

## Notes

`meta` and `versioning` are not configured in this repository yet; the data model support is
pending.
