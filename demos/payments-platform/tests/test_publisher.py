from unittest import mock

import app.publisher as p


def test_publish_uses_order_id_key():
    with mock.patch.object(p, "_producer") as prod:
        p.publish_order_created({"id": "o-1", "amount": 100, "currency": "EUR"})
    assert prod.produce.call_args.kwargs["key"] == "o-1"
