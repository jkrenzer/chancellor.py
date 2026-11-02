---
title: Local Templates and Kinds Arrive as Named, Versioned Providers
id: R0004
addressed_by:
  - D0002
  - D0005
  - D0013
  - D0025
  - D0032
  - S0001
  - S0004
short_title: Providers
description: >-
  Record kinds, templates and other contributions come from providers, addressed as
  `<provider>/<name>`, loaded from the distribution, from entry points and from local folders by one
  code path.
tags:
  - area: extension
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:3318a0617507bf81ddf3bc9bc05bf9f4f35b5a9e9d25559f871ceece2d360774
---

## Context

Projects need their own record kinds and templates without forking chancellor, and nothing may
shadow anything silently. The `PrefixLoader` decision taken for templates is extended to models.

## Requirement

- A provider declares itself in exactly one manifest, `chancellor-provider.yaml`, with its own
  `_api` version, name, version and contributions; an entry-point plugin returns the same manifest
  as a Python object.
- A kind's model is a Pydantic v2 class implementing the model interface, imported from a module the
  manifest names; a schema-first project may point at a JSON Schema and have the class built at load
  behind the `[schema]` extra. The manifest holds binding keys only.
- Record refs are declared on the model with annotated types from `chancellor.api`, so they survive
  into the JSON Schema the model emits.
- The extension points are a closed set kept in one place: kinds, templates, linters, formatters,
  config loaders and version schemes. An unknown manifest key is an error naming the loaded
  providers.
- Load order is fixed and reported: built-in, entry points sorted by distribution name, local
  providers in declared order. A later provider may add a kind or template but may not redefine one;
  an intended override is written out in configuration, such as `templates: project/decision.md.j2`.
- The built-in set is itself one or more providers, such as `builtin.jkrenzer`, loaded by the same
  code path as a local one.

## Goals

- A local provider adds a record kind and renders it without a line of chancellor changing.

## Stakeholders

- Consuming projects with their own record kinds or templates.
- Plugin authors, such as a future ECSS flavour.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
