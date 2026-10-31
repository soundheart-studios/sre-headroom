# Failure modes (all 8 are mandatory in every design answer)

| # | Failure mode | Question to answer | Typical handling |
| --- | --- | --- | --- |
| 1 | Delivery semantics | At-most / at-least / effectively-once? | At-least-once + idempotent consumers; Kafka idempotent producer, `acks=all` |
| 2 | Idempotency | What happens on redelivery? | Dedup on event id (CloudEvents `id`) in inbox table; upserts |
| 3 | Ordering | What must be ordered, by what key? | Partition key = aggregate id; SQS FIFO `MessageGroupId`; no global order |
| 4 | DLQ / poison messages | Where do failures go, who redrives? | Bounded retries with backoff -> DLQ/DLT; alert on depth; redrive runbook |
| 5 | Backpressure | Consumer slower than producer? | Lag-based autoscaling (KEDA); max in-flight; bounded queues |
| 6 | Replay | Can we reprocess history? | Retention >= recovery window; offset reset per group; replay safe due to idempotency |
| 7 | Schema evolution | How do payloads change without breaking consumers? | Registry with BACKWARD compat; new versioned type for breaking change |
| 8 | 1-hour consumer outage | Is data lost, what happens on recovery? | Retention >> 1h; lag alert; catch-up rate math (backlog / (consume - produce rate)) |
