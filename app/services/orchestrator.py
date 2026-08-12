from app.services.llm_service import classification_chain

from app.services.order_payment_service import (
    check_order_completion,
    generate_order_response,
    check_payment_completion,
    generate_payment_response,
    check_order_payment_consistency,
)

from app.policies.order_payment_consistency_policy import (
    ORDER_PAYMENT_CONSISTENCY_POLICY_CONTEXT,
)

from app.services.state_service import (
    reset_state,
    extract_order_id,
)

from app.services.response_service import generate_cs_response

from app.policies.order_completion_policy import (
    ORDER_COMPLETION_POLICY_CONTEXT,
)

from app.policies.payment_completion_policy import (
    PAYMENT_COMPLETION_POLICY_CONTEXT,
)

# =========================================================
# 1. 주문 완료 확인 최종 응답 생성
# =========================================================

def build_order_confirmation_response(
    user_input: str,
    result: dict,
    consistency_result: dict | None = None,
) -> str:
    """
    주문 완료 확인 결과와 주문-결제 일관성 결과에 따라
    최종 응답 생성 방식을 결정한다.

    - 주문 조회 실패 / 선택 필요:
      기존 Python 응답 사용

    - 주문 조회 성공 + 일관성 문제 없음:
      fact_summary 사용

    - 주문 조회 성공 + 주문/결제 불일치:
      narrative_guidance 사용
    """

    if result.get("result_type") != "success":
        return generate_order_response(result)

    # 주문-결제 상태가 비정상적이거나
    # 결제 정보를 확인할 수 없는 경우
    if consistency_result is not None:
        consistency_judgment = consistency_result.get(
            "consistency_judgment"
        )

        if consistency_judgment in {
            "needs_review",
            "payment_not_found",
            "order_not_found",
        }:
            combined_result = {
                "order_result": result,
                "consistency_result": consistency_result,
            }

            return generate_cs_response(
                user_input=user_input,
                sub_intent="order_confirmation",
                response_mode="narrative_guidance",
                result=combined_result,
                policy_context=(
                    ORDER_COMPLETION_POLICY_CONTEXT
                    + "\n\n"
                    + ORDER_PAYMENT_CONSISTENCY_POLICY_CONTEXT
                ),
            )

    # 정상적인 조회 결과
    return generate_cs_response(
        user_input=user_input,
        sub_intent="order_confirmation",
        response_mode="fact_summary",
        result=result,
        policy_context=ORDER_COMPLETION_POLICY_CONTEXT,
    )

def build_payment_confirmation_response(
    user_input: str,
    result: dict,
    consistency_result: dict | None = None,
) -> str:
    """
    결제 완료 확인 결과와 주문-결제 일관성 결과에 따라
    최종 응답 생성 방식을 결정한다.

    - 결제 조회 실패 / 선택 필요:
      기존 Python 응답 사용

    - 결제 조회 성공 + 일관성 문제 없음:
      fact_summary 사용

    - 결제 조회 성공 + 주문/결제 불일치:
      narrative_guidance 사용
    """

    if result.get("result_type") != "success":
        return generate_payment_response(result)

    if consistency_result is not None:
        consistency_judgment = consistency_result.get(
            "consistency_judgment"
        )

        if consistency_judgment in {
            "needs_review",
            "payment_not_found",
            "order_not_found",
        }:
            combined_result = {
                "payment_result": result,
                "consistency_result": consistency_result,
            }

            return generate_cs_response(
                user_input=user_input,
                sub_intent="payment_confirmation",
                response_mode="narrative_guidance",
                result=combined_result,
                policy_context=(
                    PAYMENT_COMPLETION_POLICY_CONTEXT
                    + "\n\n"
                    + ORDER_PAYMENT_CONSISTENCY_POLICY_CONTEXT
                ),
            )

    return generate_cs_response(
        user_input=user_input,
        sub_intent="payment_confirmation",
        response_mode="fact_summary",
        result=result,
        policy_context=PAYMENT_COMPLETION_POLICY_CONTEXT,
    )

# =========================================================
# 2. 이전 대화에서 처리 중인 State 확인
# =========================================================

