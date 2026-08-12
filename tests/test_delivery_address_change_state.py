from app.services.state_service import reset_state


def test_state_can_store_pending_delivery_address():

    test_state = {
        "pending_action": "collect_delivery_address",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {},
    }

    test_state["pending_data"]["new_delivery_address"] = (
        "서울시 강남구 테헤란로 123"
    )

    assert (
        test_state["pending_data"]["new_delivery_address"]
        == "서울시 강남구 테헤란로 123"
    )


def test_reset_state_clears_pending_data():

    test_state = {
        "pending_action": "confirm_delivery_address_change",
        "candidate_orders": [],
        "selected_order_id": 10001,
        "pending_data": {
            "new_delivery_address": "서울시 강남구 테헤란로 123"
        },
    }

    reset_state(test_state)

    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None
    assert test_state["pending_data"] == {}