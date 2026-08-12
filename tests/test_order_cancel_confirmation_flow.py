from copy import deepcopy

from app.data.sample_data import (
    orders,
    payments,
    refunds,
)
from app.services.orchestrator import handle_pending_state


def make_confirm_state(order_id: int) -> dict:
    return {
        "pending_action": "confirm_cancel",
        "candidate_orders": [],
        "selected_order_id": order_id,
    }


def test_confirm_cancel_yes_executes_action():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)
    test_state = make_confirm_state(10001)

    result = handle_pending_state(
        user_input="예",
        customer_id=1,
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        state=test_state,
    )

    assert result["route"] == "order_cancel"
    assert result["result"]["result_type"] == "success"

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

    assert order["order_status"] == "order_canceled"
    assert payment["payment_status"] == "payment_canceled"

    # 카드 환불은 refund_processing
    assert result["result"]["refund_status"] == "refund_processing"

    # 카드 주문 취소 처리 완료 → State 초기화
    assert test_state["pending_action"] is None
    assert test_state["selected_order_id"] is None


def test_confirm_cancel_no_does_not_execute_action():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)
    test_state = make_confirm_state(10001)

    result = handle_pending_state(
        user_input="아니오",
        customer_id=1,
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        state=test_state,
    )

    assert result["result"]["result_type"] == "cancel_aborted"

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

    # 실제 데이터가 변경되지 않아야 함
    assert order["order_status"] == "order_completed"
    assert payment["payment_status"] == "payment_completed"

    # 거절했으므로 State 종료
    assert test_state["pending_action"] is None


def test_ambiguous_confirmation_does_not_execute_action():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)
    test_state = make_confirm_state(10001)

    result = handle_pending_state(
        user_input="음... 잘 모르겠어요",
        customer_id=1,
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        state=test_state,
    )

    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10001
    )

    assert order["order_status"] == "order_completed"

    # 아직 승인 여부를 기다려야 함
    assert test_state["pending_action"] == "confirm_cancel"
    assert test_state["selected_order_id"] == 10001


def test_cash_cancel_moves_to_refund_account_collection():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)
    test_state = make_confirm_state(10006)

    result = handle_pending_state(
        user_input="예",
        customer_id=5,
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        state=test_state,
    )

    assert result["result"]["result_type"] == "refund_account_required"
    assert result["result"]["refund_status"] == "refund_account_required"

    # 주문/결제 취소는 이미 완료
    order = next(
        order
        for order in test_orders
        if order["order_id"] == 10006
    )

    payment = next(
        payment
        for payment in test_payments
        if payment["order_id"] == 10006
    )

    assert order["order_status"] == "order_canceled"
    assert payment["payment_status"] == "payment_canceled"

    # 하지만 환불계좌 입력을 기다리는 State는 유지
    assert test_state["pending_action"] == "collect_refund_account"
    assert test_state["selected_order_id"] == 10006