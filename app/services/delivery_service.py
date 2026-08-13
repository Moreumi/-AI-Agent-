# =========================================================
# app/services/delivery_service.py
# 배송 관련 데이터 조회 Service
# =========================================================


# =========================================================
# 배송 상태 확인
# =========================================================

def check_delivery_status(
    orders: list[dict],
    customer_id: int,
    order_id: int | None = None,
) -> dict:
    """
    고객의 주문을 조회하여 현재 배송 상태를 반환한다.

    이 함수는 배송 상태에 대한 Business Policy 판단이나
    자연어 응답 생성을 수행하지 않는다.

    처리 결과:
    - success
    - not_found
    - need_order_selection
    """

    # -----------------------------------------------------
    # 1. 해당 고객의 주문만 조회
    # -----------------------------------------------------

    customer_orders = [
        order
        for order in orders
        if order["customer_id"] == customer_id
    ]

    if not customer_orders:
        return {
            "result_type": "not_found",
        }

    # -----------------------------------------------------
    # 2. 주문번호가 직접 제공된 경우
    # -----------------------------------------------------

    if order_id is not None:
        selected_order = next(
            (
                order
                for order in customer_orders
                if order["order_id"] == order_id
            ),
            None,
        )

        # 해당 고객의 주문이 아니거나 존재하지 않는 주문
        if selected_order is None:
            return {
                "result_type": "not_found",
            }

    # -----------------------------------------------------
    # 3. 주문번호가 없는 경우
    # -----------------------------------------------------

    else:
        # 주문이 여러 건이면 사용자가 선택해야 함
        if len(customer_orders) > 1:
            return {
                "result_type": "need_order_selection",
                "candidate_orders": [
                    {
                        "order_id": order["order_id"],
                        "order_date": order["order_date"],
                        "total_price": order["total_price"],
                    }
                    for order in customer_orders
                ],
            }

        # 주문이 한 건이면 자동 선택
        selected_order = customer_orders[0]

    # -----------------------------------------------------
    # 4. 선택된 주문의 배송 상태 반환
    # -----------------------------------------------------

    return {
        "result_type": "success",
        "order_id": selected_order["order_id"],
        "order_status": selected_order["order_status"],
        "delivery_status": selected_order["delivery_status"],
        "order_date": selected_order["order_date"],
        "total_price": selected_order["total_price"],
    }