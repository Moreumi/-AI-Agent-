from app.data.sample_data import orders, payments
from app.services.orchestrator import handle_pending_state


# =========================================================
# 주문 수량 변경 - 주문 선택 후 기존 수량 요청 복구
# =========================================================

def test_order_change_selection_preserves_quantity_request():

    state = {
        "pending_action": "order_change_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "quantity": 1,
                "total_price": 49000,
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "quantity": 1,
                "total_price": 32000,
            },
        ],
        "selected_order_id": None,
        "pending_data": {
            "quantity_change_type": "increase",
            "quantity_value": 1,
        },
    }

    # -----------------------------------------------------
    # 두 번째 턴: 사용자가 주문번호 선택
    # -----------------------------------------------------

    result = handle_pending_state(
        user_input="10002번",
        customer_id=1,
        orders=orders,
        state=state,
        payments=payments,
    )

    # -----------------------------------------------------
    # Routing
    # -----------------------------------------------------

    assert result["route"] == "order_change"

    assert result["result"]["result_type"] == (
        "change_preview"
    )

    # -----------------------------------------------------
    # 첫 번째 턴의 increase / 1이 유지되었는지 확인
    # -----------------------------------------------------

    calculation = result["result"]["calculation"]

    assert calculation["current_quantity"] == 1
    assert calculation["target_quantity"] == 2

    assert calculation["current_total_price"] == 32000
    assert calculation["new_total_price"] == 64000

    assert (
        calculation["adjustment_type"]
        == "additional_payment_required"
    )

    assert calculation["adjustment_amount"] == 32000

    # -----------------------------------------------------
    # 다음 State → 최종 승인
    # -----------------------------------------------------

    assert state["pending_action"] == (
        "order_change_confirmation"
    )

    assert state["selected_order_id"] == 10002
    assert state["candidate_orders"] == []

    assert state["pending_data"]["target_quantity"] == 2
    assert state["pending_data"]["current_quantity"] == 1

    assert (
        state["pending_data"]["adjustment_type"]
        == "additional_payment_required"
    )

    assert state["pending_data"]["adjustment_amount"] == 32000

    # -----------------------------------------------------
    # 사용자 응답
    # -----------------------------------------------------

    assert "1개에서 2개로 변경" in result["response"]
    assert "추가 결제 필요 금액: 32,000원" in result["response"]
    assert "이대로 변경하시겠어요?" in result["response"]