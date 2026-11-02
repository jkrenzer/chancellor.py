---
title: Record-Set Version, Versioning Scheme and Absolute IDs
id: S0008
addresses:
  - R0024
short_title: Versioning and Absolute IDs
description: >-
  Where chancellor keeps the record-set version, how a configured scheme validates versions, and how
  absolute IDs refer to records from outside the record set.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:213461abb9b066e8a6b8bf3e400e6a852a7540d8fe3d1902f6d7ed5ac6d060d6
---

## Context

Chancellor's versioning support is scheme-neutral: a project chooses its scheme and policy, and
chancellor validates and exposes what the project configured.

## Subject

- The `meta` facet of the data tree, `config.<key>.versioning`, the validation of versions, and
  absolute IDs.
- Excluded: a project's choice of scheme and increment policy.

## Terms

- Record-set version: `meta.<key>.version`, the version of the record set as a whole.
- Scheme: a `VersionScheme` type that parses and orders versions, such as `semver`, `pep440` or
  `free`.
- Bare reference: a record ID alone; it means the current record-set version.
- Absolute ID: a record ID combined with the record-set version in the configured format.
- Historic reference: an absolute reference with a version older than the current record-set
  version.

## Specification

### Meta facet

- `meta.<key>.version` holds the record-set version; `<key>` is chancellor's module key, as for
  `_api` and `config`.
- `ProjectModel` has a `meta` field with public bases, so a supplied root model inherits it.

### Versioning configuration

- `config.<key>.versioning.scheme` names a version scheme; the built-ins are `semver`, `pep440` and
  `free`, and `free` is the default.
- `config.<key>.versioning.absolute_id` is the absolute-ID format with the fields `{version}` and
  `{id}`; the default is `"{version}:{id}"`.

### Validation

- Under `free`, versions are checked only by the record model's own rules.
- Under a known scheme, the record-set version and every revision version parse under the scheme,
  and revision versions increase from oldest to newest.
- Version schemes are an extension point: a provider may contribute one, resolved through the
  registry like any other type; `pep440` uses the `packaging` library.

### References

- Inside the record data, a reference is bare or absolute; a bare reference means the current
  record-set version.
- An absolute reference with the current version is checked like a bare one; one with a newer
  version is invalid input.
- An absolute reference with an older version is historic: it is not resolved, it is a warning
  rather than an error, `doctor` lists it, and templates see it marked `historic`.
- A version increment turns current absolute references into historic ones by itself.
- References from outside the record set use absolute IDs.
- A historic ID given on the command line is a warning; the command proceeds on the current record
  of that ID if it exists.
- In a local absolute ID, the part before the ID parses as a version of the configured scheme; an
  external reference names its project, as `<project>:<version>:<id>`, or is a URL.

### Templates and digest

- Templates see the record-set version, each record's absolute ID, and whether a reference is
  historic.
- The record-set version and the absolute-ID format enter every document's digest, so an increment
  rebuilds every document.

## Conformance

- Not implemented yet: the tests come with the data model support.

## References and Links

- **Governing decision**:
  - [D0036: Versioning Mechanism](../decisions/D0036-versioning-mechanism.md)
  - [D0029: Usage Errors and Ref Resolution](../decisions/D0029-usage-errors-and-ref-resolution.md)

## Notes

None.
