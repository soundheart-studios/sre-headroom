---
name: eda-architecture
description: Use when designing or reviewing event-driven or messaging systems - Kafka, SQS/SNS, EventBridge, outbox, saga, CQRS, consumers, event schemas, ordering, DLQ. Not for implementing a single code change (code-change).
adr_tags: [eda, messaging, schema]
requires: [_style, _adr]
version: 1.1.0
---
# eda-architecture

## Step 0 (preloaded at skill load; do not re-read these files)
`_style` is already in context via CLAUDE.md; follow it exactly.
ADR constraints for this repo (resolved for this skill's tags; apply per the rules in the output):
!`~/.claude/skills/_adr/scripts/adr-resolve.sh --soft --tags eda,messaging,schema,aws,data`
Touching files whose type adds tags (e.g. `*.py`, `*.ts`, CI)? Re-run once with `--files <paths>`.
How to apply them:
!`cat ~/.claude/skills/_adr/SKILL.md`

## Workflow
1. Resolve ADRs. If an ADR fixes the broker, envelope, or schema registry, use it without
   re-debating; cite it. If the user asks to switch away, apply the `_adr` must-conflict rule.
2. Pick patterns from `references/patterns.md` (outbox, saga, CQRS, fan-out, competing consumers).
3. Compare brokers with `references/broker-compare.md` only when no ADR fixes the broker.
4. Walk all 8 failure modes in `references/failure-modes.md`. Every one gets a row.
5. Offer an `adr-author` draft if the design makes a significant decision no ADR covers.

## Output template
```text
Recommendation: <pattern + broker + key settings, one or two lines> (per ADR-<id> where applicable)

| Option | When | Cost |   <- trade-offs; omit options an ADR already rules out
| ... |

| Failure mode | Handling |
| Delivery semantics | ... |
| Idempotency | ... |
| Ordering | ... |
| DLQ / poison messages | ... |
| Backpressure | ... |
| Replay | ... |
| Schema evolution | ... |
| 1-hour consumer outage | ... |

Verify: <one test or metric that proves the design, e.g. consumer-lag alert, replay drill>
```

## References
- `references/patterns.md` - read to choose the pattern.
- `references/failure-modes.md` - read every time; all 8 rows are mandatory.
- `references/broker-compare.md` - read only when no ADR fixes the broker.

## Calibration
Bad: A broker comparison table recommending SQS when the repo has an accepted ADR choosing Kafka.
Good: "Recommendation: transactional outbox -> MSK topic `orders.v1`, key=order_id (per ADR-0001); consumers idempotent on CloudEvents id (per ADR-G-0005)." followed by the 8-row table.
