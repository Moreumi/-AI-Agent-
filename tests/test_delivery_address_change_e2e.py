from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_address_change_full_e2e():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    # =====================================================
    # 1턴: 배송지 변경 요청
    # =====================================================

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

    # 아직 주소는 변경되지 않아야 함
    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    assert order["delivery_address"] == "서울시 성동구"

    # =====================================================
    # 2턴: 새 배송지 입력
    # =====================================================

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

    # 새 주소를 입력했지만 아직 승인 전이므로 변경 X
    assert order["delivery_address"] == "서울시 성동구"

    # =====================================================
    # 3턴: 사용자 최종 승인
    # =====================================================

    third_result = route_request(
        user_input="예",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert third_result["route"] == "delivery_address_change"
    assert third_result["result"]["result_type"] == "success"

    # =====================================================
    # 실제 Write Action 결과 확인
    # =====================================================

    assert (
        order["delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    assert (
        third_result["result"]["previous_delivery_address"]
        == "서울시 성동구"
    )

    assert (
        third_result["result"]["new_delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )

    # =====================================================
    # 처리 완료 후 State 초기화 확인
    # =====================================================

    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}