---
title: The Data Tree Is Split by Facet With One Owner per Module
id: R0010
addressed_by:
  - D0012
  - D0027
  - D0028
  - S0002
short_title: Facet Namespacing
description: >-
  The top level of the data holds `_api/<module>`, `config/<module>` and one section per record
  kind; chancellor owns only its own module keys and preserves the rest.
tags:
  - area: data-tree
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:2b819f783a0202707fa8575ea0b7b3905d05598cfd56bea5abecb3629685d720
---

## Context

Several tools read the same project data, as `pyproject.toml` holds shared data beside
`[tool.<name>]`. Record kinds are the shared part.

## Requirement

- The top level holds exactly three kinds of key: `_api/<module>`, `config/<module>` and one section
  per record kind; kinds are never nested under a module.
- Chancellor reads and writes `_api/chancellor` and `config/chancellor` only, and what it does not
  own survives every write it makes.
- The module key is a variable: one default plus per-facet overrides for config, API meta and
  providers. No comparison against the literal module name exists in the code.

## Goals

- One YAML file can serve chancellor and other tools without either breaking the other.

## Stakeholders

- Other tools sharing the data tree.
- Consumers embedding chancellor as a sub-module.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
