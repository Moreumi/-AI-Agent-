from app.policies.delivery_address_change_policy import (
    judge_delivery_address_change,
)


def test_preparing_shipment_is_changeable():

    result = judge_delivery_address_change(
        order_status="order_completed",
        delivery_status="preparing_shipment",
    )

    assert result["address_change_judgment"] == "changeable"
    assert result["reason"] is None


def test_in_transit_is_not_changeable():

    result = judge_delivery_address_change(
        order_status="order_completed",
        delivery_status="in_transit",
    )

    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "in_transit"


def test_delivered_is_not_changeable():

    result = judge_delivery_address_change(
        order_status="order_completed",
        delivery_status="delivered",
    )

    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "delivered"


def test_canceled_order_is_not_changeable():

    result = judge_delivery_address_change(
        order_status="order_canceled",
        delivery_status="preparing_shipment",
    )

    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "order_canceled"


def test_failed_order_is_not_changeable():

    result = judge_delivery_address_change(
        order_status="order_failed",
        delivery_status="preparing_shipment",
    )

    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "order_failed"


def test_unknown_delivery_status_needs_review():

    result = judge_delivery_address_change(
        order_status="order_completed",
        delivery_status="unknown",
    )

    assert result["address_change_judgment"] == "needs_review"
    assert result["reason"] == "unknown_delivery_status"