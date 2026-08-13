from app.data.sample_data import orders

import app.services.orchestrator as orchestrator


class FailClassificationChain:
    def invoke(self, input_data):
        raise AssertionError(
            "Pending State 처리 중에는 "
            "새로운 Intent Classification을 호출하면 안 됩니다."
        )


def create_delivery_eta_selection_state():
    return {
        "pending_action": "delivery_eta_selection",
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


def test_delivery_eta_valid_order_selection(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FailClassificationChain(),
    )

    state = create_delivery_eta_selection_state()

    result = orchestrator.route_request(
        user_input="10002번",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert result["route"] == "delivery_eta"

    delivery_result = result["result"]["delivery_result"]
    eta_result = result["result"]["eta_result"]

    assert delivery_result["order_id"] == 10002
    assert delivery_result["delivery_status"] == "preparing_shipment"

    assert eta_result["eta_judgment"] == "policy_guidance"
    assert eta_result["reason"] == "preparing_shipment"

    assert "배송 준비 중" in result["response"]
    assert "3~5 영업일" in result["response"]

    # Flow 종료 후 State 초기화
    assert state["pending_action"] is None
    assert state["candidate_orders"] == []
    assert state["selected_order_id"] is None
    assert state["pending_data"] == {}


def test_delivery_eta_invalid_order_selection(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FailClassificationChain(),
    )

    state = create_delivery_eta_selection_state()

    result = orchestrator.route_request(
        user_input="99999번",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert result["route"] == "delivery_eta"
    assert result["result"] is None

    # 잘못 선택했으므로 State 유지
    assert state["pending_action"] == "delivery_eta_selection"
    assert len(state["candidate_orders"]) == 2


def test_delivery_eta_selection_without_order_id(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FailClassificationChain(),
    )

    state = create_delivery_eta_selection_state()

    result = orchestrator.route_request(
        user_input="첫 번째 거요",
        customer_id=1,
        orders=orders,
        state=state,
    )

    assert result["route"] == "delivery_eta"
    assert result["result"] is None

    # 주문번호를 명확히 입력하지 않았으므로 State 유지
    assert state["pending_action"] == "delivery_eta_selection"
    assert len(state["candidate_orders"]) == 2