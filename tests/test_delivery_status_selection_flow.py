from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_status_selection_success():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "delivery_status_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "total_price": 49000,
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "total_price": 32000,
            },
        ],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="10002",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_status"
    assert result["result"]["result_type"] == "success"
    assert result["result"]["order_id"] == 10002
    assert result["result"]["delivery_status"] == "preparing_shipment"

    # 배송 상태 조회가 끝났으므로 State 초기화
    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}


def test_invalid_delivery_status_order_selection_keeps_state():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "delivery_status_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "total_price": 49000,
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "total_price": 32000,
            },
        ],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="99999",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_status"
    assert result["result"] is None

    # 잘못 선택했으므로 다시 선택할 수 있도록 State 유지
    assert (
        test_state["pending_action"]
        == "delivery_status_selection"
    )
    assert len(test_state["candidate_orders"]) == 2


def test_delivery_status_selection_without_order_id_keeps_state():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "delivery_status_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "total_price": 49000,
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "total_price": 32000,
            },
        ],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="첫 번째 거요",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_status"
    assert result["result"] is None

    assert (
        test_state["pending_action"]
        == "delivery_status_selection"
    )
    assert len(test_state["candidate_orders"]) == 2