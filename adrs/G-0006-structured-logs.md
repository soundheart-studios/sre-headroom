---
id: G-0006
title: Structured JSON logs with trace correlation
status: accepted
scope: global
tags: [observability, code]
enforce: should
date: 2026-03-10
owners: [platform-observability]
---
## Context
Free-text logs are not queryable across services.

## Decision
Services log JSON to stdout with trace correlation.

## Rules
- One JSON object per line with `ts`, `level`, `msg`, `service`, `trace_id`, `span_id`.
- No secrets or full PII in logs; mask card numbers and emails.
- Errors log once, at the boundary that handles them.

## Consequences
Less human-readable local output without a formatter.

## Exceptions
CLI tools may log text.
