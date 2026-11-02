---
title: Requirement Documentation Core Document
id: R0000
short_title: Requirement Core
description: Rules for chancellor's requirement records and the index of all requirements.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:5b8172a2a914c838e42f1d794569c003353889ab86bc4547481e53df9425a11e
---

## Introduction

This document is the core and root of chancellor's requirement documentation. A requirement record,
identified as `R####`, states what chancellor must achieve and under which conditions.

The records are data in `arch/data/requirements.yaml` and are rendered by chancellor itself.

A requirement states a need and leaves the solution to decisions and specifications. In the
maintainer's words: "requirements should normally not require a specific solution lest and leave
this addressing to decisions and specifications."

## Rules

Following rules are to be applied to the files in this folder:

- Do not edit the rendered documents. Change the data in `arch/data/` and run `chancellor build`.
- One record covers one requirement; related design items may share a record.
- File names are lower-kebab-case of the record ID and short title.
- Short and long title shall be descriptive and specific.
- Use clear language and be concise but do not resort too much to short or partial sentences.

Following rules are to be applied to the content of a record:

- Make each obligation verifiable where possible.
- List the decisions and specifications that address the requirement in `addressed_by`.

## Requirements

- [R0001: Built-In Record Kinds](R0001-built-in-record-kinds.md): Chancellor ships decision,
  requirement and specification kinds with their core documents, strict validation and lint-clean
  rendering, usable from an empty configuration.
  - Tags: `area: records`
- [R0002: Verbs and Agent Tools](R0002-verbs-and-agent-tools.md): The `render`, `schema`, `hash`,
  `build`, `lint` and `serve` verbs stay available from the installed console script, and the nine
  agent tools keep their names and arguments.
  - Tags: `area: cli`
- [R0003: Project-Relative Paths](R0003-project-relative-paths.md): Chancellor finds the project
  root from the data file, keeps every configured path inside it, and publishes nothing that points
  into another repository.
  - Tags: `area: paths`
- [R0004: Providers](R0004-providers.md): Record kinds, templates and other contributions come from
  providers, addressed as `<provider>/<name>`, loaded from the distribution, from entry points and
  from local folders by one code path.
  - Tags: `area: extension`
- [R0005: Single Registry](R0005-single-registry.md): One registry is the only lookup from a kind to
  its provider, model, templates, defaults and folders, and `chancellor providers` shows what it
  holds.
  - Tags: `area: extension`
- [R0006: Contribution Fingerprints](R0006-contribution-fingerprints.md): Every provider, model and
  supplied root model has a fingerprint that moves exactly when what it contributes changes.
  - Tags: `area: hashing`
- [R0007: Data Hash Scope](R0007-data-hash-scope.md): `data_hash` is the digest of the record's own
  canonical data, the same standalone and in the project, and never includes the schema that
  validated it.
  - Tags: `area: hashing`
- [R0008: Rebuild Scope and Explain](R0008-rebuild-scope-and-explain.md): The provider set and
  `config/chancellor` enter every document's digest, the lock records the provider set, and
  `explain` names the digest part that moved.
  - Tags: `area: hashing`
- [R0009: Degradations](R0009-degradations.md): An input chancellor cannot fingerprint reliably is
  recorded per build in the lock and fails `--strict`; an outdated lock is rebuilt, never an error.
  - Tags: `area: hashing`
- [R0010: Facet Namespacing](R0010-facet-namespacing.md): The top level of the data holds
  `_api/<module>`, `config/<module>` and one section per record kind; chancellor owns only its own
  module keys and preserves the rest.
  - Tags: `area: data-tree`
- [R0011: Multi-File Data Tree](R0011-multi-file-data-tree.md): Several data files merge by one
  documented rule, and splitting or merging files changes no digest while provenance stays
  explainable.
  - Tags: `area: data-tree`
- [R0012: Configuration Loading](R0012-configuration-loading.md): Configuration arrives through a
  loader interface, is validated against one merged model built from the provider set, and rejects
  unknown keys with suggestions.
  - Tags: `area: config`
- [R0013: Scoped Layout Only](R0013-scoped-layout-only.md): Only the scoped layout with
  `_api/chancellor.kind: project_records` is accepted; the old unscoped layout is refused with a
  message naming the new shape.
  - Tags: `area: data-tree`
- [R0014: Configurable Kind Locations](R0014-configurable-kind-locations.md): Each kind maps to
  exactly one configurable folder, falling back to its provider's default, and provider folders are
  never read as record data.
  - Tags: `area: paths`
- [R0015: Supplied Root Model](R0015-supplied-root-model.md): A project may validate its data with
  its own Pydantic root model under a documented protocol, inheriting chancellor's fields and
  defaults.
  - Tags: `area: extension`
- [R0016: Golden Output Guard](R0016-golden-output-guard.md): Chancellor's own synthetic records
  over every built-in kind and template are rendered and compared byte for byte with committed
  golden files.
  - Tags: `area: testing`
- [R0017: Generator and Hooks](R0017-generator-and-hooks.md): Schema-to-model generation runs
  through chancellor with documented settings, and the check forms of its commands ship as
  pre-commit hooks.
  - Tags: `area: tooling`
- [R0018: Formatter and Linter Types](R0018-formatter-and-linter-types.md): The formatter and the
  linter are configuration resolved as types through the registry; chancellor hard-wires neither and
  records what the linter reports.
  - Tags: `area: formatting`
- [R0019: Public Extension Interfaces](R0019-public-extension-interfaces.md): Formatter, linter,
  model, provider and config loader each have an abstract base class in `chancellor.api`,
  implemented by the built-ins too and documented as the public surface.
  - Tags: `area: extension`
- [R0020: Exit Codes](R0020-exit-codes.md): All commands use the same seven exit codes, documented
  in help and asserted in tests, so a script can tell a misconfiguration from a finding.
  - Tags: `area: cli`
- [R0021: Canonical Digests](R0021-canonical-digests.md): Record data, the config subtree, model
  schemas and provider manifests are digested from one canonical byte form, with exclusions declared
  on the model and a tagged digest format.
  - Tags: `area: hashing`
- [R0022: Room for Prose Documents](R0022-room-for-prose-documents.md): Chancellor builds no reports
  or prose documents yet, but its rendering must allow template-to-template rendering and functions
  that walk documents.
  - Tags: `area: rendering`
- [R0023: Renderer Version in the Lock](R0023-renderer-version-in-the-lock.md): The lock records
  which chancellor version produced the documents, including the commit for unreleased builds, and
  the documents never contain it.
  - Tags: `area: hashing`
- [R0024: Versioned Records](R0024-versioned-records.md): Every record and the record set as a whole
  are versioned under a decided and specified versioning scheme and increment policy, so a reference
  to a record stays unambiguous over time.
  - Tags: `area: records`
