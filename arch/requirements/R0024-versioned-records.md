---
title: Records and the Record Set Carry Versions That Keep References Unambiguous
id: R0024
addressed_by:
  - D0029
  - D0036
  - D0037
  - D0038
  - S0008
  - S0009
  - S0010
short_title: Versioned Records
description: >-
  Every record and the record set as a whole are versioned under a decided and specified versioning
  scheme and increment policy, so a reference to a record stays unambiguous over time.
tags:
  - area: records
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:d0045b7ccb98e269b1d69285ef6c1dec934081a227e50164681e14ddab7c9daa
---

## Context

Records change, and the set of records grows and changes as a whole. A reference written outside the
records, in code, documentation, a commit message or another project, must still lead to the content
it meant after the records have moved on.

## Requirement

- Every record carries a version that changes when the record changes.
- The record set as a whole carries a version.
- The versioning scheme and the policy for incrementing versions are decided and specified for the
  project.
- A reference from outside the record set identifies a record, and the version it refers to,
  unambiguously over time.
- Chancellor supports projects whose versioning scheme and policy differ from this project's.

## Goals

- An outside reference written today still identifies the same content after the record set moves
  on.
- A reader can tell from a version change how far a record's meaning may have moved.

## Stakeholders

- Authors of code, documentation and commit messages that refer to records.
- Other projects that refer to this project's records.
- Reviewers comparing record versions.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
