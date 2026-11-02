---
title: Code and Declarative Contributions Carry Fingerprints
id: R0006
addressed_by:
  - D0005
  - D0018
  - D0021
  - D0031
  - S0001
  - S0006
short_title: Contribution Fingerprints
description: >-
  Every provider, model and supplied root model has a fingerprint that moves exactly when what it
  contributes changes.
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
data_hash: c1:sha256:2a4b697f87ea0591a66dae655353e4dcf4ec931f6abe223cef3c5ac7103f904b
---

## Context

Locally supplied definitions must move digests the moment they change, while a reformatting
generator upgrade should rebuild nothing.

## Requirement

- A model is fingerprinted by the JSON Schema it emits, canonicalized and digested like any other
  data, plus its distribution version or, for a loose module, its source bytes.
- A declarative provider's fingerprint is a digest over its canonicalized manifest, kind
  declarations and the loader's source string of each template it contributes.
- A code provider's fingerprint is its distribution version string, compared as an exact string and
  never semver-compared.
- A supplied root model is fingerprinted by the same rule and appears in `chancellor providers`; it
  needs no degradation record.

## Goals

- A hand-written, a committed generated and a load-time generated model fingerprint alike.

## Stakeholders

- Consuming projects relying on incremental builds.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

In an editable install the version string does not change with the code, so the fingerprint adds a
digest of the package source; loose code is fingerprinted by its static import closure (D0031).
