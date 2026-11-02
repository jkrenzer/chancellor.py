---
title: Built-In Record Kinds of builtin.jkrenzer
id: S0007
addresses:
  - R0001
short_title: Built-In Record Kinds
description: >-
  Fields, validation rules, core documents and rendering of the decision, requirement and
  specification kinds that ship as `builtin.jkrenzer`.
tags: []
author: jkrenzer
date: '2026-10-30'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-30'
    description: Initial record.
data_hash: c1:sha256:12a30830f62695cd056d67642bce1e9bc5cdb24dd369337ab803d0846addf233
---

## Context

The built-in provider is what a project gets from an empty configuration. Its models are the single
source of truth for the accepted inputs; this record states them in one place.

## Subject

- The decision, requirement and specification kinds of `builtin.jkrenzer`, their core documents and
  their rendered documents.
- Excluded: the data-tree layout (S0002) and the digests (S0003, S0006).

## Terms

- Record: one entry of a kind section's `records`.
- Core document: the one `core` entry of a kind section.
- Not given: an optional value that is omitted, null or blank.

## Specification

### Kinds and files

- The kinds are `decisions`, `requirements` and `specifications`, with the aliases `adr`, `arr` and
  `asr` for their records and `adr-core`, `arr-core` and `asr-core` for their core documents.
- The default output folders are `arch/decisions`, `arch/requirements` and `arch/specification`.
- Record IDs match `D####`, `R####` and `S####`; the core documents are `D0000`, `R0000` and
  `S0000`.
- A document's file name is `<id>-<short title in lower kebab case>.md`.

### Common fields

- Every record and core document has `title`, `id`, `description`, `author`, `state` and
  `revisions`; `short_title`, `tags` and `date` are optional.
- `short_title` defaults to `title` and `date` to the first revision's date; `version` is computed
  from the last revision.
- A tag is a nonempty string or a nonempty mapping of strings to strings.
- A revision has `version`, `date` and `description`; revisions are at least one, oldest first and
  unique by version, and versions follow the configured versioning scheme (S0008).
- Text must contain non-whitespace characters; an unknown field name fails; every violation is
  reported, and the command exits 2.

### Record fields

- Every record has `context`; `references` and `notes` are optional. A reference has a
  `designation`, an optional `description` and optional `pointers`.
- A decision has `addresses`, `decision`, `alternatives` and `consequences`.
- A requirement has `addressed_by`, `requirement`, `goals`, `stakeholders` and `responsibility`.
- A specification has `addresses`, `subject`, `terms`, `specification` and `conformance`; a clause
  has a `designation`, an optional `description` and its `statements`.
- `addresses` and `addressed_by` are references with `depends="id"` and inverses of each other;
  `doctor` reports a link listed in one direction only.

### Core documents

- A core document has `introduction` and `rule_sets`, each rule set a `scope` sentence and its
  `rules`.
- Its `records` index is generated from the kind's records, ordered by ID, with short title,
  description, tags and file name; it is refused as input.
- An empty index renders "None.".

### Rendering

- The front matter is YAML serialized from the model in the kind's key order, followed by
  `data_hash`; a string longer than the wrap width is written as a folded block scalar.
- The body comes from the kind's template and is formatted by the configured formatter at
  `wrap_width`.
- An optional section that is not given renders "None.".
- A list item spanning several lines is indented under its marker, so nested bullets stay nested,
  and an item's trailing line break does not loosen the list.
- A reference renders its designation in bold, followed by its description, by a colon before its
  pointers, or by a period.
- A specification clause renders as a level-three heading with its description before its
  statements.

## Conformance

- `tests/test_models.py` and `tests/test_rendering.py` cover validation and rendering; the golden
  files under `tests/golden/` cover every kind and template.
- This repository's `arch/` documents pass `pymarkdown` and `mdformat --check`.

## References and Links

- **Governing decision**:
  - [D0001: Model Owns Record Logic](../decisions/D0001-model-owns-record-logic.md)
  - [D0013: Built-In Flavours](../decisions/D0013-built-in-flavours.md)

## Notes

None.
