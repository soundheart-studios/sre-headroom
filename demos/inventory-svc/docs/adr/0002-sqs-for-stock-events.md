---
id: "0002"
title: SQS for stock-change events
status: proposed
scope: repo
tags: [eda, messaging, aws]
enforce: must
date: 2026-09-20
owners: [catalog-team]
---
## Context
Only one consumer (search indexer) needs stock changes today.

## Decision
Publish stock-change events to an SQS standard queue.

## Rules
- Stock events go to SQS queue `inventory-stock-events-<env>`.

## Consequences
No replay; adding consumers needs SNS fan-out.

## Exceptions
None.
