from app.services.orchestrator import route_request
from app.services.state_service import state, reset_state
from app.data.sample_data import orders, payments


def test_payment_confirmation_multiturn_flow():

    # =========================================================
    # 테스트 시작 전 State 초기화
    # =========================================================

    reset_state(state)


    # =========================================================
    # 1턴
    # 주문번호 없이 결제 완료 여부 질문
    # =========================================================

    result1 = route_request(
        user_input="결제 제대로 된 거야?",
        customer_id=1,
        orders=orders,
        state=state,
        payments=payments
    )


    # Routing 결과 확인
    assert result1["route"] == "payment_confirmation"

    # 여러 주문이 있어 선택이 필요한지 확인
    assert result1["result"]["result_type"] == "need_order_selection"

    # State가 결제 확인 흐름으로 저장되었는지 확인
    assert state["pending_action"] == "payment_confirmation"

    candidate_order_ids = [
        order["order_id"]
        for order in state["candidate_orders"]
    ]

    assert candidate_order_ids == [10001, 10002]


    # =========================================================
    # 2턴
    # 사용자가 결제를 확인할 주문번호 선택
    # =========================================================

    result2 = route_request(
        user_input="10002번",
        customer_id=1,
        orders=orders,
        state=state,
        payments=payments
    )


    # Routing 결과 확인
    assert result2["route"] == "payment_confirmation"

    # 결제 조회 성공 여부 확인
    assert result2["result"]["result_type"] == "success"

    # 올바른 주문의 결제를 조회했는지 확인
    assert result2["result"]["order_id"] == 10002

    # 결제번호 확인
    assert result2["result"]["payment_id"] == 50002

    # 결제 완료 상태 확인
    assert result2["result"]["payment_status"] == "payment_completed"

    # 결제금액 확인
    assert result2["result"]["payment_amount"] == 32000

    # 작업 완료 후 State 초기화 확인
    assert state["pending_action"] is None
    assert state["candidate_orders"] == []