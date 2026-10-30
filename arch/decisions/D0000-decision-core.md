---
title: Decision Documentation Core Document
id: D0000
short_title: Decision Core
description: Rules for chancellor's decision records and the index of all decisions.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:f04fb292073e5ff432bcb8e80814a0a0bbfaa27c83d8cc31435cacf9a1a40a3c
---

## Introduction

This document is the core and root of chancellor's decision documentation. A decision record,
identified as `D####`, states one choice taken for chancellor, the alternatives that were evaluated
and the consequences. The need behind a decision belongs in a requirement record, the resulting
format or interface in a specification record.

The records are data in `arch/data/decisions.yaml` and are rendered by chancellor itself.

## Rules

Following rules are to be applied to the files in this folder:

- Do not edit the rendered documents. Change the data in `arch/data/` and run `chancellor build`.
- One record covers one decision actually taken, not one question or one table row.
- File names are lower-kebab-case of the record ID and short title.
- Short and long title shall be descriptive and specific.
- Use clear language and be concise but do not resort too much to short or partial sentences.

Following rules are to be applied to the content of a record:

- List the requirements the decision addresses in `addresses`, and keep their `addressed_by`
  consistent.
- Keep the rationale in the record, not in a commit message.
- A decision taken during implementation and not yet confirmed by the maintainer has the state
  `proposed`.

## Decisions

- [D0001: Model Owns Record Logic](D0001-model-owns-record-logic.md): Record models validate,
  default and serialize; templates render the body only and never repair, default or re-check data.
- [D0002: Providers With Prefix Addressing](D0002-providers-with-prefix-addressing.md): One
  mechanism, the provider, carries every contribution, and each contribution is addressed as
  `<provider>/<name>` so nothing shadows anything silently.
- [D0003: Coarse Environment Digest](D0003-coarse-environment-digest.md): One fingerprint covers the
  resolved provider set and one digest the whole of `config/chancellor`; any change in either
  rebuilds every document chancellor owns.
- [D0004: Config Loader Interface](D0004-config-loader-interface.md): Configuration comes from a
  loader interface whose sources follow pydantic-settings; the first release has one loader reading
  the data file.
- [D0005: Pydantic Models and Schema Fingerprints](D0005-pydantic-models-and-schema-fingerprints.md):
  A kind's model is an imported Pydantic v2 class by default, schema-first input sits behind a
  `[schema]` extra, and a model is fingerprinted by the JSON Schema it emits.
- [D0006: JCS Canonical Form](D0006-jcs-canonical-form.md): Canonical bytes are JCS (RFC 8785) over
  the validated dump with defaults filled, and digests are written `c1:sha256:<hex>`.
- [D0007: Generation Tooling in the schema Extra](D0007-generation-tooling-in-the-schema-extra.md):
  Model generation is chancellor's own plugin module inside the `[schema]` extra, with its settings
  documented flag by flag and pre-commit hooks for it and the check commands.
- [D0008: Formatter and Linter by Type](D0008-formatter-and-linter-by-type.md): Formatter and linter
  are configured as types resolved through the registry; mdformat is the default formatter and the
  default linter is none, which makes `lint` fail.
- [D0009: Abstract Classes and Six Model Hooks](D0009-abstract-classes-and-six-model-hooks.md):
  Every extension point is an abstract base class in `chancellor.api`, implemented by the built-ins
  too, and the model interface has six hooks for loading, validation, canonicalization, indexing,
  serialization and saving.
- [D0010: Seven Exit Codes](D0010-seven-exit-codes.md): Chancellor returns one of seven exit codes
  with fixed meanings from every command.
- [D0011: Runtime Dependencies](D0011-runtime-dependencies.md): mdformat and `rfc8785` are required,
  pymarkdownlnt and application-properties are dropped, and YAML is read and written with
  ruamel.yaml only.
- [D0012: Facet-Scoped Data Tree](D0012-facet-scoped-data-tree.md): The data tree is scoped by facet
  with chancellor's keys under `_api/chancellor` and `config/chancellor`, its kind is
  `project_records`, and the old layout gets no shim.
- [D0013: Built-In Flavours](D0013-built-in-flavours.md): The first release ships the
  `builtin.jkrenzer` flavour only; Nygard joins the built-ins later and ECSS comes as a plugin
  module.
- [D0014: Defer Prose Documents](D0014-defer-prose-documents.md): The first release builds records
  only and keeps rendering open for template-to-template rendering and document-walking functions.
- [D0015: Version 0.1.0](D0015-version-0-1-0.md): The first release is an internal test and stays at
  version `0.1.0`, which leaves room to change the documented public surface.
