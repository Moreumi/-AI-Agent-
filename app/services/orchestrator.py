from app.services.llm_service import classification_chain

from app.services.order_payment_service import (
    check_order_completion,
    generate_order_response,
    check_payment_completion,
    generate_payment_response
)

from app.services.state_service import (
    reset_state,
    extract_order_id
)


# =========================================================
# 이전 대화에서 진행 중인 작업 처리
# =========================================================

def handle_pending_state(
    user_input: str,
    customer_id: int,
    orders: list[dict],
    state: dict,
    payments: list[dict] | None = None
) -> dict | None:

    # 진행 중인 작업이 없으면 일반 Routing으로 이동
    if state["pending_action"] is None:
        return None


    # =====================================================
    # 주문 완료 확인 후속 처리
    # =====================================================

    if state["pending_action"] == "order_confirmation":

        selected_order_id = extract_order_id(user_input)

        if selected_order_id is None:
            return {
                "route": "order_confirmation",
                "result": None,
                "response": "확인할 주문번호를 입력해주세요."
            }

        candidate_order_ids = [
            order["order_id"]
            for order in state["candidate_orders"]
        ]

        if selected_order_id not in candidate_order_ids:
            return {
                "route": "order_confirmation",
                "result": None,
                "response": "선택 가능한 주문번호 중에서 다시 선택해주세요."
            }

        result = check_order_completion(
            orders=orders,
            customer_id=customer_id,
            order_id=selected_order_id
        )

        response = generate_order_response(result)

        reset_state(state)

        return {
            "route": "order_confirmation",
            "result": result,
            "response": response
        }


    # =====================================================
    # 결제 완료 확인 후속 처리
    # =====================================================

    if state["pending_action"] == "payment_confirmation":

        selected_order_id = extract_order_id(user_input)

        if selected_order_id is None:
            return {
                "route": "payment_confirmation",
                "result": None,
                "response": "결제 여부를 확인할 주문번호를 입력해주세요."
            }

        candidate_order_ids = [
            order["order_id"]
            for order in state["candidate_orders"]
        ]

        if selected_order_id not in candidate_order_ids:
            return {
                "route": "payment_confirmation",
                "result": None,
                "response": "선택 가능한 주문번호 중에서 다시 선택해주세요."
            }

        if payments is None:
            return {
                "route": "payment_confirmation",
                "result": None,
                "response": "결제 데이터를 확인할 수 없습니다."
            }

        result = check_payment_completion(
            orders=orders,
            payments=payments,
            customer_id=customer_id,
            order_id=selected_order_id
        )

        response = generate_payment_response(result)

        reset_state(state)

        return {
            "route": "payment_confirmation",
            "result": result,
            "response": response
        }

    return None


# =========================================================
# 전체 사용자 요청 Routing
# =========================================================

def route_request(
    user_input: str,
    customer_id: int,
    orders: list[dict],
    state: dict,
    payments: list[dict] | None = None
) -> dict:

    # ---------------------------------------------------------
    # 1. 이전 대화에서 진행 중인 작업이 있는지 먼저 확인
    # ---------------------------------------------------------

    pending_result = handle_pending_state(
        user_input=user_input,
        customer_id=customer_id,
        orders=orders,
        state=state,
        payments=payments
    )

    if pending_result is not None:
        return pending_result


    # ---------------------------------------------------------
    # 2. 새로운 사용자 질문 분류
    # ---------------------------------------------------------

    request = classification_chain.invoke(
        {
            "user_input": user_input
        }
    )


    # =========================================================
    # 주문 완료 확인
    # =========================================================

    if (
        request.intent == "cs"
        and request.cs_category == "order_payment"
        and request.sub_intent == "order_confirmation"
    ):

        result = check_order_completion(
            orders=orders,
            customer_id=customer_id,
            order_id=request.order_id
        )

        if result["result_type"] == "need_order_selection":
            state["pending_action"] = "order_confirmation"
            state["candidate_orders"] = result["candidate_orders"]

        response = generate_order_response(result)

        return {
            "route": "order_confirmation",
            "request": request.model_dump(),
            "result": result,
            "response": response
        }


    # =========================================================
    # 결제 완료 확인
    # =========================================================

    if (
        request.intent == "cs"
        and request.cs_category == "order_payment"
        and request.sub_intent == "payment_confirmation"
    ):

        if payments is None:
            return {
                "route": "payment_confirmation",
                "request": request.model_dump(),
                "result": None,
                "response": "결제 데이터를 확인할 수 없습니다."
            }

        result = check_payment_completion(
            orders=orders,
            payments=payments,
            customer_id=customer_id,
            order_id=request.order_id
        )

        if result["result_type"] == "need_order_selection":
            state["pending_action"] = "payment_confirmation"
            state["candidate_orders"] = result["candidate_orders"]

        response = generate_payment_response(result)

        return {
            "route": "payment_confirmation",
            "request": request.model_dump(),
            "result": result,
            "response": response
        }


    # =========================================================
    # 아직 구현하지 않은 기능
    # =========================================================

    return {
        "route": "not_implemented",
        "request": request.model_dump(),
        "result": None,
        "response": "아직 지원하지 않는 문의입니다."
    }