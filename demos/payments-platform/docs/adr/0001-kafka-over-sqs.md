---
id: "0001"
title: Kafka (MSK) over SQS for order and payment events
status: accepted
scope: repo
tags: [eda, messaging, aws]
enforce: must
date: 2026-04-02
owners: [payments-sre]
---
## Context
Order events need per-order ordering, replay for ledger rebuilds, and 4+ independent consumers.
SQS gives neither replay nor multi-consumer fan-out without SNS duplication.

## Decision
Order and payment events go to Amazon MSK (Kafka); SQS is not used for domain events.

## Rules
- Domain events publish to MSK topics `<domain>.v<N>` with key = aggregate id (`order_id`, `payment_id`).
- Producers use `acks=all` and `enable.idempotence=true`.
- Topic retention is at least 7 days.
- Each consumer has its own consumer group and a dead-letter topic `<topic>.dlt.<group>`.

## Consequences
MSK cost and partition planning; teams need Kafka client expertise.

## Exceptions
Third-party webhook buffering may use SQS (not a domain event).