def handle_pending_state(
    user_input: str,
    customer_id: int,
    orders: list[dict],
    state: dict,
    payments: list[dict] | None = None,
) -> dict | None:

    # 현재 기다리고 있는 후속 작업이 없는 경우
    if state["pending_action"] is None:
        return None


    # -----------------------------------------------------
    # 주문 완료 확인
    # -----------------------------------------------------

    if state["pending_action"] == "order_confirmation":

        # 사용자의 새 입력에서 주문번호 추출
        selected_order_id = extract_order_id(user_input)

        # 주문번호를 찾지 못한 경우
        if selected_order_id is None:
            return {
                "route": "order_confirmation",
                "result": None,
                "response": "확인할 주문번호를 입력해주세요.",
            }

        # 기존 State에 저장되어 있는 선택 가능한 주문번호
        candidate_order_ids = [
            order["order_id"]
            for order in state["candidate_orders"]
        ]

        # 후보에 없는 주문번호를 선택한 경우
        if selected_order_id not in candidate_order_ids:
            return {
                "route": "order_confirmation",
                "result": None,
                "response": "선택 가능한 주문번호 중에서 다시 선택해주세요.",
            }

        # 정상적인 주문번호를 선택한 경우
        result = check_order_completion(
            orders=orders,
            customer_id=customer_id,
            order_id=selected_order_id,
        )

        consistency_result = None

        if (
            result.get("result_type") == "success"
            and payments is not None
        ):
            consistency_result = check_order_payment_consistency(
                orders=orders,
                payments=payments,
                customer_id=customer_id,
                order_id=selected_order_id,
        )

        response = build_order_confirmation_response(
            user_input=user_input,
            result=result,
            consistency_result=consistency_result,
        )

        # 하나의 작업이 끝났으므로 State 초기화
        reset_state(state)

        return {
            "route": "order_confirmation",
            "result": result,
            "response": response,
        }


    # -----------------------------------------------------
    # 결제 완료 확인
    # -----------------------------------------------------

    if state["pending_action"] == "payment_confirmation":

        selected_order_id = extract_order_id(user_input)

        # 주문번호를 찾지 못한 경우
        if selected_order_id is None:
            return {
                "route": "payment_confirmation",
                "result": None,
                "response": "결제를 확인할 주문번호를 입력해주세요.",
            }

        candidate_order_ids = [
            order["order_id"]
            for order in state["candidate_orders"]
        ]

        # 후보에 없는 주문번호를 선택한 경우
        if selected_order_id not in candidate_order_ids:
            return {
                "route": "payment_confirmation",
                "result": None,
                "response": "선택 가능한 주문번호 중에서 다시 선택해주세요.",
            }

        # payments가 전달되지 않은 경우 빈 리스트 사용
        if payments is None:
            payments = []

        result = check_payment_completion(
            orders=orders,
            payments=payments,
            customer_id=customer_id,
            order_id=selected_order_id,
        )

        consistency_result = None

        if result.get("result_type") == "success":
            consistency_result = check_order_payment_consistency(
              orders=orders,
              payments=payments,
              customer_id=customer_id,
              order_id=selected_order_id,
            )
        
        response = build_payment_confirmation_response(
            user_input=user_input,
            result=result,
            consistency_result=consistency_result,
        )

        # 작업 완료 후 State 초기화
        reset_state(state)

        return {
            "route": "payment_confirmation",
            "result": result,
            "response": response,
        }

    return None


# =========================================================
# 3. Router / Orchestrator
# =========================================================

def route_request(
    user_input: str,
    customer_id: int,
    orders: list[dict],
    state: dict,
    payments: list[dict] | None = None,
) -> dict:

    # -----------------------------------------------------
    # 1) 이전 대화에서 진행 중인 작업이 있는지 먼저 확인
    # -----------------------------------------------------

    pending_result = handle_pending_state(
        user_input=user_input,
        customer_id=customer_id,
        orders=orders,
        state=state,
        payments=payments,
    )

    if pending_result is not None:
        return pending_result


    # -----------------------------------------------------
    # 2) 진행 중인 작업이 없다면 새로운 질문으로 분류
    # -----------------------------------------------------

    request = classification_chain.invoke(
        {
            "user_input": user_input,
        }
    )


    # -----------------------------------------------------
    # 3) 주문 완료 확인
    # -----------------------------------------------------

    if (
        request.intent == "cs"
        and request.cs_category == "order_payment"
        and request.sub_intent == "order_confirmation"
    ):

        result = check_order_completion(
            orders=orders,
            customer_id=customer_id,
            order_id=request.order_id,
        )

        # 주문이 여러 개라 추가 질문이 필요한 경우
        # 다음 대화를 위해 State에 저장
        if result["result_type"] == "need_order_selection":
            state["pending_action"] = "order_confirmation"
            state["candidate_orders"] = result["candidate_orders"]

        consistency_result = None

        if (
            result.get("result_type") == "success"
            and payments is not None
        ):
            consistency_result = check_order_payment_consistency(
                orders=orders,
                payments=payments,
                customer_id=customer_id,
                order_id=result["order_id"],
        )

        # 주문 완료 확인 응답 생성
        response = build_order_confirmation_response(
            user_input=user_input,
            result=result,
            consistency_result=consistency_result,
        )

        return {
            "route": "order_confirmation",
            "request": request.model_dump(),
            "result": result,
            "response": response,
        }


    # -----------------------------------------------------
    # 4) 결제 완료 확인
    # -----------------------------------------------------

    if (
        request.intent == "cs"
        and request.cs_category == "order_payment"
        and request.sub_intent == "payment_confirmation"
    ):

        if payments is None:
            payments = []

        result = check_payment_completion(
            orders=orders,
            payments=payments,
            customer_id=customer_id,
            order_id=request.order_id,
        )

        # 주문이 여러 개라 결제를 확인할 주문 선택이 필요한 경우
        if result["result_type"] == "need_order_selection":
            state["pending_action"] = "payment_confirmation"
            state["candidate_orders"] = result["candidate_orders"]
        consistency_result = None

        if result.get("result_type") == "success":
            consistency_result = check_order_payment_consistency(
                orders=orders,
                payments=payments,
                customer_id=customer_id,
                order_id=result["order_id"],
            )
        # 현재 결제 완료 확인은 기존 Python 응답 유지
        response = build_payment_confirmation_response(
            user_input=user_input,
            result=result,
            consistency_result=consistency_result,
        )

        return {
            "route": "payment_confirmation",
            "request": request.model_dump(),
            "result": result,
            "response": response,
        }


    # -----------------------------------------------------
    # 5) 아직 구현하지 않은 기능
    # -----------------------------------------------------

    return {
        "route": "not_implemented",
        "request": request.model_dump(),
        "result": None,
        "response": "아직 지원하지 않는 문의입니다.",
    }