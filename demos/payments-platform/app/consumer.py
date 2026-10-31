"""Ledger consumer for orders.v1."""
import json
import logging

from confluent_kafka import Consumer

from app.ledger import record_entry

log = logging.getLogger("ledger-worker")


def run() -> None:
    c = Consumer({"bootstrap.servers": "b-1.payments.kafka.eu-west-1.amazonaws.com:9098",
                  "group.id": "ledger-worker", "enable.auto.commit": False})
    c.subscribe(["orders.v1"])
    while True:
        msg = c.poll(1.0)
        if msg is None or msg.error():
            continue
        try:
            event = json.loads(msg.value())
            record_entry(event["order_id"], event["amount"], event["currency"])
        except Exception:
            pass
        c.commit(msg)
