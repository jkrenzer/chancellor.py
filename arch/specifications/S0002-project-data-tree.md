---
title: Project Data Tree Layout and Merge Rules
id: S0002
addresses:
  - R0003
  - R0010
  - R0011
  - R0012
  - R0013
  - R0014
  - R0015
  - R0018
short_title: Project Data Tree
description: >-
  Top-level layout of the project data tree, chancellor's configuration keys, and how several data
  files merge.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:55d305c09549a6236270879ff2f7486349b86dde050ba37c9e3f78e5ab03dbb4
---

## Context

One YAML file, or several, is the source of truth for records and for the configuration of the tools
that read them.

## Subject

- The data file `chancellor.yaml`, the files it includes, and their merged tree.
- The keys under `_api/chancellor` and `config/chancellor`.
- Excluded: the fields of individual record kinds, which their models define.

## Terms

- Data file: the main file, found as `--data`, else `$CHANCELLOR_DATA`, else the nearest
  `chancellor.yaml` upwards from the working directory.
- Module: a tool owning one key under `_api` and one under `config`, such as `chancellor`.
- Kind section: a top-level key holding the core document and records of one kind.

## Specification

### Top level

```yaml
_api:
  chancellor:
    version: "2.0.0"
    kind: project_records
config:
  chancellor:
    include: [arch/data]
decisions:
  core: {}
  records: []
```

- The top level holds `_api`, `config`, `meta` and kind sections, nothing else (S0008).
- `_api.chancellor` has `version: "2.0.0"` and `kind: project_records`.
- A kind section holds `core`, the core document, and `records`, the list of records.
- Keys under another module of `_api` or `config` are preserved and never read by chancellor.
- A tree without the scoped layout is refused with a message showing the new shape.
- Every top-level section encountered is logged at INFO level (D0027).

### Chancellor configuration

- `providers`: list of local providers, each `{name, path}`; only in the main data file.
- `include`: data-tree files or folders to merge, relative to the project root; a folder contributes
  its `*.yaml` files in name order; only in the main data file.
- `loaders`: the configuration loaders, default `["builtin.data_file"]`, by type address or import
  path.
  - Note: proposed in D0034.
- `wrap_width`: positive integer, default 100.
- `formatter` and `linter`: a type address under `type` plus the type's arguments.
- `kinds.<kind>.folder` and `kinds.<kind>.templates`: per-kind output folder and template addresses,
  defaulting to the provider's.
- `kinds.<kind>.data`: the file holding the kind's section, relative to the project root; a missing
  file means no data yet (D0019).
- `kinds.<kind>.model` and `kinds.<kind>.core_model`: a subclass of the provider's record or core
  model, as `path/to/file.py:Class` or `module:Class` (D0025).
- `data_model`: a supplied root model as `module:Class`, built from chancellor's public bases;
  output folders stay configurable alongside it (D0030).
- `snapshot`: optional path for a JSON export of the validated data.
- `lock`: lock file path, default `chancellor.lock`.
- An unknown key is an error naming the loaded providers and the nearest valid keys.
- A setting can be overridden for one run with `--set KEY=VALUE`.
  - Note: proposed in D0034.

### Merging files

- Mappings merge key-wise.
- Record lists of a kind section concatenate.
- A value defined in two files is an error naming both files.
- A record ID appearing twice is an error naming both records and files.
- The file layout enters no digest; provenance per section and record is recorded in the lock.

### Paths

- The project root is the nearest folder above the data file holding `pyproject.toml`, else `.git`,
  else the data file's folder.
- Every configured path is relative to the project root and must resolve inside it, symlinks
  included.
- Paths are stored repo-relative in POSIX form.

## Conformance

- Top level and configuration: `chancellor schema config` prints the merged configuration schema;
  the scoped-layout tests in `tests/test_project.py`.
- Merging: a split-file test shows equal digests for one file and several.
- This repository: `chancellor build --check` over `chancellor.yaml` with `include: [arch/data]`.

## References and Links

- **Governing decision**:
  - [D0012: Facet-Scoped Data Tree](../decisions/D0012-facet-scoped-data-tree.md)
  - [D0019: Per-Kind Data Files](../decisions/D0019-per-kind-data-files.md)
  - [D0025: Model Override in Configuration](../decisions/D0025-model-override-in-configuration.md)
  - [D0027: Log Top-Level Sections](../decisions/D0027-log-top-level-sections.md)
  - [D0030: Root Models by Inheritance](../decisions/D0030-root-models-by-inheritance.md)

## Notes

None.
