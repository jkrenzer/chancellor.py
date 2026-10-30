---
title: Sample Data Must Be Reviewable
id: R0001
addressed_by:
  - D0001
  - S0001
short_title: Reviewable Data
description: Every change to the sample data can be reviewed as text.
tags: []
author: sample-team
date: '2026-10-02'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-02'
    description: Initial record.
data_hash: c1:sha256:7895da2b5db759b7296ceb2be734432e1da3b2b40c7d15bb70c138d468ea872b
---

## Context

Reviewers approve data changes in pull requests.

## Requirement

- Store data in a line-oriented text format.

## Goals

- A reviewer understands a data change from the diff alone, without running any tool or opening a
  second document to look up what a value means.

## Stakeholders

- Reviewers, who approve changes.

## Responsibility

- The sample team.

## References and Links

None.

## Notes

None.
