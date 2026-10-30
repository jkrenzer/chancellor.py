---
title: Environment Changes Rebuild Conservatively and Explain Why
id: R0008
addressed_by:
  - D0003
  - D0018
  - D0020
  - D0032
  - D0033
  - S0006
short_title: Rebuild Scope and Explain
description: >-
  The provider set and `config/chancellor` enter every document's digest, the lock records the
  provider set, and `explain` names the digest part that moved.
tags:
  - area: hashing
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:73214b8bf749f673d1ccc28f3c62dcc1ae5a262360ab5b992cadb984d2bed07a
---

## Context

Which configuration key could affect which file is guesswork. A needless rebuild is cheaper than a
stale document, but a mass rebuild whose cause cannot be named is the failure the scheme exists to
prevent.

## Requirement

- One fingerprint covers the resolved provider set and one digest the whole of `config/chancellor`;
  a change in either rebuilds every document chancellor owns.
- The lock records the resolved provider set with name, origin, type, fingerprint and contributed
  kinds; a provider that disappeared, moved or changed origin is detected, and every document is
  rebuilt.
- `explain ID` names the digest part that moved: data, refs, files, templates, config, api or
  providers, and for providers which one.
- A change under another module's `_api` or `config` moves no chancellor digest; a change in a
  shared kind section rebuilds exactly the documents that read it.

## Goals

- Every rebuild has a cause that one command can name.

## Stakeholders

- Maintainers reviewing unexpected document changes.
- Other tools sharing the data tree, such as field-marshall.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
