---
title: Decision Documentation Core Document
id: D0000
short_title: Decision Core
description: Rules for the decision records of the sample project and their index.
tags: []
author: sample-team
date: '2026-10-01'
state: accepted
version: 1.0.0
revisions:
  - version: 1.0.0
    date: '2026-10-01'
    description: Initial record.
data_hash: c1:sha256:05679a32ee3702ec0188c254dda75c9bdfbd55d05b7d1c43e128c44ac1fa05dd
---

## Introduction

This document is the root of the decision documentation of the sample project.

## Rules

Following rules are to be applied to the files in this folder:

- One file covers one decision.
- A changed decision gets a new revision entry.

## Decisions

- [D0001: YAML Storage](D0001-yaml-storage.md): The sample data is kept in YAML files under version
  control.
  - Tags: `storage`, `area: data`
- [D0002: Render Documents Without Network Access](D0002-render-documents-without-network-access.md):
  Rendering works offline, from local data and templates only, so that a CI runner without network
  access produces the same documents as a developer's machine does.
