from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_payment_method_change_then_order_cancel_starts_new_flow():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    # =====================================================
    # 1턴: 결제수단 변경 문의
    # =====================================================

    first_result = route_request(
        user_input="결제 수단을 변경하고 싶어",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert first_result["route"] == "payment_method_change"

    assert (
        first_result["result"]["payment_method_change_judgment"]
        == "not_changeable"
    )

    # 결제수단 변경 문의는 안내 후 종료
    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}

    # =====================================================
    # 2턴: 사용자가 별도로 주문 취소 요청
    # =====================================================

    second_result = route_request(
        user_input="주문을 취소하고 싶어",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    # 이전 payment_method_change의 후속 처리가 아니라
    # 새로운 Intent로 order_cancel에 Routing되어야 한다.
    assert second_result["route"] == "order_cancel"

    # customer_id=1은 주문이 여러 건이므로
    # 기존 주문 취소 Flow의 주문 선택 단계로 이동
    assert (
        second_result["result"]["result_type"]
        == "need_order_selection"
    )

    assert (
        test_state["pending_action"]
        == "order_cancel_selection"
    )

    assert len(test_state["candidate_orders"]) > 0
    assert test_state["selected_order_id"] is None