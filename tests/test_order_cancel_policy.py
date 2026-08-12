from app.policies.order_cancel_policy import judge_order_cancel


def test_preparing_shipment_is_cancelable():
    result = judge_order_cancel(
        order_status="order_completed",
        delivery_status="preparing_shipment",
    )

    assert result["cancel_judgment"] == "cancelable"
    assert result["reason"] is None


def test_in_transit_is_not_cancelable():
    result = judge_order_cancel(
        order_status="order_completed",
        delivery_status="in_transit",
    )

    assert result["cancel_judgment"] == "not_cancelable"
    assert result["reason"] == "in_transit"


def test_delivered_is_not_cancelable():
    result = judge_order_cancel(
        order_status="order_completed",
        delivery_status="delivered",
    )

    assert result["cancel_judgment"] == "not_cancelable"
    assert result["reason"] == "delivered"