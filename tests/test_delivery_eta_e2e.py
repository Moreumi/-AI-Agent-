from app.schemas.chat import UserRequest
from app.data.sample_data import orders

import app.services.orchestrator as orchestrator


class DeliveryEtaE2EClassificationChain:
    def __init__(self):
        self.call_count = 0

    def invoke(self, input_data):
        self.call_count += 1

        # 첫 번째 사용자 질문에서만 Classification이 실행되어야 한다.
        if self.call_count == 1:
            return UserRequest(
                intent="cs",
                cs_category="delivery",
                sub_intent="delivery_eta",
                delivery_eta_scope="order_specific",
                order_id=None,
            )

        raise AssertionError(
            "Pending State가 존재하는 두 번째 턴에서는 "
            "Intent Classification을 다시 호출하면 안 됩니다."
        )


def test_delivery_eta_two_turn_e2e(monkeypatch):

    fake_chain = DeliveryEtaE2EClassificationChain()

    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        fake_chain,
    )

    state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    # =====================================================
    # 1턴
    # =====================================================

    first_result = orchestrator.route_request(
        user_input="내 주문 언제 와?",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert first_result["route"] == "delivery_eta"

    assert (
        first_result["result"]["result_type"]
        == "need_order_selection"
    )

    assert state["pending_action"] == "delivery_eta_selection"

    candidate_ids = [
        order["order_id"]
        for order in state["candidate_orders"]
    ]

    assert candidate_ids == [10001, 10002]

    assert "주문을 선택해 주세요" in first_result["response"]

    # =====================================================
    # 2턴
    # =====================================================

    second_result = orchestrator.route_request(
        user_input="10002번",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert second_result["route"] == "delivery_eta"

    delivery_result = second_result["result"]["delivery_result"]
    eta_result = second_result["result"]["eta_result"]

    assert delivery_result["order_id"] == 10002
    assert delivery_result["delivery_status"] == "preparing_shipment"

    assert eta_result["eta_judgment"] == "policy_guidance"
    assert eta_result["reason"] == "preparing_shipment"

    assert "배송 준비 중" in second_result["response"]
    assert "3~5 영업일" in second_result["response"]

    # 두 번째 턴에서는 Classification이 다시 호출되지 않았어야 한다.
    assert fake_chain.call_count == 1

    # Flow 종료 후 State 초기화
    assert state["pending_action"] is None
    assert state["candidate_orders"] == []
    assert state["selected_order_id"] is None
    assert state["pending_data"] == {}