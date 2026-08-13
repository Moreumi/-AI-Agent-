# =========================================================
# 배송 예상 시기 안내 Policy
# =========================================================

DELIVERY_ETA_POLICY_CONTEXT = """
현재 쇼핑몰의 일반 배송 기준은 다음과 같다.

- 일반 지역:
  배송 시작일 기준 영업일 3~5일 정도 소요된다.

- 제주 및 도서산간 지역:
  배송 시작일 기준 최대 7일 정도 소요될 수 있다.

이 배송기간은 쇼핑몰의 일반적인 안내 기준이며,
특정 주문의 확정 도착일을 의미하지 않는다.

현재 MVP에서는 택배사 실시간 배송 추적 정보나
확정 배송 예정일 데이터를 제공하지 않는다.

따라서 실제 데이터에 존재하지 않는
정확한 도착 날짜나 현재 배송 위치를 임의로 추정하지 않는다.
"""


# =========================================================
# 일반 배송기간 Policy
# =========================================================

def get_general_delivery_eta_policy() -> dict:
    """
    특정 주문이 아닌 일반적인 배송기간 문의에 사용할
    쇼핑몰 배송 Policy를 반환한다.
    """

    return {
        "eta_judgment": "general_guidance",
        "delivery_basis": "shipping_start_date",
        "standard_delivery_days": "3~5 영업일",
        "remote_area_delivery_days": "최대 7일",
    }


# =========================================================
# 특정 주문 배송 예상 시기 판단
# =========================================================

def judge_order_delivery_eta(
    order_status: str,
    delivery_status: str,
) -> dict:
    """
    특정 주문의 현재 주문 상태와 배송 상태를 기준으로
    어떤 배송 예상 안내가 가능한지 판단한다.

    실제 도착 날짜를 계산하거나 추정하지 않는다.
    """

    # 이미 취소된 주문
    if order_status == "order_canceled":
        return {
            "eta_judgment": "not_applicable",
            "reason": "order_canceled",
        }

    # 정상 완료되지 않은 주문
    if order_status == "order_failed":
        return {
            "eta_judgment": "not_applicable",
            "reason": "order_failed",
        }

    # 정의되지 않은 주문 상태
    if order_status != "order_completed":
        return {
            "eta_judgment": "needs_review",
            "reason": "unknown_order_status",
        }

    # -----------------------------------------------------
    # 여기부터는 정상 완료된 주문
    # -----------------------------------------------------

    # 배송 준비 중
    if delivery_status == "preparing_shipment":
        return {
            "eta_judgment": "policy_guidance",
            "reason": "preparing_shipment",
            "delivery_basis": "shipping_start_date",
            "standard_delivery_days": "3~5 영업일",
            "remote_area_delivery_days": "최대 7일",
        }

    # 배송 중
    if delivery_status == "in_transit":
        return {
            "eta_judgment": "policy_guidance",
            "reason": "in_transit",
            "delivery_basis": "shipping_start_date",
            "standard_delivery_days": "3~5 영업일",
            "remote_area_delivery_days": "최대 7일",
        }

    # 배송 완료
    if delivery_status == "delivered":
        return {
            "eta_judgment": "already_delivered",
            "reason": "delivered",
        }

    # 정의되지 않은 배송 상태
    return {
        "eta_judgment": "needs_review",
        "reason": "unknown_delivery_status",
    }