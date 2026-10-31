# Broker comparison (only when no ADR fixes the broker)

| Option | When | Cost |
| --- | --- | --- |
| Kafka (MSK / MSK Serverless / Confluent) | Ordered streams, replay, many consumer groups, high throughput | Ops/partition planning; per-broker cost |
| SQS standard | Work queues, simple decoupling, per-message ack | No replay; no ordering; 256KB |
| SQS FIFO | Ordered per group, dedup window 5 min | Lower throughput per group (high-throughput mode helps) |
| SNS -> SQS | Fan-out to queues | No replay; filter policies |
| EventBridge | Cross-account / SaaS routing, rules | Latency ~0.5s; 256KB; archive/replay coarse |
| Kinesis Data Streams | AWS-native ordered stream, Lambda consumers | Shard management; 7-365 day retention costs |
