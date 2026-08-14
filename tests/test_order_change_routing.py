from app.schemas.chat import UserRequest
from app.data.sample_data import (
    orders,
    payments,
    payment_adjustments,
)

import app.services.orchestrator as orchestrator


# =========================================================
# Fake Classification Chain
# =========================================================

class FakeOrderChangeWithIdChain:
    def invoke(self, input_data):
        return UserRequest(
            intent="cs",
            cs_category="order_payment",
            sub_intent="order_change",
            quantity_change_type="decrease",
            quantity_value=1,
            order_id=10007,
        )


# =========================================================
# 테스트용 State
# =========================================================

def create_state():
    return {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }


# =========================================================
# 주문번호 + 수량 요청이 모두 있는 경우
# → Preview 생성 후 최종 승인 State로 이동
# =========================================================

def test_order_change_initial_routing_to_confirmation(monkeypatch):

    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeOrderChangeWithIdChain(),
    )

    state = create_state()

    result = orchestrator.route_request(
        user_input="10007번 주문 1개 줄여줘",
        customer_id=6,
        orders=orders,
        state=state,
        payments=payments,
        payment_adjustments=payment_adjustments,
    )

    # ---------------------------------------------
    # Routing 확인
    # ---------------------------------------------

    assert result["route"] == "order_change"
    assert result["result"]["result_type"] == "change_preview"

    # ---------------------------------------------
    # 실제 계산 결과 확인
    # ---------------------------------------------

    calculation = result["result"]["calculation"]

    assert calculation["current_quantity"] == 3
    assert calculation["target_quantity"] == 2

    assert calculation["current_total_price"] == 60000
    assert calculation["new_total_price"] == 40000

    assert calculation["adjustment_type"] == (
        "partial_refund_required"
    )
    assert calculation["adjustment_amount"] == 20000

    # ---------------------------------------------
    # State 확인
    # ---------------------------------------------

    assert state["pending_action"] == (
        "order_change_confirmation"
    )

    assert state["selected_order_id"] == 10007

    assert state["candidate_orders"] == []

    assert state["pending_data"]["target_quantity"] == 2
    assert state["pending_data"]["current_quantity"] == 3

    assert (
        state["pending_data"]["adjustment_type"]
        == "partial_refund_required"
    )

    assert state["pending_data"]["adjustment_amount"] == 20000

    # ---------------------------------------------
    # 사용자 응답 확인
    # ---------------------------------------------

    assert "3개에서 2개로 변경" in result["response"]
    assert "부분 환불 예정 금액: 20,000원" in result["response"]
    assert "이대로 변경하시겠어요?" in result["response"]