---
title: Every Existing Verb and Agent Tool Stays Available From the Installed Command
id: R0002
addressed_by:
  - D0026
short_title: Verbs and Agent Tools
description: >-
  The `render`, `schema`, `hash`, `build`, `lint` and `serve` verbs stay available from the
  installed console script, and the nine agent tools keep their names and arguments.
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
data_hash: c1:sha256:faf78d9540c27537bb5e2a92032da4524d31efccc7554b269a33eeae5d1c9762
---

## Context

Scripts, task runners and agent configurations call chancellor's verbs and its nine agent tools by
name, so those names are a contract.

## Requirement

- A console script `chancellor` offers `render`, `schema`, `hash`, `build`, `lint` and `serve`. New
  verbs and exit codes are additions.
- The MCP server starts from the installed command and offers the nine agent tools with their names
  and arguments; authority flags decide which tools appear.
- The `adr`, `arr` and `asr` kind names, with their `-core` forms, stay usable as aliases.
- A generic `render_record` tool renders a record of any registered kind, provider kinds included.
- The pydantic-ai toolset sits behind an optional extra; chancellor never imports pydantic-ai at
  module level.

## Goals

- A project calls chancellor through its installed command, from scripts, task runners and
  `.mcp.json`.

## Stakeholders

- Authors and AI agents writing records through the CLI or MCP tools.

## Responsibility

- Jörn Krenzer (jkrenzer), chancellor maintainer.

## References and Links

None.

## Notes

`serve` and the MCP tools are not built yet. `hash` and `schema` take the arguments recorded in
D0026.
