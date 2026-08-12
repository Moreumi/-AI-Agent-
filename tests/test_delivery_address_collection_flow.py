from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_address_is_stored_in_state_before_confirmation():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    # -----------------------------------------------------
    # 1턴: 배송지 변경 요청
    # -----------------------------------------------------

    first_result = route_request(
        user_input="10001번 주문 배송지 바꿔줘",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert first_result["route"] == "delivery_address_change"

    assert (
        test_state["pending_action"]
        == "collect_delivery_address"
    )

    assert test_state["selected_order_id"] == 10001

    # -----------------------------------------------------
    # 2턴: 새 배송지 입력
    # -----------------------------------------------------

    second_result = route_request(
        user_input="서울시 강남구 테헤란로 123",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert second_result["route"] == "delivery_address_change"

    assert (
        test_state["pending_action"]
        == "confirm_delivery_address_change"
    )

    assert (
        test_state["pending_data"]["new_delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    # -----------------------------------------------------
    # 실제 주문 데이터는 아직 변경되면 안 됨
    # -----------------------------------------------------

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    assert order["delivery_address"] == "서울시 성동구"


def test_empty_delivery_address_keeps_collection_state():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "collect_delivery_address",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {},
    }

    result = route_request(
        user_input="   ",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"

    assert (
        test_state["pending_action"]
        == "collect_delivery_address"
    )

    assert test_state["pending_data"] == {}