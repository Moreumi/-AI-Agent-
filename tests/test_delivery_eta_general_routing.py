from app.schemas.chat import UserRequest
from app.data.sample_data import orders

import app.services.orchestrator as orchestrator


class FakeClassificationChain:
    def invoke(self, input_data):
        return UserRequest(
            intent="cs",
            cs_category="delivery",
            sub_intent="delivery_eta",
            delivery_eta_scope="general",
            order_id=None,
        )


def test_delivery_eta_general_routing(monkeypatch):
    monkeypatch.setattr(
        orchestrator,
        "classification_chain",
        FakeClassificationChain(),
    )

    state = {
        "pending_action": None,
        "candidate_orders": [],
        "selected_order_id": None,
        "pending_data": {},
    }

    result = orchestrator.route_request(
        user_input="배송은 보통 얼마나 걸려?",
        orders=orders,
        customer_id=1,
        state=state,
    )

    assert result["route"] == "delivery_eta"

    assert result["request"]["sub_intent"] == "delivery_eta"
    assert result["request"]["delivery_eta_scope"] == "general"

    assert result["result"]["eta_judgment"] == "general_guidance"

    assert "3~5 영업일" in result["response"]
    assert "최대 7일" in result["response"]

    # 일반 정책 안내이므로 State를 만들지 않아야 한다.
    assert state["pending_action"] is None
    assert state["candidate_orders"] == []
    assert state["selected_order_id"] is None
    assert state["pending_data"] == {}