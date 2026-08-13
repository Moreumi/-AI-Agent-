from copy import deepcopy

from app.data.sample_data import orders
from app.schemas.chat import UserRequest
import app.services.orchestrator as orchestrator


class FakeClassificationChain:

    def __init__(self, request: UserRequest):
        self.request = request

    def invoke(self, input_data):
        return self.request


def test_delivery_status_multi_turn_e2e(monkeypatch):
    """
    배송 상태 문의
    → 주문 여러 건
    → 주문 선택 요청
    → 사용자가 주문번호 선택
    → 배송 상태 조회
    → State 초기화

    전체 Multi-turn Flow를 검증한다.
    """

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    # -----------------------------------------------------
    # 1턴: 배송 상태 문의
    # -----------------------------------------------------

    request = UserRequest(
        intent="cs",
        cs_category="delivery",
        sub_intent="delivery_status",
        order_id=None,
    )

    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeClassificationChain(request),
    )

    first_result = orchestrator.route_request(
        user_input="내 주문 배송 상태 알려줘",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert first_result["route"] == "delivery_status"
    assert (
        first_result["result"]["result_type"]
        == "need_order_selection"
    )

    assert (
        test_state["pending_action"]
        == "delivery_status_selection"
    )

    candidate_order_ids = [
        order["order_id"]
        for order in test_state["candidate_orders"]
    ]

    assert candidate_order_ids == [10001, 10002]

    # -----------------------------------------------------
    # 2턴: 사용자가 주문번호 선택
    # -----------------------------------------------------

    second_result = orchestrator.route_request(
        user_input="10002번",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert second_result["route"] == "delivery_status"
    assert second_result["result"]["result_type"] == "success"

    assert second_result["result"]["order_id"] == 10002
    assert (
        second_result["result"]["delivery_status"]
        == "preparing_shipment"
    )

    assert "배송 준비 중" in second_result["response"]

    # -----------------------------------------------------
    # Flow 종료 후 State 초기화 확인
    # -----------------------------------------------------

    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}