# =========================================================
# 주문 수량 변경 가능 여부 Policy
# =========================================================

ORDER_CHANGE_POLICY_CONTEXT = """
현재 구현에서는 주문 수량 변경 가능 여부를
order_status, delivery_status, payment_status를 기준으로 판단한다.

[주문 상태 기준]

- order_canceled:
  이미 취소된 주문이므로 수량을 변경할 수 없다.

- order_failed:
  정상적으로 완료되지 않은 주문이므로 수량을 변경할 수 없다.

- order_completed:
  배송 상태와 결제 상태를 추가로 확인한다.

[배송 상태 기준]

- preparing_shipment:
  배송 준비 중인 주문이다.
  다른 조건도 정상이라면 수량 변경이 가능하다.

- in_transit:
  이미 배송이 시작된 주문이므로 수량을 변경할 수 없다.

- delivered:
  배송이 완료된 주문이므로 수량을 변경할 수 없다.

[결제 상태 기준]

- payment_completed:
  정상적으로 결제가 완료된 상태이다.

- payment_failed:
  정상적으로 결제가 완료되지 않았으므로
  주문 수량 변경을 진행하지 않는다.

- payment_canceled:
  결제가 취소된 주문이므로
  주문 수량 변경을 진행하지 않는다.

주문 수량 변경 가능 여부를 판단하는 것과
실제 주문 데이터를 변경하는 Action은 분리한다.

수량 변경이 가능한 경우에도
변경될 수량과 주문 금액, 결제 차액을 먼저 계산하고
사용자의 최종 승인을 받은 이후에만
실제 주문 수량 변경 Action을 실행한다.
"""


def judge_order_change(
    order_status: str,
    delivery_status: str,
    payment_status: str,
) -> dict:
    """
    주문 상태, 배송 상태, 결제 상태를 기준으로
    주문 수량 변경 가능 여부를 판단한다.

    실제 수량 변경 Action이나 금액 계산은 수행하지 않는다.
    """

    # -----------------------------------------------------
    # 1. 주문 상태 확인
    # -----------------------------------------------------

    if order_status == "order_canceled":
        return {
            "change_judgment": "not_changeable",
            "reason": "order_canceled",
        }

    if order_status == "order_failed":
        return {
            "change_judgment": "not_changeable",
            "reason": "order_failed",
        }

    if order_status != "order_completed":
        return {
            "change_judgment": "needs_review",
            "reason": "unknown_order_status",
        }

    # -----------------------------------------------------
    # 2. 배송 상태 확인
    # -----------------------------------------------------

    if delivery_status == "in_transit":
        return {
            "change_judgment": "not_changeable",
            "reason": "in_transit",
        }

    if delivery_status == "delivered":
        return {
            "change_judgment": "not_changeable",
            "reason": "delivered",
        }

    if delivery_status != "preparing_shipment":
        return {
            "change_judgment": "needs_review",
            "reason": "unknown_delivery_status",
        }

    # -----------------------------------------------------
    # 3. 결제 상태 확인
    # -----------------------------------------------------

    if payment_status == "payment_failed":
        return {
            "change_judgment": "not_changeable",
            "reason": "payment_failed",
        }

    if payment_status == "payment_canceled":
        return {
            "change_judgment": "not_changeable",
            "reason": "payment_canceled",
        }

    if payment_status != "payment_completed":
        return {
            "change_judgment": "needs_review",
            "reason": "unknown_payment_status",
        }

    # -----------------------------------------------------
    # 4. 모든 조건 충족
    # -----------------------------------------------------

    return {
        "change_judgment": "changeable",
        "reason": None,
    }