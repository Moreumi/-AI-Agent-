from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_payment_method_change_guidance_flow():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="결제 수단을 변경하고 싶어",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "payment_method_change"

    assert (
        result["result"]["payment_method_change_judgment"]
        == "not_changeable"
    )

    assert (
        result["result"]["recommended_action"]
        == "cancel_and_reorder"
    )

    # 안내형 기능이므로 Multi-turn State를 만들지 않는다.
    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}