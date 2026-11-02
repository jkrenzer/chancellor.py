---
title: Declare on Each Reference What Flows Over It
id: D0032
addresses:
  - R0004
  - R0008
  - R0019
short_title: Reference Dependencies
description: >-
  A reference declares with `depends` whether its document reads the target's ID, its file name or
  its data, and only that can rebuild the document or reach its template.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:44939ad0050c425be11b97ed4e60ddc69fed5f6dc4959d69b929359a7901d2eb
---

## Context

Hashing every record reachable through references moved core documents whose text could not differ
when one requirement changed. The maintainer's principle: "If it is e.g. just a reference to the
file name which stays the same while the content changes, the document does not need to rebuild. If
the document reads data from a source that changes it has to be rebuild, too to ensure the changes
are reflected in any imported data. So it depends on the type of reference connection and if the
changes in the referenced document can flow over this connection or not."

## Decision

- A reference is declared as `RecordRef(depends="id"|"name"|"data")`, default `id`; a declarative
  field takes `depends:` likewise. A parameter only, no aliases.
- `id`: the target's ID only; `name`: also its document's file name and path; `data`: also its
  serialized data.
- Templates see other records only under `refs.<field>`, exactly as declared, so a template cannot
  read what the digest does not cover.
- The `refs` digest part covers exactly that context plus the record's `Generated` fields, such as a
  core document's index.

## Alternatives Considered

- Hashing every record reachable through references: rejected, because it rebuilds documents that
  cannot change.

## Consequences

- `refs` and `data_hash` are reserved field names.
- In this repository, changing a requirement's `state` moves only that requirement; its
  `short_title` moves it and its core document.

## References and Links

None.

## Notes

None.
