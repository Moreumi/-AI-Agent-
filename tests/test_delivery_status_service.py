from app.data.sample_data import orders
from app.services.delivery_service import check_delivery_status


# =========================================================
# 배송 상태 조회 Service 테스트
# =========================================================


def test_delivery_status_with_explicit_order_id():
    """
    사용자가 주문번호를 직접 제공한 경우
    해당 주문의 배송 상태를 반환해야 한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=3,
        order_id=10004,
    )

    assert result["result_type"] == "success"
    assert result["order_id"] == 10004
    assert result["order_status"] == "order_completed"
    assert result["delivery_status"] == "in_transit"
    assert result["order_date"] == "2026-08-11"
    assert result["total_price"] == 57000


def test_delivery_status_auto_selects_single_order():
    """
    주문번호가 없더라도
    고객의 주문이 한 건이면 자동으로 선택해야 한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=4,
    )

    assert result["result_type"] == "success"
    assert result["order_id"] == 10005
    assert result["order_status"] == "order_completed"
    assert result["delivery_status"] == "delivered"


def test_delivery_status_requires_selection_for_multiple_orders():
    """
    주문번호가 없고 고객의 주문이 여러 건이면
    Agent가 임의로 선택하지 않고 주문 선택을 요청해야 한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=1,
    )

    assert result["result_type"] == "need_order_selection"

    candidate_order_ids = [
        order["order_id"]
        for order in result["candidate_orders"]
    ]

    assert candidate_order_ids == [10001, 10002]


def test_delivery_status_not_found_for_invalid_order_id():
    """
    존재하지 않거나 해당 고객의 주문이 아닌 주문번호는
    조회할 수 없어야 한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=3,
        order_id=10001,
    )

    assert result["result_type"] == "not_found"


def test_delivery_status_not_found_when_customer_has_no_orders():
    """
    해당 고객의 주문 자체가 없는 경우
    not_found를 반환해야 한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=999,
    )

    assert result["result_type"] == "not_found"


def test_delivery_status_returns_order_status_for_canceled_order():
    """
    Delivery Service는 배송 상태를 임의로 해석하지 않고
    주문 상태와 배송 상태의 실제 값을 함께 반환해야 한다.

    이후 Orchestrator가 취소된 주문에 대해
    잘못된 배송 안내를 하지 않도록 필요한 사실값을 전달한다.
    """

    result = check_delivery_status(
        orders=orders,
        customer_id=2,
        order_id=10003,
    )

    assert result["result_type"] == "success"
    assert result["order_id"] == 10003
    assert result["order_status"] == "order_canceled"
    assert result["delivery_status"] == "preparing_shipment"