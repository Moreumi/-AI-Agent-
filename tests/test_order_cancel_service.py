from app.data.sample_data import orders
from app.services.order_payment_service import check_order_cancel_eligibility


def test_cancelable_order():
    result = check_order_cancel_eligibility(
        orders=orders,
        customer_id=1,
        order_id=10001,
    )

    assert result["result_type"] == "success"
    assert result["cancel_judgment"] == "cancelable"
    assert result["reason"] is None


def test_in_transit_order_is_not_cancelable():
    result = check_order_cancel_eligibility(
        orders=orders,
        customer_id=3,
        order_id=10004,
    )

    assert result["result_type"] == "success"
    assert result["cancel_judgment"] == "not_cancelable"
    assert result["reason"] == "in_transit"


def test_delivered_order_is_not_cancelable():
    result = check_order_cancel_eligibility(
        orders=orders,
        customer_id=4,
        order_id=10005,
    )

    assert result["result_type"] == "success"
    assert result["cancel_judgment"] == "not_cancelable"
    assert result["reason"] == "delivered"


def test_already_canceled_order():
    result = check_order_cancel_eligibility(
        orders=orders,
        customer_id=2,
        order_id=10003,
    )

    assert result["result_type"] == "success"
    assert result["cancel_judgment"] == "already_canceled"
    assert result["reason"] == "already_canceled"