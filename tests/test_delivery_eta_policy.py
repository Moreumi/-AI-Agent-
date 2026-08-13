from app.policies.delivery_eta_policy import (
    get_general_delivery_eta_policy,
    judge_order_delivery_eta,
)


def test_general_delivery_eta_policy():
    result = get_general_delivery_eta_policy()

    assert result["eta_judgment"] == "general_guidance"
    assert result["standard_delivery_days"] == "3~5 영업일"
    assert result["remote_area_delivery_days"] == "최대 7일"


def test_order_eta_preparing_shipment():
    result = judge_order_delivery_eta(
        order_status="order_completed",
        delivery_status="preparing_shipment",
    )

    assert result["eta_judgment"] == "policy_guidance"
    assert result["reason"] == "preparing_shipment"


def test_order_eta_in_transit():
    result = judge_order_delivery_eta(
        order_status="order_completed",
        delivery_status="in_transit",
    )

    assert result["eta_judgment"] == "policy_guidance"
    assert result["reason"] == "in_transit"


def test_order_eta_delivered():
    result = judge_order_delivery_eta(
        order_status="order_completed",
        delivery_status="delivered",
    )

    assert result["eta_judgment"] == "already_delivered"
    assert result["reason"] == "delivered"


def test_order_eta_canceled():
    result = judge_order_delivery_eta(
        order_status="order_canceled",
        delivery_status="preparing_shipment",
    )

    assert result["eta_judgment"] == "not_applicable"
    assert result["reason"] == "order_canceled"


def test_order_eta_failed():
    result = judge_order_delivery_eta(
        order_status="order_failed",
        delivery_status="preparing_shipment",
    )

    assert result["eta_judgment"] == "not_applicable"
    assert result["reason"] == "order_failed"


def test_order_eta_unknown_delivery_status():
    result = judge_order_delivery_eta(
        order_status="order_completed",
        delivery_status="unknown_status",
    )

    assert result["eta_judgment"] == "needs_review"
    assert result["reason"] == "unknown_delivery_status"