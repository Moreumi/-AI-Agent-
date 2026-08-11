from app.services.orchestrator import route_request
from app.services.state_service import state, reset_state
from app.data.sample_data import orders


def test_order_confirmation_multiturn_flow():

    # =========================================================
    # 테스트 시작 전 State 초기화
    # =========================================================

    reset_state(state)


    # =========================================================
    # 1턴
    # 주문번호 없이 주문 완료 여부 질문
    # =========================================================

    result1 = route_request(
        user_input="내 주문 제대로 들어갔어?",
        customer_id=1,
        orders=orders,
        state=state
    )


    # Routing 결과 확인
    assert result1["route"] == "order_confirmation"

    # 여러 주문이 있어 선택이 필요한지 확인
    assert result1["result"]["result_type"] == "need_order_selection"

    # State가 정상적으로 저장되었는지 확인
    assert state["pending_action"] == "order_confirmation"

    candidate_order_ids = [
        order["order_id"]
        for order in state["candidate_orders"]
    ]

    assert candidate_order_ids == [10001, 10002]


    # =========================================================
    # 2턴
    # 사용자가 주문번호 선택
    # =========================================================

    result2 = route_request(
        user_input="10002번",
        customer_id=1,
        orders=orders,
        state=state
    )


    # Routing 결과 확인
    assert result2["route"] == "order_confirmation"

    # 주문 조회 성공 여부 확인
    assert result2["result"]["result_type"] == "success"

    # 올바른 주문을 조회했는지 확인
    assert result2["result"]["order_id"] == 10002

    # 주문 완료 상태인지 확인
    assert result2["result"]["order_status"] == "order_completed"

    # 작업 완료 후 State가 초기화됐는지 확인
    assert state["pending_action"] is None
    assert state["candidate_orders"] == []