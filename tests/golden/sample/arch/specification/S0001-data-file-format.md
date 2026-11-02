---
title: Sample Data File Format
id: S0001
addresses:
  - R0001
short_title: Data File Format
description: Structure of the sample data files.
tags:
  - format
author: sample-team
date: '2026-10-03'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-03'
    description: Initial record.
data_hash: c1:sha256:1b76801ef1848d56d9087e025d6c93d2f575f2092c4a279ec1c4dc9a713ae374
---

## Context

The data files are read by people and tools.

## Subject

- The sample data files.
- Excluded: the rendered documents.

## Terms

- Record: one entry of a kind section.

## Specification

### Encoding

- Files are UTF-8 with LF line endings.

### Structure

A file is a mapping:

```yaml
decisions:
  records: []
```

- The top level holds module facets and kind sections only.
- Records carry an ID.
  - Note: IDs are unique within the project.

## Conformance

- Loading the file with chancellor succeeds.

## References and Links

None.

## Notes

None.