- [D0016: No Markdown Import](D0016-no-markdown-import.md): Chancellor ships no command that parses
  records back from Markdown; a project that needs one subclasses the model's load hook.
- [D0017: Editable Install Detected](D0017-editable-install-detected.md): An editable install of
  chancellor is no degradation when its code changes are caught by the source digest; `--strict`
  means fully reproducible.
- [D0018: Whole-Set Provider Part](D0018-whole-set-provider-part.md): The providers part is one
  digest per build over the provider set and every fingerprint, so any provider change rebuilds
  every document.
- [D0019: Per-Kind Data Files](D0019-per-kind-data-files.md): `kinds.<kind>.data` names the file
  that holds a kind's records; `kinds.<kind>.folder` is where the kind's documents go.
- [D0020: Config Digest by Chancellor](D0020-config-digest-by-chancellor.md): Configuration loaders
  return data only; chancellor digests the validated configuration with defaults filled and without
  layout keys.
- [D0021: Fingerprinted Code Does Not Degrade](D0021-fingerprinted-code-does-not-degrade.md): Code
  and resources chancellor can hash completely are no degradation; an unversioned provider hashed
  completely raises only an INFO message.
- [D0022: Own Golden Fixtures](D0022-own-golden-fixtures.md): Synthetic sample records and their
  committed renders guard chancellor's output between versions.
- [D0023: One Write Path](D0023-one-write-path.md): Nothing is written outside a staging tree except
  by `apply`, and `output_path_for` is the only place output paths are built.
- [D0024: Model Hook Names](D0024-model-hook-names.md): The six model hooks are named `model_load`,
  `model_validate`, `model_canonicalize`, `model_index`, `model_serialize` and `model_save`.
- [D0025: Model Override in Configuration](D0025-model-override-in-configuration.md): A project
  replaces a kind's record or core model with a subclass of the provider's model, named in
  `config/chancellor` as `kinds.<kind>.model` or `kinds.<kind>.core_model`.
- [D0026: CLI Changes While Coding](D0026-cli-changes-while-coding.md): `hash [IDS]` and
  `schema data` replace the old forms `hash INPUT` and `schema architecture`, without aliases.
- [D0027: Log Top-Level Sections](D0027-log-top-level-sections.md): Chancellor logs every top-level
  section of the data tree it encounters at INFO level, and the user documentation explains raising
  the log level to investigate the YAML.
- [D0028: Data Snapshot Export](D0028-data-snapshot-export.md): On request, chancellor writes the
  validated data tree as JSON to a configured path; the snapshot is output, never input.
- [D0029: Usage Errors and Ref Resolution](D0029-usage-errors-and-ref-resolution.md): Command-line
  misuse exits 1, and a reference shaped like a registered kind's ID must resolve; external
  references are written so they cannot be mistaken for one.
- [D0030: Root Models by Inheritance](D0030-root-models-by-inheritance.md): A supplied root model
  inherits from base classes chancellor provides, which bring every field and its default,
  configuration included; it does not block output folders.
- [D0031: One Code Fingerprint Path](D0031-one-code-fingerprint-path.md): Every piece of Python code
  chancellor loads is fingerprinted by one function, by its distribution version, its source digest
  or its static import closure.
- [D0032: Reference Dependencies](D0032-reference-dependencies.md): A reference declares with
  `depends` whether its document reads the target's ID, its file name or its data, and only that can
  rebuild the document or reach its template.
- [D0033: One-Hop References](D0033-one-hop-references.md): A template sees a referenced record's
  declared context but not that record's own references; reaching further is an error.
- [D0034: Config Loaders and Overrides](D0034-config-loaders-and-overrides.md): Proposed:
  `config/chancellor/loaders` names the loaders by type, and `--set KEY=VALUE` overrides a setting
  for one run, recorded in the lock.
- [D0035: Unvouched Documents Kept](D0035-unvouched-documents-kept.md): Proposed: documents an
  unusable lock still names are reported as orphans and kept, and unknown files in a kind's output
  folder are warned about and kept; `doctor` flags them.
- [D0036: Versioning Mechanism](D0036-versioning-mechanism.md): Chancellor keeps the record-set
  version in a `meta` facet, validates versions through a pluggable version scheme that defaults to
  no checks, and resolves bare and absolute references.
- [D0037: SemVer for Records](D0037-semver-for-records.md): This project versions every record
  revision and the record set with SemVer 2.0.0, writes absolute IDs as `<version>:<id>`, and starts
  the record set at `0.1.0`.
- [D0038: Version Increment Policy](D0038-version-increment-policy.md): A version increments by the
  highest impact of the changes since the last version: MAJOR when an absolute ID would mislead,
  MINOR when content is added or firmed up, PATCH for corrections.
