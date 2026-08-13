from app.schemas.chat import UserRequest
from app.data.sample_data import orders

import app.services.orchestrator as orchestrator


class FakeOrderSpecificWithIdChain:
    def invoke(self, input_data):
        return UserRequest(
            intent="cs",
            cs_category="delivery",
            sub_intent="delivery_eta",
            delivery_eta_scope="order_specific",
            order_id=10004,
        )


class FakeOrderSpecificWithoutIdChain:
    def invoke(self, input_data):
        return UserRequest(
            intent="cs",
            cs_category="delivery",
            sub_intent="delivery_eta",
            delivery_eta_scope="order_specific",
            order_id=None,
        )


def create_state():
    return {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }


def test_delivery_eta_order_specific_with_order_id(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeOrderSpecificWithIdChain(),
    )

    state = create_state()

    result = orchestrator.route_request(
        user_input="10004번 주문 언제 도착해?",
        customer_id=3,
        orders=orders,
        state=state,
    )

    assert result["route"] == "delivery_eta"

    assert (
        result["result"]["delivery_result"]["order_id"]
        == 10004
    )

    assert (
        result["result"]["delivery_result"]["delivery_status"]
        == "in_transit"
    )

    assert (
        result["result"]["eta_result"]["eta_judgment"]
        == "policy_guidance"
    )

    assert "현재 배송 중" in result["response"]

    # 주문이 바로 특정되었으므로 State 생성 X
    assert state["pending_action"] is None


def test_delivery_eta_order_specific_needs_selection(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeOrderSpecificWithoutIdChain(),
    )

    state = create_state()

    result = orchestrator.route_request(
        user_input="내 주문 언제 와?",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert result["route"] == "delivery_eta"

    assert result["result"]["result_type"] == "need_order_selection"

    assert state["pending_action"] == "delivery_eta_selection"

    candidate_ids = [
        order["order_id"]
        for order in state["candidate_orders"]
    ]

    assert candidate_ids == [10001, 10002]

    assert "주문을 선택해 주세요" in result["response"]