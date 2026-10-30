---
title: The Data Tree May Span Several Files Without Changing Any Digest
id: R0011
addressed_by:
  - D0019
  - D0020
  - S0002
short_title: Multi-File Data Tree
description: >-
  Several data files merge by one documented rule, and splitting or merging files changes no digest
  while provenance stays explainable.
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
data_hash: c1:sha256:36aa8744c7404fb20ecb1a3ffef651c6fe468dff5824c186d6625ee69d71812d
---

## Context

A single file suits small projects; larger ones split by kind or topic. File layout is not content.

## Requirement

- Mappings merge key-wise, kind sections concatenate, a scalar defined in two files is an error
  naming both sites, and a duplicate record ID names the files and the records.
- Splitting a source file into several, or merging them back, changes no digest; a test covers it.
- Provenance is tracked per section, reported by `explain` and recorded in the lock.

## Goals

- Reorganizing the data files never causes a rebuild.

## Stakeholders

- Authors organizing large record sets.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
