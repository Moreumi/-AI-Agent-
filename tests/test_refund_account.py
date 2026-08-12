from copy import deepcopy

from app.data.sample_data import (
    orders,
    payments,
    refunds,
)
from app.services.order_payment_service import (
    cancel_order,
    register_refund_account,
)
from app.services.state_service import extract_refund_account


def test_extract_refund_account():

    result = extract_refund_account(
        "국민은행 / 1234567890 / 홍길동"
    )

    assert result == {
        "bank_name": "국민은행",
        "account_number": "1234567890",
        "account_holder": "홍길동",
    }


def test_invalid_refund_account_input():

    result = extract_refund_account(
        "국민은행 홍길동"
    )

    assert result is None


def test_register_refund_account():

    test_orders = deepcopy(orders)
    test_payments = deepcopy(payments)
    test_refunds = deepcopy(refunds)

    # -----------------------------------------------------
    # 먼저 계좌이체 주문을 취소하여
    # refund_account_required 상태 생성
    # -----------------------------------------------------

    cancel_result = cancel_order(
        orders=test_orders,
        payments=test_payments,
        refunds=test_refunds,
        customer_id=5,
        order_id=10006,
    )

    assert (
        cancel_result["refund_status"]
        == "refund_account_required"
    )

    # -----------------------------------------------------
    # 환불계좌 등록
    # -----------------------------------------------------

    result = register_refund_account(
        refunds=test_refunds,
        order_id=10006,
        bank_name="국민은행",
        account_number="1234567890",
        account_holder="홍길동",
    )

    assert result["result_type"] == "success"
    assert result["refund_status"] == "refund_processing"

    refund = next(
        refund
        for refund in test_refunds
        if refund["order_id"] == 10006
    )

    assert refund["bank_name"] == "국민은행"
    assert refund["account_number"] == "1234567890"
    assert refund["account_holder"] == "홍길동"
    assert refund["refund_status"] == "refund_processing"