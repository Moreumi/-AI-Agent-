from copy import deepcopy

from app.data.sample_data import orders, payments
from app.services.order_payment_service import check_order_change


# =========================================================
# 정상 수량 감소
# =========================================================

def test_order_change_service_decrease_success():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=6,
        quantity_change_type="decrease",
        quantity_value=1,
        order_id=10007,
    )

    assert result["result_type"] == "change_preview"
    assert result["order_id"] == 10007
    assert result["payment_id"] == 50007

    calculation = result["calculation"]

    assert calculation["current_quantity"] == 3
    assert calculation["target_quantity"] == 2
    assert calculation["current_total_price"] == 60000
    assert calculation["new_total_price"] == 40000
    assert calculation["adjustment_type"] == "partial_refund_required"
    assert calculation["adjustment_amount"] == 20000


# =========================================================
# 정상 수량 증가
# =========================================================

def test_order_change_service_increase_success():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=6,
        quantity_change_type="increase",
        quantity_value=2,
        order_id=10007,
    )

    assert result["result_type"] == "change_preview"

    calculation = result["calculation"]

    assert calculation["current_quantity"] == 3
    assert calculation["target_quantity"] == 5
    assert calculation["new_total_price"] == 100000
    assert calculation["adjustment_type"] == "additional_payment_required"
    assert calculation["adjustment_amount"] == 40000


# =========================================================
# 여러 주문 → 주문 선택 필요
# =========================================================

def test_order_change_service_requires_order_selection():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=1,
        quantity_change_type="increase",
        quantity_value=1,
        order_id=None,
    )

    assert result["result_type"] == "need_order_selection"

    candidate_order_ids = [
        order["order_id"]
        for order in result["candidate_orders"]
    ]

    assert 10001 in candidate_order_ids
    assert 10002 in candidate_order_ids


# =========================================================
# 수량 정보 미입력 → 추가 질문 필요
# =========================================================

def test_order_change_service_requires_quantity_input():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=6,
        quantity_change_type=None,
        quantity_value=None,
        order_id=10007,
    )

    assert result == {
        "result_type": "need_quantity_input",
        "order_id": 10007,
        "current_quantity": 3,
        "unit_price": 20000,
        "current_total_price": 60000,
    }


# =========================================================
# 배송 중 → 수량 변경 불가
# =========================================================

def test_order_change_service_blocks_in_transit_order():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=3,
        quantity_change_type="increase",
        quantity_value=1,
        order_id=10004,
    )

    assert result["result_type"] == "not_changeable"
    assert result["change_judgment"] == "not_changeable"
    assert result["reason"] == "in_transit"


# =========================================================
# 결제 실패 → 수량 변경 불가
# =========================================================

def test_order_change_service_blocks_failed_payment():
    test_payments = deepcopy(payments)

    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10007
    )

    payment["payment_status"] = "payment_failed"

    result = check_order_change(
        orders=orders,
        payments=test_payments,
        customer_id=6,
        quantity_change_type="increase",
        quantity_value=1,
        order_id=10007,
    )

    assert result["result_type"] == "not_changeable"
    assert result["change_judgment"] == "not_changeable"
    assert result["reason"] == "payment_failed"


# =========================================================
# 수량 0 → 주문 취소 안내 필요
# =========================================================

def test_order_change_service_returns_cancel_required():
    result = check_order_change(
        orders=orders,
        payments=payments,
        customer_id=6,
        quantity_change_type="decrease",
        quantity_value=3,
        order_id=10007,
    )

    assert result["result_type"] == "cancel_required"

    calculation = result["calculation"]

    assert calculation == {
        "result_type": "cancel_required",
        "reason": "target_quantity_zero",
        "current_quantity": 3,
        "target_quantity": 0,
    }