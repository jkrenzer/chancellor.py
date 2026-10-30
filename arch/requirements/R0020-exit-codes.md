---
title: Every Command Returns Exit Codes From One Fixed Table
id: R0020
addressed_by:
  - D0010
  - D0029
  - S0005
short_title: Exit Codes
description: >-
  All commands use the same seven exit codes, documented in help and asserted in tests, so a script
  can tell a misconfiguration from a finding.
tags:
  - area: cli
author: jkrenzer
date: '2026-10-29'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-29'
    description: Initial record.
data_hash: c1:sha256:06fd7b13bf158ebd88e3185ca5b0e02cee02d896db234d37e795403cb81be555
---

## Context

A tool that returns the same code for every failure leaves hooks and check modes unable to react
correctly.

## Requirement

- Every command returns only codes of the exit-code table.
- The codes are documented in the CLI help and in the docstring of each command that can return
  them.
- Each code is asserted in tests.

## Goals

- CI distinguishes configuration errors, invalid input, drift, degradations and lint findings.

## Stakeholders

- Scripts, hooks and CI calling chancellor.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

None.
