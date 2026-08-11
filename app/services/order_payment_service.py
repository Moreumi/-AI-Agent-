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
