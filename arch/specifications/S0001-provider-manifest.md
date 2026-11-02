---
title: Provider Manifest chancellor-provider.yaml
id: S0001
addresses:
  - R0004
  - R0005
  - R0006
short_title: Provider Manifest
description: >-
  Structure of a provider manifest, the one file or object by which a provider declares its name,
  version and contributions, and the load order of providers.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:6ad331f69f6da44da225aaf435386d3d99dcb97d9edaa85045b94649c3168cd3
---

## Context

Built-in, plugin and local providers declare themselves in one format, so there is one schema to
document, validate and fingerprint.

## Subject

- The manifest file `chancellor-provider.yaml` of a local or built-in provider.
- The manifest object an entry point in the group `chancellor.providers` returns.
- The load order and addressing of contributions.
- Excluded: the content of templates and the fields of record models.

## Terms

- Provider: a named bundle of contributions loaded from the distribution, an entry point or a
  project folder.
- Contribution: a kind, template, formatter, linter, config loader or version scheme a provider
  adds.
- Address: `<provider>/<name>`, the only way to name a contribution.
- Code provider: a provider fingerprinted by its distribution version.
- Declarative provider: a provider fingerprinted by a digest over its manifest and template sources.

## Specification

### Manifest keys

```yaml
_api:
  version: 1.0.0
  kind: chancellor_provider
name: example
version: "3"
templates:
  directory: templates
kinds:
  interface:
    folder: arch/interface
    templates:
      records: example/interface.md.j2
      core_document: example/interface-core.md.j2
    fields:
      protocol: {type: str, required: true}
      partners: {type: "list[record_ref]", required: false}
```

- `_api.version` is `1.0.0` and `_api.kind` is `chancellor_provider`.
- `name` matches `^[a-z][a-z0-9_-]*(\.[a-z][a-z0-9_-]*)*$`; a dot separates a flavour, as in
  `builtin.jkrenzer`.
- `version` is optional; a local provider without one is a degradation.
- The top-level keys besides `_api`, `name` and `version` are the closed set of extension points:
  `kinds`, `templates`, `formatters`, `linters`, `config_loaders`, `version_schemes`. Any other key
  is an error naming the loaded providers.
- `formatters`, `linters`, `config_loaders` and `version_schemes` map a type name to `module:Class`;
  a type is addressed as `<provider>.<name>`, e.g. `builtin.mdformat`.

### Kind declarations

- A kind declares `folder`, its default output folder relative to the project root, and
  `templates.records`.
- A kind gives exactly one model source: `model` (`module:Class`), `fields` (declarative) or
  `schema` (JSON Schema, needs the `schema` extra).
- `core_model` and `templates.core_document` are given together or not at all.
- `base` names the base model of declarative fields and is valid with `fields` only.
- A declarative field has `type` (`str`, `text`, `int`, `bool`, `date`, `record_ref`, or `list[...]`
  of these), `required` (default true), `depends` for `record_ref` fields (`id`, `name` or `data`,
  default `id`; D0032) and an optional `description`.
- `aliases` maps extra kind names to `records` or `core_document`, e.g. `adr: records`.

### Load order and addressing

- Providers load in a fixed order, built-in first, then entry points sorted by distribution name,
  then local providers in declared order.
- A later provider may add a kind or template but may not redefine one; redefinition is an error.
- Every contribution is addressed by its provider's name; templates as `<provider>/<file>`.
- The built-in providers `builtin` and `builtin.jkrenzer` load through the same code path as a local
  one.

### Fingerprints

- A code provider's fingerprint is its distribution version string, compared as an exact string.
- In an editable install, the fingerprint is `<version> source <digest>`, the digest covering the
  package source (D0017, D0031).
- Code from no distribution is fingerprinted by the digest of its source and its static import
  closure; an import that cannot be resolved records `unfingerprinted-code` (D0031).
- A provider without a version that is hashed completely raises an INFO message; one that cannot be
  hashed safely records `unversioned-provider` (D0021).
- A declarative provider's fingerprint is a digest over its canonicalized manifest, its kind
  declarations and the loader's source string of each template it contributes.
- A model's contribution to a fingerprint is the digest of the JSON Schema it emits.

## Conformance

- Manifest keys and kind declarations: `chancellor schema` of the manifest model and the tests in
  `tests/test_providers.py`.
- Load order: `chancellor providers` lists providers in load order; covered by the provider tests.
- Fingerprints: the `providers` part named by `chancellor explain` after a template change in a
  local provider.

## References and Links

- **Governing decision**:
  - [D0002: Providers With Prefix Addressing](../decisions/D0002-providers-with-prefix-addressing.md)
  - [D0005: Pydantic Models and Schema Fingerprints](../decisions/D0005-pydantic-models-and-schema-fingerprints.md)

## Notes

None.
