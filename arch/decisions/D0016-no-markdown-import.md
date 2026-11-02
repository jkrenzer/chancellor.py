---
title: Ship No Markdown Import
id: D0016
addresses:
  - R0001
short_title: No Markdown Import
description: >-
  Chancellor ships no command that parses records back from Markdown; a project that needs one
  subclasses the model's load hook.
tags: []
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:8a4655190ea97b9a599dbb2af96f65601fdcc71e8c99253845166de2bfeaba07
---

## Context

Records written before a project adopts chancellor often exist only as Markdown. Moving them into
data could be automated by parsing them back.

## Decision

- No built-in Markdown import.
- The API documentation shows a custom load hook as the worked example of a custom loader.
- A project moving to chancellor writes its data and reviews the re-rendered documents.

## Alternatives Considered

- No alternative evaluation was documented for this decision.

## Consequences

- Paths and documents are never parsed back into records.

## References and Links

None.

## Notes

None.
