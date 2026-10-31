---
id: G-0005
title: CloudEvents envelope with registered schemas
status: accepted
scope: global
tags: [eda, schema, messaging]
enforce: must
date: 2026-03-10
owners: [platform-eda]
---
## Context
Consumers broke on unannounced payload changes.

## Decision
All events use the CloudEvents 1.0 envelope and a schema registered before first publish.

## Rules
- Events carry `id`, `source`, `type`, `specversion`, `time`; `type` is reverse-DNS and versioned (`com.acme.order.created.v1`).
- Payload schema is registered (Glue Schema Registry or Confluent) with BACKWARD compatibility.
- Breaking changes publish a new `type` version; old version is dual-published until consumers migrate.
- Consumers are idempotent on CloudEvents `id`.

## Consequences
Registry dependency in the publish path.

## Exceptions
None.
