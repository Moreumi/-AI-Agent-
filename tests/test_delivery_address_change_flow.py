from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_address_change_starts_address_collection():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="10001번 주문 배송지 바꿔줘",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"

    assert result["result"]["result_type"] == "success"
    assert (
        result["result"]["address_change_judgment"]
        == "changeable"
    )

    # 다음 턴에서 새 주소를 기다리는 상태
    assert (
        test_state["pending_action"]
        == "collect_delivery_address"
    )
    assert test_state["selected_order_id"] == 10001
    assert test_state["pending_data"] == {}

    # 아직 실제 주소는 변경되면 안 됨
    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    assert order["delivery_address"] == "서울시 성동구"