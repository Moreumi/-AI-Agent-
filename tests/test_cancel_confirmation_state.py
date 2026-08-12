from app.services.state_service import (
    extract_confirmation,
    reset_state,
)


def test_cancel_confirmation_approve():
    assert extract_confirmation("예") is True
    assert extract_confirmation("네") is True


def test_cancel_confirmation_reject():
    assert extract_confirmation("아니오") is False
    assert extract_confirmation("아니요") is False


def test_cancel_confirmation_ambiguous():
    assert extract_confirmation("잘 모르겠어요") is None


def test_reset_state_clears_selected_order():
    test_state = {
        "pending_action": "confirm_cancel",
        "candidate_orders": [],
        "selected_order_id": 10001,
    }

    reset_state(test_state)

    assert test_state["pending_action"] is None
    assert test_state["candidate_orders"] == []
    assert test_state["selected_order_id"] is None