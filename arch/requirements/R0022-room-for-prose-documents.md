---
title: The First Release Leaves Room for Reports and Prose Documents
id: R0022
addressed_by:
  - D0014
short_title: Room for Prose Documents
description: >-
  Chancellor builds no reports or prose documents yet, but its rendering must allow
  template-to-template rendering and functions that walk documents.
tags:
  - area: rendering
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:1313c47e2b32941fcd4e8c49a0686d821e0d4cfd24d679c84b1eeaafe7218827
---

## Context

Records come first. Reports and ordinary documents follow later, mostly prose written as Markdown
with Jinja2.

## Requirement

- Rendering can emit a document that still contains Jinja2 in its header, to be rendered again.
- The template environment stays open to functions that resolve include files, walk chapters and
  sections recursively and read their front matter.

## Goals

- Adding prose documents later needs no redesign of rendering.

## Stakeholders

- Future users of chancellor for reports and document templates.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
