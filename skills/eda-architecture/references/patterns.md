# EDA patterns

| Pattern | When | Cost |
| --- | --- | --- |
| Transactional outbox | Must publish iff DB commit succeeds | Outbox table + relay (Debezium CDC or poller); at-least-once |
| Saga (orchestrated) | Multi-service workflow needing compensation and visibility | Orchestrator (Step Functions/Temporal) is a dependency |
| Saga (choreographed) | Few steps, loose coupling | Hard to trace; implicit workflow |
| CQRS + projections | Read model differs heavily from write model | Eventual consistency; rebuild tooling |
| Fan-out (pub/sub) | Many independent consumers of one fact | Per-consumer DLQ and lag monitoring |
| Competing consumers | Scale processing of one stream | Ordering only per partition/group key |
| Event-carried state transfer | Consumers need data without callbacks | Larger payloads; schema discipline |
| Claim check | Payload > broker limit (Kafka 1MB default, SQS 256KB) | S3 object lifecycle; extra read |
| Inbox / dedup table | Exactly-once effect on consumer side | Dedup store keyed by event id, TTL > max redelivery window |
