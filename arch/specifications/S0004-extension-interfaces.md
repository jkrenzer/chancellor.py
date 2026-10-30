---
title: Extension Interfaces of chancellor.api
id: S0004
addresses:
  - R0004
  - R0015
  - R0019
  - R0021
short_title: Extension Interfaces
description: >-
  The abstract classes, the six model hooks, the field markers and the root-model protocol that make
  up chancellor's public extension surface.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:2751976ec47ba0ecab247183bb8adbd756f61698242e116c4f55d4a94adf173f
---

## Context

Consumers extend chancellor by subclassing; the built-in types implement the same classes.

## Subject

- The public module `chancellor.api`.
- Excluded: internal modules, which may change without notice.

## Terms

- Hook: a method of an interface a subclass overrides to change one step.
- Marker: an annotation from `chancellor.api` that also appears in the emitted JSON Schema.

## Specification

### Abstract classes

- `Model` is the base of every record model and `CoreModel` the base of a kind's core document.
- `Provider`, `Formatter`, `Linter`, `ConfigLoader` and `VersionScheme` are abstract base classes.
- `RootModel` is a Protocol with `chancellor_sections()`, returning per kind its core document or
  none and its records.
- Built-in types subclass these same classes.
- `Model.output_name(suffix)` gives the file name of a record's document.
- `Model.inverse_refs` maps a `RecordRef` field to the field of the referenced record that must list
  this record back, e.g. `{"addresses": "addressed_by"}`; `doctor` reports one-sided links.
- `CoreModel.index_records(records)` returns a copy of the core document with its generated index
  filled in.
- `ProjectModel`, `ApiTree`, `ConfigTree`, `ChancellorConfig`, `KindConfig` and `Section` are public
  bases a supplied root model inherits from, with every field and its default (D0030).
- A `ConfigLoader` is constructed with a `LoaderContext` and its configured arguments.
  - Note: proposed in D0034.
- A `VersionScheme` parses and orders versions; the built-in schemes are `semver`, `pep440` (through
  the `packaging` library) and `free`, and providers may contribute more (S0008).

### Model hooks

The hook names are recorded in D0024.

- `model_load`: raw source data to validation input; the default passes it through.
- `model_validate`: Pydantic validation.
- `model_canonicalize`: the JSON data behind `data_hash`, with defaults filled and excluded fields
  left out.
- `model_index`: the record's ID and every `RecordRef` it holds.
- `model_serialize`: document data for templates and front matter, computed fields included.
- `model_save`: the data written back into the data tree, without generated and computed fields.
- `front_matter` is a class variable listing the front-matter keys in order; it is not a hook.

### Markers

- `RecordRef(depends=...)` marks a record ID and declares what flows over the reference: `"id"`
  (default), `"name"` or `"data"`; the value is written into the JSON Schema as
  `x-chancellor-record-ref`. `RecordRefs` is a list of `depends="id"` references (D0032).
- A value shaped like an ID of a registered kind must resolve; any other value is external, written
  as `<project>:<version>:<id>` or as a URL (D0029, S0008).
- `DigestExclude` keeps a field out of `model_canonicalize`.
- `Generated` marks a field chancellor fills in; it is excluded from the digest and rejected as
  input.

### Extension point names

- The extension points are exactly `kinds`, `templates`, `formatters`, `linters`, `config_loaders`
  and `version_schemes`.

### Template context

- A template sees another record only under `refs.<field>`, with exactly what that field's `depends`
  exposes (D0032).
- `refs` and `data_hash` are reserved; a model field with either name is refused.
- A referenced record's own references are not exposed; a template that reaches past one hop fails
  (D0033).

### Model overrides

- `config/chancellor/kinds/<kind>/model` and `core_model` name a subclass of the provider's model;
  any other class is refused.
- A model is named as `path/to/file.py:Class`, relative to the project root, or as `module:Class`.
- An override is fingerprinted by its code, along the one code path of D0031, and its emitted JSON
  Schema; it is no degradation when its code is hashed completely.

## Conformance

- `tests/test_models.py` and `tests/test_providers.py` exercise the hooks and markers through the
  built-in kinds and a supplied root model (`tests/rootmodel.py`).
- Documentation with a minimal subclass per class: not complete yet.

## References and Links

- **Governing decision**:
  - [D0009: Abstract Classes and Six Model Hooks](../decisions/D0009-abstract-classes-and-six-model-hooks.md)
  - [D0024: Model Hook Names](../decisions/D0024-model-hook-names.md)
  - [D0025: Model Override in Configuration](../decisions/D0025-model-override-in-configuration.md)
  - [D0032: Reference Dependencies](../decisions/D0032-reference-dependencies.md)
  - [D0029: Usage Errors and Ref Resolution](../decisions/D0029-usage-errors-and-ref-resolution.md)

## Notes

None.
