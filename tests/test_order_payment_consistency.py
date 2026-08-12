import app.services.orchestrator as orchestrator

from app.services.order_payment_service import (
    check_order_completion,
    check_payment_completion,
    check_order_payment_consistency,
)


def test_order_payment_inconsistency_routes_to_narrative_guidance(
    monkeypatch,
):
    # -----------------------------------------------------
    # 1. 의도적으로 주문/결제 상태가 불일치하는 데이터 생성
    # -----------------------------------------------------

    orders = [
        {
            "order_id": 90001,
            "customer_id": 1,
            "order_status": "order_completed",
            "order_date": "2026-08-11",
            "total_price": 32000,
            "delivery_status": "before_shipping",
        }
    ]

    payments = [
        {
            "payment_id": 59001,
            "order_id": 90001,
            "payment_method": "card",
            "payment_amount": 32000,
            "payment_status": "payment_failed",
            "payment_date": "2026-08-11",
        }
    ]

    # -----------------------------------------------------
    # 2. 주문 자체 상태 판정
    # -----------------------------------------------------

    order_result = check_order_completion(
        orders=orders,
        customer_id=1,
        order_id=90001,
    )

    assert order_result["judgment"] == "completed"

    # -----------------------------------------------------
    # 3. 주문-결제 일관성 판정
    # -----------------------------------------------------

    consistency_result = check_order_payment_consistency(
        orders=orders,
        payments=payments,
        customer_id=1,
        order_id=90001,
    )

    assert consistency_result["consistency_judgment"] == "needs_review"

    # -----------------------------------------------------
    # 4. 실제 LLM 대신 가짜 함수 사용
    # -----------------------------------------------------

    captured = {}

    def fake_generate_cs_response(**kwargs):
        captured["response_mode"] = kwargs["response_mode"]
        return "mock response"

    monkeypatch.setattr(
        orchestrator,
        "generate_cs_response",
        fake_generate_cs_response,
    )

    # -----------------------------------------------------
    # 5. Orchestrator의 응답 방식 확인
    # -----------------------------------------------------

    response = orchestrator.build_order_confirmation_response(
        user_input="내 주문 제대로 들어갔어?",
        result=order_result,
        consistency_result=consistency_result,
    )

    assert captured["response_mode"] == "narrative_guidance"
    assert response == "mock response"


#########두 번째 test#####
def test_payment_order_inconsistency_routes_to_narrative_guidance(
    monkeypatch,
):
    # -----------------------------------------------------
    # 1. 의도적으로 주문/결제 상태가 불일치하는 데이터 생성
    # -----------------------------------------------------

    orders = [
        {
            "order_id": 90002,
            "customer_id": 1,
            "order_status": "order_failed",
            "order_date": "2026-08-11",
            "total_price": 45000,
            "delivery_status": "before_shipping",
        }
    ]

    payments = [
        {
            "payment_id": 59002,
            "order_id": 90002,
            "payment_method": "card",
            "payment_amount": 45000,
            "payment_status": "payment_completed",
            "payment_date": "2026-08-11",
        }
    ]

    # -----------------------------------------------------
    # 2. 결제 자체 상태 판정
    # -----------------------------------------------------

    payment_result = check_payment_completion(
        orders=orders,
        payments=payments,
        customer_id=1,
        order_id=90002,
    )

    assert payment_result["judgment"] == "completed"

    # -----------------------------------------------------
    # 3. 주문-결제 일관성 판정
    # -----------------------------------------------------

    consistency_result = check_order_payment_consistency(
        orders=orders,
        payments=payments,
        customer_id=1,
        order_id=90002,
    )

    assert consistency_result["consistency_judgment"] == "needs_review"

    # -----------------------------------------------------
    # 4. 실제 LLM 대신 테스트용 가짜 함수 사용
    # -----------------------------------------------------

    captured = {}

    def fake_generate_cs_response(**kwargs):
        captured["response_mode"] = kwargs["response_mode"]
        return "mock response"

    monkeypatch.setattr(
        orchestrator,
        "generate_cs_response",
        fake_generate_cs_response,
    )

    # -----------------------------------------------------
    # 5. 결제 응답 방식 확인
    # -----------------------------------------------------

    response = orchestrator.build_payment_confirmation_response(
        user_input="결제 제대로 된 거야?",
        result=payment_result,
        consistency_result=consistency_result,
    )

    assert captured["response_mode"] == "narrative_guidance"
    assert response == "mock response"