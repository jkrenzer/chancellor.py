---
title: Version the Record Set in a meta Facet With a Configurable Scheme
id: D0036
addresses:
  - R0024
short_title: Versioning Mechanism
description: >-
  Chancellor keeps the record-set version in a `meta` facet, validates versions through a pluggable
  version scheme that defaults to no checks, and resolves bare and absolute references.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:6972de889c7582897224356d0eef9a50fcf02a5f9fadc0093818e0223b8fc852
---

## Context

Records carry revision versions, but chancellor treats them as opaque strings, and the record set as
a whole has no version. `_api.chancellor.version` is the version of the data-file format, not of the
records.

## Decision

- The record-set version lives in a data facet, `meta.<key>.version`, scoped by module key like
  `_api` and `config`; it describes content, so it is data, not configuration.
- How versions are written is project policy, set in `config.<key>.versioning`: a `scheme` and an
  `absolute_id` format (default `"{version}:{id}"`).
- Version handling is an extension point: a scheme is a `VersionScheme` type resolved through the
  registry; the built-ins are `semver`, `pep440` (through `packaging`) and `free`, the default,
  which checks nothing.
- A known scheme validates the record-set version and every revision version, and checks that
  revision versions increase from oldest to newest.
- Inside the record data, a bare reference means the current record-set version. An absolute
  reference with the current version is checked like a bare one; one with an older version is
  historic; one with a newer version is invalid.
- A historic reference cannot be resolved: it is a warning, not an error; `doctor` lists it and
  templates see it marked `historic`. A version increment turns current absolute references historic
  by itself.
- A historic ID given on the command line is a warning, and the command proceeds on the current
  record of that ID if it exists.
- A local absolute ID's first part parses as a version of the configured scheme; an external
  reference names its project, as `<project>:<version>:<id>`, or is a URL.
- `ProjectModel` gains a `meta` field with public bases, and templates see the record-set version
  and each record's absolute ID.

## Alternatives Considered

- Only bare references inside the record data: not chosen, because absolute references let a version
  increment mark what they cite as historic.
- Digesting the version only for documents that show it: rejected, because rebuilding every document
  is more robust and easier to check.
- One fixed scheme for every project: rejected, because projects keep their own versioning policies.
- The record-set version in configuration: rejected, because it describes content.

## Consequences

- The record-set version and the absolute-ID format enter every document's digest, so a version
  increment rebuilds every document.
- Editors can screen for historic references after an increment, and templates can mark them.
- `packaging` becomes a runtime dependency (D0011).
- `_api.chancellor.version` stays the version of the data-file format.

## References and Links

- **Specification**:
  - [S0008: Versioning and Absolute IDs](../specifications/S0008-versioning-and-absolute-ids.md)

## Notes

The data model support is not implemented yet.
