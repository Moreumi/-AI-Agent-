from copy import deepcopy

from app.data.sample_data import (
    orders,
    payments,
    refunds,
)
from app.services.order_payment_service import cancel_order


def test_card_order_cancel_action():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)

    result = cancel_order(
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        customer_id=1,
        order_id=10001,
    )

    assert result["result_type"] == "success"
    assert result["order_status"] == "order_canceled"
    assert result["payment_status"] == "payment_canceled"
    assert result["payment_method"] == "card"
    assert result["refund_status"] == "refund_processing"

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10001
    )

    refund = next(
        refund
        for refund in test_refunds
        if refund["order_id"] == 10001
    )

    assert order["order_status"] == "order_canceled"
    assert payment["payment_status"] == "payment_canceled"
    assert refund["refund_status"] == "refund_processing"


def test_cash_order_cancel_requires_refund_account():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)

    result = cancel_order(
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        customer_id=5,
        order_id=10006,
    )

    assert result["result_type"] == "refund_account_required"
    assert result["order_status"] == "order_canceled"
    assert result["payment_status"] == "payment_canceled"
    assert result["payment_method"] == "cash"
    assert result["refund_status"] == "refund_account_required"

    refund = next(
        refund
        for refund in test_refunds
        if refund["order_id"] == 10006
    )

    assert refund["bank_name"] is None
    assert refund["account_number"] is None
    assert refund["account_holder"] is None


def test_cancel_action_fails_for_invalid_order():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)

    result = cancel_order(
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        customer_id=1,
        order_id=99999,
    )

    assert result["result_type"] == "action_failed"
    assert result["reason"] == "order_not_found"

def test_cancel_order_rechecks_delivery_status_before_action():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)

    # 최초 취소 가능 여부 확인 이후
    # 실제 Action 전에 배송이 시작됐다고 가정
    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    order["delivery_status"] = "in_transit"

    result = cancel_order(
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        customer_id=1,
        order_id=10001,
    )

    assert result["result_type"] == "action_failed"
    assert result["reason"] == "in_transit"

    # Action이 차단되었으므로 주문/결제 상태가 변경되면 안 됨
    assert order["order_status"] == "order_completed"

    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10001
    )

    assert payment["payment_status"] == "payment_completed"

    # 환불 데이터도 새로 생성되면 안 됨
    assert not any(
    refund["order_id"] == 10001
    for refund in test_refunds
)