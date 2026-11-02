---
title: Increment Policy for Record Revisions and the Record Set
id: S0009
addresses:
  - R0024
short_title: Version Increment Policy
description: >-
  When this project increments a record's revision version and the record-set version, and by which
  category.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:347a48d37084ad4b174a7973bfe6c73a12fed2d439d63813d1de5b0f3eecc0e9
---

## Context

The rules apply to this project's records and record set under SemVer (S0010).

## Subject

- Increments of record revision versions and of the record-set version in this project.
- Excluded: the format of versions (S0010) and how chancellor validates them (S0008).

## Terms

- Category: MAJOR, MINOR or PATCH.
- Published state: the records as committed to the project's shared history or released.
- Batch: the record changes between two published states.

## Specification

### Published states

- Increments mark published states. A version is incremented when a change is first published,
  meaning committed to the project's shared history or released, not for each edit made while
  working.
- All changes between two published states are folded into a single increment, chosen by the highest
  category among them.
- Published versions therefore follow each other without gaps.

### MAJOR

MAJOR applies when an absolute ID would now lead a reader astray.

- A record is removed, or its ID is reused for different content.
- An accepted record's meaning is reversed or contradicted: a decision reversed, an obligation
  dropped or inverted.
- A requirement or specification is narrowed so that conforming work no longer conforms.

### MINOR

MINOR applies when content is added or firmed up without invalidating what an absolute ID said.

- A new record.
- A new obligation, alternative, consequence or clause.
- A state change that commits further, such as `proposed` to `accepted`.
- A record marked `superseded` or `deprecated` while kept.

### PATCH

PATCH applies to corrections that do not change meaning.

- Typos, wording, formatting, links, dates, tags, metadata and revision-history fixes.

### No increment

- Re-rendered documents whose record data is unchanged, after a template, formatter, chancellor or
  library upgrade.
- Layout changes: moving records between data files, `include`, `kinds.<kind>.data`, output folders.
- Configuration, lock and provider changes.
- A record's revision adds no record-set increment of its own; the coupling rules decide.

### Coupling

- A record's own revision version follows the same rules, applied to that record.
- The record-set version moves by the highest category among the record changes since the last
  record-set version.
- Between two published states, the record set makes one increment, by the highest category among
  the record changes.

### Initial development

- While the major version is 0, MAJOR-category changes increment MINOR and all others PATCH.
- The record set goes to `1.0.0` together with chancellor's first final release.
- A version never goes back; a released `<version>:<id>` stays valid in history.

## Conformance

- Reviewers check each batch's increment against these rules; no tool checks the category.

## References and Links

- **Governing decision**:
  - [D0038: Version Increment Policy](../decisions/D0038-version-increment-policy.md)

## Notes

None.
