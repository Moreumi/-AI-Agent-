from app.policies.order_completion_policy import judge_order_completion
from app.policies.payment_completion_policy import judge_payment_completion

from app.policies.order_payment_consistency_policy import (
    judge_order_payment_consistency,
)

# =========================================================
# 주문 완료 상태 확인
# =========================================================

def check_order_completion(
    orders: list[dict],
    customer_id: int,
    order_id: int | None = None
) -> dict:

    # 해당 고객의 주문만 조회
    customer_orders = [
        order
        for order in orders
        if order["customer_id"] == customer_id
    ]

    # 해당 고객의 주문이 없는 경우
    if not customer_orders:
        return {
            "result_type": "not_found"
        }

    # 주문번호가 제공된 경우
    if order_id is not None:

        matched_orders = [
            order
            for order in customer_orders
            if order["order_id"] == order_id
        ]

        if not matched_orders:
            return {
                "result_type": "not_found"
            }

        order = matched_orders[0]

        return {
            "result_type": "success",
            "judgment": judge_order_completion(order["order_status"]),
            "order_id": order["order_id"],
            "order_status": order["order_status"],
            "order_date": order["order_date"],
            "total_price": order["total_price"]
        }

    # 주문번호가 없고 해당 고객 주문이 한 건인 경우
    if len(customer_orders) == 1:

        order = customer_orders[0]

        return {
            "result_type": "success",
            "judgment": judge_order_completion(order["order_status"]),
            "order_id": order["order_id"],
            "order_status": order["order_status"],
            "order_date": order["order_date"],
            "total_price": order["total_price"]
        }

    # 주문번호가 없고 해당 고객 주문이 여러 건인 경우
    return {
        "result_type": "need_order_selection",
        "candidate_orders": [
            {
                "order_id": order["order_id"],
                "order_date": order["order_date"],
                "total_price": order["total_price"]
            }
            for order in customer_orders
        ]
    }


# =========================================================
# 주문 확인 결과 → 사용자 응답 생성
# =========================================================

def generate_order_response(result: dict) -> str:

    result_type = result["result_type"]

    # 주문을 찾지 못한 경우
    if result_type == "not_found":
        return "확인되는 주문이 없습니다. 주문번호를 다시 확인해주세요."

    # 주문이 여러 개라 선택이 필요한 경우
    if result_type == "need_order_selection":

        candidate_orders = result["candidate_orders"]

        order_list = "\n".join(
            f"- 주문번호 {order['order_id']} / "
            f"{order['order_date']} / "
            f"{order['total_price']:,}원"
            for order in candidate_orders
        )

        return (
            "확인되는 주문이 여러 건 있습니다.\n"
            "확인할 주문을 선택해주세요.\n\n"
            f"{order_list}"
        )

    # 주문을 정상적으로 찾은 경우
    if result_type == "success":

        order_status = result["order_status"]
        order_id = result["order_id"]

        if order_status == "order_completed":
            return (
                f"주문번호 {order_id}의 주문은 "
                "정상적으로 완료되었습니다."
            )

        if order_status == "order_canceled":
            return (
                f"주문번호 {order_id}의 주문은 "
                "취소된 상태입니다."
            )

        if order_status == "order_failed":
            return (
                f"주문번호 {order_id}의 주문은 "
                "정상적으로 완료되지 않았습니다."
            )

    return "주문 상태를 확인하는 중 문제가 발생했습니다."


# =========================================================
# 결제 완료 확인
# =========================================================

def check_payment_completion(
    orders: list[dict],
    payments: list[dict],
    customer_id: int,
    order_id: int | None = None
) -> dict:

    # 해당 고객의 주문만 조회
    customer_orders = [
        order
        for order in orders
        if order["customer_id"] == customer_id
    ]

    # ---------------------------------------------------------
    # 사용자가 주문번호를 직접 입력한 경우
    # ---------------------------------------------------------
    if order_id is not None:

        selected_order = next(
            (
                order
                for order in customer_orders
                if order["order_id"] == order_id
            ),
            None
        )

        # 해당 고객의 주문이 아닌 경우
        if selected_order is None:
            return {
                "result_type": "not_found"
            }

        selected_order_id = order_id

    # ---------------------------------------------------------
    # 주문번호가 없는 경우
    # ---------------------------------------------------------
    else:

        # 고객의 주문 자체가 없는 경우
        if len(customer_orders) == 0:
            return {
                "result_type": "not_found"
            }

        # 주문이 여러 개라면 사용자가 선택해야 함
        if len(customer_orders) > 1:
            return {
                "result_type": "need_order_selection",
                "candidate_orders": [
                    {
                        "order_id": order["order_id"],
                        "order_date": order["order_date"],
                        "total_price": order["total_price"]
                    }
                    for order in customer_orders
                ]
            }

        # 주문이 하나라면 자동 선택
        selected_order_id = customer_orders[0]["order_id"]

    # ---------------------------------------------------------
    # 선택된 주문의 결제 데이터 조회
    # ---------------------------------------------------------
    payment = next(
        (
            payment
            for payment in payments
            if payment["order_id"] == selected_order_id
        ),
        None
    )

    # 결제 데이터가 없는 경우
    if payment is None:
        return {
            "result_type": "not_found"
        }

    # 결제 데이터 조회 성공
    return {
        "result_type": "success",
        "judgment": judge_payment_completion(payment["payment_status"]),
        "order_id": selected_order_id,
        "payment_id": payment["payment_id"],
        "payment_status": payment["payment_status"],
        "payment_method": payment["payment_method"],
        "payment_amount": payment["payment_amount"],
        "payment_date": payment["payment_date"]
    }


