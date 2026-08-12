from app.data.sample_data import orders
from app.services.order_payment_service import (
    check_delivery_address_change_eligibility,
)


def test_delivery_address_change_is_changeable():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=1,
        order_id=10001,
    )

    assert result["result_type"] == "success"
    assert result["order_id"] == 10001
    assert result["address_change_judgment"] == "changeable"
    assert result["reason"] is None
    assert result["delivery_address"] == "서울시 성동구"


def test_in_transit_order_is_not_changeable():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=3,
        order_id=10004,
    )

    assert result["result_type"] == "success"
    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "in_transit"


def test_delivered_order_is_not_changeable():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=4,
        order_id=10005,
    )

    assert result["result_type"] == "success"
    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "delivered"


def test_canceled_order_is_not_changeable():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=2,
        order_id=10003,
    )

    assert result["result_type"] == "success"
    assert result["address_change_judgment"] == "not_changeable"
    assert result["reason"] == "order_canceled"


def test_delivery_address_change_order_not_found():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=1,
        order_id=99999,
    )

    assert result["result_type"] == "not_found"


def test_delivery_address_change_requires_order_selection():

    result = check_delivery_address_change_eligibility(
        orders=orders,
        customer_id=1,
    )

    assert result["result_type"] == "need_order_selection"
    assert len(result["candidate_orders"]) == 2