from copy import deepcopy

from app.data.sample_data import orders
from app.services.order_payment_service import (
    change_delivery_address,
)


def test_change_delivery_address_success():

    test_orders = deepcopy(orders)

    result = change_delivery_address(
        orders=test_orders,
        customer_id=1,
        order_id=10001,
        new_delivery_address="서울시 강남구 테헤란로 123",
    )

    assert result["result_type"] == "success"
    assert (
        result["previous_delivery_address"]
        == "서울시 성동구"
    )
    assert (
        result["new_delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    assert (
        order["delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )


def test_change_delivery_address_rechecks_status_before_action():

    test_orders = deepcopy(orders)

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    # 처음 조회 후 실제 Action 전에
    # 배송이 시작됐다고 가정
    order["delivery_status"] = "in_transit"

    result = change_delivery_address(
        orders=test_orders,
        customer_id=1,
        order_id=10001,
        new_delivery_address="서울시 강남구 테헤란로 123",
    )

    assert result["result_type"] == "action_failed"
    assert result["reason"] == "in_transit"

    # 실제 배송지는 변경되면 안 됨
    assert order["delivery_address"] == "서울시 성동구"


def test_change_delivery_address_order_not_found():

    test_orders = deepcopy(orders)

    result = change_delivery_address(
        orders=test_orders,
        customer_id=1,
        order_id=99999,
        new_delivery_address="서울시 강남구 테헤란로 123",
    )

    assert result["result_type"] == "action_failed"
    assert result["reason"] == "order_not_found"


def test_change_delivery_address_rejects_empty_address():

    test_orders = deepcopy(orders)

    result = change_delivery_address(
        orders=test_orders,
        customer_id=1,
        order_id=10001,
        new_delivery_address="   ",
    )

    assert result["result_type"] == "action_failed"
    assert result["reason"] == "invalid_delivery_address"