# =========================================================
# 결제 완료 확인 응답 생성
# =========================================================

def generate_payment_response(result: dict) -> str:

    result_type = result["result_type"]

    # ---------------------------------------------------------
    # 주문 또는 결제 정보를 찾지 못한 경우
    # ---------------------------------------------------------
    if result_type == "not_found":
        return "확인할 수 있는 주문 또는 결제 정보가 없습니다."

    # ---------------------------------------------------------
    # 주문이 여러 개라 사용자의 선택이 필요한 경우
    # ---------------------------------------------------------
    if result_type == "need_order_selection":

        candidate_orders = result["candidate_orders"]

        order_list = "\n".join(
            [
                f"- 주문번호 {order['order_id']} / "
                f"{order['order_date']} / "
                f"{order['total_price']:,}원"
                for order in candidate_orders
            ]
        )

        return (
            "확인되는 주문이 여러 건 있습니다.\n"
            "결제 여부를 확인할 주문을 선택해주세요.\n\n"
            f"{order_list}"
        )

    # ---------------------------------------------------------
    # 결제 데이터 조회 성공
    # ---------------------------------------------------------
    if result_type == "success":

        order_id = result["order_id"]
        payment_status = result["payment_status"]
        payment_method = result["payment_method"]
        payment_amount = result["payment_amount"]
        payment_date = result["payment_date"]

        if payment_status == "payment_completed":
            return (
                f"주문번호 {order_id}의 결제가 정상적으로 완료되었습니다.\n"
                f"결제금액: {payment_amount:,}원\n"
                f"결제수단: {payment_method}\n"
                f"결제일: {payment_date}"
            )

        if payment_status == "payment_failed":
            return (
                f"주문번호 {order_id}의 결제가 완료되지 않았습니다. "
                "결제 시도 중 실패한 것으로 확인됩니다."
            )

        if payment_status == "payment_canceled":
            return (
                f"주문번호 {order_id}의 결제는 취소된 상태입니다."
            )

    return "결제 상태를 확인할 수 없습니다."

def check_order_payment_consistency(
    orders: list[dict],
    payments: list[dict],
    customer_id: int,
    order_id: int,
) -> dict:
    """
    특정 주문의 주문 상태와 결제 상태가
    서로 일관된지 확인한다.
    """

    # -----------------------------------------------------
    # 1. 해당 고객의 주문 확인
    # -----------------------------------------------------

    order = next(
        (
            order
            for order in orders
            if order["customer_id"] == customer_id
            and order["order_id"] == order_id
        ),
        None,
    )

    if order is None:
        return {
            "result_type": "order_not_found",
            "consistency_judgment": "order_not_found",
            "order_id": order_id,
        }

    # -----------------------------------------------------
    # 2. 해당 주문의 결제 정보 확인
    # -----------------------------------------------------

    payment = next(
        (
            payment
            for payment in payments
            if payment["order_id"] == order_id
        ),
        None,
    )

    if payment is None:
        return {
            "result_type": "payment_not_found",
            "consistency_judgment": "payment_not_found",
            "order_id": order_id,
            "order_status": order["order_status"],
        }

    # -----------------------------------------------------
    # 3. 주문-결제 상태 일관성 판정
    # -----------------------------------------------------

    consistency_judgment = judge_order_payment_consistency(
        order_status=order["order_status"],
        payment_status=payment["payment_status"],
    )

    return {
        "result_type": "success",
        "consistency_judgment": consistency_judgment,
        "order_id": order_id,
        "order_status": order["order_status"],
        "payment_status": payment["payment_status"],
    }