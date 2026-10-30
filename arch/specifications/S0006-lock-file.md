---
title: Lock File and Document Input Hash
id: S0006
addresses:
  - R0006
  - R0007
  - R0008
  - R0009
  - R0023
short_title: Lock File
description: >-
  Structure of the lock file and the digest parts of a document's `input_hash` that decide whether a
  document is rebuilt.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:65dda06a83be1be309d82c88df78abe920609200eb029ec2ccb42fe1d7fbea20
---

## Context

The lock records what the last build saw, so the next build rebuilds exactly what changed and
`explain` can say why.

## Subject

- The lock file, `chancellor.lock` by default, and the digest parts it stores per document.
- Excluded: the rendered documents, which carry only their record's `data_hash`.

## Terms

- `data_hash`: the digest of a record's own canonical data.
- `input_hash`: the digest over all digest parts of one document.
- Feeding provider: a provider contributing the kind, a template in the closure, the formatter or
  the root model of a document.

## Specification

### Lock structure

```json
{
  "_api": {"kind": "chancellor_lock", "version": "2"},
  "renderer": "0.1.0",
  "environment": {"api": "c1:sha256:…", "config": "c1:sha256:…", "providers": "c1:sha256:…",
                "fingerprints": {"builtin.jkrenzer": "0.1.0"}},
  "providers": [{"name": "builtin.jkrenzer", "origin": "chancellor", "type": "code",
                 "fingerprint": "0.1.0", "kinds": ["decisions"]}],
  "degradations": [],
  "documents": {}
}
```

- The lock is JSON with sorted keys and two-space indentation, ending with a newline.
- `_api` is `{kind: chancellor_lock, version: "2"}`.
- `renderer` is chancellor's distribution version, unchanged; in an editable install the renderer
  fingerprint also carries a digest of the package source (D0017, D0031).
- `environment` holds the `api`, `config` and `providers` digests and the whole fingerprint map
  under `fingerprints`.
- `providers` lists the resolved provider set: name, origin, type `code` or `declarative`,
  fingerprint and contributed kinds.
- `degradations` lists each degradation of the build with code, subject and message.
- `documents` maps each output path to its ID, kind, part (`records` or `core_document`),
  `data_hash`, `input_hash`, digest `parts`, the digest of the bytes written as `output`, and its
  source data files.
- `cli_overrides` records the settings overridden with `--set` for the build. - Note: proposed in
  D0034.

### Digest parts

- `data`: the record's own `data_hash`.
- `refs`: per reference field, what its `depends` exposes of each target (`id`; `id`, file name and
  path; or those plus the target's data), plus the record's `Generated` fields, such as a core
  document's index context (D0032).
- A target's own references are neither exposed nor digested (D0033).
- `files`: bytes of hashed file refs.
- `templates`: source strings of every template reachable from the document's template.
- `config`: the digest of the whole validated `config/chancellor`, without the layout keys `include`
  and `kinds.<kind>.data` (D0020).
  - Note: `loaders` is excluded as well; proposed in D0034.
- `api`: the data-tree format version and the renderer fingerprint: chancellor's version, plus its
  source digest in an editable install, the Python implementation and major.minor version, and the
  installed versions of the libraries that shape output (D0017).
- `providers`: one digest per build over the provider set and every fingerprint: providers,
  `data_model`, `model:<kind>`, `code:<address>` and `schema:<kind>` (D0018).

### Reading a lock

- A lock that cannot be read, or carries another `_api` version, is ignored and everything is
  rebuilt.
- A document is rebuilt when any stored part differs, is missing or carries an unknown digest tag.
- Deleting the lock and building yields the same documents as an incremental build.
- A document in the lock that no record produces any more is an orphan: removed when the file is
  still what chancellor wrote, reported and kept otherwise.
- The document paths of an unusable lock are read best effort; those still on disk are reported as
  orphans and never deleted.
  - Note: proposed in D0035.
- A file in a kind's output folder named like a record of that kind and unknown to the plan and the
  lock is untracked: `build` warns and keeps it, and `doctor` reports it as a problem.
  - Note: proposed in D0035.

## Conformance

- `tests/test_build.py` covers cold and incremental builds, `explain` and degradations.
- This repository: `chancellor build --check` after deleting `arch/chancellor.lock` reports no
  changed document.

## References and Links

- **Governing decision**:
  - [D0003: Coarse Environment Digest](../decisions/D0003-coarse-environment-digest.md)
  - [D0018: Whole-Set Provider Part](../decisions/D0018-whole-set-provider-part.md)
  - [D0017: Editable Install Detected](../decisions/D0017-editable-install-detected.md)
  - [D0020: Config Digest by Chancellor](../decisions/D0020-config-digest-by-chancellor.md)
  - [D0032: Reference Dependencies](../decisions/D0032-reference-dependencies.md)
  - [D0035: Unvouched Documents Kept](../decisions/D0035-unvouched-documents-kept.md)

## Notes

The `files` part digests an empty list until a marker for hashed file refs exists.
