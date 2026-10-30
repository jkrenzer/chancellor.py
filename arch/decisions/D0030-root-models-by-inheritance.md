---
title: Supplied Root Models Inherit Every Field and Default From Base Classes
id: D0030
addresses:
  - R0015
short_title: Root Models by Inheritance
description: >-
  A supplied root model inherits from base classes chancellor provides, which bring every field and
  its default, configuration included; it does not block output folders.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:39caeafec1204e8d9cce68477d5706d1e856c4fb8a300efeb20835bbaf6ca7ec
---

## Context

Making a supplied root model and configured kind folders mutually exclusive would block a root-model
project from choosing where its documents go.

## Decision

- Blocking output folders for a project with a supplied root model is not intended.
- Chancellor provides inheritable base classes for all its model classes, bringing every field and
  its default, especially in the configuration; a supplied root model inherits from them, so a valid
  data model can be filled in by inheritance.
- A user who supplies classes without the base classes can still break things.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- A root model and configured output folders work together.
- The public bases are `ProjectModel`, `ApiTree`, `ConfigTree`, `ChancellorConfig`, `KindConfig` and
  `Section`; the merged configuration model is built on the consumer's `ChancellorConfig` subclass.
- Settings take priority in this order: command line, environment, data file and loaders, the
  consumer's class defaults, provider defaults, built-in defaults; the maintainer confirmed this
  order.

## References and Links

None.

## Notes

None.
