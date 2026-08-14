from app.data.sample_data import orders, payments
from app.services.orchestrator import handle_pending_state


# =========================================================
# 주문 수량 변경 - 수량 추가 입력 후 Preview 생성
# =========================================================

def test_order_change_quantity_input_creates_preview():

    # 첫 턴에서 주문은 이미 특정됐지만
    # 사용자가 변경할 수량을 말하지 않은 상태
    state = {
        "pending_action": "order_change_quantity_input",
        "candidate_orders": [],
        "selected_order_id": 10007,
        "pending_data": {},
    }

    # -----------------------------------------------------
    # 두 번째 턴: 사용자가 변경할 수량 입력
    # -----------------------------------------------------

    result = handle_pending_state(
        user_input="2개로 바꿔줘",
        customer_id=6,
        orders=orders,
        state=state,
        payments=payments,
    )

    # -----------------------------------------------------
    # Routing / Preview 결과
    # -----------------------------------------------------

    assert result["route"] == "order_change"
    assert result["result"]["result_type"] == "change_preview"

    calculation = result["result"]["calculation"]

    assert calculation["current_quantity"] == 3
    assert calculation["target_quantity"] == 2

    assert calculation["current_total_price"] == 60000
    assert calculation["new_total_price"] == 40000

    assert (
        calculation["adjustment_type"]
        == "partial_refund_required"
    )

    assert calculation["adjustment_amount"] == 20000

    # -----------------------------------------------------
    # 다음 단계는 최종 승인
    # -----------------------------------------------------

    assert state["pending_action"] == (
        "order_change_confirmation"
    )

    assert state["selected_order_id"] == 10007
    assert state["candidate_orders"] == []

    assert state["pending_data"]["target_quantity"] == 2
    assert state["pending_data"]["current_quantity"] == 3

    assert state["pending_data"]["current_total_price"] == 60000
    assert state["pending_data"]["new_total_price"] == 40000

    assert (
        state["pending_data"]["adjustment_type"]
        == "partial_refund_required"
    )

    assert state["pending_data"]["adjustment_amount"] == 20000

    # -----------------------------------------------------
    # 사용자 응답
    # -----------------------------------------------------

    assert "3개에서 2개로 변경" in result["response"]
    assert "부분 환불 예정 금액: 20,000원" in result["response"]
    assert "이대로 변경하시겠어요?" in result["response"]

# =========================================================
# 현재와 동일한 수량
# → 변경 없음 안내 후 수량 입력 State 유지
# =========================================================

def test_order_change_quantity_input_same_quantity_keeps_state():

    state = {
        "pending_action": "order_change_quantity_input",
        "candidate_orders": [],
        "selected_order_id": 10007,
        "pending_data": {},
    }

    result = handle_pending_state(
        user_input="3개로 바꿔줘",
        customer_id=6,
        orders=orders,
        state=state,
        payments=payments,
    )

    assert result["route"] == "order_change"
    assert result["result"]["result_type"] == "no_change"

    # 다시 수량을 입력할 수 있도록 State 유지
    assert state["pending_action"] == "order_change_quantity_input"
    assert state["selected_order_id"] == 10007
    assert state["candidate_orders"] == []
    assert state["pending_data"] == {}

    assert "동일하여 변경할 내용이 없습니다" in result["response"]


# =========================================================
# 현재 수량보다 많이 감소
# → 음수 수량이므로 다시 입력
# =========================================================

def test_order_change_quantity_input_invalid_quantity_keeps_state():

    state = {
        "pending_action": "order_change_quantity_input",
        "candidate_orders": [],
        "selected_order_id": 10007,
        "pending_data": {},
    }

    result = handle_pending_state(
        user_input="4개 줄여줘",
        customer_id=6,
        orders=orders,
        state=state,
        payments=payments,
    )

    assert result["route"] == "order_change"
    assert result["result"]["result_type"] == "invalid_quantity"

    # 올바른 수량을 다시 입력하도록 State 유지
    assert state["pending_action"] == "order_change_quantity_input"
    assert state["selected_order_id"] == 10007
    assert state["candidate_orders"] == []
    assert state["pending_data"] == {}

    assert "0개보다 작아질 수 없습니다" in result["response"]


# =========================================================
# 수량 0
# → 주문 수량 변경이 아니라 주문 취소 필요
# → order_change State 종료
# =========================================================

def test_order_change_quantity_input_zero_requires_cancel():

    state = {
        "pending_action": "order_change_quantity_input",
        "candidate_orders": [],
        "selected_order_id": 10007,
        "pending_data": {},
    }

    result = handle_pending_state(
        user_input="0개로 바꿔줘",
        customer_id=6,
        orders=orders,
        state=state,
        payments=payments,
    )

    assert result["route"] == "order_change"
    assert result["result"]["result_type"] == "cancel_required"

    # order_change에서는 자동 취소하지 않고 흐름 종료
    assert state["pending_action"] is None
    assert state["selected_order_id"] is None
    assert state["candidate_orders"] == []
    assert state["pending_data"] == {}

    assert "주문 취소가 필요합니다" in result["response"]