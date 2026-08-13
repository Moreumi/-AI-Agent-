from copy import deepcopy

from app.data.sample_data import orders
from app.schemas.chat import UserRequest
import app.services.orchestrator as orchestrator


# =========================================================
# 테스트용 Classification Chain
# =========================================================

class FakeClassificationChain:

    def __init__(self, request: UserRequest):
        self.request = request

    def invoke(self, input_data):
        return self.request


# =========================================================
# 배송 상태 Routing 테스트
# =========================================================


def test_delivery_status_routes_with_explicit_order_id(
    monkeypatch,
):
    """
    Classification 결과가
    cs / delivery / delivery_status이고
    주문번호까지 존재하면

    Delivery Status Service로 바로 Routing되어야 한다.
    """

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    request = UserRequest(
        intent="cs",
        cs_category="delivery",
        sub_intent="delivery_status",
        order_id=10004,
    )

    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeClassificationChain(request),
    )

    result = orchestrator.route_request(
        user_input="10004번 주문 배송 상태 알려줘",
        customer_id=3,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_status"

    assert result["request"]["intent"] == "cs"
    assert result["request"]["cs_category"] == "delivery"
    assert result["request"]["sub_intent"] == "delivery_status"
    assert result["request"]["order_id"] == 10004

    assert result["result"]["result_type"] == "success"
    assert result["result"]["order_id"] == 10004
    assert result["result"]["delivery_status"] == "in_transit"

    # 주문 선택이 필요하지 않으므로 State 생성 X
    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []


def test_delivery_status_routes_to_order_selection(
    monkeypatch,
):
    """
    배송 상태 문의이지만 주문번호가 없고
    고객 주문이 여러 건이면

    배송 상태 조회 Flow를 종료하지 않고
    주문 선택 State를 생성해야 한다.
    """

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

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

    result = orchestrator.route_request(
        user_input="내 주문 배송 상태 알려줘",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_status"
    assert result["result"]["result_type"] == "need_order_selection"

    assert (
        test_state["pending_action"]
        == "delivery_status_selection"
    )

    candidate_order_ids = [
        order["order_id"]
        for order in test_state["candidate_orders"]
    ]

    assert candidate_order_ids == [10001, 10002]

    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}