from copy import deepcopy

from app.data.sample_data import (
    orders,
    payments,
    payment_adjustments,
)
from app.services.order_payment_service import (
    change_order_quantity,
)


# =========================================================
# 수량 감소 Action
# =========================================================

def test_change_order_quantity_decrease_success():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_adjustments = deepcopy(payment_adjustments)

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=2,
    )

    assert result["result_type"] == "success"

    assert result["previous_quantity"] == 3
    assert result["new_quantity"] == 2

    assert result["previous_total_price"] == 60000
    assert result["new_total_price"] == 40000

    assert result["adjustment_type"] == "partial_refund_required"
    assert result["adjustment_amount"] == 20000
    assert result["adjustment_status"] == "pending"

    changed_order = next(
        order
        for order in test_orders
        if order["order_id"] == 10007
    )

    assert changed_order["quantity"] == 2
    assert changed_order["total_price"] == 40000

    # 기존에 실제 결제된 금액은 변경하지 않음
    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10007
    )

    assert payment["payment_amount"] == 60000

    assert len(test_adjustments) == 1
    assert test_adjustments[0]["adjustment_type"] == (
        "partial_refund_required"
    )
    assert test_adjustments[0]["adjustment_amount"] == 20000


# =========================================================
# 수량 증가 Action
# =========================================================

def test_change_order_quantity_increase_success():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_adjustments = deepcopy(payment_adjustments)

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=5,
    )

    assert result["result_type"] == "success"

    assert result["previous_quantity"] == 3
    assert result["new_quantity"] == 5

    assert result["previous_total_price"] == 60000
    assert result["new_total_price"] == 100000

    assert result["adjustment_type"] == "additional_payment_required"
    assert result["adjustment_amount"] == 40000

    changed_order = next(
        order
        for order in test_orders
        if order["order_id"] == 10007
    )

    assert changed_order["quantity"] == 5
    assert changed_order["total_price"] == 100000


# =========================================================
# Action 직전 배송 상태 변경 → 차단
# =========================================================

def test_change_order_quantity_rechecks_delivery_status():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_adjustments = deepcopy(payment_adjustments)

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10007
    )

    # Preview 이후 배송이 시작된 상황을 가정
    order["delivery_status"] = "in_transit"

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=2,
    )

    assert result == {
        "result_type": "action_failed",
        "reason": "in_transit",
        "order_id": 10007,
    }

    # Action이 차단되었으므로 실제 데이터도 그대로
    assert order["quantity"] == 3
    assert order["total_price"] == 60000
    assert test_adjustments == []


# =========================================================
# Action 직전 결제 실패 → 차단
# =========================================================

def test_change_order_quantity_rechecks_payment_status():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_adjustments = deepcopy(payment_adjustments)

    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10007
    )

    payment["payment_status"] = "payment_failed"

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=2,
    )

    assert result == {
        "result_type": "action_failed",
        "reason": "payment_failed",
        "order_id": 10007,
    }

    assert test_adjustments == []


# =========================================================
# 목표 수량 0 → Write Action 차단
# =========================================================

def test_change_order_quantity_blocks_zero_quantity():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_adjustments = deepcopy(payment_adjustments)

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=0,
    )

    assert result == {
        "result_type": "action_failed",
        "reason": "target_quantity_zero",
        "order_id": 10007,
    }

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10007
    )

    assert order["quantity"] == 3
    assert order["total_price"] == 60000
    assert test_adjustments == []


# =========================================================
# 미처리 Payment Adjustment 존재 → 추가 변경 차단
# =========================================================

def test_change_order_quantity_blocks_pending_adjustment():
    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)

    test_adjustments = [
        {
            "adjustment_id": 90001,
            "order_id": 10007,
            "payment_id": 50007,
            "adjustment_type": "partial_refund_required",
            "adjustment_amount": 20000,
            "adjustment_status": "pending",
        }
    ]

    result = change_order_quantity(
        orders=test_orders,
        payments=test_payments,
        payment_adjustments=test_adjustments,
        customer_id=6,
        order_id=10007,
        target_quantity=2,
    )

    assert result == {
        "result_type": "action_failed",
        "reason": "pending_payment_adjustment",
        "order_id": 10007,
    }

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10007
    )

    assert order["quantity"] == 3
    assert order["total_price"] == 60000
    assert len(test_adjustments) == 1