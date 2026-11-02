---
title: Specification Documentation Core Document
id: S0000
short_title: Specification Core
description: Rules for chancellor's specification records and the index of all specifications.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:e17b0dd2ae74cec0a14a8a59d46f09ab0d9519832da3a53146719d6533e56bbd
---

## Introduction

This document is the core and root of chancellor's specification documentation. A specification
record, identified as `S####`, states what an artifact of chancellor is: its structure, its
permitted content and the conditions an instance of it has to satisfy. The need for the artifact
belongs in a requirement record, the reasoning that led to it in a decision record.

The records are data in `arch/data/specifications.yaml` and are rendered by chancellor itself.

## Rules

Following rules are to be applied to the files in this folder:

- Do not edit the rendered documents. Change the data in `arch/data/` and run `chancellor build`.
- One file should cover one major topic.
- File names are lower-kebab-case of the record ID and short title.
- Short and long title shall be descriptive and specific.

Following rules are to be applied to the content of a record:

- State what the artifact is, not why it was chosen.
- Delimit the subject in the Subject section and state exclusions explicitly.
- Define every term the normative statements rely on in the Terms section.
- Every statement of a clause is normative; all remaining text is explanatory.
- State in the Conformance section how a clause is checked and which evidence the check produces.

Following rules are to be applied to the links between records:

- List the requirements a specification answers in `addresses`, and keep their `addressed_by`
  consistent.
- Link the decision that governs a specification under References and Links.

## Specifications

- [S0001: Provider Manifest](S0001-provider-manifest.md): Structure of a provider manifest, the one
  file or object by which a provider declares its name, version and contributions, and the load
  order of providers.
- [S0002: Project Data Tree](S0002-project-data-tree.md): Top-level layout of the project data tree,
  chancellor's configuration keys, and how several data files merge.
- [S0003: Canonical Form and Digests](S0003-canonical-form-and-digests.md): The canonical bytes
  behind every chancellor digest and the written form of a digest.
- [S0004: Extension Interfaces](S0004-extension-interfaces.md): The abstract classes, the six model
  hooks, the field markers and the root-model protocol that make up chancellor's public extension
  surface.
- [S0005: Exit Codes](S0005-exit-codes.md): The seven exit codes every chancellor command returns
  and what each means.
- [S0006: Lock File](S0006-lock-file.md): Structure of the lock file and the digest parts of a
  document's `input_hash` that decide whether a document is rebuilt.
- [S0007: Built-In Record Kinds](S0007-built-in-record-kinds.md): Fields, validation rules, core
  documents and rendering of the decision, requirement and specification kinds that ship as
  `builtin.jkrenzer`.
- [S0008: Versioning and Absolute IDs](S0008-versioning-and-absolute-ids.md): Where chancellor keeps
  the record-set version, how a configured scheme validates versions, and how absolute IDs refer to
  records from outside the record set.
- [S0009: Version Increment Policy](S0009-version-increment-policy.md): When this project increments
  a record's revision version and the record-set version, and by which category.
- [S0010: SemVer Versions and Absolute IDs](S0010-semver-versions-and-absolute-ids.md): This
  project's versions of records and of the record set, and the form of its absolute IDs.
