from app.services.orchestrator import route_request
from app.services.state_service import state, reset_state
from app.data.sample_data import orders


def test_order_cancel_waits_for_confirmation():

    # 테스트 시작 전 State 초기화
    reset_state(state)

    result = route_request(
        user_input="10001번 주문 취소해줘",
        customer_id=1,
        orders=orders,
        state=state,
    )

    # 주문 취소 Flow로 Routing 되었는지
    assert result["route"] == "order_cancel"

    # 주문 조회가 성공했는지
    assert result["result"]["result_type"] == "success"

    # 취소 가능한 주문인지
    assert result["result"]["cancel_judgment"] == "cancelable"

    # 중요:
    # 바로 취소하지 않고 최종 승인을 기다리는 상태인지
    assert state["pending_action"] == "confirm_cancel"

    # 어떤 주문을 취소하려는지 기억하고 있는지
    assert state["selected_order_id"] == 10001

    # 주문 데이터는 아직 변경되지 않아야 함
    order = next(
        order
        for order in orders
        if order["order_id"] == 10001
    )

    assert order["order_status"] == "order_completed"