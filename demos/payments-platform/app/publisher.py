"""Publishes order events to MSK (ADR-0001)."""
import json
import logging

from confluent_kafka import Producer

log = logging.getLogger("order-api")

_producer = Producer({
    "bootstrap.servers": "b-1.payments.kafka.eu-west-1.amazonaws.com:9098",
    "acks": "all",
    "enable.idempotence": True,
})


def publish_order_created(order: dict) -> None:
    payload = {"order_id": order["id"], "amount": order["amount"], "currency": order["currency"]}
    _producer.produce("orders.v1", key=order["id"], value=json.dumps(payload))
    _producer.flush(5)
