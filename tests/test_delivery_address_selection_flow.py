from copy import deepcopy

from app.data.sample_data import orders
from app.services.orchestrator import route_request


def test_delivery_address_change_selection_success():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "delivery_address_change_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "total_price": 49000,
                "delivery_address": "서울시 성동구",
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "total_price": 32000,
                "delivery_address": "서울시 성동구",
            },
        ],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = route_request(
        user_input="10001",
        customer_id=1,
        orders=test_orders,
        state=test_state,
    )

    assert result["route"] == "delivery_address_change"

    assert (
        test_state["pending_action"]
        == "collect_delivery_address"
    )

    assert test_state["selected_order_id"] == 10001
    assert test_state["candidate_orders"] == []


def test_invalid_delivery_address_order_selection_keeps_state():

    test_orders = deepcopy(orders)

    test_state = {
        "pending_action": "delivery_address_change_selection",
        "candidate_orders": [
            {
                "order_id": 10001,
                "order_date": "2026-08-08",
                "total_price": 49000,
                "delivery_address": "서울시 성동구",
            },
            {
                "order_id": 10002,
                "order_date": "2026-08-10",
                "total_price": 32000,
                "delivery_address": "서울시 성동구",
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

    assert result["route"] == "delivery_address_change"

    assert (
        test_state["pending_action"]
        == "delivery_address_change_selection"
    )

    assert test_state["selected_order_id"] is None