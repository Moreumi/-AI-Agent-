from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_address_change_approve_executes_action():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "confirm_delivery_address_change",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {
            "new_delivery_address": "서울시 강남구 테헤란로 123"
        },
    }

    result = route_request(
        user_input="예",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"
    assert result["result"]["result_type"] == "success"

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    # 최종 승인 후 실제 주소 변경
    assert (
        order["delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    # 처리 완료 후 State 초기화
    assert test_state["pending_action"] is None
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}


def test_delivery_address_change_reject_does_not_execute_action():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "confirm_delivery_address_change",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {
            "new_delivery_address": "서울시 강남구 테헤란로 123"
        },
    }

    result = route_request(
        user_input="아니오",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"
    assert result["result"]["result_type"] == "change_aborted"

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    # 거절했으므로 기존 주소 유지
    assert order["delivery_address"] == "서울시 성동구"

    # Flow 종료
    assert test_state["pending_action"] is None
    assert test_state["pending_data"] == {}


def test_delivery_address_change_ambiguous_keeps_confirmation_state():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "confirm_delivery_address_change",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {
            "new_delivery_address": "서울시 강남구 테헤란로 123"
        },
    }

    result = route_request(
        user_input="잠깐만요",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"

    # 승인 여부가 명확하지 않으므로 State 유지
    assert (
        test_state["pending_action"]
        == "confirm_delivery_address_change"
    )

    assert test_state["selected_order_id"] == 10001

    assert (
        test_state["pending_data"]["new_delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    # 아직 승인되지 않았으므로 실제 주소 변경 X
    assert order["delivery_address"] == "서울시 성동구"